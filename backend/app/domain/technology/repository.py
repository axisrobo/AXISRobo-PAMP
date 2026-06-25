from abc import abstractmethod
from app.domain.base_repository import BaseRepository
from app.domain.technology.entities import TechStackItem, LifecycleLog


class TechStackRepository(BaseRepository[TechStackItem]):
    @abstractmethod
    async def list_by_category(self, category: str) -> list[TechStackItem]: ...
    @abstractmethod
    async def check_compliance(self, item_id: str) -> dict: ...
    @abstractmethod
    async def soft_delete(self, id: str) -> bool: ...


class LifecycleLogRepository(BaseRepository[LifecycleLog]):
    @abstractmethod
    async def list_by_item(self, item_id: str) -> list[LifecycleLog]: ...
