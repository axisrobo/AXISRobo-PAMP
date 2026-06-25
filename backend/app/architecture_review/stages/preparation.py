"""Architecture Preparation stage routes."""

from fastapi import APIRouter

from .. import attachments as ea_attachments
from .. import artifacts, ea_requests, concerns

router = APIRouter()

router.include_router(ea_requests.router, prefix="/ea-requests", tags=["EA Requests"])
router.include_router(concerns.router, prefix="/ea-requests", tags=["EA Concerns"])
router.include_router(artifacts.router, prefix="/ea-requests", tags=["EA Artifacts"])
router.include_router(ea_attachments.router, prefix="/ea-requests/attachments", tags=["EA Attachments"])