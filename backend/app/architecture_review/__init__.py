"""Architecture review domain router."""
from fastapi import APIRouter

from . import actions, ea_review_logs, export, meetings, reports
from .stages import design, execution_operations, preparation, review


router = APIRouter()

router.include_router(actions.router, prefix="/actions", tags=["Actions"])
router.include_router(ea_review_logs.router, prefix="/ea-review-logs", tags=["EA Review Logs"])
router.include_router(export.router, prefix="/export", tags=["Export"])
router.include_router(meetings.router, prefix="/meetings", tags=["Meetings"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
router.include_router(preparation.router)
router.include_router(design.router)
router.include_router(review.router)
router.include_router(execution_operations.router)
