# UI/UX Specification: Relative Performance Machine (RPM) 1.3

## 1. Introduction & Principles

This document defines the user experience goals, information architecture, user flows, and visual design specifications for the RPM 1.3 user interface. It serves as the foundation for visual design and frontend development, ensuring a cohesive and user-centered experience.

### Target User Personas
* **Primary: Solar Asset Manager**: Responsible for the day-to-day performance of specific solar assets. Needs a fast, efficient tool to diagnose underperformance down to the component level.
* **Secondary: Regional Asset Manager**: Manages a team of asset managers and a regional portfolio. Needs high-level, aggregated views, primarily a ranked list of sites by performance deviation, to quickly identify the most critical issues across their region.

### Key Usability Goals
* **Efficiency**: An Asset Manager can trace an issue from a site-level view to a specific faulty inverter in under 5 minutes.
* **Clarity**: Data visualizations are clear, uncluttered, and immediately understandable.
* **Confidence**: Users trust the data, leading to faster, more confident dispatch decisions.
* **Discoverability**: The interface is intuitive, allowing users to find and use features without extensive training.

### Core Design Principles
1.  **Data-First, Clutter-Free**: The UI will be minimalist, ensuring data visualizations are the primary focus.
2.  **From Overview to Detail**: The application will support a seamless drill-down journey.
3.  **Actionable Insights, Not Just Data**: The tool will actively guide the user by highlighting anomalies.
4.  **Consistency is Key**: All interactions, colors, and terminology will be used consistently.

## 2. Information Architecture (IA)

### Site Map / Screen Inventory
```mermaid
graph TD
    A[Login Screen] --> B(Main Dashboard);
    B --> C{Portfolio View};
    C --> D[Site Analysis View];
    B --> E[User Settings];
    
    subgraph Global Elements
        F[AI Assistant - Overlay]
    end