# RPM Solar Performance Management System v1.3 - Technical Specification

## Executive Summary

The RPM (Relative Performance Machine) 1.3 is a comprehensive solar asset performance monitoring and analysis platform designed to reduce diagnostic time from hours/days to minutes through hierarchical drill-down capabilities and AI-enhanced diagnostics. The system provides real-time performance monitoring with customizable dashboards for solar portfolio management.

## System Architecture

### High-Level Architecture
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   Browser   │───▶│ AWS Amplify  │───▶│ API Gateway │───▶│ AWS Lambda   │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
                                                                   │
                                                                   ▼
                                                           ┌──────────────┐
                                                           │ AWS Redshift │
                                                           └──────────────┘
```

### Architecture Principles
- **Serverless-First**: AWS Lambda for auto-scaling backend
- **Decoupled Design**: Independent frontend and backend deployments
- **Data-Driven**: Direct connection to solar performance data warehouse
- **Type-Safe**: Full TypeScript implementation with runtime validation

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Frontend** |
| Framework | Next.js | 15.4.5 | React-based full-stack framework |
| Language | TypeScript | 5.4+ | Type-safe development |
| UI Library | ShadCN/UI + Radix | Latest | Accessible component system |
| State Mgmt | TanStack Query | 5.83.0 | Server state and caching |
| Styling | Tailwind CSS | 4.x | Utility-first CSS framework |
| Charts | Recharts | 3.1.0 | Solar performance visualizations |
| **Backend** |
| Framework | FastAPI | 0.104.0+ | High-performance Python API |
| Language | Python | 3.11+ | Backend development |
| ORM | SQLAlchemy | 2.0.0+ | Database abstraction |
| Validation | Pydantic | 2.0.0+ | Data modeling and validation |
| **Data** |
| Database | AWS Redshift | N/A | Columnar data warehouse |
| Driver | psycopg2 | 2.9.0+ | PostgreSQL protocol driver |
| **Infrastructure** |
| Build System | Turborepo | 1.12.4+ | Monorepo orchestration |
| Deployment | AWS CDK | Latest | Infrastructure as Code |
| CI/CD | GitHub Actions | N/A | Automated deployments |

## API Specification

### Base Configuration
- **Base URL**: `http://localhost:8000` (dev) / `https://api.rpm.solar` (prod)
- **Authentication**: HTTP Basic Authentication (MVP) → JWT (Production)
- **Content-Type**: `application/json`
- **CORS**: Configured for frontend origins

### Core Endpoints

#### Sites Management

**GET /api/sites/**
```http
GET /api/sites/
Authorization: Basic {base64(username:password)}
```

**Response Schema:**
```json
{
  "sites": [
    {
      "site_id": "ASMB3",
      "site_name": "Assembly III",
      "location": "MI",
      "capacity_kw": 79.0,
      "installation_date": "2022-01-14",
      "status": "active",
      "connectivity_status": "connected"
    }
  ],
  "total_count": 35
}
```

**GET /api/sites/{site_id}/performance**
```http
GET /api/sites/ASMB3/performance?start_date=2025-01-01T00:00:00Z&end_date=2025-01-31T23:59:59Z
Authorization: Basic {base64(username:password)}
```

**Response Schema:**
```json
{
  "site_id": "ASMB3",
  "site_name": "Assembly III",
  "data_points": [
    {
      "timestamp": "2025-01-15T12:00:00Z",
      "poa_irradiance": 850.5,
      "actual_power": 456.2,
      "expected_power": 475.8,
      "inverter_availability": 1.0
    }
  ],
  "summary": {
    "data_point_count": 1440,
    "avg_actual_power": 387.5,
    "avg_expected_power": 402.1,
    "rmse": 23.4,
    "r_squared": 0.94
  }
}
```

#### Health Monitoring

**GET /health**
- **Purpose**: System health check
- **Response**: `{"status": "healthy"}`

### Error Handling
All endpoints return structured errors:
```json
{
  "detail": {
    "error": "ValidationError",
    "message": "Site with ID 'INVALID' not found",
    "details": {"site_id": "INVALID"}
  }
}
```

**HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (validation errors)
- `401`: Unauthorized
- `404`: Resource not found
- `500`: Internal server error

## Data Models

### Backend Models (Pydantic)

```python
class SiteDetails(BaseModel):
    """Complete site information with metadata"""
    site_id: str = Field(..., description="Unique site identifier")
    site_name: Optional[str] = Field(None, description="Human-readable site name")
    location: Optional[str] = Field(None, description="Geographic location")
    capacity_kw: Optional[float] = Field(None, ge=0, description="Total capacity in kilowatts")
    installation_date: Optional[date] = Field(None, description="Installation date")
    status: Optional[str] = Field(None, description="Operational status")
    connectivity_status: Optional[str] = Field(None, description="Data connectivity status")

class PerformanceDataPoint(BaseModel):
    """Individual performance measurement"""
    timestamp: datetime = Field(..., description="Measurement timestamp")
    poa_irradiance: float = Field(..., ge=0, description="Plane of Array Irradiance (W/m²)")
    actual_power: float = Field(..., ge=0, description="Actual power output (kW)")
    expected_power: float = Field(..., ge=0, description="Expected power output (kW)")
    inverter_availability: float = Field(..., ge=0, le=1, description="Inverter availability factor")

class SiteDataSummary(BaseModel):
    """Performance statistics summary"""
    data_point_count: int = Field(..., ge=0)
    avg_actual_power: float = Field(..., ge=0)
    avg_expected_power: float = Field(..., ge=0)
    avg_poa_irradiance: float = Field(..., ge=0)
    first_reading: datetime
    last_reading: datetime
```

### Frontend Models (TypeScript)

```typescript
export interface Site {
  site_id: string;
  site_name?: string;
  location?: string;
  capacity_kw?: number;
  installation_date?: string;
  status?: string;
  connectivity_status?: 'connected' | 'disconnected';
}

export interface PerformanceDataPoint {
  poa_irradiance: number;
  actual_power: number;
  expected_power: number;
}

export interface SitePerformanceResponse {
  site_id: string;
  data_points: PerformanceDataPoint[];
  rmse: number;
  r_squared: number;
}
```

## Database Schema

### Primary Database: AWS Redshift
- **Host**: `data-analytics.crmjfkw9o04v.us-east-1.redshift.amazonaws.com`
- **Database**: `desri_analytics`
- **Connection**: SSL required, connection pooling enabled

### Core Tables

#### analytics.site_metadata
**Purpose**: Master site registry with metadata
```sql
CREATE TABLE analytics.site_metadata (
    site VARCHAR(50) PRIMARY KEY,           -- Site code (e.g., 'ASMB3')
    site_name VARCHAR(255),                 -- Human-readable name
    inverter_manufacturer VARCHAR(100),     -- Equipment details
    inverter_count INTEGER,
    dc_capacity DECIMAL(10,2),             -- DC capacity rating
    ac_capacity_technical DECIMAL(10,2),   -- Technical AC capacity
    ac_capacity_poi_limited DECIMAL(10,2), -- POI-limited AC capacity
    bifacial BOOLEAN,                      -- Panel type indicator
    asset_manager VARCHAR(255),            -- Responsible manager
    state VARCHAR(2),                      -- US state code
    utc_offset_std INTEGER,                -- Standard time offset
    utc_offset_dst INTEGER,                -- Daylight time offset
    comments TEXT,                         -- Additional notes
    site_id INTEGER,                       -- Numeric site ID
    cod_date DATE,                         -- Commercial operation date
    region VARCHAR(100),                   -- Geographic region
    ppa_price DECIMAL(10,4)               -- Power purchase agreement price
);
```

#### Time-Series Data Tables (Per Site)
**Pattern**: `dataanalytics.public.desri_{site}_{year}_{month}`
**Example**: `dataanalytics.public.desri_ASMB3_2025_07`

```sql
CREATE TABLE dataanalytics.public.desri_ASMB3_2025_07 (
    site VARCHAR(50),                      -- Site identifier
    timestamp TIMESTAMP,                   -- Data timestamp
    tag VARCHAR(50),                       -- Measurement type
    devicetype VARCHAR(100),               -- Device category
    device VARCHAR(255),                   -- Specific device ID
    value DECIMAL(15,6)                    -- Measurement value
);
```

**Key Data Types:**
- **Power Generation**: `tag = 'P'`, `devicetype = 'rmt'` (Revenue Meter)
- **Solar Irradiance**: `tag = 'POA'`, `devicetype = 'Met'` (Plane of Array)
- **Weather Data**: `tag IN ('GHI', 'BOM_TEMP')`, `devicetype = 'Met'`
- **Inverter Performance**: `tag = 'P'`, `devicetype = 'Inverter'`

### Connectivity Status Logic
```sql
-- Current implementation (interim solution)
CASE 
    WHEN site IN ('ASMB1', 'ASMB2', 'ASMB3', 'IRIS1', 'STJM1') THEN 'connected'
    WHEN cod_date > CURRENT_DATE - INTERVAL '2 years' THEN 'connected'
    ELSE 'disconnected'
END as connectivity_status

-- Planned implementation (data-driven)
CASE 
    WHEN last_data_timestamp > CURRENT_DATE - INTERVAL '7 days' 
        AND power_records > 0 
        AND met_records > 0 
    THEN 'connected'
    ELSE 'disconnected'
END as connectivity_status
```

## Frontend Architecture

### Application Structure
```
src/
├── app/                           # Next.js App Router
│   ├── layout.tsx                # Root layout with providers
│   ├── page.tsx                  # Landing page
│   ├── portfolio/                # Site portfolio section
│   │   ├── page.tsx             # Sites grid view
│   │   └── [siteId]/            # Individual site analysis
│   │       └── page.tsx         # Power curve visualization
├── components/
│   ├── providers/               # React context providers
│   │   └── QueryProvider.tsx   # TanStack Query configuration
│   └── ui/                      # Reusable UI components
│       ├── button.tsx
│       ├── card.tsx
│       └── switch.tsx
├── lib/
│   ├── api/                     # API client and query functions
│   │   └── sites.ts
│   └── utils.ts                 # Utility functions and calculations
└── types/
    └── site.ts                  # TypeScript type definitions
```

### Key Components

#### Portfolio Dashboard (`/portfolio`)
**Features:**
- Responsive grid layout for site cards
- Real-time connectivity status indicators
- Site metadata display (location, capacity, installation date)
- Search and filtering capabilities (planned)
- Aggregate portfolio statistics

**Implementation:**
```tsx
export default function PortfolioPage() {
  const { data: sitesData, isLoading, error } = useQuery({
    queryKey: sitesQueryKeys.lists(),
    queryFn: sitesApi.getSites,
  });

  // Status indicator logic
  <div className={`w-2 h-2 rounded-full ${
    site.connectivity_status === 'connected' 
      ? 'bg-green-500' 
      : 'bg-red-500'
  }`} />
}
```

#### Site Analysis (`/portfolio/[siteId]`)
**Features:**
- Power curve scatter plot (Actual vs Expected Power)
- Interactive chart controls and data filtering
- Statistical performance metrics (RMSE, R²)
- Performance summary cards
- Export capabilities (planned)

**Chart Configuration:**
```tsx
<ResponsiveContainer width="100%" height={400}>
  <ScatterChart data={performanceData}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="poa_irradiance" name="POA Irradiance" unit=" W/m²" />
    <YAxis dataKey="actual_power" name="Power" unit=" kW" />
    <Tooltip />
    <Scatter name="Actual Power" dataKey="actual_power" fill="#8884d8" />
    <Scatter name="Expected Power" dataKey="expected_power" fill="#82ca9d" />
  </ScatterChart>
</ResponsiveContainer>
```

### State Management Strategy
- **Server State**: TanStack Query with intelligent caching
- **Local State**: React hooks for component-specific state
- **Query Keys**: Hierarchical structure for cache invalidation

```typescript
export const sitesQueryKeys = {
  all: ["sites"] as const,
  lists: () => [...sitesQueryKeys.all, "list"] as const,
  details: () => [...sitesQueryKeys.all, "detail"] as const,
  sitePerformance: (siteId: string) => 
    [...sitesQueryKeys.details(), siteId, "performance"] as const,
};
```

## Backend Architecture

### Project Structure
```
src/
├── api/
│   └── routes.py                # FastAPI route definitions
├── core/
│   ├── config.py               # Application configuration
│   ├── database.py             # Database connection management
│   └── security.py             # Authentication and security
├── dal/                        # Data Access Layer
│   ├── sites.py               # Sites repository
│   └── site_performance.py    # Performance data repository
├── models/
│   └── site_performance.py    # Pydantic data models
└── services/                   # Business logic layer (future)
```

### Core Components

#### Configuration Management
```python
class Settings(BaseSettings):
    """Application configuration with environment variable support"""
    app_name: str = "RPM Solar Performance API"
    app_version: str = "1.3.0"
    debug: bool = False
    
    # Database connection
    redshift_host: Optional[str] = None
    redshift_port: int = 5439
    redshift_database: Optional[str] = None
    redshift_user: Optional[str] = None
    redshift_password: Optional[str] = None
    redshift_ssl: bool = True
    
    # Authentication
    basic_auth_username: Optional[str] = None
    basic_auth_password: Optional[str] = None
    
    class Config:
        env_file = ".env"
```

#### Database Connection Management
```python
class DatabaseConnection:
    """Redshift connection manager with connection pooling"""
    
    def get_connection_string(self) -> str:
        return (
            f"redshift+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}?sslmode=require"
        )
    
    def get_engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(
                self.get_connection_string(),
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600
            )
        return self._engine
```

#### Data Access Layer
```python
class SitesRepository:
    """Repository pattern for site data access"""
    
    def get_all_sites(self) -> List[Dict[str, Any]]:
        """Retrieve all sites with connectivity status"""
        query = self._build_sites_query()
        with self.db_connection.get_engine().connect() as connection:
            result = connection.execute(text(query))
            return [dict(zip(result.keys(), row)) for row in result.fetchall()]
    
    def _build_sites_query(self) -> str:
        """Build dynamic SQL query with connectivity logic"""
        return """
            SELECT 
                site as site_id,
                site_name,
                state as location,
                ac_capacity_poi_limited as capacity_kw,
                cod_date as installation_date,
                'active' as status,
                CASE 
                    WHEN site IN ('ASMB1', 'ASMB2', 'ASMB3', 'IRIS1', 'STJM1') THEN 'connected'
                    WHEN cod_date > CURRENT_DATE - INTERVAL '2 years' THEN 'connected'
                    ELSE 'disconnected'
                END as connectivity_status
            FROM analytics.site_metadata
            WHERE site IS NOT NULL
            ORDER BY site_name ASC
        """
```

## Business Logic and Calculations

### Solar Performance Analytics

#### Statistical Metrics
```typescript
// Root Mean Square Error calculation
export function calculateRMSE(dataPoints: PerformanceDataPoint[]): number {
  const sumSquaredErrors = dataPoints.reduce((sum, point) => {
    const error = point.actual_power - point.expected_power;
    return sum + (error * error);
  }, 0);
  
  return Math.sqrt(sumSquaredErrors / dataPoints.length);
}

// R-Squared (Coefficient of Determination)
export function calculateRSquared(dataPoints: PerformanceDataPoint[]): number {
  const actualMean = dataPoints.reduce((sum, point) => 
    sum + point.actual_power, 0) / dataPoints.length;
  
  const totalSumSquares = dataPoints.reduce((sum, point) => {
    const diff = point.actual_power - actualMean;
    return sum + (diff * diff);
  }, 0);
  
  const residualSumSquares = dataPoints.reduce((sum, point) => {
    const diff = point.actual_power - point.expected_power;
    return sum + (diff * diff);
  }, 0);
  
  return 1 - (residualSumSquares / totalSumSquares);
}
```

#### Data Quality Filters
- **Inverter Availability**: Only include data where `inverter_availability = 1.0`
- **Positive Values**: Filter out negative or zero power readings
- **Date Range Validation**: Ensure end_date > start_date
- **Reasonable Bounds**: POA irradiance < 1500 W/m², power within capacity limits

### Performance Monitoring Logic

#### Connectivity Status Determination
**Current Approach (Interim):**
- Sites in active analysis scripts → 'connected'
- Sites installed within 2 years → 'connected'  
- All others → 'disconnected'

**Target Approach (Data-Driven):**
- Has data within last 7 days → 'connected'
- Missing data or poor quality → 'disconnected'
- Table structure validation
- Data completeness scoring

## Testing Strategy

### Frontend Testing
**Framework**: Jest + React Testing Library
**Coverage Areas**:
- Component rendering and user interactions
- API integration and error handling
- Performance calculation functions
- Responsive design behavior

```typescript
describe('PortfolioPage', () => {
  it('displays site connectivity status correctly', async () => {
    const mockSites = [
      { site_id: 'ASMB3', connectivity_status: 'connected' },
      { site_id: 'ARPT1', connectivity_status: 'disconnected' }
    ];
    
    render(<PortfolioPage />);
    
    expect(screen.getByTitle('Connected')).toBeInTheDocument();
    expect(screen.getByTitle('Disconnected')).toBeInTheDocument();
  });
});
```

### Backend Testing
**Framework**: Pytest
**Coverage Areas**:
- API endpoint functionality and error handling
- Database connection and query execution
- Authentication and security validation
- Data model validation and serialization

```python
def test_sites_endpoint_authentication():
    """Test that sites endpoint requires authentication"""
    response = client.get("/api/sites/")
    assert response.status_code == 401
    
    # Test with valid credentials
    credentials = base64.b64encode(b"testuser:testpass").decode()
    headers = {"Authorization": f"Basic {credentials}"}
    response = client.get("/api/sites/", headers=headers)
    assert response.status_code == 200
```

### Integration Testing
- End-to-end user workflows
- Database connectivity and query performance
- API response time and error handling
- Cross-browser compatibility

## Configuration and Environment

### Environment Variables

#### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend API base URL
```

#### Backend (.env)
```bash
# Application Settings
APP_NAME="RPM Solar Performance API"
APP_VERSION="1.3.0"
ENVIRONMENT=development
DEBUG=true

# Authentication
BASIC_AUTH_USERNAME=testuser
BASIC_AUTH_PASSWORD=testpass

# AWS Redshift Database
REDSHIFT_HOST=data-analytics.crmjfkw9o04v.us-east-1.redshift.amazonaws.com
REDSHIFT_PORT=5439
REDSHIFT_DATABASE=desri_analytics
REDSHIFT_USER=chail
REDSHIFT_PASSWORD=U2bqPmM88D2d
REDSHIFT_SSL=true

# AWS Settings
AWS_REGION=us-east-1
```

### Build Configuration

#### Frontend (package.json)
```json
{
  "scripts": {
    "dev": "next dev --port 3000",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  }
}
```

#### Backend (pyproject.toml)
```toml
[tool.poetry]
name = "rpm-backend"
version = "1.3.0"
description = "RPM Solar Performance API"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
pydantic = "^2.0.0"
sqlalchemy = "^2.0.0"
psycopg2-binary = "^2.9.0"
mangum = "^0.17.0"
```

## Deployment Architecture

### Development Environment
- **Frontend**: `localhost:3000` (Next.js dev server)
- **Backend**: `localhost:8000` (Uvicorn ASGI server) 
- **Database**: AWS Redshift (shared development cluster)
- **Authentication**: Basic auth with test credentials

### Production Environment (Planned)
- **Frontend**: AWS Amplify (static hosting with SSR)
- **Backend**: AWS Lambda + API Gateway (serverless)
- **Database**: AWS Redshift (dedicated production cluster)
- **Authentication**: JWT with AWS Cognito
- **CDN**: AWS CloudFront for global distribution
- **Monitoring**: AWS CloudWatch + X-Ray tracing

### Infrastructure as Code
```typescript
// AWS CDK Stack (planned)
export class RpmInfrastructureStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    // Lambda function for API
    const apiFunction = new Function(this, 'RpmApiFunction', {
      runtime: Runtime.PYTHON_3_11,
      handler: 'main.lambda_handler',
      code: Code.fromAsset('dist/backend'),
      timeout: Duration.seconds(30)
    });

    // API Gateway
    const api = new LambdaRestApi(this, 'RpmApi', {
      handler: apiFunction,
      proxy: false
    });

    // Amplify for frontend hosting
    const amplifyApp = new App(this, 'RpmFrontend', {
      sourceCodeProvider: new GitHubSourceCodeProvider({
        owner: 'your-org',
        repository: 'rpm-solar',
        oauthToken: SecretValue.secretsManager('github-token')
      })
    });
  }
}
```

## Performance and Scalability

### Frontend Performance
- **Code Splitting**: Automatic route-based splitting with Next.js
- **Image Optimization**: Next.js Image component with WebP support
- **Caching Strategy**: 
  - Static assets: 1 year cache
  - API responses: 1 minute stale time
  - Component memoization for expensive calculations

### Backend Performance
- **Connection Pooling**: SQLAlchemy with 5 connections, 10 overflow
- **Query Optimization**: Indexed queries, efficient JOINs
- **Response Caching**: Application-level caching planned
- **Async Processing**: FastAPI async/await for I/O operations

### Database Performance
- **Columnar Storage**: Redshift optimized for analytical queries
- **Distribution Keys**: Proper data distribution across nodes
- **Sort Keys**: Optimized for time-series queries
- **Compression**: Automatic column compression

### Scalability Considerations
- **Serverless Architecture**: Auto-scaling Lambda functions
- **CDN Distribution**: Global edge caching with CloudFront
- **Database Scaling**: Redshift cluster auto-scaling
- **Load Balancing**: Application Load Balancer for high availability

## Security Implementation

### Authentication & Authorization
**Current (MVP)**:
- HTTP Basic Authentication with configurable credentials
- Constant-time password comparison to prevent timing attacks
- SSL/TLS encryption for all database connections

**Planned (Production)**:
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- OAuth2 integration with enterprise SSO
- API key management for external integrations

### Data Security
- **Encryption at Rest**: Redshift automatic encryption
- **Encryption in Transit**: TLS 1.2+ for all connections
- **Input Validation**: Pydantic models with strict validation
- **SQL Injection Prevention**: Parameterized queries with SQLAlchemy
- **CORS Configuration**: Restricted to known frontend origins

### Security Headers
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.rpm.solar"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

## Monitoring and Observability

### Application Monitoring
- **Health Checks**: `/health` endpoint for load balancer health checks
- **Structured Logging**: JSON-formatted logs for centralized aggregation
- **Error Tracking**: Sentry integration for error monitoring
- **Performance Metrics**: Response time and throughput monitoring

### Business Metrics
- **Site Connectivity**: Real-time tracking of connected vs disconnected sites
- **API Usage**: Endpoint utilization and user activity patterns
- **Performance Analytics**: Solar generation vs expected performance trends
- **User Engagement**: Feature adoption and usage analytics

### Alerting Strategy
- **System Health**: API availability and response time alerts
- **Data Quality**: Missing data or stale data notifications
- **Security Events**: Authentication failures and suspicious activity
- **Business KPIs**: Performance degradation alerts for critical sites

## Site Connectivity Status System

### Current Implementation
The system uses a hybrid approach to determine site connectivity:

```sql
CASE 
    -- Sites actively used in analysis scripts
    WHEN site IN ('ASMB1', 'ASMB2', 'ASMB3', 'IRIS1', 'STJM1') THEN 'connected'
    -- Recently installed sites (likely active)
    WHEN cod_date > CURRENT_DATE - INTERVAL '2 years' THEN 'connected'
    -- All others marked as disconnected
    ELSE 'disconnected'
END as connectivity_status
```

### Target Implementation: Working Data Table Approach

A site is considered "connected" if it has a **working data table** meeting these criteria:

#### 1. Table Existence
- Monthly data table exists: `dataanalytics.public.desri_{site}_{year}_{month}`
- Table is accessible and not corrupted
- Proper schema structure with required columns

#### 2. Data Recency
- Contains data within the last 7-30 days
- Most recent timestamp is within expected operational window
- No extended gaps during expected operational hours

#### 3. Data Quality
- **Power Data**: Contains meter readings (`tag = 'P'`, `devicetype = 'rmt'`)
- **Meteorological Data**: Weather data (`tag IN ('GHI','POA','BOM_TEMP')`, `devicetype = 'Met'`)
- **Inverter Data**: Performance data (`tag = 'P'`, `devicetype = 'Inverter'`)
- Data values are reasonable (not all zeros, nulls, or erroneous values)

#### 4. Data Pipeline Health
- Table is being actively updated
- Data ingestion follows expected patterns
- No signs of pipeline failures or corruption

### Implementation Example
```sql
WITH site_table_health AS (
    SELECT 
        site,
        MAX(timestamp) as last_data_timestamp,
        COUNT(*) as total_records,
        COUNT(CASE WHEN tag = 'P' AND devicetype = 'rmt' THEN 1 END) as power_records,
        COUNT(CASE WHEN tag IN ('GHI','POA','BOM_TEMP') AND devicetype = 'Met' THEN 1 END) as met_records,
        AVG(CASE WHEN tag = 'P' AND devicetype = 'rmt' AND value > 0 THEN value END) as avg_power
    FROM dataanalytics.public.desri_{site}_{year}_{month}
    WHERE timestamp > CURRENT_DATE - INTERVAL '30 days'
    GROUP BY site
)
SELECT 
    sm.site as site_id,
    sm.site_name,
    CASE 
        WHEN sth.last_data_timestamp > CURRENT_DATE - INTERVAL '7 days' 
            AND sth.power_records > 0 
            AND sth.met_records > 0 
            AND sth.avg_power IS NOT NULL 
        THEN 'connected'
        ELSE 'disconnected'
    END as connectivity_status
FROM analytics.site_metadata sm
LEFT JOIN site_table_health sth ON sm.site = sth.site
```

## Future Roadmap

### Phase 2: Enhanced Analytics (Q2 2025)
- **Hierarchical Drill-Down**: Site → Skid → Inverter level analysis
- **AI-Powered Diagnostics**: Natural language query interface
- **Advanced Visualizations**: Heat maps, trend analysis, comparative charts
- **Automated Alerts**: Performance anomaly detection and notifications
- **Mobile Interface**: Responsive design for field technicians

### Phase 3: Enterprise Features (Q3 2025)
- **Multi-Portfolio Management**: Cross-portfolio analysis and reporting
- **Work Order Integration**: Automated maintenance scheduling
- **Advanced Reporting**: Customizable reports and dashboards
- **Data Export**: PDF, Excel, and CSV export capabilities
- **Third-Party Integrations**: Weather data, market pricing, grid data

### Phase 4: AI and Automation (Q4 2025)
- **Predictive Maintenance**: ML-based equipment failure prediction
- **Performance Optimization**: AI-driven performance recommendations
- **Automated Root Cause Analysis**: Intelligent diagnostic workflows
- **Digital Twin Integration**: Virtual site modeling and simulation
- **Advanced Analytics**: Forecasting, scenario analysis, optimization

## Development Workflow

### Monorepo Structure
```
RPM-1.3/
├── apps/
│   ├── frontend/          # Next.js application
│   └── backend/           # FastAPI application
├── packages/              # Shared packages (future)
├── docs/                  # Documentation
├── infrastructure/        # AWS CDK code (planned)
└── turbo.json            # Turborepo configuration
```

### Available Commands
```bash
# Development
npm run dev              # Start both frontend and backend
npm run build            # Build both applications
npm run test             # Run all tests
npm run lint             # Lint all code
npm run type-check       # TypeScript type checking

# Individual apps
npm run dev:frontend     # Start only frontend
npm run dev:backend      # Start only backend
npm run test:frontend    # Test frontend only
npm run test:backend     # Test backend only
```

### Git Workflow
- **Main Branch**: `main` (production deployments)
- **Development**: Feature branches merged via pull requests
- **Release Process**: Semantic versioning with automated changelog
- **Current Version**: v1.3 (Active development)

## Conclusion

The RPM Solar Performance Management System v1.3 represents a comprehensive, scalable solution for solar asset monitoring and analysis. Built with modern web technologies and cloud-native architecture, it provides the foundation for advanced solar performance analytics while maintaining the flexibility to evolve with changing business needs.

The system's modular design, type-safe implementation, and focus on data quality ensure reliable performance monitoring capabilities that can scale from individual sites to large-scale solar portfolios.

---

**Document Version**: 1.0  
**Last Updated**: July 30, 2025  
**System Version**: RPM v1.3  
**Authors**: Technical Team  
**Next Review**: August 30, 2025