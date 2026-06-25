from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(kw_only=True)
class Application:
    id: UUID = field(default_factory=uuid4)
    app_id: str
    app_name: str
    description: str = ""
    owner: str = ""
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(kw_only=True)
class BCMapping:
    id: UUID = field(default_factory=uuid4)
    application_id: str
    capability_id: str
    capability_name: str = ""
    mapping_level: str = "supports"


@dataclass(kw_only=True)
class BizCapability:
    id: UUID = field(default_factory=uuid4)
    code: str
    name: str
    parent_code: str | None = None
    level: int = 1
    description: str = ""


@dataclass(kw_only=True)
class CMDBApplication:
    app_id: str
    app_name: str
    owner: str = ""
    status: str = "active"
    last_synced_at: datetime | None = None
