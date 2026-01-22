# System Trade-offs – Demand & Inventory Intelligence

This document captures intentional design trade-offs.

---

## Batch vs Real-Time

**Chosen**
- Batch forecasting

**Pros**
- Stability
- Auditability
- Lower operational cost

**Cons**
- Not suitable for instant inventory control

---

## Accuracy vs Interpretability

**Chosen**
- Balanced approach favoring interpretability

**Pros**
- Easier operational adoption
- Better trust and explainability

**Cons**
- May underperform highly complex deep models in some cases

---

## Generality vs Optimization

**Chosen**
- General-purpose forecasting and risk framework

**Pros**
- Reusable across categories
- Lower maintenance burden

**Cons**
- Less specialized optimization per SKU

---

## Conservative Risk Bias

**Chosen**
- Conservative risk estimation

**Pros**
- Fewer catastrophic stock-outs
- Higher trust from ops teams

**Cons**
- Potentially higher inventory buffers

---

## Data Simplicity vs Completeness

**Chosen**
- Operate with limited, reliable data

**Pros**
- Robustness
- Easier governance

**Cons**
- Cannot fully model supplier constraints or lead times
