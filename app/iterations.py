from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.access import ACTION_REFUSED, access_scope
from app.measures import velocity_of
from app.navigation import shell, team_breadcrumb
from app.schemas import (
    AcceptForm,
    BacklogAddForm,
    BacklogOrderForm,
    CrossTeamForm,
    IterationForm,
    PromoteForm,
    RetroForm,
    SyncNoteForm,
    WipExceptionForm,
    WipForm,
)
from app.stages import STAGES
from app.store import Database, get_store

NAME_REQUIRED = "A name is required."
DATE_REFUSED = "That date was refused."
END_BEFORE_START = "The end is before the start."
OUTSIDE_CYCLE = "That iteration is outside the cycle."
ITERATION_NEEDS_CYCLE = "An iteration needs a cycle."
NEEDS_OWNER = "That action needs the product owner."
NEEDS_MASTER = "That action needs the scrum master."
STORY_NOT_ON_TEAM = "That story is not on this team."
LIMIT_REFUSED = "That limit was refused."


def _optional_int(value: str) -> int | None:
    text = str(value).strip()
    if not text.isdigit():
        return None
    number = int(text)
    return number if number >= 1 else None


def _message(exc: ValidationError) -> str:
    for error in exc.errors():
        if "order" in str(error.get("ctx", "")) or "order" in error.get("msg", ""):
            return END_BEFORE_START
        loc = error["loc"][-1] if error["loc"] else ""
        if loc in {"name", "body", "reason", "impediment", "dependency", "statement"}:
            return NAME_REQUIRED
    return DATE_REFUSED


def _holds(store, organization_id, person_id, role, team_id) -> bool:
    held = store.person_role(organization_id, person_id)
    if held is None or held["role"] != role:
        return False
    return store.person_on_team(person_id, team_id)


def _board(rows: list[dict]) -> dict[str, list[dict]]:
    grouped = {stage: [] for stage in STAGES}
    for row in rows:
        grouped.setdefault(row["stage"], []).append(row)
    return grouped


def execution_context(store: Database, signed_in: dict, team: dict) -> dict:
    organization_id = signed_in["organization_id"]
    person = store.person_by_user_id(signed_in["id"])
    admin = access_scope(store, signed_in["id"]) is None
    show_retro = admin or (person is not None and store.person_on_team(person["id"], team["id"]))
    group_id = team["delivery_group_id"]
    iterations = store.list_iterations(team["id"])
    latest = sorted(iterations, key=lambda item: (item["ends_on"], item["id"]), reverse=True)[:3]
    return {
        "iterations": iterations,
        "velocity_history": [
            {
                "name": iteration["name"],
                "velocity": velocity_of(store.list_iteration_board(iteration["id"])),
            }
            for iteration in latest
        ],
        "cycle_choices": store.list_cycles(group_id),
        "stage_board": _board(store.stories_for_team(team["id"])),
        "stages": STAGES,
        "sync_notes": store.list_group_sync_notes(group_id),
        "cross_notes": store.list_group_cross_notes(group_id),
        "show_retro": show_retro,
        "retro_notes": store.list_team_retro_notes(team["id"]) if show_retro else [],
        "learnings": store.list_group_learnings(group_id),
    }


def register_iterations(
    app: FastAPI,
    templates: Jinja2Templates,
    team_page,
    signed_in_user,
    sign_in,
    edit_blocked,
    hidden,
) -> None:
    def render(request, store, signed_in, team, breadcrumb, status_code=200, **context):
        context.update(
            shell(store, signed_in["organization_id"], "team", team["id"], signed_in["id"])
        )
        context["team"] = team
        context["breadcrumb"] = breadcrumb
        return templates.TemplateResponse(request, "iteration.html", context, status_code=status_code)

    def crumbs(store, organization_id, iteration, team):
        trail = team_breadcrumb(store, organization_id, team)
        trail[-1] = {"name": team["name"], "href": f"/teams/{team['id']}"}
        trail.append({"name": iteration["name"], "href": None})
        return trail

    def iteration_page(request, store, signed_in, iteration_id: int, error, status_code=200):
        organization_id = signed_in["organization_id"]
        iteration = store.get_iteration(organization_id, iteration_id)
        if iteration is None:
            raise HTTPException(status_code=404)
        blocked = hidden(store, signed_in, "team", iteration["team_id"])
        if blocked is not None:
            from app.access import RECORD_HIDDEN

            return templates.TemplateResponse(
                request,
                "refused.html",
                {
                    "message": blocked or RECORD_HIDDEN,
                    **shell(store, organization_id, None, user_id=signed_in["id"]),
                },
                status_code=422,
            )
        team = store.get_team(organization_id, iteration["team_id"])
        stories = store.list_iteration_board(iteration_id)
        for story in stories:
            story["stage_group"] = story["stage"]
        completed = sum(story["estimate_value"] or 0 for story in stories if story["accepted"])
        available = store.list_stories_not_on_iteration(team["id"])
        exceptions = store.list_iteration_exceptions(iteration_id)
        return render(
            request,
            store,
            signed_in,
            team,
            crumbs(store, organization_id, iteration, team),
            status_code,
            iteration=iteration,
            stories=stories,
            board=_board(stories),
            stages=STAGES,
            completed_size=completed,
            available=available,
            people=store.list_people(organization_id),
            exceptions=exceptions,
            error=error,
        )

    def editable(request, store, iteration_id):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return None, sign_in()
        iteration = store.get_iteration(signed_in["organization_id"], iteration_id)
        if iteration is None:
            raise HTTPException(status_code=404)
        blocked = hidden(store, signed_in, "team", iteration["team_id"])
        if blocked is not None:
            return None, iteration_page(request, store, signed_in, iteration_id, blocked, 422)
        if edit_blocked(store, signed_in) is not None:
            return None, iteration_page(request, store, signed_in, iteration_id, ACTION_REFUSED, 422)
        return (signed_in, iteration), None

    @app.post("/iterations")
    def post_iteration(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        name: Annotated[str, Form()] = "",
        starts_on: Annotated[str, Form()] = "",
        ends_on: Annotated[str, Form()] = "",
        team_id: Annotated[str, Form()] = "",
        cycle_id: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        parsed_team = _optional_int(team_id)
        if parsed_team is None or store.get_team(signed_in["organization_id"], parsed_team) is None:
            raise HTTPException(status_code=404)
        if hidden(store, signed_in, "team", parsed_team) is not None:
            return team_page(request, store, signed_in, parsed_team, "That record is not available.", 422)
        if edit_blocked(store, signed_in) is not None:
            return team_page(request, store, signed_in, parsed_team, ACTION_REFUSED, 422)
        try:
            form = IterationForm(
                name=name,
                starts_on=starts_on,
                ends_on=ends_on,
                team_id=parsed_team,
                cycle_id=int(cycle_id),
            )
        except (ValidationError, ValueError) as exc:
            message = _message(exc) if isinstance(exc, ValidationError) else DATE_REFUSED
            return team_page(request, store, signed_in, parsed_team, message, 422)
        cycle = store.get_cycle(signed_in["organization_id"], form.cycle_id)
        team = store.get_team(signed_in["organization_id"], form.team_id)
        if cycle is None or team is None or cycle["delivery_group_id"] != team["delivery_group_id"]:
            return team_page(request, store, signed_in, parsed_team, ITERATION_NEEDS_CYCLE, 422)
        if form.starts_on < cycle["starts_on"] or form.ends_on > cycle["ends_on"]:
            return team_page(request, store, signed_in, parsed_team, OUTSIDE_CYCLE, 422)
        created = store.create_iteration(
            signed_in["organization_id"],
            form.team_id,
            form.cycle_id,
            form.name,
            form.starts_on,
            form.ends_on,
        )
        return RedirectResponse(f"/iterations/{created}", status_code=303)

    @app.get("/iterations/{iteration_id}")
    def get_iteration_page(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        iteration_id: int,
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        return iteration_page(request, store, signed_in, iteration_id, None)

    @app.post("/iterations/{iteration_id}/stories")
    def post_iteration_story(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        iteration_id: int,
        story_id: Annotated[str, Form()] = "",
        person_id: Annotated[str, Form()] = "",
    ):
        found, response = editable(request, store, iteration_id)
        if response is not None:
            return response
        signed_in, iteration = found
        try:
            form = BacklogAddForm(story_id=int(story_id), person_id=int(person_id))
        except (ValidationError, ValueError):
            return iteration_page(request, store, signed_in, iteration_id, STORY_NOT_ON_TEAM, 422)
        if not _holds(
            store, signed_in["organization_id"], form.person_id, "product_owner", iteration["team_id"]
        ):
            return iteration_page(request, store, signed_in, iteration_id, NEEDS_OWNER, 422)
        story = store.get_story(signed_in["organization_id"], form.story_id)
        if story is None or story["team_id"] != iteration["team_id"]:
            return iteration_page(request, store, signed_in, iteration_id, STORY_NOT_ON_TEAM, 422)
        if not store.add_iteration_story(
            signed_in["organization_id"], iteration_id, form.story_id
        ):
            return iteration_page(request, store, signed_in, iteration_id, STORY_NOT_ON_TEAM, 422)
        return RedirectResponse(f"/iterations/{iteration_id}", status_code=303)

    @app.post("/iterations/{iteration_id}/order")
    def post_order(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        iteration_id: int,
        story_id: Annotated[str, Form()] = "",
        person_id: Annotated[str, Form()] = "",
        position: Annotated[str, Form()] = "",
    ):
        found, response = editable(request, store, iteration_id)
        if response is not None:
            return response
        signed_in, iteration = found
        try:
            form = BacklogOrderForm(story_id=int(story_id), person_id=int(person_id), position=int(position))
        except (ValidationError, ValueError):
            return iteration_page(request, store, signed_in, iteration_id, NEEDS_OWNER, 422)
        if not _holds(
            store, signed_in["organization_id"], form.person_id, "product_owner", iteration["team_id"]
        ):
            return iteration_page(request, store, signed_in, iteration_id, NEEDS_OWNER, 422)
        store.set_iteration_position(iteration_id, form.story_id, form.position)
        return RedirectResponse(f"/iterations/{iteration_id}", status_code=303)

    @app.post("/iterations/{iteration_id}/acceptance")
    def post_acceptance(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        iteration_id: int,
        story_id: Annotated[str, Form()] = "",
        person_id: Annotated[str, Form()] = "",
        accepted: Annotated[str, Form()] = "",
    ):
        found, response = editable(request, store, iteration_id)
        if response is not None:
            return response
        signed_in, iteration = found
        try:
            form = AcceptForm(story_id=int(story_id), person_id=int(person_id), accepted=int(accepted))
        except (ValidationError, ValueError):
            return iteration_page(request, store, signed_in, iteration_id, NEEDS_OWNER, 422)
        if not _holds(
            store, signed_in["organization_id"], form.person_id, "product_owner", iteration["team_id"]
        ):
            return iteration_page(request, store, signed_in, iteration_id, NEEDS_OWNER, 422)
        store.set_iteration_accepted(iteration_id, form.story_id, form.accepted)
        return RedirectResponse(f"/iterations/{iteration_id}", status_code=303)

    @app.post("/teams/{team_id}/wip")
    def post_wip(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        team_id: int,
        limit: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        if store.get_team(signed_in["organization_id"], team_id) is None:
            raise HTTPException(status_code=404)
        if hidden(store, signed_in, "team", team_id) is not None:
            return team_page(request, store, signed_in, team_id, "That record is not available.", 422)
        if edit_blocked(store, signed_in) is not None:
            return team_page(request, store, signed_in, team_id, ACTION_REFUSED, 422)
        try:
            form = WipForm(limit=int(limit))
        except (ValidationError, ValueError):
            return team_page(request, store, signed_in, team_id, LIMIT_REFUSED, 422)
        store.set_wip_limit(signed_in["organization_id"], team_id, form.limit)
        return RedirectResponse(f"/teams/{team_id}", status_code=303)

    @app.post("/iterations/{iteration_id}/wip-exception")
    def post_exception(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        iteration_id: int,
        story_id: Annotated[str, Form()] = "",
        person_id: Annotated[str, Form()] = "",
        reason: Annotated[str, Form()] = "",
    ):
        found, response = editable(request, store, iteration_id)
        if response is not None:
            return response
        signed_in, iteration = found
        try:
            form = WipExceptionForm(story_id=int(story_id), person_id=int(person_id), reason=reason)
        except (ValidationError, ValueError):
            return iteration_page(request, store, signed_in, iteration_id, NEEDS_MASTER, 422)
        if not _holds(
            store, signed_in["organization_id"], form.person_id, "scrum_master", iteration["team_id"]
        ):
            return iteration_page(request, store, signed_in, iteration_id, NEEDS_MASTER, 422)
        store.add_wip_exception_row(
            signed_in["organization_id"],
            iteration_id,
            form.story_id,
            form.person_id,
            form.reason,
        )
        return RedirectResponse(f"/iterations/{iteration_id}", status_code=303)

    @app.post("/teams/{team_id}/sync-notes")
    def post_sync(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        team_id: int,
        note_on: Annotated[str, Form()] = "",
        body: Annotated[str, Form()] = "",
        person_id: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        if store.get_team(signed_in["organization_id"], team_id) is None:
            raise HTTPException(status_code=404)
        if hidden(store, signed_in, "team", team_id) is not None:
            return team_page(request, store, signed_in, team_id, "That record is not available.", 422)
        if edit_blocked(store, signed_in) is not None:
            return team_page(request, store, signed_in, team_id, ACTION_REFUSED, 422)
        try:
            form = SyncNoteForm(note_on=note_on, body=body, person_id=int(person_id))
        except (ValidationError, ValueError) as exc:
            message = _message(exc) if isinstance(exc, ValidationError) else NAME_REQUIRED
            return team_page(request, store, signed_in, team_id, message, 422)
        if not _holds(store, signed_in["organization_id"], form.person_id, "scrum_master", team_id):
            return team_page(request, store, signed_in, team_id, NEEDS_MASTER, 422)
        store.add_sync_note(
            signed_in["organization_id"],
            team_id,
            form.note_on,
            form.body,
            form.person_id,
        )
        return RedirectResponse(f"/teams/{team_id}", status_code=303)

    @app.post("/teams/{team_id}/cross-notes")
    def post_cross(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        team_id: int,
        impediment: Annotated[str, Form()] = "",
        dependency: Annotated[str, Form()] = "",
        asked_team_id: Annotated[str, Form()] = "",
        person_id: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        if store.get_team(signed_in["organization_id"], team_id) is None:
            raise HTTPException(status_code=404)
        if hidden(store, signed_in, "team", team_id) is not None:
            return team_page(request, store, signed_in, team_id, "That record is not available.", 422)
        if edit_blocked(store, signed_in) is not None:
            return team_page(request, store, signed_in, team_id, ACTION_REFUSED, 422)
        try:
            form = CrossTeamForm(
                impediment=impediment,
                dependency=dependency,
                asked_team_id=int(asked_team_id),
                person_id=int(person_id),
            )
        except (ValidationError, ValueError):
            return team_page(request, store, signed_in, team_id, NAME_REQUIRED, 422)
        if not _holds(store, signed_in["organization_id"], form.person_id, "scrum_master", team_id):
            return team_page(request, store, signed_in, team_id, NEEDS_MASTER, 422)
        if store.get_team(signed_in["organization_id"], form.asked_team_id) is None:
            return team_page(request, store, signed_in, team_id, NAME_REQUIRED, 422)
        store.add_cross_note(
            signed_in["organization_id"],
            team_id,
            form.impediment,
            form.dependency,
            form.asked_team_id,
            form.person_id,
        )
        return RedirectResponse(f"/teams/{team_id}", status_code=303)

    @app.post("/teams/{team_id}/retro-notes")
    def post_retro(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        team_id: int,
        iteration_id: Annotated[str, Form()] = "",
        body: Annotated[str, Form()] = "",
        person_id: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        if store.get_team(signed_in["organization_id"], team_id) is None:
            raise HTTPException(status_code=404)
        if hidden(store, signed_in, "team", team_id) is not None:
            return team_page(request, store, signed_in, team_id, "That record is not available.", 422)
        if edit_blocked(store, signed_in) is not None:
            return team_page(request, store, signed_in, team_id, ACTION_REFUSED, 422)
        try:
            form = RetroForm(iteration_id=int(iteration_id), body=body, person_id=int(person_id))
        except (ValidationError, ValueError):
            return team_page(request, store, signed_in, team_id, NAME_REQUIRED, 422)
        if not _holds(store, signed_in["organization_id"], form.person_id, "scrum_master", team_id):
            return team_page(request, store, signed_in, team_id, NEEDS_MASTER, 422)
        iteration = store.get_iteration(signed_in["organization_id"], form.iteration_id)
        if iteration is None or iteration["team_id"] != team_id:
            return team_page(request, store, signed_in, team_id, ITERATION_NEEDS_CYCLE, 422)
        store.add_retro_note(
            signed_in["organization_id"],
            team_id,
            form.iteration_id,
            form.body,
            form.person_id,
        )
        return RedirectResponse(f"/teams/{team_id}", status_code=303)

    @app.post("/retro-notes/{note_id}/promote")
    def post_promote(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        note_id: int,
        statement: Annotated[str, Form()] = "",
        person_id: Annotated[str, Form()] = "",
    ):
        signed_in = signed_in_user(request, store)
        if signed_in is None:
            return sign_in()
        note = store.get_retro_note(signed_in["organization_id"], note_id)
        if note is None:
            raise HTTPException(status_code=404)
        if hidden(store, signed_in, "team", note["team_id"]) is not None:
            return team_page(request, store, signed_in, note["team_id"], "That record is not available.", 422)
        if edit_blocked(store, signed_in) is not None:
            return team_page(request, store, signed_in, note["team_id"], ACTION_REFUSED, 422)
        try:
            form = PromoteForm(statement=statement, person_id=int(person_id))
        except (ValidationError, ValueError):
            return team_page(request, store, signed_in, note["team_id"], NAME_REQUIRED, 422)
        if not _holds(
            store, signed_in["organization_id"], form.person_id, "scrum_master", note["team_id"]
        ):
            return team_page(request, store, signed_in, note["team_id"], NEEDS_MASTER, 422)
        store.add_promoted_learning(
            signed_in["organization_id"], note["team_id"], note["id"], form.statement
        )
        return RedirectResponse(f"/teams/{note['team_id']}", status_code=303)
