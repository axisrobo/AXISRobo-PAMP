"""Quick test: send a meeting notice email to testuser@example.com"""
import asyncio
import json
import os
import sys

# Load .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

import httpx

EMAIL_SERVICE_URL = os.environ.get("EMAIL_SERVICE_URL", "")
print(f"EMAIL_SERVICE_URL: {EMAIL_SERVICE_URL}")


async def test_send():
    payload = {
        "project_id": "TEST001",
        "project_name": "测试项目",
        "project_objectives": "测试邮件功能",
        "meeting_no": 9999,
        "meeting_title": "下午2点开会通知（测试）",
        "start_time": "2026-03-18 14:00",
        "end_time": "2026-03-18 15:00",
        "location": "线上会议",
        "presenter": "Test User",
        "attendees": "testuser",
        "emailcc": "",
        "meeting_agenda": "下午2点开会，请准时参加。",
        "key_agreement_findings": "",
        "deck_links": "",
        "review_recording": "",
    }

    body = {
        "to": "testuser@example.com",
        "payload": json.dumps(payload, ensure_ascii=False),
        "subject": "【测试】下午2点开会通知",
        "appId": "ProjectManagement",
        "templateCode": "Meetings",
        "templateTag": "Minutes",
    }

    print("\n=== Request Body ===")
    print(json.dumps(body, indent=2, ensure_ascii=False))
    print("\nSending...")

    async with httpx.AsyncClient(timeout=30, verify=False) as client:
        response = await client.post(
            EMAIL_SERVICE_URL,
            json=body,
            headers={"Content-Type": "application/json"},
        )
        print(f"\nStatus: {response.status_code}")
        print(f"Response: {response.text}")


asyncio.run(test_send())
