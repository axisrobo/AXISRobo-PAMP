"""EA Requests router — ported from ea-requests.ts (841 LOC)."""
from __future__ import annotations

import logging
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db, AsyncSessionLocal
from app.utils.pagination import PaginationParams, paginated_response
from app.utils.filters import multi_value_condition
from app.auth import require_permission, require_role, Role, get_current_user
from app.auth.models import AuthUser
from app.auth.ownership import check_request_creator, check_request_draft_status, check_reviewer_assignment
from app.auth.audit import audit_allow, audit_deny
from app.utils.email_service import send_email
from app.infrastructure.database.repositories.review_repo import PostgresReviewRequestRepository
from app.application.review.services import ReviewService

logger = logging.getLogger("eam.routers.ea_requests")

router = APIRouter()

REVIEW_RESULT_EQUIVALENT_VALUES = {
    "Approved with Exception": ["Approved with Exception", "Approved with Actions"],
    "Approved with Actions": ["Approved with Exception", "Approved with Actions"],
}

REQUEST_STATUS_LABELS = {
    "draft": "Draft",
    "submitted": "Submitted",
    "in progress": "In Progress",
    "completed": "Completed",
    "deleted": "Deleted",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_review_result_filter(review_result: str) -> str:
    values = [value.strip() for value in review_result.split(",") if value.strip()]
    normalized: list[str] = []
    for value in values:
        for candidate in REVIEW_RESULT_EQUIVALENT_VALUES.get(value, [value]):
            if candidate not in normalized:
                normalized.append(candidate)
    return ",".join(normalized)


def _normalize_request_status(status: Any) -> Any:
    if not isinstance(status, str):
        return status

    cleaned = " ".join(status.replace("_", " ").split())
    if not cleaned:
        return cleaned

    normalized = REQUEST_STATUS_LABELS.get(cleaned.casefold())
    if normalized:
        return normalized

    words = cleaned.lower().split(" ")
    small_words = {"and", "by", "of", "to", "with"}
    return " ".join(
        "EA"
        if word == "ea"
        else word
        if index > 0 and word in small_words
        else word.capitalize()
        for index, word in enumerate(words)
    )


def _normalize_request_status_filter(status: str) -> str:
    values = [value.strip() for value in status.split(",") if value.strip()]
    normalized = [_normalize_request_status(value).casefold() for value in values]
    return ",".join(normalized)


def _multi_value_casefold_condition(column: str, prefix: str, csv_value: str, params: dict) -> str:
    vals = [v.strip().casefold() for v in csv_value.split(",") if v.strip()]
    if len(vals) == 1:
        params[prefix] = vals[0]
        return f"LOWER(TRIM({column})) = :{prefix}"
    for i, value in enumerate(vals):
        params[f"{prefix}_{i}"] = value
    placeholders = ", ".join(f":{prefix}_{i}" for i in range(len(vals)))
    return f"LOWER(TRIM({column})) IN ({placeholders})"

def _map_request(r: dict) -> dict:
    """Map a raw DB row (dict) to the camelCase API shape."""
    reviewer = r.get("assign_reviewer")
    if isinstance(reviewer, list):
        reviewer_str = ", ".join(reviewer)
    else:
        reviewer_str = reviewer or ""
    return {
        "id": r.get("id"),
        "requestId": r.get("request_id"),
        "projectId": r.get("project_id"),
        "projectName": r.get("project_name") or "",
        "pm": r.get("pm") or "",
        "pmName": r.get("pm") or "",
        "pmItcode": r.get("pm_itcode") or "",
        "dtLead": r.get("dt_lead") or "",
        "dtLeadName": r.get("dt_lead") or "",
        "dtLeadItcode": r.get("dt_lead_itcode") or "",
        "itLead": r.get("it_lead") or "",
        "itLeadName": r.get("it_lead") or "",
        "itLeadItcode": r.get("it_lead_itcode") or "",
        "status": _normalize_request_status(r.get("status")),
        "scope": r.get("review_scope"),
        "reviewScope": r.get("review_scope"),
        "wsPhase": r.get("ws_phase_name"),
        "requestorName": r.get("requester"),
        "reviewerName": reviewer_str,
        "reviewResult": r.get("review_result"),
        "organization": r.get("organization"),
        "requestDesc": r.get("request_desc"),
        "link": r.get("link"),
        "createdAt": r.get("create_at"),
        "updatedAt": r.get("update_at"),
        "createdBy": r.get("create_by"),
        "changedBy": r.get("status_changed_by") or "",
        "changedAt": r.get("status_changed_at"),
        "statusRemark": r.get("status_remark") or "",
    }


async def _generate_request_id() -> str:
    """
    Generate next request_id from business_object_sequences table.
    Pattern: EA + 2-digit fiscal year + 4-digit sequence, e.g. EA250001
    Fiscal year: Apr-Mar (if month < 4, use previous year).

    Uses a SEPARATE, immediately-committed session so that the sequence counter
    is NOT rolled back if the caller's main transaction fails. This prevents
    duplicate request_ids caused by transaction rollback + retry.
    """
    now = datetime.now()
    # Calculate fiscal_year, e.g., FY2526
    if now.month < 4:
        start_year = now.year - 1
    else:
        start_year = now.year
    end_year = start_year + 1
    fy = f"FY{str(start_year)[-2:]}{str(end_year)[-2:]}"
    seq_name = "EA_Request"


    async with AsyncSessionLocal() as seq_session:
        result = await seq_session.execute(
            text(
                "INSERT INTO eam.fiscal_year_sequences (sequence_name, fiscal_year, current_value) "
                "VALUES (:seq_name, :fy, 1)"
                "ON CONFLICT (sequence_name, fiscal_year) "
                "DO UPDATE SET current_value = eam.fiscal_year_sequences.current_value + 1 "
                "RETURNING current_value"
            ),
            {"seq_name": seq_name, "fy": fy},
        )
        row = result.fetchone()
        next_val = int(row[0])
        await seq_session.commit()
    return f"EA{str(start_year)[-2:]}{str(next_val).zfill(4)}"


# Sort field whitelist to prevent SQL injection
SORT_FIELD_MAP: dict[str, str] = {
    "requestId": "r.request_id",
    "status": "r.status",
    "scope": "r.review_scope",
    "requestorName": "r.requester",
    "reviewResult": "r.review_result",
    "projectId": "r.project_id",
    "projectName": "p.name",
    "wsPhase": "r.ws_phase_name",
    "reviewerName": "r.assign_reviewer",
    "pmName": "p.pm",
    "dtLeadName": "p.dt_lead",
    "changedBy": "r.status_changed_by",
    "changedAt": "r.status_changed_at",
    "createdBy": "r.create_by",
    "createdAt": "r.create_at",
}


# ---------------------------------------------------------------------------
# GET / — List with pagination, filtering, sorting
# ---------------------------------------------------------------------------

@router.get("", dependencies=[Depends(require_permission("ea_request", "read"))])
async def list_requests(
    pag: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
    mine: bool = Query(False),
    requestId: str | None = Query(None),
    status: str | None = Query(None),
    reviewResult: str | None = Query(None),
    scope: str | None = Query(None),
    projectId: str | None = Query(None),
    projectName: str | None = Query(None),
    requestorName: str | None = Query(None),
    organization: str | None = Query(None),
    reviewerName: str | None = Query(None),
    dateFrom: str | None = Query(None),
    dateTo: str | None = Query(None),
    bizType: str | None = Query(None),
    scoreMin: float | None = Query(None),
    scoreMax: float | None = Query(None),
    firstPass: str | None = Query(None),
    leadTimeMin: float | None = Query(None),
    leadTimeMax: float | None = Query(None),
    workerType: str | None = Query(None),
    pmName: str | None = Query(None),
):
    try:
        conditions: list[str] = ["r.status <> 'Deleted'"]
        params: dict[str, Any] = {}
        
        if mine:
            conditions.append("r.requester = :current_user")
            params["current_user"] = user.id
        extra_joins: list[str] = []

        if requestId:
            conditions.append("r.request_id ILIKE :p_requestId")
            params["p_requestId"] = f"%{requestId}%"
        if status:
            normalized_status = _normalize_request_status_filter(status)
            conditions.append(
                _multi_value_casefold_condition("r.status", "p_status", normalized_status, params)
            )
        if reviewResult:
            normalized_review_result = _normalize_review_result_filter(reviewResult)
            conditions.append(
                multi_value_condition(
                    "r.review_result", "p_reviewResult", normalized_review_result, params
                )
            )
        if scope:
            conditions.append(multi_value_condition("r.review_scope", "p_scope", scope, params))
        if requestorName:
            conditions.append("r.requester ILIKE :p_requestorName")
            params["p_requestorName"] = f"%{requestorName}%"
        if organization:
            conditions.append(multi_value_condition("r.organization", "p_organization", organization, params))
        if projectId:
            conditions.append("r.project_id = :p_projectId")
            params["p_projectId"] = projectId
        if projectName:
            conditions.append("p.name ILIKE :p_projectName")
            params["p_projectName"] = f"%{projectName}%"
        if pmName:
            conditions.append("p.pm ILIKE :p_pmName")
            params["p_pmName"] = f"%{pmName}%"
        if reviewerName:
            conditions.append(
                "(EXISTS (SELECT 1 FROM eam.eam_bigea_team_members _rv "
                "WHERE _rv.itcode = ANY(r.assign_reviewer) "
                "AND (_rv.name ILIKE :p_reviewerName OR _rv.itcode ILIKE :p_reviewerName)) "
                "OR EXISTS (SELECT 1 FROM unnest(r.assign_reviewer) AS _itc "
                "WHERE _itc ILIKE :p_reviewerName))"
            )
            params["p_reviewerName"] = f"%{reviewerName}%"
        if workerType:
            extra_joins.append(
                "JOIN eam.eam_bigea_team_members _wt2 ON _wt2.itcode = ANY(r.assign_reviewer)"
            )
            conditions.append(multi_value_condition("_wt2.worker_type", "p_workerType", workerType, params))
        if dateFrom:
            conditions.append("r.create_at >= :p_dateFrom")
            params["p_dateFrom"] = datetime.strptime(dateFrom, "%Y-%m-%d")
        if dateTo:
            date_to_dt = datetime.strptime(dateTo, "%Y-%m-%d")
            date_to_exclusive = date_to_dt.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            conditions.append("r.create_at <= :p_dateTo")
            params["p_dateTo"] = date_to_exclusive
        if firstPass == "true":
            conditions.append(
                "NOT EXISTS (SELECT 1 FROM eam.eam_request_process_log l "
                "WHERE l.request_id = r.request_id AND l.action = 'Returned by EA')"
            )
            conditions.append(
                "NOT EXISTS (SELECT 1 FROM eam.eam_meetings m WHERE m.request_id = r.request_id)"
            )
            conditions.append(
                "NOT EXISTS (SELECT 1 FROM eam.eam_actions act WHERE act.request_id = r.request_id)"
            )
        if leadTimeMin is not None or leadTimeMax is not None:
            conditions.append("r.status = 'Completed'")
            conditions.append("r.update_at IS NOT NULL")
            if leadTimeMin is not None:
                conditions.append(
                    "ROUND(EXTRACT(EPOCH FROM (r.update_at - r.create_at)) / 86400::numeric, 1) >= :p_leadTimeMin"
                )
                params["p_leadTimeMin"] = leadTimeMin
            if leadTimeMax is not None:
                conditions.append(
                    "ROUND(EXTRACT(EPOCH FROM (r.update_at - r.create_at)) / 86400::numeric, 1) <= :p_leadTimeMax"
                )
                params["p_leadTimeMax"] = leadTimeMax
        if bizType or scoreMin is not None or scoreMax is not None:
            extra_joins.append(
                "INNER JOIN eam.eam_request_attachment att ON att.request_id = r.request_id"
            )
            extra_joins.append(
                "INNER JOIN eam.eam_arch_ai_check aic ON aic.attachment_uuid = att.id"
            )
            if bizType:
                conditions.append("att.biz_type = :p_bizType")
                params["p_bizType"] = bizType
            if scoreMin is not None:
                conditions.append(
                    "(aic.result->'overall_evaluation'->>'score')::numeric >= :p_scoreMin"
                )
                params["p_scoreMin"] = scoreMin
            if scoreMax is not None:
                conditions.append(
                    "(aic.result->'overall_evaluation'->>'score')::numeric <= :p_scoreMax"
                )
                params["p_scoreMax"] = scoreMax

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        db_sort_field = SORT_FIELD_MAP.get(pag.sort_field or "", "r.request_id")
        db_sort_order = "ASC" if pag.sort_order == "asc" else "DESC"

        joins_sql = "\n      ".join(extra_joins)
        base_query = f"""
            FROM eam.eam_request r
            LEFT JOIN eam.eam_project p ON r.project_id = p.project_id OR r.project_id = p.id::text
            {joins_sql}
            {where_clause}
        """

        data_sql = f"""
            SELECT DISTINCT r.*,
              COALESCE(p.name, p.name) AS project_name,
              COALESCE(p.pm, '') AS pm,
              COALESCE(p.dt_lead, '') AS dt_lead,
              COALESCE(p.it_lead, '') AS it_lead
            {base_query}
            ORDER BY {db_sort_field} {db_sort_order} NULLS LAST
            LIMIT :p_limit OFFSET :p_offset
        """
        count_sql = f"SELECT COUNT(DISTINCT r.request_id) as total {base_query}"

        params["p_limit"] = pag.page_size
        params["p_offset"] = pag.offset

        repo = PostgresReviewRequestRepository(db)
        service = ReviewService(repo)
        rows, total = await service.list_query(data_sql, params, count_sql)

        return paginated_response([_map_request(r) for r in rows], total, pag.page, pag.page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch EA requests") from e


# ---------------------------------------------------------------------------
# GET /dashboard — 17 aggregated stats queries
# MUST be before /{id} to avoid being caught by the path param route
# ---------------------------------------------------------------------------

@router.get("/dashboard", dependencies=[Depends(require_permission("ea_request", "read"))])
async def dashboard(
    db: AsyncSession = Depends(get_db),
    # query params use 'from' which is a Python keyword, alias via Query
    date_from: str | None = Query(None, alias="from"),
    date_to: str | None = Query(None, alias="to"),
    org: str | None = Query(None),
    workerType: str | None = Query(None),
):
    try:
        # -- Build date filter clause (unaliased table) --
        date_conditions: list[str] = ["status <> 'Deleted'"]
        date_params: dict[str, Any] = {}
        if date_from:
            date_conditions.append("create_at >= :p_from")
            date_params["p_from"] = datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            date_to_exclusive = date_to_dt.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            date_conditions.append("create_at <= :p_to")
            date_params["p_to"] = date_to_exclusive
        date_where = " AND ".join(date_conditions)

        # Organization filter (supports comma-separated, e.g. "DTIT,other")
        org_filter = ""
        r_org_filter = ""
        if org:
            org_vals = [v.strip() for v in org.split(",") if v.strip()]
            if len(org_vals) == 1:
                org_filter = f" AND organization = '{org_vals[0]}'"
                r_org_filter = f" AND r.organization = '{org_vals[0]}'"
            elif len(org_vals) >= 2:
                in_list = ", ".join(f"'{v}'" for v in org_vals)
                org_filter = f" AND organization IN ({in_list})"
                r_org_filter = f" AND r.organization IN ({in_list})"

        # Worker type filter (supports comma-separated, e.g. "EA Office,Domain Architect")
        wt_filter = ""
        r_wt_filter = ""
        t_wt_filter = ""
        if workerType:
            wt_vals = [v.strip() for v in workerType.split(",") if v.strip()]
            valid_wts = [v for v in wt_vals if v in ("EA Office", "Domain Architect")]
            if len(valid_wts) == 1:
                wt_filter = (
                    f" AND EXISTS (SELECT 1 FROM eam.eam_bigea_team_members _wt "
                    f"WHERE _wt.itcode = ANY(assign_reviewer) AND _wt.worker_type = '{valid_wts[0]}')"
                )
                r_wt_filter = (
                    f" AND EXISTS (SELECT 1 FROM eam.eam_bigea_team_members _wt "
                    f"WHERE _wt.itcode = ANY(r.assign_reviewer) AND _wt.worker_type = '{valid_wts[0]}')"
                )
                t_wt_filter = f" AND t.worker_type = '{valid_wts[0]}'"
            elif len(valid_wts) == 2:
                pass  # both selected = all, no filter

        # r-aliased date conditions (for JOINed queries)
        r_date_conds: list[str] = ["r.status <> 'Deleted'"]
        if date_from:
            r_date_conds.append("r.create_at >= :p_from")
        if date_to:
            r_date_conds.append("r.create_at <= :p_to")
        r_date_where = " AND ".join(r_date_conds)

        # -- Helper to run one query and return list of dicts --
        _repo = PostgresReviewRequestRepository(db)
        _dashboard_service = ReviewService(_repo)

        async def _q(sql: str, params: dict | None = None) -> list[dict]:
            return await _dashboard_service.execute_rows(sql, params)

        dp = dict(date_params)  # shallow copy for reuse

        # 1. Count by status
        status_counts = await _q(
            f"SELECT status, COUNT(*)::int as count "
            f"FROM eam.eam_request WHERE {date_where}{org_filter}{wt_filter} "
            f"GROUP BY status ORDER BY count DESC",
            dp,
        )

        # 2. Count by review_result for Completed requests
        completed_result_counts = await _q(
            f"SELECT COALESCE(review_result, 'Unknown') as result, COUNT(*)::int as count "
            f"FROM eam.eam_request WHERE {date_where}{org_filter}{wt_filter} AND status = 'Completed' "
            f"GROUP BY review_result ORDER BY count DESC",
            dp,
        )

        # 3. Count by organization
        org_counts = await _q(
            f"SELECT COALESCE(organization, 'Unknown') as organization, COUNT(*)::int as count "
            f"FROM eam.eam_request WHERE {date_where}{org_filter}{wt_filter} "
            f"GROUP BY organization ORDER BY count DESC",
            dp,
        )

        # 4. Monthly trend
        monthly_trend = await _q(
            f"SELECT TO_CHAR(create_at, 'YYYY-MM') as month, "
            f"COUNT(*)::int as submitted, "
            f"COUNT(*) FILTER (WHERE review_result IN ('Approved','Approved with Actions'))::int as approved "
            f"FROM eam.eam_request WHERE {date_where}{org_filter}{wt_filter} "
            f"GROUP BY TO_CHAR(create_at, 'YYYY-MM') ORDER BY month",
            dp,
        )

        # 5. Monthly lead time
        monthly_lead_time = await _q(
            f"SELECT TO_CHAR(create_at, 'YYYY-MM') as month, "
            f"ROUND(MIN(EXTRACT(EPOCH FROM (update_at - create_at)) / 86400)::numeric, 1) as min_days, "
            f"ROUND(AVG(EXTRACT(EPOCH FROM (update_at - create_at)) / 86400)::numeric, 1) as avg_days, "
            f"ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (update_at - create_at)) / 86400))::numeric, 1) as median_days, "
            f"ROUND(MAX(EXTRACT(EPOCH FROM (update_at - create_at)) / 86400)::numeric, 1) as max_days "
            f"FROM eam.eam_request WHERE {date_where}{org_filter}{wt_filter} AND status = 'Completed' AND update_at IS NOT NULL "
            f"GROUP BY TO_CHAR(create_at, 'YYYY-MM') ORDER BY month",
            dp,
        )

        # 6. Monthly by organization
        monthly_by_org = await _q(
            f"SELECT TO_CHAR(create_at, 'YYYY-MM') as month, "
            f"COALESCE(organization, 'Unknown') as organization, COUNT(*)::int as count "
            f"FROM eam.eam_request WHERE {date_where}{org_filter}{wt_filter} "
            f"GROUP BY TO_CHAR(create_at, 'YYYY-MM'), organization ORDER BY month, count DESC",
            dp,
        )

        # 7. Recent requests (last 10, within date range)
        recent_conds: list[str] = ["r.status <> 'Deleted'"]
        recent_params: dict[str, Any] = {}
        if date_from:
            recent_conds.append("r.create_at >= :p_from")
            recent_params["p_from"] = date_params["p_from"]
        if date_to:
            recent_conds.append("r.create_at <= :p_to")
            recent_params["p_to"] = date_params["p_to"]
        recent_requests_raw = await _q(
            f"SELECT r.request_id, r.status, r.review_result, r.organization, "
            f"r.requester, r.create_at, r.update_at, "
            f"p.name AS project_name, r.review_scope "
            f"FROM eam.eam_request r "
            f"LEFT JOIN eam.eam_project p ON r.project_id = p.project_id OR r.project_id = p.id::text "
            f"WHERE {' AND '.join(recent_conds)}{r_org_filter}{r_wt_filter} "
            f"ORDER BY r.update_at DESC NULLS LAST LIMIT 10",
            recent_params,
        )
        recent_requests = [
            {
                "requestId": r["request_id"],
                "status": _normalize_request_status(r["status"]),
                "reviewResult": r["review_result"],
                "organization": r["organization"],
                "requester": r["requester"],
                "projectName": r["project_name"],
                "reviewScope": r["review_scope"],
                "createdAt": r["create_at"],
                "updatedAt": r["update_at"],
            }
            for r in recent_requests_raw
        ]

        # 8. Architect by Org x Worker Type
        architect_by_org_type = await _q(
            f"SELECT "
            f"CASE WHEN r.organization = 'DTIT' THEN 'DTIT' ELSE 'Other' END AS org_group, "
            f"t.worker_type, "
            f"COUNT(DISTINCT r.id)::int AS count, "
            f"COUNT(DISTINCT t.itcode)::int AS architect_count, "
            f"COUNT(DISTINCT m.id)::int AS meeting_count, "
            f"COUNT(DISTINCT ac.id)::int AS action_count "
            f"FROM eam.eam_request r "
            f"JOIN eam.eam_bigea_team_members t ON t.itcode = ANY(r.assign_reviewer) "
            f"LEFT JOIN eam.eam_meetings m ON m.project_id = r.project_id "
            f"LEFT JOIN eam.eam_actions ac ON ac.project_id = r.project_id "
            f"WHERE {r_date_where}{r_org_filter}{t_wt_filter} "
            f"AND t.worker_type IN ('EA Office', 'Domain Architect') "
            f"GROUP BY org_group, t.worker_type ORDER BY org_group, t.worker_type",
            dp,
        )

        # 9. Top 10 architects workload
        top_architects = await _q(
            f"SELECT t.name AS architect_name, "
            f"COUNT(DISTINCT r.id)::int AS count, "
            f"COUNT(DISTINCT m.id)::int AS meeting_count, "
            f"COUNT(DISTINCT ac.id)::int AS action_count "
            f"FROM eam.eam_request r "
            f"JOIN eam.eam_bigea_team_members t ON t.itcode = ANY(r.assign_reviewer) "
            f"LEFT JOIN eam.eam_meetings m ON m.project_id = r.project_id "
            f"LEFT JOIN eam.eam_actions ac ON ac.project_id = r.project_id "
            f"WHERE {r_date_where}{r_org_filter}{t_wt_filter} "
            f"GROUP BY t.name ORDER BY count DESC LIMIT 10",
            dp,
        )

        # 10. Monthly review activity
        # Build the conditional JOIN fragments for org/wt filters
        meeting_org_join = ""
        action_org_join = ""
        if org or workerType:
            meeting_org_join = (
                f"JOIN eam.eam_request r ON r.project_id = mt.project_id "
                f"AND r.status <> 'Deleted'{r_org_filter}{r_wt_filter}"
            )
            action_org_join = (
                f"JOIN eam.eam_request r2 ON r2.project_id = ac.project_id "
                f"AND r2.status <> 'Deleted'"
                f"{r_org_filter.replace('r.', 'r2.')}{r_wt_filter.replace('r.', 'r2.')}"
            )

        monthly_review_activity = await _q(
            f"SELECT month, "
            f"ROUND(meetings::numeric / NULLIF(projects, 0), 1) AS avg_meetings, "
            f"ROUND(actions::numeric / NULLIF(projects, 0), 1) AS avg_actions, "
            f"min_meetings, max_meetings, min_actions, max_actions "
            f"FROM ( "
            f"  SELECT m.month, m.projects, m.meetings, m.min_meetings, m.max_meetings, "
            f"         COALESCE(a.actions, 0) AS actions, "
            f"         COALESCE(a.min_actions, 0) AS min_actions, "
            f"         COALESCE(a.max_actions, 0) AS max_actions "
            f"  FROM ( "
            f"    SELECT TO_CHAR(mt.create_at, 'YYYY-MM') AS month, "
            f"           COUNT(DISTINCT mt.project_id)::int AS projects, "
            f"           COUNT(*)::int AS meetings, "
            f"           MIN(pc.cnt)::int AS min_meetings, "
            f"           MAX(pc.cnt)::int AS max_meetings "
            f"    FROM eam.eam_meetings mt "
            f"    JOIN (SELECT project_id, TO_CHAR(create_at, 'YYYY-MM') AS month, COUNT(*)::int AS cnt "
            f"         FROM eam.eam_meetings WHERE create_at IS NOT NULL "
            f"         GROUP BY project_id, TO_CHAR(create_at, 'YYYY-MM')) pc "
            f"      ON pc.project_id = mt.project_id AND pc.month = TO_CHAR(mt.create_at, 'YYYY-MM') "
            f"    {meeting_org_join} "
            f"    WHERE mt.create_at IS NOT NULL "
            f"    GROUP BY TO_CHAR(mt.create_at, 'YYYY-MM') "
            f"  ) m "
            f"  LEFT JOIN ( "
            f"    SELECT TO_CHAR(ac.create_at, 'YYYY-MM') AS month, "
            f"           COUNT(*)::int AS actions, "
            f"           MIN(pc2.cnt)::int AS min_actions, "
            f"           MAX(pc2.cnt)::int AS max_actions "
            f"    FROM eam.eam_actions ac "
            f"    JOIN (SELECT project_id, TO_CHAR(create_at, 'YYYY-MM') AS month, COUNT(*)::int AS cnt "
            f"         FROM eam.eam_actions WHERE create_at IS NOT NULL "
            f"         GROUP BY project_id, TO_CHAR(create_at, 'YYYY-MM')) pc2 "
            f"      ON pc2.project_id = ac.project_id AND pc2.month = TO_CHAR(ac.create_at, 'YYYY-MM') "
            f"    {action_org_join} "
            f"    WHERE ac.create_at IS NOT NULL "
            f"    GROUP BY TO_CHAR(ac.create_at, 'YYYY-MM') "
            f"  ) a ON a.month = m.month "
            f") sub ORDER BY month",
        )

        # 11. Monthly Org x Worker Type trend
        monthly_org_type_trend = await _q(
            f"SELECT TO_CHAR(r.create_at, 'YYYY-MM') AS month, "
            f"CASE WHEN r.organization = 'DTIT' THEN 'DTIT' ELSE 'Other' END AS org_group, "
            f"t.worker_type, "
            f"COUNT(DISTINCT r.id)::int AS count, "
            f"COUNT(DISTINCT t.itcode)::int AS architect_count "
            f"FROM eam.eam_request r "
            f"JOIN eam.eam_bigea_team_members t ON t.itcode = ANY(r.assign_reviewer) "
            f"WHERE {r_date_where}{r_org_filter}{t_wt_filter} "
            f"AND t.worker_type IN ('EA Office', 'Domain Architect') "
            f"GROUP BY TO_CHAR(r.create_at, 'YYYY-MM'), org_group, t.worker_type "
            f"ORDER BY month, org_group, t.worker_type",
            dp,
        )

        # 12. Architecture Diagram Score Stats
        diagram_score_stats = await _q(
            f"SELECT a.biz_type, "
            f"MIN((c.result->'overall_evaluation'->>'score')::numeric) AS min_score, "
            f"MAX((c.result->'overall_evaluation'->>'score')::numeric) AS max_score, "
            f"ROUND(AVG((c.result->'overall_evaluation'->>'score')::numeric), 1) AS avg_score, "
            f"ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (c.result->'overall_evaluation'->>'score')::numeric))::numeric, 1) AS median_score, "
            f"COUNT(*)::int AS total "
            f"FROM eam.eam_arch_ai_check c "
            f"JOIN eam.eam_request_attachment a ON a.id = c.attachment_uuid "
            f"JOIN eam.eam_request r ON r.request_id = a.request_id "
            f"WHERE {r_date_where}{r_org_filter}{r_wt_filter} "
            f"AND c.result->'overall_evaluation'->>'score' IS NOT NULL "
            f"GROUP BY a.biz_type ORDER BY a.biz_type",
            dp,
        )

        # 13. Monthly Architecture Score Trends
        monthly_arch_score = await _q(
            f"SELECT TO_CHAR(r.create_at, 'YYYY-MM') AS month, a.biz_type, "
            f"MIN((c.result->'overall_evaluation'->>'score')::numeric) AS min_score, "
            f"ROUND(AVG((c.result->'overall_evaluation'->>'score')::numeric), 1) AS avg_score, "
            f"ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (c.result->'overall_evaluation'->>'score')::numeric))::numeric, 1) AS median_score, "
            f"MAX((c.result->'overall_evaluation'->>'score')::numeric) AS max_score, "
            f"COUNT(*)::int AS total "
            f"FROM eam.eam_arch_ai_check c "
            f"JOIN eam.eam_request_attachment a ON a.id = c.attachment_uuid "
            f"JOIN eam.eam_request r ON r.request_id = a.request_id "
            f"WHERE {r_date_where}{r_org_filter}{r_wt_filter} "
            f"AND c.result->'overall_evaluation'->>'score' IS NOT NULL "
            f"GROUP BY TO_CHAR(r.create_at, 'YYYY-MM'), a.biz_type ORDER BY month, a.biz_type",
            dp,
        )

        # 14. First-pass approval rate
        first_pass_rows = await _q(
            f"SELECT "
            f"COUNT(*)::int AS total_completed, "
            f"COUNT(*) FILTER ( "
            f"  WHERE NOT EXISTS ( "
            f"    SELECT 1 FROM eam.eam_request_process_log l "
            f"    WHERE l.request_id = r.request_id AND l.action = 'Returned by EA' "
            f"  ) AND NOT EXISTS ( "
            f"    SELECT 1 FROM eam.eam_meetings m WHERE m.request_id = r.request_id "
            f"  ) AND NOT EXISTS ( "
            f"    SELECT 1 FROM eam.eam_actions act WHERE act.request_id = r.request_id "
            f"  ) "
            f")::int AS first_pass_count, "
            f"COUNT(*) FILTER ( "
            f"  WHERE EXISTS ( "
            f"    SELECT 1 FROM eam.eam_request_process_log l "
            f"    WHERE l.request_id = r.request_id AND l.action = 'Returned by EA' "
            f"  ) "
            f")::int AS return_count, "
            f"COUNT(*) FILTER ( "
            f"  WHERE EXISTS ( "
            f"    SELECT 1 FROM eam.eam_meetings m WHERE m.request_id = r.request_id "
            f"  ) "
            f")::int AS meeting_count, "
            f"COUNT(*) FILTER ( "
            f"  WHERE EXISTS ( "
            f"    SELECT 1 FROM eam.eam_actions act WHERE act.request_id = r.request_id "
            f"  ) "
            f")::int AS action_count "
            f"FROM eam.eam_request r "
            f"WHERE r.status = 'Completed' AND {date_where}{org_filter}{wt_filter}",
            dp,
        )
        first_pass_rate = first_pass_rows[0] if first_pass_rows else {
            "total_completed": 0, "first_pass_count": 0
        }

        # 15. Individual scores for scatter plot
        score_distribution = await _q(
            f"SELECT a.biz_type, "
            f"ROUND((c.result->'overall_evaluation'->>'score')::numeric, 2) AS score "
            f"FROM eam.eam_arch_ai_check c "
            f"JOIN eam.eam_request_attachment a ON a.id = c.attachment_uuid "
            f"JOIN eam.eam_request r ON r.request_id = a.request_id "
            f"WHERE {r_date_where}{r_org_filter}{r_wt_filter} "
            f"AND c.result->'overall_evaluation'->>'score' IS NOT NULL "
            f"ORDER BY a.biz_type, score",
            dp,
        )

        # 16. Monthly first-pass trend
        monthly_first_pass = await _q(
            f"SELECT TO_CHAR(r.create_at, 'YYYY-MM') AS month, "
            f"COUNT(*)::int AS total, "
            f"COUNT(*) FILTER ( "
            f"  WHERE NOT EXISTS ( "
            f"    SELECT 1 FROM eam.eam_request_process_log l "
            f"    WHERE l.request_id = r.request_id AND l.action = 'Returned by EA' "
            f"  ) AND NOT EXISTS ( "
            f"    SELECT 1 FROM eam.eam_meetings m WHERE m.request_id = r.request_id "
            f"  ) AND NOT EXISTS ( "
            f"    SELECT 1 FROM eam.eam_actions act WHERE act.request_id = r.request_id "
            f"  ) "
            f")::int AS first_pass "
            f"FROM eam.eam_request r "
            f"WHERE r.status = 'Completed' AND {date_where}{org_filter}{wt_filter} "
            f"GROUP BY TO_CHAR(r.create_at, 'YYYY-MM') ORDER BY month",
            dp,
        )

        # 17. Monthly Top 10 Architects
        monthly_top_architects = await _q(
            f"SELECT month, architect_name, project_count, rank::int "
            f"FROM ( "
            f"  SELECT TO_CHAR(r.create_at, 'YYYY-MM') AS month, "
            f"         t.name AS architect_name, "
            f"         COUNT(DISTINCT r.id)::int AS project_count, "
            f"         ROW_NUMBER() OVER ( "
            f"           PARTITION BY TO_CHAR(r.create_at, 'YYYY-MM') "
            f"           ORDER BY COUNT(DISTINCT r.id) DESC "
            f"         ) AS rank "
            f"  FROM eam.eam_request r "
            f"  JOIN eam.eam_bigea_team_members t ON t.itcode = ANY(r.assign_reviewer) "
            f"  WHERE {r_date_where}{r_org_filter}{t_wt_filter} "
            f"  GROUP BY TO_CHAR(r.create_at, 'YYYY-MM'), t.name "
            f") ranked WHERE rank <= 10 ORDER BY month, rank",
            dp,
        )

        # 18. Monthly Requestor vs Reviewer time split (with action breakdown)
        monthly_rr_time = await _q(
            f"WITH events AS ( "
            f"  SELECT r.request_id, 'Created' AS action, r.create_at AS event_at "
            f"  FROM eam.eam_request r "
            f"  WHERE r.status = 'Completed' AND {date_where}{org_filter}{wt_filter} "
            f"  UNION ALL "
            f"  SELECT l.request_id, l.action, l.create_at "
            f"  FROM eam.eam_request_process_log l "
            f"  JOIN eam.eam_request r ON r.request_id = l.request_id "
            f"  WHERE r.status = 'Completed' AND {r_date_where}{r_org_filter}{r_wt_filter} "
            f"), "
            f"timeline AS ( "
            f"  SELECT request_id, action, event_at, "
            f"    LEAD(event_at) OVER (PARTITION BY request_id ORDER BY event_at) AS next_at "
            f"  FROM events "
            f"), "
            f"phases AS ( "
            f"  SELECT request_id, action, event_at, next_at, "
            f"    EXTRACT(EPOCH FROM (next_at - event_at)) / 86400.0 AS days, "
            f"    CASE WHEN action IN ('Created','Returned by EA') THEN 'requestor' "
            f"         WHEN action IN ('Submitted','Accepted by EA') THEN 'reviewer' END AS owner "
            f"  FROM timeline WHERE next_at IS NOT NULL "
            f"), "
            f"per_req AS ( "
            f"  SELECT request_id, MIN(event_at) AS created, "
            f"    SUM(CASE WHEN owner='requestor' THEN days ELSE 0 END) AS req_days, "
            f"    SUM(CASE WHEN owner='reviewer' THEN days ELSE 0 END) AS rev_days "
            f"  FROM phases GROUP BY request_id "
            f"), "
            f"reviewer_phases AS ( "
            f"  SELECT request_id, event_at AS phase_start, next_at AS phase_end "
            f"  FROM phases WHERE owner = 'reviewer' "
            f"), "
            f"action_clips AS ( "
            f"  SELECT a.request_id, rp.phase_start, rp.phase_end, "
            f"    GREATEST(a.open_date, rp.phase_start) AS clip_start, "
            f"    LEAST(COALESCE(a.close_date, rp.phase_end), rp.phase_end) AS clip_end "
            f"  FROM eam.eam_actions a "
            f"  JOIN reviewer_phases rp ON a.request_id = rp.request_id "
            f"  WHERE a.open_date IS NOT NULL "
            f"    AND a.open_date < rp.phase_end "
            f"    AND COALESCE(a.close_date, rp.phase_end) > rp.phase_start "
            f"), "
            f"phase_action_coverage AS ( "
            f"  SELECT request_id, phase_start, phase_end, "
            f"    EXTRACT(EPOCH FROM ( "
            f"      LEAST(MAX(clip_end), phase_end) - GREATEST(MIN(clip_start), phase_start) "
            f"    )) / 86400.0 AS coverage_days "
            f"  FROM action_clips WHERE clip_start < clip_end "
            f"  GROUP BY request_id, phase_start, phase_end "
            f"), "
            f"per_req_action AS ( "
            f"  SELECT request_id, "
            f"    SUM(GREATEST(0, coverage_days)) AS action_days "
            f"  FROM phase_action_coverage "
            f"  GROUP BY request_id "
            f") "
            f"SELECT TO_CHAR(pr.created, 'YYYY-MM') AS month, "
            f"  COUNT(*)::int AS count, "
            f"  ROUND(AVG(pr.req_days)::numeric, 1) AS avg_requestor_days, "
            f"  ROUND(AVG(pr.rev_days)::numeric, 1) AS avg_reviewer_days, "
            f"  ROUND(AVG(COALESCE(pa.action_days, 0))::numeric, 1) AS avg_action_days, "
            f"  ROUND(AVG(pr.rev_days - COALESCE(pa.action_days, 0))::numeric, 1) AS avg_pure_reviewer_days "
            f"FROM per_req pr "
            f"LEFT JOIN per_req_action pa ON pr.request_id = pa.request_id "
            f"GROUP BY TO_CHAR(pr.created, 'YYYY-MM') ORDER BY month",
            dp,
        )

        # 19. Overall Requestor vs Reviewer time split (for pie chart, with action breakdown)
        rr_split_rows = await _q(
            f"WITH events AS ( "
            f"  SELECT r.request_id, 'Created' AS action, r.create_at AS event_at "
            f"  FROM eam.eam_request r "
            f"  WHERE r.status = 'Completed' AND {date_where}{org_filter}{wt_filter} "
            f"  UNION ALL "
            f"  SELECT l.request_id, l.action, l.create_at "
            f"  FROM eam.eam_request_process_log l "
            f"  JOIN eam.eam_request r ON r.request_id = l.request_id "
            f"  WHERE r.status = 'Completed' AND {r_date_where}{r_org_filter}{r_wt_filter} "
            f"), "
            f"timeline AS ( "
            f"  SELECT request_id, action, event_at, "
            f"    LEAD(event_at) OVER (PARTITION BY request_id ORDER BY event_at) AS next_at "
            f"  FROM events "
            f"), "
            f"phases AS ( "
            f"  SELECT request_id, action, event_at, next_at, "
            f"    EXTRACT(EPOCH FROM (next_at - event_at)) / 86400.0 AS days, "
            f"    CASE WHEN action IN ('Created','Returned by EA') THEN 'requestor' "
            f"         WHEN action IN ('Submitted','Accepted by EA') THEN 'reviewer' END AS owner "
            f"  FROM timeline WHERE next_at IS NOT NULL "
            f"), "
            f"per_req AS ( "
            f"  SELECT request_id, "
            f"    SUM(CASE WHEN owner='requestor' THEN days ELSE 0 END) AS req_days, "
            f"    SUM(CASE WHEN owner='reviewer' THEN days ELSE 0 END) AS rev_days "
            f"  FROM phases GROUP BY request_id "
            f"), "
            f"reviewer_phases AS ( "
            f"  SELECT request_id, event_at AS phase_start, next_at AS phase_end "
            f"  FROM phases WHERE owner = 'reviewer' "
            f"), "
            f"action_clips AS ( "
            f"  SELECT a.request_id, rp.phase_start, rp.phase_end, "
            f"    GREATEST(a.open_date, rp.phase_start) AS clip_start, "
            f"    LEAST(COALESCE(a.close_date, rp.phase_end), rp.phase_end) AS clip_end "
            f"  FROM eam.eam_actions a "
            f"  JOIN reviewer_phases rp ON a.request_id = rp.request_id "
            f"  WHERE a.open_date IS NOT NULL "
            f"    AND a.open_date < rp.phase_end "
            f"    AND COALESCE(a.close_date, rp.phase_end) > rp.phase_start "
            f"), "
            f"phase_action_coverage AS ( "
            f"  SELECT request_id, phase_start, phase_end, "
            f"    EXTRACT(EPOCH FROM ( "
            f"      LEAST(MAX(clip_end), phase_end) - GREATEST(MIN(clip_start), phase_start) "
            f"    )) / 86400.0 AS coverage_days "
            f"  FROM action_clips WHERE clip_start < clip_end "
            f"  GROUP BY request_id, phase_start, phase_end "
            f"), "
            f"per_req_action AS ( "
            f"  SELECT request_id, "
            f"    SUM(GREATEST(0, coverage_days)) AS action_days "
            f"  FROM phase_action_coverage "
            f"  GROUP BY request_id "
            f") "
            f"SELECT COUNT(*)::int AS count, "
            f"  ROUND(AVG(pr.req_days)::numeric, 1) AS avg_requestor_days, "
            f"  ROUND(AVG(pr.rev_days)::numeric, 1) AS avg_reviewer_days, "
            f"  ROUND(AVG(COALESCE(pa.action_days, 0))::numeric, 1) AS avg_action_days, "
            f"  ROUND(AVG(pr.rev_days - COALESCE(pa.action_days, 0))::numeric, 1) AS avg_pure_reviewer_days "
            f"FROM per_req pr "
            f"LEFT JOIN per_req_action pa ON pr.request_id = pa.request_id",
            dp,
        )
        rr_time_split = rr_split_rows[0] if rr_split_rows else {
            "count": 0, "avg_requestor_days": 0, "avg_reviewer_days": 0,
            "avg_action_days": 0, "avg_pure_reviewer_days": 0
        }

        total = sum(r.get("count", 0) for r in status_counts)

        return {
            "total": total,
            "statusCounts": status_counts,
            "completedResultCounts": completed_result_counts,
            "orgCounts": org_counts,
            "monthlyTrend": monthly_trend,
            "monthlyLeadTime": monthly_lead_time,
            "monthlyByOrg": monthly_by_org,
            "architectByOrgType": architect_by_org_type,
            "topArchitects": top_architects,
            "monthlyReviewActivity": monthly_review_activity,
            "monthlyOrgTypeTrend": monthly_org_type_trend,
            "diagramScoreStats": diagram_score_stats,
            "monthlyArchScore": monthly_arch_score,
            "firstPassRate": first_pass_rate,
            "scoreDistribution": score_distribution,
            "monthlyFirstPass": monthly_first_pass,
            "monthlyTopArchitects": monthly_top_architects,
            "monthlyRequestorReviewerTime": monthly_rr_time,
            "requestorReviewerTimeSplit": rr_time_split,
            "recentRequests": recent_requests,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard stats") from e


# ---------------------------------------------------------------------------
# GET /filter-options — Distinct values for search dropdowns
# MUST be before /{id}
# ---------------------------------------------------------------------------

@router.get("/filter-options", dependencies=[Depends(require_permission("ea_request", "read"))])
async def filter_options(db: AsyncSession = Depends(get_db)):
    try:
        proj_result = await db.execute(text(
            "SELECT DISTINCT r.project_id, "
            "  p.name AS project_name, "
            "FROM eam.eam_request r "
            "LEFT JOIN eam.eam_project p ON r.project_id = p.project_id OR r.project_id = p.id::text "
            "WHERE r.project_id IS NOT NULL AND r.project_id <> '' "
            "ORDER BY r.project_id"
        ))
        org_result = await db.execute(text(
            "SELECT DISTINCT organization "
            "FROM eam.eam_request "
            "WHERE organization IS NOT NULL AND organization <> '' "
            "ORDER BY organization"
        ))
        return {
            "projects": [
                {"project_id": r[0], "project_name": r[1] or ""}
                for r in proj_result.fetchall()
            ],
            "organizations": [r[0] for r in org_result.fetchall()],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch filter options") from e


# ---------------------------------------------------------------------------
# GET /{id} — Get single request by request_id or UUID
# ---------------------------------------------------------------------------

@router.get("/{id}", dependencies=[Depends(require_permission("ea_request", "read"))])
async def get_request(id: str, db: AsyncSession = Depends(get_db)):
    try:
        # Support lookup by UUID (id column) or by request_id (e.g. EA250161)
        data_result = await db.execute(
            text(
                "SELECT r.*, "
                "  p.name AS project_name, "
                "  COALESCE(p.pm, '') AS pm, "
                "  COALESCE(p.pm_itcode, '') AS pm_itcode, "
                "  COALESCE(p.dt_lead, '') AS dt_lead, "
                "  COALESCE(p.dt_lead_itcode, '') AS dt_lead_itcode, "
                "  COALESCE(p.it_lead, '') AS it_lead, "
                "  COALESCE(p.it_lead_itcode, '') AS it_lead_itcode, "
                "  '' AS project_source, "
                "  tm_req.name AS requester_display_name "
                "FROM eam.eam_request r "
                "LEFT JOIN eam.eam_project p ON r.project_id = p.project_id OR r.project_id = p.id::text "
                "LEFT JOIN eam.eam_bigea_team_members tm_req ON tm_req.itcode = r.requester "
                "WHERE r.request_id = :rid OR r.id::text = :rid LIMIT 1"
            ),
            {"rid": id},
        )
        row = data_result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Request not found")
        request_data = dict(row._mapping)

        def _fmt_person(name: str | None, itcode: str | None) -> str:
            """Format as 'Name (itcode)' when both are available."""
            name = (name or "").strip()
            itcode = (itcode or "").strip()
            if itcode:
                import re as _re
                name = _re.sub(rf"\s*\({_re.escape(itcode)}\)", "", name).strip()
            if name and itcode:
                return f"{name} ({itcode})"
            return name or itcode

        request_data["_pm_formatted"]        = _fmt_person(request_data.get("pm"),      request_data.get("pm_itcode"))
        request_data["_dt_lead_formatted"]   = _fmt_person(request_data.get("dt_lead"), request_data.get("dt_lead_itcode"))
        request_data["_it_lead_formatted"]   = _fmt_person(request_data.get("it_lead"), request_data.get("it_lead_itcode"))
        request_data["_requester_formatted"] = _fmt_person(
            request_data.get("requester_display_name"), request_data.get("requester")
        )

        # Format assign_reviewer itcodes as "Name (itcode)"
        reviewer_itcodes = request_data.get("assign_reviewer") or []
        if isinstance(reviewer_itcodes, str):
            reviewer_itcodes = [reviewer_itcodes] if reviewer_itcodes else []
        if reviewer_itcodes:
            rv_result = await db.execute(
                text(
                    "SELECT itcode, name FROM eam.eam_bigea_team_members "
                    "WHERE itcode = ANY(:itcodes)"
                ),
                {"itcodes": list(reviewer_itcodes)},
            )
            rv_name_map = {r.itcode: r.name for r in rv_result.fetchall()}
        else:
            rv_name_map = {}
        request_data["_reviewer_formatted"] = ", ".join(
            _fmt_person(rv_name_map.get(itc), itc) for itc in reviewer_itcodes
        )

        # Use the actual request_id for attachment lookup
        actual_request_id = request_data.get("request_id", id)
        att_result = await db.execute(
            text(
                "SELECT DISTINCT ON (a.id) "
                "a.id, a.attachment_name, a.biz_type, a.app_arch_type, a.original_name, "
                "a.create_at, a.create_by, "
                "c.id as ai_check_id, c.result as ai_result, c.create_at as ai_check_at "
                "FROM eam.eam_request_attachment a "
                "LEFT JOIN eam.eam_arch_ai_check c ON c.attachment_uuid = a.id "
                "WHERE a.request_id = :rid "
                "ORDER BY a.id, c.create_at DESC NULLS LAST"
            ),
            {"rid": actual_request_id},
        )
        attachment_rows = [dict(r._mapping) for r in att_result.fetchall()]

        def extract_file_name(path: str | None) -> str:
            if not path:
                return ""
            parts = path.split("/")
            return parts[-1]

        def parse_ai_result(result: Any) -> Any:
            if result is None:
                return None
            try:
                return json.loads(result) if isinstance(result, str) else result
            except (json.JSONDecodeError, TypeError):
                return None

        def map_attachment(r: dict) -> dict:
            ai_result = parse_ai_result(r.get("ai_result"))
            ai_score = None
            if isinstance(ai_result, dict):
                oe = ai_result.get("overall_evaluation")
                if isinstance(oe, dict):
                    ai_score = oe.get("score")
            attachment_name = r.get("attachment_name") or ""
            return {
                "id": r.get("id"),
                "fileName": extract_file_name(attachment_name),
                "originalName": r.get("original_name") or None,
                "filePath": attachment_name,
                "attachmentName": attachment_name,
                "uploadBy": r.get("create_by") or "",
                "createdAt": r.get("create_at"),
                "aiScore": ai_score,
                "aiResult": ai_result,
                "aiCheckId": r.get("ai_check_id"),
                "evaluatedAt": r.get("ai_check_at"),
                "appArchType": r.get("app_arch_type"),
                "bizType": r.get("biz_type"),
            }

        app_diagrams = [map_attachment(r) for r in attachment_rows if r.get("biz_type") == "App_Arch"]
        tech_diagrams = [map_attachment(r) for r in attachment_rows if r.get("biz_type") == "Tech_Arch"]
        attachments = [map_attachment(r) for r in attachment_rows if r.get("biz_type") == "Proj_Intro"]

        return {
            **_map_request(request_data),
            "pmName": request_data["_pm_formatted"],
            "dtLeadName": request_data["_dt_lead_formatted"],
            "itLeadName": request_data["_it_lead_formatted"],
            "requestorName": request_data.get("requester") or "",
            "reviewerName": request_data["_reviewer_formatted"],
            "assignReviewer": list(request_data.get("assign_reviewer") or []),
            "projectSource": request_data.get("project_source"),
            "appDiagrams": app_diagrams,
            "techDiagrams": tech_diagrams,
            "attachments": attachments,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch request") from e


# ---------------------------------------------------------------------------
# POST / — Create new EA request
# ---------------------------------------------------------------------------

@router.post("", status_code=201, dependencies=[Depends(require_permission("ea_request", "write"))])
async def create_request(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    try:
        project_id = body.get("projectId")
        if not project_id:
            raise HTTPException(status_code=400, detail="projectId is required")

        request_id = await _generate_request_id()

        assign_reviewer = body.get("assignReviewer") or []

        # Use the authenticated user as the creator
        created_by = user.id

        await db.execute(
            text(
                "INSERT INTO eam.eam_request "
                "(request_id, project_id, review_scope, ws_phase_name, requester, "
                "status, link, assign_reviewer, organization, request_desc, "
                "create_by, create_at, update_at) "
                "VALUES (:request_id, :project_id, :review_scope, :ws_phase, :requester, "
                "'Draft', :link, :assign_reviewer, :organization, :request_desc, "
                ":created_by, NOW(), NOW())"
            ),
            {
                "request_id": request_id,
                "project_id": project_id,
                "review_scope": body.get("reviewScope"),
                "ws_phase": body.get("wsPhase"),
                "requester": body.get("requester"),
                "link": body.get("link"),
                "assign_reviewer": assign_reviewer,
                "organization": body.get("organization"),
                "request_desc": body.get("requestDesc"),
                "created_by": created_by,
            },
        )

        # Log the process
        await db.execute(
            text(
                "INSERT INTO eam.eam_request_process_log "
                "(request_id, action, comment, operator, create_at) "
                "VALUES (:request_id, 'Created', 'Request created', :operator, NOW())"
            ),
            {"request_id": request_id, "operator": created_by},
        )

        await db.commit()

        audit_allow(
            user=user,
            action="create",
            resource_type="ea_request",
            resource_id=request_id,
        )

        # Fetch the created row to return
        result = await db.execute(
            text(
                "SELECT r.*, "
                "  p.name AS project_name, "
                "  COALESCE(p.pm, '') AS pm, "
                "  COALESCE(p.pm_itcode, '') AS pm_itcode, "
                "  COALESCE(p.dt_lead, '') AS dt_lead, "
                "  COALESCE(p.dt_lead_itcode, '') AS dt_lead_itcode, "
                "  COALESCE(p.it_lead, '') AS it_lead, "
                "  COALESCE(p.it_lead_itcode, '') AS it_lead_itcode "
                "FROM eam.eam_request r "
                "LEFT JOIN eam.eam_project p ON r.project_id = p.project_id OR r.project_id = p.id::text "
                "WHERE r.request_id = :rid LIMIT 1"
            ),
            {"rid": request_id},
        )
        created = dict(result.fetchone()._mapping)
        return _map_request(created)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.warning("Failed to create EA request: %s", e)

        raise HTTPException(status_code=500, detail="Failed to create EA request") from e


# ---------------------------------------------------------------------------
# PUT /{id} — Update EA request
# ---------------------------------------------------------------------------

@router.put("/{id}", dependencies=[Depends(require_permission("ea_request", "write"))])
async def update_request(
    id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    try:
        # Find existing
        existing_result = await db.execute(
            text("SELECT * FROM eam.eam_request WHERE request_id = :rid LIMIT 1"),
            {"rid": id},
        )
        existing = existing_result.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Request not found")
        existing_dict = dict(existing._mapping)

        # ── Authorization: record-level enforcement ────────────────
        #
        # 1. EA_Admin → bypass all ownership checks
        # 2. EA_Reviewer updating review fields on an assigned request
        #    in "Complete EA Review" status → allow only review fields
        # 3. Creator updating own request → allow
        # 4. Otherwise → 403
        #

        # Fields that only a reviewer (or admin) may set
        REVIEW_FIELDS = {"reviewResult", "statusRemark"}
        # Fields that signal this is a review-completion update
        body_keys = set(body.keys()) - {"updatedBy", "status"}

        is_review_update = bool(body_keys & REVIEW_FIELDS) and body_keys <= REVIEW_FIELDS

        if not user.is_admin:
            # Reviewer-specific update (e.g., completing review)
            if is_review_update and user.is_reviewer:
                await check_reviewer_assignment(user, id, db)
                audit_allow(
                    user=user,
                    action="review_update",
                    resource_type="ea_request",
                    resource_id=id,
                )
            else:
                # Creator-only path
                await check_request_creator(user, id, db)
                audit_allow(
                    user=user,
                    action="update",
                    resource_type="ea_request",
                    resource_id=id,
                )
        else:
            audit_allow(
                user=user,
                action="update",
                resource_type="ea_request",
                resource_id=id,
            )

        set_clauses: list[str] = ["update_at = NOW()"]
        params: dict[str, Any] = {"rid": id}

        # Read existing status FIRST (used in submit validation below)
        existing_status = _normalize_request_status(existing_dict.get("status"))

        if "status" in body:
            body["status"] = _normalize_request_status(body.get("status"))

        # ── Submit-specific validation ─────────────────────────────
        new_status_raw = body.get("status")
        if new_status_raw == "Submitted" and not user.is_admin:
            if existing_status != "Draft":
                raise HTTPException(
                    status_code=400,
                    detail=f"Only Draft requests can be submitted (current: {existing_status})",
                )
            if existing_dict.get("requester") != user.id:
                raise HTTPException(
                    status_code=403,
                    detail="Only the requester can submit this request",
                )

            # Process gate: questionnaire -> concern identification -> artifact selection
            # must be completed before a request can be submitted.
            target_project_id = body.get("projectId") or existing_dict.get("project_id")
            avdm_result = await db.execute(
                text(
                    "SELECT evaluation, artifact_selection, "
                    "questionnaire_confirmed_at, concern_requirement_confirmed_at, artifact_requirement_confirmed_at "
                    "FROM eam.avdm_project_assessment "
                    "WHERE project_id = :pid LIMIT 1"
                ),
                {"pid": target_project_id},
            )
            avdm_row = avdm_result.mappings().first()
            if not avdm_row or not avdm_row.get("evaluation"):
                raise HTTPException(
                    status_code=400,
                    detail="Please complete AVDM questionnaire and concern identification before submitting request",
                )
            if not avdm_row.get("questionnaire_confirmed_at"):
                raise HTTPException(
                    status_code=400,
                    detail="Please confirm questionnaire before submitting request",
                )
            if not avdm_row.get("concern_requirement_confirmed_at"):
                raise HTTPException(
                    status_code=400,
                    detail="Please confirm concern requirement before submitting request",
                )
            if not avdm_row.get("artifact_requirement_confirmed_at"):
                raise HTTPException(
                    status_code=400,
                    detail="Please confirm artifact requirement before submitting request",
                )
            if not (avdm_row.get("artifact_selection") or []):
                raise HTTPException(
                    status_code=400,
                    detail="Please complete artifact selection before submitting request",
                )

        # ── Returned by EA: action → status mapping ───────────────────────────
        # The UI sends status="Returned by EA" as an action identifier.
        # The actual DB status transitions back to "Draft"; review_result = "Returned by EA".
        is_return_action = new_status_raw == "Returned by EA"
        if is_return_action:
            if not user.is_admin:
                raise HTTPException(
                    status_code=403,
                    detail="Only EA admins can return review requests",
                )
            if existing_status != "Submitted":
                raise HTTPException(
                    status_code=400,
                    detail=f"Only Submitted requests can be returned (current: {existing_status})",
                )
            # Map action → actual DB status + review result
            body["status"] = "Draft"
            body["reviewResult"] = "Returned by EA"
            body["updatedBy"] = user.id
            new_status_raw = "Draft"

        # ── Complete EA Review: Approved / Approved with Exception / Not Passed ──────
        # The UI sends status="Completed" + reviewResult = one of the valid results.
        # The log action should be the reviewResult value, not "Completed".
        COMPLETE_REVIEW_RESULTS = {"Approved", "Approved with Exception", "Not Passed"}
        RESULTS_REQUIRING_COMMENT = {"Approved with Exception", "Not Passed"}
        complete_review_result = body.get("reviewResult") if new_status_raw == "Completed" else None
        is_complete_action = complete_review_result in COMPLETE_REVIEW_RESULTS
        if is_complete_action:
            if existing_status != "In Progress":
                raise HTTPException(
                    status_code=400,
                    detail=f"Only In Progress requests can be completed (current: {existing_status})",
                )
            if complete_review_result in RESULTS_REQUIRING_COMMENT:
                status_remark = (body.get("statusRemark") or "").strip()
                if not status_remark:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Comments is required when review result is '{complete_review_result}'",
                    )
            if not user.is_admin:
                # Must be one of the assigned reviewers
                await check_reviewer_assignment(user, id, db)
            body["updatedBy"] = user.id

        # ── Accepted by EA: action → status mapping ───────────────────────────
        # The UI sends status="Accepted by EA" as an action identifier.
        # The actual DB status transitions to "In Progress"; review_result = "Accepted by EA".
        is_accept_action = new_status_raw == "Accepted by EA"
        if is_accept_action:
            if not user.is_admin:
                raise HTTPException(
                    status_code=403,
                    detail="Only EA admins can accept review requests",
                )
            if existing_status != "Submitted":
                raise HTTPException(
                    status_code=400,
                    detail=f"Only Submitted requests can be accepted (current: {existing_status})",
                )
            if not (body.get("assignReviewer") or []):
                raise HTTPException(
                    status_code=400,
                    detail="Assign Reviewer is required to accept a request",
                )
            # Map action → actual DB status + review result
            body["status"] = "In Progress"
            body["reviewResult"] = "Accepted by EA"
            body["updatedBy"] = user.id  # use real operator, not "System"
            new_status_raw = "In Progress"

        field_map = {
            "projectId": "project_id",
            "reviewScope": "review_scope",
            "wsPhase": "ws_phase_name",
            "requester": "requester",
            "status": "status",
            "link": "link",
            "assignReviewer": "assign_reviewer",
            "reviewResult": "review_result",
            "organization": "organization",
            "requestDesc": "request_desc",
            "statusRemark": "status_remark",
            "updatedBy": "update_by",
            "processId": "process_id",
        }

        # Auto-set process_id=10000 when submitting
        if new_status_raw == "Submitted" and "processId" not in body:
            body["processId"] = "10000"
        for api_key, db_col in field_map.items():
            if api_key in body:
                set_clauses.append(f"{db_col} = :u_{db_col}")
                params[f"u_{db_col}"] = body[api_key]

        new_status = body.get("status")
        updated_by = body.get("updatedBy")
        # NOTE: existing_status was already set above (before submit validation)

        # Track status change
        if new_status and new_status != existing_status:
            set_clauses.append("status_changed_by = :u_scb")
            set_clauses.append("status_changed_at = NOW()")
            params["u_scb"] = updated_by

            # Ensure a "Created" log exists (may be missing for legacy data)
            created_check = await db.execute(
                text(
                    "SELECT 1 FROM eam.eam_request_process_log "
                    "WHERE request_id = :rid AND action = 'Created' LIMIT 1"
                ),
                {"rid": id},
            )
            if not created_check.fetchone():
                await db.execute(
                    text(
                        "INSERT INTO eam.eam_request_process_log "
                        "(request_id, action, comment, operator, create_at) "
                        "VALUES (:request_id, 'Created', 'Request created', :operator, :created_at)"
                    ),
                    {
                        "request_id": id,
                        "operator": existing_dict.get("create_by") or user.id,
                        "created_at": existing_dict.get("create_at"),
                    },
                )

            # Use the status value directly as action when it's a known transition.
            # For "Accepted by EA", "Returned by EA" and complete results, the action name
            # differs from or is more specific than the stored status.
            if is_complete_action:
                log_action = complete_review_result  # e.g. "Approved", "Not Passed"
            elif is_accept_action:
                log_action = "Accepted by EA"
            elif is_return_action:
                log_action = "Returned by EA"
            elif new_status in ("Submitted", "In Progress", "Completed", "Deleted"):
                log_action = new_status
            else:
                log_action = f"Status changed: {existing_status} -> {new_status}"

            await db.execute(
                text(
                    "INSERT INTO eam.eam_request_process_log "
                    "(request_id, action, comment, operator, create_at) "
                    "VALUES (:request_id, :action, :comment, :operator, NOW())"
                ),
                {
                    "request_id": id,
                    "action": log_action,
                    "comment": body.get("statusRemark"),
                    "operator": updated_by or user.id,
                },
            )

        update_sql = f"UPDATE eam.eam_request SET {', '.join(set_clauses)} WHERE request_id = :rid"
        await db.execute(text(update_sql), params)
        await db.commit()

        # Return updated row
        result = await db.execute(
            text(
                "SELECT r.*, "
                "  p.name AS project_name, "
                "  COALESCE(p.pm, '') AS pm, "
                "  COALESCE(p.pm_itcode, '') AS pm_itcode, "
                "  COALESCE(p.dt_lead, '') AS dt_lead, "
                "  COALESCE(p.dt_lead_itcode, '') AS dt_lead_itcode, "
                "  COALESCE(p.it_lead, '') AS it_lead, "
                "  COALESCE(p.it_lead_itcode, '') AS it_lead_itcode, "
                "  rp.name AS requester_name "
                "FROM eam.eam_request r "
                "LEFT JOIN eam.eam_project p ON r.project_id = p.project_id OR r.project_id = p.id::text "
                "LEFT JOIN eam.resource_pool rp ON rp.itcode = r.requester "
                "WHERE r.request_id = :rid LIMIT 1"
            ),
            {"rid": id},
        )
        updated = dict(result.fetchone()._mapping)
        mapped = _map_request(updated)

        requester_itcode = updated.get("requester") or ""
        requester_name = updated.get("requester_name") or requester_itcode

        # ── Send email notification on submit ──────────────────────
        if is_accept_action:
            try:
                from app.config import settings as _cfg
                pm_itcode = updated.get("pm_itcode") or ""
                dt_lead_itcode = updated.get("dt_lead_itcode") or ""
                it_lead_itcode = updated.get("it_lead_itcode") or ""
                domain = _cfg.EMAIL_DOMAIN

                raw_reviewers = updated.get("assign_reviewer") or []
                if isinstance(raw_reviewers, str):
                    import re as _re
                    raw_reviewers = [v.strip() for v in _re.split(r"[,{}]", raw_reviewers) if v.strip()]
                reviewer_emails = ";".join(f"{r}{domain}" for r in raw_reviewers if r)

                request_id_str = updated.get("request_id", "")
                project_id_str = updated.get("project_id", "")
                project_name_str = updated.get("project_name") or ""

                status_changed_ts = updated.get("status_changed_at")
                from datetime import datetime as _dt
                if status_changed_ts:
                    status_changed_str = (
                        status_changed_ts.strftime("%Y-%m-%d %H:%M:%S")
                        if isinstance(status_changed_ts, _dt)
                        else str(status_changed_ts)[:19]
                    )
                else:
                    status_changed_str = _dt.now().strftime("%Y-%m-%d %H:%M:%S")

                request_url = f"{_cfg.SITE_URL.rstrip('/')}/ea-review/request/{id}"
                link_text = f"{request_id_str} - {project_id_str}"
                if project_name_str:
                    link_text += f" - {project_name_str}"

                reviewer_display = ", ".join(raw_reviewers)

                base_payload = {
                    "requester": requester_name,
                    "requestId": request_id_str,
                    "requestName": link_text,
                    "projectId": project_id_str,
                    "projectName": project_name_str,
                    "reviewScope": updated.get("review_scope", ""),
                    "wsPhaseName": updated.get("ws_phase_name", ""),
                    "statusChangedAt": status_changed_str,
                    "status": "In Progress",
                    "reviewResult": "Accepted by EA",
                    "statusRemark": body.get("statusRemark", ""),
                    "assignReviewer": reviewer_display,
                    "linkUrl": request_url,
                }

                # --- Notify email: to requester ---
                to_email = f"{requester_itcode}{domain}" if requester_itcode else ""
                if to_email:
                    cc_parts: list[str] = [_cfg.EMAIL_DEFAULT_CC]
                    for itcode in [pm_itcode, dt_lead_itcode, it_lead_itcode]:
                        if itcode:
                            cc_parts.append(f"{itcode}{domain}")
                    notify_payload = {
                        **base_payload,
                        "notifyContentVar": "Please reach your assigned architect to schedule the EA review.",
                    }
                    await send_email(
                        to=to_email,
                        subject=f"[AxisArch] Your request {request_id_str} has been Accepted by EA.",
                        payload=notify_payload,
                        template_code="EAReviewRequest",
                        template_tag="EAReviewRequestNotify",
                        cc=";".join(cc_parts),
                    )
                    logger.info("Accept notify email dispatched to %s for request %s", to_email, request_id_str)

                # --- Remind email: to assigned reviewers ---
                if reviewer_emails:
                    remind_cc_parts: list[str] = [_cfg.EMAIL_DEFAULT_CC]
                    for itcode in [pm_itcode, dt_lead_itcode, it_lead_itcode, requester_itcode]:
                        if itcode:
                            remind_cc_parts.append(f"{itcode}{domain}")
                    await send_email(
                        to=reviewer_emails,
                        subject=f"[AxisArch] EA Review Request {request_id_str} is waiting for your review.",
                        payload=base_payload,
                        template_code="EAReviewRequest",
                        template_tag="EAReviewRequestReminder",
                        cc=";".join(remind_cc_parts),
                    )
                    logger.info("Accept remind email dispatched to %s for request %s", reviewer_emails, request_id_str)

            except Exception as email_err:
                logger.warning("Failed to send accept notification emails: %s", email_err)

        if is_return_action:
            try:
                from app.config import settings as _cfg
                pm_itcode = updated.get("pm_itcode") or ""
                dt_lead_itcode = updated.get("dt_lead_itcode") or ""
                it_lead_itcode = updated.get("it_lead_itcode") or ""
                domain = _cfg.EMAIL_DOMAIN
                to_email = f"{requester_itcode}{domain}" if requester_itcode else ""
                if to_email:
                    cc_parts: list[str] = [_cfg.EMAIL_DEFAULT_CC]
                    for itcode in [pm_itcode, dt_lead_itcode, it_lead_itcode]:
                        if itcode:
                            cc_parts.append(f"{itcode}{domain}")

                    request_id_str = updated.get("request_id", "")
                    project_id_str = updated.get("project_id", "")
                    project_name_str = updated.get("project_name") or ""

                    status_changed_ts = updated.get("status_changed_at")
                    from datetime import datetime as _dt
                    if status_changed_ts:
                        status_changed_str = (
                            status_changed_ts.strftime("%Y-%m-%d %H:%M:%S")
                            if isinstance(status_changed_ts, _dt)
                            else str(status_changed_ts)[:19]
                        )
                    else:
                        status_changed_str = _dt.now().strftime("%Y-%m-%d %H:%M:%S")

                    request_url = f"{_cfg.SITE_URL.rstrip('/')}/ea-review/request/{id}"
                    link_text = f"{request_id_str} - {project_id_str}"
                    if project_name_str:
                        link_text += f" - {project_name_str}"

                    email_payload = {
                        "requester": requester_name,
                        "requestId": request_id_str,
                        "requestName": link_text,
                        "projectId": project_id_str,
                        "projectName": project_name_str,
                        "reviewScope": updated.get("review_scope", ""),
                        "wsPhaseName": updated.get("ws_phase_name", ""),
                        "statusChangedAt": status_changed_str,
                        "status": "Draft",
                        "reviewResult": "Returned by EA",
                        "statusRemark": body.get("statusRemark", ""),
                        "assignReviewer": "",
                        "linkUrl": request_url,
                        "notifyContentVar": None,
                    }
                    await send_email(
                        to=to_email,
                        subject=f"[AxisArch] Your request {request_id_str} has been Returned by EA.",
                        payload=email_payload,
                        template_code="EAReviewRequest",
                        template_tag="EAReviewRequestNotify",
                        cc=";".join(cc_parts),
                    )
                    logger.info("Return notify email dispatched to %s for request %s", to_email, request_id_str)
            except Exception as email_err:
                logger.warning("Failed to send return notification email: %s", email_err)

        if is_complete_action:
            try:
                from app.config import settings as _cfg
                pm_itcode = updated.get("pm_itcode") or ""
                dt_lead_itcode = updated.get("dt_lead_itcode") or ""
                it_lead_itcode = updated.get("it_lead_itcode") or ""
                domain = _cfg.EMAIL_DOMAIN
                to_email = f"{requester_itcode}{domain}" if requester_itcode else ""
                if to_email:
                    cc_parts: list[str] = [_cfg.EMAIL_DEFAULT_CC]
                    for itcode in [pm_itcode, dt_lead_itcode, it_lead_itcode]:
                        if itcode:
                            cc_parts.append(f"{itcode}{domain}")

                    request_id_str = updated.get("request_id", "")
                    project_id_str = updated.get("project_id", "")
                    project_name_str = updated.get("project_name") or ""

                    raw_reviewers = updated.get("assign_reviewer") or []
                    if isinstance(raw_reviewers, str):
                        import re as _re
                        raw_reviewers = [v.strip() for v in _re.split(r"[,{}]", raw_reviewers) if v.strip()]
                    reviewer_display = ", ".join(raw_reviewers)

                    status_changed_ts = updated.get("status_changed_at")
                    from datetime import datetime as _dt
                    if status_changed_ts:
                        status_changed_str = (
                            status_changed_ts.strftime("%Y-%m-%d %H:%M:%S")
                            if isinstance(status_changed_ts, _dt)
                            else str(status_changed_ts)[:19]
                        )
                    else:
                        status_changed_str = _dt.now().strftime("%Y-%m-%d %H:%M:%S")

                    request_url = f"{_cfg.SITE_URL.rstrip('/')}/ea-review/request/{id}"
                    link_text = f"{request_id_str} - {project_id_str}"
                    if project_name_str:
                        link_text += f" - {project_name_str}"

                    email_payload = {
                        "requester": requester_name,
                        "requestId": request_id_str,
                        "requestName": link_text,
                        "projectId": project_id_str,
                        "projectName": project_name_str,
                        "reviewScope": updated.get("review_scope", ""),
                        "wsPhaseName": updated.get("ws_phase_name", ""),
                        "statusChangedAt": status_changed_str,
                        "status": "Completed",
                        "reviewResult": complete_review_result,
                        "statusRemark": body.get("statusRemark", ""),
                        "assignReviewer": reviewer_display,
                        "linkUrl": request_url,
                        "notifyContentVar": None,
                    }
                    await send_email(
                        to=to_email,
                        subject=f"[AxisArch] Your request {request_id_str} has been {complete_review_result}.",
                        payload=email_payload,
                        template_code="EAReviewRequest",
                        template_tag="EAReviewRequestNotify",
                        cc=";".join(cc_parts),
                    )
                    logger.info("Complete notify email dispatched to %s for request %s", to_email, request_id_str)
            except Exception as email_err:
                logger.warning("Failed to send complete notification email: %s", email_err)

        if new_status == "Submitted":
            try:
                from app.config import settings as _cfg
                pm_itcode = updated.get("pm_itcode") or ""
                dt_lead_itcode = updated.get("dt_lead_itcode") or ""
                domain = _cfg.EMAIL_DOMAIN
                to_email = f"{requester_itcode}{domain}" if requester_itcode else ""

                if not to_email:
                    logger.warning(
                        "Skipping submit email for request %s: requester field is empty", id
                    )
                else:
                    # --- CC list ---
                    cc_parts: list[str] = [_cfg.EMAIL_DEFAULT_CC]
                    for itcode in [pm_itcode, dt_lead_itcode]:
                        if itcode:
                            cc_parts.append(f"{itcode}{domain}")
                    cc_email = ";".join(cc_parts) if cc_parts else None

                    request_id_str = updated.get("request_id", "")
                    project_id_str = updated.get("project_id", "")
                    project_name_str = updated.get("project_name") or ""

                    # Format statusChangedAt from status_changed_at
                    status_changed_ts = updated.get("status_changed_at")
                    if status_changed_ts:
                        from datetime import datetime as _dt
                        if isinstance(status_changed_ts, _dt):
                            status_changed_str = status_changed_ts.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            status_changed_str = str(status_changed_ts)[:19]
                    else:
                        from datetime import datetime as _dt
                        status_changed_str = _dt.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Build request detail link (id = UUID used by frontend route)
                    from app.config import settings as _cfg
                    request_url = f"{_cfg.SITE_URL.rstrip('/')}/ea-review/request/{id}"
                    link_text = f"{request_id_str} - {project_id_str}"
                    if project_name_str:
                        link_text += f" - {project_name_str}"

                    email_payload = {
                        "requester": requester_name,
                        "requestId": request_id_str,
                        "projectId": project_id_str,
                        "projectName": project_name_str,
                        "reviewScope": updated.get("review_scope", ""),
                        "wsPhaseName": updated.get("ws_phase_name", ""),
                        "statusChangedAt": status_changed_str,
                        "status": "Submitted",
                        "assignReviewer": "",
                        "reviewResult": "",
                        "statusRemark": body.get("statusRemark", ""),
                        "requestName": link_text,
                        "linkUrl": request_url,
                        "notifyContentVar": (
                            "Thank you for submitting your EA review request. "
                            "Your request has been successfully received and is now in the processing workflow."
                        ),
                    }
                    email_result = await send_email(
                        to=to_email,
                        subject=f"[AxisArch] Your request {request_id_str} has been submitted successfully.",
                        payload=email_payload,
                        template_code="EAReviewRequest",
                        template_tag="EAReviewRequestNotify",
                        cc=cc_email,
                    )
                    logger.info("Submit email dispatched for request %s to %s: %s", request_id_str, to_email, email_result)
            except Exception as email_err:
                # Email failure must NOT roll back the DB transaction
                logger.warning("Failed to send submit notification email: %s", email_err)

        return mapped
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update EA request") from e


# ---------------------------------------------------------------------------
# DELETE /{id} — Soft delete (set status to 'Deleted')
# ---------------------------------------------------------------------------

@router.delete("/{id}", dependencies=[Depends(require_permission("ea_request", "write"))])
async def delete_request(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    try:
        # ── Authorization: creator ownership + draft status ────────
        # Admin bypasses both checks (check_request_creator returns early).
        # Normal users must own the request AND it must be in Draft status.
        request_data = await check_request_creator(user, id, db)
        await check_request_draft_status(request_data, operation="delete")

        audit_allow(
            user=user,
            action="delete",
            resource_type="ea_request",
            resource_id=id,
        )

        await db.execute(
            text(
                "UPDATE eam.eam_request SET status = 'Deleted', update_at = NOW(), "
                "status_changed_by = :uid, status_changed_at = NOW() "
                "WHERE request_id = :rid"
            ),
            {"rid": id, "uid": user.id},
        )
        await db.commit()
        return {"message": "Request deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete EA request") from e
