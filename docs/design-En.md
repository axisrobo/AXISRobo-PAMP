# AxisArch System Detailed Design Document

> **Note:** This document was last updated 2026-03-26 and is not a complete translation
> of `design.md`. See `docs/architecture.md` for the current architecture reference.
>
> Version: 2.0.0 | Generated: 2026-03-26

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Technology Stack](#2-technology-stack)
3. [System Architecture](#3-system-architecture)
4. [Backend Detailed Design](#4-backend-detailed-design)
   - 4.1 [Application Entry & Middleware](#41-application-entry--middleware)
   - 4.2 [Authentication & Authorization (Auth)](#42-authentication--authorization-auth)
   - 4.3 [Module A: EA Review](#43-module-a-ea-review)
   - 4.4 [Module B: App Solution (Application Management)](#44-module-b-app-solution-application-management)
   - 4.5 [Module C: Reports & Analytics](#45-module-c-reports--analytics)
   - 4.6 [Module D: Auth & Users](#46-module-d-auth--users)
   - 4.7 [Module E: Config & Data](#47-module-e-config--data)
   - 4.8 [Module F: Shared Services](#48-module-f-shared-services)
   - 4.9 [AI Agent (Architecture Check Agent)](#49-ai-agent-architecture-check-agent)
   - 4.10 [Scheduled Tasks](#410-scheduled-tasks)
5. [Database Design](#5-database-design)
   - 5.1 [Schema Overview](#51-schema-overview)
   - 5.2 [Core Table Structures](#52-core-table-structures)
6. [Frontend Detailed Design](#6-frontend-detailed-design)
   - 6.1 [Overall Structure](#61-overall-structure)
   - 6.2 [Routing Design](#62-routing-design)
   - 6.3 [Page Module Details](#63-page-module-details)
   - 6.4 [Common Component Library](#64-common-component-library)
   - 6.5 [Core Utility Layer](#65-core-utility-layer)
7. [API Summary](#7-api-summary)
8. [Security Design](#8-security-design)
9. [Data Flow Diagram](#9-data-flow-diagram)

---

## 1. System Overview

AxisArch is a generic enterprise architecture management platform, supporting the following core business domains:

| Business Domain | Description |
|-----------------|-------------|
| **EA Review** | Manages the full lifecycle of project EA review requests, including submission, acceptance, review, completion, return, and state transitions, as well as related meetings, action items, schedules, and attachment management |
| **App Solution (Application Management)** | Manages enterprise application systems, maintains business capability mapping (BCM), manages technology stack, and integrates with CMDB |
| **Reports & Analytics** | EA review data statistics and visualization, including status distribution, monthly trends, architecture score distribution, lead time analysis, etc. |
| **BC Visualization** | Visualizes BizCapability and application mapping via heatmap/mindmap |
| **Certification Management** | Manages team member technical certifications, including batch import and notifications |
| **Master Data** | Reference data management for data centers, data classification, legal entities, etc. |
| **Settings** | Audit logs, team member management, review scope configuration |

---

## 2. Technology Stack

### Backend

| Component | Version/Selection |
|-----------|------------------|
| Language  | Python 3.11+      |
| Web Framework | FastAPI       |
| ORM/DB Driver | SQLAlchemy (AsyncIO) + asyncpg |
| Database  | PostgreSQL (Schema: `eam`) |
| Authentication | Keycloak (JWT/OIDC) |
| Data Migration | Custom SQL files (executed at startup) |
| Scheduled Tasks | APScheduler (AsyncIOScheduler) |
| File Storage | S3-compatible object storage |
| AI Integration | LangChain + custom workflow (architecture diagram AI check) |
| Email Service | Enterprise email API (async sending) |
| Excel Export | openpyxl |

### Frontend

| Component | Version/Selection |
|-----------|------------------|
| Framework | Next.js 14 (App Router) |
| Language  | TypeScript (strict mode) |
| UI Library | Ant Design v6 |
| Styles    | Tailwind CSS |
| State Management | Zustand (global) + React Query (server state) |
| Authentication | Keycloak JS Adapter |
| Charts    | Custom Canvas/SVG components |
| E2E Testing | Playwright |

---
