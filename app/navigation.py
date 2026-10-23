
from app.access import access_scope, prune_tree
from app.store import Database


def shell(
    store: Database,
    organization_id: int,
    current: str | None,
    current_id: int | None = None,
    user_id: int | None = None,
) -> dict:
    tree = store.organization_tree(organization_id)
    if user_id is not None:
        scope = access_scope(store, user_id)
        if scope is not None:
            tree = prune_tree(tree, scope)
    return {
        "nav_tree": tree,
        "nav_current": current,
        "nav_current_id": current_id,
    }


def portfolio_breadcrumb(portfolio: dict) -> list[dict]:
    return [{"name": portfolio["name"], "href": None}]


def stream_breadcrumb(
    store: Database, organization_id: int, stream: dict
) -> list[dict]:
    portfolio = store.get_portfolio(organization_id, stream["portfolio_id"])
    return [
        _link(portfolio, f"/portfolios/{portfolio['id']}"),
        {"name": stream["name"], "href": None},
    ]


def group_breadcrumb(
    store: Database, organization_id: int, group: dict
) -> list[dict]:
    stream = store.get_value_stream(organization_id, group["value_stream_id"])
    portfolio = store.get_portfolio(organization_id, stream["portfolio_id"])
    return [
        _link(portfolio, f"/portfolios/{portfolio['id']}"),
        _link(stream, f"/value-streams/{stream['id']}"),
        {"name": group["name"], "href": None},
    ]


def team_breadcrumb(
    store: Database, organization_id: int, team: dict
) -> list[dict]:
    group = store.get_delivery_group(organization_id, team["delivery_group_id"])
    stream = store.get_value_stream(organization_id, group["value_stream_id"])
    portfolio = store.get_portfolio(organization_id, stream["portfolio_id"])
    return [
        _link(portfolio, f"/portfolios/{portfolio['id']}"),
        _link(stream, f"/value-streams/{stream['id']}"),
        _link(group, f"/delivery-groups/{group['id']}"),
        {"name": team["name"], "href": None},
    ]


def _link(record: dict, href: str) -> dict:
    return {"name": record["name"], "href": href}


def goal_breadcrumb(store: Database, organization_id: int, goal: dict) -> list[dict]:
    stream = store.get_value_stream(organization_id, goal["value_stream_id"])
    return stream_breadcrumb(store, organization_id, stream)[:-1] + [
        _link(stream, f"/value-streams/{stream['id']}"),
        {"name": goal["name"], "href": None},
    ]


def initiative_breadcrumb(
    store: Database, organization_id: int, initiative: dict
) -> list[dict]:
    goal = store.get_goal(organization_id, initiative["goal_id"])
    return goal_breadcrumb(store, organization_id, goal)[:-1] + [
        _link(goal, f"/goals/{goal['id']}"),
        {"name": initiative["name"], "href": None},
    ]


def feature_breadcrumb(
    store: Database, organization_id: int, feature: dict
) -> list[dict]:
    initiative = store.get_initiative(organization_id, feature["initiative_id"])
    return initiative_breadcrumb(store, organization_id, initiative)[:-1] + [
        _link(initiative, f"/initiatives/{initiative['id']}"),
        {"name": feature["name"], "href": None},
    ]


def story_breadcrumb(store: Database, organization_id: int, story: dict) -> list[dict]:
    feature = store.get_feature(organization_id, story["feature_id"])
    return feature_breadcrumb(store, organization_id, feature)[:-1] + [
        _link(feature, f"/features/{feature['id']}"),
        {"name": story["name"], "href": None},
    ]
