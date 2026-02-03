# Monitoring, Drift Detection & Retraining

---

## 11.1 Data Drift Monitoring

Data drift is tracked at **feature-level and aggregate levels** to detect changes in customer behavior, data quality, or upstream pipelines.

---

### 11.1.1 Monitored Features

Key features monitored include:
- Behavioral / engagement features:
  - Session counts
  - Days since last activity
- Transactional features:
  - Total spend
  - Average order value
- Returns & refund features:
  - Return rate
  - Refund ratios
- Lifecycle features:
  - Tenure
  - Segment membership

Additional features flagged for monitoring if downstream models depend heavily on them.

---

### 11.1.2 Drift Metrics

For each feature:
- **Population stability index (PSI)** — detects distribution shifts
- **Kolmogorov-Smirnov (KS) statistic** — continuous feature comparison
- **Categorical divergence** — Jensen-Shannon divergence for discrete features
- **Missingness changes** — sudden increase in nulls triggers alerts

---

### 11.1.3 Monitoring Cadence

- Daily monitoring for high-velocity features (churn-related)
- Weekly for lower-frequency features (CLV or segment features)
- Alerts trigger **automated notifications** and dashboards

---

### 11.1.4 Data Quality Checks

- Schema enforcement
- Null rate thresholds
- Range validation
- Outlier detection

Data quality issues may **block inference** or trigger fallback defaults.

---

## 11.2 Model Drift Monitoring

Even with stable features, **model performance can degrade** over time due to behavioral changes.

---

### 11.2.1 Key Model Metrics

- **Churn prediction:**
  - Rolling AUC
  - Precision/Recall @ K
  - Calibration drift
- **CLV prediction:**
  - Rolling MAE / RMSE
  - Top-decile revenue capture
- **Segmentation stability:**
  - Segment migration rates
  - Cohort overlap metrics

---

### 11.2.2 Drift Detection Techniques

- Compare predicted distributions vs. historical expectations
- Monitor residuals over time
- Track cohort-level performance:
  - New vs. mature customers
  - Segment-specific drift
- Detect sudden spikes or drops in prediction scores

---

### 11.2.3 Operational Alerts

- Threshold-based triggers for automated alerts:
  - AUC drop > X%
  - Median CLV error > threshold
  - PSI > threshold on critical features
- Alerts routed to:
  - Data science team
  - MLops team
  - Business stakeholders if high-risk

### Alert-to-Action Mapping

Each alert type has a predefined response.

| Alert Type | Severity | Default Action |
|----------|---------|----------------|
| Feature PSI spike | Medium | Feature review |
| Missingness surge | High | Block inference / fallback |
| AUC degradation | High | Shadow retraining |
| Calibration drift | Medium | Threshold review |
| Segment instability | Medium | Segment audit |

Alerts without a defined action are not considered valid.

### Alert Severity & Escalation

Alerts are classified as:
- **Info**: Logged for trend analysis
- **Warning**: Requires review within SLA
- **Critical**: Immediate action required

Critical alerts:
- Page on-call engineer
- May trigger automatic safeguards

---

### 11.2.4 Intervention-Aware Monitoring

Monitoring distinguishes between:
- Natural behavior drift
- Intervention-induced behavior changes

Where possible:
- Predictions are tagged with downstream actions
- Performance is evaluated separately for treated vs untreated cohorts

This prevents feedback loops from silently contaminating training data.

---

## 11.3 Retraining Triggers

Retraining is **event-driven**, not strictly calendar-based, though periodic retraining is maintained as a safety net.

---

### 11.3.1 Automatic Retraining Conditions

- Data drift exceeds thresholds on key features
- Model performance degradation detected
- New cohort behaviors (e.g., marketing campaigns, onboarding surge)
- Feature store schema changes or updates

### Drift Remediation Principles

Not all drift requires retraining.

- Data drift → investigate pipelines and features
- Calibration drift → adjust thresholds
- Semantic drift → feature redesign
- Performance drift → retraining

Retraining is a last resort, not a reflex.

---

### 11.3.2 Scheduled Retraining

- Churn model: weekly or bi-weekly
- CLV model: monthly
- Segmentation: quarterly or triggered by drift detection

This ensures:
- Predictive performance remains stable
- The system adapts to evolving customer behavior
- Historical data is reprocessed to maintain point-in-time correctness

---

### 11.3.3 Retraining Pipeline

- Reuses snapshot feature datasets
- Applies versioned models
- Validates new model against:
  - Baselines
  - Shadow / canary deployment metrics
  - Segment-level performance checks

- Alerts triggered if retraining fails

---

### 11.3.4 Human Oversight

- High-risk retraining requires **manual review and approval**
- Performance degradation or drift detection can trigger:
  - Model retraining
  - Feature review
  - Business intervention

---

### 11.3.5 Retraining Cooldown & Stability Controls

After retraining:
- A minimum stabilization period is enforced
- Additional retraining is suppressed unless critical alerts fire

This prevents overreaction to transient noise.

--

## 11.4 Summary

Monitoring and retraining strategy ensures:

- **System reliability:** Data and model drift detected early
- **Predictive trustworthiness:** KPIs monitored continuously
- **Adaptation to behavior change:** Retraining triggered by meaningful signals
- **Auditability:** Every retraining and drift alert logged

## Monitoring System Health

The monitoring system itself is monitored for:
- Data freshness
- Alert delivery failures
- Metric computation errors

Silent monitoring failures are treated as high-risk incidents.

> By combining feature-level, model-level, and cohort-level monitoring, the Customer Intelligence System remains trustworthy and actionable over time.