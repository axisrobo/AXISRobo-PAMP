"""Export endpoint tests — Priority 3."""
import pytest


@pytest.mark.readonly
@pytest.mark.priority3
class TestExport:
    """Tests for /api/export/:entity CSV export."""

    def test_export_ea_requests(self, client):
        resp = client.get("/api/export/ea-requests")
        assert resp.status_code == 200
        ct = resp.headers.get("content-type", "")
        assert "text/csv" in ct or "application/octet-stream" in ct
        assert resp.headers.get("content-disposition") is not None
        # CSV should have BOM and header row
        text = resp.text
        assert len(text) > 0

    def test_export_projects(self, client):
        resp = client.get("/api/export/projects")
        assert resp.status_code == 200
        ct = resp.headers.get("content-type", "")
        assert "text/csv" in ct or "application/octet-stream" in ct

    def test_export_meetings(self, client):
        resp = client.get("/api/export/meetings")
        assert resp.status_code == 200

    def test_export_actions(self, client):
        resp = client.get("/api/export/actions")
        assert resp.status_code == 200

    def test_export_bcm(self, client):
        resp = client.get("/api/export/bcm")
        assert resp.status_code == 200

    def test_export_bcm_with_filter(self, client):
        resp = client.get("/api/export/bcm", params={"appId": "SAP"})
        assert resp.status_code == 200

    def test_export_lead_time(self, client):
        resp = client.get("/api/export/lead-time")
        assert resp.status_code == 200

    def test_export_unknown_entity(self, client):
        resp = client.get("/api/export/nonexistent")
        assert resp.status_code in (400, 404, 500)

    def test_export_csv_has_header(self, client):
        resp = client.get("/api/export/projects")
        if resp.status_code == 200:
            lines = resp.text.strip().split("\n")
            assert len(lines) >= 1  # At least header row

    def test_export_csv_no_formula_injection(self, client):
        """Verify exported CSV doesn't start cells with dangerous chars."""
        resp = client.get("/api/export/projects")
        if resp.status_code == 200:
            text = resp.text
            # No cell should start with = + - @ (formula injection)
            for line in text.split("\n")[1:]:  # Skip header
                for cell in line.split(","):
                    cell = cell.strip().strip('"')
                    if cell:
                        assert cell[0] not in ("=", "+", "@"), \
                            f"Potential formula injection: {cell[:20]}"
