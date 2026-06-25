"""Execution and Operations stage routes.

Operational artifact submission and run-state endpoints can be registered here
without mixing them back into preparation or design route modules.
"""

from fastapi import APIRouter

router = APIRouter()