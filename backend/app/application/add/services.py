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
        entity = Concern(
            code=dto.code,
            name=dto.name,
            category=dto.category,
            description=dto.description,
            severity=dto.severity,
            likelihood=dto.likelihood,
            classification=dto.classification
        )
        return await self._repo.create(entity)


class AssessmentService:
    def __init__(self, repo: AssessmentRepository):
        self._repo = repo

    async def create_assessment(self, dto: AssessmentDTO):
        from app.domain.add.entities import ProjectAssessment
        entity = ProjectAssessment(
            project_id=dto.project_id,
            concern_id=dto.concern_id,
            score=dto.score,
            notes=dto.notes,
            assessed_by=dto.assessed_by
        )
        return await self._repo.create(entity)

    async def get_recommendations(self, project_id: str):
        return await self._repo.get_recommendations(project_id)
