from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import ADMIN_PASSWORD, ADMIN_USERNAME
from app.main import create_app
from app.sample_data import SAMPLE_PASSWORD, SampleAlreadyLoaded, load_sample
from app.settings import Settings


def _client(path: Path) -> TestClient:
    return TestClient(
        create_app(Settings(database_path=path, session_secret="test-session-secret"))
    )


def _sign_in(client: TestClient, username: str, password: str) -> None:
    response = client.post(
        "/sign-in",
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_sample_data_splits_home_by_role(tmp_path: Path):
    database = tmp_path / "sample.sqlite"
    loaded = load_sample(database)
    with pytest.raises(SampleAlreadyLoaded):
        load_sample(database)

    with _client(database) as client:
        _sign_in(client, ADMIN_USERNAME, ADMIN_PASSWORD)
        admin = client.get("/")
        assert "Supply chain" in admin.text
        assert "Storefront" in admin.text
        assert "Warehouse fulfillment" in admin.text
        assert "Checkout experience" in admin.text
        assert "Create portfolio" in admin.text
        portfolio = client.get(f"/portfolios/{loaded['supply_chain_id']}")
        assert 'action="/value-streams"' in portfolio.text
        team = client.get(f"/teams/{loaded['build_id']}")
        assert "Show the next bin" in team.text
        assert "Sprint 2" in team.text
        assert "Record the walking miles" in team.text
        model = client.get(f"/teams/{loaded['model_id']}")
        assert "Sprint 1" in model.text
        assert "Compare travel-time models" in model.text
        assert "Labels are still being printed" in team.text
        assert "The aisle labels are hard to read" in team.text
        assert 'aria-label="Team views"' in team.text

        client.post("/sign-out", follow_redirects=False)
        _sign_in(client, "dev", SAMPLE_PASSWORD)
        developer = client.get("/")
        assert "2 projects" in developer.text
        assert "3 sprints" in developer.text
        assert "Build crew" in developer.text
        assert "Sprint 2" in developer.text
        assert "Picker week" in developer.text
        assert "Model crew" in developer.text
        assert "Create portfolio" not in developer.text
        refused = client.post(
            "/value-streams",
            data={"name": "Nope", "portfolio_id": str(loaded["supply_chain_id"])},
        )
        assert refused.status_code == 422
        assert "That action was refused." in refused.text

        client.post("/sign-out", follow_redirects=False)
        _sign_in(client, "owen", SAMPLE_PASSWORD)
        crew = client.get("/")
        assert "Choose who from the organization joins a team" in crew.text
        assert "Create portfolio" not in crew.text
        placed = client.post(
            "/crew",
            data={
                "person_id": str(loaded["rio_id"]),
                "team_id": str(loaded["build_id"]),
                "role": "team_member",
            },
            follow_redirects=True,
        )
        assert "Rio Alvarez" in placed.text
        assert 'class="seat">Team member' in placed.text

        client.post("/sign-out", follow_redirects=False)
        _sign_in(client, "lea", SAMPLE_PASSWORD)
        lea = client.get("/")
        assert "Checkout crew" in lea.text
        assert "Lane week" in lea.text
        assert "1 project" in lea.text
        assert "Model crew" not in lea.text
