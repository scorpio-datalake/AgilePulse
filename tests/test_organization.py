import re
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.db import ADMIN_DISPLAY_NAME, ADMIN_PASSWORD, ADMIN_USERNAME
from app.main import create_app
from app.settings import Settings

RECORD_TABLES = (
    "users",
    "people",
    "portfolios",
    "value_streams",
    "delivery_groups",
    "teams",
    "role_assignments",
)


def _settings(path: Path) -> Settings:
    return Settings(database_path=path, session_secret="test-session-secret")


def _client(path: Path) -> TestClient:
    return TestClient(create_app(_settings(path)))


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


def _person_id(client: TestClient, name: str) -> str:
    page = client.get("/people")
    match = re.search(rf'href="/people/(\d+)">{re.escape(name)}</a>', page.text)
    assert match is not None
    return match.group(1)


def _add_person(client: TestClient, name: str, role: str = "team_member", **fields) -> str:
    return _record_id(_create(client, "/people", {"name": name, "role": role, **fields}))


def _between(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


def _structure(client: TestClient) -> dict[str, str]:
    portfolio_id = _record_id(_create(client, "/portfolios", {"name": "Payments"}))
    stream_id = _record_id(
        _create(
            client,
            "/value-streams",
            {"name": "Checkout", "portfolio_id": portfolio_id},
        )
    )
    group_id = _record_id(
        _create(
            client,
            "/delivery-groups",
            {"name": "Checkout group", "value_stream_id": stream_id},
        )
    )
    team_id = _record_id(
        _create(
            client,
            "/teams",
            {"name": "Lane", "delivery_group_id": group_id},
        )
    )
    return {
        "portfolio_id": portfolio_id,
        "stream_id": stream_id,
        "group_id": group_id,
        "team_id": team_id,
    }


def test_one_organization_is_seeded_once(tmp_path: Path):
    database = tmp_path / "org.sqlite"
    with _client(database):
        pass
    with _client(database):
        pass

    with sqlite3.connect(database) as connection:
        organizations = connection.execute("SELECT id, name FROM organizations").fetchall()
        user = connection.execute(
            "SELECT organization_id FROM users WHERE username = ?",
            (ADMIN_USERNAME,),
        ).fetchone()
    assert len(organizations) == 1
    assert user is not None
    assert user[0] == organizations[0][0]


def test_portfolio_can_be_created_and_renamed(tmp_path: Path):
    with _client(tmp_path / "portfolio.sqlite") as client:
        for path in ("/", "/people", "/portfolios/1"):
            signed_out = client.get(path, follow_redirects=False)
            assert signed_out.status_code == 303
            assert signed_out.headers["location"] == "/sign-in"
        refused_post = client.post("/portfolios", data={"name": "Payments"}, follow_redirects=False)
        assert refused_post.status_code == 303
        assert refused_post.headers["location"] == "/sign-in"

        _sign_in(client)
        empty = client.post("/portfolios", data={"name": " "})
        assert empty.status_code == 422
        assert "A name is required." in empty.text

        portfolio_id = _record_id(_create(client, "/portfolios", {"name": "Payments"}))
        renamed = client.post(
            f"/portfolios/{portfolio_id}",
            data={"name": "Payments desk"},
            follow_redirects=True,
        )
        assert renamed.status_code == 200
        assert "Payments desk" in renamed.text
        assert 'value="Payments desk"' in renamed.text

        home = client.get("/")
        assert "Payments desk" in home.text
        assert f"Signed in as {ADMIN_DISPLAY_NAME}." in home.text


def test_value_stream_stays_under_its_portfolio(tmp_path: Path):
    with _client(tmp_path / "stream.sqlite") as client:
        _sign_in(client)
        portfolio_id = _record_id(_create(client, "/portfolios", {"name": "Payments"}))

        empty = client.post(
            "/value-streams",
            data={"name": " ", "portfolio_id": portfolio_id},
        )
        assert empty.status_code == 422
        assert "A name is required." in empty.text

        missing = client.post("/value-streams", data={"name": "Checkout"})
        assert missing.status_code == 422
        assert "A value stream needs a portfolio." in missing.text

        unknown = client.post(
            "/value-streams",
            data={"name": "Checkout", "portfolio_id": "999"},
        )
        assert unknown.status_code == 422
        assert "A value stream needs a portfolio." in unknown.text

        stream_id = _record_id(
            _create(
                client,
                "/value-streams",
                {"name": "Checkout", "portfolio_id": portfolio_id},
            )
        )
        renamed = client.post(
            f"/value-streams/{stream_id}",
            data={"name": "Checkout flow"},
            follow_redirects=True,
        )
        assert "Checkout flow" in renamed.text

        portfolio = client.get(f"/portfolios/{portfolio_id}")
        assert f'href="/value-streams/{stream_id}"' in portfolio.text
        assert "Checkout flow" in portfolio.text


def test_delivery_group_saves_with_no_facilitator(tmp_path: Path):
    with _client(tmp_path / "group.sqlite") as client:
        _sign_in(client)
        created = _structure(client)
        group = client.get(f"/delivery-groups/{created['group_id']}")
        assert "Facilitator seat is empty." in group.text
        assert "Checkout group" in group.text

        renamed = client.post(
            f"/delivery-groups/{created['group_id']}",
            data={"name": "Checkout lane"},
            follow_redirects=True,
        )
        assert "Checkout lane" in renamed.text
        assert "Facilitator seat is empty." in renamed.text

        stream = client.get(f"/value-streams/{created['stream_id']}")
        assert "Checkout lane" in stream.text


def test_team_name_is_whatever_the_shop_calls_it(tmp_path: Path):
    with _client(tmp_path / "team.sqlite") as client:
        _sign_in(client)
        created = _structure(client)
        team = client.get(f"/teams/{created['team_id']}")
        assert "Lane" in team.text
        assert 'name="name"' in team.text
        for phrase in (
            "site-reliability",
            "database team",
            "network team",
            "firewall team",
        ):
            assert phrase not in team.text

        renamed = client.post(
            f"/teams/{created['team_id']}",
            data={"name": "Counter"},
            follow_redirects=True,
        )
        assert "Counter" in renamed.text
        assert 'value="Counter"' in renamed.text

        group = client.get(f"/delivery-groups/{created['group_id']}")
        assert "Counter" in group.text


def test_people_include_the_local_user(tmp_path: Path):
    with _client(tmp_path / "people.sqlite") as client:
        _sign_in(client)
        people = client.get("/people")
        assert ADMIN_DISPLAY_NAME in people.text

        empty = client.post("/people", data={"name": " "})
        assert empty.status_code == 422
        assert "A name is required." in empty.text

        person_id = _add_person(client, "Avery")
        renamed = client.post(
            f"/people/{person_id}",
            data={"name": "Avery Cole"},
            follow_redirects=True,
        )
        assert "Avery Cole" in renamed.text

        again = client.get("/people")
        assert "Avery Cole" in again.text
        assert ADMIN_DISPLAY_NAME in again.text


def test_person_can_join_a_team_when_created(tmp_path: Path):
    with _client(tmp_path / "assign-team.sqlite") as client:
        _sign_in(client)
        before = client.get("/people")
        assert 'name="team_id"' not in before.text

        created = _structure(client)
        people = client.get("/people")
        assert 'name="team_id"' in people.text
        assert '<option value="">None</option>' in people.text
        assert f'value="{created["team_id"]}"' in people.text

        _add_person(client, "Avery")
        team = client.get(f"/teams/{created['team_id']}")
        assert "Avery" not in _between(team.text, "<h2>Members</h2>", "<h2>Add a member</h2>")

        _add_person(client, "Bo", team_id=created["team_id"])
        team = client.get(f"/teams/{created['team_id']}")
        assert "Bo" in _between(team.text, "<h2>Members</h2>", "<h2>Add a member</h2>")

        missing = client.post(
            "/people",
            data={"name": "Ghost", "role": "team_member", "team_id": "999"},
        )
        assert missing.status_code == 422
        assert "That team was not found." in missing.text
        assert "Ghost" not in client.get("/people").text


def test_membership_can_be_added_and_removed(tmp_path: Path):
    with _client(tmp_path / "members.sqlite") as client:
        _sign_in(client)
        created = _structure(client)
        person_id = _add_person(client, "Avery")
        assert (
            client.post(
                f"/teams/{created['team_id']}/members",
                data={"person_id": person_id},
                follow_redirects=False,
            ).status_code
            == 303
        )
        assert (
            client.post(
                f"/delivery-groups/{created['group_id']}/members",
                data={"person_id": person_id},
                follow_redirects=False,
            ).status_code
            == 303
        )

        team = client.get(f"/teams/{created['team_id']}")
        group = client.get(f"/delivery-groups/{created['group_id']}")
        assert "Avery" in _between(team.text, "<h2>Members</h2>", "<h2>Add a member</h2>")
        assert "Avery" in _between(group.text, "<h2>Members</h2>", "<h2>Add a member</h2>")

        match = re.search(r'action="/memberships/(\d+)/remove"', team.text)
        assert match is not None
        removed = client.post(f"/memberships/{match.group(1)}/remove", follow_redirects=True)
        assert removed.status_code == 200

        team = client.get(f"/teams/{created['team_id']}")
        group = client.get(f"/delivery-groups/{created['group_id']}")
        assert "Avery" not in _between(team.text, "<h2>Members</h2>", "<h2>Add a member</h2>")
        assert "Avery" in _between(group.text, "<h2>Members</h2>", "<h2>Add a member</h2>")


def test_one_role_per_person_on_the_matching_record(tmp_path: Path):
    with _client(tmp_path / "roles.sqlite") as client:
        _sign_in(client)
        created = _structure(client)
        people = {
            "stream_owner": _add_person(
                client, "Rhea", "stream_owner", value_stream_id=created["stream_id"]
            ),
            "group_facilitator": _add_person(
                client,
                "Ned",
                "group_facilitator",
                delivery_group_id=created["group_id"],
            ),
            "product_manager": _add_person(
                client, "Pat", "product_manager", delivery_group_id=created["group_id"]
            ),
            "business_stakeholder": _add_person(
                client,
                "Kim",
                "business_stakeholder",
                delivery_group_id=created["group_id"],
            ),
            "product_owner": _add_person(client, "Ada", "product_owner"),
            "scrum_master": _add_person(client, "Bo", "scrum_master"),
            "technical_lead": _add_person(client, "Lux", "technical_lead"),
            "team_member": _add_person(client, "Cam", "team_member"),
        }
        labels = {
            "stream_owner": "Stream owner",
            "group_facilitator": "Group facilitator",
            "product_manager": "Product manager",
            "business_stakeholder": "Business stakeholder",
            "product_owner": "Product owner",
            "scrum_master": "Scrum master",
            "technical_lead": "Technical lead",
            "team_member": "Team member",
        }
        pages = {
            "stream_owner": f"/value-streams/{created['stream_id']}",
            "group_facilitator": f"/delivery-groups/{created['group_id']}",
            "product_manager": f"/delivery-groups/{created['group_id']}",
            "business_stakeholder": f"/delivery-groups/{created['group_id']}",
        }
        for role, person_name in (
            ("stream_owner", "Rhea"),
            ("group_facilitator", "Ned"),
            ("product_manager", "Pat"),
            ("business_stakeholder", "Kim"),
        ):
            page = client.get(pages[role])
            assert f"{labels[role]}: {person_name}" in page.text
        directory = client.get("/people")
        for role, person_name in (
            ("product_owner", "Ada"),
            ("scrum_master", "Bo"),
            ("technical_lead", "Lux"),
            ("team_member", "Cam"),
        ):
            assert person_name in directory.text
            assert labels[role] in directory.text

        second = client.post(
            "/roles",
            data={
                "role": "scrum_master",
                "person_id": people["product_owner"],
                "team_id": created["team_id"],
            },
        )
        assert second.status_code == 422
        assert "That person already has a role." in second.text
        ada = client.get(f"/people/{people['product_owner']}")
        assert "Product owner" in ada.text

        wrong = client.post(
            "/roles",
            data={
                "role": "stream_owner",
                "person_id": _add_person(client, "Noor"),
                "team_id": created["team_id"],
            },
        )
        assert wrong.status_code == 422
        assert "That role does not belong on this record." in wrong.text


def test_structure_survives_a_new_process(tmp_path: Path):
    database = tmp_path / "structure.sqlite"
    with _client(database) as client:
        _sign_in(client)
        created = _structure(client)
        _add_person(client, "Ada", "product_owner")
        _add_person(client, "Bo", "scrum_master")

    with _client(database) as client:
        _sign_in(client)
        home = client.get("/")
        assert "Payments" in home.text
        portfolio = client.get(f"/portfolios/{created['portfolio_id']}")
        assert "Checkout" in portfolio.text
        stream = client.get(f"/value-streams/{created['stream_id']}")
        assert "Checkout group" in stream.text
        group = client.get(f"/delivery-groups/{created['group_id']}")
        assert "Lane" in group.text
        assert "Facilitator seat is empty." in group.text
        people = client.get("/people")
        assert "Ada" in people.text
        assert "Product owner" in people.text
        assert "Bo" in people.text
        assert "Scrum master" in people.text

    with sqlite3.connect(database) as connection:
        organization_ids = {
            row[0] for row in connection.execute("SELECT id FROM organizations")
        }
        assert len(organization_ids) == 1
        organization_id = organization_ids.pop()
        for table in RECORD_TABLES:
            stored = {
                row[0]
                for row in connection.execute(f"SELECT organization_id FROM {table}")
            }
            assert stored == {organization_id}
