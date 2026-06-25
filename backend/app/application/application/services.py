from __future__ import annotations
from typing import Any
from app.domain.application.repository import ApplicationRepository, BizCapabilityRepository

class ApplicationService:
    def __init__(self, repo: ApplicationRepository):
        self._repo = repo

    async def list_applications(self, page: int = 1, page_size: int = 20):
        return await self._repo.list(page, page_size)

    async def list_applications_filtered(
        self, *,
        page: int = 1,
        page_size: int = 20,
        appId: str | None = None,
        name: str | None = None,
        projectId: str | None = None,
        sort_field: str = "app_id",
        sort_order: str = "asc",
    ) -> tuple[list[dict[str, Any]], int]:
        return await self._repo.list_applications_filtered(
            page=page,
            page_size=page_size,
            appId=appId,
            name=name,
            projectId=projectId,
            sort_field=sort_field,
            sort_order=sort_order,
        )

    async def list_cmdb_applications_filtered(
        self, *,
        page: int = 1,
        page_size: int = 20,
        appId: str | None = None,
        name: str | None = None,
        sort_field: str = "app_id",
        sort_order: str = "asc",
    ) -> tuple[list[dict[str, Any]], int]:
        return await self._repo.list_cmdb_applications_filtered(
            page=page,
            page_size=page_size,
            appId=appId,
            name=name,
            sort_field=sort_field,
            sort_order=sort_order,
        )

    async def list_bcm_versions(self) -> list[str]:
        return await self._repo.list_bcm_versions()

    async def list_cmdb_filtered(
        self, *,
        page: int = 1,
        page_size: int = 20,
        appId: str | None = None,
        name: str | None = None,
        q: str | None = None,
        status: str | None = None,
        ownerTower: str | None = None,
        ownedBy: str | None = None,
        portfolio: str | None = None,
        classification: str | None = None,
        solutionType: str | None = None,
        serviceArea: str | None = None,
        ownership: str | None = None,
        appFullName: str | None = None,
        sort_field: str = "app_id",
        sort_order: str = "asc",
    ) -> tuple[list[dict[str, Any]], int]:
        return await self._repo.list_cmdb_filtered(
            page=page,
            page_size=page_size,
            appId=appId,
            name=name,
            q=q,
            status=status,
            ownerTower=ownerTower,
            ownedBy=ownedBy,
            portfolio=portfolio,
            classification=classification,
            solutionType=solutionType,
            serviceArea=serviceArea,
            ownership=ownership,
            appFullName=appFullName,
            sort_field=sort_field,
            sort_order=sort_order,
        )


class BizCapabilityService:
    def __init__(self, repo: BizCapabilityRepository):
        self._repo = repo

    async def list_filtered(
        self, *,
        page: int = 1,
        page_size: int = 20,
        version: str | None = None,
        domainL1: str | None = None,
        subDomainL2: str | None = None,
        capabilityGroupL3: str | None = None,
        level: str | None = None,
        sort_field: str = "bc_id",
        sort_order: str = "asc",
    ) -> tuple[list[dict[str, Any]], int]:
        return await self._repo.list_filtered(
            page=page,
            page_size=page_size,
            version=version,
            domainL1=domainL1,
            subDomainL2=subDomainL2,
            capabilityGroupL3=capabilityGroupL3,
            level=level,
            sort_field=sort_field,
            sort_order=sort_order,
        )
