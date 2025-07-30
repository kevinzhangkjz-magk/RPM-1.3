# 7. Epic 2: Hierarchical Drill-Down & Data Filtering
**Expanded Goal**: This epic introduces the core interactive feature: the ability to drill down through the asset hierarchy to isolate underperforming components.

## Story 2.1: Backend API for Skid & Inverter Data
**As the** Frontend Application, **I want** new API endpoints to retrieve performance data for all skids on a site and all inverters on a skid, **so that** I can populate the drill-down views.
**Acceptance Criteria:** 1. A `GET /api/sites/{site_id}/skids` endpoint is created. 2. A `GET /api/skids/{skid_id}/inverters` endpoint is created. 3. Both endpoints filter for 100% availability. 4. API responses are optimized for speed.

## Story 2.2: Skid-Level Visualization UI
**As a** Solar Asset Manager, **I want** to click on a site and see a comparative view of all its skids, **so that** I can identify which skids are underperforming.
**Acceptance Criteria:** 1. A "View Skids" UI element is available. 2. Clicking it transitions to a Skid-Level View. 3. The view displays a comparative visualization of all skids. 4. The view highlights underperforming skids.

## Story 2.3: Inverter-Level Visualization UI
**As a** Solar Asset Manager, **I want** to select an underperforming skid and see a comparative view of all its inverters, **so that** I can pinpoint the specific faulty inverter.
**Acceptance Criteria:** 1. A user can select a skid from the Skid-Level View. 2. Selecting a skid transitions to an Inverter-Level View. 3. The view displays a comparative visualization of all inverters. 4. The view highlights the specific underperforming inverter(s).

## Story 2.4: GHI/POA Sensor View Toggle
**As a** Solar Asset Manager, **I want** to switch my power curve analysis between using Plane of Array (POA) and Global Horizontal Irradiance (GHI), **so that** I can validate sensor data.
**Acceptance Criteria:** 1. Backend APIs can optionally switch between POA and GHI data. 2. A UI toggle exists on all analysis views to switch between POA and GHI. 3. The chart and statistics update correctly when toggled.
