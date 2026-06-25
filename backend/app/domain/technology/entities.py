from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(kw_only=True)
class TechStackItem:
    id: UUID = field(default_factory=uuid4)
    name: str
    category: str
    version: str = ""
    status: str = "active"
    eol_date: datetime | None = None
    security_advice: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(kw_only=True)
class LifecycleLog:
    id: UUID = field(default_factory=uuid4)
    item_id: str
    action: str
    previous_status: str = ""
    new_status: str = ""
    changed_by: str = ""
    changed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
