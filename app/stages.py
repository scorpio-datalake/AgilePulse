from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.access import RECORD_HIDDEN, access_scope, allows
from app.navigation import feature_breadcrumb, shell, story_breadcrumb
from app.schemas import (
    AgentActionForm,
    CriterionForm,
    PathFlagsForm,
    PersonActionForm,
    PolicyApprovalForm,
    ProductionFlagForm,
    StageForm,
)
from app.store import Database, get_store

STAGES = ("Discover", "Define", "Build", "Check", "Ship")
STAGE_REFUSED = "That stage was refused."
BUILD_NEEDS_APPROVAL = "Build needs an approved definition."
CHECK_SAME_PERSON = "The person who built this cannot complete Check."
CHECK_WAITING = "Check is waiting on the done list."
LEARNING_STAYS = "A prototype or experiment stays in Check."
SHIP_EXPLICIT = "Ship starts from Check."
SHIP_KIND = "That ship action is for a prototype or an experiment."
PERSON_REFUSED = "That person was refused."
BOARD_LIMIT = "The board is at its limit."
POLICY_BLOCKED = "That move is blocked until a person approves it."
CRITERIA_REFUSED = "Those acceptance criteria were refused."
AGENT_REFUSED = "That agent action was refused."
APPROVAL_REFUSED = "That approval was refused."
DONE_LABELS = (
    ("integrated", "Integrated with the product"),
    ("acceptance", "Acceptance criteria met"),
    ("dependency", "No open dependency without an owner"),
    ("rollback", "Rollback note"),
    ("architecture", "Architecture review"),
    ("pii", "PII review"),
)


def now_stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def definition_key(name: str, kind: str) -> str:
    return f"{name}\n{kind}"


def required_done_keys(store: Database, kind: str, item: dict) -> list[str]:
    keys = ["integrated", "acceptance", "dependency"]
    if item["changes_production"]:
        keys.append("rollback")
    feature = item if kind == "feature" else store.get_feature(item["organization_id"], item["feature_id"])
    if feature is not None and feature["architecture_applies"]:
        keys.append("architecture")
    if feature is not None and feature["pii_applies"]:
        keys.append("pii")
    return keys


def done_items(store: Database, kind: str, item: dict) -> list[dict]:
    stored = store.done_check_map(kind, item["id"])
    required = set(required_done_keys(store, kind, item))
    return [
        {"key": key, "label": label, "done": stored.get(key, 0), "required": key in required}
        for key, label in DONE_LABELS
        if key in required
    ]


def move_stage(
    store: Database,
    organization_id: int,
    kind: str,
    item: dict,
    to_stage: str,
    person_id: int,
    *,
    explicit_ship: bool = False,
) -> str | None:
    if to_stage not in STAGES:
        return STAGE_REFUSED
    if store.get_person(organization_id, person_id) is None:
        return PERSON_REFUSED
    if to_stage == item["stage"] and to_stage != "Check":
        return None
    learning = item["kind"] in {"prototype", "experiment"}
    if to_stage == "Ship" and learning and not explicit_ship:
        return LEARNING_STAYS
    if explicit_ship:
        if not learning:
            return SHIP_KIND
        if item["stage"] != "Check":
            return SHIP_EXPLICIT
    if to_stage == "Build":
        approved = item["approved_definition"] == definition_key(item["name"], item["kind"])
        if not item["approved_by_person_id"] or not approved:
            return BUILD_NEEDS_APPROVAL
    if to_stage == "Check":
        builder = store.latest_builder_id(kind, item["id"])
        if builder is not None and builder == person_id:
            return CHECK_SAME_PERSON
        stored = store.done_check_map(kind, item["id"])
        for key in required_done_keys(store, kind, item):
            if not stored.get(key):
                return CHECK_WAITING
        if item["stage"] == "Check":
            return None
    if kind == "story" and to_stage == "Build":
        iteration_id = store.iteration_id_for_story(item["id"])
        if iteration_id is not None:
            iteration = store.get_iteration(organization_id, iteration_id)
            team = None if iteration is None else store.get_team(organization_id, iteration["team_id"])
            if team is not None and store.build_count(iteration_id) >= team["wip_limit"]:
                if store.take_wip_exception(iteration_id, item["id"]) is None:
                    return BOARD_LIMIT
    policies = store.policies_for_move(
        organization_id, kind, item["id"], item["stage"], to_stage
    )
    if any(policy["effect"] == "block" and not policy["approved"] for policy in policies):
        return POLICY_BLOCKED
    changed_at = now_stamp()
    store.record_stage(
        organization_id,
        kind,
        item["id"],
        item["stage"],
        to_stage,
        person_id,
        changed_at,
    )
    person = store.get_person(organization_id, person_id)
    actor_name = "" if person is None else person["name"]
    for policy in policies:
        if policy["effect"] != "warning":
            continue
        store.add_evidence(
            organization_id,
            kind,
            item["id"],
            "warning",
            "person",
            actor_name,
            changed_at,
            item["stage"],
            to_stage,
        )
    return None


def after_definition_edit(
    store: Database,
    organization_id: int,
    kind: str,
    record_id: int,
    person_id: int,
) -> None:
    item = (
        store.get_feature(organization_id, record_id)
        if kind == "feature"
        else store.get_story(organization_id, record_id)
    )
    if item is None or not item["approved_by_person_id"]:
        return
    if item["approved_definition"] == definition_key(item["name"], item["kind"]):
        return
    previous = item["stage"]
    store.clear_approval(organization_id, kind, record_id)
    if previous != "Check":
        store.record_stage(
            organization_id,
            kind,
            record_id,
            previous,
            "Check",
            person_id,
            now_stamp(),
        )


def register_stages(
    app: FastAPI,
    templates: Jinja2Templates,
    feature_page,
    story_page,
    signed_in_user,
    sign_in,
    edit_blocked,
) -> None:
    def page(kind):
        return feature_page if kind == "feature" else story_page

    def load(store, organization_id, kind, record_id):
        if kind == "feature":
            return store.get_feature(organization_id, record_id)
        return store.get_story(organization_id, record_id)

    def guard(request, store, record_id, kind):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return None, sign_in()
        blocked = edit_blocked(store, signed_in)
        if blocked is not None:
            return None, page(kind)(request, store, signed_in, record_id, blocked, 422)
        item = load(store, signed_in["organization_id"], kind, record_id)
        if item is None:
            raise HTTPException(status_code=404)
        return (signed_in, item), None

    def add(kind: str, record_id_name: str):
        prefix = "features" if kind == "feature" else "stories"

        @app.post(f"/{prefix}/{{record_id}}/stage")
        def post_stage(
            request: Request,
            store: Annotated[Database, Depends(get_store)],
            record_id: int,
            stage: Annotated[str, Form()] = "",
            person_id: Annotated[str, Form()] = "",
        ):
            found, response = guard(request, store, record_id, kind)
            if response is not None:
                return response
            signed_in, item = found
            try:
                form = StageForm(stage=stage, person_id=int(person_id))
            except (ValidationError, ValueError):
                return page(kind)(request, store, signed_in, record_id, STAGE_REFUSED, 422)
            message = move_stage(
                store, signed_in["organization_id"], kind, item, form.stage, form.person_id
            )
            if message is not None:
                return page(kind)(request, store, signed_in, record_id, message, 422)
            return RedirectResponse(f"/{prefix}/{record_id}", status_code=303)

        @app.post(f"/{prefix}/{{record_id}}/approval")
        def post_approval(
            request: Request,
            store: Annotated[Database, Depends(get_store)],
            record_id: int,
            person_id: Annotated[str, Form()] = "",
        ):
            found, response = guard(request, store, record_id, kind)
            if response is not None:
                return response
            signed_in, item = found
            try:
                form = PersonActionForm(person_id=int(person_id))
            except (ValidationError, ValueError):
                return page(kind)(request, store, signed_in, record_id, PERSON_REFUSED, 422)
            if store.get_person(signed_in["organization_id"], form.person_id) is None:
                return page(kind)(request, store, signed_in, record_id, PERSON_REFUSED, 422)
            store.approve_definition(
                signed_in["organization_id"],
                kind,
                record_id,
                form.person_id,
                definition_key(item["name"], item["kind"]),
            )
            return RedirectResponse(f"/{prefix}/{record_id}", status_code=303)

        @app.post(f"/{prefix}/{{record_id}}/ship")
        def post_ship(
            request: Request,
            store: Annotated[Database, Depends(get_store)],
            record_id: int,
            person_id: Annotated[str, Form()] = "",
        ):
            found, response = guard(request, store, record_id, kind)
            if response is not None:
                return response
            signed_in, item = found
            try:
                form = PersonActionForm(person_id=int(person_id))
            except (ValidationError, ValueError):
                return page(kind)(request, store, signed_in, record_id, PERSON_REFUSED, 422)
            message = move_stage(
                store,
                signed_in["organization_id"],
                kind,
                item,
                "Ship",
                form.person_id,
                explicit_ship=True,
            )
            if message is not None:
                return page(kind)(request, store, signed_in, record_id, message, 422)
            return RedirectResponse(f"/{prefix}/{record_id}", status_code=303)

        @app.post(f"/{prefix}/{{record_id}}/done-list")
        def post_done(
            request: Request,
            store: Annotated[Database, Depends(get_store)],
            record_id: int,
            integrated: Annotated[str, Form()] = "",
            acceptance: Annotated[str, Form()] = "",
            dependency: Annotated[str, Form()] = "",
            rollback: Annotated[str, Form()] = "",
            architecture: Annotated[str, Form()] = "",
            pii: Annotated[str, Form()] = "",
        ):
            found, response = guard(request, store, record_id, kind)
            if response is not None:
                return response
            signed_in, _item = found
            marked = {
                key
                for key, value in {
                    "integrated": integrated,
                    "acceptance": acceptance,
                    "dependency": dependency,
                    "rollback": rollback,
                    "architecture": architecture,
                    "pii": pii,
                }.items()
                if value == "1"
            }
            store.save_done_checks(signed_in["organization_id"], kind, record_id, marked)
            return RedirectResponse(f"/{prefix}/{record_id}", status_code=303)

        post_stage.__name__ = f"post_{kind}_stage"
        post_approval.__name__ = f"post_{kind}_approval"
        post_ship.__name__ = f"post_{kind}_ship"
        post_done.__name__ = f"post_{kind}_done"
        return record_id_name

    add("feature", "feature_id")
    add("story", "story_id")

    @app.post("/features/{feature_id}/path-flags")
    def post_feature_flags(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        feature_id: int,
        changes_production: Annotated[str, Form()] = "",
        architecture_applies: Annotated[str, Form()] = "",
        pii_applies: Annotated[str, Form()] = "",
    ):
        found, response = guard(request, store, feature_id, "feature")
        if response is not None:
            return response
        signed_in, _item = found
        try:
            form = PathFlagsForm(
                changes_production=int(changes_production or "0"),
                architecture_applies=int(architecture_applies or "0"),
                pii_applies=int(pii_applies or "0"),
            )
        except (ValidationError, ValueError):
            return feature_page(request, store, signed_in, feature_id, STAGE_REFUSED, 422)
        store.set_feature_path_flags(
            signed_in["organization_id"],
            feature_id,
            form.changes_production,
            form.architecture_applies,
            form.pii_applies,
        )
        return RedirectResponse(f"/features/{feature_id}", status_code=303)

    @app.post("/stories/{story_id}/production")
    def post_story_production(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        story_id: int,
        changes_production: Annotated[str, Form()] = "",
    ):
        found, response = guard(request, store, story_id, "story")
        if response is not None:
            return response
        signed_in, _item = found
        try:
            form = ProductionFlagForm(changes_production=int(changes_production or "0"))
        except (ValidationError, ValueError):
            return story_page(request, store, signed_in, story_id, STAGE_REFUSED, 422)
        store.set_story_production(signed_in["organization_id"], story_id, form.changes_production)
        return RedirectResponse(f"/stories/{story_id}", status_code=303)

    def evidence_page(request, store, signed_in, kind, record_id):
        item = load(store, signed_in["organization_id"], kind, record_id)
        if item is None:
            raise HTTPException(status_code=404)
        stream_id = _stream_id(store, signed_in["organization_id"], kind, item)
        if stream_id is None or not allows(access_scope(store, signed_in["id"]), "stream", stream_id):
            return templates.TemplateResponse(
                request,
                "refused.html",
                {
                    "message": RECORD_HIDDEN,
                    **shell(store, signed_in["organization_id"], None, user_id=signed_in["id"]),
                },
                status_code=422,
            )
        organization_id = signed_in["organization_id"]
        if kind == "feature":
            breadcrumb = feature_breadcrumb(store, organization_id, item)
            root = "features"
        else:
            breadcrumb = story_breadcrumb(store, organization_id, item)
            root = "stories"
        breadcrumb[-1] = {"name": item["name"], "href": f"/{root}/{record_id}"}
        breadcrumb.append({"name": "Evidence", "href": None})
        return templates.TemplateResponse(
            request,
            "evidence.html",
            {
                "work": item,
                "entries": store.list_evidence(kind, record_id),
                "breadcrumb": breadcrumb,
                **shell(store, organization_id, kind, record_id, signed_in["id"]),
            },
        )

    @app.get("/features/{feature_id}/evidence")
    def get_feature_evidence(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        feature_id: int,
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        return evidence_page(request, store, signed_in, "feature", feature_id)

    @app.get("/stories/{story_id}/evidence")
    def get_story_evidence(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        story_id: int,
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        return evidence_page(request, store, signed_in, "story", story_id)

    def add_item_routes(kind: str):
        prefix = "features" if kind == "feature" else "stories"

        @app.post(f"/{prefix}/{{record_id}}/policy-approval")
        def post_policy_approval(
            request: Request,
            store: Annotated[Database, Depends(get_store)],
            record_id: int,
            policy_id: Annotated[str, Form()] = "",
            person_id: Annotated[str, Form()] = "",
        ):
            found, response = guard(request, store, record_id, kind)
            if response is not None:
                return response
            signed_in, _item = found
            try:
                form = PolicyApprovalForm(policy_id=int(policy_id), person_id=int(person_id))
            except (ValidationError, ValueError):
                return page(kind)(request, store, signed_in, record_id, APPROVAL_REFUSED, 422)
            if not store.approve_policy(
                signed_in["organization_id"],
                form.policy_id,
                kind,
                record_id,
                form.person_id,
                now_stamp(),
            ):
                return page(kind)(request, store, signed_in, record_id, APPROVAL_REFUSED, 422)
            return RedirectResponse(f"/{prefix}/{record_id}", status_code=303)

        @app.post(f"/{prefix}/{{record_id}}/criteria")
        def post_criteria(
            request: Request,
            store: Annotated[Database, Depends(get_store)],
            record_id: int,
            measure_name: Annotated[str, Form()] = "",
            threshold: Annotated[str, Form()] = "",
            dataset_label: Annotated[str, Form()] = "",
            latency_target: Annotated[str, Form()] = "",
        ):
            found, response = guard(request, store, record_id, kind)
            if response is not None:
                return response
            signed_in, _item = found
            try:
                form = CriterionForm(
                    measure_name=measure_name,
                    threshold=threshold,
                    dataset_label=dataset_label,
                    latency_target=latency_target,
                )
            except ValidationError:
                return page(kind)(request, store, signed_in, record_id, CRITERIA_REFUSED, 422)
            if not store.set_criteria(
                signed_in["organization_id"],
                kind,
                record_id,
                form.measure_name,
                form.threshold,
                form.dataset_label,
                form.latency_target,
            ):
                raise HTTPException(status_code=404)
            return RedirectResponse(f"/{prefix}/{record_id}", status_code=303)

        @app.post(f"/{prefix}/{{record_id}}/agent-action")
        def post_agent(
            request: Request,
            store: Annotated[Database, Depends(get_store)],
            record_id: int,
            action: Annotated[str, Form()] = "",
            actor_name: Annotated[str, Form()] = "",
            before_text: Annotated[str, Form()] = "",
            after_text: Annotated[str, Form()] = "",
        ):
            found, response = guard(request, store, record_id, kind)
            if response is not None:
                return response
            signed_in, _item = found
            try:
                form = AgentActionForm(
                    action=action,
                    actor_name=actor_name,
                    before_text=before_text,
                    after_text=after_text,
                )
            except ValidationError:
                return page(kind)(request, store, signed_in, record_id, AGENT_REFUSED, 422)
            store.add_evidence(
                signed_in["organization_id"],
                kind,
                record_id,
                form.action,
                "agent",
                form.actor_name,
                now_stamp(),
                form.before_text,
                form.after_text,
            )
            return RedirectResponse(f"/{prefix}/{record_id}/evidence", status_code=303)

        post_policy_approval.__name__ = f"post_{kind}_policy_approval"
        post_criteria.__name__ = f"post_{kind}_criteria"
        post_agent.__name__ = f"post_{kind}_agent"

    add_item_routes("feature")
    add_item_routes("story")


def _stream_id(store: Database, organization_id: int, kind: str, item: dict) -> int | None:
    feature = item if kind == "feature" else store.get_feature(organization_id, item["feature_id"])
    if feature is None:
        return None
    initiative = store.get_initiative(organization_id, feature["initiative_id"])
    if initiative is None:
        return None
    goal = store.get_goal(organization_id, initiative["goal_id"])
    if goal is None:
        return None
    return goal["value_stream_id"]


def stage_context(store: Database, kind: str, item: dict) -> dict:
    return {
        "history": store.list_stage_changes(kind, item["id"]),
        "done_items": done_items(store, kind, item),
        "people": store.list_people(item["organization_id"]),
        "stages": STAGES,
        "blocks": store.open_blocks(item["organization_id"], kind, item["id"], item["stage"]),
    }
