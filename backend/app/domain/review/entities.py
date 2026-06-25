from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(kw_only=True)
class ReviewRequest:
    id: UUID = field(default_factory=uuid4)
    request_id: str
    title: str
    description: str = ""
    status: str = "draft"
    submitter: str = ""
    reviewer: str = ""
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(kw_only=True)
class Meeting:
    id: UUID = field(default_factory=uuid4)
    request_id: str
    title: str
    meeting_date: datetime | None = None
    location: str = ""
    attendees: str = ""
    minutes: str = ""
    status: str = "scheduled"


@dataclass(kw_only=True)
class Action:
    id: UUID = field(default_factory=uuid4)
    request_id: str
    meeting_id: str = ""
    description: str
    assignee: str = ""
    due_date: datetime | None = None
    status: str = "open"


@dataclass(kw_only=True)
class Attachment:
    id: UUID = field(default_factory=uuid4)
    request_id: str
    filename: str
    content_type: str = "application/octet-stream"
    s3_key: str = ""
    size_bytes: int = 0
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
