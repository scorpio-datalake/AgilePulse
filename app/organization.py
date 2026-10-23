from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.access import ACTION_REFUSED, RECORD_HIDDEN, access_scope, allows, allows_edit
from app.landing import ASSIGNABLE_ROLES, CREW_ROLES, home_context
from app.store import Database, get_store
from app.stages import STAGES
from app.navigation import (
    group_breadcrumb,
    portfolio_breadcrumb,
    shell,
    stream_breadcrumb,
    team_breadcrumb,
)
from app.schemas import (
    DeliveryGroupForm,
    MembershipForm,
    NameForm,
    PersonCreateForm,
    PolicyForm,
    RoleForm,
    TeamForm,
    ValueStreamForm,
)

NAME_REQUIRED = "A name is required."
STREAM_NEEDS_PORTFOLIO = "A value stream needs a portfolio."
GROUP_NEEDS_STREAM = "A delivery group needs a value stream."
TEAM_NEEDS_GROUP = "A team needs a delivery group."
ROLE_WRONG_RECORD = "That role does not belong on this record."
ROLE_REFUSED = "That role was refused."
POLICY_REFUSED = "That policy was refused."
ROLE_NEEDS_STREAM = "A stream owner needs a value stream."
ROLE_NEEDS_GROUP = "That role needs a delivery group."
ACCESS_LABELS = {"admin": "Admin", "member": "Member", "viewer": "Viewer"}

ROLE_LABELS = {
    "stream_owner": "Stream owner",
    "group_facilitator": "Group facilitator",
    "product_manager": "Product manager",
    "business_stakeholder": "Business stakeholder",
    "product_owner": "Product owner",
    "scrum_master": "Scrum master",
    "technical_lead": "Technical lead",
    "team_member": "Team member",
}


def register_organization(app: FastAPI, templates: Jinja2Templates) -> None:
    def user(request: Request, store: Database):
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

    def refused(request: Request, store, signed_in, message: str):
        return render(
            request,
            "refused.html",
            store,
            signed_in,
            None,
            status_code=422,
            message=message,
        )

    def home_page(request, store, signed_in, error: str | None, status_code: int = 200):
        return render(
            request,
            "home.html",
            store,
            signed_in,
            "home",
            status_code=status_code,
            display_name=signed_in["display_name"],
            error=error,
            **home_context(store, signed_in),
        )

    def portfolio_page(request, store, signed_in, portfolio_id: int, error, status_code=200):
        portfolio = store.get_portfolio(signed_in["organization_id"], portfolio_id)
        if portfolio is None:
            raise HTTPException(status_code=404)
        hidden = _hidden(store, signed_in, "portfolio", portfolio_id)
        if hidden is not None:
            return refused(request, store, signed_in, hidden)
        return render(
            request,
            "portfolio.html",
            store,
            signed_in,
            "portfolio",
            portfolio_id,
            portfolio_breadcrumb(portfolio),
            status_code,
            portfolio=portfolio,
            streams=_keep(store, signed_in, "stream", store.list_value_streams(portfolio_id)),
            can_create_stream=_is_admin(store, signed_in["id"]),
            error=error,
        )

    def stream_page(request, store, signed_in, value_stream_id: int, error, status_code=200):
        organization_id = signed_in["organization_id"]
        stream = store.get_value_stream(organization_id, value_stream_id)
        if stream is None:
            raise HTTPException(status_code=404)
        hidden = _hidden(store, signed_in, "stream", value_stream_id)
        if hidden is not None:
            return refused(request, store, signed_in, hidden)
        return render(
            request,
            "value_stream.html",
            store,
            signed_in,
            "value_stream",
            value_stream_id,
            stream_breadcrumb(store, organization_id, stream),
            status_code,
            stream=stream,
            groups=_keep(
                store,
                signed_in,
                "group",
                store.list_delivery_groups(value_stream_id),
            ),
            people=store.list_people(organization_id),
            assignments=_labeled(
                store.list_role_assignments(organization_id, value_stream_id=value_stream_id)
            ),
            goals=store.list_goals(value_stream_id),
            error=error,
        )

    def group_page(request, store, signed_in, delivery_group_id: int, error, status_code=200):
        organization_id = signed_in["organization_id"]
        group = store.get_delivery_group(organization_id, delivery_group_id)
        if group is None:
            raise HTTPException(status_code=404)
        hidden = _hidden(store, signed_in, "group", delivery_group_id)
        if hidden is not None:
            return refused(request, store, signed_in, hidden)
        assignments = _labeled(
            store.list_role_assignments(organization_id, delivery_group_id=delivery_group_id)
        )
        facilitator = next(
            (item for item in assignments if item["role"] == "group_facilitator"),
            None,
        )
        return render(
            request,
            "delivery_group.html",
            store,
            signed_in,
            "delivery_group",
            delivery_group_id,
            group_breadcrumb(store, organization_id, group),
            status_code,
            group=group,
            teams=_keep(store, signed_in, "team", store.list_teams(delivery_group_id)),
            members=_seated(
                store.list_members(organization_id, delivery_group_id=delivery_group_id)
            ),
            people=store.list_people(organization_id),
            assignments=assignments,
            facilitator=facilitator,
            stages=STAGES,
            feature_board=_stage_board(store.features_for_stream(group["value_stream_id"])),
            story_board=_stage_board(store.stories_for_group(delivery_group_id)),
            cycles=store.list_cycles(delivery_group_id),
            policies=store.list_policies(delivery_group_id),
            error=error,
        )

    def team_page(request, store, signed_in, team_id: int, error, status_code=200):
        organization_id = signed_in["organization_id"]
        team = store.get_team(organization_id, team_id)
        if team is None:
            raise HTTPException(status_code=404)
        hidden = _hidden(store, signed_in, "team", team_id)
        if hidden is not None:
            return refused(request, store, signed_in, hidden)
        from app.iterations import execution_context

        return render(
            request,
            "team.html",
            store,
            signed_in,
            "team",
            team_id,
            team_breadcrumb(store, organization_id, team),
            status_code,
            team=team,
            members=_seated(store.list_members(organization_id, team_id=team_id)),
            people=_described(store.list_people(organization_id)),
            team_choices=store.list_teams(team["delivery_group_id"]),
            error=error,
            **execution_context(store, signed_in, team),
        )

    def people_page(request, store, signed_in, error, status_code=200):
        organization_id = signed_in["organization_id"]
        return render(
            request,
            "people.html",
            store,
            signed_in,
            "people",
            status_code=status_code,
            people=_described(store.list_people(organization_id)),
            streams=_keep(
                store,
                signed_in,
                "stream",
                store.list_streams_for_roles(organization_id),
            ),
            groups=_keep(
                store,
                signed_in,
                "group",
                store.list_groups_for_roles(organization_id),
            ),
            teams=_keep(
                store,
                signed_in,
                "team",
                store.list_teams_for_assignment(organization_id),
            ),
            error=error,
        )

    def person_page(request, store, signed_in, person_id: int, error, status_code=200):
        person = store.get_person(signed_in["organization_id"], person_id)
        if person is None:
            raise HTTPException(status_code=404)
        actor = store.person_by_user_id(signed_in["id"])
        held = store.role_for_person(person_id)
        person["access_label"] = ACCESS_LABELS.get(person["account_access"], "")
        person["role_label"] = ROLE_LABELS.get(held["role"], "") if held else ""
        return render(
            request,
            "person.html",
            store,
            signed_in,
            "people",
            status_code=status_code,
            person=person,
            actor_is_admin=actor is not None and actor["account_access"] == "admin",
            error=error,
        )

    @app.post("/portfolios")
    def post_portfolio(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        name: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        if not _is_admin(store, signed_in["id"]):
            return home_page(request, store, signed_in, ACTION_REFUSED, 422)
        try:
            form = NameForm(name=name)
        except ValidationError:
            return home_page(request, store, signed_in, NAME_REQUIRED, 422)
        portfolio_id = store.create_portfolio(signed_in["organization_id"], form.name)
        return RedirectResponse(f"/portfolios/{portfolio_id}", status_code=303)

    @app.post("/crew")
    def post_crew(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        person_id: Annotated[str, Form()] = "",
        team_id: Annotated[str, Form()] = "",
        role: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        actor = store.person_by_user_id(signed_in["id"])
        held = store.role_for_person(actor["id"]) if actor is not None else None
        if held is None or held["role"] not in CREW_ROLES:
            return home_page(request, store, signed_in, ACTION_REFUSED, 422)
        parsed_person = _optional_int(person_id)
        parsed_team = _optional_int(team_id)
        allowed = {value for value, _label in ASSIGNABLE_ROLES}
        if parsed_person is None or parsed_team is None or role not in allowed:
            return home_page(request, store, signed_in, ROLE_REFUSED, 422)
        if not allows(access_scope(store, signed_in["id"]), "team", parsed_team):
            return home_page(request, store, signed_in, RECORD_HIDDEN, 422)
        membership = store.add_membership(
            signed_in["organization_id"], parsed_person, team_id=parsed_team
        )
        if membership not in (None, "That person is already a member."):
            return home_page(request, store, signed_in, membership, 422)
        message = store.assign_role(
            signed_in["organization_id"],
            parsed_person,
            role,
            team_id=parsed_team,
        )
        if message is not None:
            return home_page(request, store, signed_in, message, 422)
        return RedirectResponse("/", status_code=303)

    @app.get("/portfolios/{portfolio_id}")
    def get_portfolio_page(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        portfolio_id: int,
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        return portfolio_page(request, store, signed_in, portfolio_id, None)

    @app.post("/portfolios/{portfolio_id}")
    def post_portfolio_name(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        portfolio_id: int,
        name: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        blocked = _blocked(store, signed_in, edit=True, kind="portfolio", record_id=portfolio_id)
        if blocked == RECORD_HIDDEN:
            return refused(request, store, signed_in, blocked)
        if blocked is not None:
            return portfolio_page(request, store, signed_in, portfolio_id, blocked, 422)
        try:
            form = NameForm(name=name)
        except ValidationError:
            return portfolio_page(request, store, signed_in, portfolio_id, NAME_REQUIRED, 422)
        if not store.rename_portfolio(signed_in["organization_id"], portfolio_id, form.name):
            raise HTTPException(status_code=404)
        return RedirectResponse(f"/portfolios/{portfolio_id}", status_code=303)

    @app.post("/value-streams")
    def post_value_stream(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        name: Annotated[str, Form()] = "",
        portfolio_id: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        if not _is_admin(store, signed_in["id"]):
            return home_page(request, store, signed_in, ACTION_REFUSED, 422)
        parsed = _optional_int(portfolio_id)
        blocked = _blocked(store, signed_in, edit=True, kind="portfolio", record_id=parsed or 0)
        if blocked is not None:
            return refused(request, store, signed_in, blocked)
        try:
            form = ValueStreamForm(name=name, portfolio_id=parsed)
        except ValidationError as exc:
            message = _name_or_parent(exc, STREAM_NEEDS_PORTFOLIO)
            if parsed is None or store.get_portfolio(signed_in["organization_id"], parsed) is None:
                return refused(request, store, signed_in, message)
            return portfolio_page(request, store, signed_in, parsed, message, 422)
        created = store.create_value_stream(
            signed_in["organization_id"], form.portfolio_id, form.name
        )
        if created is None:
            return refused(request, store, signed_in, STREAM_NEEDS_PORTFOLIO)
        return RedirectResponse(f"/value-streams/{created}", status_code=303)

    @app.get("/value-streams/{value_stream_id}")
    def get_stream_page(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        value_stream_id: int,
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        return stream_page(request, store, signed_in, value_stream_id, None)

    @app.post("/value-streams/{value_stream_id}")
    def post_stream_name(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        value_stream_id: int,
        name: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        blocked = _blocked(store, signed_in, edit=True, kind="stream", record_id=value_stream_id)
        if blocked == RECORD_HIDDEN:
            return refused(request, store, signed_in, blocked)
        if blocked is not None:
            return stream_page(request, store, signed_in, value_stream_id, blocked, 422)
        try:
            form = NameForm(name=name)
        except ValidationError:
            return stream_page(request, store, signed_in, value_stream_id, NAME_REQUIRED, 422)
        if not store.rename_value_stream(
            signed_in["organization_id"], value_stream_id, form.name
        ):
            raise HTTPException(status_code=404)
        return RedirectResponse(f"/value-streams/{value_stream_id}", status_code=303)

    @app.post("/delivery-groups")
    def post_delivery_group(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        name: Annotated[str, Form()] = "",
        value_stream_id: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        parsed = _optional_int(value_stream_id)
        blocked = _blocked(store, signed_in, edit=True, kind="stream", record_id=parsed or 0)
        if blocked is not None:
            return refused(request, store, signed_in, blocked)
        try:
            form = DeliveryGroupForm(name=name, value_stream_id=parsed)
        except ValidationError as exc:
            message = _name_or_parent(exc, GROUP_NEEDS_STREAM)
            if parsed is None or store.get_value_stream(
                signed_in["organization_id"], parsed
            ) is None:
                return refused(request, store, signed_in, message)
            return stream_page(request, store, signed_in, parsed, message, 422)
        created = store.create_delivery_group(
            signed_in["organization_id"], form.value_stream_id, form.name
        )
        if created is None:
            return refused(request, store, signed_in, GROUP_NEEDS_STREAM)
        return RedirectResponse(f"/delivery-groups/{created}", status_code=303)

    @app.get("/delivery-groups/{delivery_group_id}")
    def get_group_page(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        delivery_group_id: int,
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        return group_page(request, store, signed_in, delivery_group_id, None)

    @app.post("/delivery-groups/{delivery_group_id}")
    def post_group_name(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        delivery_group_id: int,
        name: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        blocked = _blocked(
            store, signed_in, edit=True, kind="group", record_id=delivery_group_id
        )
        if blocked == RECORD_HIDDEN:
            return refused(request, store, signed_in, blocked)
        if blocked is not None:
            return group_page(request, store, signed_in, delivery_group_id, blocked, 422)
        try:
            form = NameForm(name=name)
        except ValidationError:
            return group_page(request, store, signed_in, delivery_group_id, NAME_REQUIRED, 422)
        if not store.rename_delivery_group(
            signed_in["organization_id"], delivery_group_id, form.name
        ):
            raise HTTPException(status_code=404)
        return RedirectResponse(f"/delivery-groups/{delivery_group_id}", status_code=303)

    @app.post("/delivery-groups/{delivery_group_id}/policies")
    def post_policy(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        delivery_group_id: int,
        to_stage: Annotated[str, Form()] = "",
        effect: Annotated[str, Form()] = "",
        from_stage: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        blocked = _blocked(
            store, signed_in, edit=True, kind="group", record_id=delivery_group_id
        )
        if blocked == RECORD_HIDDEN:
            return refused(request, store, signed_in, blocked)
        if blocked is not None:
            return group_page(request, store, signed_in, delivery_group_id, blocked, 422)
        try:
            form = PolicyForm(to_stage=to_stage, effect=effect, from_stage=from_stage)
        except ValidationError:
            return group_page(request, store, signed_in, delivery_group_id, POLICY_REFUSED, 422)
        if (
            store.add_policy(
                signed_in["organization_id"],
                delivery_group_id,
                form.from_stage,
                form.to_stage,
                form.effect,
            )
            is None
        ):
            raise HTTPException(status_code=404)
        return RedirectResponse(f"/delivery-groups/{delivery_group_id}", status_code=303)

    @app.post("/teams")
    def post_team(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        name: Annotated[str, Form()] = "",
        delivery_group_id: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        parsed = _optional_int(delivery_group_id)
        blocked = _blocked(store, signed_in, edit=True, kind="group", record_id=parsed or 0)
        if blocked is not None:
            return refused(request, store, signed_in, blocked)
        try:
            form = TeamForm(name=name, delivery_group_id=parsed)
        except ValidationError as exc:
            message = _name_or_parent(exc, TEAM_NEEDS_GROUP)
            if parsed is None or store.get_delivery_group(
                signed_in["organization_id"], parsed
            ) is None:
                return refused(request, store, signed_in, message)
            return group_page(request, store, signed_in, parsed, message, 422)
        created = store.create_team(
            signed_in["organization_id"], form.delivery_group_id, form.name
        )
        if created is None:
            return refused(request, store, signed_in, TEAM_NEEDS_GROUP)
        return RedirectResponse(f"/teams/{created}", status_code=303)

    @app.get("/teams/{team_id}")
    def get_team_page(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        team_id: int,
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        return team_page(request, store, signed_in, team_id, None)

    @app.post("/teams/{team_id}")
    def post_team_name(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        team_id: int,
        name: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        blocked = _blocked(store, signed_in, edit=True, kind="team", record_id=team_id)
        if blocked == RECORD_HIDDEN:
            return refused(request, store, signed_in, blocked)
        if blocked is not None:
            return team_page(request, store, signed_in, team_id, blocked, 422)
        try:
            form = NameForm(name=name)
        except ValidationError:
            return team_page(request, store, signed_in, team_id, NAME_REQUIRED, 422)
        if not store.rename_team(signed_in["organization_id"], team_id, form.name):
            raise HTTPException(status_code=404)
        return RedirectResponse(f"/teams/{team_id}", status_code=303)

    @app.get("/people")
    def get_people(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        return people_page(request, store, signed_in, None)

    @app.post("/people")
    def post_person(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        name: Annotated[str, Form()] = "",
        role: Annotated[str, Form()] = "",
        value_stream_id: Annotated[str, Form()] = "",
        delivery_group_id: Annotated[str, Form()] = "",
        team_id: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        blocked = _blocked(store, signed_in, edit=True)
        if blocked is not None:
            return people_page(request, store, signed_in, blocked, 422)
        try:
            NameForm(name=name)
        except ValidationError:
            return people_page(request, store, signed_in, NAME_REQUIRED, 422)
        stream_id = _optional_int(value_stream_id)
        group_id = _optional_int(delivery_group_id)
        parsed_team_id = _optional_int(team_id)
        try:
            form = PersonCreateForm(
                name=name,
                role=role,
                value_stream_id=stream_id,
                delivery_group_id=group_id,
            )
        except ValidationError as exc:
            return people_page(request, store, signed_in, _person_form_error(exc), 422)
        place = _role_place(form.role)
        if place == "stream" and not allows(access_scope(store, signed_in["id"]), "stream", form.value_stream_id):
            return refused(request, store, signed_in, RECORD_HIDDEN)
        if place == "group" and not allows(access_scope(store, signed_in["id"]), "group", form.delivery_group_id):
            return refused(request, store, signed_in, RECORD_HIDDEN)
        if parsed_team_id is not None and not allows(
            access_scope(store, signed_in["id"]), "team", parsed_team_id
        ):
            return refused(request, store, signed_in, RECORD_HIDDEN)
        person_id, message = store.create_person_with_role(
            signed_in["organization_id"],
            form.name,
            form.role,
            value_stream_id=form.value_stream_id,
            delivery_group_id=form.delivery_group_id,
            team_id=parsed_team_id,
        )
        if message is not None or person_id is None:
            return people_page(request, store, signed_in, message or ROLE_REFUSED, 422)
        return RedirectResponse(f"/people/{person_id}", status_code=303)

    @app.get("/people/{person_id}")
    def get_person_page(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        person_id: int,
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        return person_page(request, store, signed_in, person_id, None)

    @app.post("/people/{person_id}")
    def post_person_name(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        person_id: int,
        name: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        blocked = _blocked(store, signed_in, edit=True)
        if blocked is not None:
            return person_page(request, store, signed_in, person_id, blocked, 422)
        try:
            form = NameForm(name=name)
        except ValidationError:
            return person_page(request, store, signed_in, person_id, NAME_REQUIRED, 422)
        if not store.rename_person(signed_in["organization_id"], person_id, form.name):
            raise HTTPException(status_code=404)
        return RedirectResponse(f"/people/{person_id}", status_code=303)

    @app.post("/people/{person_id}/access")
    def post_person_access(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        person_id: int,
        account_access: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        actor = store.person_by_user_id(signed_in["id"])
        if actor is None or actor["account_access"] != "admin":
            return person_page(request, store, signed_in, person_id, ACTION_REFUSED, 422)
        message = store.set_account_access(
            signed_in["organization_id"], person_id, account_access
        )
        if message is not None:
            return person_page(request, store, signed_in, person_id, message, 422)
        return RedirectResponse(f"/people/{person_id}", status_code=303)

    @app.post("/delivery-groups/{delivery_group_id}/members")
    def post_group_member(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        delivery_group_id: int,
        person_id: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        blocked = _blocked(store, signed_in, edit=True, kind="group", record_id=delivery_group_id)
        if blocked == RECORD_HIDDEN:
            return refused(request, store, signed_in, blocked)
        if blocked is not None:
            return group_page(request, store, signed_in, delivery_group_id, blocked, 422)
        message = _membership_error(person_id)
        if message is None:
            message = store.add_membership(
                signed_in["organization_id"],
                int(person_id),
                delivery_group_id=delivery_group_id,
            )
        if message is not None:
            return group_page(request, store, signed_in, delivery_group_id, message, 422)
        return RedirectResponse(f"/delivery-groups/{delivery_group_id}", status_code=303)

    @app.post("/teams/{team_id}/members")
    def post_team_member(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        team_id: int,
        person_id: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        blocked = _blocked(store, signed_in, edit=True, kind="team", record_id=team_id)
        if blocked == RECORD_HIDDEN:
            return refused(request, store, signed_in, blocked)
        if blocked is not None:
            return team_page(request, store, signed_in, team_id, blocked, 422)
        message = _membership_error(person_id)
        if message is None:
            message = store.add_membership(
                signed_in["organization_id"],
                int(person_id),
                team_id=team_id,
            )
        if message is not None:
            return team_page(request, store, signed_in, team_id, message, 422)
        return RedirectResponse(f"/teams/{team_id}", status_code=303)

    @app.post("/memberships/{membership_id}/remove")
    def post_remove_member(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        membership_id: int,
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        membership = store.get_membership(signed_in["organization_id"], membership_id)
        if membership is None:
            raise HTTPException(status_code=404)
        kind = "team" if membership["team_id"] is not None else "group"
        record_id = membership["team_id"] or membership["delivery_group_id"]
        blocked = _blocked(store, signed_in, edit=True, kind=kind, record_id=record_id)
        if blocked is not None:
            return refused(request, store, signed_in, blocked)
        membership = store.remove_membership(signed_in["organization_id"], membership_id)
        if membership is None:
            raise HTTPException(status_code=404)
        if membership["team_id"] is not None:
            return RedirectResponse(f"/teams/{membership['team_id']}", status_code=303)
        return RedirectResponse(
            f"/delivery-groups/{membership['delivery_group_id']}",
            status_code=303,
        )

    @app.post("/roles")
    def post_role(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        person_id: Annotated[str, Form()] = "",
        role: Annotated[str, Form()] = "",
        value_stream_id: Annotated[str, Form()] = "",
        delivery_group_id: Annotated[str, Form()] = "",
        team_id: Annotated[str, Form()] = "",
    ):
        signed_in = user(request, store)
        if signed_in is None:
            return sign_in()
        blocked = _blocked(store, signed_in, edit=True)
        if blocked is not None:
            return refused(request, store, signed_in, blocked)
        stream_id = _optional_int(value_stream_id)
        group_id = _optional_int(delivery_group_id)
        parsed_team_id = _optional_int(team_id)
        try:
            form = RoleForm(
                person_id=_optional_int(person_id),
                role=role,
                value_stream_id=stream_id,
                delivery_group_id=group_id,
                team_id=parsed_team_id,
            )
        except ValidationError as exc:
            message = _role_form_error(exc)
            return _role_page(
                request,
                store,
                signed_in,
                stream_id,
                group_id,
                parsed_team_id,
                message,
            )
        scope = access_scope(store, signed_in["id"])
        if form.value_stream_id is not None and not allows(scope, "stream", form.value_stream_id):
            return refused(request, store, signed_in, RECORD_HIDDEN)
        if form.delivery_group_id is not None and not allows(scope, "group", form.delivery_group_id):
            return refused(request, store, signed_in, RECORD_HIDDEN)
        if form.team_id is not None and not allows(scope, "team", form.team_id):
            return refused(request, store, signed_in, RECORD_HIDDEN)
        message = store.assign_role(
            signed_in["organization_id"],
            form.person_id,
            form.role,
            value_stream_id=form.value_stream_id,
            delivery_group_id=form.delivery_group_id,
            team_id=form.team_id,
        )
        if message is not None:
            return _role_page(
                request,
                store,
                signed_in,
                form.value_stream_id,
                form.delivery_group_id,
                form.team_id,
                message,
            )
        if form.value_stream_id is not None:
            return RedirectResponse(f"/value-streams/{form.value_stream_id}", status_code=303)
        if form.delivery_group_id is not None:
            return RedirectResponse(f"/delivery-groups/{form.delivery_group_id}", status_code=303)
        return RedirectResponse(f"/teams/{form.team_id}", status_code=303)

    def _role_page(request, store, signed_in, stream_id, group_id, team_id, message):
        filled = [item for item in (stream_id, group_id, team_id) if item is not None]
        if len(filled) != 1:
            return refused(request, store, signed_in, message)
        if stream_id is not None:
            stream = store.get_value_stream(signed_in["organization_id"], stream_id)
            if stream is None:
                return refused(request, store, signed_in, message)
            return stream_page(request, store, signed_in, stream_id, message, 422)
        if group_id is not None:
            group = store.get_delivery_group(signed_in["organization_id"], group_id)
            if group is None:
                return refused(request, store, signed_in, message)
            return group_page(request, store, signed_in, group_id, message, 422)
        team = store.get_team(signed_in["organization_id"], team_id)
        if team is None:
            return refused(request, store, signed_in, message)
        return team_page(request, store, signed_in, team_id, message, 422)

    def edit_blocked(store, signed_in):
        return _blocked(store, signed_in, edit=True)

    from app.cycles import register_cycles
    from app.iterations import register_iterations

    register_cycles(app, templates, group_page, user, sign_in, edit_blocked, _hidden)
    register_iterations(app, templates, team_page, user, sign_in, edit_blocked, _hidden)


def _stage_board(rows: list[dict]) -> dict[str, list[dict]]:
    grouped = {stage: [] for stage in STAGES}
    for row in rows:
        grouped[row["stage"]].append(row)
    return grouped


def _optional_int(value: str | int | None) -> int | None:
    if isinstance(value, int):
        return value if value >= 1 else None
    if value is None:
        return None
    text = value.strip()
    if not text.isdigit():
        return None
    number = int(text)
    if number < 1:
        return None
    return number


def _name_or_parent(exc: ValidationError, parent_message: str) -> str:
    for error in exc.errors():
        if error["loc"][-1] == "name":
            return NAME_REQUIRED
    return parent_message


def _membership_error(person_id: str) -> str | None:
    try:
        MembershipForm(person_id=_optional_int(person_id))
    except ValidationError:
        return "That person was not found."
    return None


def _role_form_error(exc: ValidationError) -> str:
    for error in exc.errors():
        if error["loc"] and error["loc"][-1] == "person_id":
            return ROLE_REFUSED
    return ROLE_WRONG_RECORD


def _is_admin(store, user_id: int) -> bool:
    person = store.person_by_user_id(user_id)
    return person is not None and person["account_access"] == "admin"


def _blocked(store, signed_in, *, edit=False, kind=None, record_id=None):
    scope = access_scope(store, signed_in["id"])
    if kind is not None and not allows(scope, kind, record_id):
        return RECORD_HIDDEN
    if edit and not allows_edit(scope):
        return ACTION_REFUSED
    return None


def _hidden(store, signed_in, kind: str, record_id: int) -> str | None:
    if allows(access_scope(store, signed_in["id"]), kind, record_id):
        return None
    return RECORD_HIDDEN


def _keep(store, signed_in, kind: str, records: list[dict]) -> list[dict]:
    scope = access_scope(store, signed_in["id"])
    if scope is None:
        return records
    return [record for record in records if record["id"] in scope[kind]]


def _seated(members: list[dict]) -> list[dict]:
    for member in members:
        member["seat"] = ROLE_LABELS.get(member.get("role") or "", "")
    return members


def _described(people: list[dict]) -> list[dict]:
    for person in people:
        person["role_label"] = ROLE_LABELS.get(person.get("role") or "", "")
        person["access_label"] = ACCESS_LABELS.get(person.get("account_access") or "", "")
    return people


def _role_place(role: str) -> str:
    if role == "stream_owner":
        return "stream"
    if role in {"group_facilitator", "product_manager", "business_stakeholder"}:
        return "group"
    return "team"


def _person_form_error(exc: ValidationError) -> str:
    for error in exc.errors():
        location = error.get("loc") or ()
        if location and location[-1] == "name":
            return NAME_REQUIRED
        if location and location[-1] == "role":
            return ROLE_REFUSED
        if str(error.get("ctx", {}).get("error", "")) == "stream":
            return ROLE_NEEDS_STREAM
        if str(error.get("ctx", {}).get("error", "")) == "group":
            return ROLE_NEEDS_GROUP
    return ROLE_REFUSED


def _labeled(assignments: list[dict]) -> list[dict]:
    for assignment in assignments:
        assignment["label"] = ROLE_LABELS[assignment["role"]]
    return assignments
