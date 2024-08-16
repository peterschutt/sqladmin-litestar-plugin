from __future__ import annotations

from advanced_alchemy.base import UUIDAuditBase
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar import Litestar
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyAsyncConfig
from sqlalchemy import Column, String
from sqlalchemy.ext.asyncio import create_async_engine

import sqladmin_litestar_plugin
from sqladmin_litestar_plugin.ext.advanced_alchemy import AuditModelView

engine = create_async_engine("sqlite+aiosqlite:///")


class Entity(UUIDAuditBase):
    my_column = Column(String(10))


class EntityAdmin(AuditModelView, model=Entity): ...


app = Litestar(
    plugins=(
        SQLAlchemyPlugin(config=SQLAlchemyAsyncConfig(engine_instance=engine, create_all=True)),
        sqladmin_litestar_plugin.SQLAdminPlugin(
            views=[EntityAdmin], engine=engine, base_url="/admin"
        ),
    ),
)
