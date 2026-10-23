from pathlib import Path

from fastapi.testclient import TestClient

from app.db import ADMIN_PASSWORD, ADMIN_USERNAME, attach_login, connect
from app.main import create_app
from app.settings import Settings

HIDDEN = "That record is not available."


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


def _open_as(client: TestClient, path: Path, person_id: str, username: str) -> None:
    session = connect(path)
    try:
        attach_login(session, int(person_id), username, "member-pass")
    finally:
        session.close()
    client.post("/sign-out", follow_redirects=False)
    signed_in = client.post(
        "/sign-in",
        data={"username": username, "password": "member-pass"},
        follow_redirects=False,
    )
    assert signed_in.status_code == 303


def _chain(client: TestClient, portfolio: str, stream: str, group: str, team: str) -> dict:
    portfolio_id = _record_id(_create(client, "/portfolios", {"name": portfolio}))
    stream_id = _record_id(
        _create(client, "/value-streams", {"name": stream, "portfolio_id": portfolio_id})
    )
    group_id = _record_id(
        _create(client, "/delivery-groups", {"name": group, "value_stream_id": stream_id})
    )
    team_id = _record_id(_create(client, "/teams", {"name": team, "delivery_group_id": group_id}))
    return {"stream_id": stream_id, "group_id": group_id, "team_id": team_id}


def test_group_board_features_and_plan_stay_with_members(tmp_path: Path):
    database = tmp_path / "group-visibility.sqlite"
    with _client(database) as client:
        _sign_in(client)
        warehouse = _chain(client, "Supply chain", "Warehouse fulfillment", "Warehouse", "Build crew")
        other = _chain(client, "Other portfolio", "Other stream", "Other group", "Other crew")
        goal_id = _record_id(
            _create(client, "/goals", {"name": "Fewer miles", "value_stream_id": warehouse["stream_id"]})
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
        cycle_id = _record_id(
            _create(
                client,
                "/cycles",
                {
                    "name": "Warehouse cycle",
                    "starts_on": "2026-10-05",
                    "ends_on": "2026-11-16",
                    "delivery_group_id": warehouse["group_id"],
                },
            )
        )
        iteration_id = _record_id(
            _create(
                client,
                "/iterations",
                {
                    "name": "Week one",
                    "starts_on": "2026-10-06",
                    "ends_on": "2026-10-17",
                    "team_id": warehouse["team_id"],
                    "cycle_id": cycle_id,
                },
            )
        )
        member_id = _record_id(
            _create(
                client,
                "/people",
                {"name": "Ada", "role": "team_member", "team_id": warehouse["team_id"]},
            )
        )
        outsider_id = _record_id(
            _create(
                client,
                "/people",
                {"name": "Bea", "role": "team_member", "team_id": other["team_id"]},
            )
        )
        seated_id = _record_id(
            _create(
                client,
                "/people",
                {
                    "name": "Cara",
                    "role": "group_facilitator",
                    "delivery_group_id": warehouse["group_id"],
                },
            )
        )
        addresses = (f"/iterations/{iteration_id}", f"/features/{feature_id}", f"/cycles/{cycle_id}")

        _open_as(client, database, member_id, "ada")
        for address in addresses:
            page = client.get(address)
            assert page.status_code == 200, page.text
            assert HIDDEN not in page.text

        _open_as(client, database, outsider_id, "bea")
        for address in addresses:
            page = client.get(address)
            assert page.status_code == 422
            assert HIDDEN in page.text

        _open_as(client, database, seated_id, "cara")
        for address in addresses:
            page = client.get(address)
            assert page.status_code == 422
            assert HIDDEN in page.text
