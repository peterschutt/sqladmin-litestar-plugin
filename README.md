# sqladmin-litestar-plugin

## Overview

The `SQLAdminPlugin` integrates SQLAdmin with a Litestar application.

## Acknowledgements

Thanks to [aminalaee](https://github.com/aminalaee) and all [contributors](https://github.com/aminalaee/sqladmin/graphs/contributors) for the excellent [SQLAdmin](https://github.com/aminalaee/sqladmin) project.

## Installation

To install the dependencies, run:

```bash
pip install sqladmin-litestar-plugin
```

## Usage

To use the plugin, import the `SQLAdminPlugin` class and pass it to the `Litestar` application.

By default, the plugin will create a new admin interface at `/admin`.

### Example

```python
from litestar import Litestar
from sqladmin import ModelView
from sqladmin_litestar_plugin import SQLAdminPlugin
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base


engine = create_async_engine("sqlite+aiosqlite:///example.db")
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.name]


async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # Create tables


admin = SQLAdminPlugin(views=[UserAdmin], engine=engine)
app = Litestar(plugins=[admin], on_startup=[on_startup])
```

## Configuration

The `SQLAdminPlugin` accepts the following arguments:

- `views`: A sequence of `ModelView` classes to add to the admin app. Each `ModelView` class configures the interface for a SQL model.
- `engine`: An SQLAlchemy engine to connect to your database.
- `sessionmaker`: An SQLAlchemy `sessionmaker` instance used to manage sessions.
- `base_url`: The base URL where the admin app will be hosted.
- `title`: The title of the admin app, which appears in the browser's title bar and the header of the admin interface.
- `logo_url`: The URL of the logo to display in the admin app, enhancing brand visibility.
- `templates_dir`: The directory containing the Jinja2 templates for the admin interface, allowing for customization of the UI.
- `middlewares`: A sequence of Starlette middlewares to add to the admin app, useful for handling requests or adding additional functionality.
- `authentication_backend`: An authentication backend to secure the admin app, managing user authentication and authorization.

Views are not added to the admin app until the Litestar application is instantiated, so you can append views to the
`views` list until this point.

## Use with Advanced-Alchemy Audit Base Variants

Advanced-Alchemy (AA) provides variants of base models that include `created_at` and `updated_at` fields which enforce
that `tzinfo` is set on the `datetime` instance passed through to SQLAlchemy.

When a model is created via the SQLAdmin UI, the `created_at` and `updated_at` fields default to the current time in UTC,
however, the `tzinfo` property of the `datetime` is not set.

`sqladmin-litestar-plugin` provides a custom `ModelView` class that ensures the `tzinfo` property is set on `datetime`
instances when the form field represents an AA `DateTimeUTC` field.

Example:

```python
from __future__ import annotations

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import Column, String

from sqladmin_litestar_plugin.ext.advanced_alchemy import AuditModelView


class Entity(UUIDAuditBase):
    my_column = Column(String(10))


class EntityAdmin(AuditModelView, model=Entity): ...
```

For a full working example, see the `examples/aa_audit_base` directory in this repo.

The `AuditModelView` class should also be useful for models that don't depend on one of the AA audit model bases, but
still use `DateTimeUTC` fields.
