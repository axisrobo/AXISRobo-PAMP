# PAMF — Roadmap

> **Product positioning**: Enterprise Architecture Management & Governance Platform
> **Aligned with**: *Enterprise AI Security Architecture Guideline v2.4* — OWASP Agentic Top 10, CAEP, Zero Trust, SPIFFE

---

## Domain Capability Roadmap

### Business Capability Management

Manage enterprise business capabilities, their hierarchy, and mapping to applications.

- [x] Business capability CRUD (`biz_cap_map`, `bc_master_data` tables)
- [x] Capability hierarchy with parent-child relationships and level tracking
- [x] Business capability ↔ application mapping (which apps support which capabilities)
- [ ] Capability maturity assessment framework
- [ ] Capability heatmap visualization (coverage, gaps, overlaps)
- [ ] Capability-based investment planning and roadmapping

### Application Asset Management

Manage the application portfolio as enterprise assets with lifecycle tracking.

- [x] Application registration and basic metadata (name, owner, status)
- [x] Application ↔ business capability mapping
- [x] Application ↔ data entity mapping (`application_data_entity`)
- [x] Application legal entity and company code tracking
- [x] Application member/owner assignment
- [ ] Application lifecycle stage tracking (Plan, Build, Run, Retire)
- [ ] Application dependency and integration topology
- [ ] Application health scoring (TCO, risk, technical debt, business value)

### Application Portfolio Management

Portfolio-level governance and decision-making for application investments.

- [x] CMDB application synchronization (EE)
- [x] Application ↔ Project mapping (which projects change which apps)
- [x] Application architecture review integration (EA Review module)
- [ ] Portfolio rationalization (keep, invest, migrate, retire decisions)
- [ ] Application TCO modeling and cost attribution
- [ ] Portfolio roadmap with timeline-based transformation planning

### Application Architecture Management

Govern application-level architecture decisions, integration patterns, and solution evaluation.

- [x] Application registration and portfolio management (CMDB)
- [x] Application -> business capability mapping
- [x] Application -> data entity mapping
- [ ] Application integration management (APIs, events, messaging topology)
- [ ] Solution architecture evaluation methodology (weighted scoring, trade-off analysis)
- [ ] Application architecture patterns catalog (microservices, modular monolith, event-driven)
- [ ] Application modernization planning (legacy assessment, migration strategy)
- [ ] Application architecture decision records (ADR with context, options, rationale, consequences)
- [ ] Application dependency and integration topology visualization

### Data Management

Enterprise data governance — data assets, classification, residency, flows, and privacy.

- [x] Data classification framework by sensitivity tier
- [x] Data privacy and compliance tracking
- [x] Company and legal entity registry
- [ ] Data residency and sovereignty management (GDPR, PIPL, CCPA jurisdiction mapping)
- [ ] Data flow mapping and lineage visualization
- [ ] Data quality metrics and monitoring
- [ ] Data catalog with business glossary integration
- [ ] Data ownership and stewardship assignment

### Technology Management

Manage the technology stack lifecycle, compliance, and standardization.

- [x] Technology stack master data catalog
- [x] Key technology stack item CRUD with versioning
- [x] Technology stack ↔ application lifecycle management
- [x] Technology stack compliance checking (approved list, restricted software)
- [x] Technology stack auto-checking log and audit trail
- [x] Technology stack categorization (languages, frameworks, platforms, tools)
- [ ] Technology obsolescence tracking and upgrade planning
- [ ] Technology risk assessment and vulnerability correlation
- [ ] Technology standards board with approval workflow
- [ ] Cloud service and SaaS governance

### Security Management

Enterprise security governance — architecture-level security controls and risk assessment.

- [x] AI architecture diagram security review (AI check agent)
- [x] AI security self-assessment against Enterprise AI Security Guideline v2.4
- [ ] Threat modeling integration with architecture review
- [ ] Security control compliance mapping (NIST, ISO 27001, SOC 2)
- [ ] Vulnerability management for technology stacks
- [ ] Security incident response workflow
- [ ] Secrets and credentials management governance

### AI Management

Govern AI projects, models, agents, and their architecture compliance.

- [x] AI project self-assessment (AT0-AT8 tier x L0-L4 maturity matrix)
- [x] Architecture review checklist (11 sections, 49 items) aligned with security guideline
- [x] Counterparty type governance (CP1-CP4: internal, partner, supplier, consumer)
- [x] AI architecture diagram review (App Arch + Tech Arch) with scoring
- [x] AI-related project flagging and tracking
- [ ] AI model registry with version and provenance tracking
- [ ] AI Bill of Materials (AIBOM) generation and verification
- [ ] Agent identity and naming service registry
- [ ] MCP server and tool governance (registration, approval, provenance)
- [ ] AI governance maturity scoring and benchmarking

### Architecture Governance

Manage architecture review workflows, governance policies, and decision accountability.

- [x] EA Review workflow (create, submit, review, complete with status transitions)
- [x] AI-powered architecture diagram review (App Arch + Tech Arch scoring)
- [x] AVDM questionnaire -> concern derivation -> viewpoint -> artifact chain
- [x] Architecture review checklist with compliance scoring
- [x] Architecture lifecycle stage tracking (Preparation -> Design -> Review -> Operations)
- [ ] Architecture governance policy engine (define, version, enforce architecture rules)
- [ ] Architecture decision traceability (who decided what, with which evidence)
- [ ] Architecture governance maturity assessment (AT0-AT8 x L0-L4 matrix)
- [ ] Architecture compliance mapping to regulatory frameworks (GDPR, NIS2, EU AI Act)
- [ ] Architecture review dashboard and governance analytics

### Architecture Planning Management

Align architecture initiatives with business strategy through structured planning and roadmapping.

- [ ] Architecture strategy alignment (business goals -> architecture initiatives mapping)
- [ ] Annual architecture planning cycle (proposal, review, approval, budget allocation)
- [ ] Architecture initiative portfolio management (prioritization, dependency tracking)
- [ ] Architecture capability gap analysis (current vs target state assessment)
- [ ] Architecture transition planning (as-is -> to-be roadmap with milestones)
- [ ] Architecture investment planning and business case modeling
- [ ] Architecture planning dashboard (initiative status, roadmap visualization, KPI tracking)

### Architecture Content Management

Manage architecture standards, guidelines, templates, and reference architectures as governed content.

- [ ] Architecture standards library (TOGAF, C4, UML, BPMN reference documents)
- [ ] Architecture guideline management (security guidelines, coding standards, design patterns)
- [ ] Architecture template catalog (review templates, assessment templates, report templates)
- [ ] Reference architecture repository (solution architectures, pattern libraries, blueprints)
- [ ] Architecture knowledge base (decisions, lessons learned, best practices)
- [ ] Content versioning and lifecycle (draft -> review -> published -> deprecated)
- [ ] Content search and discovery with metadata tagging
- [ ] Architecture content governance (access control, approval workflow, audit trail)

### Architecture Research Management

Track emerging technologies, architecture trends, and maintain the technology radar.

- [ ] Technology radar (assess, trial, adopt, hold -- ring-based visualization)
- [ ] Architecture trend monitoring and impact analysis
- [ ] Technology evaluation framework (POC criteria, scoring methodology)
- [ ] Research initiative management (proposal, experiment, findings, recommendation)
- [ ] Architecture innovation pipeline (ideation -> prototype -> pilot -> adoption)
- [ ] External reference tracking (industry reports, analyst research, competitor analysis)
- [ ] Technology radar publishing and stakeholder communication

### Operations Architecture Management

Design and manage non-functional requirements, operational capabilities, and service levels.

- [ ] Non-functional requirements catalog (availability, performance, scalability, security, compliance)
- [ ] NFR design and specification per architecture domain
- [ ] Service level objective (SLO) and service level agreement (SLA) management
- [ ] Operational runbook and standard operating procedure management
- [ ] Disaster recovery and business continuity architecture planning
- [ ] Capacity planning and performance engineering guidelines
- [ ] Operational readiness assessment (pre-go-live architecture review)
- [ ] Operations architecture monitoring and observability design

### Architecture Talent Management

Develop architecture competencies through structured learning, certification, and career paths.

- [ ] Architecture competency framework (skills matrix per role: Enterprise, Solution, Domain, Technical)
- [ ] Architecture training curriculum (courses by competency level: Foundation -> Practitioner -> Expert)
- [ ] Architecture certification management (internal certification tracks, external cert tracking)
- [ ] Architecture exam and assessment platform (question banks, scoring, certification issuance)
- [ ] Architecture mentor and coach assignment
- [ ] Architecture community of practice (forums, knowledge sharing, peer reviews)
- [ ] Architecture career path and progression framework
- [ ] Architecture talent dashboard (skills coverage, certification status, development plans)

### System Management

Platform-level technical infrastructure — identity, access, audit, and system administration.

- [x] Role-based access control (3 roles: admin, reviewer, requestor)
- [x] OSS local auth with JWT (AUTH_MODE=local)
- [x] Audit logging with cryptographic integrity (`eam_audit_log`)
- [x] User activity auditing and permission tracking
- [x] Resource pool management (itcode, name, email, organization hierarchy)
- [x] Certification management for architecture roles
- [x] Master data CRUD and data versioning
- [x] System configuration — questionnaire, concern mapping, viewpoint/artifact catalogs
- [ ] System audit and usage analytics dashboard
- [ ] Bulk data import/export with validation

---

## Platform Evolution Roadmap

## v1.0 — De-brand & Document (Current)
- [x] Remove all enterprise branding
- [x] Add architecture, status, roadmap, threat model, API docs
- [x] Align development harness (AGENTS.md, OpenCode)
- [x] OSS local auth (username/password + JWT, 3 roles)
- [x] Database-backed file storage (S3 fallback)
- [x] AVDM concern catalog, viewpoint catalog, concern↔artifact mapping
- [x] Questionnaire → Concern → Viewpoint → Artifact data chain
- [x] Expandable Concern/Artifact views in EA Review
- [x] Project form PM/DT/IT selector fixes
- [x] DB schema documentation (98 tables)
- [ ] Verify build + test suite passes

## v1.1 — Clean Architecture Refactoring (In Progress)
- [x] Extract domain layer (entities, value objects, repository interfaces)
- [x] Create application service layer (use cases, DTOs)
- [x] Implement repository layer (wrap raw SQL)
- [x] Thin API routers (delegate to services)
- [x] Plugin system for integrations (auth, email, CMDB, storage)
- [x] Frontend feature-folder restructuring
- [x] AVDM config pages moved to `(add_config)` route group
- [ ] Unify dual-project-table architecture (eam.project vs eam.eam_project)

## v1.2 — Frontend Modernization
- [ ] Unit test setup (Vitest + React Testing Library)
- [ ] Shared component library extraction
- [ ] API versioning (v1 → v2 with deprecation)
- [ ] Error boundary pages
- [ ] Loading skeleton patterns

## v1.3 — Multi-Tenancy
- [ ] Schema-level or row-level tenant isolation
- [ ] Tenant-aware auth
- [ ] Tenant-scoped master data
- [ ] Tenant admin dashboard

## v2.0 — Architecture Policy & Decision Governance

*PAMF as the single source of truth for architecture decisions, policies, and their traceability*

PAMF governs architecture at **design-time and review-time** — it defines what architectures should look like and verifies compliance, without runtime enforcement. The AI Security Guideline's identity and policy patterns are adapted as architecture governance capabilities that PAMF provides to organizations.

- [ ] **Architecture Element Registry** — Single registry for all governed elements: applications, data assets, integration flows, technology stacks, AI agents. Each element carries scenario class, stakeholder type, owner, trust level, and linked architecture decisions.
- [ ] **Architecture Policy Engine** — Define architecture rules as version-controlled policy code. Example: "All applications handling PII must complete Data Architecture Viewpoint review and produce a Data Flow artifact." Policy compliance evaluated during architecture review.
- [ ] **Architecture Decision Traceability** — Full chain from questionnaire → concern → viewpoint → artifact → review outcome → implementation. Every architecture decision has provenance: who decided what, based on which evidence, resulting in which prescribed artifacts.
- [ ] **Architecture Identity Model** — Application identity, data asset identity, integration identity, AI agent identity — all registered, classified, and linked to architecture policies and review requirements.
- [ ] **Shadow Architecture Governance** — Discovery and registration of ungoverned architecture elements (Shadow AI, unregistered APIs, undocumented data flows). PAMF as the detection and onboarding mechanism for AT0 elements.

## v2.1 — Continuous Architecture Compliance Assessment

*PAMF as the continuous governance layer between declared architecture and implementation reality*

Architecture governance is not a one-time review. PAMF provides continuous assessment: comparing what was declared (AVDM questionnaire → concerns → viewpoints → artifacts) against what exists. When implementations drift, PAMF flags, escalates, and triggers re-review.

- [ ] **Architecture-Implementation Drift Detection** — Compare declared architecture (AVDM questionnaire results, prescribed artifacts, review decisions) against actual implementations. Deviation → automated re-review trigger or governance escalation.
- [ ] **Architecture Risk Boundary Definition** — Define critical risk combinations for architecture governance: "data with sensitivity X + integration with untrusted partner + external communication capability" → mandatory architecture review gate. PAMF identifies these combinations and enforces review requirements.
- [ ] **Architecture Audit Trail** — Complete time-series record of all architecture governance actions: who reviewed what, when, with which evidence, resulting in which decision. Supports EU AI Act Art. 72 trajectory-level requirements for architecture decisions.
- [x] **Architecture Review Automation** — Workflow-driven architecture review with automated compliance scoring. Each review gate evaluates against defined architecture policies. Non-negotiable gates halt progression until resolved.

## v2.2 — Architecture Supply Chain Governance

*PAMF as the governance authority for architecture component provenance and composition*

Every architecture is composed of components — frameworks, platforms, tools, APIs, data sources, AI models. PAMF governs their provenance, version, and compliance status, providing an Architecture Bill of Materials that traces what each architecture element depends on.

- [ ] **Architecture Bill of Materials (ABOM)** — Multi-layer traceability for each governed architecture: framework layer / platform layer / tool layer / data source layer / external dependency layer. PAMF generates and verifies ABOM completeness.
- [ ] **Component Provenance Verification** — Every architecture component (MCP server, plugin, external API, SDK, model) carries verified provenance: origin, version, approval status, known vulnerabilities. PAMF flags unverified components during architecture review.
- [ ] **Architecture Composition Governance** — When architectures change (new dependency, new integration, new data source), PAMF evaluates the impact against existing policies and triggers re-review for affected elements.
- [ ] **Coding Agent Architecture Governance** — Define separate architecture policies for IDE-resident vs CI-resident coding agents. PAMF tracks which architectures are modified by which agents, with distinct review requirements per trust model.

## v2.3 — Stakeholder-Context Architecture Governance

*PAMF as the multi-stakeholder governance platform — one platform, multiple governance contexts*

Different stakeholders need different governance models. PAMF provides context-appropriate architecture governance views: what a supplier sees vs what an internal reviewer sees vs what a consumer sees — all from the same architecture governance platform, with data isolation between contexts.

- [ ] **Stakeholder Governance Contexts** — Internal employee / External partner / Supplier / Consumer — each with distinct architecture visibility scope, data classification boundaries, consent requirements, and review authority.
- [ ] **Supplier Architecture Governance** — Per-supplier architecture governance domains with data isolation (supplier A must not see supplier B's architecture data, BOM, pricing, or quality metrics). PAMF enforces this at the governance layer through data classification and access policy.
- [ ] **Consumer-Facing Architecture Governance** — Governance of architectures that directly serve consumers (CP4). PAMF tracks consent records, data subject rights, and regulatory obligations linked to architecture decisions that affect consumer data.
- [ ] **Multi-Architecture Governance Dashboard** — Unified governance view across all architecture domains and stakeholder contexts. Governance maturity scoring per domain, compliance gap analysis, cross-domain impact assessment.

## v2.4 — Architecture Data Governance & Observability

*PAMF as the guardian of architecture-sensitive data — classification, protection, and governance of what enters AI systems*

Architecture data itself is sensitive: BOM data, supplier costs, quality metrics, architecture decisions, security assessments. PAMF must classify, protect, and govern access to this data — especially before it enters any AI-assisted analysis or recommendation pipeline.

- [ ] **Architecture Data Classification Engine** — Classify architecture data by sensitivity tier. PAMF applies data handling rules before architecture data enters any analysis, report, or AI recommendation context.
- [ ] **Crown Jewels Architecture Mapping** — Identify and catalog enterprise-critical architecture assets. Manufacturing-specific: BOM structures, supplier cost data, cross-supplier quality comparisons, strategic procurement plans. PAMF governs who can see what.
- [ ] **Architecture Knowledge Base Governance** — All architecture knowledge sources (standards documents, review templates, architecture decisions, reference architectures) governed for provenance, version, and access. PAMF ensures AI-assisted architecture analysis uses only trusted, governed sources.
- [ ] **Architecture Governance Observability** — Dashboards and metrics for architecture governance health: policy compliance rates, drift detection alerts, review cycle times, governance maturity trends. Prometheus + Grafana integration for governance metrics.
- [ ] **Audit Log Integrity** — All architecture governance actions cryptographically hashed in append-only audit log for regulatory compliance and forensic traceability.

## v3.0 — Architecture Governance Maturity & Regulatory Compliance

*PAMF as the enterprise-grade architecture governance platform — maturity assessment, regulatory compliance mapping, decision-level accountability*

PAMF provides the governance infrastructure for organizations to assess, improve, and demonstrate architecture governance maturity. From self-assessment to regulatory compliance mapping to decision-level accountability.

- [x] **Architecture Governance Maturity Assessment** — AT0-AT8 adoption tier × L0-L4 governance maturity self-assessment matrix. Automated go/no-go gates based on architecture risk profile. PAMF as the assessment engine.
- [ ] **Regulatory Architecture Compliance Mapping** — Architecture decisions → applicable regulations → compliance evidence. PAMF maps which architecture reviews satisfy which regulatory requirements (GDPR Art. 33, NIS2 24h, EU AI Act Art. 72, PIPL, DORA conditional).
- [ ] **Decision-Level Architecture Accountability** — Full reconstruction of any governed architecture outcome: which questionnaire triggered which concern, which concern selected which viewpoint, which viewpoint prescribed which artifact, who reviewed, who approved, with what evidence. Audit-ready, regulator-ready.
- [ ] **Architecture Governance Policy as Code** — All architecture governance rules expressed as version-controlled, testable policy code. Architecture governance CI/CD pipeline with automated policy testing. Policy changes require architecture review approval.
- [ ] **Cross-Organization Architecture Governance Federation** — Multi-tenant governance for organizations managing architectures across business units, geographies, and regulatory jurisdictions. Each domain with independent policy sets, shared governance platform.

## v3.1 — Plugin Marketplace
- [ ] Plugin SDK specification
- [ ] Hot-reload module system
- [ ] Plugin registry with versioning
- [ ] Community plugin templates

## v3.2 — Internationalization
- [ ] i18n key extraction tooling
- [ ] zh/en localization packs
- [ ] RTL layout support
- [ ] Locale-aware date/number formatting
