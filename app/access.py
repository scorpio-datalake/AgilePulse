from app.store import Database

ACTION_REFUSED = "That action was refused."
RECORD_HIDDEN = "That record is not available."


def access_scope(store: Database, user_id: int | None) -> dict | None:
    if user_id is None:
        return _empty_scope()
    person = store.person_by_user_id(user_id)
    if person is None:
        return _empty_scope()
    if person["account_access"] == "admin":
        return None
    scope = store.membership_scope(person["id"])
    scope["edit"] = person["account_access"] == "member"
    return scope


def allows(scope: dict | None, kind: str, record_id: int) -> bool:
    if scope is None:
        return True
    return record_id in scope[kind]


def allows_edit(scope: dict | None) -> bool:
    if scope is None:
        return True
    return bool(scope["edit"])


def prune_tree(tree: list[dict], scope: dict) -> list[dict]:
    pruned = []
    for portfolio in tree:
        if portfolio["id"] not in scope["portfolio"]:
            continue
        streams = []
        for stream in portfolio["streams"]:
            if stream["id"] not in scope["stream"]:
                continue
            groups = []
            for group in stream["groups"]:
                if group["id"] not in scope["group"]:
                    continue
                teams = [team for team in group["teams"] if team["id"] in scope["team"]]
                groups.append({**group, "teams": teams})
            streams.append({**stream, "groups": groups})
        pruned.append({**portfolio, "streams": streams})
    return pruned


def _empty_scope() -> dict:
    return {
        "portfolio": set(),
        "stream": set(),
        "group": set(),
        "team": set(),
        "edit": False,
    }
