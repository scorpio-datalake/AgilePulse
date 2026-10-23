from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates

from app.access import RECORD_HIDDEN, access_scope, allows
from app.measures import flow_measures, signal_ratio, velocity_of
from app.navigation import group_breadcrumb, shell, team_breadcrumb
from app.store import Database, get_store


def register_flow(app: FastAPI, templates: Jinja2Templates, signed_in_user, sign_in) -> None:
    def hidden(request, store, signed_in, kind, record_id):
        if allows(access_scope(store, signed_in["id"]), kind, record_id):
            return None
        return templates.TemplateResponse(
            request,
            "refused.html",
            {
                "message": RECORD_HIDDEN,
                **shell(store, signed_in["organization_id"], None, user_id=signed_in["id"]),
            },
            status_code=422,
        )

    def measures_for(store, items, starts_on, ends_on):
        feature_ids = [item["id"] for item in items if item["target_kind"] == "feature"]
        story_ids = [item["id"] for item in items if item["target_kind"] == "story"]
        stamps = store.list_stage_stamps("feature", feature_ids) + store.list_stage_stamps(
            "story", story_ids
        )
        return flow_measures(items, stamps, starts_on, ends_on)

    def reliability_for(store, cycle_id):
        return [
            {
                "description": outcome["description"],
                "reliability": signal_ratio(outcome["planned_signal"], outcome["actual_signal"]),
            }
            for outcome in store.list_cycle_outcomes(cycle_id)
        ]

    @app.get("/delivery-groups/{delivery_group_id}/flow")
    def group_flow(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        delivery_group_id: int,
        cycle_id: int | None = None,
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        organization_id = signed_in["organization_id"]
        group = store.get_delivery_group(organization_id, delivery_group_id)
        if group is None:
            raise HTTPException(status_code=404)
        refused = hidden(request, store, signed_in, "group", delivery_group_id)
        if refused is not None:
            return refused
        cycles = store.list_cycles(delivery_group_id)
        selected = _selected(cycles, cycle_id)
        measures = None
        reliability = []
        if selected is not None:
            items = store.list_group_flow_items(delivery_group_id)
            measures = measures_for(store, items, selected["starts_on"], selected["ends_on"])
            reliability = reliability_for(store, selected["id"])
        breadcrumb = group_breadcrumb(store, organization_id, group)
        breadcrumb[-1] = {"name": group["name"], "href": f"/delivery-groups/{group['id']}"}
        breadcrumb.append({"name": "Flow", "href": None})
        return templates.TemplateResponse(
            request,
            "flow.html",
            {
                "heading": group["name"],
                "scope": "cycle",
                "choices": cycles,
                "selected": selected,
                "measures": measures,
                "reliability": reliability,
                "velocity": [],
                "choice_field": "cycle_id",
                "form_action": f"/delivery-groups/{delivery_group_id}/flow",
                "breadcrumb": breadcrumb,
                **shell(store, organization_id, "delivery_group", delivery_group_id, signed_in["id"]),
            },
        )

    @app.get("/teams/{team_id}/flow")
    def team_flow(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        team_id: int,
        iteration_id: int | None = None,
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        organization_id = signed_in["organization_id"]
        team = store.get_team(organization_id, team_id)
        if team is None:
            raise HTTPException(status_code=404)
        refused = hidden(request, store, signed_in, "team", team_id)
        if refused is not None:
            return refused
        iterations = store.list_iterations(team_id)
        selected = _selected(iterations, iteration_id)
        measures = None
        reliability = []
        if selected is not None:
            items = [
                {
                    "target_kind": "story",
                    "id": story["id"],
                    "name": story["name"],
                    "stage": story["stage"],
                    "kind": story["kind"],
                }
                for story in store.list_iteration_board(selected["id"])
            ]
            measures = measures_for(store, items, selected["starts_on"], selected["ends_on"])
            reliability = [
                {
                    "description": outcome["description"],
                    "reliability": signal_ratio(outcome["planned_signal"], outcome["actual_signal"]),
                }
                for outcome in store.list_cycle_outcomes(selected["cycle_id"])
                if outcome["team_id"] in {None, team_id}
            ]
        breadcrumb = team_breadcrumb(store, organization_id, team)
        breadcrumb[-1] = {"name": team["name"], "href": f"/teams/{team['id']}"}
        breadcrumb.append({"name": "Flow", "href": None})
        return templates.TemplateResponse(
            request,
            "flow.html",
            {
                "heading": team["name"],
                "scope": "iteration",
                "choices": iterations,
                "selected": selected,
                "measures": measures,
                "reliability": reliability,
                "velocity": _velocity_history(store, iterations),
                "choice_field": "iteration_id",
                "form_action": f"/teams/{team_id}/flow",
                "breadcrumb": breadcrumb,
                **shell(store, organization_id, "team", team_id, signed_in["id"]),
            },
        )


def _selected(choices: list[dict], record_id: int | None) -> dict | None:
    if not choices:
        return None
    if record_id is None:
        return choices[-1]
    for choice in choices:
        if choice["id"] == record_id:
            return choice
    return None


def _velocity_history(store: Database, iterations: list[dict]) -> list[dict]:
    latest = sorted(iterations, key=lambda item: (item["ends_on"], item["id"]), reverse=True)[:3]
    return [
        {
            "name": iteration["name"],
            "velocity": velocity_of(store.list_iteration_board(iteration["id"])),
        }
        for iteration in latest
    ]

