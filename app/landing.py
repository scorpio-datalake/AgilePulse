from datetime import date

from app.access import access_scope, allows

CREW_ROLES = frozenset({"product_owner", "product_manager", "scrum_master"})
ASSIGNABLE_ROLES = (
    ("team_member", "Team member"),
    ("product_owner", "Product owner"),
    ("scrum_master", "Scrum master"),
    ("technical_lead", "Technical lead"),
)
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


def home_context(store, user) -> dict:
    person = store.person_by_user_id(user["id"])
    role = _role_name(store, person)
    admin = person is not None and person["account_access"] == "admin"
    if admin:
        return {
            "landing": "admin",
            "can_create_portfolio": True,
            "portfolios": _portfolios_with_streams(store, user["organization_id"]),
            "crew": None,
            "work": None,
        }
    if role in CREW_ROLES:
        return {
            "landing": "crew",
            "can_create_portfolio": False,
            "portfolios": [],
            "crew": _crew(store, user, person["id"]),
            "work": None,
        }
    return {
        "landing": "developer",
        "can_create_portfolio": False,
        "portfolios": [],
        "crew": None,
        "work": _work(store, user["organization_id"], person["id"] if person else None),
    }


def _role_name(store, person) -> str | None:
    if person is None:
        return None
    held = store.role_for_person(person["id"])
    if held is None:
        return None
    return held["role"]


def _portfolios_with_streams(store, organization_id: int) -> list[dict]:
    portfolios = []
    for portfolio in store.list_portfolios(organization_id):
        portfolios.append(
            {**portfolio, "streams": store.list_value_streams(portfolio["id"])}
        )
    return portfolios


def _crew(store, user, person_id: int) -> dict:
    organization_id = user["organization_id"]
    people = []
    for person in store.list_people(organization_id):
        people.append(
            {
                "id": person["id"],
                "name": person["name"],
                "role_label": ROLE_LABELS.get(person.get("role") or "", ""),
            }
        )
    return {
        "people": people,
        "teams": _visible_teams(store, user, person_id),
        "roles": [{"value": value, "label": label} for value, label in ASSIGNABLE_ROLES],
    }


def _visible_teams(store, user, person_id: int) -> list[dict]:
    scope = access_scope(store, user["id"])
    if scope is None:
        scope = store.membership_scope(person_id)
        scope = {**scope, "edit": True}
    teams = []
    for team_id in sorted(scope["team"]):
        if not allows(scope, "team", team_id):
            continue
        team = store.get_team(user["organization_id"], team_id)
        if team is not None:
            teams.append(team)
    return teams


def _work(store, organization_id: int, person_id: int | None) -> dict:
    empty = {
        "project_count": 0,
        "sprint_count": 0,
        "current_project": None,
        "current_sprint": None,
        "past_sprints": [],
        "past_projects": [],
    }
    if person_id is None:
        return empty
    today = date.today().isoformat()
    projects = []
    scope = store.membership_scope(person_id)
    for team_id in sorted(scope["team"]):
        team = store.get_team(organization_id, team_id)
        if team is None:
            continue
        iterations = store.list_iterations(team_id)
        current = [
            item for item in iterations if item["starts_on"] <= today <= item["ends_on"]
        ]
        past = [item for item in iterations if item["ends_on"] < today]
        projects.append(
            {
                "id": team["id"],
                "name": team["name"],
                "href": f"/teams/{team['id']}",
                "current": current,
                "past": past,
                "iteration_count": len(iterations),
            }
        )
    current_project = next((project for project in projects if project["current"]), None)
    if current_project is None and projects:
        current_project = max(
            projects,
            key=lambda project: max((item["ends_on"] for item in project["past"]), default=""),
        )
    past_projects = [
        project
        for project in projects
        if current_project is None or project["id"] != current_project["id"]
    ]
    current_sprint = current_project["current"][0] if current_project and current_project["current"] else None
    past_sprints = current_project["past"] if current_project else []
    return {
        "project_count": len(projects),
        "sprint_count": sum(project["iteration_count"] for project in projects),
        "current_project": current_project,
        "current_sprint": current_sprint,
        "past_sprints": past_sprints,
        "past_projects": past_projects,
    }
