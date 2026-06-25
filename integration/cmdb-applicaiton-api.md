# CMDB Application API Documentation

## Overview

The CMDB Application API enables querying application CI records with flexible filter options and customizable field selection. Requests support pagination, multiple filter conditions, and custom views. Authorization is required for access.

---

## Endpoint

```
POST <configured-cmdb-endpoint>/api/v2/ci-query/search/1
```

---

## Authentication

- **Header:** `Authorization: <Bearer Token or API Key>`
- **Header:** `Content-Type: application/json`

---

## Request Parameters

### Query String
| Name   | Type   | Description     | Example |
|--------|--------|----------------|---------|
| page   | int    | Page number    | 1       |
| size   | int    | Items per page | 10      |

### Request Body (JSON)
| Name         | Type           | Description             |
|--------------|----------------|-------------------------|
| conditions   | Array<Object>  | Query filter conditions |
| showColumns  | Array<Object>  | Fields to return        |

#### Condition Object
| Name     | Type   | Description         | Example |
|----------|--------|--------------------|---------|
| column   | string | Field to filter    | "u_status" |
| option   | int    | Operator code (8 = equals) | 8 |
| value    | mixed  | Value to compare   | "Decommissioned" |

#### ShowColumn Object
| Name    | Type   | Description                | Example               |
|---------|--------|---------------------------|-----------------------|
| column  | string | Field name                | "app_full_name"      |
| label   | string | Display name (English)    | "Application Full Name" |
| labelCn | string | Display name (Chinese)    | "应用系统全称"           |
| orderNo | int    | Sort order in results     | 3                     |
| show    | int    | Visibility (1=Show, 0=Hide) | 1                  |

---

## Request Example

```json
POST /cmdb/api/v2/ci-query/search/1?page=1&size=10
Content-Type: application/json
Authorization: <token>

{
    "conditions": [
        { "column": "u_status", "option": 8, "value": "Decommissioned" }
    ],
    "showColumns": [
        { "column": "name", "label": "Application Name", "labelCn": "应用系统名称", "orderNo": 2, "show": 0 },
        // ...more fields (see table below)
    ]
}
```

---

## Response Structure

```json
{
    "success": true,
    "code": null,
    "message": null,
    "data": {
        "allFields": [],
        "ciFieldMap": {},
        "pageResult": {
            "page": {
                "number": 1,
                "size": 10,
                "totalElements": 2762
            },
            "rows": [
                {
                    "_id": "string",
                    "patch_level": "string",
                    "name": "string",
                    "app_full_name": "string",
                    "u_status": "string",
                    "short_description": "string",
                    "owned_by": "string",
                    "u_service_area": "string",
                    "appowner_orgname": "string",
                    "functionOwnerL4OrgName": "string",
                    "appPortfolioMgt": "string",
                    "appClassification": ["string", ...],
                    "applicationSolutionType": "string",
                    "u_budget_owner": "string",
                    "app_operation_owner": "string",
                    "AppOperationOwnerTower": "string",
                    "AppOperationOwnerDomain": "string",
                    "appDtOwner": "string",
                    "registerPhase": "string"
                },
                // ... more entries
            ]
        }
    },
    "timestamp": 1773906272381,
    "messageCode": null
}
```

---

## Field List

| Field                     | EN Label                         | CN Label                             | Type    | Example                                        |
|---------------------------|----------------------------------|--------------------------------------|---------|-----------------------------------------------|
| _id                       | ID                               | 主键                                 | string  | "62b9ccf2c361f9640cddaf2c"                    |
| patch_level               | Application Unified ID           | 应用ID                               | string  | "A002893"                                   |
| name                      | Application Name                 | 应用系统名称                          | string  | "312MMEBLD"                                 |
| app_full_name             | Application Full Name            | 应用系统全称                          | string  | "312 MME Build Server"                      |
| u_status                  | Current State                    | 状态                                 | string  | "Active"                                    |
| short_description         | Description                      | 描述                                 | string  | "Ubuntu servers for ... "                   |
| owned_by                  | Application IT Owner             | 应用系统负责人                         | string  | "w36195"                                    |
| u_service_area            | Function (Value Chain)           | 系统功能(价值链)                      | string  | "Others"                                    |
| appowner_orgname          | Application Owner Tower          | 应用系统负责人所属部门信息               | string  | "IDG AI Ecosystem AI Cloud Engineering"     |
| functionOwnerL4OrgName    | Application Owner Domain         | 应用系统负责人所在部门                  | string  | "IDG AI Ecosystem Development"              |
| appPortfolioMgt           | Application Portfolio Management | 应用组合管理                           | string  | "Migrate"                                   |
| appClassification         | Application Classification       | 应用分类                              | [string]| ["Others"]                                  |
| applicationSolutionType   | Application Solution Type        | 应用解决方案类型                       | string  | "Package"                                   |
| u_budget_owner            | Application Ownership            | 应用所属部门                           | string  | "Shadow"                                    |
| app_operation_owner       | App Operation Owner              | 应用系统Operation负责人                | string  | "w36195"                                    |
| AppOperationOwnerTower    | App Operation Owner Tower        | 应用系统Operation负责人所属部门信息      | string  | "IDG AI Ecosystem AI Cloud Engineering"     |
| AppOperationOwnerDomain   | App Operation Owner Domain       | 应用系统Operation负责人所在部门          | string  | "IDG AI Ecosystem Development"              |
| appDtOwner                | Application DT Owner             | 应用DT负责人                            | string  | "" (empty possible)                         |
| registerPhase             | Registration & Certification Status | 注册与认证阶段                     | string  | "Registered"                                |

---

## Response Example

```json
{
    "success": true,
    "data": {
        "pageResult": {
            "page": {
                "number": 1,
                "size": 10,
                "totalElements": 2762
            },
            "rows": [
                {
                    "_id": "62b9ccf2c361f9640cddaf2c",
                    "name": "312MMEBLD",
                    "app_full_name": "312 MME Build Server",
                    "u_status": "Active",
                    "short_description": "Ubuntu servers for engineering and MBG product development to build software"
                }
                // ... more entries
            ]
        }
    },
    "timestamp": 1773906272381
}
```

---

## Typical Use Cases

- Search for applications by filters (status, owner, classification, etc.)
- Page through CI (Configuration Items) lists
- Customize result fields for integration/display

---

## Notes

- Provide a valid `Authorization` token for requests.
- The "option" code in "conditions" field may vary (8 = equals).
- Use `showColumns` to control the fields in query results.
- Results are paginated; use the `pageResult.page` fields to navigate.
