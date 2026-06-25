"""Tests for app/utils/date_helpers.py — full coverage."""
from __future__ import annotations

import pytest
from datetime import date, datetime

from app.utils.date_helpers import parse_date, parse_datetime, coerce_params


# ═══════════════════════════════════════════════════════════════════
# parse_date
# ═══════════════════════════════════════════════════════════════════

class TestParseDate:
    def test_none_returns_none(self):
        assert parse_date(None) is None

    def test_date_returned_as_is(self):
        d = date(2024, 1, 15)
        assert parse_date(d) is d

    def test_datetime_returns_date_part(self):
        dt = datetime(2024, 3, 10, 12, 30)
        assert parse_date(dt) == date(2024, 3, 10)

    def test_iso_string_parsed(self):
        assert parse_date("2025-06-15") == date(2025, 6, 15)

    def test_iso_string_with_extra_chars_truncated(self):
        # Only first 10 chars used
        assert parse_date("2025-06-15T10:00:00") == date(2025, 6, 15)

    def test_empty_string_returns_none(self):
        assert parse_date("") is None

    def test_whitespace_string_returns_none(self):
        assert parse_date("   ") is None

    def test_string_with_whitespace_stripped(self):
        assert parse_date("  2025-06-15  ") == date(2025, 6, 15)


# ═══════════════════════════════════════════════════════════════════
# parse_datetime
# ═══════════════════════════════════════════════════════════════════

class TestParseDatetime:
    def test_none_returns_none(self):
        assert parse_datetime(None) is None

    def test_datetime_strips_timezone(self):
        dt = datetime(2024, 3, 10, 12, 0, tzinfo=__import__('datetime').timezone.utc)
        result = parse_datetime(dt)
        assert result == datetime(2024, 3, 10, 12, 0)
        assert result.tzinfo is None

    def test_naive_datetime_returned_as_is(self):
        dt = datetime(2024, 3, 10, 12, 30)
        result = parse_datetime(dt)
        assert result == dt
        assert result.tzinfo is None

    def test_date_promoted_to_midnight(self):
        d = date(2024, 5, 20)
        result = parse_datetime(d)
        assert result == datetime(2024, 5, 20, 0, 0, 0)

    def test_iso_date_string(self):
        assert parse_datetime("2025-03-17") == datetime(2025, 3, 17)

    def test_iso_datetime_with_seconds(self):
        assert parse_datetime("2025-03-17T13:00:00") == datetime(2025, 3, 17, 13, 0, 0)

    def test_iso_datetime_without_seconds(self):
        assert parse_datetime("2025-03-17T13:00") == datetime(2025, 3, 17, 13, 0)

    def test_iso_datetime_with_z_suffix(self):
        assert parse_datetime("2025-03-17T13:00:00Z") == datetime(2025, 3, 17, 13, 0, 0)

    def test_iso_datetime_with_positive_offset(self):
        assert parse_datetime("2025-03-17T13:00:00+08:00") == datetime(2025, 3, 17, 13, 0, 0)

    def test_iso_datetime_with_space_separator(self):
        assert parse_datetime("2025-03-17 13:00:00") == datetime(2025, 3, 17, 13, 0, 0)

    def test_empty_string_returns_none(self):
        assert parse_datetime("") is None

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError, match="Cannot parse datetime"):
            parse_datetime("not-a-date")


# ═══════════════════════════════════════════════════════════════════
# coerce_params
# ═══════════════════════════════════════════════════════════════════

class TestCoerceParams:
    def test_coerce_date_field(self):
        params = {"start_date": "2025-01-10", "val": 42}
        result = coerce_params(params, date_fields={"start_date"})
        assert result["start_date"] == date(2025, 1, 10)
        assert result["val"] == 42

    def test_coerce_datetime_field(self):
        params = {"start_time": "2025-01-10T09:00:00"}
        result = coerce_params(params, datetime_fields={"start_time"})
        assert result["start_time"] == datetime(2025, 1, 10, 9, 0, 0)

    def test_coerce_both_fields(self):
        params = {"d": "2025-06-01", "dt": "2025-06-01T12:00:00"}
        result = coerce_params(params, date_fields={"d"}, datetime_fields={"dt"})
        assert result["d"] == date(2025, 6, 1)
        assert result["dt"] == datetime(2025, 6, 1, 12, 0, 0)

    def test_missing_field_skipped(self):
        params = {"other": "value"}
        result = coerce_params(params, date_fields={"start_date"})
        assert result == {"other": "value"}

    def test_no_fields_specified_returns_unchanged(self):
        params = {"key": "value"}
        result = coerce_params(params)
        assert result == {"key": "value"}

    def test_none_date_field_coerced_to_none(self):
        params = {"end_date": None}
        result = coerce_params(params, date_fields={"end_date"})
        assert result["end_date"] is None
