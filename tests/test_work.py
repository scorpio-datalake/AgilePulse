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


def test_work_model_links_and_estimates(tmp_path: Path):
    with _client(tmp_path / "work.sqlite") as client:
        signed_out = client.get("/goals/1", follow_redirects=False)
        assert signed_out.status_code == 303
        assert signed_out.headers["location"] == "/sign-in"

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

        empty_goal = client.post("/goals", data={"name": " ", "value_stream_id": stream_id})
        assert empty_goal.status_code == 422
        assert "A name is required." in empty_goal.text

        missing_goal = client.post("/goals", data={"name": "Fewer walking miles"})
        assert missing_goal.status_code == 422
        assert "A goal needs a value stream." in missing_goal.text

        goal_id = _record_id(
            _create(client, "/goals", {"name": "Fewer walking miles", "value_stream_id": stream_id})
        )
        renamed_goal = client.post(
            f"/goals/{goal_id}",
            data={"name": "Shorter walks"},
            follow_redirects=True,
        )
        assert "Shorter walks" in renamed_goal.text
        stream_page = client.get(f"/value-streams/{stream_id}")
        assert "Shorter walks" in stream_page.text
        _create_redirect = client.post(
            f"/goals/{goal_id}",
            data={"name": "Fewer walking miles"},
            follow_redirects=False,
        )
        assert _create_redirect.status_code == 303

        missing_initiative = client.post("/initiatives", data={"name": "Slot the picks"})
        assert missing_initiative.status_code == 422
        assert "An initiative needs a goal." in missing_initiative.text

        initiative_id = _record_id(
            _create(
                client,
                "/initiatives",
                {"name": "Slot the picks", "goal_id": goal_id},
            )
        )
        opened = client.get(f"/initiatives/{initiative_id}")
        assert "Proposed" in opened.text

        empty_initiative = client.post(
            "/initiatives",
            data={"name": " ", "goal_id": goal_id},
        )
        assert empty_initiative.status_code == 422
        assert "A name is required." in empty_initiative.text
        bad_state = client.post(
            f"/initiatives/{initiative_id}/state",
            data={"state": "Building"},
        )
        assert bad_state.status_code == 422
        assert "That state was refused." in bad_state.text

        shaped = client.post(
            f"/initiatives/{initiative_id}/state",
            data={"state": "Shaping"},
            follow_redirects=True,
        )
        assert "Shaping" in shaped.text
        assert "Shaping" in client.get(f"/initiatives/{initiative_id}").text

        missing_feature = client.post(
            "/features",
            data={"name": "Pick path", "kind": "feature"},
        )
        assert missing_feature.status_code == 422
        assert "A feature needs an initiative." in missing_feature.text
        empty_feature = client.post(
            "/features",
            data={"name": " ", "initiative_id": initiative_id, "kind": "feature"},
        )
        assert empty_feature.status_code == 422
        assert "A name is required." in empty_feature.text
        bad_kind = client.post(
            "/features",
            data={"name": "Loose item", "initiative_id": initiative_id, "kind": "spike"},
        )
        assert bad_kind.status_code == 422
        assert "That kind was refused." in bad_kind.text

        feature_id = _record_id(
            _create(
                client,
                "/features",
                {"name": "Pick path", "initiative_id": initiative_id, "kind": "feature"},
            )
        )
        _create(
            client,
            "/features",
            {"name": "Aisle map", "initiative_id": initiative_id, "kind": "platform"},
        )
        _create(
            client,
            "/features",
            {"name": "Which aisle first", "initiative_id": initiative_id, "kind": "experiment"},
        )
        initiative = client.get(f"/initiatives/{initiative_id}")
        assert "Pick path" in initiative.text
        assert "Platform" in initiative.text
        assert "Experiment" in initiative.text
        assert f'href="/goals/{goal_id}"' in initiative.text

        edited_feature = client.post(
            f"/features/{feature_id}",
            data={"name": "Shorter pick path", "kind": "prototype"},
            follow_redirects=True,
        )
        assert "Shorter pick path" in edited_feature.text
        assert "Prototype" in edited_feature.text
        restored = client.post(
            f"/features/{feature_id}",
            data={"name": "Pick path", "kind": "feature"},
            follow_redirects=False,
        )
        assert restored.status_code == 303

        priority = client.post(
            f"/features/{feature_id}/priority",
            data={"value_sooner": "5", "urgency": "3", "risk": "2", "economic_size": "4"},
            follow_redirects=True,
        )
        assert 'name="value_sooner" value="5"' in priority.text
        assert 'name="urgency" value="3"' in priority.text
        assert 'name="risk" value="2"' in priority.text
        assert 'name="economic_size" value="4"' in priority.text
        assert "score" not in priority.text.lower()
        reloaded_priority = client.get(f"/features/{feature_id}")
        assert 'name="urgency" value="3"' in reloaded_priority.text
        refused_priority = client.post(
            f"/features/{feature_id}/priority",
            data={"value_sooner": "5", "urgency": "3", "risk": "2", "economic_size": "0"},
        )
        assert refused_priority.status_code == 422
        assert "Those priority numbers were refused." in refused_priority.text
        empty_priority = client.post(f"/features/{feature_id}/priority", data={})
        assert empty_priority.status_code == 422
        assert "Those priority numbers were refused." in empty_priority.text

        missing_story = client.post("/stories", data={"name": "Show the next bin", "kind": "feature"})
        assert missing_story.status_code == 422
        assert "A story needs a feature." in missing_story.text
        empty_story = client.post(
            "/stories",
            data={"name": " ", "feature_id": feature_id, "kind": "feature"},
        )
        assert empty_story.status_code == 422
        assert "A name is required." in empty_story.text

        story_id = _record_id(
            _create(
                client,
                "/stories",
                {"name": "Show the next bin", "feature_id": feature_id, "kind": "feature"},
            )
        )
        renamed_story = client.post(
            f"/stories/{story_id}",
            data={"name": "Show the following bin", "kind": "platform"},
            follow_redirects=True,
        )
        assert "Show the following bin" in renamed_story.text
        assert "Platform" in renamed_story.text
        client.post(
            f"/stories/{story_id}",
            data={"name": "Show the next bin", "kind": "feature"},
            follow_redirects=False,
        )
        feature = client.get(f"/features/{feature_id}")
        assert "Show the next bin" in feature.text
        assert "New story" in feature.text
        assert f'href="/initiatives/{initiative_id}"' in feature.text
        aisle_id = feature.text.split(">Aisle map<", 1)[0].rsplit('value="', 1)[-1].split('"', 1)[0]
        moved = client.post(
            f"/stories/{story_id}/feature",
            data={"feature_id": aisle_id},
            follow_redirects=True,
        )
        assert "Show the next bin" in moved.text
        assert "Show the next bin" not in client.get(f"/features/{feature_id}").text
        client.post(
            f"/stories/{story_id}/feature",
            data={"feature_id": feature_id},
            follow_redirects=False,
        )
        story_page = client.get(f"/stories/{story_id}")
        assert f'href="/features/{feature_id}"' in story_page.text
        assert f'href="/initiatives/{initiative_id}"' in story_page.text
        assert f'href="/goals/{goal_id}"' in story_page.text
        assert f'href="/value-streams/{stream_id}"' in story_page.text
        assert f'href="/portfolios/{portfolio_id}"' in story_page.text

        sized = client.post(
            f"/teams/{team_id}/sizing",
            data={
                "method": "tshirt",
                "size_xs": "1",
                "size_s": "2",
                "size_m": "3",
                "size_l": "5",
                "size_xl": "8",
            },
            follow_redirects=True,
        )
        assert 'value="3"' in sized.text

        estimated = client.post(
            f"/stories/{story_id}/estimate",
            data={"team_id": team_id, "label": "M", "points": ""},
            follow_redirects=True,
        )
        assert "M is 3" in estimated.text
        changed_sizes = client.post(
            f"/teams/{team_id}/sizing",
            data={
                "method": "tshirt",
                "size_xs": "1",
                "size_s": "2",
                "size_m": "4",
                "size_l": "5",
                "size_xl": "8",
            },
            follow_redirects=True,
        )
        assert 'name="size_m" value="4"' in changed_sizes.text
        assert "M is 3" in client.get(f"/stories/{story_id}").text

        client.post(
            f"/teams/{team_id}/sizing",
            data={
                "method": "points",
                "size_xs": "1",
                "size_s": "2",
                "size_m": "3",
                "size_l": "5",
                "size_xl": "8",
            },
            follow_redirects=False,
        )
        second_id = _record_id(
            _create(
                client,
                "/stories",
                {"name": "Confirm the pick", "feature_id": feature_id, "kind": "feature"},
            )
        )
        pointed = client.post(
            f"/stories/{second_id}/estimate",
            data={"team_id": team_id, "label": "M", "points": "5"},
            follow_redirects=True,
        )
        assert "Estimate: 5" in pointed.text
        assert "M is" not in pointed.text

        still = client.get(f"/stories/{story_id}")
        assert "M is 3" in still.text
        goal = client.get(f"/goals/{goal_id}")
        assert "Slot the picks" in goal.text
        assert f'href="/value-streams/{stream_id}"' in goal.text
