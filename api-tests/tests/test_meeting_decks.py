"""Meeting Decks endpoint tests — Priority 3."""
import pytest


@pytest.mark.readonly
@pytest.mark.priority3
class TestMeetingDecks:
    def test_list_returns_array(self, client):
        resp = client.get("/api/meeting-decks")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)

    def test_list_with_meetingId(self, client):
        resp = client.get("/api/meeting-decks", params={"meetingId": "1"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


@pytest.mark.write
@pytest.mark.priority3
class TestMeetingDecksCRUD:
    def test_create_and_delete(self, client):
        # Get a meeting first
        meetings = client.get("/api/meetings", params={"pageSize": 1}).json()
        if not meetings["data"]:
            pytest.skip("No meetings")
        meeting_id = str(meetings["data"][0]["meetingNo"])

        data = {
            "meetingId": meeting_id,
            "deckName": "__API_TEST_DECK__",
            "deckUrl": "https://example.com/test-deck",
        }
        resp = client.post("/api/meeting-decks", json=data)
        assert resp.status_code == 201
        created = resp.json()
        deck_id = created["id"]

        # Delete
        del_resp = client.delete(f"/api/meeting-decks/{deck_id}")
        assert del_resp.status_code == 200
