# Time Semantics & Leakage Controls

---

## 4.1 Feature Time Windows

All features in this system are constructed using **strictly historical data relative to an “as-of” timestamp**.

Time is treated as a **first-class dimension**, not a column.

---

### 4.1.1 As-Of Time Definition

For every customer prediction, an **as-of timestamp `T`** is defined.

All features must satisfy:
> **feature_event_time ≤ T**

No exceptions.

This applies consistently across:
- Training
- Validation
- Backtesting
- Online inference

### Leakage Enforcement Guarantees

Leakage prevention is enforced through **system-level controls**, not manual discipline.

Enforcement mechanisms include:
- Automated checks rejecting features with `event_time > T`
- Schema validation on feature timestamps
- Pipeline failures on time boundary violations
- Code review requirements for new feature definitions

Any feature failing enforcement checks is:
- Excluded from training and inference
- Logged for audit and review

---

### 4.1.2 Feature Window Types

Features are grouped by **explicit lookback windows**.

#### Common Windows

- Short-term: last **7 / 14 / 30 days**
- Mid-term: last **60 / 90 days**
- Long-term: last **180 / 365 days**

Each feature declares:
- Lookback duration
- Aggregation logic
- Minimum data requirement

---

### 4.1.3 Feature Window Construction Examples

#### Orders-Based Features
- Total spend in last 30 days
- Number of orders in last 90 days
- Average order value over last 180 days

#### Engagement-Based Features
- Number of sessions in last 7 / 30 days
- Session frequency trend (last 30 vs prior 30)
- Days since last activity

#### Returns-Based Features
- Return rate over last 90 days
- Time since last return
- Refund ratio (last 180 days)

---

### 4.1.4 Event Time vs Processing Time

All features are computed using **event timestamps**, not ingestion timestamps.

Late-arriving events:
- Are included only if `event_time ≤ T`
- Are excluded otherwise

This prevents future information from leaking backward.

---

### 4.1.5 Feature Freezing

Once features are computed for a given `T`:
- They are immutable
- Stored with versioned timestamps
- Reproducible for audits and backtests

## Feature Lineage & Auditability

For every prediction, the system records:
- Feature names and values
- Feature versions
- As-of timestamp `T`
- Model version

This enables:
- Exact prediction reproduction
- Post-hoc audits
- Root-cause analysis of failures

Predictions without complete lineage metadata are considered invalid.

---

## 4.2 Label Generation

Labels are generated **strictly after the feature window ends**.

This section defines **exact temporal boundaries**.

---

### 4.2.1 Churn Label Timing

#### Definition

Given:
- Feature cutoff time: `T`
- Prediction horizon: `H` (e.g., 30 / 60 / 90 days)

Churn label is defined as:

> Did the customer churn in the interval **(T, T + H]**?

---

#### Label Construction Logic

- Look for qualifying churn events:
  - No orders
  - No sessions
  - Explicit account closure
- Only events with `event_time > T` are considered

Customers are:
- Positive if churn occurs in horizon
- Negative otherwise

---

### 4.2.2 CLV Target Timing

#### Definition

CLV targets use **future realized revenue**.

Given:
- Feature cutoff time: `T`
- Revenue horizon: `H`

CLV target = sum of revenue where:
> `T < order_time ≤ T + H`

---

### 4.2.3 Censoring & Incomplete Labels

- Customers active beyond `T + H` are right-censored
- Censoring is explicitly tracked
- Survival models handle censoring natively

---

### 4.2.4 Label Finalization Delay

To avoid contamination:
- Labels are generated only after **full horizon elapses**
- No provisional labels are used for training

---

## 4.3 Training vs Inference Parity

This system enforces **feature parity** between training and inference.

---

### 4.3.1 Single Source of Feature Logic

- Feature definitions live in:
  - Feature store
  - Versioned pipelines
- Same code path used for:
  - Offline training
  - Online inference

No reimplementation in notebooks or services.

---

### 4.3.2 Point-in-Time Correctness

Training data is built using:
- Historical snapshots
- As-of joins
- Time-aware aggregations

This ensures:
- Training data matches what would have been available at prediction time

---

### 4.3.3 Backtesting Consistency

Backtests simulate:
- Rolling as-of times
- Historical feature availability
- True future labels

This avoids overly optimistic validation results.

---

### 4.3.4 Online Inference Constraints

At inference time:
- Only features available up to request time are used
- No batch-only features are assumed
- Missing features are handled explicitly

---

## 4.4 Known Leakage Risks & Mitigations

This section documents **known leakage vectors** and how they are mitigated.

---

### 4.4.1 Implicit Future Signals

**Risk**
- Features like “days until next order”
- Flags derived from downstream systems

**Mitigation**
- Feature review checklist
- Automated feature lineage checks
- Explicit rejection of post-T features

---

### 4.4.2 Aggregation Over Full History

**Risk**
- Lifetime averages computed including future periods

**Mitigation**
- All aggregations bounded by lookback windows
- No unbounded “lifetime” features in training

---

### 4.4.3 Label-Derived Features

**Risk**
- Using churn indicators as features
- Proxy variables too close to the label

**Mitigation**
- Feature-label correlation audits
- Manual review of high-importance features

---

### 4.4.4 Returns & Refund Timing

**Risk**
- Returns recorded after churn window but tied to earlier orders

**Mitigation**
- Use return event time, not order time
- Explicit lag buffers for sensitive features

---

### 4.4.5 Data Backfills & Corrections

**Risk**
- Historical backfills introduce future knowledge into training sets

**Mitigation**
- Snapshot-based training datasets
- No retraining on backfilled periods without re-simulation

#### Retraining Eligibility Rules

Training data is eligible for retraining only if:
- All features were available as of their respective `T`
- Labels were finalized after full horizon completion
- No retroactive data corrections were applied post hoc

If these conditions are not met:
- Data must be re-simulated using historical snapshots
- Or excluded entirely from training

---

### 4.4.6 Segment Leakage

**Risk**
- Segments computed using future behavior and reused historically

**Mitigation**
- Segments recomputed per as-of time
- No static segmentation labels across time

---

### 4.4.7 Leakage vs Feature Drift

Leakage and feature drift are treated as **distinct failure modes**.

- Leakage:
  - Use of future information
  - Invalidates model evaluation
  - Requires immediate rollback

- Drift:
  - Changes in data distribution over time
  - Does not imply incorrect feature construction
  - Requires monitoring and potential retraining

Drift detection does not override leakage controls.

---

## 4.5 Feature Availability Guarantees

For every feature:
- Availability SLA is documented
- Update frequency is defined
- Staleness tolerance is explicit

If a feature is unavailable:
- Fallback defaults are applied
- Prediction confidence may be reduced

### Impact on Prediction Confidence

When features are missing, stale, or delayed:
- Prediction confidence is reduced
- Downstream systems may suppress automated actions
- Confidence indicators are surfaced alongside predictions

Predictions without sufficient feature coverage are explicitly flagged.

---

## 4.6 Summary

This system enforces **strict temporal causality**.

By:
- Defining as-of times
- Bounding feature windows
- Delaying label creation
- Enforcing training/inference parity
- Explicitly documenting leakage risks

…the Customer Intelligence System avoids the most common and dangerous failure mode in ML systems:  
**accidental use of the future**.