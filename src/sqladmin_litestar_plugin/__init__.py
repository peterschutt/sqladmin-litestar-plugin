from __future__ import annotations

from typing import TYPE_CHECKING, Any

import sqladmin
from litestar import asgi
from litestar.plugins.base import InitPluginProtocol
from litestar.types.empty import Empty
from litestar.utils.empty import value_or_default
from starlette.applications import Starlette

if TYPE_CHECKING:
    from collections.abc import Sequence

    from litestar.config.app import AppConfig
    from litestar.types.asgi_types import Receive, Scope, Send
    from litestar.types.empty import EmptyType
    from sqladmin import ModelView
    from sqladmin.authentication import AuthenticationBackend
    from sqlalchemy.engine import Engine
    from sqlalchemy.ext.asyncio import AsyncEngine
    from sqlalchemy.orm import sessionmaker
    from starlette import types as st_types
    from starlette.middleware import Middleware

__all__ = ("SQLAdminPlugin",)


class SQLAdminPlugin(InitPluginProtocol):
    def __init__(  # noqa: PLR0913
        self,
        *,
        views: Sequence[type[ModelView]] | EmptyType = Empty,
        engine: Engine | AsyncEngine | EmptyType = Empty,
        sessionmaker: sessionmaker[Any] | EmptyType = Empty,
        base_url: str | EmptyType = Empty,
        title: str | EmptyType = Empty,
        logo_url: str | EmptyType = Empty,
        templates_dir: str | EmptyType = Empty,
        middlewares: Sequence[Middleware] | EmptyType = Empty,
        authentication_backend: AuthenticationBackend | EmptyType = Empty,
    ) -> None:
        """Initializes the SQLAdminPlugin.

        Args:
            views: A sequence of ModelView classes to add to the admin app.
            engine: An SQLAlchemy engine.
            sessionmaker: An SQLAlchemy sessionmaker.
            base_url: The base URL for the admin app.
            title: The title of the admin app.
            logo_url: The URL of the logo to display in the admin app.
            templates_dir: The directory containing the Jinja2 templates for the admin app.
            middlewares: A sequence of Starlette middlewares to add to the admin app.
            authentication_backend: An authentication backend to use for the admin app.
        """
        self.views = list(value_or_default(views, []))
        admin_kwargs = {
            kw: value
            for kw, value in [
                ("engine", engine),
                ("sessionmaker", sessionmaker),
                ("base_url", base_url),
                ("title", title),
                ("logo_url", logo_url),
                ("templates_dir", templates_dir),
                ("middlewares", middlewares),
                ("authentication_backend", authentication_backend),
            ]
            if value is not Empty
        }
        self.app = Starlette()
        self.admin = sqladmin.Admin(app=self.app, **admin_kwargs)  # type: ignore[arg-type]
        self.app.add_middleware(PathFixMiddleware, base_url=self.admin.base_url)
        # disables redirecting based on absence/presence of trailing slashes
        self.app.router.redirect_slashes = False
        self.admin.admin.router.redirect_slashes = False

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        for view in self.views:
            self.admin.add_view(view)

        @asgi("/", is_mount=True)
        async def wrapped_app(scope: Scope, receive: Receive, send: Send) -> None:
            """Wraps the ASGI app to ensure the litestar app is set in the scope.

            Starlette overwrites the app in the scope, so we need to ensure it is set back to the
            litestar app, in case it is needed after the request is handled (e.g., for exception
            handling).
            """
            app = scope["app"]
            try:
                await self.app(scope, receive, send)  # type: ignore[arg-type]
            finally:
                scope["app"] = app

        app_config.route_handlers.append(wrapped_app)
        return app_config


class PathFixMiddleware:
    def __init__(self, app: st_types.ASGIApp, *, base_url: str) -> None:
        self.app = app
        self.base_url = base_url.rstrip("/")

    async def __call__(
        self, scope: st_types.Scope, receive: st_types.Receive, send: st_types.Send
    ) -> None:
        orig_path = scope["path"]
        orig_raw = scope["raw_path"]

        path = f"/{scope['path'].lstrip('/').rstrip('/')}"
        if path == self.base_url:
            path = f"{path}/"

        scope["path"] = path
        scope["raw_path"] = scope["path"].encode("utf-8")

        def reset_paths() -> None:
            scope["path"] = orig_path
            scope["raw_path"] = orig_raw

        async def send_wrapper(message: Any) -> None:
            await send(message)
            reset_paths()

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            reset_paths()
