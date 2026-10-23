from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.access import ACTION_REFUSED
from app.navigation import group_breadcrumb, shell
from app.schemas import (
    CapacityForm,
    ConfidenceForm,
    CycleForm,
    DecisionForm,
    DependencyForm,
    DependentWorkForm,
    MilestoneForm,
    OutcomeActualForm,
    OutcomeForm,
    OutcomeLinkForm,
    ReviewForm,
    RiskForm,
)
from app.store import Database, get_store

NAME_REQUIRED = "A name is required."
DATE_REFUSED = "That date was refused."
END_BEFORE_START = "The end is before the start."
CYCLE_NEEDS_GROUP = "A cycle needs a delivery group."
OUTCOME_REQUIRED = "An outcome needs a description and a planned signal."
DEPENDENCY_REQUIRED = "A dependency needs a description, an owner, and a needed-by date."
WORK_REQUIRED = "Dependent work needs the change, what done looks like, and a needed-by date."
RISK_REFUSED = "That risk was refused."
SCORE_REFUSED = "That score was refused."
LINK_REFUSED = "That link was refused."
FACILITATOR_EMPTY = "The facilitator seat is empty."
NEEDS_FACILITATOR = "That action needs the group facilitator."
REVIEW_REFUSED = "That review was refused."


def _optional_int(value: str) -> int | None:
    text = str(value).strip()
    if not text.isdigit():
        return None
    number = int(text)
    return number if number >= 1 else None


def _message(exc: ValidationError, empty: str) -> str:
    for error in exc.errors():
        if "order" in str(error.get("ctx", "")) or error.get("msg") == "Value error, order":
            return END_BEFORE_START
        loc = error["loc"][-1] if error["loc"] else ""
        if loc in {"name", "description", "planned_signal", "needed", "done_looks_like", "note", "statement"}:
            return empty
    return DATE_REFUSED


def _average(scores: list[int]) -> str:
    if not scores:
        return ""
    value = sum(scores) / len(scores)
    text = f"{value:.1f}"
    return text[:-2] if text.endswith(".0") else text


def register_cycles(
    app: FastAPI,
    templates: Jinja2Templates,
    group_page,
    signed_in_user,
    sign_in,
    edit_blocked,
    hidden,
) -> None:
    def render(request, store, signed_in, current, current_id, breadcrumb, status_code=200, **context):
        context.update(
            shell(store, signed_in["organization_id"], current, current_id, signed_in["id"])
        )
        context["breadcrumb"] = breadcrumb
        return templates.TemplateResponse(request, "cycle.html", context, status_code=status_code)

    def refused(request, store, signed_in, message: str):
        return templates.TemplateResponse(
            request,
            "refused.html",
            {
                "message": message,
                **shell(store, signed_in["organization_id"], None, user_id=signed_in["id"]),
            },
            status_code=422,
        )

    def breadcrumb(store, organization_id, cycle):
        group = store.get_delivery_group(organization_id, cycle["delivery_group_id"])
        crumbs = group_breadcrumb(store, organization_id, group)
        crumbs[-1] = {"name": group["name"], "href": f"/delivery-groups/{group['id']}"}
        crumbs.append({"name": cycle["name"], "href": None})
        return crumbs

    def cycle_page(request, store, signed_in, cycle_id: int, error, status_code=200):
        organization_id = signed_in["organization_id"]
        cycle = store.get_cycle(organization_id, cycle_id)
        if cycle is None:
            raise HTTPException(status_code=404)
        blocked = hidden(store, signed_in, "group", cycle["delivery_group_id"])
        if blocked is not None:
            return refused(request, store, signed_in, blocked)
        group = store.get_delivery_group(organization_id, cycle["delivery_group_id"])
        teams = store.list_teams(group["id"])
        features = store.features_for_stream(group["value_stream_id"])
        outcomes = store.list_cycle_outcomes(cycle_id)
        for outcome in outcomes:
            outcome["links"] = store.list_outcome_links(outcome["id"])
        reviews = store.list_cycle_reviews(cycle_id)
        votes = store.list_cycle_votes(cycle_id)
        facilitator = store.facilitator_person_id(organization_id, group["id"])
        return render(
            request,
            store,
            signed_in,
            "delivery_group",
            group["id"],
            breadcrumb(store, organization_id, cycle),
            status_code,
            cycle=cycle,
            group=group,
            teams=teams,
            features=features,
            stories=store.stories_for_group(group["id"]),
            people=store.list_people(organization_id),
            outcomes=outcomes,
            milestones=store.list_milestones(cycle_id),
            dependencies=store.list_dependencies(cycle_id),
            dependent_work=store.list_dependent_work(cycle_id),
            architecture_features=[item for item in features if item["architecture_applies"]],
            pii_features=[item for item in features if item["pii_applies"]],
            reviews=reviews,
            risks=store.list_risks(cycle_id),
            votes=votes,
            average=_average([item["score"] for item in votes]),
            capacities=store.list_capacities(cycle_id),
            decisions=store.list_decisions(cycle_id),
            facilitator_id=facilitator,
            error=error,
        )

    def editable(request, store, cycle_id):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return None, sign_in()
        cycle = store.get_cycle(signed_in["organization_id"], cycle_id)
        if cycle is None:
            raise HTTPException(status_code=404)
        blocked = hidden(store, signed_in, "group", cycle["delivery_group_id"])
        if blocked is not None:
            return None, refused(request, store, signed_in, blocked)
        if edit_blocked(store, signed_in) is not None:
            return None, cycle_page(request, store, signed_in, cycle_id, ACTION_REFUSED, 422)
        return (signed_in, cycle), None

    @app.post("/cycles")
    def post_cycle(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        name: Annotated[str, Form()] = "",
        starts_on: Annotated[str, Form()] = "",
        ends_on: Annotated[str, Form()] = "",
        delivery_group_id: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        parsed = _optional_int(delivery_group_id)
        if parsed is None or store.get_delivery_group(signed_in["organization_id"], parsed) is None:
            return refused(request, store, signed_in, CYCLE_NEEDS_GROUP)
        blocked = hidden(store, signed_in, "group", parsed)
        if blocked is not None:
            return refused(request, store, signed_in, blocked)
        if edit_blocked(store, signed_in) is not None:
            return group_page(request, store, signed_in, parsed, ACTION_REFUSED, 422)
        try:
            form = CycleForm(
                name=name, starts_on=starts_on, ends_on=ends_on, delivery_group_id=parsed
            )
        except ValidationError as exc:
            return group_page(request, store, signed_in, parsed, _message(exc, NAME_REQUIRED), 422)
        created = store.create_cycle(
            signed_in["organization_id"],
            form.delivery_group_id,
            form.name,
            form.starts_on,
            form.ends_on,
        )
        if created is None:
            return refused(request, store, signed_in, CYCLE_NEEDS_GROUP)
        return RedirectResponse(f"/cycles/{created}", status_code=303)

    @app.get("/cycles/{cycle_id}")
    def get_cycle_page(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        cycle_id: int,
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        return cycle_page(request, store, signed_in, cycle_id, None)

    @app.post("/cycles/{cycle_id}/outcomes")
    def post_outcome(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        cycle_id: int,
        description: Annotated[str, Form()] = "",
        planned_signal: Annotated[str, Form()] = "",
        team_id: Annotated[str, Form()] = "",
    ):
        found, response = editable(request, store, cycle_id)
        if response is not None:
            return response
        signed_in, cycle = found
        parsed_team = _optional_int(team_id)
        try:
            form = OutcomeForm(
                description=description, planned_signal=planned_signal, team_id=parsed_team
            )
        except ValidationError:
            return cycle_page(request, store, signed_in, cycle_id, OUTCOME_REQUIRED, 422)
        if form.team_id is not None and store.get_team(signed_in["organization_id"], form.team_id) is None:
            return cycle_page(request, store, signed_in, cycle_id, OUTCOME_REQUIRED, 422)
        store.add_outcome(
            signed_in["organization_id"],
            cycle["id"],
            form.team_id,
            form.description,
            form.planned_signal,
        )
        return RedirectResponse(f"/cycles/{cycle_id}", status_code=303)

    @app.post("/outcomes/{outcome_id}/actual")
    def post_actual(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        outcome_id: int,
        actual_signal: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        cycle_for_outcome = store.outcome_cycle_id(signed_in["organization_id"], outcome_id)
        if cycle_for_outcome is None:
            raise HTTPException(status_code=404)
        found, response = editable(request, store, cycle_for_outcome)
        if response is not None:
            return response
        try:
            form = OutcomeActualForm(actual_signal=actual_signal)
        except ValidationError:
            return cycle_page(request, store, signed_in, cycle_for_outcome, OUTCOME_REQUIRED, 422)
        store.set_outcome_actual(outcome_id, form.actual_signal)
        return RedirectResponse(f"/cycles/{cycle_for_outcome}", status_code=303)

    @app.post("/cycles/{cycle_id}/milestones")
    def post_milestone(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        cycle_id: int,
        name: Annotated[str, Form()] = "",
        happens_on: Annotated[str, Form()] = "",
    ):
        found, response = editable(request, store, cycle_id)
        if response is not None:
            return response
        signed_in, cycle = found
        try:
            form = MilestoneForm(name=name, happens_on=happens_on)
        except ValidationError as exc:
            return cycle_page(request, store, signed_in, cycle_id, _message(exc, NAME_REQUIRED), 422)
        store.add_milestone(signed_in["organization_id"], cycle["id"], form.name, form.happens_on)
        return RedirectResponse(f"/cycles/{cycle_id}", status_code=303)

    @app.post("/cycles/{cycle_id}/dependencies")
    def post_dependency(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        cycle_id: int,
        description: Annotated[str, Form()] = "",
        owner_person_id: Annotated[str, Form()] = "",
        needed_by: Annotated[str, Form()] = "",
        opened_on: Annotated[str, Form()] = "",
        status: Annotated[str, Form()] = "open",
        providing_team_id: Annotated[str, Form()] = "",
    ):
        found, response = editable(request, store, cycle_id)
        if response is not None:
            return response
        signed_in, cycle = found
        try:
            form = DependencyForm(
                description=description,
                owner_person_id=int(owner_person_id),
                needed_by=needed_by,
                opened_on=opened_on,
                status=status or "open",
                providing_team_id=_optional_int(providing_team_id),
            )
        except (ValidationError, ValueError):
            return cycle_page(request, store, signed_in, cycle_id, DEPENDENCY_REQUIRED, 422)
        if store.get_person(signed_in["organization_id"], form.owner_person_id) is None:
            return cycle_page(request, store, signed_in, cycle_id, DEPENDENCY_REQUIRED, 422)
        store.add_dependency(
            signed_in["organization_id"],
            cycle["id"],
            description=form.description,
            owner_person_id=form.owner_person_id,
            needed_by=form.needed_by,
            status=form.status,
            opened_on=form.opened_on,
            providing_team_id=form.providing_team_id,
        )
        return RedirectResponse(f"/cycles/{cycle_id}", status_code=303)

    @app.post("/cycles/{cycle_id}/dependent-work")
    def post_dependent_work(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        cycle_id: int,
        feature_id: Annotated[str, Form()] = "",
        needed: Annotated[str, Form()] = "",
        done_looks_like: Annotated[str, Form()] = "",
        needed_by: Annotated[str, Form()] = "",
        status: Annotated[str, Form()] = "open",
        providing_team_id: Annotated[str, Form()] = "",
    ):
        found, response = editable(request, store, cycle_id)
        if response is not None:
            return response
        signed_in, cycle = found
        try:
            form = DependentWorkForm(
                feature_id=int(feature_id),
                needed=needed,
                done_looks_like=done_looks_like,
                needed_by=needed_by,
                status=status or "open",
                providing_team_id=_optional_int(providing_team_id),
            )
        except (ValidationError, ValueError):
            return cycle_page(request, store, signed_in, cycle_id, WORK_REQUIRED, 422)
        if store.get_feature(signed_in["organization_id"], form.feature_id) is None:
            return cycle_page(request, store, signed_in, cycle_id, WORK_REQUIRED, 422)
        store.add_dependent_work(
            signed_in["organization_id"],
            cycle["id"],
            feature_id=form.feature_id,
            needed=form.needed,
            done_looks_like=form.done_looks_like,
            needed_by=form.needed_by,
            status=form.status,
            providing_team_id=form.providing_team_id,
        )
        return RedirectResponse(f"/cycles/{cycle_id}", status_code=303)

    @app.post("/cycles/{cycle_id}/reviews")
    def post_review(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        cycle_id: int,
        kind: Annotated[str, Form()] = "",
        feature_id: Annotated[str, Form()] = "",
        reviewer_person_id: Annotated[str, Form()] = "",
        reviewed_on: Annotated[str, Form()] = "",
        result: Annotated[str, Form()] = "",
    ):
        found, response = editable(request, store, cycle_id)
        if response is not None:
            return response
        signed_in, _cycle = found
        if kind not in {"architecture", "pii"}:
            return cycle_page(request, store, signed_in, cycle_id, REVIEW_REFUSED, 422)
        try:
            form = ReviewForm(
                feature_id=int(feature_id),
                reviewer_person_id=int(reviewer_person_id),
                reviewed_on=reviewed_on,
                result=result,
            )
        except (ValidationError, ValueError):
            return cycle_page(request, store, signed_in, cycle_id, REVIEW_REFUSED, 422)
        feature = store.get_feature(signed_in["organization_id"], form.feature_id)
        applies = feature is not None and (
            feature["architecture_applies"] if kind == "architecture" else feature["pii_applies"]
        )
        if not applies or store.get_person(signed_in["organization_id"], form.reviewer_person_id) is None:
            return cycle_page(request, store, signed_in, cycle_id, REVIEW_REFUSED, 422)
        store.save_review(
            signed_in["organization_id"],
            cycle_id,
            feature_id=form.feature_id,
            kind=kind,
            reviewer_person_id=form.reviewer_person_id,
            reviewed_on=form.reviewed_on,
            result=form.result,
        )
        return RedirectResponse(f"/cycles/{cycle_id}", status_code=303)

    @app.post("/cycles/{cycle_id}/risks")
    def post_risk(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        cycle_id: int,
        description: Annotated[str, Form()] = "",
        state: Annotated[str, Form()] = "open",
    ):
        found, response = editable(request, store, cycle_id)
        if response is not None:
            return response
        signed_in, cycle = found
        try:
            form = RiskForm(description=description, state=state or "open")
        except ValidationError:
            return cycle_page(request, store, signed_in, cycle_id, RISK_REFUSED, 422)
        store.add_risk(signed_in["organization_id"], cycle["id"], form.description, form.state)
        return RedirectResponse(f"/cycles/{cycle_id}", status_code=303)

    @app.post("/risks/{risk_id}")
    def post_risk_state(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        risk_id: int,
        state: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        row = store.get_risk(signed_in["organization_id"], risk_id)
        if row is None:
            raise HTTPException(status_code=404)
        found, response = editable(request, store, row["cycle_id"])
        if response is not None:
            return response
        try:
            form = RiskForm(description=row["description"], state=state)
        except ValidationError:
            return cycle_page(request, store, signed_in, row["cycle_id"], RISK_REFUSED, 422)
        store.set_risk_state(risk_id, form.state)
        return RedirectResponse(f"/cycles/{row['cycle_id']}", status_code=303)

    @app.post("/cycles/{cycle_id}/confidence")
    def post_confidence(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        cycle_id: int,
        person_id: Annotated[str, Form()] = "",
        score: Annotated[str, Form()] = "",
    ):
        found, response = editable(request, store, cycle_id)
        if response is not None:
            return response
        signed_in, _cycle = found
        try:
            form = ConfidenceForm(person_id=int(person_id), score=int(score))
        except (ValidationError, ValueError):
            return cycle_page(request, store, signed_in, cycle_id, SCORE_REFUSED, 422)
        if store.get_person(signed_in["organization_id"], form.person_id) is None:
            return cycle_page(request, store, signed_in, cycle_id, SCORE_REFUSED, 422)
        store.save_confidence(
            signed_in["organization_id"], cycle_id, form.person_id, form.score
        )
        return RedirectResponse(f"/cycles/{cycle_id}", status_code=303)

    @app.post("/cycles/{cycle_id}/capacity")
    def post_capacity(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        cycle_id: int,
        team_id: Annotated[str, Form()] = "",
        note: Annotated[str, Form()] = "",
    ):
        found, response = editable(request, store, cycle_id)
        if response is not None:
            return response
        signed_in, cycle = found
        try:
            form = CapacityForm(team_id=int(team_id), note=note)
        except (ValidationError, ValueError):
            return cycle_page(request, store, signed_in, cycle_id, NAME_REQUIRED, 422)
        team = store.get_team(signed_in["organization_id"], form.team_id)
        if team is None or team["delivery_group_id"] != cycle["delivery_group_id"]:
            return cycle_page(request, store, signed_in, cycle_id, NAME_REQUIRED, 422)
        store.save_capacity(signed_in["organization_id"], cycle_id, form.team_id, form.note)
        return RedirectResponse(f"/cycles/{cycle_id}", status_code=303)

    @app.post("/cycles/{cycle_id}/links")
    def post_link(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        cycle_id: int,
        outcome_id: Annotated[str, Form()] = "",
        feature_id: Annotated[str, Form()] = "",
        story_id: Annotated[str, Form()] = "",
    ):
        found, response = editable(request, store, cycle_id)
        if response is not None:
            return response
        signed_in, _cycle = found
        try:
            form = OutcomeLinkForm(
                outcome_id=int(outcome_id),
                feature_id=_optional_int(feature_id),
                story_id=_optional_int(story_id),
            )
        except (ValidationError, ValueError):
            return cycle_page(request, store, signed_in, cycle_id, LINK_REFUSED, 422)
        if not store.outcome_in_cycle(form.outcome_id, cycle_id):
            return cycle_page(request, store, signed_in, cycle_id, LINK_REFUSED, 422)
        if form.feature_id is not None and store.get_feature(
            signed_in["organization_id"], form.feature_id
        ) is None:
            return cycle_page(request, store, signed_in, cycle_id, LINK_REFUSED, 422)
        if form.story_id is not None and store.get_story(signed_in["organization_id"], form.story_id) is None:
            return cycle_page(request, store, signed_in, cycle_id, LINK_REFUSED, 422)
        store.add_outcome_link(
            signed_in["organization_id"],
            form.outcome_id,
            form.feature_id,
            form.story_id,
        )
        return RedirectResponse(f"/cycles/{cycle_id}", status_code=303)

    @app.post("/cycles/{cycle_id}/decisions")
    def post_decision(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        cycle_id: int,
        statement: Annotated[str, Form()] = "",
        person_id: Annotated[str, Form()] = "",
    ):
        found, response = editable(request, store, cycle_id)
        if response is not None:
            return response
        signed_in, cycle = found
        facilitator = store.facilitator_person_id(
            signed_in["organization_id"], cycle["delivery_group_id"]
        )
        if facilitator is None:
            return cycle_page(request, store, signed_in, cycle_id, FACILITATOR_EMPTY, 422)
        try:
            form = DecisionForm(statement=statement, person_id=int(person_id))
        except (ValidationError, ValueError):
            return cycle_page(request, store, signed_in, cycle_id, NAME_REQUIRED, 422)
        held = store.person_role(signed_in["organization_id"], form.person_id)
        if (
            held is None
            or held["role"] != "group_facilitator"
            or held["delivery_group_id"] != cycle["delivery_group_id"]
        ):
            return cycle_page(request, store, signed_in, cycle_id, NEEDS_FACILITATOR, 422)
        store.add_group_decision(
            signed_in["organization_id"], cycle_id, form.statement, form.person_id
        )
        return RedirectResponse(f"/cycles/{cycle_id}", status_code=303)
