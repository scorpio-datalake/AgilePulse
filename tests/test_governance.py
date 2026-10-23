from pathlib import Path

from fastapi.testclient import TestClient

from app.db import ADMIN_PASSWORD, ADMIN_USERNAME
from app.main import create_app
from app.settings import Settings


def _client(path: Path) -> TestClient:
    return TestClient(create_app(Settings(database_path=path, session_secret="test-session-secret")))


def _sign_in(client: TestClient) -> None:
    response = client.post(
        "/sign-in",
        data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 303


def _create(client: TestClient, path: str, data: dict) -> str:
    response = client.post(path, data=data, follow_redirects=False)
    assert response.status_code == 303, response.text
    return response.headers["location"]


def _record_id(location: str) -> str:
    return location.rstrip("/").rsplit("/", 1)[-1]


def test_governance_and_evidence(tmp_path: Path):
    with _client(tmp_path / "governance.sqlite") as client:
        _sign_in(client)
        portfolio_id = _record_id(_create(client, "/portfolios", {"name": "Supply chain"}))
        stream_id = _record_id(
            _create(
                client,
                "/value-streams",
                {"name": "Warehouse fulfillment", "portfolio_id": portfolio_id},
            )
        )
        group_id = _record_id(
            _create(
                client,
                "/delivery-groups",
                {"name": "Optimization of the warehouse", "value_stream_id": stream_id},
            )
        )
        team_id = _record_id(
            _create(client, "/teams", {"name": "Build crew", "delivery_group_id": group_id})
        )
        goal_id = _record_id(
            _create(client, "/goals", {"name": "Fewer walking miles", "value_stream_id": stream_id})
        )
        initiative_id = _record_id(
            _create(client, "/initiatives", {"name": "Slot the picks", "goal_id": goal_id})
        )
        feature_id = _record_id(
            _create(
                client,
                "/features",
                {"name": "Pick path", "initiative_id": initiative_id, "kind": "feature"},
            )
        )
        dev_id = _record_id(
            _create(client, "/people", {"name": "Dev", "role": "team_member", "team_id": team_id})
        )
        checker_id = _record_id(
            _create(
                client, "/people", {"name": "Checker", "role": "team_member", "team_id": team_id}
            )
        )
        _create(
            client,
            f"/delivery-groups/{group_id}/policies",
            {"from_stage": "", "to_stage": "Check", "effect": "warning"},
        )
        _create(
            client,
            f"/delivery-groups/{group_id}/policies",
            {"from_stage": "", "to_stage": "Ship", "effect": "block"},
        )
        group = client.get(f"/delivery-groups/{group_id}")
        assert 'class="policy">warning into Check' in group.text
        assert 'class="policy">block into Ship' in group.text

        client.post(
            f"/features/{feature_id}/stage",
            data={"stage": "Define", "person_id": dev_id},
            follow_redirects=True,
        )
        client.post(
            f"/features/{feature_id}/approval",
            data={"person_id": dev_id},
            follow_redirects=True,
        )
        client.post(
            f"/features/{feature_id}/stage",
            data={"stage": "Build", "person_id": dev_id},
            follow_redirects=True,
        )
        client.post(
            f"/features/{feature_id}/done-list",
            data={"integrated": "1", "acceptance": "1", "dependency": "1", "rollback": "1"},
            follow_redirects=True,
        )
        checked = client.post(
            f"/features/{feature_id}/stage",
            data={"stage": "Check", "person_id": checker_id},
            follow_redirects=True,
        )
        assert 'class="stage">Check' in checked.text, checked.text
        blocked = client.post(
            f"/features/{feature_id}/stage",
            data={"stage": "Ship", "person_id": dev_id},
            follow_redirects=True,
        )
        assert blocked.status_code == 422
        assert "That move is blocked until a person approves it." in blocked.text
        policy_id = blocked.text.split('name="policy_id" value="', 1)[1].split('"', 1)[0]
        approved = client.post(
            f"/features/{feature_id}/policy-approval",
            data={"policy_id": policy_id, "person_id": dev_id},
            follow_redirects=False,
        )
        assert approved.status_code == 303
        shipped = client.post(
            f"/features/{feature_id}/stage",
            data={"stage": "Ship", "person_id": dev_id},
            follow_redirects=True,
        )
        assert 'class="stage">Ship' in shipped.text, shipped.text
        recorded = client.post(
            f"/features/{feature_id}/agent-action",
            data={
                "action": "scored the sample",
                "actor_name": "picker-agent",
                "before_text": "draft",
                "after_text": "scored",
            },
            follow_redirects=True,
        )
        assert recorded.status_code == 200
        assert "person Dev" in recorded.text
        assert "person Checker" in recorded.text
        assert "warning" in recorded.text
        assert "agent picker-agent scored the sample draft scored" in recorded.text
        saved = client.post(
            f"/features/{feature_id}/criteria",
            data={
                "measure_name": "accuracy",
                "threshold": "0.9",
                "dataset_label": "held-out",
                "latency_target": "200ms",
            },
            follow_redirects=True,
        )
        assert 'class="criterion">accuracy 0.9 held-out 200ms<' in saved.text
        reloaded = client.get(f"/features/{feature_id}")
        assert 'class="criterion">accuracy 0.9 held-out 200ms<' in reloaded.text
