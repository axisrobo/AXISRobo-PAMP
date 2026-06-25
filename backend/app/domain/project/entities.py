from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(kw_only=True)
class Project:
    id: UUID = field(default_factory=uuid4)
    project_id: str = ""
    name: str
    description: str = ""
    status: str = "active"
    owner_id: str = ""
    category: str = "regular"
    type: str = ""
    start_date: str = ""
    go_live_date: str = ""
    duration: str = ""
    objectives: str = ""
    ai_related: str = ""
    comment: str = ""
    pm: str = ""
    pm_itcode: str = ""
    dt_lead: str = ""
    dt_lead_itcode: str = ""
    it_lead: str = ""
    it_lead_itcode: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(kw_only=True)
class TeamMember:
    id: UUID = field(default_factory=uuid4)
    project_id: str
    user_itcode: str
    role: str = "member"
