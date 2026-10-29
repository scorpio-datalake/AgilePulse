from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.access import ACTION_REFUSED, RECORD_HIDDEN, access_scope, allows, allows_edit
from app.flow import register_flow
from app.measures import with_delay_cost
from app.stages import after_definition_edit, register_stages, stage_context
from app.navigation import (
    feature_breadcrumb,
    goal_breadcrumb,
    initiative_breadcrumb,
    shell,
    story_breadcrumb,
    team_breadcrumb,
)
from app.organization import ROLE_LABELS
from app.schemas import (
    FeatureForm,
    GoalForm,
    InitiativeForm,
    InitiativeStateForm,
    NameForm,
    PriorityForm,
    SizingForm,
    StoryFeatureForm,
    StoryForm,
)
from app.store import Database, get_store

NAME_REQUIRED = "A name is required."
GOAL_NEEDS_STREAM = "A goal needs a value stream."
INITIATIVE_NEEDS_GOAL = "An initiative needs a goal."
FEATURE_NEEDS_INITIATIVE = "A feature needs an initiative."
STORY_NEEDS_FEATURE = "A story needs a feature."
STATE_REFUSED = "That state was refused."
KIND_REFUSED = "That kind was refused."
PRIORITY_REFUSED = "Those priority numbers were refused."
ESTIMATE_REFUSED = "That estimate was refused."
SIZING_REFUSED = "That sizing method was refused."

KIND_LABELS = {
    "feature": "Feature",
    "platform": "Platform",
    "prototype": "Prototype",
    "experiment": "Experiment",
}
SHIRT_FIELDS = {
    "XS": "size_xs",
    "S": "size_s",
    "M": "size_m",
    "L": "size_l",
    "XL": "size_xl",
}


def register_work(app: FastAPI, templates: Jinja2Templates) -> None:
    def signed_in_user(request: Request, store: Database):
        user_id = request.session.get("user_id")
        if not isinstance(user_id, int):
            return None
        found = store.user_by_id(user_id)
        if found is None or found["organization_id"] is None:
            return None
        return found

    def sign_in():
        return RedirectResponse("/sign-in", status_code=303)

    def render(
        request,
        name,
        store,
        signed_in,
        current,
        current_id=None,
        breadcrumb=None,
        status_code=200,
        **context,
    ):
        context.update(
            shell(store, signed_in["organization_id"], current, current_id, signed_in["id"])
        )
        if breadcrumb is not None:
            context["breadcrumb"] = breadcrumb
        return templates.TemplateResponse(request, name, context, status_code=status_code)

    def refused(request, store, signed_in, message: str):
        return render(
            request,
            "refused.html",
            store,
            signed_in,
            None,
            status_code=422,
            message=message,
        )

    def stream_id_for(store, organization_id, kind: str, record_id: int) -> int | None:
        if kind == "goal":
            goal = store.get_goal(organization_id, record_id)
            return None if goal is None else goal["value_stream_id"]
        if kind == "initiative":
            initiative = store.get_initiative(organization_id, record_id)
            if initiative is None:
                return None
            return stream_id_for(store, organization_id, "goal", initiative["goal_id"])
        if kind == "feature":
            feature = store.get_feature(organization_id, record_id)
            if feature is None:
                return None
            return stream_id_for(store, organization_id, "initiative", feature["initiative_id"])
        story = store.get_story(organization_id, record_id)
        if story is None:
            return None
        return stream_id_for(store, organization_id, "feature", story["feature_id"])

    def hidden_stream(store, signed_in, stream_id: int) -> str | None:
        if allows(access_scope(store, signed_in["id"]), "stream", stream_id):
            return None
        return RECORD_HIDDEN

    def edit_blocked(store, signed_in) -> str | None:
        if allows_edit(access_scope(store, signed_in["id"])):
            return None
        return ACTION_REFUSED

    def goal_page(request, store, signed_in, goal_id: int, error, status_code=200):
        organization_id = signed_in["organization_id"]
        goal = store.get_goal(organization_id, goal_id)
        if goal is None:
            raise HTTPException(status_code=404)
        parent = stream_id_for(store, organization_id, "goal", goal_id)
        if parent is None or hidden_stream(store, signed_in, parent) is not None:
            return refused(request, store, signed_in, RECORD_HIDDEN)
        return render(
            request,
            "goal.html",
            store,
            signed_in,
            "goal",
            goal_id,
            goal_breadcrumb(store, organization_id, goal),
            status_code,
            goal=goal,
            initiatives=store.list_initiatives(goal_id),
            error=error,
        )

    def initiative_page(request, store, signed_in, initiative_id: int, error, status_code=200):
        organization_id = signed_in["organization_id"]
        initiative = store.get_initiative(organization_id, initiative_id)
        if initiative is None:
            raise HTTPException(status_code=404)
        parent = stream_id_for(store, organization_id, "initiative", initiative_id)
        if parent is None or hidden_stream(store, signed_in, parent) is not None:
            return refused(request, store, signed_in, RECORD_HIDDEN)
        return render(
            request,
            "initiative.html",
            store,
            signed_in,
            "initiative",
            initiative_id,
            initiative_breadcrumb(store, organization_id, initiative),
            status_code,
            initiative=initiative,
            features=_kinds(with_delay_cost(store.list_features(initiative_id))),
            error=error,
        )

    def feature_page(request, store, signed_in, feature_id: int, error, status_code=200, tab=None):
        organization_id = signed_in["organization_id"]
        feature = store.get_feature(organization_id, feature_id)
        if feature is None:
            raise HTTPException(status_code=404)
        parent = stream_id_for(store, organization_id, "feature", feature_id)
        if parent is None or hidden_stream(store, signed_in, parent) is not None:
            return refused(request, store, signed_in, RECORD_HIDDEN)
        feature["kind_label"] = KIND_LABELS[feature["kind"]]
        feature["delay_cost"] = with_delay_cost([feature])[0]["delay_cost"]
        path = stage_context(store, "feature", feature)
        if tab not in {"stories", "feature", "path"}:
            tab = "path" if error else "stories"
        return render(
            request,
            "feature.html",
            store,
            signed_in,
            "feature",
            feature_id,
            feature_breadcrumb(store, organization_id, feature),
            status_code,
            feature=feature,
            stories=_kinds(store.list_stories(feature_id)),
            feature_choices=store.list_features(feature["initiative_id"]),
            history=path["history"],
            done_items=path["done_items"],
            people=path["people"],
            stages=path["stages"],
            blocks=path["blocks"],
            tab=tab,
            error=error,
        )

    def story_page(request, store, signed_in, story_id: int, error, status_code=200):
        organization_id = signed_in["organization_id"]
        story = store.get_story(organization_id, story_id)
        if story is None:
            raise HTTPException(status_code=404)
        parent = stream_id_for(store, organization_id, "story", story_id)
        if parent is None or hidden_stream(store, signed_in, parent) is not None:
            return refused(request, store, signed_in, RECORD_HIDDEN)
        story["kind_label"] = KIND_LABELS[story["kind"]]
        path = stage_context(store, "story", story)
        scope = access_scope(store, signed_in["id"])
        teams = store.list_teams_for_sizing(organization_id)
        if scope is not None:
            teams = [team for team in teams if team["id"] in scope["team"]]
        return render(
            request,
            "story.html",
            store,
            signed_in,
            "story",
            story_id,
            story_breadcrumb(store, organization_id, story),
            status_code,
            story=story,
            teams=teams,
            history=path["history"],
            done_items=path["done_items"],
            people=path["people"],
            stages=path["stages"],
            blocks=path["blocks"],
            error=error,
        )

    def stream_error(request, store, signed_in, value_stream_id: int, message: str):
        organization_id = signed_in["organization_id"]
        stream = store.get_value_stream(organization_id, value_stream_id)
        if stream is None:
            return refused(request, store, signed_in, message)
        assignments = store.list_role_assignments(
            organization_id, value_stream_id=value_stream_id
        )
        for assignment in assignments:
            assignment["label"] = ROLE_LABELS[assignment["role"]]
        from app.navigation import stream_breadcrumb

        return render(
            request,
            "value_stream.html",
            store,
            signed_in,
            "value_stream",
            value_stream_id,
            stream_breadcrumb(store, organization_id, stream),
            422,
            stream=stream,
            groups=store.list_delivery_groups(value_stream_id),
            assignments=assignments,
            error=message,
        )

    @app.post("/goals")
    def post_goal(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        name: Annotated[str, Form()] = "",
        value_stream_id: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        parsed = _optional_int(value_stream_id)
        if parsed is None or store.get_value_stream(signed_in["organization_id"], parsed) is None:
            return refused(request, store, signed_in, GOAL_NEEDS_STREAM)
        blocked = hidden_stream(store, signed_in, parsed)
        if blocked is not None:
            return refused(request, store, signed_in, blocked)
        if edit_blocked(store, signed_in) is not None:
            return stream_error(request, store, signed_in, parsed, ACTION_REFUSED)
        try:
            form = GoalForm(name=name, value_stream_id=parsed)
        except ValidationError:
            return stream_error(request, store, signed_in, parsed, _name_or(GOAL_NEEDS_STREAM))
        created = store.create_goal(signed_in["organization_id"], form.value_stream_id, form.name)
        if created is None:
            return refused(request, store, signed_in, GOAL_NEEDS_STREAM)
        return RedirectResponse(f"/goals/{created}", status_code=303)

    @app.get("/goals/{goal_id}")
    def get_goal_page(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        goal_id: int,
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        return goal_page(request, store, signed_in, goal_id, None)

    @app.post("/goals/{goal_id}")
    def post_goal_name(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        goal_id: int,
        name: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        if edit_blocked(store, signed_in) is not None:
            return goal_page(request, store, signed_in, goal_id, ACTION_REFUSED, 422)
        try:
            form = NameForm(name=name)
        except ValidationError:
            return goal_page(request, store, signed_in, goal_id, NAME_REQUIRED, 422)
        if not store.rename_goal(signed_in["organization_id"], goal_id, form.name):
            raise HTTPException(status_code=404)
        return RedirectResponse(f"/goals/{goal_id}", status_code=303)

    @app.post("/initiatives")
    def post_initiative(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        name: Annotated[str, Form()] = "",
        goal_id: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        parsed = _optional_int(goal_id)
        if parsed is None or store.get_goal(signed_in["organization_id"], parsed) is None:
            return refused(request, store, signed_in, INITIATIVE_NEEDS_GOAL)
        parent = stream_id_for(store, signed_in["organization_id"], "goal", parsed)
        if parent is None or hidden_stream(store, signed_in, parent) is not None:
            return refused(request, store, signed_in, RECORD_HIDDEN)
        if edit_blocked(store, signed_in) is not None:
            return goal_page(request, store, signed_in, parsed, ACTION_REFUSED, 422)
        try:
            form = InitiativeForm(name=name, goal_id=parsed)
        except ValidationError:
            return goal_page(request, store, signed_in, parsed, NAME_REQUIRED, 422)
        created = store.create_initiative(signed_in["organization_id"], form.goal_id, form.name)
        if created is None:
            return refused(request, store, signed_in, INITIATIVE_NEEDS_GOAL)
        return RedirectResponse(f"/initiatives/{created}", status_code=303)

    @app.get("/initiatives/{initiative_id}")
    def get_initiative_page(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        initiative_id: int,
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        return initiative_page(request, store, signed_in, initiative_id, None)

    @app.post("/initiatives/{initiative_id}")
    def post_initiative_name(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        initiative_id: int,
        name: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        if edit_blocked(store, signed_in) is not None:
            return initiative_page(request, store, signed_in, initiative_id, ACTION_REFUSED, 422)
        try:
            form = NameForm(name=name)
        except ValidationError:
            return initiative_page(request, store, signed_in, initiative_id, NAME_REQUIRED, 422)
        if not store.rename_initiative(signed_in["organization_id"], initiative_id, form.name):
            raise HTTPException(status_code=404)
        return RedirectResponse(f"/initiatives/{initiative_id}", status_code=303)

    @app.post("/initiatives/{initiative_id}/state")
    def post_initiative_state(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        initiative_id: int,
        state: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        if edit_blocked(store, signed_in) is not None:
            return initiative_page(request, store, signed_in, initiative_id, ACTION_REFUSED, 422)
        try:
            form = InitiativeStateForm(state=state)
        except ValidationError:
            return initiative_page(request, store, signed_in, initiative_id, STATE_REFUSED, 422)
        if not store.set_initiative_state(
            signed_in["organization_id"], initiative_id, form.state
        ):
            raise HTTPException(status_code=404)
        return RedirectResponse(f"/initiatives/{initiative_id}", status_code=303)

    @app.post("/features")
    def post_feature(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        name: Annotated[str, Form()] = "",
        initiative_id: Annotated[str, Form()] = "",
        kind: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        parsed = _optional_int(initiative_id)
        if parsed is None or store.get_initiative(signed_in["organization_id"], parsed) is None:
            return refused(request, store, signed_in, FEATURE_NEEDS_INITIATIVE)
        parent = stream_id_for(store, signed_in["organization_id"], "initiative", parsed)
        if parent is None or hidden_stream(store, signed_in, parent) is not None:
            return refused(request, store, signed_in, RECORD_HIDDEN)
        if edit_blocked(store, signed_in) is not None:
            return initiative_page(request, store, signed_in, parsed, ACTION_REFUSED, 422)
        try:
            form = FeatureForm(name=name, initiative_id=parsed, kind=kind)
        except ValidationError as exc:
            return initiative_page(
                request, store, signed_in, parsed, _name_or_kind(exc), 422
            )
        created = store.create_feature(
            signed_in["organization_id"],
            form.initiative_id,
            form.name,
            form.kind,
        )
        if created is None:
            return refused(request, store, signed_in, FEATURE_NEEDS_INITIATIVE)
        return RedirectResponse(f"/features/{created}", status_code=303)

    @app.get("/features/{feature_id}")
    def get_feature_page(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        feature_id: int,
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        return feature_page(request, store, signed_in, feature_id, None)

    @app.post("/features/{feature_id}")
    def post_feature_name(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        feature_id: int,
        name: Annotated[str, Form()] = "",
        kind: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        feature = store.get_feature(signed_in["organization_id"], feature_id)
        if feature is None:
            raise HTTPException(status_code=404)
        if edit_blocked(store, signed_in) is not None:
            return feature_page(request, store, signed_in, feature_id, ACTION_REFUSED, 422, tab="feature")
        try:
            form = FeatureForm(name=name, initiative_id=feature["initiative_id"], kind=kind)
        except ValidationError as exc:
            return feature_page(request, store, signed_in, feature_id, _name_or_kind(exc), 422, tab="feature")
        if not store.update_feature(
            signed_in["organization_id"], feature_id, form.name, form.kind
        ):
            raise HTTPException(status_code=404)
        editor = store.person_by_user_id(signed_in["id"])
        if editor is not None:
            after_definition_edit(
                store, signed_in["organization_id"], "feature", feature_id, editor["id"]
            )
        return RedirectResponse(f"/features/{feature_id}", status_code=303)

    @app.post("/features/{feature_id}/priority")
    def post_feature_priority(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        feature_id: int,
        value_sooner: Annotated[str, Form()] = "",
        urgency: Annotated[str, Form()] = "",
        risk: Annotated[str, Form()] = "",
        economic_size: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        if store.get_feature(signed_in["organization_id"], feature_id) is None:
            raise HTTPException(status_code=404)
        if edit_blocked(store, signed_in) is not None:
            return feature_page(request, store, signed_in, feature_id, ACTION_REFUSED, 422, tab="feature")
        try:
            form = PriorityForm(
                value_sooner=_optional_int(value_sooner, allow_zero=True),
                urgency=_optional_int(urgency, allow_zero=True),
                risk=_optional_int(risk, allow_zero=True),
                economic_size=_optional_int(economic_size, allow_zero=True),
            )
        except ValidationError:
            return feature_page(request, store, signed_in, feature_id, PRIORITY_REFUSED, 422, tab="feature")
        if not store.set_feature_priority(
            signed_in["organization_id"],
            feature_id,
            form.value_sooner,
            form.urgency,
            form.risk,
            form.economic_size,
        ):
            raise HTTPException(status_code=404)
        return RedirectResponse(f"/features/{feature_id}", status_code=303)

    @app.post("/stories")
    def post_story(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        name: Annotated[str, Form()] = "",
        feature_id: Annotated[str, Form()] = "",
        kind: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        parsed = _optional_int(feature_id)
        if parsed is None or store.get_feature(signed_in["organization_id"], parsed) is None:
            return refused(request, store, signed_in, STORY_NEEDS_FEATURE)
        parent = stream_id_for(store, signed_in["organization_id"], "feature", parsed)
        if parent is None or hidden_stream(store, signed_in, parent) is not None:
            return refused(request, store, signed_in, RECORD_HIDDEN)
        if edit_blocked(store, signed_in) is not None:
            return feature_page(request, store, signed_in, parsed, ACTION_REFUSED, 422, tab="stories")
        try:
            form = StoryForm(name=name, feature_id=parsed, kind=kind)
        except ValidationError as exc:
            return feature_page(request, store, signed_in, parsed, _name_or_kind(exc), 422, tab="stories")
        created = store.create_story(
            signed_in["organization_id"], form.feature_id, form.name, form.kind
        )
        if created is None:
            return refused(request, store, signed_in, STORY_NEEDS_FEATURE)
        return RedirectResponse(f"/stories/{created}", status_code=303)

    @app.post("/stories/{story_id}/feature")
    def post_story_feature(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        story_id: int,
        feature_id: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        story = store.get_story(signed_in["organization_id"], story_id)
        if story is None:
            raise HTTPException(status_code=404)
        if edit_blocked(store, signed_in) is not None:
            return story_page(request, store, signed_in, story_id, ACTION_REFUSED, 422)
        try:
            form = StoryFeatureForm(feature_id=int(feature_id))
        except (ValidationError, ValueError):
            return feature_page(request, store, signed_in, story["feature_id"], STORY_NEEDS_FEATURE, 422, tab="stories")
        if not store.set_story_feature(signed_in["organization_id"], story_id, form.feature_id):
            return feature_page(request, store, signed_in, story["feature_id"], STORY_NEEDS_FEATURE, 422, tab="stories")
        return RedirectResponse(f"/features/{form.feature_id}", status_code=303)

    @app.get("/stories/{story_id}")
    def get_story_page(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        story_id: int,
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        return story_page(request, store, signed_in, story_id, None)

    @app.post("/stories/{story_id}")
    def post_story_name(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        story_id: int,
        name: Annotated[str, Form()] = "",
        kind: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        story = store.get_story(signed_in["organization_id"], story_id)
        if story is None:
            raise HTTPException(status_code=404)
        if edit_blocked(store, signed_in) is not None:
            return story_page(request, store, signed_in, story_id, ACTION_REFUSED, 422)
        try:
            form = StoryForm(name=name, feature_id=story["feature_id"], kind=kind)
        except ValidationError as exc:
            return story_page(request, store, signed_in, story_id, _name_or_kind(exc), 422)
        if not store.update_story(
            signed_in["organization_id"], story_id, form.name, form.kind
        ):
            raise HTTPException(status_code=404)
        editor = store.person_by_user_id(signed_in["id"])
        if editor is not None:
            after_definition_edit(
                store, signed_in["organization_id"], "story", story_id, editor["id"]
            )
        return RedirectResponse(f"/stories/{story_id}", status_code=303)

    @app.post("/stories/{story_id}/estimate")
    def post_story_estimate(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        story_id: int,
        team_id: Annotated[str, Form()] = "",
        label: Annotated[str, Form()] = "",
        points: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        if store.get_story(signed_in["organization_id"], story_id) is None:
            raise HTTPException(status_code=404)
        if edit_blocked(store, signed_in) is not None:
            return story_page(request, store, signed_in, story_id, ACTION_REFUSED, 422)
        parsed_team = _optional_int(team_id)
        team = None if parsed_team is None else store.get_team(
            signed_in["organization_id"], parsed_team
        )
        if team is None or not allows(access_scope(store, signed_in["id"]), "team", team["id"]):
            return story_page(request, store, signed_in, story_id, ESTIMATE_REFUSED, 422)
        if team["sizing_method"] == "tshirt":
            field = SHIRT_FIELDS.get(label)
            if field is None:
                return story_page(request, store, signed_in, story_id, ESTIMATE_REFUSED, 422)
            stored_label = label
            stored_value = team[field]
        else:
            stored_value = _optional_int(points)
            if stored_value is None:
                return story_page(request, store, signed_in, story_id, ESTIMATE_REFUSED, 422)
            stored_label = None
        if not store.set_story_estimate(
            signed_in["organization_id"],
            story_id,
            team["id"],
            stored_label,
            stored_value,
        ):
            raise HTTPException(status_code=404)
        return RedirectResponse(f"/stories/{story_id}", status_code=303)

    @app.post("/teams/{team_id}/sizing")
    def post_team_sizing(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        team_id: int,
        method: Annotated[str, Form()] = "",
        size_xs: Annotated[str, Form()] = "",
        size_s: Annotated[str, Form()] = "",
        size_m: Annotated[str, Form()] = "",
        size_l: Annotated[str, Form()] = "",
        size_xl: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        team = store.get_team(signed_in["organization_id"], team_id)
        if team is None:
            raise HTTPException(status_code=404)
        if not allows(access_scope(store, signed_in["id"]), "team", team_id):
            return refused(request, store, signed_in, RECORD_HIDDEN)
        if edit_blocked(store, signed_in) is not None:
            return _team_error(request, store, signed_in, team, ACTION_REFUSED)
        try:
            form = SizingForm(
                method=method,
                size_xs=_optional_int(size_xs),
                size_s=_optional_int(size_s),
                size_m=_optional_int(size_m),
                size_l=_optional_int(size_l),
                size_xl=_optional_int(size_xl),
            )
        except ValidationError:
            return _team_error(request, store, signed_in, team, SIZING_REFUSED)
        if not store.save_team_sizing(
            signed_in["organization_id"],
            team_id,
            form.method,
            form.size_xs,
            form.size_s,
            form.size_m,
            form.size_l,
            form.size_xl,
        ):
            raise HTTPException(status_code=404)
        return RedirectResponse(f"/teams/{team_id}", status_code=303)

    def _team_error(request, store, signed_in, team, message: str):

        organization_id = signed_in["organization_id"]
        members = store.list_members(organization_id, team_id=team["id"])
        for member in members:
            member["seat"] = ROLE_LABELS.get(member.get("role") or "", "")
        people = store.list_people(organization_id)
        for person in people:
            person["role_label"] = ROLE_LABELS.get(person.get("role") or "", "")
        return render(
            request,
            "team.html",
            store,
            signed_in,
            "team",
            team["id"],
            team_breadcrumb(store, organization_id, team),
            422,
            team=team,
            members=members,
            people=people,
            error=message,
            **_execution(store, signed_in, team),
        )

    def _execution(store, signed_in, team):
        from app.iterations import execution_context

        group_teams = store.list_teams(team["delivery_group_id"])
        return {
            **execution_context(store, signed_in, team),
            "team_choices": group_teams,
        }

    register_stages(app, templates, feature_page, story_page, signed_in_user, sign_in, edit_blocked)
    register_flow(app, templates, signed_in_user, sign_in)


def _optional_int(value: str | int | None, allow_zero: bool = False) -> int | None:
    if isinstance(value, int):
        if value > 0 or (allow_zero and value == 0):
            return value
        return None
    if value is None:
        return None
    text = str(value).strip()
    if not text.isdigit():
        return None
    number = int(text)
    if number < 1 and not (allow_zero and number == 0):
        return None
    return number


def _name_or(parent_message: str) -> str:
    return NAME_REQUIRED if parent_message else parent_message


def _name_or_kind(exc: ValidationError) -> str:
    for error in exc.errors():
        if error["loc"] and error["loc"][-1] == "name":
            return NAME_REQUIRED
    return KIND_REFUSED


def _kinds(records: list[dict]) -> list[dict]:
    for record in records:
        record["kind_label"] = KIND_LABELS.get(record.get("kind") or "", "")
    return records
