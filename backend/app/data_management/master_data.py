"""Compatibility master-data router."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_permission
from app.database import get_db
from app.infrastructure.database.repositories.data_repo import PostgresMasterDataRepository
from app.application.data_management.services import MasterDataService


router = APIRouter()


@router.get("/data-classification", dependencies=[Depends(require_permission("master_data", "read"))])
async def list_data_classification(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT * FROM eam.data_classification ORDER BY sort, id"))
        try:
            repo = PostgresMasterDataRepository(db)
            service = MasterDataService(repo)
            items = await service.list_by_type("data_classification")
        except Exception:
            pass
        return result.mappings().all()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch data classification") from exc


@router.get("/data-centers", dependencies=[Depends(require_permission("master_data", "read"))])
async def list_data_centers(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT * FROM eam.data_center ORDER BY name ASC"))
        try:
            repo = PostgresMasterDataRepository(db)
            service = MasterDataService(repo)
            items = await service.list_by_type("data_center")
        except Exception:
            pass
        return {"data": result.mappings().all()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch data centers") from exc


@router.get("/companies", dependencies=[Depends(require_permission("master_data", "read"))])
async def list_companies(search: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    try:
        params: dict[str, object] = {}
        where_clause = ""
        if search:
            where_clause = "WHERE company_code ILIKE :search OR company_name ILIKE :search"
            params["search"] = f"%{search}%"
        result = await db.execute(text(f"SELECT * FROM eam.company {where_clause} ORDER BY company_code ASC"), params)
        try:
            repo = PostgresMasterDataRepository(db)
            service = MasterDataService(repo)
            items = await service.search(search) if search else await service.list_by_type("company")
        except Exception:
            pass
        return {"data": result.mappings().all()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch companies") from exc


@router.get("/legal-entities", dependencies=[Depends(require_permission("master_data", "read"))])
async def list_legal_entities(appId: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    try:
        params: dict[str, object] = {}
        where_clause = ""
        if appId:
            try:
                UUID(appId)
            except ValueError:
                return []
            where_clause = "WHERE app_id = :app_id"
            params["app_id"] = appId
        result = await db.execute(text(f"SELECT * FROM eam.legal_entity {where_clause} ORDER BY create_at DESC"), params)
        try:
            repo = PostgresMasterDataRepository(db)
            service = MasterDataService(repo)
            items = await service.list_by_type("legal_entity")
        except Exception:
            pass
        return result.mappings().all()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch legal entities") from exc


@router.get("/help-files", dependencies=[Depends(require_permission("master_data", "read"))])
async def list_help_files(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT * FROM eam.help_file ORDER BY create_at DESC"))
        try:
            repo = PostgresMasterDataRepository(db)
            service = MasterDataService(repo)
            items = await service.list_by_type("help_file")
        except Exception:
            pass
        return {"data": result.mappings().all()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch help files") from exc