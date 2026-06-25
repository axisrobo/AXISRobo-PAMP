from __future__ import annotations
from typing import Any
from app.domain.technology.repository import TechStackRepository

class TechStackService:
    def __init__(self, repo: TechStackRepository):
        self._repo = repo

    async def list_items(self, page: int = 1, page_size: int = 20):
        return await self._repo.list(page, page_size)

    async def list_master_items(
        self, *,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        subCategory: str | None = None,
        component: str | None = None,
        componentPackage: str | None = None,
        eaAdvice: str | None = None,
        status: str | None = None,
        sort_field: str = "master_no",
        sort_order: str = "asc",
    ) -> tuple[list[dict[str, Any]], int]:
        return await self._repo.list_master_filtered(
            page=page,
            page_size=page_size,
            category=category,
            subCategory=subCategory,
            component=component,
            componentPackage=componentPackage,
            eaAdvice=eaAdvice,
            status=status,
            sort_field=sort_field,
            sort_order=sort_order,
        )

    async def soft_delete(self, item_id: str):
        return await self._repo.soft_delete(item_id)
