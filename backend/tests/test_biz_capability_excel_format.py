import io
from types import SimpleNamespace

import openpyxl
import pytest

biz_capability_module = pytest.importorskip("app.application_management.biz_capability")
EXPORT_HEADERS = biz_capability_module.EXPORT_HEADERS
_build_biz_capability_export_row = biz_capability_module._build_biz_capability_export_row
_extract_biz_capability_label_name = biz_capability_module._extract_biz_capability_label_name
_parse_excel_rows = biz_capability_module._parse_excel_rows
validate_biz_capability_import = biz_capability_module.validate_biz_capability_import


def _build_excel_bytes(headers: list[str], rows: list[list[object]]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None
    ws.append(headers)
    for row in rows:
        ws.append(row)

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def test_extract_biz_capability_label_name_strips_hierarchy_id_prefix():
    assert _extract_biz_capability_label_name("C.1.Product Development", 2) == "Product Development"
    assert _extract_biz_capability_label_name("C.1 Product Development", 2) == "Product Development"
    assert _extract_biz_capability_label_name("C7.HR", 2) == "HR"
    assert _extract_biz_capability_label_name("C8.Legal", 2) == "Legal"
    assert _extract_biz_capability_label_name("C9.Administration", 2) == "Administration"
    assert _extract_biz_capability_label_name("C.1.1 Portfolio & Planning Management", 3) == "Portfolio & Planning Management"
    assert _extract_biz_capability_label_name("Strategy Definition") == "Strategy Definition"
    assert _extract_biz_capability_label_name("") is None


def test_parse_excel_rows_imports_only_hierarchy_names():
    content = _build_excel_bytes(
        [
            "Domain(L1)",
            "Sub Domain(L2)",
            "Capability Group(L3)",
            "BC ID",
            "BC Name",
            "BC Name with ID",
            "BC Name CN",
            "Level",
            "Alias",
            "BC BF Description",
            "BG",
            "GEO",
            "BC Biz Owner",
            "BC Biz Team",
            "BC DT Owner",
            "BC DT Team",
        ],
        [
            [
                "C.1.Product Development",
                "",
                "",
                "C.1",
                "Product Development",
                "C.1 Product Development",
                "Strategy Definition CN",
                1,
                "",
                "",
                "Corporate",
                "Global",
                "Owner A",
                "Team A",
                "DT Owner A",
                "DT Team A",
            ],
            [
                "C.1.Product Development",
                "C.1.1 Portfolio & Planning Management",
                "",
                "C.1.1",
                "Portfolio & Planning Management",
                "C.1.1 Portfolio & Planning Management",
                "Strategy Definition CN",
                2,
                "",
                "",
                "Corporate",
                "Global",
                "Owner A",
                "Team A",
                "DT Owner A",
                "DT Team A",
            ],
            [
                "C.1.Product Development",
                "C.1.1 Portfolio & Planning Management",
                "C.1.1.1 Strategy Definition",
                "C.1.1.1",
                "Strategy Definition",
                "C.1.1.1 Strategy Definition",
                "Strategy Definition CN",
                3,
                "SD",
                "Own the product strategy",
                "Corporate",
                "Global",
                "Owner A",
                "Team A",
                "DT Owner A",
                "DT Team A",
            ]
        ],
    )

    parsed, errors = _parse_excel_rows(content, "2026")

    assert errors == []
    assert len(parsed) == 3
    target = parsed[-1]
    assert target["lv1_domain"] == "Product Development"
    assert target["lv2_sub_domain"] == "Portfolio & Planning Management"
    assert target["lv3_capability_group"] == "Strategy Definition"
    assert target["bc_description"] == "Own the product strategy"
    assert target["biz_group"] == "Corporate"
    assert target["biz_owner"] == "Owner A"
    assert target["biz_team"] == "Team A"
    assert target["dt_owner"] == "DT Owner A"
    assert target["dt_team"] == "DT Team A"
    assert target["data_version"] == "2026"


def test_parse_excel_rows_uses_bc_name_with_id_when_bc_name_missing():
    content = _build_excel_bytes(
        [
            "Domain(L1)",
            "Sub Domain(L2)",
            "Capability Group(L3)",
            "BC ID",
            "BC Name with ID",
            "Level",
        ],
        [
            [
                "C.1.Product Development",
                "",
                "",
                "C.1",
                "Product Development",
                1,
            ],
            [
                "C.1.Product Development",
                "C.1.1 Portfolio & Planning Management",
                "",
                "C.1.1",
                "C.1.1 Portfolio & Planning Management",
                2,
            ],
            [
                "C.1.Product Development",
                "C.1.1 Portfolio & Planning Management",
                "C.1.1.1 Strategy Definition",
                "C.1.1.1",
                "C.1.1.1 Strategy Definition",
                3,
            ]
        ],
    )

    parsed, errors = _parse_excel_rows(content, "2026")

    assert errors == []
    assert len(parsed) == 3
    assert parsed[-1]["bc_name"] == "Strategy Definition"


def test_build_biz_capability_export_row_combines_hierarchy_id_and_name():
    row = _build_biz_capability_export_row(
        {
            "bc_id": "C.1.4.2",
            "parent_bc_id": "C.1.4",
            "bc_name": "Sample Model Build Planning",
            "bc_name_cn": None,
            "lv1_domain": "Product Development",
            "lv2_sub_domain": "Product Design",
            "lv3_capability_group": "Sample Model Build Planning",
            "level": 3,
            "bc_description": None,
            "alias": None,
            "biz_group": None,
            "geo": None,
            "biz_owner": None,
            "biz_team": None,
            "dt_owner": None,
            "dt_team": None,
            "remark": None,
            "data_version": "2026",
        }
    )

    assert row[0] == "C.1.Product Development"
    assert row[1] == "C.1.4 Product Design"
    assert row[2] == "C.1.4.2 Sample Model Build Planning"
    assert row[3] == "C.1.4.2"
    assert row[4] == "Sample Model Build Planning"
    assert row[5] == "C.1.4.2 Sample Model Build Planning"


def test_export_to_import_round_trip_keeps_core_fields():
    source = {
        "bc_id": "C.1.4.2",
        "parent_bc_id": "C.1.4",
        "bc_name": "Sample Model Build Planning",
        "bc_name_cn": "样机建造规划",
        "lv1_domain": "Product Development",
        "lv2_sub_domain": "Product Design",
        "lv3_capability_group": "Sample Model Build Planning",
        "level": 3,
        "bc_description": "Plan and control sample model build work",
        "alias": "SMBP",
        "biz_group": "Corporate",
        "geo": "Global",
        "biz_owner": "Owner A",
        "biz_team": "Team A",
        "dt_owner": "DT Owner A",
        "dt_team": "DT Team A",
        "remark": "",
        "data_version": "2026",
    }

    parent_l1 = {
        **source,
        "bc_id": "C.1",
        "bc_name": "Product Development",
        "level": 1,
        "lv2_sub_domain": None,
        "lv3_capability_group": None,
        "parent_bc_id": "root",
    }
    parent_l2 = {
        **source,
        "bc_id": "C.1.4",
        "bc_name": "Product Design",
        "level": 2,
        "lv3_capability_group": None,
        "parent_bc_id": "C.1",
    }

    content = _build_excel_bytes(
        EXPORT_HEADERS,
        [
            _build_biz_capability_export_row(parent_l1),
            _build_biz_capability_export_row(parent_l2),
            _build_biz_capability_export_row(source),
        ],
    )
    parsed, errors = _parse_excel_rows(content, "2026")

    assert errors == []
    assert len(parsed) == 3

    imported = parsed[-1]
    assert imported["bc_id"] == source["bc_id"]
    assert imported["bc_name"] == source["bc_name"]
    assert imported["bc_name_cn"] == source["bc_name_cn"]
    assert imported["lv1_domain"] == source["lv1_domain"]
    assert imported["lv2_sub_domain"] == source["lv2_sub_domain"]
    assert imported["lv3_capability_group"] == source["lv3_capability_group"]
    assert imported["biz_group"] == source["biz_group"]
    assert imported["dt_owner"] == source["dt_owner"]
    assert imported["dt_team"] == source["dt_team"]


def test_parse_excel_rows_defaults_l1_parent_to_root_and_uses_data_version_arg():
    content = _build_excel_bytes(
        EXPORT_HEADERS,
        [
            [
                "C.1.Product Development",
                "",
                "",
                "C.1",
                "Product Development",
                "C.1 Product Development",
                "产品开发",
                1,
                "",
                "L1 description",
                "Corporate",
                "Global",
                "Owner L1",
                "Team L1",
                "DT Owner L1",
                "DT Team L1",
            ]
        ],
    )

    parsed, errors = _parse_excel_rows(content, "2026")

    assert errors == []
    assert len(parsed) == 1
    assert parsed[0]["parent_bc_id"] == "root"
    assert parsed[0]["data_version"] == "2026"


@pytest.mark.asyncio
async def test_validate_biz_capability_import_accepts_xlsm_extension():
    content = _build_excel_bytes(
        [
            "Domain(L1)",
            "Sub Domain(L2)",
            "Capability Group(L3)",
            "BC ID",
            "BC Name",
            "Level",
        ],
        [["C7.HR", "", "", "C7", "HR", 1]],
    )

    class DummyUploadFile:
        def __init__(self, filename: str, payload: bytes):
            self.filename = filename
            self._payload = payload

        async def read(self) -> bytes:
            return self._payload

    result = await validate_biz_capability_import(
        file=DummyUploadFile("biz-capability-source.xlsm", content),
        dataVersion="2026",
    )

    assert result["valid"] is True
    assert result["validRows"] == 1
