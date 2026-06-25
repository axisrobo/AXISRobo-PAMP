"""Master Data endpoint tests — Priority 3."""
import pytest


@pytest.mark.readonly
@pytest.mark.priority3
class TestMasterData:
    def test_data_classification(self, client):
        resp = client.get("/api/master-data/data-classification")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)

    def test_data_centers(self, client):
        resp = client.get("/api/master-data/data-centers")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)

    def test_companies(self, client):
        resp = client.get("/api/master-data/companies")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)

    def test_companies_search(self, client):
        resp = client.get("/api/master-data/companies", params={"search": "test"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_legal_entities(self, client):
        resp = client.get("/api/master-data/legal-entities")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)

    def test_legal_entities_with_appId(self, client):
        # Get a real appId from existing data
        entities = client.get("/api/master-data/legal-entities").json()
        if not entities:
            pytest.skip("No legal entities")
        app_id = entities[0].get("appId")
        if not app_id:
            pytest.skip("No appId in legal entities")
        resp = client.get("/api/master-data/legal-entities", params={"appId": app_id})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_help_files(self, client):
        resp = client.get("/api/master-data/help-files")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
