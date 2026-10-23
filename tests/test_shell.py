import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.db import ADMIN_DISPLAY_NAME, ADMIN_PASSWORD, ADMIN_USERNAME
from app.main import create_app
from app.settings import Settings


def _settings(path: Path) -> Settings:
    return Settings(database_path=path, session_secret="test-session-secret")


def _client(path: Path) -> TestClient:
    return TestClient(create_app(_settings(path)))


def test_page_shell_says_the_app_is_up(tmp_path: Path):
    with _client(tmp_path / "app.sqlite") as client:
        response = client.get("/sign-in")
        assert response.status_code == 200
        assert "AgilePulse is up." in response.text
        assert 'src="/static/htmx.min.js"' in response.text
        assert 'src="/static/alpine.min.js"' in response.text
        assert "Static shell" not in response.text
        assert 'href="/static/app.css"' in response.text
        stylesheet = client.get("/static/app.css")
        assert stylesheet.status_code == 200
        assert "--brand:" in stylesheet.text
        htmx = client.get("/static/htmx.min.js")
        alpine = client.get("/static/alpine.min.js")
        assert htmx.status_code == 200
        assert alpine.status_code == 200
        assert "htmx" in htmx.text
        assert "Alpine" in alpine.text


def test_sqlite_is_created_and_kept_across_startups(tmp_path: Path):
    first_path = tmp_path / "kept.sqlite"
    with _client(first_path):
        pass
    assert first_path.exists()

    with sqlite3.connect(first_path) as connection:
        connection.execute(
            "UPDATE users SET display_name = ? WHERE username = ?",
            ("Kept", ADMIN_USERNAME),
        )
        versions = connection.execute(
            "SELECT version FROM schema_migrations"
        ).fetchall()
        assert versions == [(1,), (2,), (3,), (4,), (5,), (6,), (7,), (8,)]

    with _client(first_path):
        pass
    with sqlite3.connect(first_path) as connection:
        name = connection.execute(
            "SELECT display_name FROM users WHERE username = ?",
            (ADMIN_USERNAME,),
        ).fetchone()
        count = connection.execute("SELECT COUNT(*) FROM users").fetchone()
    assert name == ("Kept",)
    assert count == (1,)

    fresh_path = tmp_path / "fresh.sqlite"
    with _client(fresh_path):
        pass
    assert fresh_path.exists()
    assert fresh_path.read_bytes() != first_path.read_bytes()


def test_local_user_session(tmp_path: Path):
    with _client(tmp_path / "session.sqlite") as client:
        empty = client.post("/sign-in", data={"username": "", "password": ""})
        assert empty.status_code == 422
        assert "Sign-in was refused." in empty.text

        wrong = client.post(
            "/sign-in",
            data={"username": ADMIN_USERNAME, "password": "nope"},
        )
        assert wrong.status_code == 401
        assert "Sign-in was refused." in wrong.text

        signed_in = client.post(
            "/sign-in",
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            follow_redirects=False,
        )
        assert signed_in.status_code == 303
        assert signed_in.headers["location"] == "/"

        home = client.get("/")
        assert home.status_code == 200
        assert f"Signed in as {ADMIN_DISPLAY_NAME}." in home.text

        client.post("/sign-out", follow_redirects=False)
        after = client.get("/", follow_redirects=False)
        assert after.status_code == 303
        assert after.headers["location"] == "/sign-in"


def test_empty_home_survives_a_new_process(tmp_path: Path):
    database = tmp_path / "home.sqlite"
    with _client(database) as first:
        first.post(
            "/sign-in",
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        )
        page = first.get("/")
        assert "Nothing here yet." in page.text
        assert f"Signed in as {ADMIN_DISPLAY_NAME}." in page.text

    with _client(database) as second:
        signed_out = second.get("/", follow_redirects=False)
        assert signed_out.status_code == 303
        assert signed_out.headers["location"] == "/sign-in"
        second.post(
            "/sign-in",
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        )
        again = second.get("/")
        assert "Nothing here yet." in again.text
        assert f"Signed in as {ADMIN_DISPLAY_NAME}." in again.text


def test_shell_against_temporary_database(tmp_path: Path):
    database = tmp_path / "temp.sqlite"
    assert not database.exists()
    with _client(database) as client:
        assert database.exists()
        client.post(
            "/sign-in",
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        )
        home = client.get("/")
        assert home.status_code == 200
        assert "Nothing here yet." in home.text
        assert f"Signed in as {ADMIN_DISPLAY_NAME}." in home.text


def test_product_setup_replaces_admin_password(tmp_path: Path):
    settings = Settings(
        database_path=tmp_path / "setup.sqlite",
        session_secret="test-session-secret",
        require_admin_setup=True,
    )
    with TestClient(create_app(settings)) as client:
        signed_in = client.post(
            "/sign-in",
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            follow_redirects=False,
        )
        assert signed_in.status_code == 303
        assert signed_in.headers["location"] == "/setup/password"
        blocked = client.get("/", follow_redirects=False)
        assert blocked.status_code == 303
        assert blocked.headers["location"] == "/setup/password"

        kept = client.post(
            "/setup/password",
            data={"password": ADMIN_PASSWORD, "password_again": ADMIN_PASSWORD},
        )
        assert kept.status_code == 422
        assert "Choose a password other than admin." in kept.text

        changed = client.post(
            "/setup/password",
            data={"password": "warehouse", "password_again": "warehouse"},
            follow_redirects=False,
        )
        assert changed.status_code == 303
        assert changed.headers["location"] == "/setup/user"

        still_blocked = client.get("/", follow_redirects=False)
        assert still_blocked.headers["location"] == "/setup/user"
        added = client.post("/setup/user", data={"name": "Ada"}, follow_redirects=False)
        assert added.status_code == 303
        assert added.headers["location"] == "/"
        home = client.get("/")
        assert home.status_code == 200
        assert f"Signed in as {ADMIN_DISPLAY_NAME}." in home.text

        client.post("/sign-out")
        refused = client.post(
            "/sign-in",
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        )
        assert refused.status_code == 401
        opened = client.post(
            "/sign-in",
            data={"username": ADMIN_USERNAME, "password": "warehouse"},
            follow_redirects=False,
        )
        assert opened.status_code == 303
        assert opened.headers["location"] == "/"
