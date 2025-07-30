# 2\. High Level Architecture

## Technical Summary

This architecture describes a modern, cloud-native web application on AWS, featuring a Next.js frontend and a serverless Python backend. The layers communicate via a public REST API for the MVP. This serverless, decoupled approach is designed for performance and scalability.

## Platform and Infrastructure Choice

  * **Platform**: **Amazon Web Services (AWS)**.
  * **Key Services**: AWS Amplify (Frontend Hosting), AWS Lambda (Backend Compute), Amazon API Gateway (API Layer), AWS Redshift (Database).
  * **Deployment Regions**: Placeholder: `us-east-1`. **Note**: The final region must be confirmed to be the same as the existing Redshift cluster to minimize latency.

## Repository Structure

  * **Structure**: A **Monorepo** managed by **Turborepo**.
  * **Organization**: An `apps` directory for `web` and `api`, and a `packages` directory for shared code.

## High Level Architecture Diagram

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

## Architectural Patterns

  * **Jamstack Architecture**: For a performant, scalable, and secure frontend.
  * **Serverless Architecture**: For a cost-efficient and auto-scaling backend.
  * **API Gateway Pattern**: To centralize routing and security for the API.

-----
