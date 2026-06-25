from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EmailMessage:
    to: list[str]
    subject: str
    body: str
    cc: list[str] | None = None
    is_html: bool = False


class EmailProvider(ABC):
    @abstractmethod
    async def send(self, message: EmailMessage) -> bool: ...
