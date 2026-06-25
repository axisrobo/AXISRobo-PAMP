from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

T = TypeVar("T")

class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]: ...
    @abstractmethod
    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[T], int]: ...
    @abstractmethod
    async def create(self, entity: T) -> T: ...
    @abstractmethod
    async def update(self, entity: T) -> T: ...
    @abstractmethod
    async def delete(self, id: str) -> bool: ...
