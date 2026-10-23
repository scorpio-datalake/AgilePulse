"""Load the sample organization described in how_to_create_data.md.

Run from the project directory:

    python -m app.sample_data
    python -m app.sample_data data/scaled_engine.sqlite

Sprints are dated from the day you run the script, so one sprint on Build crew
includes today and an earlier sprint is already over.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

from app.db import ADMIN_USERNAME, attach_login, connect, migrate
from app.stages import definition_key
from app.store import SqlStore

SAMPLE_PASSWORD = "sample"
SAMPLE_PORTFOLIO = "Supply chain"
DISCOVERY_CYCLE = "Discovery of the AI models"
WAREHOUSE_GROUP = "Optimization of the warehouse"


class SampleAlreadyLoaded(Exception):
    pass


def load_sample(path: Path) -> dict:
    path = path.expanduser().resolve()
    migrate(path)
    session = connect(path)
    try:
        store = SqlStore(session)
        admin = store.user_by_username(ADMIN_USERNAME)
        if admin is None or admin["organization_id"] is None:
            raise RuntimeError("The local admin user is missing.")
        organization_id = int(admin["organization_id"])
        if _cycle_named(store, organization_id, DISCOVERY_CYCLE):
            raise SampleAlreadyLoaded(f"{DISCOVERY_CYCLE} is already in {path}.")
        group = _find_group(store, organization_id, WAREHOUSE_GROUP)
        if group is not None:
            return add_warehouse_plan(store, organization_id, group)
        return _load(store, session, organization_id)
    finally:
        session.close()


def _load(store: SqlStore, session, organization_id: int) -> dict:
    today = date.today()
    supply_id = _created(store.create_portfolio(organization_id, "Supply chain"))
    storefront_id = _created(store.create_portfolio(organization_id, "Storefront"))
    warehouse_id = _created(
        store.create_value_stream(organization_id, supply_id, "Warehouse fulfillment")
    )
    checkout_stream_id = _created(
        store.create_value_stream(organization_id, storefront_id, "Checkout experience")
    )
    warehouse_group_id = _created(
        store.create_delivery_group(organization_id, warehouse_id, "Optimization of the warehouse")
    )
    checkout_group_id = _created(
        store.create_delivery_group(organization_id, checkout_stream_id, "Lane redesign")
    )
    build_id = _created(store.create_team(organization_id, warehouse_group_id, "Build crew"))
    model_id = _created(store.create_team(organization_id, warehouse_group_id, "Model crew"))
    checkout_id = _created(store.create_team(organization_id, checkout_group_id, "Checkout crew"))

    nia_id = _person(
        store,
        organization_id,
        "Nia Chen",
        "product_manager",
        delivery_group_id=warehouse_group_id,
    )
    _ok(store.add_membership(organization_id, nia_id, delivery_group_id=warehouse_group_id))
    owen_id = _person(
        store, organization_id, "Owen Park", "product_owner", team_id=build_id
    )
    sam_id = _person(
        store, organization_id, "Sam Reed", "scrum_master", team_id=build_id
    )
    dev_id = _person(
        store, organization_id, "Dev Patel", "team_member", team_id=build_id
    )
    _ok(store.add_membership(organization_id, dev_id, team_id=model_id))
    lea_id = _person(
        store, organization_id, "Lea Ortiz", "technical_lead", team_id=checkout_id
    )
    rio_id = _created(store.create_person(organization_id, "Rio Alvarez"))

    for person_id, username, name in (
        (nia_id, "nia", "Nia Chen"),
        (owen_id, "owen", "Owen Park"),
        (sam_id, "sam", "Sam Reed"),
        (dev_id, "dev", "Dev Patel"),
        (lea_id, "lea", "Lea Ortiz"),
    ):
        attach_login(session, person_id, username, SAMPLE_PASSWORD)
        store.rename_person(organization_id, person_id, name)

    plan = add_warehouse_plan(
        store,
        organization_id,
        {"id": warehouse_group_id, "value_stream_id": warehouse_id},
    )
    checkout_cycle_id = _created(
        store.create_cycle(
            organization_id,
            checkout_group_id,
            "Checkout cycle",
            _day(today, -90),
            _day(today, 40),
        )
    )
    _created(
        store.create_iteration(
            organization_id,
            checkout_id,
            checkout_cycle_id,
            "Lane week",
            _day(today, -1),
            _day(today, 10),
        )
    )
    store.save_team_sizing(organization_id, build_id, "tshirt", 1, 2, 3, 5, 8)
    store.set_wip_limit(organization_id, build_id, 2)
    store.add_policy(organization_id, warehouse_group_id, "Define", "Build", "warning")
    store.add_sync_note(
        organization_id,
        build_id,
        _day(today, -2),
        "Labels are still being printed",
        sam_id,
    )
    store.add_cross_note(
        organization_id,
        build_id,
        "Need the slot feed",
        "Model crew publishes the feed",
        model_id,
        sam_id,
    )
    store.add_retro_note(
        organization_id,
        build_id,
        plan["picker_id"],
        "The aisle labels are hard to read",
        sam_id,
    )

    return {
        "organization_id": organization_id,
        "supply_chain_id": supply_id,
        "storefront_id": storefront_id,
        "build_id": build_id,
        "rio_id": rio_id,
        "lea_id": lea_id,
        "model_id": model_id,
    }


def add_warehouse_plan(store: SqlStore, organization_id: int, group: dict) -> dict:
    """Two cycles and the Optimization of the warehouse board.

    Discovery of the AI models is the earlier cycle. Sprint 1 sits on Model crew.
    Warehouse pick optimization is the current cycle. Picker week and Sprint 2 sit
    on Build crew. Dates are offsets from the day this runs.
    """
    today = date.today()
    group_id = group["id"]
    stream_id = group["value_stream_id"]
    teams = {team["name"]: team for team in store.list_teams(group_id)}
    build = teams["Build crew"]
    model = teams["Model crew"]
    people = {person["name"]: person["id"] for person in store.list_people(organization_id)}
    builder = people.get("dev1") or people.get("Dev Patel") or next(iter(people.values()))
    checker = people.get("test1") or people.get("Sam Reed") or builder

    goal_id = _created(store.create_goal(organization_id, stream_id, "Fewer walking miles"))
    picking_id = _created(store.create_initiative(organization_id, goal_id, "Slot the picks"))
    store.set_initiative_state(organization_id, picking_id, "Active")
    models_id = _created(store.create_initiative(organization_id, goal_id, "Choose the pick model"))
    store.set_initiative_state(organization_id, models_id, "Active")

    pick_path = _feature(store, organization_id, picking_id, "Pick path", "feature", "Build", builder, checker, today)
    _feature(store, organization_id, picking_id, "Aisle map", "platform", "Define", builder, checker, today)
    _feature(store, organization_id, picking_id, "Which aisle first", "experiment", "Discover", builder, checker, today)
    travel = _feature(store, organization_id, models_id, "Travel-time model", "experiment", "Check", builder, checker, today)

    _criteria(
        store,
        organization_id,
        "feature",
        pick_path,
        "Miles per pick",
        "Lower than the week before the cycle",
        "A full picker shift",
        "Route chosen before the picker walks",
    )

    stories = {
        "compare": _placed_story(
            store, organization_id, travel, model["id"], "Compare travel-time models", "experiment", "Check",
            builder, checker, today, "Sprint 1",
            "Walk-time error", "Under 0.4 minutes", "One week of completed picks", "Score a route in under 50 ms",
        ),
        "label": _placed_story(
            store, organization_id, travel, model["id"], "Label a week of pick paths", "feature", "Define",
            builder, checker, today, None,
            "Labeled routes", "At least 200 routes", "Pick paths from last week", "Not timed",
        ),
        "baseline": _placed_story(
            store, organization_id, travel, model["id"], "Score the nearest-aisle baseline", "feature", "Build",
            builder, checker, today, None,
            "Baseline miles per pick", "Recorded for the same week", "Completed picks", "Batch finishes overnight",
        ),
        "card": _placed_story(
            store, organization_id, travel, model["id"], "Write the model card", "platform", "Discover",
            builder, checker, today, None,
            "Model card sections", "Data, metric, and limit filled in", "The chosen model", "Not timed",
        ),
        "label_slot": _placed_story(
            store, organization_id, pick_path, build["id"], "Print the slot label", "feature", "Discover",
            builder, checker, today, None,
            "Label reads the slot", "Matches the bin the model chose", "A test pick", "Shown before the picker walks",
        ),
        "next_bin": _placed_story(
            store, organization_id, pick_path, build["id"], "Show the next bin", "feature", "Define",
            builder, checker, today, None,
            "Next bin on the screen", "The bin the model named", "One pick", "Under 1 second",
        ),
        "confirm": _placed_story(
            store, organization_id, pick_path, build["id"], "Confirm the pick", "feature", "Build",
            builder, checker, today, None,
            "Confirmed picks", "The package in hand matches the bin", "A test aisle", "Under 1 second",
        ),
        "blocked": _placed_story(
            store, organization_id, pick_path, build["id"], "Warn when the aisle is blocked", "feature", "Check",
            builder, checker, today, None,
            "Blocked-aisle warning", "Shown before the picker enters", "A closed aisle", "Under 1 second",
        ),
        "miles": _placed_story(
            store, organization_id, pick_path, build["id"], "Record the walking miles", "feature", "Ship",
            builder, checker, today, None,
            "Miles per pick", "Lower than last week", "A full shift", "Recorded at the end of the pick",
        ),
    }

    discovery_id = _created(
        store.create_cycle(
            organization_id, group_id, DISCOVERY_CYCLE, _day(today, -80), _day(today, -36)
        )
    )
    sprint_1 = _created(
        store.create_iteration(
            organization_id, model["id"], discovery_id, "Sprint 1", _day(today, -80), _day(today, -50)
        )
    )
    warehouse_id = _created(
        store.create_cycle(
            organization_id,
            group_id,
            "Warehouse pick optimization",
            _day(today, -28),
            _day(today, 28),
        )
    )
    picker_id = _created(
        store.create_iteration(
            organization_id, build["id"], warehouse_id, "Picker week", _day(today, -28), _day(today, -8)
        )
    )
    sprint_2 = _created(
        store.create_iteration(
            organization_id, build["id"], warehouse_id, "Sprint 2", _day(today, -4), _day(today, 10)
        )
    )
    for key in ("compare", "label", "baseline"):
        store.add_iteration_story(organization_id, sprint_1, stories[key])
    store.add_iteration_story(organization_id, picker_id, stories["miles"])
    for key in ("next_bin", "confirm", "blocked"):
        store.add_iteration_story(organization_id, sprint_2, stories[key])

    store.add_outcome(
        organization_id, discovery_id, model["id"], "A pick model is chosen", "One model card accepted"
    )
    store.add_outcome(
        organization_id, warehouse_id, None, "Fewer walking miles", "Miles per pick down"
    )
    store.add_milestone(organization_id, warehouse_id, "Picker screen ready", _day(today, 10))
    store.set_wip_limit(organization_id, build["id"], 3)
    store.set_wip_limit(organization_id, model["id"], 3)
    return {
        "build_id": build["id"],
        "model_id": model["id"],
        "picker_id": picker_id,
        "sprint_1": sprint_1,
        "sprint_2": sprint_2,
    }


def _feature(store, organization_id, initiative_id, name, kind, stage, builder, checker, today) -> int:
    feature_id = _created(store.create_feature(organization_id, initiative_id, name, kind))
    if stage in {"Build", "Check", "Ship"}:
        store.approve_definition(organization_id, "feature", feature_id, builder, definition_key(name, kind))
    if stage in {"Check", "Ship"}:
        store.save_done_checks(
            organization_id, "feature", feature_id, {"integrated", "acceptance", "dependency", "rollback"}
        )
    _walk(store, organization_id, "feature", feature_id, stage, builder, checker, today)
    return feature_id


def _placed_story(
    store, organization_id, feature_id, team_id, name, kind, stage, builder, checker, today, _iteration, *criteria
) -> int:
    story_id = _created(store.create_story(organization_id, feature_id, name, kind))
    store.set_story_estimate(organization_id, story_id, team_id, "M", 3)
    store.set_criteria(organization_id, "story", story_id, *criteria)
    if stage in {"Build", "Check", "Ship"}:
        store.approve_definition(organization_id, "story", story_id, builder, definition_key(name, kind))
    if stage in {"Check", "Ship"}:
        store.save_done_checks(
            organization_id, "story", story_id, {"integrated", "acceptance", "dependency", "rollback"}
        )
    _walk(store, organization_id, "story", story_id, stage, builder, checker, today)
    return story_id


def _criteria(store, organization_id, kind, record_id, measure, threshold, dataset, latency) -> None:
    store.set_criteria(organization_id, kind, record_id, measure, threshold, dataset, latency)


def _walk(store, organization_id, kind, record_id, stage, builder, checker, today) -> None:
    walked = "Discover"
    for target in ("Define", "Build", "Check", "Ship"):
        if stage == "Discover" or walked == stage:
            return
        actor = checker if target in {"Check", "Ship"} else builder
        store.record_stage(organization_id, kind, record_id, walked, target, actor, _day(today, -1))
        walked = target
        if walked == stage:
            return


def _find_group(store: SqlStore, organization_id: int, name: str) -> dict | None:
    for portfolio in store.list_portfolios(organization_id):
        for stream in store.list_value_streams(portfolio["id"]):
            for group in store.list_delivery_groups(stream["id"]):
                if group["name"] == name:
                    return group
    return None


def _cycle_named(store: SqlStore, organization_id: int, name: str) -> bool:
    for portfolio in store.list_portfolios(organization_id):
        for stream in store.list_value_streams(portfolio["id"]):
            for group in store.list_delivery_groups(stream["id"]):
                if any(cycle["name"] == name for cycle in store.list_cycles(group["id"])):
                    return True
    return False


def _person(store, organization_id, name, role, **place) -> int:
    person_id, message = store.create_person_with_role(organization_id, name, role, **place)
    if person_id is None:
        raise RuntimeError(message or f"Could not add {name}.")
    return person_id


def _created(row_id: int | None) -> int:
    if row_id is None:
        raise RuntimeError("Sample data stopped on a missing record.")
    return row_id


def _ok(message: str | None) -> None:
    if message is not None:
        raise RuntimeError(message)


def _day(today: date, offset: int) -> str:
    return (today + timedelta(days=offset)).isoformat()


def main() -> None:
    raw = sys.argv[1] if len(sys.argv) > 1 else "data/scaled_engine.sqlite"
    try:
        load_sample(Path(raw))
    except SampleAlreadyLoaded as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Sample data loaded into {Path(raw).expanduser().resolve()}")
    print("Sign in as admin / admin, or as nia, owen, sam, dev, or lea with password sample.")


if __name__ == "__main__":
    main()
