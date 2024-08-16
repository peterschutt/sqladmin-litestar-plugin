from __future__ import annotations

from datetime import timezone
from typing import Any

from sqladmin import ModelView
from sqladmin.forms import ModelConverter, converts
from wtforms import DateTimeField


class DateTimeUTCField(DateTimeField):
    def process_formdata(self, valuelist: list[Any]) -> None:
        super().process_formdata(valuelist)

        if self.data is None:
            return

        self.data = self.data.replace(tzinfo=timezone.utc)


class DateTimeUTCConverter(ModelConverter):
    # mypy: error: Untyped decorator makes function "convert_date_time_utc" untyped  [misc]
    @converts("DateTimeUTC")  # type: ignore[misc]
    def convert_date_time_utc(self, *, kwargs: dict[str, Any], **_: Any) -> DateTimeUTCField:  # noqa: PLR6301
        return DateTimeUTCField(**kwargs)


class AuditModelView(ModelView):
    form_converter = DateTimeUTCConverter
