"""Pagination helpers matching the TS backend contract."""
import math
from fastapi import Query


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        pageSize: int = Query(20, ge=1, le=500),
        sortField: str | None = Query(None),
        sortBy: str | None = Query(None),
        sortOrder: str | None = Query(None),
    ):
        self.page = page
        self.page_size = pageSize
        self.sort_field = sortField or sortBy
        self.sort_order = sortOrder

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def paginated_response(data: list, total: int, page: int, page_size: int) -> dict:
    """Build the standard pagination response shape."""
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 0
    return {
        "data": data,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": total_pages,
    }
