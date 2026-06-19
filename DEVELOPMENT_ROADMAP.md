# Development Roadmap & Action Plan

**Last Updated:** 2026-06-18  
**Target Milestone:** Production-Ready National Job Aggregator

---

## 📋 PHASE BREAKDOWN

### 🟢 PHASE 0: IMMEDIATE (Days 1-3) - Foundation

#### Task 0.1: Create Districts Registry
**Priority:** 🔴 CRITICAL  
**Effort:** 4 hours  
**Impact:** 50x coverage increase

**Deliverable:** `districts_config.json`
```json
{
  "districts": [
    {
      "state": "Uttar Pradesh",
      "district": "Ambedkar Nagar",
      "url": "https://ambedkar-nagar.nic.in/notice/recruitment/",
      "status": "verified"
    },
    // ... 50+ more
  ]
}
```

**Acceptance Criteria:**
- [ ] At least 50 verified district URLs
- [ ] At least 5 states represented
- [ ] Each URL accessible and returns content
- [ ] Format matches JSON schema

**Data Sources:**
- NIC (National Informatics Centre) - nic.in district portals
- State employment agencies
- Government websites archives
- Previous records/databases

---

#### Task 0.2: Move to Environment Configuration
**Priority:** 🟡 HIGH  
**Effort:** 1 hour  
**Impact:** Security + Flexibility

**Deliverables:**
- `.env.example` file
- `.env` file (local)
- Updated `job_scraper_bot.py`

**Code Changes Required:**
```python
# Before:
DB_CONFIG = {"dbname": "umbrella_jobs", "user": "postgres", ...}

# After:
import os
from dotenv import load_dotenv
load_dotenv()
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
}
```

**Acceptance Criteria:**
- [ ] No hardcoded credentials in code
- [ ] `.env.example` documents all variables
- [ ] `.env` in `.gitignore`
- [ ] Code reads from environment

---

#### Task 0.3: Add Logging Framework
**Priority:** 🟡 HIGH  
**Effort:** 2 hours  
**Impact:** Observability

**Implementation:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Replace print() with logger calls
# logger.info(), logger.error(), logger.warning(), logger.debug()
```

**Acceptance Criteria:**
- [ ] All print() statements replaced with logger calls
- [ ] Log levels used appropriately
- [ ] Log file generated in `logs/` directory
- [ ] Rotating file handler for large logs

---

#### Task 0.4: Add requirements.txt
**Priority:** 🟡 HIGH  
**Effort:** 30 minutes  
**Impact:** Reproducibility

**File:**
```txt
requests==2.31.0
beautifulsoup4==4.12.2
psycopg2-binary==2.9.9
python-dotenv==1.0.0
```

**Acceptance Criteria:**
- [ ] All dependencies listed with versions
- [ ] Can install via `pip install -r requirements.txt`
- [ ] All imports work after installation

---

### 🟡 PHASE 1: MVP (Days 4-28) - 50% Readiness

#### Task 1.1: Load Districts Configuration Dynamically
**Priority:** 🔴 CRITICAL  
**Effort:** 2 hours  

**Implementation:**
- Modify `process_districts()` to load from JSON
- Add validation for district URLs
- Support both file-based and database config

#### Task 1.2: Implement FastAPI REST API
**Priority:** 🔴 CRITICAL  
**Effort:** 5 days  

**Endpoints to implement:**
```
GET  /api/jobs?state=&district=&page=
GET  /api/jobs/:id
GET  /api/search?q=
GET  /api/districts
GET  /api/states
GET  /api/stats
POST /api/alerts/subscribe
```

**Tools:** FastAPI, Pydantic, SQLAlchemy

#### Task 1.3: Create Database Schema Migrations
**Priority:** 🔴 CRITICAL  
**Effort:** 2 hours  

**Tools:** Alembic (SQLAlchemy migrations)

**Schema updates needed:**
```sql
-- New columns
ALTER TABLE umbrella_jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE umbrella_jobs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();
ALTER TABLE umbrella_jobs ADD COLUMN IF NOT EXISTS salary_min INTEGER;
ALTER TABLE umbrella_jobs ADD COLUMN IF NOT EXISTS salary_max INTEGER;
ALTER TABLE umbrella_jobs ADD COLUMN IF NOT EXISTS experience_years INTEGER;
ALTER TABLE umbrella_jobs ADD COLUMN IF NOT EXISTS post_type VARCHAR(100);

-- New tables
CREATE TABLE IF NOT EXISTS states (...);
CREATE TABLE IF NOT EXISTS districts (...);
CREATE TABLE IF NOT EXISTS job_categories (...);
```

#### Task 1.4: Build React Web Interface
**Priority:** 🔴 CRITICAL  
**Effort:** 7 days  

**Pages needed:**
- [ ] Job Search/Listing (with filters)
- [ ] Job Detail View
- [ ] Advanced Search
- [ ] Statistics Dashboard
- [ ] Job Alerts Setup
- [ ] User Dashboard

**Tech Stack:** React, TypeScript, TailwindCSS, Axios

#### Task 1.5: Add Data Validation Pipeline
**Priority:** 🟡 HIGH  
**Effort:** 3 days  

**Validators to implement:**
- URL format validation
- PDF URL validation
- Title length/quality checks
- Duplicate detection improvements
- Date format standardization

#### Task 1.6: Implement Caching Layer
**Priority:** 🟡 HIGH  
**Effort:** 2 days  

**Tools:** Redis

**Caching strategy:**
- Cache job listings (5 min TTL)
- Cache district/state lists (24 hr TTL)
- Cache search results (10 min TTL)

#### Task 1.7: Add Comprehensive Testing
**Priority:** 🟡 HIGH  
**Effort:** 4 days  

**Test coverage targets:**
- [ ] Unit tests for scraper functions (80%)
- [ ] Integration tests for DB operations (80%)
- [ ] API endpoint tests (90%)
- [ ] End-to-end tests (50%)

**Tools:** pytest, pytest-asyncio, httpx

---

### 🟠 PHASE 2: EXPANSION (Days 29-42) - 65% Readiness

#### Task 2.1: Add Central Government Agency Coverage
**Priority:** 🔴 CRITICAL  
**Effort:** 5 days  

**Agencies to add:**
1. UPSC (https://www.upsc.gov.in/)
2. SSC (https://ssc.nic.in/)
3. RRB (https://www.rrbonline.nic.in/)
4. IBPS (https://www.ibps.in/)
5. SBI (https://www.sbi.co.in/web/careers)
6. Railway Board
7. ISRO
8. HAL

**Implementation approach:**
- Create agency-specific scraper adapters
- Handle different HTML structures
- Centralize common parsing logic

#### Task 2.2: Implement PDF Text Extraction
**Priority:** 🟡 HIGH  
**Effort:** 3 days  

**Tools:** pdfplumber, PyPDF2, pytesseract

**Pipeline:**
```
1. Download PDF from pdf_url
2. Extract text using pdfplumber
3. If extraction fails (scanned), use OCR (Tesseract)
4. Store extracted text in new 'job_pdf_text' table
5. Index for full-text search
```

**Acceptance Criteria:**
- [ ] 90% of PDFs successfully extracted
- [ ] Text stored in database
- [ ] Searchable via full-text index
- [ ] OCR works for scanned PDFs

#### Task 2.3: Add AI Job Title Standardization
**Priority:** 🟡 HIGH  
**Effort:** 4 days  

**Approach:**
- Option A: Use GPT-3.5/4 API (quick, paid)
- Option B: Fine-tune local NER model (flexible, free)
- Create mapping: raw title → standardized title

**Implementation:**
```python
STANDARD_TITLES = {
    "Engineer", "Teacher", "Manager", "Clerk", 
    "Police", "Doctor", "Nurse", ...
}

def standardize_job_title(raw_title):
    # Use LLM or classifier to map
    return mapped_title
```

#### Task 2.4: Build User Authentication System
**Priority:** 🟡 HIGH  
**Effort:** 3 days  

**Features:**
- User registration
- Email verification
- JWT-based authentication
- Social login (optional)
- Password reset

**Tech Stack:** FastAPI-Users or Authlib

#### Task 2.5: Expand District Coverage to 150+
**Priority:** 🟡 HIGH  
**Effort:** 3 days  

**Approach:**
- Research and add district URLs for all states
- Test scraper on each new district
- Document success/failure rates

**Target:**
- [ ] At least 150 districts/entities
- [ ] All states represented
- [ ] Success rate > 70%

#### Task 2.6: Add Job Alerts & Email Notifications
**Priority:** 🟡 HIGH  
**Effort:** 3 days  

**Features:**
- [ ] Email alert subscriptions
- [ ] Custom search filters
- [ ] Email digest (daily/weekly)
- [ ] Unsubscribe management

**Tools:** Celery, Redis, SendGrid/SMTP

---

### 🔴 PHASE 3: PRODUCTION (Days 43-60) - 80% Readiness

#### Task 3.1: Add Monitoring & Alerting
**Priority:** 🔴 CRITICAL  
**Effort:** 3 days  

**Monitoring:**
- Scraper health checks
- Database connection monitoring
- API response times
- Data quality metrics

**Tools:** Prometheus, Grafana, AlertManager

#### Task 3.2: Security Hardening
**Priority:** 🔴 CRITICAL  
**Effort:** 3 days  

**Actions:**
- [ ] HTTPS everywhere
- [ ] Input validation/sanitization
- [ ] SQL injection prevention (already done)
- [ ] CORS configuration
- [ ] Rate limiting
- [ ] DDoS protection
- [ ] Security headers
- [ ] Secrets management (HashiCorp Vault)

#### Task 3.3: Performance Optimization
**Priority:** 🟡 HIGH  
**Effort:** 3 days  

**Actions:**
- [ ] Database query optimization
- [ ] Index strategy for searches
- [ ] API response compression
- [ ] CDN for static assets
- [ ] Lazy loading for UI
- [ ] API pagination optimization

#### Task 3.4: Documentation & Runbooks
**Priority:** 🟡 HIGH  
**Effort:** 3 days  

**Documentation to create:**
- [ ] README.md (complete)
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Deployment guide
- [ ] Architecture diagram
- [ ] Database schema docs
- [ ] Troubleshooting guide
- [ ] Runbooks for common issues

#### Task 3.5: Mobile App Adaptation
**Priority:** 🟢 NICE-TO-HAVE  
**Effort:** 5 days  

**Options:**
- React Native / Flutter app
- Progressive Web App (PWA)
- Mobile-first redesign

#### Task 3.6: Analytics & Insights Dashboard
**Priority:** 🟢 NICE-TO-HAVE  
**Effort:** 4 days  

**Metrics to track:**
- Jobs by state/district/agency
- Growth trends
- User engagement
- Application completion rates
- Most searched positions

---

## 🎯 SPRINT SCHEDULE

### Week 1: Foundation
- [ ] Day 1-2: Districts registry + environment config
- [ ] Day 3: Logging + requirements.txt
- [ ] Day 4-5: First API endpoints
- **Daily Standup:** 30 min (9 AM)
- **Milestone:** 20% readiness

### Week 2: MVP Core
- [ ] Day 6-7: Database schema migrations
- [ ] Day 8-9: React frontend (pages 1-3)
- [ ] Day 10: Testing setup
- **Deliverable:** Working job search UI
- **Milestone:** 35% readiness

### Week 3: Expansion
- [ ] Day 11-12: Central agencies (5 agencies)
- [ ] Day 13-14: PDF extraction
- [ ] Day 15: Testing + bug fixes
- **Deliverable:** 100k+ jobs in database
- **Milestone:** 50% readiness (MVP Complete)

### Week 4: Advanced Features
- [ ] Day 16-17: AI standardization
- [ ] Day 18-19: User auth + alerts
- [ ] Day 20: Performance optimization
- **Milestone:** 65% readiness

### Week 5-6: Production Ready
- [ ] Day 21-22: Monitoring + alerting
- [ ] Day 23-24: Security hardening
- [ ] Day 25-26: Documentation + runbooks
- [ ] Day 27-28: Load testing + scale testing
- **Milestone:** 80% readiness (Production Ready)

---

## 📊 SUCCESS METRICS

### By Phase:

**Phase 0 (Days 1-3):**
- [ ] 50+ districts in registry
- [ ] Zero hardcoded secrets
- [ ] Proper logging output
- [ ] Requirements.txt working

**Phase 1 (Days 4-28):**
- [ ] API serving 20k+ jobs
- [ ] React UI functional on desktop
- [ ] 80%+ test coverage
- [ ] 150+ districts scraped
- [ ] Average API response < 500ms

**Phase 2 (Days 29-42):**
- [ ] 100k+ jobs in database
- [ ] 8 central agencies added
- [ ] 90% PDF extraction success
- [ ] User authentication working
- [ ] Email alerts operational

**Phase 3 (Days 43-60):**
- [ ] 0 critical alerts in 7 days
- [ ] 99.5% API uptime
- [ ] <100ms P95 response times
- [ ] 500+ daily active users (target)
- [ ] Ready for prod deployment

---

## 🚨 RISK MITIGATION

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Website structure changes | High | Medium | Modular scraper patterns + monitoring |
| Rate limiting from sites | Medium | Low | Polite crawling + proxy rotation |
| PDF extraction failures | High | Medium | Fallback to OCR + manual review |
| Database growth > capacity | Medium | High | Early indexing + query optimization |
| Team bandwidth | Medium | High | MVP first, nice-to-haves later |

---

## 💡 QUICK REFERENCE

### Key Configuration Files to Create:
- `districts_config.json` - District registry
- `.env` - Environment variables
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Local dev environment
- `alembic/` - Database migrations

### Key Code Modules to Create:
- `src/api/` - FastAPI app
- `src/scrapers/` - District/agency scrapers
- `src/models/` - SQLAlchemy models
- `src/services/` - Business logic
- `tests/` - Test suite
- `frontend/` - React app

### Key Infrastructure:
- PostgreSQL (database)
- Redis (cache + task queue)
- Celery (async tasks)
- Docker (containerization)
- GitHub Actions (CI/CD)

---

## 📞 DECISION CHECKPOINTS

### Before Phase 2:
- [ ] Phase 1 milestones met?
- [ ] Technical debt acceptable?
- [ ] Team bandwidth available?

### Before Phase 3:
- [ ] 100k+ jobs successfully scraped?
- [ ] API performing well under load?
- [ ] User testing completed?

### Before Production:
- [ ] All security checks passed?
- [ ] Monitoring in place?
- [ ] SLA requirements defined?
- [ ] Legal/compliance reviewed?

---

## 📚 LEARNING RESOURCES

- FastAPI tutorial: https://fastapi.tiangolo.com/
- SQLAlchemy ORM: https://docs.sqlalchemy.org/
- React guide: https://react.dev/
- Celery tasks: https://docs.celeryproject.io/
- Web scraping best practices: https://scrapy.org/
- Docker for Python: https://docs.docker.com/

---

**Next Step:** Start Phase 0, Task 0.1 (Districts Registry)  
**Estimated Start Date:** Immediately  
**Estimated Completion:** 5-6 weeks from start

