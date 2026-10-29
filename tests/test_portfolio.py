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


def _row(page: str, name: str) -> str:
    return next(
        row for row in page.split("<tr>") if f">{name}</a>" in row and 'class="load"' in row
    )


def test_portfolio_investment(tmp_path: Path):
    with _client(tmp_path / "portfolio.sqlite") as client:
        _sign_in(client)
        portfolio_id = _record_id(_create(client, "/portfolios", {"name": "Supply chain"}))
        stream_id = _record_id(
            _create(
                client,
                "/value-streams",
                {"name": "Warehouse fulfillment", "portfolio_id": portfolio_id},
            )
        )
        other_stream_id = _record_id(
            _create(
                client,
                "/value-streams",
                {"name": "Checkout experience", "portfolio_id": portfolio_id},
            )
        )
        goal_id = _record_id(
            _create(client, "/goals", {"name": "Fewer walking miles", "value_stream_id": stream_id})
        )
        other_goal_id = _record_id(
            _create(
                client,
                "/goals",
                {"name": "Shorter lanes", "value_stream_id": other_stream_id},
            )
        )
        initiative_ids = [
            _record_id(_create(client, "/initiatives", {"name": name, "goal_id": goal_id}))
            for name in ("One", "Two", "Three", "Four", "Five")
        ]
        other_initiative_id = _record_id(
            _create(client, "/initiatives", {"name": "Lane signs", "goal_id": other_goal_id})
        )
        ada_id = _record_id(
            _create(
                client,
                "/people",
                {"name": "Ada", "role": "stream_owner", "value_stream_id": stream_id},
            )
        )
        bea_id = _record_id(
            _create(
                client,
                "/people",
                {"name": "Bea", "role": "stream_owner", "value_stream_id": other_stream_id},
            )
        )

        saved = client.post(
            "/guardrails",
            data={"value_stream_id": stream_id, "kind": "capacity", "amount": "4"},
            follow_redirects=True,
        )
        assert saved.status_code == 200
        assert 'class="guardrail">capacity 4' in saved.text

        refused_amount = client.post(
            "/guardrails",
            data={"value_stream_id": stream_id, "kind": "budget", "amount": "0"},
            follow_redirects=True,
        )
        assert refused_amount.status_code == 422
        assert "That guardrail was refused." in refused_amount.text
        refused_kind = client.post(
            "/guardrails",
            data={"value_stream_id": stream_id, "kind": "headcount", "amount": "4"},
            follow_redirects=True,
        )
        assert refused_kind.status_code == 422
        assert "That guardrail was refused." in refused_kind.text
        refused_stream = client.post(
            "/guardrails",
            data={"value_stream_id": "", "kind": "budget", "amount": "1"},
            follow_redirects=True,
        )
        assert refused_stream.status_code == 422
        assert "A guardrail needs a value stream." in refused_stream.text
        still = client.get(f"/value-streams/{stream_id}")
        assert 'class="guardrail">capacity 4' in still.text

        empty = client.post(
            "/workshops",
            data={
                "value_stream_id": stream_id,
                "person_id": [ada_id, bea_id],
                "initiative_id": [initiative_ids[0], initiative_ids[1]],
                "amount": ["2", "3"],
                "recommendation": "   ",
            },
            follow_redirects=True,
        )
        assert empty.status_code == 422
        assert "A recommendation is required." in empty.text
        stranger = client.post(
            "/workshops",
            data={
                "value_stream_id": stream_id,
                "person_id": ["999999"],
                "initiative_id": [initiative_ids[0]],
                "amount": ["2"],
                "recommendation": "Invite someone on the roster.",
            },
            follow_redirects=True,
        )
        assert stranger.status_code == 422
        assert "That person is not in the organization." in stranger.text
        other_stream = client.post(
            "/workshops",
            data={
                "value_stream_id": stream_id,
                "person_id": [ada_id, bea_id],
                "initiative_id": [other_initiative_id],
                "amount": ["2"],
                "recommendation": "Spend it on the other stream.",
            },
            follow_redirects=True,
        )
        assert other_stream.status_code == 422
        assert "That initiative is on another stream." in other_stream.text
        assert "Spend it on the other stream." not in client.get(f"/value-streams/{stream_id}").text

        recommendation = "Keep four in flight and pause the fifth."
        recorded = client.post(
            "/workshops",
            data={
                "value_stream_id": stream_id,
                "person_id": [ada_id, bea_id],
                "initiative_id": initiative_ids,
                "amount": ["2", "3", "", "", ""],
                "recommendation": recommendation,
            },
            follow_redirects=True,
        )
        assert recorded.status_code == 200, recorded.text
        assert 'class="participant">Ada' in recorded.text
        assert 'class="participant">Bea' in recorded.text
        assert 'class="allocation">One 2' in recorded.text
        assert 'class="allocation">Two 3' in recorded.text
        assert recommendation in recorded.text
        assert 'class="guardrail">capacity 4' in recorded.text
        one = client.get(f"/initiatives/{initiative_ids[0]}")
        assert "<p>Proposed</p>" in one.text

        portfolio = client.get(f"/portfolios/{portfolio_id}")
        warehouse = _row(portfolio.text, "Warehouse fulfillment")
        checkout = _row(portfolio.text, "Checkout experience")
        assert "capacity 4" in warehouse
        assert "load 5" in warehouse
        assert 'class="over"' in warehouse
        assert recommendation in warehouse
        assert "no guardrail" in checkout
        assert "load 1" in checkout
        assert "over" not in checkout
        assert 'name="state"' not in portfolio.text

        done = client.post(
            f"/initiatives/{initiative_ids[4]}/state",
            data={"state": "Done"},
            follow_redirects=False,
        )
        assert done.status_code == 303
        reloaded = client.get(f"/portfolios/{portfolio_id}")
        warehouse = _row(reloaded.text, "Warehouse fulfillment")
        assert "load 4" in warehouse
        assert "over" not in warehouse
        assert recommendation in warehouse
        assert "<p>Done</p>" in client.get(f"/initiatives/{initiative_ids[4]}").text
