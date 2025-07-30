# 13\. Deployment Architecture

  * **Frontend**: Deployed via AWS Amplify Hosting linked to the GitHub main branch.
  * **Backend**: Deployed via AWS CDK scripts run by a GitHub Actions CI/CD pipeline.
  * **Environments**: Separate configurations for Development, Staging, and Production.

-----
