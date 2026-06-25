"""Tests for meeting decks router."""
from __future__ import annotations

from datetime import datetime
from .conftest import make_client, reset_overrides, FakeResult


_DECK_ROW = {
    "id": 1, "deck_id": "DECK001", "meeting_id": 1001,
    "deck_name": "EA Review Deck Q1",
    "file_path": "/decks/deck001.pptx", "s3_key": None,
    "created_by": "admin", "created_at": datetime(2025, 1, 1),
}


def _bad_db():
    from unittest.mock import AsyncMock

    async def gen():
        db = AsyncMock()
        async def _raise(*a, **kw):
            raise RuntimeError("fail")
        db.execute = _raise
        db.rollback = AsyncMock()
        yield db
    return gen


class TestListMeetingDecks:
    def test_returns_decks(self):
        client = make_client(FakeResult([_DECK_ROW]))
        resp = client.get("/api/meetings/1001/decks")
        assert resp.status_code == 200
        reset_overrides()

    def test_db_error_returns_500(self):
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user
        app.dependency_overrides[get_db] = _bad_db()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/meetings/1001/decks")
        assert resp.status_code == 500
        reset_overrides()


class TestCreateMeetingDeck:
    def test_creates_deck(self):
        client = make_client(FakeResult([_DECK_ROW]))
        resp = client.post("/api/meetings/1001/decks", json={
            "deckName": "New Deck",
        })
        assert resp.status_code in (200, 201)
        reset_overrides()


class TestDeleteMeetingDeck:
    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.delete("/api/meetings/1001/decks/NONEXISTENT")
        assert resp.status_code == 404
        reset_overrides()

    def test_deletes_deck(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user

        async def db_gen():
            db = AsyncMock()
            get_r = MagicMock()
            get_r.mappings.return_value.first.return_value = _DECK_ROW
            del_r = MagicMock()
            del_r.rowcount = 1
            call = [0]
            async def execute(*a, **kw):
                idx = call[0]; call[0] += 1
                return get_r if idx == 0 else del_r
            db.execute = execute
            db.commit = AsyncMock()
            yield db

        app.dependency_overrides[get_db] = db_gen
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/api/meetings/1001/decks/DECK001")
        assert resp.status_code == 200
        reset_overrides()
