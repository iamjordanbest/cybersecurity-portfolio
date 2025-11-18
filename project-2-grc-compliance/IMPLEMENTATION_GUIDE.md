# 🛠️ GRC Analytics Platform - Implementation Guide

## Quick Start

This guide provides step-by-step instructions for implementing each enhancement phase.

---

## Phase 1: Performance Optimization

### Prerequisites
```bash
# Install Redis
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Linux: sudo apt-get install redis-server
# macOS: brew install redis

# Install Python dependencies
pip install redis python-redis-lock sqlalchemy psycopg2-binary memory_profiler
```

### Step 1: Redis Cache Implementation

Create `src/cache/redis_manager.py`:
```python
import redis
import json
import pickle
from typing import Any, Optional
from datetime import timedelta

class CacheManager:
    """Redis cache manager for GRC platform."""
    
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=False  # Handle binary data
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        data = self.redis_client.get(key)
        if data:
            return pickle.loads(data)
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL (seconds)."""
        self.redis_client.setex(
            key,
            ttl,
            pickle.dumps(value)
        )
    
    def delete(self, key: str):
        """Delete key from cache."""
        self.redis_client.delete(key)
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern."""
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)
```

### Step 2: Update Risk Scoring with Caching

Modify `src/analytics/risk_scoring.py`:
```python
from src.cache.redis_manager import CacheManager

class RiskScoringEngine:
    def __init__(self, db_connection, cache_manager=None):
        self.conn = db_connection
        self.cache = cache_manager or CacheManager()
    
    def calculate_all_risk_scores(self, use_cache=True):
        """Calculate risk scores with caching."""
        cache_key = "risk_scores:all"
        
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        # Original calculation logic
        scores = self._calculate_scores()
        
        # Cache for 1 hour
        self.cache.set(cache_key, scores, ttl=3600)
        
        return scores
```

### Step 3: Add Connection Pooling

Create `src/database/pool.py`:
```python
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker
import sqlite3

class DatabasePool:
    """Database connection pool manager."""
    
    def __init__(self, db_path, pool_size=5):
        # For SQLite
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            poolclass=pool.QueuePool,
            pool_size=pool_size,
            max_overflow=10,
            pool_pre_ping=True
        )
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """Get database session from pool."""
        return self.Session()
```

### Step 4: Performance Monitoring

Create `src/utils/performance_monitor.py`:
```python
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def monitor_performance(threshold_ms=100):
    """Decorator to monitor function performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed_ms = (time.time() - start) * 1000
            
            if elapsed_ms > threshold_ms:
                logger.warning(
                    f"Slow query detected: {func.__name__} "
                    f"took {elapsed_ms:.2f}ms"
                )
            
            return result
        return wrapper
    return decorator
```

---

## Phase 2: Multi-Framework Support

### Database Schema Updates

Create `scripts/add_multi_framework_support.sql`:
```sql
-- Frameworks table
CREATE TABLE IF NOT EXISTS frameworks (
    framework_id INTEGER PRIMARY KEY AUTOINCREMENT,
    framework_code TEXT UNIQUE NOT NULL,
    framework_name TEXT NOT NULL,
    version TEXT,
    description TEXT,
    published_date DATE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Framework controls
CREATE TABLE IF NOT EXISTS framework_controls (
    fc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    framework_id INTEGER NOT NULL,
    control_identifier TEXT NOT NULL,
    control_name TEXT NOT NULL,
    control_description TEXT,
    control_category TEXT,
    implementation_guidance TEXT,
    FOREIGN KEY (framework_id) REFERENCES frameworks(framework_id),
    UNIQUE(framework_id, control_identifier)
);

-- Cross-framework mappings
CREATE TABLE IF NOT EXISTS control_mappings (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_framework_id INTEGER NOT NULL,
    source_control_id TEXT NOT NULL,
    target_framework_id INTEGER NOT NULL,
    target_control_id TEXT NOT NULL,
    mapping_type TEXT CHECK(mapping_type IN ('EXACT', 'PARTIAL', 'RELATED')),
    confidence_score REAL,
    notes TEXT,
    FOREIGN KEY (source_framework_id) REFERENCES frameworks(framework_id),
    FOREIGN KEY (target_framework_id) REFERENCES frameworks(framework_id)
);

-- Framework baselines/profiles
CREATE TABLE IF NOT EXISTS framework_profiles (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    framework_id INTEGER NOT NULL,
    profile_name TEXT NOT NULL,
    profile_description TEXT,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (framework_id) REFERENCES frameworks(framework_id)
);

-- Insert frameworks
INSERT INTO frameworks (framework_code, framework_name, version, description) VALUES
('NIST-800-53', 'NIST Special Publication 800-53', 'Rev 5', 'Security and Privacy Controls'),
('ISO-27001', 'ISO/IEC 27001', '2013', 'Information Security Management'),
('CIS', 'CIS Controls', 'v8', 'CIS Critical Security Controls'),
('PCI-DSS', 'Payment Card Industry Data Security Standard', 'v4.0', 'Payment card security'),
('SOC2', 'SOC 2 Type II', '2017', 'Trust Services Criteria');

-- Create indexes
CREATE INDEX idx_framework_controls_framework ON framework_controls(framework_id);
CREATE INDEX idx_framework_controls_identifier ON framework_controls(control_identifier);
CREATE INDEX idx_control_mappings_source ON control_mappings(source_framework_id, source_control_id);
CREATE INDEX idx_control_mappings_target ON control_mappings(target_framework_id, target_control_id);
```

---

## Phase 3: Testing & Quality Assurance

### Test Infrastructure Setup

1. **Install testing dependencies:**
```bash
pip install pytest pytest-cov pytest-mock pytest-asyncio black flake8 pylint mypy
```

2. **Create pytest configuration:**

`pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=70
```

3. **Create test structure:**
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_risk_scoring.py
│   ├── test_roi_calculator.py
│   ├── test_trend_analysis.py
│   └── test_cache_manager.py
└── integration/
    ├── __init__.py
    ├── test_data_pipeline.py
    ├── test_api_endpoints.py
    └── test_dashboard.py
```

4. **Example test file:**

`tests/unit/test_risk_scoring.py`:
```python
import pytest
from src.analytics.risk_scoring import RiskScoringEngine
from unittest.mock import Mock, MagicMock

@pytest.fixture
def mock_db_connection():
    """Create mock database connection."""
    conn = Mock()
    cursor = Mock()
    conn.cursor.return_value = cursor
    return conn

@pytest.fixture
def risk_engine(mock_db_connection):
    """Create RiskScoringEngine instance."""
    return RiskScoringEngine(mock_db_connection)

def test_calculate_base_score(risk_engine):
    """Test base score calculation."""
    result = risk_engine.calculate_base_score(
        cvss_score=7.5,
        exploit_available=True,
        attack_count=5
    )
    assert result > 0
    assert isinstance(result, float)

def test_calculate_exposure_score(risk_engine):
    """Test exposure score calculation."""
    result = risk_engine.calculate_exposure_score(
        affected_systems=100,
        critical_systems=20
    )
    assert result >= 0
    assert result <= 10
```

---

## Phase 4: REST API Layer

### FastAPI Setup

1. **Install dependencies:**
```bash
pip install fastapi uvicorn pydantic python-jose passlib python-multipart
```

2. **Project structure:**
```
src/api/
├── __init__.py
├── main.py                 # FastAPI app
├── dependencies.py         # Auth, DB dependencies
├── models/
│   ├── __init__.py
│   ├── request_models.py   # Pydantic request models
│   └── response_models.py  # Pydantic response models
├── routers/
│   ├── __init__.py
│   ├── controls.py
│   ├── compliance.py
│   ├── risk.py
│   ├── roi.py
│   └── threats.py
└── security/
    ├── __init__.py
    ├── auth.py
    └── rate_limit.py
```

3. **Basic API setup:**

`src/api/main.py`:
```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers import controls, compliance, risk, roi

app = FastAPI(
    title="GRC Analytics API",
    description="REST API for GRC Analytics Platform",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(controls.router, prefix="/api/v1/controls", tags=["controls"])
app.include_router(compliance.router, prefix="/api/v1/compliance", tags=["compliance"])
app.include_router(risk.router, prefix="/api/v1/risk", tags=["risk"])
app.include_router(roi.router, prefix="/api/v1/roi", tags=["roi"])

@app.get("/")
def root():
    return {"message": "GRC Analytics API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

---

## Development Workflow

### 1. Branch Strategy
```bash
# Create feature branch
git checkout -b feature/phase1-caching

# Work on implementation
git add .
git commit -m "feat: add Redis caching layer"

# Push and create PR
git push origin feature/phase1-caching
```

### 2. Code Quality Checks
```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/
pylint src/

# Type checking
mypy src/

# Run tests
pytest
```

### 3. Performance Testing
```bash
# Run performance benchmark
python scripts/performance_benchmark.py

# Profile code
python -m memory_profiler src/analytics/risk_scoring.py
```

---

## Deployment Checklist

### Phase 1 Deployment
- [ ] Redis server running
- [ ] Cache keys configured
- [ ] Performance monitoring enabled
- [ ] Benchmark tests passing
- [ ] Documentation updated

### Phase 2 Deployment
- [ ] Multi-framework schema deployed
- [ ] Framework data ingested
- [ ] Cross-framework mappings loaded
- [ ] UI updated for framework selection
- [ ] Migration scripts tested

### Phase 3 Deployment
- [ ] All tests passing
- [ ] Coverage >70%
- [ ] CI/CD pipeline configured
- [ ] Pre-commit hooks installed
- [ ] Quality badges added

### Phase 4 Deployment
- [ ] API server running
- [ ] Authentication configured
- [ ] Rate limiting enabled
- [ ] API documentation published
- [ ] Integration tests passing

---

## Troubleshooting

### Redis Connection Issues
```python
# Test Redis connection
import redis
r = redis.Redis(host='localhost', port=6379)
r.ping()  # Should return True
```

### Database Lock Issues
```python
# Use connection pooling
# Increase timeout
conn = sqlite3.connect('db.sqlite', timeout=30)
```

### Performance Issues
```python
# Profile slow functions
import cProfile
cProfile.run('function_to_profile()')
```

---

## Next Steps

Ready to start? Let's begin with **Phase 1: Performance Optimization**!

Would you like me to:
1. ✅ **Start implementing Phase 1** (Redis caching)
2. 📝 Create detailed code for a specific component
3. 🔧 Set up the testing infrastructure first
4. 📊 Create a project tracking board

Let me know how you'd like to proceed!
