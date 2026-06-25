from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(kw_only=True)
class Concern:
    id: UUID = field(default_factory=uuid4)
    code: str
    name: str
    category: str
    description: str = ""
    severity: str = "medium"
    likelihood: str = "medium"
    classification: str = "recommended"


@dataclass(kw_only=True)
class QuestionnaireConfig:
    id: UUID = field(default_factory=uuid4)
    sections: list[dict] = field(default_factory=list)
    version: int = 1
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(kw_only=True)
class ProjectAssessment:
    id: UUID = field(default_factory=uuid4)
    project_id: str
    concern_id: str
    score: int = 0
    notes: str = ""
    assessed_by: str = ""
    assessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(kw_only=True)
class Viewpoint:
    code: str
    name: str
    description: str = ""


@dataclass(kw_only=True)
class Artifact:
    code: str
    name: str
    viewpoint_code: str
    description: str = ""
