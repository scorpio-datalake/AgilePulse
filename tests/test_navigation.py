import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.db import ADMIN_PASSWORD, ADMIN_USERNAME, attach_login, connect
from app.main import create_app
from app.settings import Settings


def _client(path: Path) -> TestClient:
    return TestClient(
        create_app(Settings(database_path=path, session_secret="test-session-secret"))
    )


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


def _sidebar(text: str) -> str:
    return text.split('<nav class="sidebar"', 1)[1].split("</nav>", 1)[0]


def _breadcrumb(text: str) -> str:
    return text.split('aria-label="Breadcrumb"', 1)[1].split("</nav>", 1)[0]


def test_sidebar_marks_the_signed_in_page(tmp_path: Path):
    with _client(tmp_path / "sidebar.sqlite") as client:
        sign_in = client.get("/sign-in")
        assert '<nav class="sidebar"' not in sign_in.text

        _sign_in(client)
        home = client.get("/")
        assert '<a href="/" aria-current="page">Home</a>' in _sidebar(home.text)
        assert 'aria-current="page">People</a>' not in _sidebar(home.text)

        people = client.get("/people")
        assert '<a href="/people" aria-current="page">People</a>' in _sidebar(people.text)
        assert '<a href="/" aria-current="page">' not in _sidebar(people.text)
        assert 'aria-label="Breadcrumb"' not in people.text
        assert 'aria-label="Breadcrumb"' not in home.text

        client.post("/sign-out", follow_redirects=False)
        signed_out = client.get("/sign-in")
        assert '<nav class="sidebar"' not in signed_out.text


def test_tree_lists_a_saved_record(tmp_path: Path):
    with _client(tmp_path / "tree.sqlite") as client:
        _sign_in(client)
        portfolio_id = _record_id(_create(client, "/portfolios", {"name": "Supply chain"}))
        portfolio = client.get(f"/portfolios/{portfolio_id}")
        sidebar = _sidebar(portfolio.text)
        assert f'href="/portfolios/{portfolio_id}" aria-current="page"' in sidebar
        assert "Supply chain" in sidebar

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
            _create(
                client,
                "/teams",
                {"name": "Build crew", "delivery_group_id": group_id},
            )
        )
        team = client.get(f"/teams/{team_id}")
        sidebar = _sidebar(team.text)
        assert f'href="/portfolios/{portfolio_id}"' in sidebar
        assert f'href="/value-streams/{stream_id}"' in sidebar
        assert f'href="/delivery-groups/{group_id}"' in sidebar
        assert f'href="/teams/{team_id}" aria-current="page"' in sidebar
        assert "Build crew" in sidebar


def test_breadcrumb_links_every_ancestor(tmp_path: Path):
    with _client(tmp_path / "crumb.sqlite") as client:
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
            _create(
                client,
                "/teams",
                {"name": "Build crew", "delivery_group_id": group_id},
            )
        )
        team = client.get(f"/teams/{team_id}")
        crumb = _breadcrumb(team.text)
        assert f'href="/portfolios/{portfolio_id}">Supply chain</a>' in crumb
        assert f'href="/value-streams/{stream_id}">Warehouse fulfillment</a>' in crumb
        assert f'href="/delivery-groups/{group_id}">Optimization of the warehouse</a>' in crumb
        assert f'href="/teams/{team_id}"' not in crumb
        assert "<span>Build crew</span>" in crumb

        group = client.get(f"/delivery-groups/{group_id}")
        stream = client.get(f"/value-streams/{stream_id}")
        portfolio = client.get(f"/portfolios/{portfolio_id}")
        assert "Optimization of the warehouse" in _breadcrumb(group.text)
        assert f'href="/portfolios/{portfolio_id}"' in _breadcrumb(stream.text)
        assert "<span>Supply chain</span>" in _breadcrumb(portfolio.text)
        assert 'href="' not in _breadcrumb(portfolio.text)


def test_empty_record_offers_the_next_form(tmp_path: Path):
    with _client(tmp_path / "next.sqlite") as client:
        _sign_in(client)
        portfolio_id = _record_id(_create(client, "/portfolios", {"name": "Supply chain"}))
        portfolio = client.get(f"/portfolios/{portfolio_id}")
        assert 'action="/value-streams"' in portfolio.text
        assert f'name="portfolio_id" value="{portfolio_id}"' in portfolio.text

        stream_id = _record_id(
            _create(
                client,
                "/value-streams",
                {"name": "Warehouse fulfillment", "portfolio_id": portfolio_id},
            )
        )
        stream = client.get(f"/value-streams/{stream_id}")
        assert 'action="/delivery-groups"' in stream.text
        assert "Warehouse fulfillment" in _sidebar(stream.text)

        group_id = _record_id(
            _create(
                client,
                "/delivery-groups",
                {"name": "Optimization of the warehouse", "value_stream_id": stream_id},
            )
        )
        group = client.get(f"/delivery-groups/{group_id}")
        assert 'action="/teams"' in group.text

        team_id = _record_id(
            _create(
                client,
                "/teams",
                {"name": "Build crew", "delivery_group_id": group_id},
            )
        )
        opened = client.get(f"/teams/{team_id}")
        assert opened.status_code == 200
        assert "Build crew" in _sidebar(opened.text)


def test_members_and_roles_come_before_rename(tmp_path: Path):
    with _client(tmp_path / "order.sqlite") as client:
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
            _create(
                client,
                "/teams",
                {"name": "Build crew", "delivery_group_id": group_id},
            )
        )
        team = client.get(f"/teams/{team_id}").text
        assert team.index("<h2>Members</h2>") < team.index("Save team")
        assert 'action="/roles"' not in team
        assert 'href="/people"' in _sidebar(team)

        group = client.get(f"/delivery-groups/{group_id}").text
        assert group.index("<h2>Members</h2>") < group.index("Save delivery group")
        assert 'action="/roles"' not in group
        assert 'href="/people"' in _sidebar(group)


def test_navigation_reads_sidebar_and_breadcrumb(tmp_path: Path):
    with _client(tmp_path / "navigation.sqlite") as client:
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
        team_location = _create(
            client,
            "/teams",
            {"name": "Build crew", "delivery_group_id": group_id},
        )
        team = client.get(team_location)
        sidebar = _sidebar(team.text)
        crumb = _breadcrumb(team.text)
        assert "Supply chain" in sidebar
        assert "Warehouse fulfillment" in sidebar
        assert "Optimization of the warehouse" in sidebar
        assert 'aria-current="page"' in sidebar
        assert "Build crew" in sidebar
        assert re.search(r'href="/portfolios/\d+">Supply chain</a>', crumb)
        assert re.search(r'href="/value-streams/\d+">Warehouse fulfillment</a>', crumb)
        assert re.search(
            r'href="/delivery-groups/\d+">Optimization of the warehouse</a>',
            crumb,
        )
        assert "<span>Build crew</span>" in crumb
        assert "http://" not in team.text
        assert "https://" not in team.text


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


def test_shell_header_and_access(tmp_path: Path):
    database = tmp_path / "shell.sqlite"
    with _client(database) as client:
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
        other_id = _record_id(_create(client, "/portfolios", {"name": "Other portfolio"}))
        other_stream = _record_id(
            _create(
                client,
                "/value-streams",
                {"name": "Other stream", "portfolio_id": other_id},
            )
        )
        home = client.get("/")
        assert "Static shell" not in home.text
        assert 'href="/static/app.css"' in home.text
        assert 'class="primary"' in home.text
        stylesheet = client.get("/static/app.css").text
        assert "max-width: 36rem" not in stylesheet
        assert 'a[aria-current="page"]' in stylesheet

        team = client.get(f"/teams/{team_id}").text
        assert 'class="record-header"' in team
        assert 'class="record-type">Team' in team
        assert 'aria-label="Breadcrumb"' in team
        assert 'class="members"' in team
        assert f'href="/teams/{team_id}" aria-current="page"' in _sidebar(team)

        person_id = _record_id(
            _create(client, "/people", {"name": "Ada", "role": "product_owner"})
        )
        added = client.post(
            f"/teams/{team_id}/members",
            data={"person_id": person_id},
            follow_redirects=True,
        )
        assert "Ada" in added.text
        assert "Product owner" in added.text

        _open_as(client, database, person_id, "ada")
        renamed = client.post(
            f"/teams/{team_id}",
            data={"name": "Counter"},
            follow_redirects=True,
        )
        assert renamed.status_code == 200
        assert 'value="Counter"' in renamed.text

        client.post("/sign-out", follow_redirects=False)
        _sign_in(client)
        viewer = client.post(
            f"/people/{person_id}/access",
            data={"account_access": "viewer"},
            follow_redirects=True,
        )
        assert "Viewer" in viewer.text
        _open_as(client, database, person_id, "ada-viewer")
        refused = client.post(
            f"/teams/{team_id}",
            data={"name": "Other"},
            follow_redirects=True,
        )
        assert "That action was refused." in refused.text
        assert 'value="Counter"' in refused.text
        assert 'value="Other"' not in refused.text

        client.post("/sign-out", follow_redirects=False)
        _sign_in(client)
        owner_id = _record_id(
            _create(
                client,
                "/people",
                {"name": "Rhea", "role": "stream_owner", "value_stream_id": other_stream},
            )
        )
        client.post(
            f"/teams/{team_id}/members",
            data={"person_id": owner_id},
            follow_redirects=False,
        )
        _open_as(client, database, owner_id, "rhea")
        sidebar = _sidebar(client.get("/").text)
        assert "Supply chain" in sidebar
        assert "Counter" in sidebar
        assert "Other portfolio" not in sidebar
