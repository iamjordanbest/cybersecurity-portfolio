# GRC Analytics Platform - Technical Architecture

## System Overview

The GRC Analytics Platform is a production-ready compliance monitoring and risk analysis system built with Python, SQLite, and Streamlit. The architecture follows a layered design pattern with clear separation of concerns.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │   Streamlit    │  │   PDF Reports  │  │  CSV Exports   │   │
│  │   Dashboard    │  │   (Executive)  │  │  (Operations)  │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
│         │                     │                    │            │
└─────────┼─────────────────────┼────────────────────┼────────────┘
          │                     │                    │
┌─────────▼─────────────────────▼────────────────────▼────────────┐
│                       APPLICATION LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │Risk Scoring  │  │Trend Analysis│  │ROI Calculator│         │
│  │    Engine    │  │    Engine    │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │         Configuration Manager (YAML)              │          │
│  └──────────────────────────────────────────────────┘          │
│         │                     │                    │            │
└─────────┼─────────────────────┼────────────────────┼────────────┘
          │                     │                    │
┌─────────▼─────────────────────▼────────────────────▼────────────┐
│                      DATA ACCESS LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │            Database Manager (SQLite)              │          │
│  │  - CRUD Operations                                │          │
│  │  - Query Builder                                  │          │
│  │  - Transaction Management                         │          │
│  └──────────────────────────────────────────────────┘          │
│         │                     │                    │            │
└─────────┼─────────────────────┼────────────────────┼────────────┘
          │                     │                    │
┌─────────▼─────────────────────▼────────────────────▼────────────┐
│                     DATA INGESTION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │ Validator  │→ │   Parser   │→ │ Normalizer │               │
│  │ (Schema)   │  │   (ETL)    │  │ (Transform)│               │
│  └────────────┘  └────────────┘  └────────────┘               │
│         │                                                        │
└─────────┼────────────────────────────────────────────────────────┘
          │
┌─────────▼────────────────────────────────────────────────────────┐
│                       STORAGE LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   SQLite DB  │  │  NIST Catalog│  │Config Files  │         │
│  │  (grc.db)    │  │   (CSV/JSON) │  │   (YAML)     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Descriptions

### 1. Presentation Layer

#### 1.1 Streamlit Dashboard (`src/dashboard/app.py`)
**Purpose:** Interactive web-based dashboard for real-time compliance monitoring

**Features:**
- Overview panel with key metrics
- Risk analysis charts and tables
- Trend visualization (6-12 months)
- Interactive filters (family, owner, status, date range)
- Drill-down capabilities
- What-if scenario modeling

**Technology:**
- Streamlit 1.28+
- Plotly for interactive charts
- Pandas for data manipulation

**Key Pages:**
1. **Home/Overview:** Compliance scorecard, status distribution
2. **Risk Analysis:** Top risks, heat maps, family breakdown
3. **Trends:** Velocity charts, projections, control aging
4. **ROI Calculator:** Investment scenarios, cost-benefit analysis
5. **Controls Explorer:** Searchable control database with filters

#### 1.2 PDF Report Generator (`src/reports/pdf_generator.py`)
**Purpose:** Executive-level reports for board presentations

**Features:**
- Executive summary (1-page)
- Top 10 risks
- Compliance trends
- ROI analysis
- Recommended actions

**Technology:**
- ReportLab for PDF generation
- Jinja2 for templating
- Matplotlib for static charts

#### 1.3 CSV Exporter (`src/reports/csv_exporter.py`)
**Purpose:** Operational ticket exports for remediation tracking

**Features:**
- Prioritized action list
- Owner assignments
- Effort estimates
- Due dates

---

### 2. Application Layer

#### 2.1 Risk Scoring Engine (`src/analytics/risk_scorer.py`)

**Class:** `RiskScorer`

**Methods:**
```python
class RiskScorer:
    def __init__(self, config_path: str):
        """Load scoring configuration from YAML"""
        
    def calculate_control_risk(self, control: dict) -> float:
        """Calculate individual control risk score"""
        
    def calculate_family_score(self, family: str) -> dict:
        """Aggregate risk for NIST control family"""
        
    def calculate_overall_posture(self) -> float:
        """Overall compliance score (0-100)"""
        
    def get_top_risks(self, n: int = 10) -> List[dict]:
        """Return top N highest-risk controls"""
        
    def calculate_staleness_factor(self, control: dict) -> float:
        """Calculate overdue penalty"""
```

**Configuration:** Reads from `config/scoring.yaml`

**Key Algorithms:**
- Multi-factor risk calculation
- Staleness penalty calculation
- Family-level aggregation
- Overall compliance scoring

#### 2.2 Trend Analyzer (`src/analytics/trend_analyzer.py`)

**Class:** `TrendAnalyzer`

**Methods:**
```python
class TrendAnalyzer:
    def __init__(self, db_manager):
        """Initialize with database connection"""
        
    def calculate_compliance_velocity(self, months: int = 6) -> float:
        """Calculate rate of compliance improvement"""
        
    def project_future_compliance(self, months_ahead: int) -> dict:
        """Predict future compliance score"""
        
    def identify_problematic_controls(self) -> List[dict]:
        """Find controls that repeatedly fail"""
        
    def calculate_remediation_velocity(self) -> float:
        """Controls fixed per month"""
        
    def generate_trend_data(self, family: str = None) -> pd.DataFrame:
        """Historical data for charting"""
```

**Data Source:** `audit_history` table

**Key Algorithms:**
- Linear regression for velocity
- Trend projection
- Control aging analysis
- Pattern detection

#### 2.3 ROI Calculator (`src/analytics/roi_calculator.py`)

**Class:** `ROICalculator`

**Methods:**
```python
class ROICalculator:
    def __init__(self, config_path: str):
        """Load ROI parameters from YAML"""
        
    def calculate_risk_exposure(self, controls: List[dict]) -> float:
        """Calculate current risk exposure ($$)"""
        
    def calculate_remediation_cost(self, controls: List[dict]) -> float:
        """Total cost to fix controls"""
        
    def calculate_risk_reduction_value(self, controls: List[dict]) -> float:
        """Expected value of risk reduction"""
        
    def calculate_roi(self, controls: List[dict]) -> dict:
        """Complete ROI analysis"""
        
    def calculate_npv(self, controls: List[dict], years: int = 3) -> float:
        """Net present value with discount rate"""
        
    def scenario_analysis(self, scenarios: List[str]) -> dict:
        """Compare multiple remediation scenarios"""
```

**Configuration:** Reads from `config/roi_parameters.yaml`

**Key Algorithms:**
- Risk-Adjusted Loss Expectancy (RALE)
- Net Present Value (NPV)
- Payback period calculation
- Scenario comparison

#### 2.4 Configuration Manager (`src/utils/config_loader.py`)

**Class:** `ConfigLoader`

**Methods:**
```python
class ConfigLoader:
    @staticmethod
    def load_scoring_config() -> dict:
        """Load scoring.yaml"""
        
    @staticmethod
    def load_roi_config() -> dict:
        """Load roi_parameters.yaml"""
        
    @staticmethod
    def load_remediation_templates() -> dict:
        """Load remediation_templates.yaml"""
        
    @staticmethod
    def validate_config(config: dict, schema: dict) -> bool:
        """Validate configuration against JSON schema"""
```

**Technology:** PyYAML, jsonschema

---

### 3. Data Access Layer

#### 3.1 Database Manager (`src/utils/db_manager.py`)

**Class:** `DatabaseManager`

**Methods:**
```python
class DatabaseManager:
    def __init__(self, db_path: str):
        """Initialize SQLite connection"""
        
    # CRUD Operations
    def create_control(self, control: dict) -> str:
    def read_control(self, control_id: str) -> dict:
    def update_control(self, control_id: str, updates: dict) -> bool:
    def delete_control(self, control_id: str) -> bool:
    
    # Query Methods
    def get_all_controls(self, filters: dict = None) -> pd.DataFrame:
    def get_controls_by_family(self, family: str) -> pd.DataFrame:
    def get_failed_controls(self) -> pd.DataFrame:
    def get_overdue_controls(self) -> pd.DataFrame:
    
    # Audit History
    def add_audit_record(self, audit: dict) -> str:
    def get_audit_history(self, control_id: str) -> pd.DataFrame:
    
    # Risk Scores
    def save_risk_scores(self, scores: List[dict]) -> bool:
    def get_latest_risk_scores(self) -> pd.DataFrame:
    
    # Transaction Management
    def begin_transaction(self):
    def commit_transaction(self):
    def rollback_transaction(self):
    
    # Utility
    def execute_query(self, query: str, params: tuple) -> pd.DataFrame:
    def get_table_schema(self, table_name: str) -> dict:
```

**Design Patterns:**
- Singleton pattern for database connection
- Context manager for transactions
- Connection pooling (for future scalability)

**Error Handling:**
- Automatic retry on lock errors
- Transaction rollback on errors
- Logging of all database operations

---

### 4. Data Ingestion Layer

#### 4.1 Validator (`src/ingestion/validator.py`)

**Class:** `DataValidator`

**Methods:**
```python
class DataValidator:
    def __init__(self, schema_path: str):
        """Load JSON schema for validation"""
        
    def validate_schema(self, data: pd.DataFrame) -> ValidationResult:
        """Validate data against schema"""
        
    def check_required_fields(self, data: pd.DataFrame) -> List[str]:
        """Return missing required fields"""
        
    def validate_enums(self, data: pd.DataFrame) -> List[str]:
        """Check enum values (status, etc.)"""
        
    def validate_data_types(self, data: pd.DataFrame) -> List[str]:
        """Check data type consistency"""
        
    def validate_business_rules(self, data: pd.DataFrame) -> List[str]:
        """Check business logic (e.g., next_test_due >= last_test_date)"""
```

**Technology:** jsonschema, Pydantic

**Validation Rules:**
- Required fields present
- Valid enum values
- Data type consistency
- Date logic (next_test_due >= last_test_date)
- Control weight range (1.0-10.0)
- Foreign key integrity (nist_control_id exists)

#### 4.2 Parser (`src/ingestion/parser.py`)

**Class:** `ComplianceParser`

**Methods:**
```python
class ComplianceParser:
    @staticmethod
    def parse_csv(file_path: str) -> pd.DataFrame:
        """Parse CSV compliance export"""
        
    @staticmethod
    def parse_json(file_path: str) -> pd.DataFrame:
        """Parse JSON compliance export"""
        
    @staticmethod
    def parse_oscal(file_path: str) -> pd.DataFrame:
        """Parse NIST OSCAL format"""
        
    def detect_format(self, file_path: str) -> str:
        """Auto-detect file format"""
```

**Supported Formats:**
- CSV (generic compliance exports)
- JSON (structured compliance data)
- OSCAL (NIST Open Security Controls Assessment Language)

#### 4.3 Normalizer (`src/ingestion/normalizer.py`)

**Class:** `DataNormalizer`

**Methods:**
```python
class DataNormalizer:
    def normalize_status(self, status: str) -> str:
        """Map various status values to standard enum"""
        # "Passed" → "pass", "Failed" → "fail", etc.
        
    def normalize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize date formats"""
        
    def enrich_with_nist(self, df: pd.DataFrame) -> pd.DataFrame:
        """Join with NIST control reference data"""
        
    def deduplicate_controls(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate control records"""
        
    def fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply default values for optional fields"""
```

**Transformation Rules:**
- Status normalization (various inputs → standard enum)
- Date format standardization (ISO 8601)
- NIST control mapping
- Default value population
- Deduplication logic

---

## Data Flow

### 1. Data Ingestion Flow

```
CSV/JSON File
     ↓
[Validator] → Check schema, data types, business rules
     ↓ (if valid)
[Parser] → Read and parse file
     ↓
[Normalizer] → Standardize formats, enrich with NIST data
     ↓
[Database Manager] → Insert into SQLite
     ↓
SQLite Database
```

### 2. Risk Calculation Flow

```
User Request (via Dashboard or API)
     ↓
[Database Manager] → Fetch controls data
     ↓
[Risk Scorer] → Calculate individual risk scores
     ↓
[Risk Scorer] → Aggregate family/overall scores
     ↓
[Database Manager] → Save risk_scores table
     ↓
[Dashboard] → Display results
```

### 3. Trend Analysis Flow

```
User Request
     ↓
[Database Manager] → Fetch audit_history table
     ↓
[Trend Analyzer] → Calculate velocity, trends
     ↓
[Trend Analyzer] → Project future state
     ↓
[Dashboard] → Display charts and projections
```

### 4. Report Generation Flow

```
User Request (Generate Report)
     ↓
[Database Manager] → Fetch latest data
     ↓
[Risk Scorer] → Calculate current scores
     ↓
[Trend Analyzer] → Calculate trends
     ↓
[ROI Calculator] → Calculate ROI metrics
     ↓
[PDF Generator] → Compile report
     ↓
Output PDF File
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.10+ | Core development |
| Database | SQLite | 3.x | Data storage |
| Dashboard | Streamlit | 1.28+ | Web UI |
| Data Processing | Pandas | 2.0+ | Data manipulation |
| Visualization | Plotly | 5.17+ | Interactive charts |
| Static Charts | Matplotlib | 3.8+ | PDF report charts |
| PDF Generation | ReportLab | 4.0+ | Report creation |
| Configuration | PyYAML | 6.0+ | Config management |
| Validation | Pydantic | 2.4+ | Data validation |
| Testing | pytest | 7.4+ | Unit/integration tests |

### Additional Libraries

- **python-dateutil:** Date parsing and manipulation
- **jsonschema:** JSON schema validation
- **loguru:** Enhanced logging
- **tqdm:** Progress bars for data processing
- **click:** CLI tool framework

---

## Deployment Architecture

### Local Deployment

```
User's Machine
├── Python 3.10+ Environment
├── SQLite Database (grc.db)
├── Application Code
└── Config Files (YAML)
```

**Command:**
```bash
streamlit run src/dashboard/app.py
```

### Docker Deployment

```
Docker Container
├── Python 3.10 Base Image
├── Application Code
├── SQLite Volume Mount
├── Config Volume Mount
└── Exposed Port: 8501
```

**Dockerfile:**
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "src/dashboard/app.py"]
```

**Command:**
```bash
docker build -t grc-compliance .
docker run -p 8501:8501 -v $(pwd)/data:/app/data grc-compliance
```

### Cloud Deployment (Future)

Potential deployment on:
- **AWS:** ECS + RDS (PostgreSQL instead of SQLite)
- **Azure:** App Service + Azure SQL Database
- **GCP:** Cloud Run + Cloud SQL

---

## Security Considerations

### 1. Data Protection
- SQLite database file permissions restricted to application user
- No sensitive credentials in config files (use environment variables)
- Input validation to prevent SQL injection
- Sanitization of user inputs in dashboard

### 2. Access Control
- Future: Add authentication layer (Streamlit Auth, OAuth)
- Role-based access control (RBAC) for different user types
- Audit logging of all data modifications

### 3. API Security (Future)
- JWT-based authentication
- Rate limiting
- HTTPS/TLS for all communications

---

## Performance Considerations

### 1. Database Optimization
- Indexes on frequently queried fields
- Query result caching (Streamlit cache)
- Batch inserts for audit history
- Regular VACUUM and ANALYZE operations

### 2. Dashboard Performance
- Lazy loading of large datasets
- Pagination for control lists
- Cached calculations (risk scores)
- Incremental data loading

### 3. Scalability Limits
**Current (SQLite):**
- Up to 1,000 controls: Excellent performance
- Up to 100,000 audit records: Good performance
- Concurrent users: 1-5 (SQLite limitation)

**Future (PostgreSQL):**
- Unlimited controls and audit records
- 100+ concurrent users
- Distributed deployment

---

## Error Handling Strategy

### 1. Application Layer
```python
try:
    # Business logic
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    return error_response("Invalid data", details=str(e))
except DatabaseError as e:
    logger.critical(f"Database error: {e}")
    return error_response("System error", retry=True)
except Exception as e:
    logger.exception("Unexpected error")
    return error_response("Unexpected error occurred")
```

### 2. Data Layer
- Automatic retry on database lock
- Transaction rollback on errors
- Connection pool management

### 3. User Facing
- Friendly error messages in dashboard
- Detailed error logs for debugging
- Graceful degradation (show cached data if current calculation fails)

---

## Logging Strategy

### Log Levels
- **DEBUG:** Detailed diagnostic information
- **INFO:** General informational messages
- **WARNING:** Warning messages (e.g., missing optional fields)
- **ERROR:** Error messages (e.g., validation failures)
- **CRITICAL:** Critical errors (e.g., database unavailable)

### Log Destinations
- Console (development)
- File (`logs/grc_analytics.log`, rotated daily)
- Future: Centralized logging (ELK stack, CloudWatch)

### Log Format
```
2024-11-03 14:30:45 | INFO | risk_scorer.py:calculate_control_risk:125 | Calculated risk for CTRL-001: 45.2
```

---

## Testing Strategy

### 1. Unit Tests (`tests/unit/`)
- Test individual functions in isolation
- Mock database and external dependencies
- Coverage target: 80%+

**Example:**
```python
def test_calculate_control_risk():
    scorer = RiskScorer(config_path="config/scoring.yaml")
    control = {
        'control_weight': 9.0,
        'status': 'fail',
        'business_impact': 'critical',
        # ...
    }
    risk = scorer.calculate_control_risk(control)
    assert risk > 50.0  # Failed critical control should have high risk
```

### 2. Integration Tests (`tests/integration/`)
- Test component interactions
- Use test database
- Test full data flow (ingestion → calculation → display)

### 3. End-to-End Tests
- Test complete user workflows
- Selenium/Playwright for dashboard testing
- Validate report generation

---

## Configuration Management

### Configuration Files

| File | Purpose | Format |
|------|---------|--------|
| `config/scoring.yaml` | Risk scoring parameters | YAML |
| `config/roi_parameters.yaml` | ROI calculation settings | YAML |
| `config/remediation_templates.yaml` | Remediation action templates | YAML |
| `.env` | Environment-specific settings | Key=Value |

### Environment Variables
```bash
DATABASE_PATH=data/processed/grc.db
LOG_LEVEL=INFO
STREAMLIT_PORT=8501
ENABLE_DEBUGGING=false
```

---

## Future Enhancements

### Phase 2 (Months 2-3)
1. **REST API:** Flask/FastAPI for programmatic access
2. **Authentication:** User login and RBAC
3. **Multi-tenant:** Support multiple organizations
4. **Notifications:** Email/Slack alerts for overdue controls

### Phase 3 (Months 4-6)
1. **PostgreSQL Migration:** Replace SQLite for scalability
2. **Real-time Sync:** Integration with compliance platforms (Sprinter, Vanta, Drata)
3. **ML Predictions:** Predict which controls likely to fail
4. **Mobile App:** React Native mobile dashboard

### Phase 4 (Months 7-12)
1. **Multi-framework Support:** SOC 2, ISO 27001, PCI-DSS
2. **Workflow Engine:** Approval workflows for remediation
3. **Collaboration Features:** Comments, attachments, discussions
4. **Advanced Analytics:** Control dependency mapping, breach simulation

---

**Document Version:** 1.0  
**Last Updated:** 2024-11-03  
**Architecture Version:** v1.0  
**Maintainer:** Jordan Best
