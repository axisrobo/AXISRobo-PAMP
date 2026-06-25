"""Unified date/datetime parsing helpers.

All backend routes MUST use these helpers when passing date or datetime
values from request bodies to SQL queries via asyncpg.

asyncpg requires native Python ``datetime.date`` or ``datetime.datetime``
objects — passing raw ISO-8601 strings will raise ``DataError``.

Usage
-----
::

    from app.utils.date_helpers import parse_date, parse_datetime

    # For DATE columns (YYYY-MM-DD):
    params["issue_date"] = parse_date(body.get("issuedDate"))

    # For TIMESTAMP / TIMESTAMPTZ columns:
    params["start_time"] = parse_datetime(body.get("startTime"))

    # In dynamic SET builders, use coerce_params() to auto-convert:
    params = coerce_params(params, date_fields={"issue_date"}, datetime_fields={"start_time"})
"""
from __future__ import annotations

from datetime import date, datetime


def parse_date(val: str | date | None) -> date | None:
    """Convert an ISO date string ``"YYYY-MM-DD"`` → ``datetime.date``.

    Accepts:
        - ``None`` → ``None``
        - ``datetime.date`` → returned as-is
        - ``datetime.datetime`` → ``.date()``
        - ``str`` (ISO-8601, only first 10 chars used) → ``date.fromisoformat()``
    """
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    s = str(val).strip()
    if not s:
        return None
    return date.fromisoformat(s[:10])


def parse_datetime(val: str | datetime | None) -> datetime | None:
    """Convert an ISO datetime string → naive ``datetime.datetime``.

    Accepts:
        - ``None`` → ``None``
        - ``datetime`` → timezone stripped (naive)
        - ``date`` → promoted to ``datetime`` at midnight
        - ``str`` (various ISO formats) → parsed then made naive

    Handles formats:
        - ``"2025-03-17"``
        - ``"2025-03-17T13:00:00"``
        - ``"2025-03-17T13:00"``
        - ``"2025-03-17T13:00:00Z"``
        - ``"2025-03-17T13:00:00+08:00"``
    """
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.replace(tzinfo=None)
    if isinstance(val, date):
        return datetime(val.year, val.month, val.day)
    v = str(val).strip()
    if not v:
        return None
    v = v.rstrip("Z").replace(" ", "T")
    # Strip timezone offset "+HH:MM" or "+HHMM"
    if "+" in v and v.rindex("+") > 10:
        v = v[:v.rindex("+")]
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse datetime: {val!r}")


def coerce_params(
    params: dict,
    *,
    date_fields: set[str] | None = None,
    datetime_fields: set[str] | None = None,
) -> dict:
    """Auto-convert string values in *params* dict for named date/datetime fields.

    This is a convenience wrapper for dynamic SET builders — pass the sets of
    DB column names that should be dates or datetimes, and this function will
    convert any string values to the proper Python type.

    ::

        params = coerce_params(
            params,
            date_fields={"start_date", "end_date"},
            datetime_fields={"start_time", "end_time"},
        )
    """
    if date_fields:
        for key in date_fields:
            if key in params:
                params[key] = parse_date(params[key])
    if datetime_fields:
        for key in datetime_fields:
            if key in params:
                params[key] = parse_datetime(params[key])
    return params
