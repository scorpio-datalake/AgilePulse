from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from starlette.middleware.sessions import SessionMiddleware

from app.db import ADMIN_PASSWORD, ADMIN_USERNAME, migrate
from app.landing import home_context
from app.navigation import shell
from app.organization import register_organization
from app.work import register_work
from app.passwords import verify_password
from app.schemas import NameForm, PasswordChangeForm, SignInForm
from app.settings import Settings, load_settings
from app.store import Database, get_store, open_store

PACKAGE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")
REFUSED = "Sign-in was refused."
PASSWORD_REQUIRED = "A password is required."
PASSWORD_MISMATCH = "Type the same password in both fields."
PASSWORD_DEFAULT = "Choose a password other than admin."
NAME_REQUIRED = "A name is required."


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    settings.database_path = settings.database_path.expanduser().resolve()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        migrate(app.state.settings.database_path)
        yield

    app = FastAPI(title="AgilePulse", lifespan=lifespan)
    app.state.settings = settings

    app.add_middleware(AdminSetupMiddleware)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie="se_session",
        same_site="lax",
        https_only=False,
    )
    app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")

    @app.get("/")
    def home(request: Request, store: Annotated[Database, Depends(get_store)]):
        user = _current_user(request, store)
        if user is None:
            return RedirectResponse("/sign-in", status_code=303)
        return templates.TemplateResponse(
            request,
            "home.html",
            {
                "display_name": user["display_name"],
                "error": None,
                **home_context(store, user),
                **shell(store, user["organization_id"], "home", user_id=user["id"]),
            },
        )

    @app.get("/sign-in")
    def sign_in_page(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
    ):
        signed_in = _current_user(request, store)
        if signed_in is not None:
            return RedirectResponse(_next_page(request, store, signed_in), status_code=303)
        return _sign_in_page(request, None)

    @app.post("/sign-in")
    def sign_in(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        username: Annotated[str, Form()] = "",
        password: Annotated[str, Form()] = "",
    ):
        try:
            form = SignInForm(username=username, password=password)
        except ValidationError:
            return _sign_in_page(request, REFUSED, status_code=422)
        user = store.user_by_username(form.username)
        if user is None or not verify_password(form.password, user["password_hash"]):
            return _sign_in_page(request, REFUSED, status_code=401)
        request.session["user_id"] = user["id"]
        return RedirectResponse(_next_page(request, store, user), status_code=303)

    @app.get("/setup/password")
    def setup_password_page(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
    ):
        user = _current_user(request, store)
        if user is None:
            return RedirectResponse("/sign-in", status_code=303)
        return _password_page(request, store, user, None)

    @app.post("/setup/password")
    def setup_password(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        password: Annotated[str, Form()] = "",
        password_again: Annotated[str, Form()] = "",
    ):
        user = _current_user(request, store)
        if user is None:
            return RedirectResponse("/sign-in", status_code=303)
        if not password.strip() or not password_again.strip():
            return _password_page(request, store, user, PASSWORD_REQUIRED, status_code=422)
        try:
            form = PasswordChangeForm(password=password, password_again=password_again)
        except ValidationError:
            return _password_page(request, store, user, PASSWORD_MISMATCH, status_code=422)
        if form.password.casefold() == ADMIN_PASSWORD:
            return _password_page(request, store, user, PASSWORD_DEFAULT, status_code=422)
        store.set_password(user["id"], form.password)
        user = store.user_by_id(user["id"])
        return RedirectResponse(_next_page(request, store, user), status_code=303)

    @app.get("/setup/user")
    def setup_user_page(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
    ):
        user = _current_user(request, store)
        if user is None:
            return RedirectResponse("/sign-in", status_code=303)
        return _user_page(request, store, user, None)

    @app.post("/setup/user")
    def setup_user(
        request: Request,
        store: Annotated[Database, Depends(get_store)],
        name: Annotated[str, Form()] = "",
    ):
        user = _current_user(request, store)
        if user is None:
            return RedirectResponse("/sign-in", status_code=303)
        try:
            form = NameForm(name=name)
        except ValidationError:
            return _user_page(request, store, user, NAME_REQUIRED, status_code=422)
        store.create_person(user["organization_id"], form.name)
        return RedirectResponse("/", status_code=303)

    @app.post("/sign-out")
    def sign_out(request: Request):
        request.session.clear()
        return RedirectResponse("/sign-in", status_code=303)

    register_organization(app, templates)
    register_work(app, templates)
    return app


def _current_user(request: Request, store: Database):
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        return None
    return store.user_by_id(user_id)


def _sign_in_page(request: Request, error: str | None, status_code: int = 200):
    return templates.TemplateResponse(
        request,
        "sign_in.html",
        {
            "error": error,
            "admin_username": ADMIN_USERNAME,
            "admin_password": ADMIN_PASSWORD,
            "require_admin_setup": request.app.state.settings.require_admin_setup,
        },
        status_code=status_code,
    )


def _next_page(request: Request, store: Database, user) -> str:
    if not request.app.state.settings.require_admin_setup:
        return "/"
    return _pending_setup(store, user) or "/"


def _pending_setup(store: Database, user) -> str | None:
    if user["must_change_password"]:
        return "/setup/password"
    organization_id = user["organization_id"]
    if organization_id is None or not store.has_added_user(organization_id):
        return "/setup/user"
    return None


def _password_page(
    request: Request,
    store: Database,
    user,
    error: str | None,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        request,
        "setup_password.html",
        {"error": error, **shell(store, user["organization_id"], None, user_id=user["id"])},
        status_code=status_code,
    )


def _user_page(
    request: Request,
    store: Database,
    user,
    error: str | None,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        request,
        "setup_user.html",
        {"error": error, **shell(store, user["organization_id"], None, user_id=user["id"])},
        status_code=status_code,
    )


class AdminSetupMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        settings = scope["app"].state.settings
        path = scope["path"]
        if (
            not settings.require_admin_setup
            or path.startswith("/static")
            or path in {"/sign-in", "/sign-out"}
        ):
            await self.app(scope, receive, send)
            return
        user_id = scope.get("session", {}).get("user_id")
        if not isinstance(user_id, int):
            await self.app(scope, receive, send)
            return
        with open_store(settings.database_path) as store:
            user = store.user_by_id(user_id)
            destination = None if user is None else _pending_setup(store, user)
        if destination is None:
            if path.startswith("/setup"):
                response = RedirectResponse("/", status_code=303)
                await response(scope, receive, send)
                return
            await self.app(scope, receive, send)
            return
        if path == destination:
            await self.app(scope, receive, send)
            return
        response = RedirectResponse(destination, status_code=303)
        await response(scope, receive, send)
