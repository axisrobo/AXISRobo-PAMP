"""Application management module router."""
from fastapi import APIRouter

from . import applications, biz_capability, cmdb


router = APIRouter()

router.include_router(applications.router, prefix="/applications", tags=["Applications"])
router.include_router(biz_capability.router, prefix="/biz-capability", tags=["BizCapability"])
router.include_router(cmdb.router, prefix="/cmdb", tags=["CMDB"])
