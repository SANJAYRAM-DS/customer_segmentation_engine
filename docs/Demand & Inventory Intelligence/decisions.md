# Key Decisions – Demand & Inventory Intelligence

This document records major architectural and modeling decisions and their rationale.

---

## Batch-Based Forecasting

**Decision**  
All forecasts and risk estimates are generated in batch.

**Rationale**
- Improves reproducibility and auditability
- Aligns with planning and procurement workflows
- Reduces operational complexity

---

## SKU-Level Granularity

**Decision**  
All outputs are generated at the individual SKU level.

**Rationale**
- Enables precise inventory prioritization
- Captures heterogeneous demand behavior
- Avoids over-generalization at category level

---

## Forecast-First, Risk-Second Design

**Decision**  
Risk models are downstream of demand forecasts.

**Rationale**
- Separates demand estimation from inventory logic
- Allows independent improvement of forecasting models
- Enables uncertainty propagation into risk estimates

---

## Probabilistic Risk Outputs

**Decision**  
Stock-out and overstock are expressed probabilistically.

**Rationale**
- Reflects inherent demand uncertainty
- Enables ranking and prioritization
- Avoids brittle threshold-only logic

---

## Privacy-Safe Data Design

**Decision**  
System does not ingest customer-level or PII data.

**Rationale**
- Reduces compliance and security risk
- Improves portability across environments
- Simplifies governance

---

## Conservative Operational Bias

**Decision**  
Prefer conservative forecasts and risk estimates over aggressive optimization.

**Rationale**
- Reduces costly operational failures
- Builds trust with planning teams
- Aligns with decision-support role
