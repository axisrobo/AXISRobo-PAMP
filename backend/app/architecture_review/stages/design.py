"""Architecture Design stage routes."""

from fastapi import APIRouter

from .. import architecture_check
from .. import architecture_check_interactions

router = APIRouter()

router.include_router(architecture_check.router, prefix="/arch-check-apps", tags=["Architecture Check"])
router.include_router(
    architecture_check_interactions.router,
    prefix="/arch-check-interactions",
    tags=["Architecture Check Interactions"],
)