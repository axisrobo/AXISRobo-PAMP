"""Technology stack management module router."""
from fastapi import APIRouter

from . import technology_stack


router = APIRouter()

router.include_router(technology_stack.router, prefix="/technology-stack", tags=["Technology Stack"])
