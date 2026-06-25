from app.architecture_review.ea_requests import (
    _map_request,
    _normalize_request_status,
    _normalize_request_status_filter,
)


def test_normalize_request_status_from_uppercase():
    assert _normalize_request_status("DRAFT") == "Draft"
    assert _normalize_request_status("SUBMITTED") == "Submitted"
    assert _normalize_request_status("IN PROGRESS") == "In Progress"


def test_normalize_request_status_filter_from_mixed_case_csv():
    
    assert _normalize_request_status_filter("Draft,SUBMITTED, in progress ") == "draft,submitted,in progress"


def test_map_request_normalizes_status_value():
    result = _map_request(
        {
            "id": 1,
            "request_id": "REQ-1",
            "project_id": "P-1",
            "project_name": "Test Project",
            "pm": "pm01",
            "status": "DRAFT",
            "review_scope": "ALL",
            "ws_phase_name": None,
            "requester": "user01",
            "assign_reviewer": ["reviewer01"],
            "review_result": None,
            "organization": "DTIT",
            "request_desc": None,
            "link": None,
            "create_at": None,
            "update_at": None,
            "create_by": "user01",
            "status_changed_by": None,
            "status_changed_at": None,
            "dt_lead": None,
        }
    )

    assert result["status"] == "Draft"
    assert result["reviewerName"] == "reviewer01"
