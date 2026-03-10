---
# title: Customer Segmentation Engine
# emoji: 📊
# colorFrom: blue
# colorTo: purple
# sdk: docker
# pinned: false
---

<div align="center">

# 🧠 Customer Intelligence System

**Enterprise-grade ML pipeline that transforms raw behavioral data into actionable customer intelligence**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

  [API Docs](#api-reference) · [Architecture](#architecture) · [Getting Started](#getting-started)

</div>

---

## 📌 Overview

The **Customer Intelligence System** creates a **single, consistent, predictive view of each customer** by combining three ML-powered signals:

| Signal | Model | Type | Description |
|--------|-------|------|-------------|
| **Customer Segmentation** | MiniBatchKMeans | Clustering | Behavioral & value-based customer grouping |
| **Churn Risk** | Calibrated Logistic Regression | Classification | 90-day churn probability with calibrated scores |
| **Customer Lifetime Value** | Two-Stage Gradient Boosting | Regression | Expected 12-month revenue per customer |

This enables the business to **shift from hindsight analytics to foresight decision-making** — driving retention, reducing cost-per-acquisition, and personalizing customer experience at scale.

---

## ✨ Key Capabilities

<table>
<tr>
<td width="50%">

### ML Pipeline
- 🔄 End-to-end batch pipeline (data → features → train → inference → snapshot)
- 📊 Automated drift detection (PSI, KS, Jensen-Shannon)
- 🏆 Champion-Challenger model promotion with statistical testing
- 🔁 Online learning support via SGD models
- 📝 Full experiment lineage & reproducibility (dataset fingerprints, code versions)

</td>
<td width="50%">

### Production Operations
- 🛡️ Kill switch infrastructure for instant model disabling
- 🔒 JWT + RBAC authentication with API key support
- 📈 SLA/SLO monitoring (99.5% uptime, p99 < 1s)
- 🚀 Shadow → Canary → Production deployment pipeline
- 📋 Immutable audit logging for all system actions

</td>
</tr>
<tr>
<td>

### Data Engineering
- 🧹 Four-source data ingestion with schema validation
- ⚙️ Time-windowed feature engineering (7d, 30d, 90d)
- ✅ Feature contracts with allowed/forbidden categories
- 📦 Hive-partitioned Parquet storage
- 🔍 Automated feature validation & quality gates

</td>
<td>

### Frontend Dashboard
- 📊 Executive overview with KPIs & revenue-at-risk
- 👥 Segment analysis with distribution charts
- ⚠️ Churn risk monitoring & alerts
- 💰 CLV value analysis & tier breakdowns
- 🏥 Customer health scoring & trend tracking

</td>
</tr>
</table>

---

## 🏛️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          CUSTOMER INTELLIGENCE SYSTEM                           │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────────┐   │
│  │  Raw Data    │───▶│   Feature    │───▶│   ML Models  │───▶│   Customer    │   │
│  │  Ingestion   │    │  Engineering │    │  (3 Models)  │    │   Snapshot    │   │
│  │             │    │             │    │             │    │              │   │
│  │ • customers │    │ • Validation│    │ • Churn     │    │ • Health     │   │
│  │ • orders    │    │ • Windowing │    │ • CLV       │    │ • Investment │   │
│  │ • sessions  │    │ • Contracts │    │ • Segments  │    │ • Trends     │   │
│  │ • returns   │    │ • Registry  │    │ • Registry  │    │ • Flags      │   │
│  └─────────────┘    └──────────────┘    └──────────────┘    └──────┬────────┘   │
│                                                                     │            │
│  ┌──────────────────────────────────────────────────────────────────┘            │
│  │                                                                               │
│  ▼                                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────────┐   │
│  │  FastAPI      │    │  Monitoring  │    │  Governance  │    │   Frontend    │   │
│  │  Backend      │    │  & Drift     │    │  & Security  │    │   Dashboard   │   │
│  │              │    │             │    │             │    │              │   │
│  │ • REST API   │    │ • PSI/KS    │    │ • Kill Switch│    │ • React/TS  │   │
│  │ • Auth/RBAC  │    │ • Alerts    │    │ • Audit Log │    │ • Recharts  │   │
│  │ • Rate Limit │    │ • SLA/SLO   │    │ • RBAC      │    │ • 7 Pages   │   │
│  │ • Caching    │    │ • Reports   │    │ • Safeguards│    │ • Real-time │   │
│  └──────────────┘    └──────────────┘    └──────────────┘    └───────────────┘   │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

> **Design Philosophy:** Batch-first, API-second. Interpretable models over maximum complexity. Customer-level predictions with full lineage.

---

## 📂 Project Structure

```
customer-intelligence-system/
│
├── backend/
│   ├── api/                        # FastAPI application
│   │   ├── app.py                  # Application entry point & middleware setup
│   │   ├── schemas.py              # Pydantic response models
│   │   ├── routes/                 # API route handlers
│   │   │   ├── overview.py         # Executive dashboard KPIs
│   │   │   ├── segments.py         # Segment analysis endpoints
│   │   │   ├── risk.py             # Churn risk endpoints  
│   │   │   ├── value.py            # CLV value endpoints
│   │   │   ├── health.py           # Customer health endpoints
│   │   │   ├── customers.py        # Customer list & detail endpoints
│   │   │   ├── alerts.py           # Alert management endpoints
│   │   │   └── export.py           # Data export endpoints
│   │   └── middleware/             # Middleware stack
│   │       ├── auth.py             # JWT + RBAC authentication
│   │       ├── rate_limiter.py     # SlowAPI rate limiting
│   │       ├── security_headers.py # Security headers (HSTS, CSP, etc.)
│   │       ├── kill_switch.py      # Kill switch middleware
│   │       └── logging.py          # Request/response logging
│   │
│   ├── data/
│   │   ├── raw/                    # Source datasets (Parquet)
│   │   │   ├── customers.parquet
│   │   │   ├── orders.parquet
│   │   │   ├── sessions.parquet
│   │   │   └── returns.parquet
│   │   ├── processed/              # Model-specific feature sets
│   │   │   ├── churn/
│   │   │   ├── clv/
│   │   │   └── segmentation/
│   │   ├── outputs/                # Aggregated analytics outputs
│   │   │   └── snapshot_date=YYYY-MM-DD/
│   │   └── snapshots/              # Customer snapshot (single source of truth)
│   │       └── customer_snapshot/
│   │           └── snapshot_date=YYYY-MM-DD/
│   │
│   ├── features/                   # Feature engineering pipeline
│   │   ├── build_customer_features.py  # Main feature pipeline
│   │   ├── validation.py           # Feature validation & drift detection
│   │   └── feature_contracts.yaml  # Feature registry & contracts
│   │
│   ├── models/
│   │   ├── segmentation/           # MiniBatchKMeans clustering
│   │   │   ├── train.py
│   │   │   └── config.yaml
│   │   ├── churn/                  # Calibrated Logistic Regression
│   │   │   ├── train.py
│   │   │   └── config.yaml
│   │   ├── clv/                    # Two-Stage Gradient Boosting
│   │   │   ├── train.py
│   │   │   └── config.yaml
│   │   ├── model_registry/         # Versioned model artifacts (.joblib)
│   │   ├── promotion.py            # Champion-Challenger evaluation
│   │   ├── online_learning.py      # SGD-based online learning
│   │   └── build_models.py         # Model training orchestrator
│   │
│   ├── snapshot/                   # Customer snapshot builder
│   │   ├── build_customer_snapshot.py  # Snapshot assembly
│   │   ├── health.py               # Health score computation
│   │   ├── investment.py           # Investment priority assignment
│   │   ├── rules.py                # Business flag logic
│   │   ├── trends.py               # Trend computation
│   │   └── schema.py               # Snapshot schema validation
│   │
│   ├── monitoring/                 # Drift & model monitoring
│   │   ├── drift_monitor.py        # PSI, KS, JS divergence detection
│   │   └── model_monitor.py        # Model performance tracking
│   │
│   ├── orchestration/              # Pipeline orchestration
│   │   ├── run_pipeline.py         # End-to-end pipeline runner
│   │   └── training_orchestrator.py # Training lifecycle management
│   │
│   ├── evaluation/                 # Evaluation metrics
│   │   ├── metrics.py              # Churn/CLV/Segmentation metrics
│   │   └── report_generator.py     # Evaluation report generation
│   │
│   ├── deployment/                 # Deployment management
│   │   └── deployment_manager.py   # Shadow → Canary → Production
│   │
│   ├── explainability/             # Model explainability
│   │   └── shap_explainer.py       # SHAP-based explanations
│   │
│   ├── caching/                    # Data loading & caching
│   │   └── loader.py               # LRU-cached data loader
│   │
│   ├── safeguards/                 # Safety infrastructure
│   │   └── kill_switch.py          # Kill switch + prediction safeguards
│   │
│   ├── governance/                 # Audit & compliance
│   │   └── audit_logger.py         # Immutable audit logging
│   │
│   ├── security/                   # Security policies
│   │   ├── data_access_matrix.md   # RBAC access control matrix
│   │   └── secrets_policy.md       # Secrets management policy
│   │
│   ├── platform/                   # Platform operations
│   │   ├── sla_slo.md              # SLA/SLO definitions
│   │   ├── scaling_policy.md       # Scaling configuration
│   │   └── env_matrix.md           # Environment configuration matrix
│   │
│   └── k8s/                        # Kubernetes manifests
│       ├── configmap.yaml
│       ├── cronjob.yaml
│       ├── deployment.yaml
│       ├── secrets.yaml
│       └── service.yaml
│
├── frontend/                       # React + TypeScript dashboard
│   ├── src/
│   │   ├── App.tsx                 # Application router
│   │   ├── pages/                  # 7 dashboard pages
│   │   │   ├── ExecutiveOverview.tsx
│   │   │   ├── Segmentation.tsx
│   │   │   ├── ChurnRisk.tsx
│   │   │   ├── CLVValue.tsx
│   │   │   ├── CustomerHealth.tsx
│   │   │   ├── Customers.tsx
│   │   │   └── Alerts.tsx
│   │   ├── components/             # Reusable UI components
│   │   └── lib/                    # API client & utilities
│   └── package.json
│
├── docs/                           # System documentation
│   └── Customer Intelligence system/
│       ├── architecture.md         # Architecture decisions
│       ├── decisions.md            # Design decision log
│       ├── tradeoffs.md            # Trade-off analysis
│       ├── failure_scenarios.md    # Failure mode documentation
│       └── system_dependencies.md  # Dependency mapping
│
├── Dockerfile                      # Production container
├── Procfile                        # Platform startup command
├── render.yaml                     # Render deployment config
├── railway.json                    # Railway deployment config
├── requirements.txt                # Python dependencies
└── .env.example                    # Environment variable template
```

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+ & npm (for frontend)
- **Git LFS** (for large files: `.parquet`, `.joblib`)

### 1. Clone & Install

```bash
# Clone the repository
git clone https://github.com/SANJAYRAM-DS/customer-segmentation-engine.git
cd customer-segmentation-engine

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### 2. Configure Environment

```bash
# Copy and configure environment variables
cp .env.example .env

# Key variables to set:
# ENVIRONMENT=development
# SECRET_KEY=your-secure-random-key
# CORS_ORIGINS=http://localhost:5173
# ENABLE_AUTHENTICATION=false   (for local dev)
# ENABLE_RATE_LIMITING=false    (for local dev)
```

### 3. Run the ML Pipeline

```bash
# Run the full pipeline: data → features → training → inference → snapshot
python -m backend.orchestration.run_pipeline
```

This will:
1. Load and validate raw data from `backend/data/raw/`
2. Build time-windowed customer features
3. Run drift detection against baseline statistics
4. Train all three models (Segmentation, Churn, CLV)
5. Generate predictions for all customers
6. Build the customer snapshot with health scores & business flags
7. Produce aggregated analytics outputs

### 4. Start the Backend API

```bash
# Development mode (auto-reload)
uvicorn backend.api.app:app --reload --port 8000

# Production mode
gunicorn backend.api.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 5. Start the Frontend

```bash
cd frontend
npm run dev
# → Dashboard available at http://localhost:5173
```

---

## 🔌 API Reference

**Base URL:** `http://localhost:8000/api/v1`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (public) |
| `GET` | `/api/v1/overview` | Executive dashboard KPIs, segment & health distributions, revenue at risk |
| `GET` | `/api/v1/segments` | Segment profiles, size, avg metrics per segment |
| `GET` | `/api/v1/risk` | Churn risk distribution, high-risk customer breakdown |
| `GET` | `/api/v1/value` | CLV distribution, value tier analysis |
| `GET` | `/api/v1/health` | Customer health band distribution & trends |
| `GET` | `/api/v1/customers` | Paginated customer list with filtering & sorting |
| `GET` | `/api/v1/customers/{id}` | Individual customer 360° detail view |
| `GET` | `/api/v1/alerts` | Active alerts (drift, churn spikes, anomalies) |
| `GET` | `/api/v1/export/{format}` | Data export (CSV/JSON) |
| `GET` | `/debug` | System diagnostics (dev only) |

### Query Parameters (Overview)

```bash
# Filter by segment, health band, or investment priority
GET /api/v1/overview?segment_name=Power%20User&health_band=Healthy

# Paginated customer list with sorting
GET /api/v1/customers?page=1&page_size=50&sort_by=churn_probability&ascending=false
```

### Authentication

```bash
# JWT Bearer Token
Authorization: Bearer <jwt_token>

# API Key (system integration)
X-API-Key: <api_key>
```

> **Note:** Authentication is disabled by default for development. Set `ENABLE_AUTHENTICATION=true` in production.

---

## 🤖 Models

### Churn Prediction

| Aspect | Detail |
|--------|--------|
| **Algorithm** | Logistic Regression + CalibratedClassifierCV (sigmoid, 3-fold) |
| **Target** | `churn_90d` — binary label (churned within 90 days) |
| **Features** | Log-scaled (recency, tenure, order count, spend, session metrics) + rates (return rate, discount rate) + categorical (country, device) |
| **Validation** | Temporal split (80/20 by recency), PR-AUC primary metric |
| **Class Balance** | `class_weight="balanced"` to handle imbalanced churn |
| **Output** | Calibrated probability ∈ [0, 1] |

### Customer Lifetime Value (CLV)

| Aspect | Detail |
|--------|--------|
| **Algorithm** | Two-stage: GradientBoostingClassifier (purchase probability) + GradientBoostingRegressor (expected spend) |
| **Target** | `future_90d_spend` — revenue in the next 90 days |
| **Calibration** | Isotonic calibration on purchase stage; Duan smearing factor on spend stage |
| **Validation** | Quantile-based temporal split; RMSE primary metric, revenue-weighted MAE |
| **Output** | Expected 12-month CLV (90d × 4 multiplier) |

### Customer Segmentation

| Aspect | Detail |
|--------|--------|
| **Algorithm** | MiniBatchKMeans (batch_size=2048, n_init=10) |
| **Features** | 5 RFM-inspired: recency_days, order_count, total_spend, session_frequency, return_rate |
| **Scaler** | RobustScaler (outlier-resistant) |
| **Validation** | Silhouette Score (primary), Davies-Bouldin Index, Calinski-Harabasz Index |
| **Default k** | 4 clusters (configurable via `config.yaml`) |

---

## 🔄 Pipeline

The orchestration pipeline (`backend/orchestration/run_pipeline.py`) runs 7 sequential stages with intelligent caching:

```
Stage 1: Data Ingestion & Validation
   │  ↳ Load raw Parquet files, validate schemas, compute fingerprints
   ▼
Stage 2: Feature Engineering
   │  ↳ Time-windowed aggregations (7d/30d/90d), target construction
   │  ↳ Skip if data fingerprint unchanged (state_store.json)
   ▼
Stage 3: Drift Detection
   │  ↳ PSI, KS test, JS divergence against baseline distributions
   │  ↳ Alerts if PSI > 0.1 or KS > 0.1
   ▼
Stage 4: Model Training
   │  ↳ Train Segmentation → Churn → CLV (sequential)
   │  ↳ Champion-Challenger promotion with 1% min improvement gate
   │  ↳ Skip if features unchanged and no drift detected
   ▼
Stage 5: Batch Inference
   │  ↳ Score all customers with champion models
   │  ↳ Prediction safeguards: clipping, bounds checking
   ▼
Stage 6: Customer Snapshot
   │  ↳ Merge features + predictions + health scores + business flags
   │  ↳ Schema validation gate (hard fail on mismatch)
   │  ↳ Persist as Hive-partitioned Parquet
   ▼
Stage 7: Analytics Outputs
   ↳ KPIs, aggregations, distributions, migrations, trends
```

### Retraining Policy

| Trigger | Condition | Action |
|---------|-----------|--------|
| Data change | Dataset fingerprint changes | Rebuild features + retrain |
| Drift detected | PSI > 0.1 or KS > 0.1 | Retrain models |
| Scheduled | Configurable interval | Full pipeline run |
| Manual | Operator override | Force retrain |

---

## 📊 Monitoring & Observability

### Drift Detection

| Metric | Method | Threshold | Used For |
|--------|--------|-----------|----------|
| **PSI** | Population Stability Index | > 0.1 (warning), > 0.25 (critical) | Numeric features |
| **KS Test** | Kolmogorov-Smirnov | > 0.1 (p < 0.05) | Numeric distributions |
| **JS Divergence** | Jensen-Shannon | > 0.1 | Categorical features |

### SLA / SLO Targets

| Signal | Target |
|--------|--------|
| API Availability | ≥ 99.5% (30-day rolling) |
| p50 Latency | ≤ 200ms |
| p99 Latency | ≤ 1000ms |
| Data Freshness | ≤ 24 hours |
| Prediction Coverage | ≥ 95% of customers scored |
| Batch Pipeline Runtime | ≤ 2 hours |

### Kill Switch

Instant containment of faulty models without full rollback:

```python
from backend.safeguards.kill_switch import emergency_disable_model

# Disable a model type immediately
emergency_disable_model(
    model_type="churn",
    reason="Anomalous predictions detected",
    triggered_by="on-call-engineer",
    config_dir=Path("config")
)
```

---

## 🚢 Deployment

### Docker (Recommended)

```bash
docker build -t customer-intelligence .
docker run -p 7860:7860 customer-intelligence
```

### Supported Platforms

| Platform | Config File | Notes |
|----------|-------------|-------|
| **Hugging Face Spaces** | `Dockerfile` | Docker SDK, port 7860, auto-downloads LFS files from HF Hub |
| **Render** | `render.yaml` | Auto-deploy from GitHub, free tier available |
| **Railway** | `railway.json` | Nixpacks builder, health check enabled, auto-restart on failure |
| **Kubernetes** | `backend/k8s/` | Full manifests: Deployment, Service, CronJob, ConfigMap, Secrets |

### Deployment Pipeline

```
Shadow Mode ──▶ Canary (5% traffic) ──▶ Production (100%)
     │                   │                        │
     ▼                   ▼                        ▼
 No user impact     Monitor metrics         Full promotion
 Log predictions    Compare vs champion     Archive old model
 Validate outputs   Auto-rollback gates     Update registry
```

### Environment Matrix

| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| `DEBUG` | `true` | `false` | `false` |
| `ENABLE_DOCS` | `true` | `true` | `false` |
| `ENABLE_AUTHENTICATION` | `false` | `true` | `true` |
| `ENABLE_RATE_LIMITING` | optional | `true` | `true` |
| `WORKERS` | 1 | 2 | 4+ |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `WARNING` |

---

## 🔒 Security

| Layer | Implementation |
|-------|----------------|
| **Authentication** | JWT (HS256) + API Key dual mode |
| **Authorization** | Role-Based Access Control (viewer → analyst → admin) |
| **Rate Limiting** | SlowAPI with configurable limits per endpoint |
| **Security Headers** | HSTS, X-Content-Type-Options, X-Frame-Options, CSP |
| **Secrets** | Environment variables, never in code; 90-day rotation policy |
| **Audit Trail** | JSONL-based immutable logging of all data access, model events, and admin actions |
| **Prediction Safeguards** | Bounds checking, NaN detection, kill switch blocking |
| **Data Access** | 4-level sensitivity classification (Public → Internal → Confidential → Restricted PII) |

---

## 🛠️ Tech Stack

### Backend

| Component | Technology | Version |
|-----------|------------|---------|
| Web Framework | FastAPI | 0.115.6 |
| ASGI Server | Uvicorn + Gunicorn | 0.34.0 / 23.0.0 |
| Data Processing | Pandas + NumPy + PyArrow | 2.2.3 / 2.2.2 / 19.0.0 |
| Machine Learning | scikit-learn + SciPy | 1.6.1 / 1.15.1 |
| Serialization | Joblib + Pydantic | 1.4.2 / 2.10.6 |
| Authentication | python-jose (JWT) + passlib | 3.3.0 / 1.7.4 |
| Caching | Redis (optional) + lru_cache | 5.0.1 |
| Rate Limiting | SlowAPI | 0.1.9 |
| Monitoring | Sentry SDK | 1.40.0 |
| Configuration | python-dotenv + PyYAML | 1.0.1 / 6.0.1 |

### Frontend

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | React + TypeScript | 18.3 / 5.8 |
| Build Tool | Vite | 5.4 |
| UI Components | Radix UI + shadcn/ui | Latest |
| Charts | Recharts | 2.15 |
| State / Data | TanStack React Query + Zustand | 5.83 / 5.0 |
| Routing | React Router | 6.30 |
| Styling | Tailwind CSS | 3.4 |
| Testing | Vitest + Testing Library | 3.2 |

---

## 📚 Documentation

Comprehensive documentation is available in the `docs/` and `backend/platform/` directories:

| Document | Location | Description |
|----------|----------|-------------|
| Architecture | `docs/Customer Intelligence system/architecture.md` | System architecture & layer design |
| Design Decisions | `docs/Customer Intelligence system/decisions.md` | Decision log with rationale |
| Trade-offs | `docs/Customer Intelligence system/tradeoffs.md` | Documented trade-off analysis |
| Failure Scenarios | `docs/Customer Intelligence system/failure_scenarios.md` | Failure mode documentation |
| SLA/SLO | `backend/platform/sla_slo.md` | Service level objectives & error budgets |
| Scaling Policy | `backend/platform/scaling_policy.md` | Horizontal/vertical scaling configuration |
| Environment Matrix | `backend/platform/env_matrix.md` | Dev/Staging/Prod configuration diffs |
| Data Access Matrix | `backend/security/data_access_matrix.md` | RBAC & data sensitivity levels |
| Secrets Policy | `backend/security/secrets_policy.md` | Secret management & rotation |

---

## 📊 Dashboard Pages

| Page | Route | Key Metrics |
|------|-------|-------------|
| **Executive Overview** | `/` | Total customers, avg churn, avg CLV, revenue at risk, segment & health distributions |
| **Segmentation** | `/segmentation` | Segment profiles, size distribution, behavioral characteristics |
| **Churn Risk** | `/churn-risk` | Risk distribution, high-risk cohort, churn trends |
| **CLV Value** | `/clv-value` | Value tiers, CLV distribution, revenue concentration |
| **Customer Health** | `/customer-health` | Health bands, score trends, engagement activity |
| **Customers** | `/customers` | Searchable customer list, 360° detail view, individual trends |
| **Alerts** | `/alerts` | Drift alerts, churn spikes, anomaly notifications |

---

## 🧪 Testing

```bash
# Backend: Run the pipeline with validation
python -m backend.orchestration.run_pipeline

# Frontend: Run unit tests
cd frontend && npm test

# Frontend: Watch mode
cd frontend && npm run test:watch

# Frontend: Lint
cd frontend && npm run lint
```

---

## 🗺️ Roadmap

- [ ] Real-time inference endpoint for single-customer scoring
- [ ] MLflow / W&B experiment tracking integration
- [ ] Feature store migration (Feast / Tecton)
- [ ] SHAP explanations integrated into dashboard
- [ ] A/B testing framework for model comparison in production
- [ ] Customer feedback loop (human-in-the-loop corrections)
- [ ] Multi-tenancy support
- [ ] Automated retraining triggers based on drift alerts

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with** ❤️ **for production ML engineering**

*From raw data to actionable intelligence — end to end.*

</div>
