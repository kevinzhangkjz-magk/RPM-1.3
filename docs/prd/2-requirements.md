# 2. Requirements

## Functional
* **FR1**: The system shall display a time-series power curve for a selected solar site, plotting actual power against the expected 8760 model data.
* **FR2**: From a site-level view, the user shall be able to drill down to view the performance of individual skids associated with that site.
* **FR3**: From a skid-level view, the user shall be able to drill down to view the performance of individual inverters associated with that skid.
* **FR4**: The user shall be able to filter all power curve visualizations to include only data points where inverter availability is 100%.
* **FR5**: The system shall provide a text-based chat interface for a user to submit diagnostic queries.
* **FR6**: The AI assistant shall answer the five predefined diagnostic questions by providing a text summary and generating a supporting data visualization.
* **FR7**: The user shall be able to add, remove, and arrange predefined widgets (performance leaderboard, active alerts, power curves) on a personal dashboard.
* **FR8**: The system shall provide a "Save Dashboard" function to persist the user's dashboard layout.

## Non-Functional
* **NFR1**: All power curve visualizations and AI query responses must load in under 5 seconds for a typical one-week data query.
* **NFR2**: The system shall be built using a Python-based backend and a modern JavaScript frontend (e.g., React/Next.js with ShadCN or Streamlit).
* **NFR3**: The system shall query data exclusively from the existing AWS Redshift database.
* **NFR4**: The system architecture must be scalable to support the entire DESRI portfolio of sites, beyond the initial eight.
* **NFR5**: The system must require user authentication and authorization to control access to data.
