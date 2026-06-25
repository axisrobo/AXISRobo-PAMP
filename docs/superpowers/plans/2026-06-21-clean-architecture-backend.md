# AxisArch Clean Architecture — Backend Refactoring Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor backend from router-directly-calls-SQL to Clean Architecture: domain/application/infrastructure/interfaces layers with plugin system.

**Architecture:** Bottom-up incremental migration per module. Keep API contract intact, all 577 passing tests must stay green. Domain layer first (zero deps), then infrastructure (DB repos), then application (services), finally thin routers. Plugin system for enterprise integrations loaded at startup.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy async, asyncpg, Pydantic v2

---

## Module Migration Order

| Phase | Module | Impact | Why First |
|-------|--------|--------|-----------|
| F1 | Shared Foundation | Base classes, DI container, plugin registry | All modules depend on this |
| F2 | ADD (avdm) | ~643 lines | Smallest module, good template |
| F3 | Project Management | ~200 lines | Simple CRUD, quick win |
| F4 | Data Management | ~443 lines | Moderate complexity |
| F5 | Application Portfolio | ~758 lines | Medium complexity |
| F6 | Technology Stack | ~400 lines | Medium complexity |
| F7 | EA Review | ~2,622 lines | Largest, saved for last (most learning accumulated) |

---

### Task F1-1: Domain Base Classes

**Files:**
- Create: `backend/app/domain/__init__.py`
- Create: `backend/app/domain/base_entity.py`
- Create: `backend/app/domain/base_repository.py`
- Test: `backend/tests/domain/test_base_entity.py`

- [ ] **Step 1: Write BaseEntity**

```python
# backend/app/domain/base_entity.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

@dataclass(kw_only=True)
class BaseEntity:
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
```

- [ ] **Step 2: Write BaseRepository abstract**

```python
# backend/app/domain/base_repository.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional

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
```

- [ ] **Step 3: Write base entity test**

```python
# backend/tests/domain/test_base_entity.py
from uuid import UUID
from backend.app.domain.base_entity import BaseEntity

def test_base_entity_auto_generates_id():
    entity = BaseEntity()
    assert isinstance(entity.id, UUID)

def test_base_entity_auto_generates_timestamps():
    entity = BaseEntity()
    assert entity.created_at is not None
    assert entity.updated_at is not None
```

- [ ] **Step 4: Run tests**

```powershell
cd backend; .\venv\Scripts\python.exe -m pytest tests/domain/test_base_entity.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/domain/ tests/domain/
git commit -m "feat(domain): add BaseEntity and BaseRepository abstract base classes"
```

---

### Task F1-2: Plugin Registry + DI Container

**Files:**
- Create: `backend/app/plugins/__init__.py`
- Create: `backend/app/infrastructure/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create plugin registry**

```python
# backend/app/plugins/__init__.py
"""Enterprise integration plugins. Loaded at startup based on configuration."""
from __future__ import annotations
from typing import Any

class PluginRegistry:
    def __init__(self):
        self._providers: dict[str, Any] = {}

    def register(self, name: str, provider: Any) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> Any | None:
        return self._providers.get(name)

    def get_or_default(self, name: str, default: Any) -> Any:
        return self._providers.get(name, default)

# Singleton
plugin_registry = PluginRegistry()
```

- [ ] **Step 2: Create infrastructure init**

```python
# backend/app/infrastructure/__init__.py
"""Infrastructure layer — database, storage, email, auth adapters."""
```

- [ ] **Step 3: Wire plugin registry into main.py lifespan**

In `backend/app/main.py`, add to the lifespan function:

```python
from app.plugins import plugin_registry

# Inside lifespan startup:
logger.info(f"Enabled API modules: {sorted(enabled_module_keys)}")

# Initialize plugins based on settings
from app.config import settings as _cfg
if _cfg.CMDB_API_URL:
    logger.info("CMDB sync plugin configured")
if _cfg.EMAIL_SERVICE_URL:
    logger.info("Email plugin configured")
# Future: plugin_registry.register("email", BCTEmailProvider(settings))
```

- [ ] **Step 4: Verify import**

```powershell
cd backend; .\venv\Scripts\python.exe -c "from app.main import app; print('OK')"
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/plugins/ backend/app/infrastructure/ backend/app/main.py
git commit -m "feat(core): add PluginRegistry and infrastructure layer scaffolding"
```

---

### Task F1-3: Auth Provider Abstraction

**Files:**
- Create: `backend/app/infrastructure/auth/__init__.py`
- Create: `backend/app/infrastructure/auth/provider.py`
- Modify: `backend/app/auth/providers.py`
- Create: `backend/app/plugins/auth/__init__.py`

- [ ] **Step 1: Define AuthProvider abstract interface**

```python
# backend/app/infrastructure/auth/provider.py
from abc import ABC, abstractmethod
from app.auth.models import AuthUser

class AuthProvider(ABC):
    @abstractmethod
    async def authenticate(self, token: str) -> AuthUser | None: ...
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> dict | None: ...
```

- [ ] **Step 2: Make DevAuthProvider implement AuthProvider**

In `backend/app/auth/providers.py`, add `AuthProvider` as base class:

```python
from app.infrastructure.auth.provider import AuthProvider

class DevAuthProvider(AuthProvider):
    async def authenticate(self, token: str) -> AuthUser | None:
        # existing logic
        ...
    async def refresh_token(self, refresh_token: str) -> dict | None:
        return None
```

- [ ] **Step 3: Make KeycloakAuthProvider implement AuthProvider**

Similarly make `KeycloakAuthProvider` inherit from `AuthProvider`.

- [ ] **Step 4: Create plugins/auth init**

```python
# backend/app/plugins/auth/__init__.py
"""Authentication provider plugins."""
```

- [ ] **Step 5: Verify tests still pass**

```powershell
cd backend; .\venv\Scripts\python.exe -m pytest tests/auth/ -v --tb=short
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/infrastructure/auth/ backend/app/auth/providers.py backend/app/plugins/auth/
git commit -m "feat(auth): extract AuthProvider abstract interface"
```

---

### Task F1-4: Storage Provider Abstraction

**Files:**
- Create: `backend/app/infrastructure/storage/__init__.py`
- Create: `backend/app/infrastructure/storage/provider.py`
- Modify: `backend/app/utils/s3_storage.py`
- Create: `backend/app/plugins/storage/__init__.py`

- [ ] **Step 1: Define StorageProvider abstract**

```python
# backend/app/infrastructure/storage/provider.py
from abc import ABC, abstractmethod
from typing import BinaryIO

class StorageProvider(ABC):
    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str: ...
    @abstractmethod
    async def download(self, key: str) -> bytes: ...
    @abstractmethod
    async def delete(self, key: str) -> bool: ...
    @abstractmethod
    async def presign_url(self, key: str, expires_in: int = 3600) -> str: ...
```

- [ ] **Step 2: Make S3 storage implement StorageProvider**

In `backend/app/utils/s3_storage.py`, add `StorageProvider` as base:

```python
from app.infrastructure.storage.provider import StorageProvider

class S3Storage(StorageProvider):
    ...
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/infrastructure/storage/ backend/app/utils/s3_storage.py backend/app/plugins/storage/
git commit -m "feat(storage): extract StorageProvider abstract interface"
```

---

### Task F1-5: Email Provider Abstraction

**Files:**
- Create: `backend/app/infrastructure/email/__init__.py`
- Create: `backend/app/infrastructure/email/provider.py`
- Modify: `backend/app/utils/email_service.py`
- Create: `backend/app/plugins/email/__init__.py`

- [ ] **Step 1: Define EmailProvider abstract**

```python
# backend/app/infrastructure/email/provider.py
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
```

- [ ] **Step 2: Create concrete SMTP provider (stub)**

```python
# backend/app/infrastructure/email/smtp_provider.py
import logging
from app.infrastructure.email.provider import EmailProvider, EmailMessage

logger = logging.getLogger(__name__)

class SMTPEmailProvider(EmailProvider):
    async def send(self, message: EmailMessage) -> bool:
        logger.info(f"[STUB] Would send email to {message.to}: {message.subject}")
        return True
```

- [ ] **Step 3: Wire existing email service to EmailProvider pattern**

In `backend/app/utils/email_service.py`, add a factory:

```python
from app.config import settings
from app.infrastructure.email.provider import EmailProvider
from app.infrastructure.email.smtp_provider import SMTPEmailProvider

def create_email_provider() -> EmailProvider:
    if settings.EMAIL_SERVICE_URL:
        # Return BCT or custom provider
        return SMTPEmailProvider()  # placeholder
    return SMTPEmailProvider()
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/infrastructure/email/ backend/app/utils/email_service.py backend/app/plugins/email/
git commit -m "feat(email): extract EmailProvider abstract interface with SMTP stub"
```

---

### Task F2-1: ADD Domain Entities

**Files:**
- Create: `backend/app/domain/add/__init__.py`
- Create: `backend/app/domain/add/entities.py`
- Create: `backend/app/domain/add/repository.py`
- Test: `backend/tests/domain/add/test_add_domain.py`

- [ ] **Step 1: Extract ADD entities from existing avdm/models.py**

Read `backend/app/avdm/models.py` to understand the key entities. Create domain entities:

```python
# backend/app/domain/add/entities.py
from dataclasses import dataclass, field
from datetime import datetime
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
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class ProjectAssessment:
    id: UUID = field(default_factory=uuid4)
    project_id: str
    concern_id: str
    score: int = 0
    notes: str = ""
    assessed_by: str = ""
    assessed_at: datetime = field(default_factory=datetime.utcnow)

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
```

- [ ] **Step 2: Define ADD repository interface**

```python
# backend/app/domain/add/repository.py
from abc import abstractmethod
from typing import Optional
from app.domain.base_repository import BaseRepository
from app.domain.add.entities import Concern, QuestionnaireConfig, ProjectAssessment, Viewpoint, Artifact

class ConcernRepository(BaseRepository[Concern]):
    @abstractmethod
    async def list_by_category(self, category: str) -> list[Concern]: ...

class AssessmentRepository(BaseRepository[ProjectAssessment]):
    @abstractmethod
    async def list_by_project(self, project_id: str) -> list[ProjectAssessment]: ...
    @abstractmethod
    async def get_recommendations(self, project_id: str) -> list[dict]: ...

class ViewpointRepository(BaseRepository[Viewpoint]):
    @abstractmethod
    async def list_all(self) -> list[Viewpoint]: ...

class ArtifactRepository(BaseRepository[Artifact]):
    @abstractmethod
    async def list_by_viewpoint(self, viewpoint_code: str) -> list[Artifact]: ...

class QuestionnaireConfigRepository(BaseRepository[QuestionnaireConfig]):
    @abstractmethod
    async def get_current(self) -> Optional[QuestionnaireConfig]: ...
    @abstractmethod
    async def update_current(self, config: QuestionnaireConfig) -> QuestionnaireConfig: ...
```

- [ ] **Step 3: Write domain tests**

```python
# backend/tests/domain/add/test_add_domain.py
from backend.app.domain.add.entities import Concern, ProjectAssessment

def test_concern_creation():
    concern = Concern(code="C001", name="Security Review", category="security", severity="high")
    assert concern.code == "C001"
    assert concern.severity == "high"

def test_project_assessment_defaults():
    assessment = ProjectAssessment(project_id="proj-1", concern_id="C001")
    assert assessment.score == 0
    assert assessment.notes == ""
```

- [ ] **Step 4: Run tests**

```powershell
cd backend; .\venv\Scripts\python.exe -m pytest tests/domain/add/ -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/domain/add/ tests/domain/add/
git commit -m "feat(domain): add ADD domain entities and repository interfaces"
```

---

### Task F2-2: ADD Infrastructure (Database Repository)

**Files:**
- Create: `backend/app/infrastructure/database/repositories/__init__.py`
- Create: `backend/app/infrastructure/database/repositories/add_repo.py`
- Test: `backend/tests/infrastructure/test_add_repo.py`

- [ ] **Step 1: Read existing avdm/repository.py to understand SQL queries**

The existing `backend/app/avdm/repository.py` contains the raw SQL. We'll wrap it.

- [ ] **Step 2: Implement ConcernRepository**

```python
# backend/app/infrastructure/database/repositories/add_repo.py
from __future__ import annotations
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.add.repository import ConcernRepository, AssessmentRepository, ViewpointRepository, ArtifactRepository, QuestionnaireConfigRepository
from app.domain.add.entities import Concern, ProjectAssessment, Viewpoint, Artifact, QuestionnaireConfig
from app.database import get_session

class PostgresConcernRepository(ConcernRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: str) -> Optional[Concern]:
        result = await self._session.execute(
            text("SELECT id, code, name, category, description, severity, likelihood, classification FROM eam_concern WHERE id = :id"),
            {"id": id}
        )
        row = result.fetchone()
        return self._to_entity(row) if row else None

    async def list(self, page: int = 1, page_size: int = 20) -> tuple[list[Concern], int]:
        count_result = await self._session.execute(text("SELECT COUNT(*) FROM eam_concern"))
        total = count_result.scalar()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            text("SELECT id, code, name, category, description, severity, likelihood, classification FROM eam_concern ORDER BY code LIMIT :limit OFFSET :offset"),
            {"limit": page_size, "offset": offset}
        )
        items = [self._to_entity(row) for row in result.fetchall()]
        return items, total

    async def list_by_category(self, category: str) -> list[Concern]:
        result = await self._session.execute(
            text("SELECT id, code, name, category, description, severity, likelihood, classification FROM eam_concern WHERE category = :category ORDER BY code"),
            {"category": category}
        )
        return [self._to_entity(row) for row in result.fetchall()]

    async def create(self, entity: Concern) -> Concern:
        await self._session.execute(
            text("INSERT INTO eam_concern (id, code, name, category, description, severity, likelihood, classification) VALUES (:id, :code, :name, :category, :description, :severity, :likelihood, :classification)"),
            self._to_params(entity)
        )
        return entity

    async def update(self, entity: Concern) -> Concern:
        await self._session.execute(
            text("UPDATE eam_concern SET name=:name, category=:category, description=:description, severity=:severity, likelihood=:likelihood, classification=:classification WHERE id=:id"),
            self._to_params(entity)
        )
        return entity

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(text("DELETE FROM eam_concern WHERE id = :id"), {"id": id})
        return result.rowcount > 0

    @staticmethod
    def _to_entity(row) -> Concern:
        return Concern(id=str(row[0]), code=row[1], name=row[2], category=row[3], description=row[4] or "", severity=row[5] or "medium", likelihood=row[6] or "medium", classification=row[7] or "recommended")

    @staticmethod
    def _to_params(entity: Concern) -> dict:
        return {"id": str(entity.id), "code": entity.code, "name": entity.name, "category": entity.category, "description": entity.description, "severity": entity.severity, "likelihood": entity.likelihood, "classification": entity.classification}
```

- [ ] **Step 3: Run tests (requires DB)**

```powershell
cd backend; .\venv\Scripts\python.exe -m pytest tests/infrastructure/test_add_repo.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/infrastructure/database/repositories/ tests/infrastructure/
git commit -m "feat(infra): add PostgresConcernRepository for ADD module"
```

---

### Task F2-3: ADD Application Service

**Files:**
- Create: `backend/app/application/add/__init__.py`
- Create: `backend/app/application/add/dto.py`
- Create: `backend/app/application/add/services.py`

- [ ] **Step 1: Define DTOs**

```python
# backend/app/application/add/dto.py
from dataclasses import dataclass

@dataclass
class ConcernDTO:
    code: str
    name: str
    category: str
    description: str = ""
    severity: str = "medium"
    likelihood: str = "medium"
    classification: str = "recommended"

@dataclass
class AssessmentDTO:
    project_id: str
    concern_id: str
    score: int = 0
    notes: str = ""
    assessed_by: str = ""

@dataclass
class AssessmentResultDTO:
    concern_code: str
    concern_name: str
    score: int
    classification: str
    recommendation: str
```

- [ ] **Step 2: Implement ConcernService**

```python
# backend/app/application/add/services.py
from app.domain.add.repository import ConcernRepository, AssessmentRepository
from app.application.add.dto import ConcernDTO, AssessmentDTO, AssessmentResultDTO

class ConcernService:
    def __init__(self, repo: ConcernRepository):
        self._repo = repo

    async def list_concerns(self, page: int = 1, page_size: int = 20):
        return await self._repo.list(page, page_size)

    async def list_by_category(self, category: str):
        return await self._repo.list_by_category(category)

    async def create_concern(self, dto: ConcernDTO):
        from app.domain.add.entities import Concern
        entity = Concern(code=dto.code, name=dto.name, category=dto.category, description=dto.description, severity=dto.severity, likelihood=dto.likelihood, classification=dto.classification)
        return await self._repo.create(entity)

class AssessmentService:
    def __init__(self, repo: AssessmentRepository):
        self._repo = repo

    async def create_assessment(self, dto: AssessmentDTO):
        from app.domain.add.entities import ProjectAssessment
        entity = ProjectAssessment(project_id=dto.project_id, concern_id=dto.concern_id, score=dto.score, notes=dto.notes, assessed_by=dto.assessed_by)
        return await self._repo.create(entity)

    async def get_recommendations(self, project_id: str):
        return await self._repo.get_recommendations(project_id)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/application/add/
git commit -m "feat(app): add ADD application service layer with DTOs"
```

---

### Task F2-4: ADD Thin Router (Refactor)

**Files:**
- Modify: `backend/app/avdm/routes.py` → delegate to services

- [ ] **Step 1: Rewrite ADD routes to use services**

Refactor `backend/app/avdm/routes.py` key endpoints:

```python
# Inside GET /api/add/concerns handler:
concern_repo = PostgresConcernRepository(session)
concern_service = ConcernService(concern_repo)
items, total = await concern_service.list_concerns(page, page_size)
```

- [ ] **Step 2: Verify all existing ADD tests pass**

```powershell
cd backend; .\venv\Scripts\python.exe -m pytest tests/ --test-ignore=tests/routers/test_team_members.py --test-ignore=tests/utils/test_csv_export.py -k "avdm or add" -v --tb=short
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/avdm/routes.py
git commit -m "refactor(add): delegate ADD router to application services"
```

---

### Task F3-F7: Remaining Modules (Pattern Replication)

The remaining modules follow the same 4-step pattern established by ADD:

1. **Domain**: Extract entities + repository interfaces
2. **Infrastructure**: Implement database repositories
3. **Application**: Create DTOs + services
4. **Interfaces**: Thin router delegating to services

**Module-specific notes:**

| Module | Key Entities | Repository Methods | Complexity |
|--------|-------------|-------------------|------------|
| Project | Project, TeamMember | CRUD + list_by_owner | Low |
| Data Mgmt | MasterDataEntry, Resource, Certification | CRUD + search + soft delete | Medium |
| App Portfolio | Application, BCMapping, BizCapability, CMDBApp | CRUD + visualisation + sync | Medium |
| Tech Stack | TechStackItem, LifecycleLog | CRUD + lifecycle + compliance | Medium |
| EA Review | ReviewRequest, Meeting, Action, Attachment | Full workflow + dashboard aggregation | High |

**Gateway Principle:** Never remove the old router module. Add new domain/app/infra code alongside, then refactor the router to use services. Old SQL in routers stays until services are fully wired.

---

### Task F8: Plugin System Wiring

**Files:**
- Modify: `backend/app/main.py` → plugin loading in lifespan

- [ ] **Step 1: Wire plugins at startup**

```python
# In backend/app/main.py lifespan:
from app.plugins import plugin_registry
from app.config import settings as _cfg

# Auth provider
if _cfg.AUTH_DISABLED:
    from app.auth.providers import DevAuthProvider
    plugin_registry.register("auth", DevAuthProvider(_cfg))
elif _cfg.KEYCLOAK_SERVER_URL:
    from app.auth.providers import KeycloakAuthProvider
    plugin_registry.register("auth", KeycloakAuthProvider(_cfg))

# Storage provider
if _cfg.S3_ENDPOINT:
    from app.utils.s3_storage import S3Storage
    plugin_registry.register("storage", S3Storage(_cfg))

# Email provider
from app.utils.email_service import create_email_provider
plugin_registry.register("email", create_email_provider())
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/main.py
git commit -m "feat(plugins): wire provider plugins at startup lifespan"
```

---

## Verification

After all tasks complete:

```powershell
cd backend; .\venv\Scripts\python.exe -m pytest tests/ -v --tb=short
```

Expected: Same 577 passing as before refactoring (or better). No regression.

```powershell
cd backend; .\venv\Scripts\python.exe -c "from app.main import app; print(f'OK: {app.title}')"
```

Expected: `OK: AxisArch API`

---

## Summary

| Phase | Tasks | New Files | Modified Files |
|-------|-------|-----------|----------------|
| F1: Foundation | 5 | ~10 | ~5 |
| F2: ADD Module | 4 | ~8 | ~3 |
| F3-F7: Remaining | 5 | ~30 | ~10 |
| F8: Plugin Wiring | 1 | 0 | 1 |
| **Total** | **15** | **~48** | **~19** |
