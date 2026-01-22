# Key Architectural and Modeling Decisions

This document records major design decisions and their rationale.

---

## Batch-First Inference

**Decision**  
Primary inference is batch-based with optional near-real-time access.

**Rationale**
- Improves reproducibility
- Simplifies feature freshness guarantees
- Reduces operational complexity

---

## Customer-Level Focus

**Decision**  
System operates at the customer level, not session or event level.

**Rationale**
- Aligns with churn and CLV use cases
- Enables stable prioritization
- Simplifies downstream consumption

---

## Time-Based Validation

**Decision**  
All models use time-based splits.

**Rationale**
- Prevents leakage
- Reflects real-world deployment conditions
- Produces realistic performance estimates

---

## Unsupervised Segmentation

**Decision**  
Customer segments are learned, not rule-defined.

**Rationale**
- Avoids brittle heuristics
- Adapts to behavioral change
- Produces data-driven groupings

---

## Synthetic / Public Data Compatibility

**Decision**  
System does not depend on PII or proprietary identity attributes.

**Rationale**
- Enables privacy-safe development
- Improves portability
- Supports early-stage or constrained enSSSvironments

---

## Probabilistic Outputs

**Decision**  
All predictions are probabilistic, not deterministic.

**Rationale**
- Reflects inherent uncertainty
- Encourages ranking over hard decisions
- Supports responsible usage
