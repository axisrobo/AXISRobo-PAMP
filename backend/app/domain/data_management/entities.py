from dataclasses import dataclass, field
from datetime import datetime, date, timezone
from uuid import UUID, uuid4


@dataclass(kw_only=True)
class MasterDataEntry:
    id: UUID = field(default_factory=uuid4)
    data_type: str
    code: str
    name: str
    description: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(kw_only=True)
class Certification:
    id: UUID = field(default_factory=uuid4)
    person_itcode: str
    cert_type: str
    cert_name: str
    issue_date: date | None = None
    expiry_date: date | None = None
    status: str = "active"


@dataclass(kw_only=True)
class Resource:
    id: UUID = field(default_factory=uuid4)
    name: str
    resource_type: str
    description: str = ""
    is_available: bool = True
