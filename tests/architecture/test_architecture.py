"""Architecture check (T024, research R7, Constitution Principle I).

Fails if the Domain or Application import forbidden libraries/layers, or if an API
route handler contains a business condition or does not call exactly one use case.
Static check of the stated rules, not a proof; code review still applies.
"""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "changeflow"

DOMAIN_FORBIDDEN = (
    "fastapi",
    "starlette",
    "pydantic",
    "sqlite3",
    "sqlalchemy",
    "httpx",
    "uvicorn",
    "changeflow.application",
    "changeflow.infrastructure",
    "changeflow.api",
)
APPLICATION_FORBIDDEN = (
    "fastapi",
    "starlette",
    "sqlite3",
    "sqlalchemy",
    "uvicorn",
    "changeflow.infrastructure",
    "changeflow.api",
)

ROUTE_METHODS = {"get", "post", "put", "patch", "delete"}
FORBIDDEN_NODES = (ast.If, ast.IfExp, ast.Match, ast.While, ast.For, ast.BoolOp, ast.Compare)
FORBIDDEN_NAMES = {"Status", "Role", "requester_id", "roles"}


# --- Import checks -----------------------------------------------------------


def imported_modules(path: Path, src_root: Path = SRC) -> set[str]:
    """Absolute names of every module imported by the file, resolving relative imports."""
    package = ["changeflow", *path.relative_to(src_root).parent.parts]
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: len(package) - (node.level - 1)]
                module = ".".join([*base, *([node.module] if node.module else [])])
            else:
                module = node.module or ""
            names.add(module)
            names.update(f"{module}.{alias.name}" for alias in node.names)
    return names


def violations(package_dir: Path, forbidden: tuple[str, ...], src_root: Path = SRC) -> list[str]:
    found = []
    for path in sorted(package_dir.rglob("*.py")):
        for name in imported_modules(path, src_root):
            for prefix in forbidden:
                if name == prefix or name.startswith(prefix + "."):
                    found.append(f"{path.relative_to(src_root)} imports {name}")
    return found


def test_domain_has_no_http_persistence_or_outer_layer_imports():
    assert violations(SRC / "domain", DOMAIN_FORBIDDEN) == []


def test_application_has_no_http_persistence_or_outer_layer_imports():
    assert violations(SRC / "application", APPLICATION_FORBIDDEN) == []


# --- Route handler checks ----------------------------------------------------


def is_route(func: ast.AST) -> bool:
    for decorator in getattr(func, "decorator_list", []):
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "router"
            and target.attr in ROUTE_METHODS
        ):
            return True
    return False


def use_case_params(func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    args = [*func.args.posonlyargs, *func.args.args, *func.args.kwonlyargs]
    return {
        a.arg
        for a in args
        if isinstance(a.annotation, ast.Name) and a.annotation.id == "UseCases"
    }


def handler_violations(func: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    problems = []
    params = use_case_params(func)
    use_case_calls = 0
    for statement in func.body:
        for node in ast.walk(statement):
            if isinstance(node, FORBIDDEN_NODES):
                problems.append(f"{func.name}: contains {type(node).__name__}")
            if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
                problems.append(f"{func.name}: refers to {node.id}")
            if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_NAMES:
                problems.append(f"{func.name}: refers to .{node.attr}")
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in params
            ):
                use_case_calls += 1
    if use_case_calls != 1:
        problems.append(f"{func.name}: calls {use_case_calls} use cases (expected exactly 1)")
    return problems


def check_routes_source(source: str) -> list[str]:
    problems = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_route(node):
            problems.extend(handler_violations(node))
    return problems


def test_route_handlers_have_no_business_conditions_and_call_one_use_case():
    source = (SRC / "api" / "routes.py").read_text()
    assert check_routes_source(source) == []


# --- Self-tests: the checker must not pass vacuously -------------------------

BAD_HANDLER = '''
@router.post("/change-requests/{id}/approve")
async def approve(id: str, request: Request, use_cases: UseCases = Depends(get_use_cases)):
    loaded = use_cases.get(bearer_token(request), id)
    if loaded.status == Status.PENDING_REVIEW and loaded.requester_id != "x":
        return use_cases.approve(bearer_token(request), id, await json_body(request))
'''

GOOD_HANDLER = '''
@router.post("/change-requests/{id}/approve")
async def approve(id: str, request: Request, use_cases: UseCases = Depends(get_use_cases)):
    return to_out(use_cases.approve(bearer_token(request), id, await json_body(request)))
'''


def test_checker_flags_a_handler_with_business_conditions():
    problems = check_routes_source(BAD_HANDLER)
    assert any("If" in p for p in problems)
    assert any("Compare" in p for p in problems)
    assert any("Status" in p for p in problems)
    assert any("requester_id" in p for p in problems)
    assert any("calls 2 use cases" in p for p in problems)


def test_checker_accepts_a_thin_handler():
    assert check_routes_source(GOOD_HANDLER) == []


@pytest.mark.parametrize(
    "source,expected",
    [
        ("import sqlite3\n", "sqlite3"),
        ("from fastapi import Request\n", "fastapi.Request"),
        ("from ..infrastructure import sqlite_db\n", "changeflow.infrastructure.sqlite_db"),
    ],
)
def test_import_checker_flags_forbidden_imports(tmp_path, source, expected):
    fake_src = tmp_path / "changeflow"
    module = fake_src / "domain" / "bad.py"
    module.parent.mkdir(parents=True)
    module.write_text(source)
    found = violations(fake_src / "domain", DOMAIN_FORBIDDEN, src_root=fake_src)
    assert any(expected in v for v in found)
