# Evaluation & Validation Strategy

---

## 7.1 Offline Metrics

Offline metrics are chosen to reflect **decision quality**, not just statistical fit.

Metrics differ by ML task.

---

### 7.1.1 Churn Prediction Metrics

#### Primary Metrics

- **AUC-ROC**
  - Measures ranking quality across thresholds
  - Useful for comparing models

- **Precision @ K**
  - Measures how many flagged customers truly churn
  - Directly tied to retention capacity constraints

- **Recall @ K**
  - Measures how much churn is captured within budget

#### Calibration Metrics

- **Brier Score**
- **Calibration curves**

Calibration is critical because:
- Probabilities drive spend decisions
- Poor calibration leads to over- or under-investment

### Threshold & K Selection

Thresholds and K values are not optimized purely for metrics.

They are determined by:
- Operational capacity (e.g., number of customers reachable)
- Budget constraints
- Business-defined risk tolerance

Metric reporting always specifies the chosen K and its business rationale.

---

### 7.1.2 CLV Estimation Metrics

#### Regression Metrics

- **MAE / RMSE**
  - Error magnitude awareness
- **MAPE** (used cautiously)
  - Sensitive to low-value customers

#### Economic Metrics

- **Revenue-weighted error**
- **Top-decile CLV accuracy**

Focus is placed on:
> Accuracy for **high-value customers**, not the median user.

---

### 7.1.3 Segmentation Evaluation

Segmentation has no ground-truth label.

Evaluation focuses on:

- **Stability over time**
- **Inter-segment separation**
- **Intra-segment cohesion**
- **Business interpretability**

Metrics may include:
- Silhouette score (secondary)
- Segment migration rate

---

## 7.2 Backtesting Methodology

All evaluation respects **temporal causality**.

Random splits are explicitly forbidden.

---

### 7.2.1 Rolling Time-Based Validation

Training and testing use **rolling windows**.

Example:
- Train: Jan–Jun
- Validate: Jul
- Slide window forward

This simulates:
- Real deployment conditions
- Model degradation over time

---

### 7.2.2 Multiple Horizon Evaluation

Models are evaluated across:
- 30-day churn
- 60-day churn
- 90-day churn

This ensures:
- Robustness to horizon choice
- Avoidance of overfitting to a single window

---

### 7.2.3 Delayed Label Validation

Labels are only evaluated after:
- Full prediction horizon has elapsed
- Data corrections and late events settled

---

### 7.2.4 Data Leakage Checks

Validation pipelines include:
- Feature timestamp audits
- Label lookahead checks
- Feature importance anomaly detection

---

## 7.3 Segment-Level Analysis

Aggregate metrics hide failures.

All evaluations are **stratified**.

---

### 7.3.1 Customer Segment Performance

Performance reported by:
- Behavioral segment
- Value tier
- Lifecycle stage

This identifies:
- Segments where model underperforms
- Overconfident predictions

---

### 7.3.2 Value-Weighted Evaluation

Metrics are weighted by:
- Historical value
- Predicted CLV

This ensures:
- Models are optimized for economic impact
- Not just accuracy on low-value customers

---

### 7.3.3 Cold-Start vs Mature Customers

Separate evaluation for:
- New customers
- Established customers

Cold-start performance is expected to be weaker but monitored explicitly.

---

### 7.3.4 Temporal Regime Analysis

Performance analyzed across:
- Seasonal peaks
- Promotion-heavy periods
- Demand shocks

This detects:
- Regime-specific brittleness
- Overfitting to “normal” periods

### 7.3.5 Metric Ownership & Review Cadence

- Core offline metrics are reviewed on a fixed cadence
- Ownership is shared between ML and business stakeholders
- Metric regressions trigger investigation before retraining or promotion

Metrics without an owner are not considered actionable.

---

## 7.4 Baseline Comparison

All models are compared against **explicit baselines**.

---

### 7.4.1 Baseline Types

- Rule-based heuristics
- Logistic regression
- RFM-based CLV
- Cox survival model

---

### 7.4.2 Improvement Measurement

Models must demonstrate:
- Statistically significant lift
- Consistent gains across time
- Improvement in business-relevant metrics

Example:
- Lift in retention rate at fixed budget
- Reduction in wasted incentives

### Statistical Validation

Performance improvements must be supported by statistical evidence.

Accepted approaches include:
- Confidence intervals over rolling windows
- Bootstrap resampling
- Paired tests on time-aligned predictions

Marginal improvements without statistical support are treated as inconclusive.

---

### 7.4.3 No-Regression Policy

A new model is rejected if:
- It underperforms baseline in any critical segment
- Gains are limited to non-business-critical cohorts

---

### 7.4.4 Model Promotion Criteria

To move to production:
- Must beat baseline for ≥ N consecutive periods
- Must pass stability and calibration checks
- Must be reviewed by stakeholders

### 7.4.5 Metric Trade-off Resolution

When metrics conflict:
- Business-aligned metrics take precedence over generic accuracy
- Stability and calibration outweigh small ranking gains
- High-value segment performance outweighs aggregate improvements

Trade-offs are documented during model review.

---

## 7.5 Offline-to-Online Alignment

Offline metrics are **necessary but not sufficient**.

Final validation occurs via:
- Controlled experiments
- Gradual rollout
- Business KPI monitoring

## Offline–Online Mismatch Handling

If online results diverge materially from offline expectations:
- Rollback or shadow mode is triggered
- Root-cause analysis is performed
- Offline evaluation assumptions are revisited

Offline metrics are treated as hypotheses, not guarantees.

---

## 7.6 Summary

This evaluation strategy ensures:

- Time-correct validation
- Segment-aware performance visibility
- Baseline-grounded improvement claims
- Economic relevance over metric vanity

The goal is not to maximize AUC, but to:
> **Make better retention and value decisions in the real world.**