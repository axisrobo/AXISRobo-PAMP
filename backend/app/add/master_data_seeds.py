"""Bootstrap seeds aligned to the normalized AVDM master-data schema."""
from __future__ import annotations

from dataclasses import replace

from .master_data_models import (
    QuestionAnswerOptionItemModel,
    QuestionAnswerOptionSetModel,
    QuestionAnswerTypeModel,
    QuestionCategoryModel,
    QuestionGroupModel,
    QuestionModel,
)


QUESTION_YES_NO_OPTION_SET_KEY = "questionYesNoOptions"


DEFAULT_QUESTION_GROUPS: tuple[QuestionGroupModel, ...] = (
    QuestionGroupModel("scale_overall", "Scale Overall", "Project and delivery scale indicators.", 10),
    QuestionGroupModel("complexity_overall", "Complexity Overall", "Technical, data, requirement, and compliance complexity factors.", 20),
    QuestionGroupModel("change", "Change Trigger", "Business, application, data, technology, and governance change triggers.", 30),
    QuestionGroupModel("architecture_type", "Architecture Type", "Dominant architecture style selections.", 40),
)


DEFAULT_QUESTION_CATEGORIES: tuple[QuestionCategoryModel, ...] = (
    QuestionCategoryModel("project_scale", "scale_overall", "Project Scale", "Capture application scope, external reach, and scale indicators for the initiative.", 10),
    QuestionCategoryModel("change_scale", "scale_overall", "Change Scale", "Capture new-build versus change-impact scope across the solution landscape.", 20),
    QuestionCategoryModel("project_resource_and_size", "scale_overall", "Project Resource and Size", "Capture delivery capacity, resource scale, and funding indicators.", 30),
    QuestionCategoryModel("technical_complexity", "complexity_overall", "Technical Complexity", "Capture deployment, integration, runtime, and platform complexity factors.", 40),
    QuestionCategoryModel("data_complexity", "complexity_overall", "Data Complexity", "Capture data model, lineage, integration, quality, and governance complexity for the solution.", 50),
    QuestionCategoryModel("compliance_complexity", "complexity_overall", "Compliance Complexity", "Capture regulatory scope, control obligations, traceability, and audit complexity for the solution.", 60),
    QuestionCategoryModel("requirement_complexity", "complexity_overall", "Requirement Complexity", "Capture business requirement ambiguity, organizational change, and strategic complexity.", 70),
    QuestionCategoryModel("solution_complexity", "complexity_overall", "Solution Complexity", "Capture solution optioning, dependency, delivery, and architecture impact complexity.", 80),
    QuestionCategoryModel("security_complexity", "complexity_overall", "Security Complexity", "Capture security control, exposure, and assurance complexity for the solution.", 90),
    QuestionCategoryModel("business_change", "change", "Business Change", "Activate business capability, business process, stakeholder, and organizational concerns.", 100),
    QuestionCategoryModel("application_change", "change", "Application Change", "Activate application boundary, service decomposition, lifecycle, ownership, and collaboration concerns.", 110),
    QuestionCategoryModel("data_change", "change", "Data Change", "Activate data flow, lineage, sharing, privacy scope, and integration concerns.", 120),
    QuestionCategoryModel("technology_change", "change", "Technology Change", "Activate technology stack, platform, deployment, observability, security mechanism, and runtime concerns.", 130),
    QuestionCategoryModel("compliance_change", "change", "Compliance Change", "Activate compliance, control traceability, governance, location, and regulatory concerns.", 140),
    QuestionCategoryModel("security_change", "change", "Security Change", "Capture security policy, control, identity, and protection changes introduced by the project.", 150),
    QuestionCategoryModel("other_change", "change", "Other Change", "Capture cross-cutting or context-specific concerns not fully covered above.", 160),
    QuestionCategoryModel("technical_architecture_type", "architecture_type", "Technical Architecture Type", "Capture the dominant technical architecture style for the project.", 170),
    QuestionCategoryModel("application_architecture_type", "architecture_type", "Application Architecture Type", "Capture the dominant application architecture style for the project.", 180),
    QuestionCategoryModel("data_architecture_type", "architecture_type", "Data Architecture Type", "Capture the dominant data architecture style for the project.", 190),
    QuestionCategoryModel("business_architecture_type", "architecture_type", "Business Architecture Type", "Capture the dominant business architecture style for the project.", 200),
    QuestionCategoryModel("security_architecture_type", "architecture_type", "Security Architecture Type", "Capture the dominant security architecture style for the project.", 210),
)


DEFAULT_QUESTION_ANSWER_TYPES: tuple[QuestionAnswerTypeModel, ...] = (
    QuestionAnswerTypeModel("radio", "Single Choice Radio", "single_choice", "radio", description="Best for Yes/No and small exclusive choices."),
    QuestionAnswerTypeModel("select", "Single Choice Select", "single_choice", "select", description="Best for long exclusive choice sets."),
    QuestionAnswerTypeModel("multiselect", "Multi Choice Select", "multi_choice", "multiselect", allows_multiple=True, description="Best for selecting multiple applicable options."),
    QuestionAnswerTypeModel("text", "Single Line Text", "text", "text", allows_free_text=True, description="Best for concise free-text answers."),
    QuestionAnswerTypeModel("textarea", "Multi Line Text", "text", "textarea", allows_free_text=True, description="Best for narrative or justification input."),
)


DEFAULT_SHARED_OPTION_SETS: tuple[QuestionAnswerOptionSetModel, ...] = (
    QuestionAnswerOptionSetModel(QUESTION_YES_NO_OPTION_SET_KEY, "Question Yes / No", "Reusable Yes/No choices for question-bank radio answers.", sort_order=1),
    QuestionAnswerOptionSetModel("projectTypeOptions", "Project Type", "Reusable project type choices.", sort_order=5),
    QuestionAnswerOptionSetModel("applicationCountRangeOptions", "Application Count", "Reusable application-count ranges.", sort_order=10),
    QuestionAnswerOptionSetModel("externalSystemCountRangeOptions", "External System Count", "Reusable external-system count ranges.", sort_order=20),
    QuestionAnswerOptionSetModel("newApplicationCountRangeOptions", "New Application Count", "Reusable new-application count ranges.", sort_order=30),
    QuestionAnswerOptionSetModel("modifiedApplicationCountRangeOptions", "Modified Application Count", "Reusable modified-application count ranges.", sort_order=40),
    QuestionAnswerOptionSetModel("dataCenterCountRangeOptions", "Data Center Count", "Reusable data-center count ranges.", sort_order=50),
    QuestionAnswerOptionSetModel("cloudRegionScopeOptions", "Cloud Region Scope", "Reusable cloud/region topology choices.", sort_order=60),
    QuestionAnswerOptionSetModel("techStackKindsCountRangeOptions", "Tech Stack Variety", "Reusable technology-kind count ranges.", sort_order=70),
    QuestionAnswerOptionSetModel("integrationTechKindsCountRangeOptions", "Integration Technology Variety", "Reusable integration-technology count ranges.", sort_order=80),
)


DEFAULT_SHARED_OPTION_ITEMS: tuple[QuestionAnswerOptionItemModel, ...] = (
    QuestionAnswerOptionItemModel(QUESTION_YES_NO_OPTION_SET_KEY, "Y", "Yes", sort_order=10),
    QuestionAnswerOptionItemModel(QUESTION_YES_NO_OPTION_SET_KEY, "N", "No", sort_order=20),
    QuestionAnswerOptionItemModel("projectTypeOptions", "WEB_APP_SERVICE", "Web Application / Service-Oriented System", sort_order=10),
    QuestionAnswerOptionItemModel("projectTypeOptions", "DATA_ETL_ELT_BI", "Data Project (ETL / ELT / BI)", sort_order=20),
    QuestionAnswerOptionItemModel("projectTypeOptions", "AI_ML_LLM_RAG_MLOPS", "AI Project (ML / LLM / RAG / MLOps / LLMOps)", sort_order=30),
    QuestionAnswerOptionItemModel("projectTypeOptions", "COMPLEX_BUSINESS_PROCESS", "Complex Business Process System", sort_order=40),
    QuestionAnswerOptionItemModel("projectTypeOptions", "IDENTITY_INTERACTION_HEAVY_INTEGRATION", "Identity & Interaction-Heavy Integration", sort_order=50),
    QuestionAnswerOptionItemModel("projectTypeOptions", "PERFORMANCE_RESILIENCE_HEAVY_INTEGRATION", "Performance & Resilience-Heavy Integration", sort_order=60),
    QuestionAnswerOptionItemModel("applicationCountRangeOptions", "LE_5", "5 or fewer", sort_order=10),
    QuestionAnswerOptionItemModel("applicationCountRangeOptions", "6_20", "6 to 20", sort_order=20),
    QuestionAnswerOptionItemModel("applicationCountRangeOptions", "21_50", "21 to 50", sort_order=30),
    QuestionAnswerOptionItemModel("applicationCountRangeOptions", "51_100", "51 to 100", sort_order=40),
    QuestionAnswerOptionItemModel("applicationCountRangeOptions", "GT_100", "More than 100", sort_order=50),
    QuestionAnswerOptionItemModel("externalSystemCountRangeOptions", "LE_5", "5 or fewer", sort_order=10),
    QuestionAnswerOptionItemModel("externalSystemCountRangeOptions", "5_20", "5 to 20", sort_order=20),
    QuestionAnswerOptionItemModel("externalSystemCountRangeOptions", "20_50", "20 to 50", sort_order=30),
    QuestionAnswerOptionItemModel("externalSystemCountRangeOptions", "GT_50", "More than 50", sort_order=40),
    QuestionAnswerOptionItemModel("newApplicationCountRangeOptions", "1", "1", sort_order=10),
    QuestionAnswerOptionItemModel("newApplicationCountRangeOptions", "2_5", "2 to 5", sort_order=20),
    QuestionAnswerOptionItemModel("newApplicationCountRangeOptions", "5_20", "5 to 20", sort_order=30),
    QuestionAnswerOptionItemModel("newApplicationCountRangeOptions", "20_50", "20 to 50", sort_order=40),
    QuestionAnswerOptionItemModel("newApplicationCountRangeOptions", "GT_50", "More than 50", sort_order=50),
    QuestionAnswerOptionItemModel("modifiedApplicationCountRangeOptions", "1", "1", sort_order=10),
    QuestionAnswerOptionItemModel("modifiedApplicationCountRangeOptions", "2_5", "2 to 5", sort_order=20),
    QuestionAnswerOptionItemModel("modifiedApplicationCountRangeOptions", "5_20", "5 to 20", sort_order=30),
    QuestionAnswerOptionItemModel("modifiedApplicationCountRangeOptions", "20_50", "20 to 50", sort_order=40),
    QuestionAnswerOptionItemModel("modifiedApplicationCountRangeOptions", "GT_50", "More than 50", sort_order=50),
    QuestionAnswerOptionItemModel("dataCenterCountRangeOptions", "1", "1", sort_order=10),
    QuestionAnswerOptionItemModel("dataCenterCountRangeOptions", "2_3", "2 to 3", sort_order=20),
    QuestionAnswerOptionItemModel("dataCenterCountRangeOptions", "4_10", "4 to 10", sort_order=30),
    QuestionAnswerOptionItemModel("dataCenterCountRangeOptions", "GT_10", "More than 10", sort_order=40),
    QuestionAnswerOptionItemModel("cloudRegionScopeOptions", "SINGLE_CLOUD_SINGLE_REGION", "Single cloud / Single region", sort_order=10),
    QuestionAnswerOptionItemModel("cloudRegionScopeOptions", "SINGLE_CLOUD_MULTI_REGION", "Single cloud / Multi region", sort_order=20),
    QuestionAnswerOptionItemModel("cloudRegionScopeOptions", "MULTI_CLOUD_SINGLE_REGION", "Multi cloud / Single region", sort_order=30),
    QuestionAnswerOptionItemModel("cloudRegionScopeOptions", "MULTI_CLOUD_MULTI_REGION", "Multi cloud / Multi region", sort_order=40),
    QuestionAnswerOptionItemModel("techStackKindsCountRangeOptions", "1_2", "1 to 2", sort_order=10),
    QuestionAnswerOptionItemModel("techStackKindsCountRangeOptions", "3_5", "3 to 5", sort_order=20),
    QuestionAnswerOptionItemModel("techStackKindsCountRangeOptions", "6_10", "6 to 10", sort_order=30),
    QuestionAnswerOptionItemModel("techStackKindsCountRangeOptions", "GT_10", "More than 10", sort_order=40),
    QuestionAnswerOptionItemModel("integrationTechKindsCountRangeOptions", "1_2", "1 to 2", sort_order=10),
    QuestionAnswerOptionItemModel("integrationTechKindsCountRangeOptions", "3_5", "3 to 5", sort_order=20),
    QuestionAnswerOptionItemModel("integrationTechKindsCountRangeOptions", "6_10", "6 to 10", sort_order=30),
    QuestionAnswerOptionItemModel("integrationTechKindsCountRangeOptions", "GT_10", "More than 10", sort_order=40),
)


_DEFAULT_QUESTION_BANK: tuple[QuestionModel, ...] = (
    QuestionModel(1, "business_change", "radio", "Will this project introduce a new business model or business process?", question_key="business_model_or_process", design_intent="Identify whether business architecture viewpoints need activation.", sort_order=10),
    QuestionModel(2, "application_change", "radio", "Will this project build a new custom application?", question_key="new_custom_application", design_intent="Trigger core application design and domain boundary concerns.", sort_order=20),
    QuestionModel(3, "application_change", "radio", "Will this project refactor an existing application?", question_key="refactor_existing_application", sort_order=30),
    QuestionModel(4, "application_change", "radio", "Will this project sunset an existing application?", question_key="sunset_existing_application", sort_order=40),
    QuestionModel(5, "application_change", "radio", "Will this project purchase SaaS software?", question_key="purchase_saas_software", sort_order=50),
    QuestionModel(6, "application_change", "radio", "Will this project purchase new licenses or capacity for existing SaaS software?", question_key="expand_existing_saas_capacity", sort_order=60),
    QuestionModel(7, "application_change", "radio", "Will this project onboard a new user group with significantly different roles or permissions?", question_key="new_user_group_roles", sort_order=70),
    QuestionModel(8, "application_change", "radio", "Will this project enable external access for the application for the first time?", question_key="enable_external_access", sort_order=80),
    QuestionModel(9, "data_change", "radio", "Will this project start storing PII or change the scope of PII stored by the application?", question_key="pii_scope_change", sort_order=90),
    QuestionModel(10, "data_change", "radio", "Will this project integrate with another internal or external IT system for the first time?", question_key="first_time_system_integration", sort_order=100),
    QuestionModel(11, "data_change", "radio", "Will this project start exchanging new data entities between already integrated systems?", question_key="new_data_entities_exchange", sort_order=110),
    QuestionModel(12, "technology_change", "radio", "Will this project use development languages outside the approved list?", question_key="non_standard_languages", sort_order=120),
    QuestionModel(13, "technology_change", "radio", "Will this project use frameworks or core libraries outside the approved list?", question_key="non_standard_frameworks", sort_order=130),
    QuestionModel(14, "technology_change", "radio", "Will this project use technical platforms or middleware outside the approved list?", question_key="non_standard_platforms", sort_order=140),
    QuestionModel(15, "technology_change", "radio", "Will this project use technical tools outside the approved list?", question_key="non_standard_tools", sort_order=150),
    QuestionModel(16, "technology_change", "radio", "Will this project use restricted software?", question_key="restricted_software", sort_order=160),
    QuestionModel(17, "technology_change", "radio", "Will this project use communication protocols other than HTTP(S), Kafka, or JDBC?", question_key="non_standard_protocols", sort_order=170),
    QuestionModel(18, "technology_change", "radio", "Will this project use an application-level authentication method other than OAuth2?", question_key="non_standard_application_auth", sort_order=180),
    QuestionModel(19, "technology_change", "radio", "Will this project use a user-level authentication method other than SSO Provider or Enterprise IDP?", question_key="non_standard_user_auth", sort_order=190),
    QuestionModel(20, "compliance_change", "radio", "Will this project use an authorization method other than UCA?", question_key="non_standard_authorization", sort_order=200),
    QuestionModel(21, "compliance_change", "radio", "Will this project use a deployment location or environment other than Beiyan, Shenyang, or Reston?", question_key="non_standard_deployment_location", sort_order=210),
    QuestionModel(22, "other_change", "radio", "Will this project build or change reusable services consumed by more than two applications?", question_key="shared_service_change", sort_order=220),
    QuestionModel(23, "technology_change", "radio", "Will this project build or change a mini program?", question_key="mini_program_change", sort_order=230),
    QuestionModel(24, "application_change", "radio", "Will this project build or change a mobile app?", question_key="mobile_app_change", sort_order=240),
    QuestionModel(25, "technology_change", "radio", "Will this project adopt AI in the project or application?", question_key="ai_adoption", sort_order=250),
)


DEFAULT_QUESTION_BANK: tuple[QuestionModel, ...] = tuple(
    replace(question, option_set_key=QUESTION_YES_NO_OPTION_SET_KEY)
    if question.answer_type_key == "radio" and not question.option_set_key
    else question
    for question in _DEFAULT_QUESTION_BANK
)