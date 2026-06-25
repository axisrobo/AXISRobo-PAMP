# AI Architecture Review API Documentation

## Overview
This document describes how to obtain an access token and use the AI Architecture Review API in the test environment. It also details the request and response formats.

---

## 1. Obtain Access Token

**Endpoint:**
```
POST <configured-endpoint>/token
```

**Headers:**
- `Content-Type: application/x-www-form-urlencoded`
- `X-API-KEY: otZmsYQ7TU7n9wcXMIjHhxsCnj5kcGbJ`

**Body (x-www-form-urlencoded):**
- `username=api_itinvest_zbb`
- `password=XXXXX`

**Example cURL:**
```sh
curl --location '<configured-endpoint>/token' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --header 'X-API-KEY: otZmsYQ7TU7n9wcXMIjHhxsCnj5kcGbJ' \
  --data-urlencode 'username=api_itinvest_zbb' \
  --data-urlencode 'password=XXXXX'
```

---

## 2. AI Architecture Review API

**Endpoint:**
```
POST <configured-endpoint>/sit/v1/services/ea/openapi/ea/architecture/review
```

**Headers:**
- `X-API-KEY: otZmsYQ7TU7n9wcXMIjHhxsCnj5kcGbJ`
- `Authorization: <access_token>`

**Form Data:**
- `userId` (string): User ID (e.g., "hubz2")
- `language` (string): Language code (e.g., "zh")
- `reviewType` (string): Review type (e.g., "Tech_Arch")
- `appArchRuleName` (string): Architecture rule name (e.g., "New_App")
- `scenario` (string): Scenario (e.g., "EAM")
- `bizType` (string): Business type (e.g., "EAM")
- `bizOrderNo` (string): Business order number (e.g., "EA250008")
- `file` (file): Architecture diagram file to upload

**Example cURL:**
```sh
curl --location '<configured-endpoint>/sit/v1/services/ea/openapi/ea/architecture/review' \
  --header 'X-API-KEY: otZmsYQ7TU7n9wcXMIjHhxsCnj5kcGbJ' \
  --header 'Authorization: <access_token>' \
  --form 'userId="hubz2"' \
  --form 'language="zh"' \
  --form 'reviewType="Tech_Arch"' \
  --form 'appArchRuleName="New_App"' \
  --form 'scenario="AxisArch"' \
  --form 'bizType="EAM"' \
  --form 'bizOrderNo="EA250008"' \
  --form 'file=@"/path/to/your/architecture-diagram.png"'
```

---

## 3. Response Format

The API returns a JSON object with the following structure:

```
{
  "code": "string",           // Record code
  "id": number,                // Record ID
  "issues": [                  // List of detected issues
    {
      "description": "string",         // Issue description
      "dimension": "string",           // Issue dimension
      "id": "string",                  // Issue ID
      "impact": "string",              // Impact description
      "issue_type": "string",          // Issue type (e.g., must_fix)
      "priority": "string",            // Priority (e.g., high)
      "related_entities": "string",    // Related entities
      "related_relationships": "string",// Related relationships
      "suggestion": "string"            // Suggestion for resolution
    }
  ],
  "overall_evaluation": {
    "score": number,           // Overall score
    "summary": "string"        // Overall summary
  },
  "recommendations": [         // List of recommendations
    "string"
  ],
  "score_breakdown": {
    "cloud_network_completeness": { "score": number, "max": number },      // Cloud network completeness
    "connectivity": { "score": number, "max": number },                    // Connectivity
    "interaction_integration": { "score": number, "max": number },         // Interaction & integration
    "security_compliance": { "score": number, "max": number },             // Security & compliance
    "technical_component_completeness": { "score": number, "max": number },// Technical component completeness
    "terminology_expression": { "score": number, "max": number }           // Terminology expression
  },
  "title": "string"            // Architecture title
}
```

### Example Response
```
{
  "code": "",
  "id": 0,
  "issues": [
    {
      "description": "Data center and public cloud lack jurisdiction and location labels.",
      "dimension": "Entity",
      "id": "E-001",
      "impact": "Compliance assessment and data sovereignty analysis.",
      "issue_type": "must_fix",
      "priority": "High",
      "related_entities": "SY Data Center, Azure PRC",
      "related_relationships": "",
      "suggestion": "Add deployment location and jurisdiction details."
    }
  ],
  "overall_evaluation": {
    "score": 8,
    "summary": "The architecture is clear, with reasonable layering and components. Some core security details, cross-region connections, and runtime environments are missing and need to be supplemented with physical deployment and security measures."
  },
  "recommendations": [
    "Complete all data center and cloud platform location/jurisdiction information."
  ],
  "score_breakdown": {
    "cloud_network_completeness": 1.5,
    "connectivity": 0.7,
    "interaction_integration": 2,
    "security_compliance": 1.5,
    "technical_component_completeness": 1.7,
    "terminology_expression": 0.6
  },
  "title": "Example Multi-Data Center and Public Cloud Hybrid Architecture (2024)"
}
```

---

## 4. Notes
- The `Authorization` header must be set to the access token obtained from the token endpoint.
- The `X-API-KEY` is required for both endpoints.
- The file upload should be a valid architecture diagram image.

---

## 5. Contact
For further information, please contact the API provider support team.
