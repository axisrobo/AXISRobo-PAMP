from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.architecture_review.ai.service import process_attachment_ai_check
from tests.conftest import make_user


class _FetchOneResult:
    def __init__(self, value):
        self._value = value

    def fetchone(self):
        return SimpleNamespace(_mapping={"app_arch_type": self._value})


@pytest.mark.asyncio
async def test_process_attachment_ai_check_persists_raw_and_structured_results(monkeypatch):
    user = make_user()
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[_FetchOneResult("New_App"), None, None, None])
    db.commit = AsyncMock()

    async def _fake_run_internal_workflow(**kwargs):
        return {
            "result": {
                "title": "Sample Review",
                "overall_evaluation": {
                    "score": 8.5,
                    "summary": "Looks good",
                },
                "issues": [],
                "recommendations": [],
            },
            "content_extract_result": {
                "applications": [
                    {
                        "id": "A000001",
                        "name": "App One",
                        "functions": ["Core"],
                        "standard_id": "A000001",
                        "id_is_standard": True,
                        "application_status": "New",
                    }
                ],
                "interactions": [
                    {
                        "source_app_id": "A000001",
                        "target_app_id": "A000002",
                        "interaction_type": "Event",
                        "direction": "one_way",
                        "source_function": "",
                        "target_function": "",
                        "interface_status": "New",
                        "business_object": "Order",
                    }
                ],
            },
        }

    monkeypatch.setattr(
        "app.architecture_review.ai.service_common.run_internal_workflow",
        _fake_run_internal_workflow,
    )
    monkeypatch.setattr("app.architecture_review.ai.service_common.agent_watch.send_request", lambda **kwargs: None)
    monkeypatch.setattr("app.architecture_review.ai.service_common.agent_watch.receive_response", lambda **kwargs: None)
    monkeypatch.setattr("app.architecture_review.ai.service_common.agent_watch.generate_trace_id", lambda: "trace-1")
    monkeypatch.setattr("app.architecture_review.ai.service_common.agent_watch.generate_span_id", lambda: "span-1")

    result = await process_attachment_ai_check(
        db=db,
        user=user,
        request_id="EA1001",
        biz_type="App_Arch",
        language="en",
        attachment_name="pm/eam/app/1-sample.png",
        attachment_uuid="uuid-1",
        file_content=b"png",
    )

    assert result["score"] == 8.5
    assert result["attachmentUuid"] == "uuid-1"
    assert result["result"]["title"] == "Sample Review"
    assert db.execute.await_count == 4
    app_insert_payload = db.execute.await_args_list[1].args[1]
    interaction_insert_payload = db.execute.await_args_list[2].args[1]
    insert_payload = db.execute.await_args_list[-1].args[1]
    assert app_insert_payload["status"] == "Waiting to Confirm"
    assert interaction_insert_payload["status"] == "Waiting to Confirm"
    assert insert_payload["check_cost"] >= 0
    assert insert_payload["total_cost"] >= insert_payload["check_cost"]
    db.commit.assert_awaited_once()
