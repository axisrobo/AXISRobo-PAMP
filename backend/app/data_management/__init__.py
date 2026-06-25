"""Data management module router."""
from fastapi import APIRouter

from . import master_data, resources


router = APIRouter()

router.include_router(master_data.router, prefix="/master-data", tags=["Master Data"])
router.include_router(resources.router, prefix="/resources", tags=["Resources"])
