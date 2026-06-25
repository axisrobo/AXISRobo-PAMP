"""CSV export helpers with formula injection prevention."""
import csv
import io
from fastapi.responses import StreamingResponse


def sanitize_cell(value) -> str:
    """Prevent CSV formula injection."""
    if value is None:
        return ""
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@"):
        s = "'" + s
    return s


def build_csv_response(rows: list[dict], headers: list[str], filename: str) -> StreamingResponse:
    """Create a CSV StreamingResponse with BOM and Content-Disposition."""
    buf = io.StringIO()
    buf.write("\ufeff")  # UTF-8 BOM
    writer = csv.writer(buf)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([sanitize_cell(row.get(h, "")) for h in headers])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
