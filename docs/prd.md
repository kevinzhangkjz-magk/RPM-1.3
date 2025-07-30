# RPM 1.3 Product Requirements Document (PRD)

## 1. Goals and Background Context

### Goals
* Deliver an MVP of the RPM 1.3 platform by August 15th, 2025, that successfully enables core performance analysis workflows.
* Drastically reduce the time it takes for an asset manager to diagnose underperformance, from hours or days down to minutes.
* Increase asset revenue by minimizing lost production volume through faster fault resolution.
* Consolidate the diagnostic workflow by replacing manual, multi-tool processes with a single, integrated platform.

### Background Context
The current process for diagnosing solar asset underperformance is inefficient and fragmented. Asset managers must manually analyze data across multiple tools, leading to significant delays in identifying the root cause of issues. This reactive workflow results in prolonged asset downtime and preventable revenue loss. RPM 1.3 is being developed to address these inefficiencies by creating a unified, AI-enhanced platform that provides rapid, hierarchical visualization and diagnostics, enabling a shift from reactive troubleshooting to proactive asset management.

### Change Log
| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 2025-07-28 | 1.0 | Initial PRD Draft | John (PM) |

## 2. Requirements

### Functional
* **FR1**: The system shall display a time-series power curve for a selected solar site, plotting actual power against the expected 8760 model data.
* **FR2**: From a site-level view, the user shall be able to drill down to view the performance of individual skids associated with that site.
* **FR3**: From a skid-level view, the user shall be able to drill down to view the performance of individual inverters associated with that skid.
* **FR4**: The user shall be able to filter all power curve visualizations to include only data points where inverter availability is 100%.
* **FR5**: The system shall provide a text-based chat interface for a user to submit diagnostic queries.
* **FR6**: The AI assistant shall answer the five predefined diagnostic questions by providing a text summary and generating a supporting data visualization.
* **FR7**: The user shall be able to add, remove, and arrange predefined widgets (performance leaderboard, active alerts, power curves) on a personal dashboard.
* **FR8**: The system shall provide a "Save Dashboard" function to persist the user's dashboard layout.

### Non-Functional
* **NFR1**: All power curve visualizations and AI query responses must load in under 5 seconds for a typical one-week data query.
* **NFR2**: The system shall be built using a Python-based backend and a modern JavaScript frontend (e.g., React/Next.js with ShadCN or Streamlit).
* **NFR3**: The system shall query data exclusively from the existing AWS Redshift database.
* **NFR4**: The system architecture must be scalable to support the entire DESRI portfolio of sites, beyond the initial eight.
* **NFR5**: The system must require user authentication and authorization to control access to data.

## 3. User Interface Design Goals

### Overall UX Vision
The user experience will be clean, simple, and highly intuitive, prioritizing data clarity and speed. The design should empower asset managers to move seamlessly from high-level performance detection to granular diagnosis with minimal friction, making a complex analysis process feel straightforward and powerful.

### Key Interaction Paradigms
* **Hierarchical Drill-Down**: The core interaction model will be clicking through visual layers of data.
* **Natural Language Query**: Users will interact with the AI assistant through a persistent, text-based chat interface.
* **Dashboard Customization**: Users will arrange widgets on their dashboard, likely via drag-and-drop functionality.

### Core Screens and Views
* **Main Dashboard**: The user's customizable landing page.
* **Site Analysis View**: The primary workspace for displaying the power curve and hierarchical data.
* **AI Assistant Interface**: The chat panel, accessible from all views.
* **Login Screen**: A standard interface for user authentication.

### Accessibility
* **Standard**: WCAG AA.

### Branding
* **Inspiration**: The design will follow the branding established by the **desri.com** website.
* **Aesthetic**: A professional, clean, and analytically rigorous feel, using a minimalist design with generous white space.
* **Color Palette**: A dominant white background, with shades of deep blue and a calm, light teal/green for accents.
* **Typography**: A clean, modern sans-serif font for readability.

### Target Device and Platforms
* **Primary**: Web Responsive, with a design optimized for desktop browser use.

## 4. Technical Assumptions

### Repository Structure
* To be determined by the Architect, but a monorepo is recommended to simplify dependency management.

### Service Architecture
* The system should be designed with a decoupled architecture (e.g., microservices or serverless) to support scalability.

### Testing Requirements
* The project will require a comprehensive testing suite, including unit, integration, and end-to-end (E2E) tests.

### Additional Technical Assumptions and Requests
* **Frontend**: React or Next.js with the ShadCN component toolkit. Streamlit is a potential alternative.
* **Backend**: A Python-based framework such as FastAPI or Flask.
* **Database**: AWS Redshift.
* **Infrastructure**: Amazon Web Services (AWS).

## 5. Epic List

* **Epic 1: Foundational Setup & Site-Level Visualization**
    * **Goal**: Establish the project's technical foundation and deliver the core site-level power curve visualization.
* **Epic 2: Hierarchical Drill-Down & Data Filtering**
    * **Goal**: Implement the full hierarchical drill-down capability (Site → Skid → Inverter) and the 100% availability filter.
* **Epic 3: AI Assistant & Dashboard Customization**
    * **Goal**: Introduce the AI diagnostic assistant for query-based analysis and implement the customizable user dashboard.

## 6. Epic 1: Foundational Setup & Site-Level Visualization
**Expanded Goal**: This epic establishes the technical groundwork and delivers the first functional screen: a site-level performance view where a user can select one of the eight initial sites and see its actual vs. expected power curve.

### Story 1.1: Project Scaffolding & CI/CD Setup
**As a** Developer, **I want** a structured monorepo with separate frontend and backend packages and a basic CI/CD pipeline, **so that** I have a stable foundation to build and deploy the application.
**Acceptance Criteria:** 1. A monorepo is initialized. 2. A frontend application shell is created. 3. A backend application shell is created. 4. A basic CI/CD pipeline is configured to run linter checks and build both applications.

### Story 1.2: Backend API for Site Performance Data
**As the** Frontend Application, **I want** a secure API endpoint to retrieve the time-series performance data for a specific site, **so that** I can display it on a power curve.
**Acceptance Criteria:** 1. An API endpoint `GET /api/sites/{site_id}/performance` is created. 2. The endpoint accepts `site_id`, `start_date`, and `end_date`. 3. It connects to Redshift and retrieves performance data. 4. It correctly filters for 100% inverter availability. 5. It returns data in a valid JSON format. 6. The endpoint requires user authentication.

### Story 1.3: Site Selection UI
**As a** Solar Asset Manager, **I want** to see a list of available solar sites and select one, **so that** I can view its performance data.
**Acceptance Criteria:** 1. The UI displays a list of the eight initial solar sites. 2. A user can click on a site. 3. Selecting a site navigates to the Site Analysis View for that site.

### Story 1.4: Site-Level Power Curve Visualization
**As a** Solar Asset Manager, **I want** to view a power curve chart for a selected site, **so that** I can visually compare its actual performance against the expected model.
**Acceptance Criteria:** 1. The Site Analysis View displays a chart. 2. X-axis is POA Irradiance, Y-axis is Power. 3. Plots 'actual power' data points in one color. 4. Plots 'expected power' data points in another color. 5. Displays the 'expected power' model as a trend line. 6. User can toggle visibility of data points and trend line. 7. Displays calculated RMSE and R-squared values. 8. Fetches data from the API in Story 1.2.

## 7. Epic 2: Hierarchical Drill-Down & Data Filtering
**Expanded Goal**: This epic introduces the core interactive feature: the ability to drill down through the asset hierarchy to isolate underperforming components.

### Story 2.1: Backend API for Skid & Inverter Data
**As the** Frontend Application, **I want** new API endpoints to retrieve performance data for all skids on a site and all inverters on a skid, **so that** I can populate the drill-down views.
**Acceptance Criteria:** 1. A `GET /api/sites/{site_id}/skids` endpoint is created. 2. A `GET /api/skids/{skid_id}/inverters` endpoint is created. 3. Both endpoints filter for 100% availability. 4. API responses are optimized for speed.

### Story 2.2: Skid-Level Visualization UI
**As a** Solar Asset Manager, **I want** to click on a site and see a comparative view of all its skids, **so that** I can identify which skids are underperforming.
**Acceptance Criteria:** 1. A "View Skids" UI element is available. 2. Clicking it transitions to a Skid-Level View. 3. The view displays a comparative visualization of all skids. 4. The view highlights underperforming skids.

### Story 2.3: Inverter-Level Visualization UI
**As a** Solar Asset Manager, **I want** to select an underperforming skid and see a comparative view of all its inverters, **so that** I can pinpoint the specific faulty inverter.
**Acceptance Criteria:** 1. A user can select a skid from the Skid-Level View. 2. Selecting a skid transitions to an Inverter-Level View. 3. The view displays a comparative visualization of all inverters. 4. The view highlights the specific underperforming inverter(s).

### Story 2.4: GHI/POA Sensor View Toggle
**As a** Solar Asset Manager, **I want** to switch my power curve analysis between using Plane of Array (POA) and Global Horizontal Irradiance (GHI), **so that** I can validate sensor data.
**Acceptance Criteria:** 1. Backend APIs can optionally switch between POA and GHI data. 2. A UI toggle exists on all analysis views to switch between POA and GHI. 3. The chart and statistics update correctly when toggled.

## 8. Epic 3: AI Assistant & Dashboard Customization
**Expanded Goal**: This epic delivers the AI assistant that can answer diagnostic questions and the customizable dashboard for a personalized user experience.

### Story 3.1: Backend API for AI Assistant
**As the** Frontend Application, **I want** a single API endpoint that can process natural language queries, **so that** I can provide users with AI-driven diagnostic answers.
**Acceptance Criteria:** 1. A `POST /api/query` endpoint is created. 2. It accepts a natural language question. 3. It translates the question into a SQL query. 4. It returns a structured JSON response with a summary and data. 5. It can answer the five predefined diagnostic questions.

### Story 3.2: AI Assistant Chat UI
**As a** Solar Asset Manager, **I want** a persistent chat interface, **so that** I can ask diagnostic questions from anywhere in the application.
**Acceptance Criteria:** 1. A chat icon is persistent in the bottom-right corner. 2. Clicking opens a chat panel. 3. User can type and submit questions. 4. The panel displays the conversation. 5. It can render visualizations returned by the AI.

### Story 3.3: Dashboard Widget Implementation
**As a** Developer, **I want** reusable dashboard widgets for the performance leaderboard, active alerts, and power curves, **so that** they can be added to the customizable dashboard.
**Acceptance Criteria:** 1. A "Performance Leaderboard" widget is created. 2. An "Active Alerts" widget is created (can be a placeholder for MVP). 3. A "Power Curve" widget is created.

### Story 3.4: Dashboard Customization & Persistence
**As a** Solar Asset Manager, **I want** to arrange widgets on my dashboard and save the layout, **so that** my preferred view is available every time I log in.
**Acceptance Criteria:** 1. The dashboard is a grid where widgets can be managed. 2. A "Save Dashboard" button exists. 3. Clicking the button saves the layout to the user's profile. 4. The user's saved layout loads by default on login.