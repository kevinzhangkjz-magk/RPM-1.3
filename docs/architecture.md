Of course. Here is the provided text formatted as a Markdown file.

# RPM 1.3 Fullstack Architecture Document

-----

## 1\. Introduction

This document outlines the complete fullstack architecture for RPM 1.3, including backend systems, frontend implementation, and their integration. It serves as the single source of truth for AI-driven development.

### Starter Template or Existing Project

This is a greenfield project. To manage the Next.js frontend and Python backend, we will initialize the project using a **monorepo structure** managed by a tool like **Turborepo**.

### Change Log

| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 2025-07-28 | 1.0 | Initial Architecture Draft | Winston (Architect) |

-----

## 2\. High Level Architecture

### Technical Summary

This architecture describes a modern, cloud-native web application on AWS, featuring a Next.js frontend and a serverless Python backend. The layers communicate via a public REST API for the MVP. This serverless, decoupled approach is designed for performance and scalability.

### Platform and Infrastructure Choice

  * **Platform**: **Amazon Web Services (AWS)**.
  * **Key Services**: AWS Amplify (Frontend Hosting), AWS Lambda (Backend Compute), Amazon API Gateway (API Layer), AWS Redshift (Database).
  * **Deployment Regions**: Placeholder: `us-east-1`. **Note**: The final region must be confirmed to be the same as the existing Redshift cluster to minimize latency.

### Repository Structure

  * **Structure**: A **Monorepo** managed by **Turborepo**.
  * **Organization**: An `apps` directory for `web` and `api`, and a `packages` directory for shared code.

### High Level Architecture Diagram

```mermaid
graph TD
    subgraph User
        A[Browser]
    end

    subgraph "AWS Cloud"
        B(AWS Amplify Hosting) -- Serves --> A;
        A -- HTTPS API Calls --> C(API Gateway);
        C -- Proxies to --> E[AWS Lambda Functions (Python Backend)];
        E -- SQL Queries --> F[(AWS Redshift)];
    end
```

### Architectural Patterns

  * **Jamstack Architecture**: For a performant, scalable, and secure frontend.
  * **Serverless Architecture**: For a cost-efficient and auto-scaling backend.
  * **API Gateway Pattern**: To centralize routing and security for the API.

-----

## 3\. Tech Stack

| Category | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| Frontend Language | TypeScript | 5.4+ | Type safety for UI code |
| Frontend Framework| Next.js | 14+ | React framework for frontend |
| UI Components | ShadCN/UI | latest | UI component toolkit |
| Backend Language | Python | 3.11+ | Backend and data logic |
| Backend Framework | FastAPI | latest | High-performance API framework|
| API Style | REST | n/a | API communication standard |
| Database | AWS Redshift | n/a | Data warehouse |
| Frontend Testing | Jest & RTL | latest | Unit & component testing |
| Backend Testing | Pytest | latest | Unit & integration testing |
| E2E Testing | Playwright | latest | End-to-end browser testing |
| Build Tool | Turborepo | latest | Monorepo build system |
| Infrastructure | AWS CDK | latest | Infrastructure as Code |
| CI/CD | GitHub Actions | n/a | Continuous integration/deploy|

-----

## 4\. Data Models

  * **Site**: Represents a single solar site.
  * **PerformanceDataPoint**: Represents a single time-series telemetry reading.
  * **(User model to be handled by local storage in MVP)**.

-----

## 5\. API Specification

The following public REST endpoints will be created for the MVP:

  * `GET /api/sites`
  * `GET /api/sites/{site_id}/performance`
  * `GET /api/sites/{site_id}/skids`
  * `GET /api/skids/{skid_id}/inverters`
  * `POST /api/query`

-----

## 6\. Components

  * **Frontend Application**: Renders the UI and handles user interaction.
  * **Backend API**: Manages request routing via API Gateway.
  * **Data Service**: Lambda function with business logic for querying Redshift.
  * **AI Diagnostic Service**: Lambda function for the AI assistant.

-----

## 7\. Core Workflows

(Sequence diagram for the Root Cause Analysis drill-down is defined here).

-----

## 8\. Database Schema

The architecture will interact with the existing `sites` and `inverter_telemetry` tables in AWS Redshift. No new tables are required in Redshift for the MVP.

-----

## 9\. Frontend Architecture

  * **Component Organization**: A feature-based structure (`components/ui`, `components/features`).
  * **State Management**: Zustand for global client-side state.
  * **Routing**: Next.js App Router.
  * **Data Fetching**: TanStack Query (React Query) for managing server state.
  * **Dashboard Persistence (MVP)**: The dashboard layout will be saved in the browser's Local Storage.

-----

## 10\. Backend Architecture

  * **Approach**: A serverless architecture using AWS Lambda and FastAPI.
  * **Data Access**: A dedicated Data Access Layer (DAL) / repository module will separate SQL logic from service logic.

-----

## 11\. Unified Project Structure

(Detailed monorepo folder structure for apps and packages is defined here).

-----

## 12\. Development Workflow

(Prerequisites, setup steps, npm commands, and .env variable structures are defined here).

-----

## 13\. Deployment Architecture

  * **Frontend**: Deployed via AWS Amplify Hosting linked to the GitHub main branch.
  * **Backend**: Deployed via AWS CDK scripts run by a GitHub Actions CI/CD pipeline.
  * **Environments**: Separate configurations for Development, Staging, and Production.

-----

## 14\. Security and Performance

  * **Security**: Includes XSS prevention, input validation, rate limiting, and a strict CORS policy.
  * **Performance**: Includes code splitting, data caching (TanStack Query), CDN asset optimization, and efficient database-side query aggregation.

-----

## 15\. Testing Strategy

  * **Pyramid**: A strategy of many Unit tests, some Integration tests, and few E2E tests.
  * **Tools**: Jest & RTL (Frontend), Pytest (Backend), Playwright (E2E).

-----

## 16\. Coding Standards

  * **Critical Rules**: Defines mandatory rules for type sharing, environment variables, and service layer usage.
  * **Naming Conventions**: Specifies conventions for files and code elements for both frontend and backend.

-----

## 17\. Error Handling Strategy

  * **Unified Approach**: Defines a standard JSON error format, and outlines how errors are caught, logged, and presented to the user on both the frontend and backend.

-----

## 18\. Monitoring and Observability

  * **Stack**: Uses AWS CloudWatch RUM for frontend and Amazon CloudWatch for backend logs and metrics.
  * **Key Metrics**: Defines key frontend (Core Web Vitals) and backend (error rates, latency) metrics to track.