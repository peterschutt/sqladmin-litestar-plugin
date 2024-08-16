from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import Column, String
from sqlalchemy.orm import sessionmaker
from wtforms import Form

from sqladmin_litestar_plugin.ext.advanced_alchemy import AuditModelView, DateTimeUTCField


class DummyPostData(Dict[str, Any]):
    def getlist(self, key: str) -> list[Any]:
        v = self[key]
        if isinstance(v, (list, tuple)):
            return list(v)
        return [v]


def test_date_time_utc_field() -> None:
    class F(Form):
        f = DateTimeUTCField()

    form = F(DummyPostData({"f": "2021-01-01 00:00:00"}))
    assert form.f.data == datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def test_date_time_utc_field_on_no_data() -> None:
    class F(Form):
        f = DateTimeUTCField()

    form = F(DummyPostData({"f": []}))
    assert form.f.data is None


@pytest.mark.anyio
async def test_audit_model_view() -> None:
    class MyModel(UUIDAuditBase):
        my_column = Column(String(10))

    class MyModelView(AuditModelView, model=MyModel):
        session_maker = sessionmaker()

    view = MyModelView()
    form = await view.scaffold_form()

    assert isinstance(form()._fields["created_at"], DateTimeUTCField)
    assert isinstance(form()._fields["updated_at"], DateTimeUTCField)
