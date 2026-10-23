from pathlib import Path

from fastapi.testclient import TestClient

from app.db import ADMIN_PASSWORD, ADMIN_USERNAME, attach_login, connect
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


def _between(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


def _shop(client: TestClient) -> dict:
    portfolio_id = _record_id(_create(client, "/portfolios", {"name": "Supply chain"}))
    stream_id = _record_id(
        _create(client, "/value-streams", {"name": "Warehouse fulfillment", "portfolio_id": portfolio_id})
    )
    group_id = _record_id(
        _create(
            client,
            "/delivery-groups",
            {"name": "Optimization of the warehouse", "value_stream_id": stream_id},
        )
    )
    build_id = _record_id(
        _create(client, "/teams", {"name": "Build crew", "delivery_group_id": group_id})
    )
    model_id = _record_id(
        _create(client, "/teams", {"name": "Model crew", "delivery_group_id": group_id})
    )
    goal_id = _record_id(
        _create(client, "/goals", {"name": "Fewer walking miles", "value_stream_id": stream_id})
    )
    initiative_id = _record_id(
        _create(client, "/initiatives", {"name": "Slot the picks", "goal_id": goal_id})
    )
    return {
        "portfolio_id": portfolio_id,
        "stream_id": stream_id,
        "group_id": group_id,
        "build_id": build_id,
        "model_id": model_id,
        "initiative_id": initiative_id,
    }


def _feature(client: TestClient, initiative_id: str, name: str, kind: str) -> str:
    return _record_id(
        _create(client, "/features", {"name": name, "initiative_id": initiative_id, "kind": kind})
    )


def _person(client: TestClient, name: str, role: str, **extra) -> str:
    return _record_id(_create(client, "/people", {"name": name, "role": role, **extra}))


def _stage(client: TestClient, feature_id: str, stage: str, person_id: str, ok: bool):
    response = client.post(
        f"/features/{feature_id}/stage",
        data={"stage": stage, "person_id": person_id},
        follow_redirects=True,
    )
    if ok:
        assert response.status_code == 200, response.text
        assert f'class="stage">{stage}' in response.text
    return response


def _done(client: TestClient, feature_id: str, keys: list[str]):
    response = client.post(
        f"/features/{feature_id}/done-list",
        data={key: "1" for key in keys},
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_delivery_path(tmp_path: Path):
    with _client(tmp_path / "path.sqlite") as client:
        signed_out = client.get("/features/1", follow_redirects=False)
        assert signed_out.status_code == 303
        assert signed_out.headers["location"] == "/sign-in"
        _sign_in(client)
        shop = _shop(client)
        dev_id = _person(client, "dev1", "team_member", team_id=shop["build_id"])
        tester_id = _person(client, "test1", "team_member", team_id=shop["build_id"])
        feature_id = _feature(client, shop["initiative_id"], "Pick path", "feature")
        refused = client.post(
            f"/features/{feature_id}/stage",
            data={"stage": "Nope", "person_id": dev_id},
        )
        assert refused.status_code == 422
        assert "That stage was refused." in refused.text

        moved = _stage(client, feature_id, "Define", dev_id, True)
        assert "dev1 from Discover to Define" in moved.text
        again = client.get(f"/features/{feature_id}")
        assert 'class="stage">Define' in again.text
        assert "dev1 from Discover to Define" in again.text

        blocked = _stage(client, feature_id, "Build", dev_id, False)
        assert "Build needs an approved definition." in blocked.text
        client.post(
            f"/features/{feature_id}/approval",
            data={"person_id": dev_id},
            follow_redirects=True,
        )
        _stage(client, feature_id, "Build", dev_id, True)

        same = _stage(client, feature_id, "Check", dev_id, False)
        assert "The person who built this cannot complete Check." in same.text
        waiting = _stage(client, feature_id, "Check", tester_id, False)
        assert "Check is waiting on the done list." in waiting.text
        _done(client, feature_id, ["integrated", "acceptance", "dependency"])
        still = _stage(client, feature_id, "Check", tester_id, False)
        assert "Check is waiting on the done list." in still.text
        _done(client, feature_id, ["integrated", "acceptance", "dependency", "rollback"])
        _stage(client, feature_id, "Check", tester_id, True)
        client.post(
            f"/features/{feature_id}/path-flags",
            data={"changes_production": "1", "architecture_applies": "1", "pii_applies": "0"},
            follow_redirects=True,
        )
        review_block = _stage(client, feature_id, "Check", tester_id, False)
        assert "Check is waiting on the done list." in review_block.text

        platform_id = _feature(client, shop["initiative_id"], "Aisle map", "platform")
        _stage(client, platform_id, "Define", dev_id, True)
        client.post(f"/features/{platform_id}/approval", data={"person_id": dev_id}, follow_redirects=True)
        _stage(client, platform_id, "Build", dev_id, True)
        renamed = client.post(
            f"/features/{platform_id}",
            data={"name": "Aisle map revised", "kind": "platform"},
            follow_redirects=True,
        )
        assert 'class="stage">Check' in renamed.text
        assert "to Check" in renamed.text

        experiment_id = _feature(client, shop["initiative_id"], "Which aisle first", "experiment")
        _stage(client, experiment_id, "Define", dev_id, True)
        client.post(
            f"/features/{experiment_id}/approval",
            data={"person_id": dev_id},
            follow_redirects=True,
        )
        _stage(client, experiment_id, "Build", dev_id, True)
        _done(client, experiment_id, ["integrated", "acceptance", "dependency"])
        _stage(client, experiment_id, "Check", tester_id, True)
        stayed = client.post(
            f"/features/{experiment_id}/stage",
            data={"stage": "Ship", "person_id": tester_id},
            follow_redirects=True,
        )
        assert "A prototype or experiment stays in Check." in stayed.text
        assert 'class="stage">Check' in stayed.text
        shipped = client.post(
            f"/features/{experiment_id}/ship",
            data={"person_id": tester_id},
            follow_redirects=True,
        )
        assert 'class="stage">Ship' in shipped.text

        story_id = _record_id(
            _create(
                client,
                "/stories",
                {"name": "Show the next bin", "feature_id": feature_id, "kind": "feature"},
            )
        )
        client.post(
            f"/stories/{story_id}/estimate",
            data={"team_id": shop["build_id"], "label": "M", "points": ""},
            follow_redirects=True,
        )
        story_define = client.post(
            f"/stories/{story_id}/stage",
            data={"stage": "Define", "person_id": dev_id},
            follow_redirects=True,
        )
        assert 'class="stage">Define' in story_define.text
        team_page = client.get(f"/teams/{shop['build_id']}").text
        assert "Show the next bin" in _between(team_page, "<h3>Define</h3>", "<h3>Build</h3>")
        group_page = client.get(f"/delivery-groups/{shop['group_id']}").text
        assert "Show the next bin" in _between(group_page, "<h3>Define</h3>", "<h3>Build</h3>")
        assert "Pick path" in _between(group_page, "<h3>Check</h3>", "<h3>Ship</h3>")


def test_cycle_alignment(tmp_path: Path):
    with _client(tmp_path / "cycle.sqlite") as client:
        _sign_in(client)
        shop = _shop(client)
        owner_id = _person(client, "po1", "product_owner", team_id=shop["build_id"])
        pick_id = _feature(client, shop["initiative_id"], "Pick path", "feature")
        aisle_id = _feature(client, shop["initiative_id"], "Aisle map", "platform")
        experiment_id = _feature(client, shop["initiative_id"], "Which aisle first", "experiment")
        cycle_id = _record_id(
            _create(
                client,
                "/cycles",
                {
                    "name": "Warehouse cycle",
                    "starts_on": "2026-10-05",
                    "ends_on": "2026-11-16",
                    "delivery_group_id": shop["group_id"],
                },
            )
        )
        opened = client.get(f"/cycles/{cycle_id}").text
        assert "Warehouse cycle" in opened
        assert "2026-10-05" in opened
        assert "2026-11-16" in opened
        assert "Save decision" not in opened
        assert 'class="dependent-work"' not in opened
        assert 'class="architecture-review"' not in opened
        assert 'class="pii-review"' not in opened
        group = client.get(f"/delivery-groups/{shop['group_id']}").text
        assert "Warehouse cycle" in group

        _create(
            client,
            f"/cycles/{cycle_id}/outcomes",
            {"description": "Fewer walking miles", "planned_signal": "Miles per pick down", "team_id": ""},
        )
        _create(
            client,
            f"/cycles/{cycle_id}/outcomes",
            {
                "description": "Build crew finishes the picker screen",
                "planned_signal": "Screen in use",
                "team_id": shop["build_id"],
            },
        )
        outcome_page = client.get(f"/cycles/{cycle_id}").text
        group_outcome = outcome_page.split('name="outcome_id"', 1)[1]
        outcome_id = group_outcome.split('value="', 1)[1].split('"', 1)[0]
        _create(
            client,
            f"/cycles/{cycle_id}/links",
            {"outcome_id": outcome_id, "feature_id": pick_id, "story_id": ""},
        )
        _create(
            client,
            f"/cycles/{cycle_id}/milestones",
            {"name": "Picker screen ready", "happens_on": "2026-10-30"},
        )
        _create(
            client,
            f"/cycles/{cycle_id}/dependencies",
            {
                "description": "Slot map from the warehouse",
                "owner_person_id": owner_id,
                "needed_by": "2026-10-20",
                "opened_on": "2026-10-06",
                "status": "open",
                "providing_team_id": "",
            },
        )
        _create(
            client,
            f"/cycles/{cycle_id}/dependent-work",
            {
                "feature_id": pick_id,
                "needed": "Firewall change",
                "done_looks_like": "The picker can reach the slot service",
                "needed_by": "2026-10-18",
                "status": "open",
                "providing_team_id": "",
            },
        )
        _create(
            client,
            f"/cycles/{cycle_id}/dependent-work",
            {
                "feature_id": pick_id,
                "needed": "Database change",
                "done_looks_like": "The slot table is readable",
                "needed_by": "2026-10-18",
                "status": "open",
                "providing_team_id": shop["model_id"],
            },
        )
        client.post(
            f"/features/{pick_id}/path-flags",
            data={"changes_production": "1", "architecture_applies": "1", "pii_applies": "0"},
            follow_redirects=False,
        )
        client.post(
            f"/features/{experiment_id}/path-flags",
            data={"changes_production": "0", "architecture_applies": "0", "pii_applies": "1"},
            follow_redirects=False,
        )
        _create(
            client,
            f"/cycles/{cycle_id}/reviews",
            {
                "kind": "architecture",
                "feature_id": pick_id,
                "reviewer_person_id": owner_id,
                "reviewed_on": "2026-10-08",
                "result": "approved",
            },
        )
        _create(
            client,
            f"/cycles/{cycle_id}/reviews",
            {
                "kind": "pii",
                "feature_id": experiment_id,
                "reviewer_person_id": owner_id,
                "reviewed_on": "2026-10-09",
                "result": "changes_requested",
            },
        )
        risk = client.post(
            f"/cycles/{cycle_id}/risks",
            data={"description": "Slot data arrives late", "state": "open"},
            follow_redirects=True,
        )
        risk_id = risk.text.split('action="/risks/', 1)[1].split('"', 1)[0]
        client.post(f"/risks/{risk_id}", data={"state": "owned"}, follow_redirects=True)
        _create(client, f"/cycles/{cycle_id}/confidence", {"person_id": owner_id, "score": "5"})
        admin_id = client.get("/people").text.split("Admin", 1)[0]
        admin_person = admin_id.split('href="/people/')[-1].split('"', 1)[0]
        _create(client, f"/cycles/{cycle_id}/confidence", {"person_id": admin_person, "score": "3"})
        _create(
            client,
            f"/cycles/{cycle_id}/capacity",
            {"team_id": shop["build_id"], "note": "Build crew can take the picker screen"},
        )
        summary = client.get(f"/cycles/{cycle_id}").text
        assert "Fewer walking miles" in summary
        assert "Miles per pick down" in summary
        assert "Build crew finishes the picker screen" in summary
        assert "Screen in use" in summary
        assert "Pick path" in summary
        assert "Picker screen ready" in summary
        assert "2026-10-30" in summary
        assert "opened 2026-10-06" in summary
        assert "Firewall change" in summary
        assert "Database change" in summary
        assert "Model crew" in summary
        architecture = [line for line in summary.splitlines() if "architecture-review" in line]
        pii = [line for line in summary.splitlines() if "pii-review" in line]
        assert any("Pick path" in line for line in architecture)
        assert all("Aisle map" not in line for line in architecture)
        assert any("Which aisle first" in line for line in pii)
        assert all("Aisle map" not in line and "Pick path" not in line for line in pii)
        assert "approved" in summary
        assert "changes_requested" in summary
        assert "owned" in summary
        assert "Average: 4" in summary
        assert "Build crew can take the picker screen" in summary

        _person(client, "fac1", "group_facilitator", delivery_group_id=shop["group_id"])
        saved = client.post(
            f"/cycles/{cycle_id}/decisions",
            data={"statement": "Keep the picker screen in this cycle", "person_id": owner_id},
            follow_redirects=True,
        )
        assert "That action needs the group facilitator." in saved.text
        facilitator_page = client.get(f"/cycles/{cycle_id}").text
        fac_id = facilitator_page.split("fac1", 1)[0].split('value="')[-1].split('"', 1)[0]
        decided = client.post(
            f"/cycles/{cycle_id}/decisions",
            data={"statement": "Keep the picker screen in this cycle", "person_id": fac_id},
            follow_redirects=True,
        )
        assert "Keep the picker screen in this cycle" in decided.text
        assert "acting as group_facilitator" in decided.text
        assert aisle_id


def test_team_execution(tmp_path: Path):
    database = tmp_path / "iteration.sqlite"
    with _client(database) as client:
        _sign_in(client)
        shop = _shop(client)
        po_id = _person(client, "po1", "product_owner", team_id=shop["build_id"])
        sm_id = _person(client, "sm1", "scrum_master", team_id=shop["build_id"])
        member_id = _person(client, "mle1", "team_member", team_id=shop["model_id"])
        cycle_id = _record_id(
            _create(
                client,
                "/cycles",
                {
                    "name": "Warehouse cycle",
                    "starts_on": "2026-10-05",
                    "ends_on": "2026-11-16",
                    "delivery_group_id": shop["group_id"],
                },
            )
        )
        outside = client.post(
            "/iterations",
            data={
                "name": "Too late",
                "starts_on": "2026-11-01",
                "ends_on": "2026-12-01",
                "team_id": shop["build_id"],
                "cycle_id": cycle_id,
            },
        )
        assert outside.status_code == 422
        assert "That iteration is outside the cycle." in outside.text
        iteration_id = _record_id(
            _create(
                client,
                "/iterations",
                {
                    "name": "Picker week",
                    "starts_on": "2026-10-05",
                    "ends_on": "2026-10-16",
                    "team_id": shop["build_id"],
                    "cycle_id": cycle_id,
                },
            )
        )
        opened = client.get(f"/iterations/{iteration_id}").text
        assert "Picker week" in opened
        assert "2026-10-05" in opened
        assert "2026-10-16" in opened
        team_page = client.get(f"/teams/{shop['build_id']}").text
        assert "Picker week" in team_page

        feature_id = _feature(client, shop["initiative_id"], "Pick path", "feature")
        first_id = _record_id(
            _create(client, "/stories", {"name": "Show the next bin", "feature_id": feature_id, "kind": "feature"})
        )
        second_id = _record_id(
            _create(client, "/stories", {"name": "Confirm the pick", "feature_id": feature_id, "kind": "feature"})
        )
        for story_id in (first_id, second_id):
            client.post(
                f"/stories/{story_id}/estimate",
                data={"team_id": shop["build_id"], "label": "M", "points": ""},
                follow_redirects=False,
            )
        refused = client.post(
            f"/iterations/{iteration_id}/stories",
            data={"story_id": first_id, "person_id": sm_id},
            follow_redirects=True,
        )
        assert "That action needs the product owner." in refused.text
        added = client.post(
            f"/iterations/{iteration_id}/stories",
            data={"story_id": first_id, "person_id": po_id},
            follow_redirects=True,
        )
        assert "Show the next bin" in added.text
        assert ">3<" in added.text or ">3</span>" in added.text
        client.post(
            f"/iterations/{iteration_id}/stories",
            data={"story_id": second_id, "person_id": po_id},
            follow_redirects=False,
        )
        accepted = client.post(
            f"/iterations/{iteration_id}/acceptance",
            data={"story_id": first_id, "person_id": po_id, "accepted": "1"},
            follow_redirects=True,
        )
        assert "Completed size: 3" in accepted.text
        sm_accept = client.post(
            f"/iterations/{iteration_id}/acceptance",
            data={"story_id": second_id, "person_id": sm_id, "accepted": "1"},
            follow_redirects=True,
        )
        assert "That action needs the product owner." in sm_accept.text

        client.post(
            f"/stories/{first_id}/stage",
            data={"stage": "Define", "person_id": po_id},
            follow_redirects=False,
        )
        board = client.get(f"/iterations/{iteration_id}").text
        assert "Show the next bin" in _between(board, "<h3>Define</h3>", "<h3>Build</h3>")

        client.post(f"/teams/{shop['build_id']}/wip", data={"limit": "1"}, follow_redirects=False)
        for story_id in (first_id, second_id):
            client.post(f"/stories/{story_id}/stage", data={"stage": "Define", "person_id": po_id}, follow_redirects=False)
            client.post(f"/stories/{story_id}/approval", data={"person_id": po_id}, follow_redirects=False)
        first_build = client.post(
            f"/stories/{first_id}/stage",
            data={"stage": "Build", "person_id": po_id},
            follow_redirects=True,
        )
        assert 'class="stage">Build' in first_build.text
        second_build = client.post(
            f"/stories/{second_id}/stage",
            data={"stage": "Build", "person_id": po_id},
            follow_redirects=True,
        )
        assert "The board is at its limit." in second_build.text
        raised = client.post(
            f"/iterations/{iteration_id}/wip-exception",
            data={"story_id": second_id, "person_id": sm_id, "reason": "The dock is blocked"},
            follow_redirects=True,
        )
        assert "Limit raised: The dock is blocked" in raised.text
        entered = client.post(
            f"/stories/{second_id}/stage",
            data={"stage": "Build", "person_id": po_id},
            follow_redirects=True,
        )
        assert 'class="stage">Build' in entered.text

        client.post(
            f"/teams/{shop['build_id']}/sync-notes",
            data={"note_on": "2026-10-06", "body": "Labels are still being printed", "person_id": po_id},
            follow_redirects=True,
        )
        sync_refused = client.get(f"/teams/{shop['build_id']}").text
        assert "Labels are still being printed" not in sync_refused
        client.post(
            f"/teams/{shop['build_id']}/sync-notes",
            data={"note_on": "2026-10-06", "body": "Labels are still being printed", "person_id": sm_id},
            follow_redirects=True,
        )
        client.post(
            f"/teams/{shop['build_id']}/cross-notes",
            data={
                "impediment": "Need the slot feed",
                "dependency": "Model crew publishes the feed",
                "asked_team_id": shop["model_id"],
                "person_id": sm_id,
            },
            follow_redirects=True,
        )
        client.post(
            f"/teams/{shop['build_id']}/retro-notes",
            data={
                "iteration_id": iteration_id,
                "body": "The aisle labels are hard to read",
                "person_id": sm_id,
            },
            follow_redirects=True,
        )
        retro_page = client.get(f"/teams/{shop['build_id']}").text
        assert "Labels are still being printed" in retro_page
        assert "2026-10-06" in retro_page
        assert "The aisle labels are hard to read" in retro_page
        note_id = retro_page.split('action="/retro-notes/', 1)[1].split("/", 1)[0]
        client.post(
            f"/retro-notes/{note_id}/promote",
            data={"statement": "Label the aisles before the next pick test", "person_id": sm_id},
            follow_redirects=True,
        )
        _open_as(client, database, member_id, "mle1")
        other = client.get(f"/teams/{shop['model_id']}").text
        assert "Labels are still being printed" in other
        assert "Need the slot feed" in other
        assert "Label the aisles before the next pick test" in other
        assert "The aisle labels are hard to read" not in other
