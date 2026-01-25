# Customer Intelligence System – Architecture

## Overview

The Customer Intelligence System is a modular, batch-first predictive platform designed to generate **customer-level intelligence signals** such as churn risk, customer lifetime value (CLV), and behavioral segments.

The architecture intentionally separates **data ingestion, feature computation, modeling, and output delivery** to ensure scalability, reproducibility, governance, and long-term maintainability.

---

## High-Level Flow

**Raw Data → Validation → Feature Engineering → Models → Output Surfaces → Consumers**

---

## Core Architectural Layers

1. Data Sources  
2. Data Validation & Normalization  
3. Feature Engineering Layer  
4. Modeling Layer  
5. Output & Consumption Layer  
6. Monitoring & Governance  

---

## Data Sources

The system ingests batch data from multiple upstream systems:

- Orders  
- Sessions  
- Returns  
- Customer Metadata  

All datasets are assumed to be linked via a **stable customer identifier** provided by upstream systems.  
Identity resolution is considered out of scope.

---

## Data Validation & Normalization

Incoming data is validated before any downstream processing to ensure correctness and consistency.

Key responsibilities:
- Schema validation
- Data type enforcement
- Missing value handling
- Basic sanity checks (ranges, null thresholds)

This layer acts as a **data quality gate** for the entire system.

---

## Feature Engineering Layer

The feature engineering layer produces **time-aware, leakage-safe customer features** shared across all models.

Capabilities:
- Time-windowed aggregations (7d / 30d / 90d)
- Snapshot-based feature computation
- Leakage-safe transformations
- Shared feature definitions across models

Features may be optionally backed by a **versioned feature store** to support reproducibility and offline–online consistency.

---

## Modeling Layer

The modeling layer consists of **independent but coordinated models** operating on the shared feature set.

Supported model types:
- Churn prediction (classification or survival analysis)
- Customer Lifetime Value (CLV) estimation (regression or survival)
- Customer segmentation (KMeans / HDBSCAN)
- Optional behavioral embeddings

Models are:
- Trained independently
- Versioned and registered centrally
- Deployed via batch inference pipelines

---

## Output & Consumption Layer

Model outputs are published as **customer-level intelligence artifacts**.

Output surfaces include:
- API: `/customer/profile`
- Analytical tables: `customer_risk_scores`
- Dashboards: Customer Health Overview

All outputs are:
- Versioned
- Timestamped
- Auditable
- Safe for downstream consumption

---

## System Architecture Diagram

```mermaid
flowchart TD
    %% --- Styling ---
    classDef process fill:#E3F2FD,stroke:#1565C0,stroke-width:1px;
    classDef store fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,stroke-dasharray: 5 5;
    classDef db fill:#ECEFF1,stroke:#455A64,stroke-width:2px,shape:cylinder;
    classDef output fill:#FFF3E0,stroke:#E65100,stroke-width:1px;
    classDef monitor fill:#37474F,stroke:#CFD8DC,color:white;
    classDef training fill:#FFCCBC,stroke:#BF360C;
    classDef feature fill:#C8E6C9,stroke:#388E3C;

    %% --- Top Sources ---
    subgraph Sources [ ]
        S_Cust(Customers)
        S_Ord(Orders)
        S_Ret(Returns)
        S_Sess(Sessions)
    end
    class S_Cust,S_Ord,S_Ret,S_Sess db;

    %% --- Raw Data Layer ---
    subgraph RawDataLayer [Raw Data]
        RD_Check[Schema & Quality Checks<br>with Data Contracts & Evolution]:::process
        RD_Valid[Validated Data]:::feature
        RD_Report[Data Quality Report]:::output
    end

    S_Cust & S_Ord & S_Ret & S_Sess --> RD_Check
    RD_Check --> RD_Valid
    RD_Check --> RD_Report

    %% --- Feature Layer ---
    subgraph FeatureLayer [Feature Layer]
        FE[Feature Engineering]:::feature
        
        subgraph FeatureStore [Feature Store Layer]
            FS_Offline[(Offline Store<br>Parquet)]:::db
            FS_Online[(Online Store<br>Redis)]:::db
        end
        
        F_Train[Training Features]:::feature
        F_Raw[Raw Features]:::feature
        F_Inf[Inference Features]:::feature
    end

    RD_Valid --> FE
    FE --> FS_Offline
    FE --> FS_Online
    FS_Offline --> F_Train & F_Raw & F_Inf

    %% --- Model Training & MLOps ---
    MLflow[Experiment Tracking<br>MLflow]:::process
    
    subgraph TrainingLayer [Model Training]
        MT_Churn[Train<br>Churn Model]:::training
        MT_CLV[Train<br>CLV Model]:::training
        MT_Seg[Train<br>Segmentation Model]:::training
    end

    MT_Eval[Model Evaluation & Governance<br>Baseline Comparison, Fairness Checks, Approval Gate]:::monitor
    MT_Version[Versioned Models]:::process
    MT_Retrain[Retraining Strategy<br>Drift & Time Triggers, Backtesting]:::monitor

    F_Train --> TrainingLayer
    TrainingLayer <--> MLflow
    TrainingLayer --> MT_Eval
    MT_Eval --> MT_Version
    MT_Retrain -.->|Triggers| TrainingLayer

    %% --- Inference Layer ---
    subgraph InferenceLayer [Inference]
        BI[Batch Inference]:::process
        BI_Pred[Customer Predictions]:::feature
        
        RTI[Real-Time Inference]:::feature
        RTI_Pred[Real-Time Predictions]:::feature
    end

    F_Inf --> BI
    MT_Version --> BI
    BI --> BI_Pred

    FS_Online --> RTI
    MT_Version --> RTI
    RTI --> RTI_Pred

    %% --- Analysis & Explainability ---
    HistSnap[(Historical Snapshots)]:::db
    BI_Pred --> HistSnap

    subgraph OutputsMetrics [Outputs Layer]
        KPIs:::process
        Distributions:::process
        Trends:::process
        Migrations:::process
    end
    
    ExplainLayer[Model Explainability Layer<br>Feature Attributions SHAP, Reason Codes]:::process

    HistSnap --> OutputsMetrics
    MT_Version --> ExplainLayer

    %% --- Caching & Storage ---
    CacheOpt[Caching Layer<br>Optional]:::store
    CustSnap[Customer Snapshot<br>V, R, E, S, Investment]:::feature
    DailySnap[(Daily Snapshots<br>with history)]:::db
    CacheFinal[Caching Layer]:::store
    CachedOut[Cached Outputs]:::process

    OutputsMetrics -.-> CacheOpt
    CacheOpt --> CustSnap
    CustSnap --> DailySnap
    DailySnap --> CacheFinal
    CacheFinal --> CachedOut

    %% --- API & Monitoring Layer ---
    subgraph APILayerGroup [API Layer]
        API_Dash[API & Dashboard]:::feature
        API_Explain[Explainability Insights]:::feature
    end

    CachedOut --> API_Dash
    RTI_Pred --> API_Dash
    ExplainLayer --> API_Explain

    subgraph Monitoring [Monitoring & Alerts]
        Mon_Data[(Data Drift)]:::monitor
        Mon_Model[(Model Drift)]:::monitor
        Mon_Alerts[Alerts & Logs]:::monitor
        Mon_Trigger[Retraining Strategy<br>Drift & Time Triggers, Backtesting]:::monitor
    end

    API_Dash --> Mon_Data & Mon_Model & Mon_Alerts
    Mon_Data & Mon_Model --> Mon_Trigger
    Mon_Trigger -.->|Feedback Loop| MT_Retrain
```


## Design Principles

- Time-awareness by default
- Batch-first, API-second
- Privacy-first data usage
- Modular and replaceable components
- Strong observability and auditability

---

## Non-Goals

- Real-time recommendation
- Campaign execution
- Personalization logic
- Identity resolution
