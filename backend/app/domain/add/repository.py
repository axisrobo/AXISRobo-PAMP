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
