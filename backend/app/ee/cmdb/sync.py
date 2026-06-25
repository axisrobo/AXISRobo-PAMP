"""CMDB Application Synchronization Task."""
import logging
from typing import Any, List, Dict
from datetime import datetime
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.config import settings
from app.database import AsyncSessionLocal

logger = logging.getLogger("eam.tasks.cmdb_sync")


def _get_app_columns() -> List[Dict[str, Any]]:
    """Return the list of columns to be fetched and their mapping."""
    return [
        {"column": "_id", "label": "ID", "show": 1},
        {"column": "patch_level", "label": "Application Unified ID", "show": 1},
        {"column": "name", "label": "Application Name", "show": 1},
        {"column": "app_full_name", "label": "Application Full Name", "show": 1},
        {"column": "u_status", "label": "Current State", "show": 1},
        {"column": "short_description", "label": "Description", "show": 1},
        {"column": "owned_by", "label": "Application IT Owner", "show": 1},
        {"column": "u_service_area", "label": "Function (Value Chain)", "show": 1},
        {"column": "appowner_orgname", "label": "Application Owner Tower", "show": 1},
        {"column": "functionOwnerL4OrgName", "label": "Application Owner Domain", "show": 1},
        {"column": "appPortfolioMgt", "label": "Application Portfolio Management", "show": 1},
        {"column": "appClassification", "label": "Application Classification", "show": 1},
        {"column": "applicationSolutionType", "label": "Application Solution Type", "show": 1},
        {"column": "u_budget_owner", "label": "Application Ownership", "show": 1},
        {"column": "app_operation_owner", "label": "App Operation Owner", "show": 1},
        {"column": "AppOperationOwnerTower", "label": "App Operation Owner Tower", "show": 1},
        {"column": "AppOperationOwnerDomain", "label": "App Operation Owner Domain", "show": 1},
        {"column": "appDtOwner", "label": "Application DT Owner", "show": 1},
        {"column": "registerPhase", "label": "Registration & Certification Status", "show": 1},
    ]


async def fetch_cmdb_page(client: httpx.AsyncClient, page: int, size: int) -> Dict[str, Any]:
    """Fetch a single page of applications from CMDB."""
    payload = {
        "conditions": [],
        "showColumns": _get_app_columns()
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": settings.CMDB_API_TOKEN
    }
    url = f"{settings.CMDB_API_URL}?page={page}&size={size}"
    
    response = await client.post(url, json=payload, headers=headers, timeout=60.0)
    response.raise_for_status()
    data = response.json()
    if not data.get("success"):
        raise Exception(f"CMDB API Error: {data.get('message')}")
    return data.get("data", {})


def _format_classification(val: Any) -> str:
    """Convert array-like classification to comma-separated string."""
    if isinstance(val, list):
        return ",".join(str(i) for i in val)
    return str(val) if val is not None else ""


async def sync_cmdb_applications():
    """Daily synchronization task for CMDB applications."""
    logger.info("Starting CMDB Application sync...")
    page = 1
    size = 100
    total_processed = 0
    
    async with httpx.AsyncClient(verify=False) as client:
        try:
            # First fetch to get total elements
            data = await fetch_cmdb_page(client, page, size)
            total_elements = data.get("pageResult", {}).get("page", {}).get("totalElements", 0)
            logger.info(f"Total applications to sync: {total_elements}")
            
            while total_processed < total_elements:
                if page > 1:
                    data = await fetch_cmdb_page(client, page, size)
                
                rows = data.get("pageResult", {}).get("rows", [])
                if not rows:
                    break
                
                await _upsert_rows(rows)
                
                total_processed += len(rows)
                logger.info(f"Processed {total_processed}/{total_elements} applications")
                page += 1
                
            logger.info("CMDB Application sync completed successfully.")
        except Exception as e:
            logger.error(f"CMDB sync failed: {e}", exc_info=True)
            raise


async def _upsert_rows(rows: List[Dict[str, Any]]):
    """Batch upsert application rows into the database."""
    now = datetime.now()
    async with AsyncSessionLocal() as db:
        for row in rows:
            # Prepare data according to mapping in spec
            app_id = row.get("patch_level")
            if not app_id:
                continue
                
            u_status = row.get("u_status", "")
            
            # Basic transformation logic
            # decommissioned_at logic: if status becomes Decommissioned, set to now
            # In a real sync, we might want to check the previous status, but here we'll 
            # just set it if current is Decommissioned.
            decommissioned_at = None
            if u_status == "Decommissioned":
                decommissioned_at = now

            params = {
                "p_id": row.get("_id"),
                "p_short_description": row.get("short_description"),
                "p_u_service_area": row.get("u_service_area"),
                "p_u_status": u_status,
                "p_app_full_name": row.get("app_full_name"),
                "p_owned_by": row.get("owned_by"),
                "p_name": row.get("name"),
                "p_app_it_owner": row.get("owned_by"),  # Mapping from spec
                "p_app_owner_tower": row.get("appowner_orgname"),
                "p_app_owner_domain": row.get("functionOwnerL4OrgName"),
                "p_app_id": app_id,
                "p_patch_level": app_id,
                "p_portfolio_mgt": row.get("appPortfolioMgt"),
                "p_app_classification": _format_classification(row.get("appClassification")),
                "p_app_ownership": row.get("u_budget_owner"),
                "p_app_solution_type": row.get("applicationSolutionType"),
                "p_app_operation_owner": row.get("app_operation_owner"),
                "p_app_operation_owner_tower": row.get("AppOperationOwnerTower"),
                "p_app_operation_owner_domain": row.get("AppOperationOwnerDomain"),
                "p_app_dt_owner": row.get("appDtOwner"),
                "p_update_at": now,
                "p_decommissioned_at": decommissioned_at
            }
            
            # UPSERT query
            query = text("""
                INSERT INTO eam.cmdb_application (
                    _id, short_description, u_service_area, u_status, app_full_name,
                    owned_by, "name", app_it_owner, app_owner_tower, app_owner_domain,
                    app_id, patch_level, portfolio_mgt, app_classification,
                    update_at, app_ownership, app_solution_type, app_operation_owner,
                    app_operation_owner_tower, app_operation_owner_domain,
                    decommissioned_at, app_dt_owner
                ) VALUES (
                    :p_id, :p_short_description, :p_u_service_area, :p_u_status, :p_app_full_name,
                    :p_owned_by, :p_name, :p_app_it_owner, :p_app_owner_tower, :p_app_owner_domain,
                    :p_app_id, :p_patch_level, :p_portfolio_mgt, :p_app_classification,
                    :p_update_at, :p_app_ownership, :p_app_solution_type, :p_app_operation_owner,
                    :p_app_operation_owner_tower, :p_app_operation_owner_domain,
                    :p_decommissioned_at, :p_app_dt_owner
                ) ON CONFLICT (app_id) DO UPDATE SET
                    _id = EXCLUDED._id,
                    short_description = EXCLUDED.short_description,
                    u_service_area = EXCLUDED.u_service_area,
                    u_status = EXCLUDED.u_status,
                    app_full_name = EXCLUDED.app_full_name,
                    owned_by = EXCLUDED.owned_by,
                    "name" = EXCLUDED."name",
                    app_it_owner = EXCLUDED.app_it_owner,
                    app_owner_tower = EXCLUDED.app_owner_tower,
                    app_owner_domain = EXCLUDED.app_owner_domain,
                    patch_level = EXCLUDED.patch_level,
                    portfolio_mgt = EXCLUDED.portfolio_mgt,
                    app_classification = EXCLUDED.app_classification,
                    update_at = EXCLUDED.update_at,
                    app_ownership = EXCLUDED.app_ownership,
                    app_solution_type = EXCLUDED.app_solution_type,
                    app_operation_owner = EXCLUDED.app_operation_owner,
                    app_operation_owner_tower = EXCLUDED.app_operation_owner_tower,
                    app_operation_owner_domain = EXCLUDED.app_operation_owner_domain,
                    decommissioned_at = COALESCE(EXCLUDED.decommissioned_at, eam.cmdb_application.decommissioned_at),
                    app_dt_owner = EXCLUDED.app_dt_owner
            """)
            await db.execute(query, params)
        await db.commit()
