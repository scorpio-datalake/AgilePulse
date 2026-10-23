import re
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db import ADMIN_PASSWORD, ADMIN_USERNAME, connect
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


def _person(client: TestClient, name: str, role: str, **extra) -> str:
    return _record_id(_create(client, "/people", {"name": name, "role": role, **extra}))


def _stamp(path: Path, feature_id: str, to_stage: str, stamp: str) -> None:
    session = connect(path)
    try:
        session.execute(
            text(
                "UPDATE stage_changes SET changed_at = :stamp "
                "WHERE target_kind = 'feature' AND target_id = :feature_id AND to_stage = :to_stage"
            ),
            {"stamp": stamp, "feature_id": int(feature_id), "to_stage": to_stage},
        )
        session.commit()
    finally:
        session.close()


def _ship_feature(client: TestClient, feature_id: str, builder: str, checker: str) -> None:
    for stage, person in (("Define", builder), ("Build", builder)):
        moved = client.post(
            f"/features/{feature_id}/stage",
            data={"stage": stage, "person_id": person},
            follow_redirects=True,
        )
        if stage == "Define":
            client.post(
                f"/features/{feature_id}/approval",
                data={"person_id": builder},
                follow_redirects=True,
            )
        assert f'class="stage">{stage}' in moved.text or stage == "Define"
    client.post(
        f"/features/{feature_id}/done-list",
        data={"integrated": "1", "acceptance": "1", "dependency": "1", "rollback": "1"},
        follow_redirects=True,
    )
    checked = client.post(
        f"/features/{feature_id}/stage",
        data={"stage": "Check", "person_id": checker},
        follow_redirects=True,
    )
    assert 'class="stage">Check' in checked.text, checked.text
    shipped = client.post(
        f"/features/{feature_id}/stage",
        data={"stage": "Ship", "person_id": checker},
        follow_redirects=True,
    )
    assert 'class="stage">Ship' in shipped.text, shipped.text


def _reach_build(client: TestClient, feature_id: str, person: str) -> None:
    client.post(
        f"/features/{feature_id}/stage",
        data={"stage": "Define", "person_id": person},
        follow_redirects=True,
    )
    client.post(f"/features/{feature_id}/approval", data={"person_id": person}, follow_redirects=True)
    built = client.post(
        f"/features/{feature_id}/stage",
        data={"stage": "Build", "person_id": person},
        follow_redirects=True,
    )
    assert 'class="stage">Build' in built.text, built.text


def test_flow_and_priority(tmp_path: Path):
    database = tmp_path / "flow.sqlite"
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
        goal_id = _record_id(
            _create(client, "/goals", {"name": "Fewer walking miles", "value_stream_id": stream_id})
        )
        initiative_id = _record_id(
            _create(client, "/initiatives", {"name": "Slot the picks", "goal_id": goal_id})
        )
        fast_id = _record_id(
            _create(
                client,
                "/features",
                {"name": "Fast slot", "initiative_id": initiative_id, "kind": "feature"},
            )
        )
        slow_id = _record_id(
            _create(
                client,
                "/features",
                {"name": "Slow slot", "initiative_id": initiative_id, "kind": "feature"},
            )
        )
        plain_id = _record_id(
            _create(
                client,
                "/features",
                {"name": "Unknown slot", "initiative_id": initiative_id, "kind": "feature"},
            )
        )
        _create(
            client,
            f"/features/{fast_id}/priority",
            {"value_sooner": "8", "urgency": "2", "risk": "0", "economic_size": "2"},
        )
        _create(
            client,
            f"/features/{slow_id}/priority",
            {"value_sooner": "1", "urgency": "1", "risk": "0", "economic_size": "4"},
        )
        initiative = client.get(f"/initiatives/{initiative_id}")
        assert initiative.status_code == 200
        assert initiative.text.index(f"/features/{fast_id}") < initiative.text.index(
            f"/features/{slow_id}"
        )
        assert initiative.text.index(f"/features/{slow_id}") < initiative.text.index(
            f"/features/{plain_id}"
        )
        assert 'class="delay-cost">5<' in initiative.text
        assert 'class="delay-cost">0.5<' in initiative.text
        fast_page = client.get(f"/features/{fast_id}")
        assert 'class="delay-cost">5<' in fast_page.text

        builder = _person(client, "Dev", "team_member", team_id=team_id)
        checker = _person(client, "Checker", "team_member", team_id=team_id)
        _ship_feature(client, fast_id, builder, checker)
        _ship_feature(client, slow_id, builder, checker)
        _reach_build(client, plain_id, builder)
        for feature_id, stamps in {
            fast_id: {
                "Define": "2026-03-01T00:00:00+00:00",
                "Build": "2026-03-02T00:00:00+00:00",
                "Check": "2026-03-03T00:00:00+00:00",
                "Ship": "2026-03-04T00:00:00+00:00",
            },
            slow_id: {
                "Define": "2026-03-01T00:00:00+00:00",
                "Build": "2026-03-01T00:00:00+00:00",
                "Check": "2026-03-02T00:00:00+00:00",
                "Ship": "2026-03-03T00:00:00+00:00",
            },
            plain_id: {
                "Define": "2026-03-05T00:00:00+00:00",
                "Build": "2026-03-06T00:00:00+00:00",
            },
        }.items():
            for stage, stamp in stamps.items():
                _stamp(database, feature_id, stage, stamp)

        cycle_id = _record_id(
            _create(
                client,
                "/cycles",
                {
                    "name": "March",
                    "delivery_group_id": group_id,
                    "starts_on": "2026-03-01",
                    "ends_on": "2026-03-10",
                },
            )
        )
        _create(
            client,
            f"/cycles/{cycle_id}/outcomes",
            {"description": "Fewer returns", "planned_signal": "10", "team_id": ""},
        )
        _create(
            client,
            f"/cycles/{cycle_id}/outcomes",
            {"description": "Fewer guesses", "planned_signal": "soon", "team_id": ""},
        )
        cycle_page = client.get(f"/cycles/{cycle_id}").text
        outcome_ids = re.findall(r"/outcomes/(\d+)/actual", cycle_page)
        client.post(f"/outcomes/{outcome_ids[0]}/actual", data={"actual_signal": "8"}, follow_redirects=True)
        client.post(
            f"/outcomes/{outcome_ids[1]}/actual",
            data={"actual_signal": "later"},
            follow_redirects=True,
        )
        flow = client.get(f"/delivery-groups/{group_id}/flow?cycle_id={cycle_id}")
        assert flow.status_code == 200
        assert 'class="throughput">2<' in flow.text
        assert 'class="lead-time">2<' in flow.text
        assert 'class="wip">1<' in flow.text
        assert 'class="active">7<' in flow.text
        assert 'class="wait">4<' in flow.text
        assert 'class="mix-feature">3<' in flow.text
        assert 'class="mix-platform">0<' in flow.text
        assert 'class="mix-prototype">0<' in flow.text
        assert 'class="mix-experiment">0<' in flow.text
        assert "Fewer returns 0.8" in flow.text
        assert "Fewer guesses not a number" in flow.text

        owner = _person(client, "Owner", "product_owner", team_id=team_id)
        cycle_id = _record_id(
            _create(
                client,
                "/cycles",
                {
                    "name": "Spring",
                    "delivery_group_id": group_id,
                    "starts_on": "2026-04-01",
                    "ends_on": "2026-06-30",
                },
            )
        )
        for name, start, end in (
            ("Iter One", "2026-04-01", "2026-04-14"),
            ("Iter Two", "2026-04-15", "2026-04-28"),
            ("Iter Three", "2026-04-29", "2026-05-12"),
        ):
            _create(
                client,
                "/iterations",
                {
                    "team_id": team_id,
                    "cycle_id": cycle_id,
                    "name": name,
                    "starts_on": start,
                    "ends_on": end,
                },
            )
        medium_id = _record_id(
            _create(
                client,
                "/stories",
                {"name": "Label the aisle", "feature_id": fast_id, "kind": "feature"},
            )
        )
        points_id = _record_id(
            _create(
                client,
                "/stories",
                {"name": "Count the walk", "feature_id": fast_id, "kind": "feature"},
            )
        )
        _create(
            client,
            f"/stories/{medium_id}/estimate",
            {"team_id": team_id, "label": "M", "points": ""},
        )
        _create(
            client,
            f"/teams/{team_id}/sizing",
            {
                "method": "points",
                "size_xs": "1",
                "size_s": "2",
                "size_m": "3",
                "size_l": "5",
                "size_xl": "8",
            },
        )
        _create(
            client,
            f"/stories/{points_id}/estimate",
            {"team_id": team_id, "label": "", "points": "5"},
        )
        team_page = client.get(f"/teams/{team_id}").text
        third_id = re.search(r'/iterations/(\d+)">Iter Three', team_page).group(1)
        for story_id in (medium_id, points_id):
            added = client.post(
                f"/iterations/{third_id}/stories",
                data={"story_id": story_id, "person_id": owner},
                follow_redirects=True,
            )
            assert added.status_code == 200, added.text
            _ship_story(client, story_id, builder, checker)
        team_page = client.get(f"/teams/{team_id}").text
        assert 'class="velocity">Iter Three 8<' in team_page
        assert 'class="velocity">Iter Two 0<' in team_page
        assert 'class="velocity">Iter One 0<' in team_page
        assert team_page.index("Iter Three 8") < team_page.index("Iter Two 0")
        assert team_page.index("Iter Two 0") < team_page.index("Iter One 0")


def _ship_story(client: TestClient, story_id: str, builder: str, checker: str) -> None:
    client.post(
        f"/stories/{story_id}/stage",
        data={"stage": "Define", "person_id": builder},
        follow_redirects=True,
    )
    client.post(f"/stories/{story_id}/approval", data={"person_id": builder}, follow_redirects=True)
    built = client.post(
        f"/stories/{story_id}/stage",
        data={"stage": "Build", "person_id": builder},
        follow_redirects=True,
    )
    assert 'class="stage">Build' in built.text, built.text
    client.post(
        f"/stories/{story_id}/done-list",
        data={"integrated": "1", "acceptance": "1", "dependency": "1"},
        follow_redirects=True,
    )
    checked = client.post(
        f"/stories/{story_id}/stage",
        data={"stage": "Check", "person_id": checker},
        follow_redirects=True,
    )
    assert 'class="stage">Check' in checked.text, checked.text
    shipped = client.post(
        f"/stories/{story_id}/stage",
        data={"stage": "Ship", "person_id": checker},
        follow_redirects=True,
    )
    assert 'class="stage">Ship' in shipped.text, shipped.text
