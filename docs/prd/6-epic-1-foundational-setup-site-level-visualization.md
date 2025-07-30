# 6. Epic 1: Foundational Setup & Site-Level Visualization
**Expanded Goal**: This epic establishes the technical groundwork and delivers the first functional screen: a site-level performance view where a user can select one of the eight initial sites and see its actual vs. expected power curve.

## Story 1.1: Project Scaffolding & CI/CD Setup
**As a** Developer, **I want** a structured monorepo with separate frontend and backend packages and a basic CI/CD pipeline, **so that** I have a stable foundation to build and deploy the application.
**Acceptance Criteria:** 1. A monorepo is initialized. 2. A frontend application shell is created. 3. A backend application shell is created. 4. A basic CI/CD pipeline is configured to run linter checks and build both applications.

## Story 1.2: Backend API for Site Performance Data
**As the** Frontend Application, **I want** a secure API endpoint to retrieve the time-series performance data for a specific site, **so that** I can display it on a power curve.
**Acceptance Criteria:** 1. An API endpoint `GET /api/sites/{site_id}/performance` is created. 2. The endpoint accepts `site_id`, `start_date`, and `end_date`. 3. It connects to Redshift and retrieves performance data. 4. It correctly filters for 100% inverter availability. 5. It returns data in a valid JSON format. 6. The endpoint requires user authentication.

## Story 1.3: Site Selection UI
**As a** Solar Asset Manager, **I want** to see a list of available solar sites and select one, **so that** I can view its performance data.
**Acceptance Criteria:** 1. The UI displays a list of the eight initial solar sites. 2. A user can click on a site. 3. Selecting a site navigates to the Site Analysis View for that site.

## Story 1.4: Site-Level Power Curve Visualization
**As a** Solar Asset Manager, **I want** to view a power curve chart for a selected site, **so that** I can visually compare its actual performance against the expected model.
**Acceptance Criteria:** 1. The Site Analysis View displays a chart. 2. X-axis is POA Irradiance, Y-axis is Power. 3. Plots 'actual power' data points in one color. 4. Plots 'expected power' data points in another color. 5. Displays the 'expected power' model as a trend line. 6. User can toggle visibility of data points and trend line. 7. Displays calculated RMSE and R-squared values. 8. Fetches data from the API in Story 1.2.
