"""Dictionary Options endpoint tests — Priority 3."""
import pytest


@pytest.mark.readonly
@pytest.mark.priority3
class TestDictOptions:
    def test_list_options(self, client):
        resp = client.get("/api/dict-options")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)

    def test_list_with_categoryId(self, client):
        # First get categories
        cats = client.get("/api/dict-options/categories").json()
        if not cats:
            pytest.skip("No categories")
        cat_id = cats[0].get("categoryId")
        if not cat_id:
            pytest.skip("No categoryId")
        resp = client.get("/api/dict-options", params={"categoryId": cat_id})
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)

    def test_list_with_lang(self, client):
        resp = client.get("/api/dict-options", params={"lang": "en"})
        assert resp.status_code == 200

    def test_categories(self, client):
        resp = client.get("/api/dict-options/categories")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        if body:
            assert "categoryId" in body[0]
