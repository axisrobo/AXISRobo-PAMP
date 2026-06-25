"""Pagination assertion helpers."""
import math


def assert_paginated(body: dict, *, min_total: int = 0):
    """Validate the standard pagination response shape:
    { data: [...], total: int, page: int, pageSize: int, totalPages: int }
    """
    assert "data" in body and isinstance(body["data"], list), f"Missing or invalid 'data': {type(body.get('data'))}"
    assert "total" in body and isinstance(body["total"], int), f"Missing or invalid 'total': {body.get('total')}"
    assert body["total"] >= min_total, f"total={body['total']} < min_total={min_total}"
    assert "page" in body and isinstance(body["page"], int) and body["page"] >= 1, f"Invalid 'page': {body.get('page')}"
    assert "pageSize" in body and isinstance(body["pageSize"], int), f"Invalid 'pageSize': {body.get('pageSize')}"
    assert "totalPages" in body and isinstance(body["totalPages"], int), f"Invalid 'totalPages': {body.get('totalPages')}"
    # Derived check
    expected_pages = max(1, math.ceil(body["total"] / body["pageSize"])) if body["total"] > 0 else body["totalPages"]
    if body["total"] > 0:
        assert body["totalPages"] == expected_pages, (
            f"totalPages={body['totalPages']} != ceil({body['total']}/{body['pageSize']})={expected_pages}"
        )


def assert_has_keys(item: dict, keys: list[str], label: str = "item"):
    """Assert that a dict has all expected keys."""
    missing = [k for k in keys if k not in item]
    assert not missing, f"{label} missing keys: {missing}. Available: {list(item.keys())}"


def assert_sorted(items: list[dict], key: str, order: str = "asc"):
    """Assert items are sorted by key in given order."""
    values = [item.get(key) for item in items if item.get(key) is not None]
    if len(values) < 2:
        return  # Can't verify sort with < 2 non-null values
    normalized = [str(v).lower() for v in values]
    if order == "asc":
        assert normalized == sorted(normalized), f"Not sorted asc by {key}: {values[:5]}"
    else:
        assert normalized == sorted(normalized, reverse=True), f"Not sorted desc by {key}: {values[:5]}"
