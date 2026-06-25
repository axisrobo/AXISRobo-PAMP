"""Tests for app/utils/csv_export.py — full coverage."""
from __future__ import annotations

import io
import pytest
from fastapi.responses import StreamingResponse

from app.utils.csv_export import sanitize_cell, build_csv_response


class TestSanitizeCell:
    def test_none_returns_empty_string(self):
        assert sanitize_cell(None) == ""

    def test_normal_string_unchanged(self):
        assert sanitize_cell("hello world") == "hello world"

    def test_equals_sign_prefix_escaped(self):
        assert sanitize_cell("=SUM(A1:A10)") == "'=SUM(A1:A10)"

    def test_plus_sign_prefix_escaped(self):
        assert sanitize_cell("+1234") == "'+1234"

    def test_minus_sign_prefix_escaped(self):
        assert sanitize_cell("-bad") == "'-bad"

    def test_at_sign_prefix_escaped(self):
        assert sanitize_cell("@user") == "'@user"

    def test_integer_value(self):
        assert sanitize_cell(42) == "42"

    def test_empty_string_not_escaped(self):
        assert sanitize_cell("") == ""


class TestBuildCsvResponse:
    def test_returns_streaming_response(self):
        rows = [{"name": "Alice", "age": 30}]
        headers = ["name", "age"]
        response = build_csv_response(rows, headers, "test.csv")
        assert isinstance(response, StreamingResponse)

    def test_content_disposition_set(self):
        response = build_csv_response([], ["col"], "report.csv")
        assert "report.csv" in response.headers["content-disposition"]

    async def test_csv_content_correct(self):
        rows = [{"a": "hello", "b": "world"}, {"a": "=inject", "b": "safe"}]
        response = build_csv_response(rows, ["a", "b"], "out.csv")
        # Consume the streaming content
        content = b""
        async for chunk in response.body_iterator:
            if isinstance(chunk, bytes):
                content += chunk
            else:
                content += chunk.encode()
        text = content.decode("utf-8-sig")  # strip BOM
        assert "hello" in text
        assert "world" in text
        # formula injection prevented
        assert "'=inject" in text

    async def test_missing_column_returns_empty(self):
        rows = [{"name": "Bob"}]
        response = build_csv_response(rows, ["name", "missing_col"], "out.csv")
        content = b""
        async for chunk in response.body_iterator:
            if isinstance(chunk, bytes):
                content += chunk
            else:
                content += chunk.encode()
        text = content.decode("utf-8-sig")
        assert "Bob" in text
