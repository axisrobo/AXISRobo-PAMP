"""Tests for app/utils/filters.py — full coverage."""
from __future__ import annotations

import pytest

from app.utils.filters import multi_value_condition, multi_value_int_condition


class TestMultiValueCondition:
    def test_single_value_produces_eq(self):
        params: dict = {}
        cond = multi_value_condition("status", "status", "Active", params)
        assert cond == "status = :status"
        assert params == {"status": "Active"}

    def test_multiple_values_produces_in(self):
        params: dict = {}
        cond = multi_value_condition("status", "status", "Active,Planned", params)
        assert cond == "status IN (:status_0, :status_1)"
        assert params["status_0"] == "Active"
        assert params["status_1"] == "Planned"

    def test_values_stripped_of_whitespace(self):
        params: dict = {}
        cond = multi_value_condition("status", "status", " Active , Planned ", params)
        assert params["status_0"] == "Active"
        assert params["status_1"] == "Planned"

    def test_empty_segments_ignored(self):
        params: dict = {}
        cond = multi_value_condition("status", "st", "Active,,Planned", params)
        assert cond == "status IN (:st_0, :st_1)"
        assert "st_0" in params
        assert "st_1" in params

    def test_custom_column_and_prefix(self):
        params: dict = {}
        cond = multi_value_condition("u.domain", "dom", "EA,BCM", params)
        assert cond == "u.domain IN (:dom_0, :dom_1)"
        assert params["dom_0"] == "EA"


class TestMultiValueIntCondition:
    def test_single_int_produces_eq(self):
        params: dict = {}
        cond = multi_value_int_condition("category_id", "cat", "5", params)
        assert cond == "category_id = :cat"
        assert params["cat"] == 5

    def test_multiple_ints_produces_in(self):
        params: dict = {}
        cond = multi_value_int_condition("category_id", "cat", "1,2,3", params)
        assert cond == "category_id IN (:cat_0, :cat_1, :cat_2)"
        assert params["cat_0"] == 1
        assert params["cat_1"] == 2
        assert params["cat_2"] == 3

    def test_whitespace_stripped(self):
        params: dict = {}
        multi_value_int_condition("id", "id", " 10 , 20 ", params)
        assert params["id_0"] == 10
        assert params["id_1"] == 20
