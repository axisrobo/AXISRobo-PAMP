"""Architecture Review stage routes.

Review-specific confirmations and reviewer decisions currently live in the
AVDM module and request detail workflow. This router is intentionally present
as the stable boundary for future review-stage endpoints.
"""

from fastapi import APIRouter

router = APIRouter()