from abc import abstractmethod
from app.domain.base_repository import BaseRepository
from app.domain.application.entities import Application, BCMapping, BizCapability, CMDBApplication


class ApplicationRepository(BaseRepository[Application]):
    @abstractmethod
    async def list_by_app_id(self, app_id: str) -> list[Application]: ...


class BCMappingRepository(BaseRepository[BCMapping]):
    @abstractmethod
    async def list_by_application(self, application_id: str) -> list[BCMapping]: ...
    @abstractmethod
    async def list_by_capability(self, capability_id: str) -> list[BCMapping]: ...


class BizCapabilityRepository(BaseRepository[BizCapability]):
    @abstractmethod
    async def list_by_parent(self, parent_code: str | None) -> list[BizCapability]: ...
    @abstractmethod
    async def get_tree(self) -> list[dict]: ...


class CMDBApplicationRepository(BaseRepository[CMDBApplication]):
    @abstractmethod
    async def upsert_from_cmdb(self, apps: list[CMDBApplication]) -> int: ...
