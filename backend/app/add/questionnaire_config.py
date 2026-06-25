"""Default questionnaire configuration for AVDM."""
from __future__ import annotations

DEFAULT_CONFIG_KEY = "default"
DEFAULT_MAPPING_CONFIG_KEY = "default"
DEFAULT_ARTIFACT_CATALOG_CONFIG_KEY = "default"
DEFAULT_VIEWPOINT_ARTIFACT_MAPPING_CONFIG_KEY = "default"


def _section_condition(
    field: str,
    *,
    equals: str | None = None,
    in_values: list[str] | None = None,
    not_equals: str | None = None,
) -> dict:
    condition: dict = {"field": field}
    if equals is not None:
        condition["equals"] = equals
    if in_values is not None:
        condition["in"] = in_values
    if not_equals is not None:
        condition["notEquals"] = not_equals
    return condition


def _section_field(
    key: str,
    label: str,
    *,
    control: str,
    options: list[dict] | None = None,
    options_source: str | None = None,
    required: bool = False,
    enabled_when: list[dict] | None = None,
    required_when: list[dict] | None = None,
    clear_when_disabled: bool = True,
    placeholder: str | None = None,
) -> dict:
    field = {
        "key": key,
        "label": label,
        "control": control,
        "options": options or [],
        "optionsSource": options_source,
        "required": required,
        "enabledWhen": enabled_when or [],
        "requiredWhen": required_when or [],
        "clearWhenDisabled": clear_when_disabled,
    }
    if placeholder is not None:
        field["placeholder"] = placeholder
    return field


def _questionnaire_section(key: str, title: str, description: str, fields: list[dict]) -> dict:
    return {
        "key": key,
        "title": title,
        "description": description,
        "fields": fields,
    }


def _yes_no_options() -> list[dict]:
    return [
        {"label": "Yes", "value": "Yes"},
        {"label": "No", "value": "No"},
    ]


def _yes_no_not_sure_options() -> list[dict]:
    return [
        {"label": "Yes", "value": "Yes"},
        {"label": "No", "value": "No"},
        {"label": "Not Sure", "value": "Not Sure"},
    ]


DEFAULT_QUESTIONNAIRE_CONFIG: dict = {
    "questionnaireSections": [
        _questionnaire_section(
            "projectScaleSection",
            "Project Scale",
            "Project scope and external interaction size.",
            [
                _section_field(
                    "applicationsInScope",
                    "How many applications are in scope?",
                    control="select",
                    options_source="applicationCountRangeOptions",
                    required=True,
                ),
                _section_field(
                    "hasExternalSystems",
                    "Does it involve external systems?",
                    control="radio",
                    options=_yes_no_options(),
                    required=True,
                ),
                _section_field(
                    "externalSystemsCount",
                    "How many external systems are involved?",
                    control="select",
                    options_source="externalSystemCountRangeOptions",
                    enabled_when=[_section_condition("hasExternalSystems", equals="Yes")],
                    required_when=[_section_condition("hasExternalSystems", equals="Yes")],
                ),
            ],
        ),
        _questionnaire_section(
            "changeScopeSection",
            "Change Scope",
            "Project delivery scope across new and modified applications.",
            [
                _section_field(
                    "hasNewApplications",
                    "Will there be new applications?",
                    control="radio",
                    options=_yes_no_options(),
                    required=True,
                ),
                _section_field(
                    "newApplicationsCount",
                    "How many new applications?",
                    control="select",
                    options_source="newApplicationCountRangeOptions",
                    enabled_when=[_section_condition("hasNewApplications", equals="Yes")],
                    required_when=[_section_condition("hasNewApplications", equals="Yes")],
                ),
                _section_field(
                    "modifiedApplicationsCount",
                    "How many applications will be modified?",
                    control="select",
                    options_source="modifiedApplicationCountRangeOptions",
                    required=True,
                ),
            ],
        ),
        _questionnaire_section(
            "complexitySection",
            "Technical Complexity",
            "Operational and technical delivery complexity factors.",
            [
                _section_field(
                    "dataCenterCount",
                    "How many data centers are involved?",
                    control="select",
                    options_source="dataCenterCountRangeOptions",
                    required=True,
                ),
                _section_field(
                    "cloudRegionScope",
                    "How many clouds/regions are involved?",
                    control="select",
                    options_source="cloudRegionScopeOptions",
                    required=True,
                ),
                _section_field(
                    "hasCrossBorderDataFlow",
                    "Does this involve cross-border data?",
                    control="radio",
                    options=_yes_no_options(),
                    required=True,
                ),
                _section_field(
                    "techStackKindsCount",
                    "How many technology stacks are involved?",
                    control="select",
                    options_source="techStackKindsCountRangeOptions",
                    required=True,
                ),
                _section_field(
                    "integrationTechKindsCount",
                    "How many integration technologies are involved?",
                    control="select",
                    options_source="integrationTechKindsCountRangeOptions",
                    required=True,
                ),
            ],
        ),
        _questionnaire_section(
            "privacyCheckpoint1Section",
            "Privacy & Data Protection - Checkpoint 1",
            "Third-party entity data handling and transfer screening.",
            [
                _section_field(
                    "subsidiaries",
                    "Subsidiary / JV / holding data",
                    control="multiselect",
                    options=[
                        {"label": "Example Corp", "value": "example_corp"},
                        {"label": "Kaitian", "value": "Kaitian"},
                        {"label": "NECPC", "value": "NECPC"},
                        {"label": "FCCL", "value": "FCCL"},
                        {"label": "Other", "value": "Other"},
                    ],
                ),
                _section_field(
                    "hasThirdPartyData",
                    "Store/process third-party entity data",
                    control="radio",
                    options=_yes_no_options(),
                ),
                _section_field(
                    "transferToThirdParty",
                    "Transfer data to third-party entities",
                    control="radio",
                    options=_yes_no_options(),
                ),
                _section_field(
                    "comments",
                    "Checkpoint 1 comments",
                    control="textarea",
                    placeholder="Capture context or exceptions",
                ),
            ],
        ),
        _questionnaire_section(
            "privacyCheckpoint2Section",
            "Checkpoint 2 (RoW involved or deployed on RoW)",
            "Screening for personal data, company records, and regulated data outside PRC scope.",
            [
                _section_field(
                    "required",
                    "Does Checkpoint 2 apply?",
                    control="radio",
                    options=_yes_no_options(),
                ),
                _section_field(
                    "personalDataType",
                    "Personal Data Type",
                    control="select",
                    options=[
                        {"label": "General Personal Data", "value": "General Personal Data"},
                        {"label": "Sensitive Personal Data", "value": "Sensitive Personal Data"},
                    ],
                ),
                _section_field(
                    "companyRecords",
                    "Company Records",
                    control="select",
                    options=[
                        {"label": "Tax", "value": "Tax"},
                        {"label": "Accounting", "value": "Accounting"},
                        {"label": "Employee Record", "value": "Employee Record"},
                    ],
                ),
                _section_field(
                    "governmentSecurityData",
                    "Government & Security Data",
                    control="radio",
                    options=_yes_no_options(),
                ),
                _section_field(
                    "criticalInfrastructureData",
                    "Critical Infrastructure Data",
                    control="radio",
                    options=_yes_no_options(),
                ),
                _section_field(
                    "comments",
                    "Checkpoint 2 comments",
                    control="textarea",
                    placeholder="Capture context or exceptions",
                ),
            ],
        ),
        _questionnaire_section(
            "privacyCheckpoint3Section",
            "Checkpoint 3 (PRC involved or deployed on PRC)",
            "Screening for PRC personal information and cross-border transfer obligations.",
            [
                _section_field(
                    "required",
                    "Does Checkpoint 3 apply?",
                    control="radio",
                    options=_yes_no_options(),
                ),
                _section_field(
                    "personalDataType",
                    "Personal Data Type",
                    control="select",
                    options=[
                        {"label": "General Personal Data", "value": "General Personal Data"},
                        {"label": "Sensitive Personal Data", "value": "Sensitive Personal Data"},
                    ],
                ),
                _section_field(
                    "personalDataVolume",
                    "Processed personal data count",
                    control="select",
                    options=[
                        {"label": "More than 1,000,000", "value": "More than 1,000,000"},
                        {"label": "Less than 1,000,000", "value": "Less than 1,000,000"},
                    ],
                ),
                _section_field(
                    "sensitiveDataVolume",
                    "Processed sensitive personal data count",
                    control="select",
                    options=[
                        {"label": "More than 100,000", "value": "More than 100,000"},
                        {"label": "Less than 100,000", "value": "Less than 100,000"},
                    ],
                ),
                _section_field(
                    "ciio",
                    "CIIO",
                    control="radio",
                    options=_yes_no_not_sure_options(),
                ),
                _section_field(
                    "importantData",
                    "Important Data",
                    control="radio",
                    options=_yes_no_not_sure_options(),
                ),
                _section_field(
                    "crossBorderTransfer",
                    "Cross-border Transfer",
                    control="radio",
                    options=_yes_no_not_sure_options(),
                ),
                _section_field(
                    "comments",
                    "Checkpoint 3 comments",
                    control="textarea",
                    placeholder="Capture context or exceptions",
                ),
            ],
        ),
    ],
    "questionnaireCategories": [],
    "questionBank": [],
    "projectTypeOptions": [],
    "projectTypeGuide": {
        "title": "Project Type - Architecture Artifact Matrix",
        "introduction": [
            "This guide provides project-type-driven guidance for selecting architecture artifacts.",
            "It focuses on when specific artifacts are required, recommended, or optional based on system complexity and risk profile.",
            "This guide does not define architecture artifacts, viewpoints, or governance processes. Those topics are covered in separate Enterprise Architecture standards and governance guides.",
        ],
        "objectives": [
            {
                "title": "Establish a project-type-driven architecture baseline",
                "description": "Define the essential architecture artifacts required for different project types based on business complexity, integration patterns, and risk profiles rather than enforcing a one-size-fits-all documentation model.",
            },
            {
                "title": "Allocate architecture effort based on risk and complexity",
                "description": "Align required artifacts with typical technical, security, data, and operational risks so architecture deliverables mitigate the most critical risks first.",
            },
            {
                "title": "Improve architecture review and cross-team communication efficiency",
                "description": "Provide a shared and consistent artifact baseline so reviewers and stakeholders can focus on key design decisions and trade-offs instead of document completeness.",
            },
            {
                "title": "Balance standardization and flexibility",
                "description": "Maintain enterprise-level consistency and auditability while allowing projects to tailor architecture views to their own delivery characteristics and needs.",
            },
        ],
        "scopeIntro": "This matrix applies to architecture design, solution review, and technical governance activities for the following project types:",
        "scopeProjectTypes": [
            "Web applications and service-oriented systems",
            "Data projects (ETL / ELT / BI)",
            "AI projects (ML / LLM / RAG / MLOps / LLMOps)",
            "Complex business process systems",
            "Identity and interaction-heavy integration solutions",
            "Performance- and resilience-critical integration systems",
            "Systems with complex logic such as workflows, rule engines, and transaction control",
        ],
        "scopeNote": "The matrix does not prescribe specific technologies or implementations. Its purpose is to define which architectural concerns must be explicitly described and reviewed.",
        "corePrinciples": [
            {
                "title": "Driven by project characteristics, not technology labels",
                "description": "Architecture artifact selection is based on actual system complexity and risk exposure rather than labels such as Web, AI, or Data.",
            },
            {
                "title": "Mandatory does not mean exhaustive design",
                "description": "Mandatory indicates the minimum artifact set required to support architecture review and risk assessment, not a requirement to document every design detail.",
            },
            {
                "title": "Recommended artifacts expose hidden risks",
                "description": "Recommended artifacts usually surface cross-system interactions, runtime behavior, and non-functional risks such as security, performance, resilience, and compliance.",
            },
            {
                "title": "Optional artifacts support communication, not governance",
                "description": "Optional artifacts help explain complex ideas, improve understanding across roles, and supplement non-critical design areas. They should not become gating items for architecture approval.",
            },
        ],
        "governanceBoundary": [
            "Core architecture artifacts such as Technical Diagram, App Collaboration Diagram, and Auth & Service Flow remain within EA governance scope and are used to assess architectural consistency, controllability, and risk.",
            "Data Asset Matrix, Data Compliance Diagram, and Resource List use EA-provided templates for consistency, readability, and reuse but are not subject to mandatory EA governance approval.",
            "The decision to produce, maintain, and size these supporting artifacts remains with the project team based on regulatory requirements and project-specific risk.",
        ],
        "recommendedUsage": [
            "During solution design, use the matrix to quickly identify Mandatory and Recommended artifacts.",
            "During architecture review, focus on key decisions and risks captured in Mandatory artifacts.",
            "For complex or high-risk projects, use Recommended artifacts to surface runtime and non-functional risks early.",
            "For low-complexity projects, allow reasonable tailoring to avoid unnecessary documentation overhead.",
        ],
        "artifactSelectionIntro": [
            "This section defines how architecture artifacts are selected based on project type, system complexity, and risk profile.",
            "It does not introduce new artifact types. It provides guidance on when existing artifacts are required, recommended, optional, or not required.",
            "The matrix below represents the default selection baseline. Projects may tailor the selection based on justified risk assessment, provided that all Mandatory artifacts are addressed.",
            "Each project should be mapped to the closest project type based on its dominant complexity and risk characteristics rather than implementation technology alone.",
        ],
        "legend": [
            {"symbol": "Mandatory", "meaning": "Required baseline artifact for architecture review and risk assessment."},
            {"symbol": "Recommended", "meaning": "Strongly advised to surface hidden runtime or non-functional risk."},
            {"symbol": "Optional", "meaning": "Useful for communication and clarification but not normally gating."},
            {"symbol": "Not Required", "meaning": "Not part of the default baseline for this project type."},
        ],
        "note": "For the Data Asset Matrix, Data Compliance Diagram, and Resource List, EA provides standardized templates for consistency and reuse. Governance and maintenance responsibilities remain defined in the EA Governance Guide and usually stay with the project team or another governance team.",
    },
    "assessmentMatrices": [],
    "projectTypeProfiles": [],
    "applicationCountRangeOptions": [],
    "externalSystemCountRangeOptions": [],
    "newApplicationCountRangeOptions": [],
    "modifiedApplicationCountRangeOptions": [],
    "dataCenterCountRangeOptions": [],
    "cloudRegionScopeOptions": [],
    "techStackKindsCountRangeOptions": [],
    "integrationTechKindsCountRangeOptions": [],
}
