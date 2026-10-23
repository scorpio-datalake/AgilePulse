import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
SKIPPED = {"connect", "migrate", "attach_login"}


def _session_functions() -> list[str]:
    tree = ast.parse((APP / "db.py").read_text())
    names = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name.startswith("_") or node.name in SKIPPED:
            continue
        if node.args.args and node.args.args[0].arg == "session":
            names.append(node.name)
    return names


def _class_methods(class_name: str) -> list[str]:
    tree = ast.parse((APP / "store.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return [
                item.name
                for item in node.body
                if isinstance(item, ast.FunctionDef) and item.name != "__init__"
            ]
    raise AssertionError(class_name)


def test_store_matches_database_functions():
    names = _session_functions()
    assert _class_methods("Database") == names
    assert _class_methods("SqlStore") == names
