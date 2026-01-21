# Demand & Inventory Intelligence System  
## Architecture & Design Document (RFC)

---

## 1. Overview

The Demand & Inventory Intelligence System is a **batch-first predictive analytics platform** designed to forecast SKU-level demand and quantify inventory risks such as **stock-out** and **overstock**.

The system supports:
- Inventory planning
- Procurement decision-making
- Operational risk monitoring

The architecture emphasizes **time-aware computation, modular modeling, uncertainty handling, and operational safety**.

---

## 2. Goals & Non-Goals

### Goals
- Accurate SKU-level demand forecasting
- Early detection of inventory risks
- Reproducible, auditable batch pipelines
- Safe planning-oriented outputs

### Non-Goals
- Real-time inventory control
- Order fulfillment execution
- Pricing optimization
- Supplier negotiation or contracting

---

## 3. High-Level Flow (HLD)

**Historical Data → Feature Engineering → Forecast Models → Risk Models → Output Surfaces → Operations Teams**

---

## 4. Core Architectural Layers

1. Data Sources  
2. Feature Engineering Layer  
3. Modeling Layer  
4. Output & Consumption Layer  
5. Monitoring & Governance  

---

## 5. Data Sources

The system ingests **time-stamped, SKU-aligned batch data**:

- Historical sales (SKU × date)
- Promotion calendars
- Seasonality and calendar signals
- Inventory levels (on-hand, in-transit where available)

All datasets are aligned on **SKU and time**, with explicit cutoff dates to prevent leakage.

---

## 6. Feature Engineering Layer

The feature layer produces **time-aware, snapshot-consistent SKU features** shared across all models.

Key feature groups:
- Lagged demand (t-1, t-7, t-30)
- Rolling statistics (mean, volatility)
- Promotion indicators
- Calendar and seasonality signals
- Inventory coverage metrics (days of supply)

All features are computed **as-of a forecast cutoff date** and reused across training and inference.

---

## 7. Modeling Layer

Models are **independent but coordinated**, sharing the same feature layer.

### Model Types
- **Demand Forecasting**
  - Statistical (ARIMA, ETS)
  - ML (XGBoost, LightGBM)
  - Optional deep models (Temporal CNN / RNN)
- **Stock-out Risk Estimation**
- **Overstock Risk Estimation**
- **Anomaly Detection**
  - Demand spikes/drops
  - Inventory inconsistencies

Each model is:
- Trained independently
- Versioned and registered
- Deployed via batch inference

---

## 8. Output & Consumption Layer

All outputs are **SKU-level, timestamped, and versioned**.

### Output Surfaces
- Forecast tables (point + intervals)
- Risk probability tables
- Alert streams (stock-out / overstock)
- Operations dashboards

These outputs support planners and operations teams—not automated execution systems.

---

## 9. System Architecture (Logical View)

```mermaid
flowchart TD
    A[Historical Data<br>Sales<br>Promotions<br>Inventory]

    B[Feature Engineering<br>Lagged demand<br>Rolling stats<br>Seasonality<br>Inventory context]

    C[Demand Forecast Models]

    D[Inventory Risk Models<br>Stock-out<br>Overstock]

    E[Output Surfaces<br>Forecast Tables<br>Risk Tables<br>Alerts<br>Dashboards]

    F[Monitoring & Governance<br>Drift<br>Accuracy<br>Pipeline Health]

    A --> B
    B --> C
    C --> D
    D --> E
    B --> F
    C --> F
    D --> F
```

## Training Pipeline
```mermaid
flowchart TD
    T0[Training Cutoff Date T0]
    F1[Feature Generation<br>As-of T0]
    L1[Label Construction<br>Future demand windows<br>Risk outcomes]
    M1[Model Training]
    E1[Backtesting & Evaluation<br>MAE RMSE MAPE<br>Risk calibration]
    R1[Model Registry]

    T0 --> F1 --> L1 --> M1 --> E1 --> R1
```

# Inference Pipeline
```mermaid
flowchart TD
    T1[Inference Snapshot Date T1]
    F2[Feature Generation<br>As-of T1]
    M2[Load Production Models]
    P1[Batch Forecast & Risk Run<br>Rolling horizons<br>Prediction intervals]
    O1[Output Surfaces]

    T1 --> F2 --> M2 --> P1 --> O1
```
---

## Design Principles

- Batch-first, planning-oriented design
- Time-awareness and leakage prevention
- Explicit uncertainty handling
- Modular and replaceable components
- No customer-level data usage

---

## Non-Goals

- Real-time inventory control
- Order fulfillment execution
- Pricing optimization
- Supplier negotiation