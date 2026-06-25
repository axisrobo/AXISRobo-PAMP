from abc import abstractmethod
from app.domain.base_repository import BaseRepository
from app.domain.data_management.entities import MasterDataEntry, Certification, Resource


class MasterDataRepository(BaseRepository[MasterDataEntry]):
    @abstractmethod
    async def search(self, query: str) -> list[MasterDataEntry]: ...
    @abstractmethod
    async def list_by_type(self, data_type: str) -> list[MasterDataEntry]: ...


class CertificationRepository(BaseRepository[Certification]):
    @abstractmethod
    async def list_by_person(self, itcode: str) -> list[Certification]: ...
    @abstractmethod
    async def list_expiring_soon(self, days: int = 30) -> list[Certification]: ...


class ResourceRepository(BaseRepository[Resource]):
    @abstractmethod
    async def list_by_type(self, resource_type: str) -> list[Resource]: ...
