"""Project management module router."""
from fastapi import APIRouter

from . import projects
from . import team_members


router = APIRouter()

router.include_router(projects.router, prefix="/projects", tags=["Projects"])
router.include_router(team_members.router, prefix="/team-members", tags=["Team Members"])
