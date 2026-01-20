# Customer Intelligence System – Architecture

## Overview

The Customer Intelligence System is a modular, batch-first predictive system designed to generate customer-level intelligence signals such as churn risk, customer lifetime value (CLV), and behavioral segments.

The architecture separates data ingestion, feature computation, modeling, and output delivery to ensure scalability, reproducibility, and governance.

---

## High-Level Architecture

Raw Data → Validation → Feature Engineering → Models → Output Surfaces → Consumers

### Core Layers

1. Data Sources
2. Feature Engineering Layer
3. Modeling Layer
4. Output Layer
5. Monitoring & Governance

---

## Data Sources

- Orders
- Sessions
- Returns
- Customer Metadata

All data is assumed to be linked by a stable customer identifier provided upstream.

---

## Feature Engineering Layer

- Time-windowed aggregations (7d / 30d / 90d)
- Snapshot-based computation
- Leakage-safe transformations
- Shared feature definitions across models

Optionally backed by a versioned feature store.

---

## Modeling Layer

Independent but coordinated models:
- Churn prediction (classification or survival)
- CLV estimation (regression or survival)
- Customer segmentation (KMeans / HDBSCAN)
- Optional behavior embeddings

Models are trained and deployed independently but share the same feature layer.

---

## Output Layer

- API: `/customer/profile`
- Analytical tables: `customer_risk_scores`
- Dashboards: Customer Health Overview

All outputs are customer-level, versioned, and timestamped.

---
## System Architecture

┌───────────────────────┐
│   Source Systems      │
│                       │
│ Orders                │
│ Sessions              │
│ Returns               │
│ Customer Metadata     │
└──────────┬────────────┘
           │
           ▼
┌──────────────────────┐
│ Data Validation      │
│ & Normalization      │
│                      │
│ - Schema checks      │
│ - Type enforcement   │
│ - Missing handling   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Feature Engineering  │
│                      │
│ - Time-windowed aggs │
│ - Behavioral signals │
│ - Leakage-safe logic │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Feature Store        │
│ (Versioned)          │
└──────┬────────┬──────┘
       │        │
       ▼        ▼
┌────────────┐ ┌────────────┐
│ Training   │ │ Inference  │
│ Pipelines  │ │ Pipelines  │
└─────┬──────┘ └─────┬──────┘
      │              │
      ▼              ▼
┌────────────┐ ┌──────────────────┐
│ Model      │ │ Output Surfaces  │
│ Registry   │ │                  │
│            │ │ API              │
│            │ │ Tables           │
│            │ │ Dashboards       │
└────────────┘ └──────────────────┘

---

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
