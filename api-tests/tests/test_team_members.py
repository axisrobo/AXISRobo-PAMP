"""Team Members endpoint tests — Priority 3."""
import pytest
from helpers.pagination import assert_paginated, assert_has_keys


MEMBER_KEYS = ["itcode", "name", "workerType"]


@pytest.mark.readonly
@pytest.mark.priority3
class TestTeamMembersList:
    def test_list_paginated(self, client):
        resp = client.get("/api/team-members")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body)

    def test_item_keys(self, client):
        resp = client.get("/api/team-members", params={"pageSize": 1})
        body = resp.json()
        if not body["data"]:
            pytest.skip("No team members")
        assert_has_keys(body["data"][0], MEMBER_KEYS, "team-member")

    def test_filter_itcode(self, client):
        sample = client.get("/api/team-members", params={"pageSize": 1}).json()
        if not sample["data"]:
            pytest.skip("No team members")
        itcode = sample["data"][0].get("itcode", "")
        if not itcode:
            pytest.skip("No itcode")
        resp = client.get("/api/team-members", params={"itcode": itcode[:3]})
        assert resp.status_code == 200
        assert resp.json()["total"] > 0

    def test_filter_name(self, client):
        resp = client.get("/api/team-members", params={"name": "a"})
        assert resp.status_code == 200

    def test_filter_workerType(self, client):
        resp = client.get("/api/team-members", params={"workerType": "EA Office"})
        assert resp.status_code == 200

    def test_filter_country(self, client):
        resp = client.get("/api/team-members", params={"country": "CN"})
        assert resp.status_code == 200

    def test_sort_by_name(self, client):
        resp = client.get("/api/team-members", params={
            "sortField": "name", "sortOrder": "asc", "pageSize": 10
        })
        assert resp.status_code == 200

    def test_pagination_size(self, client):
        resp = client.get("/api/team-members", params={"page": 1, "pageSize": 3})
        body = resp.json()
        assert len(body["data"]) <= 3


@pytest.mark.write
@pytest.mark.priority3
class TestTeamMembersCRUD:
    def test_create_update_delete(self, client):
        data = {
            "itcode": "__APITEST__",
            "name": "API Test Member",
            "email": "apitest@test.com",
            "workerType": "EA Office",
            "country": "CN",
        }
        resp = client.post("/api/team-members", json=data)
        assert resp.status_code == 201

        # Update
        update_resp = client.put("/api/team-members/__APITEST__", json={
            "name": "API Test Member Updated",
        })
        assert update_resp.status_code == 200

        # Delete
        del_resp = client.delete("/api/team-members/__APITEST__")
        assert del_resp.status_code == 200
