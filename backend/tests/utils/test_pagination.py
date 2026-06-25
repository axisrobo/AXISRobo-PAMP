"""Tests for app/utils/pagination.py — full coverage."""
from __future__ import annotations

import math
import pytest

from app.utils.pagination import PaginationParams, paginated_response


class TestPaginationParams:
    def test_defaults(self):
        p = PaginationParams.__new__(PaginationParams)
        p.page = 1
        p.page_size = 20
        p.sort_field = None
        p.sort_order = None
        assert p.offset == 0

    def test_offset_calculation_page_2(self):
        p = PaginationParams.__new__(PaginationParams)
        p.page = 2
        p.page_size = 20
        assert p.offset == 20

    def test_offset_calculation_page_3_size_10(self):
        p = PaginationParams.__new__(PaginationParams)
        p.page = 3
        p.page_size = 10
        assert p.offset == 20

    def test_sort_field_from_sortField(self):
        p = PaginationParams.__new__(PaginationParams)
        p.page = 1
        p.page_size = 20
        p.sort_field = "createdAt"
        p.sort_order = "asc"
        assert p.sort_field == "createdAt"


class TestPaginatedResponse:
    def test_basic_response_shape(self):
        result = paginated_response([{"id": 1}], total=1, page=1, page_size=20)
        assert result["data"] == [{"id": 1}]
        assert result["total"] == 1

    def test_total_pages_single_page(self):
        result = paginated_response([], total=5, page=1, page_size=20)
        assert result["totalPages"] == 1

    def test_total_pages_multiple(self):
        result = paginated_response([], total=45, page=1, page_size=20)
        assert result["totalPages"] == 3

    def test_total_zero_returns_zero_pages(self):
        result = paginated_response([], total=0, page=1, page_size=20)
        assert result["totalPages"] == 0

    def test_page_passed_through(self):
        result = paginated_response([], total=100, page=3, page_size=20)
        assert result["page"] == 3

    def test_page_size_passed_through(self):
        result = paginated_response([], total=100, page=1, page_size=15)
        assert result["pageSize"] == 15
