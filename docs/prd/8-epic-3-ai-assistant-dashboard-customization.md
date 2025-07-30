# 8. Epic 3: AI Assistant & Dashboard Customization
**Expanded Goal**: This epic delivers the AI assistant that can answer diagnostic questions and the customizable dashboard for a personalized user experience.

## Story 3.1: Backend API for AI Assistant
**As the** Frontend Application, **I want** a single API endpoint that can process natural language queries, **so that** I can provide users with AI-driven diagnostic answers.
**Acceptance Criteria:** 1. A `POST /api/query` endpoint is created. 2. It accepts a natural language question. 3. It translates the question into a SQL query. 4. It returns a structured JSON response with a summary and data. 5. It can answer the five predefined diagnostic questions.

## Story 3.2: AI Assistant Chat UI
**As a** Solar Asset Manager, **I want** a persistent chat interface, **so that** I can ask diagnostic questions from anywhere in the application.
**Acceptance Criteria:** 1. A chat icon is persistent in the bottom-right corner. 2. Clicking opens a chat panel. 3. User can type and submit questions. 4. The panel displays the conversation. 5. It can render visualizations returned by the AI.

## Story 3.3: Dashboard Widget Implementation
**As a** Developer, **I want** reusable dashboard widgets for the performance leaderboard, active alerts, and power curves, **so that** they can be added to the customizable dashboard.
**Acceptance Criteria:** 1. A "Performance Leaderboard" widget is created. 2. An "Active Alerts" widget is created (can be a placeholder for MVP). 3. A "Power Curve" widget is created.

## Story 3.4: Dashboard Customization & Persistence
**As a** Solar Asset Manager, **I want** to arrange widgets on my dashboard and save the layout, **so that** my preferred view is available every time I log in.
**Acceptance Criteria:** 1. The dashboard is a grid where widgets can be managed. 2. A "Save Dashboard" button exists. 3. Clicking the button saves the layout to the user's profile. 4. The user's saved layout loads by default on login.