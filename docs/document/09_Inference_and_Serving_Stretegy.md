# Inference & Serving Strategy

---

## 9.1 Batch Inference

Batch inference is the **primary serving mode** for customer intelligence models  
(churn, CLV, segmentation).

It prioritizes:
- Scalability
- Cost efficiency
- Deterministic outputs
- Business workflow alignment

---

### 9.1.1 Batch Schedule

Batch predictions are generated on a fixed cadence aligned with business usage.

Typical schedules:
- **Churn**: Daily or weekly
- **CLV**: Weekly or monthly
- **Segmentation**: Monthly or quarterly

Schedules are:
- Explicitly configured
- Logged per run
- Independent of training cadence

---

### 9.1.2 Input Data Cutoff (As-Of Time)

Each batch run uses:
- A clearly defined **as-of timestamp**
- Only data available up to that time

This prevents:
- Lookahead bias
- Inconsistent reruns
- Silent data leakage

### Prediction Freshness Guarantees

Each prediction type defines:
- Maximum acceptable age
- Refresh expectation

If freshness guarantees are violated:
- Predictions are flagged as stale
- Automated actions may be suppressed
- Consumers are notified via metadata

---

### 9.1.3 Batch Processing Flow

1. Load feature snapshots (point-in-time correct)
2. Apply the pinned model version
3. Generate predictions
4. Run output validation checks
5. Persist results to storage

Each step is:
- Idempotent
- Retry-safe
- Logged

---

### 9.1.4 Output Storage

Predictions are stored in:
- Append-only tables
- Partitioned by:
  - Prediction date
  - Model version

Stored outputs include:
- Prediction score
- Prediction timestamp
- Model version
- Feature version
- Confidence or uncertainty (if available)

---

### 9.1.5 Batch Failure Handling

If a batch job fails:
- Previous successful predictions remain available
- No partial results are published
- Alerts are raised

Fallback behavior:
- Use last known good predictions
- Mark outputs as stale if SLA is exceeded

### Serving Incident Response

For serving incidents:
- Severity is assessed based on impacted consumers
- Fallback modes are activated
- Communication is sent to affected teams

Post-incident:
- Root-cause analysis is documented
- Preventive actions are tracked


### Serving SLA Ownership & Enforcement

Each serving mode has an explicit SLA owner.

- SLA breaches trigger:
  - Alerts
  - Incident tracking
  - Root-cause analysis
- Repeated breaches require:
  - Capacity adjustment
  - Pipeline redesign
  - Business stakeholder notification

SLAs are enforced, not informational.

---

## 9.2 Real-Time Inference (If Applicable - not for this system)

Real-time inference is **optional** and used only when:
- Immediate decisions are required
- Latency constraints justify complexity

Examples:
- On-session churn risk
- Personalized offers
- Real-time eligibility checks

---

### 9.2.1 Latency Requirements

Defined SLAs:
- **p95 latency target** (e.g., <100ms)
- **p99 latency ceiling**

Latency budgets include:
- Feature retrieval
- Model execution
- Network overhead

---

### 9.2.2 Feature Availability Constraints

Real-time inference uses:
- A limited subset of features
- Only low-latency, online-safe signals

Offline-only features are:
- Excluded
- Or approximated with cached values

---

### 9.2.3 Fallback Behavior

If real-time inference fails due to:
- Feature unavailability
- Timeout
- Model service error

Fallback strategies include:
- Returning last batch prediction
- Returning a default conservative score
- Skipping model-driven action

Fallback behavior is:
- Explicitly defined
- Logged
- Monitored

---

### 9.2.4 Consistency with Batch Predictions

Batch and real-time models:
- Share feature definitions where possible
- Use compatible scaling and transformations

Differences are:
- Documented
- Justified
- Tested

---

## 9.3 Output Versioning

Predictions are treated as **versioned data products**, not ephemeral signals.

---

### 9.3.1 Output Schema Versioning

Each prediction record includes:
- Output schema version
- Model version
- Training run ID

Schema changes:
- Are backward-compatible where possible
- Trigger new output versions when breaking

---

### 9.3.2 Prediction Lineage

Every prediction can be traced back to:
- Input data snapshot
- Feature version
- Model artifact
- Training configuration

This supports:
- Debugging
- Audits
- Reproducing past decisions

---

### 9.3.3 Output Validation & Guardrails

Before publishing predictions:
- Value ranges are checked
- Null or NaN rates validated
- Distribution shifts detected

Invalid outputs:
- Are quarantined
- Do not overwrite previous predictions

### Inter-Batch Consistency Checks

Between consecutive batch runs:
- Distribution shifts are monitored
- Large score jumps are flagged
- Unexpected population changes are investigated

This prevents silent degradation across runs.

---

### 9.3.4 Consumer Safety

Downstream consumers (CRM, BI, pricing engines) are protected via:
- Stable schemas
- Explicit deprecation timelines
- Clear documentation of score meaning

No consumer relies on:
- Implicit defaults
- Unversioned outputs

### Prediction Semantics Contract

Each score explicitly defines:
- Meaning (probability, rank, estimate)
- Valid range
- Intended use
- Known limitations

Scores must not be interpreted outside their documented semantics.

---

## 9.4 Consumer Integration

Predictions are consumed by:
- Marketing automation
- Retention workflows
- Analytics dashboards
- Decision engines

Consumption patterns are:
- Read-only
- Non-blocking
- Decoupled from inference execution

## Access Control & Authorization

Prediction access is governed by:
- Role-based access control (RBAC)
- Least-privilege principles

Consumers are authorized for:
- Specific outputs
- Specific versions
- Specific usage contexts

Unauthorized access to predictions is blocked and logged.

---

## 9.5 Summary

This inference and serving strategy ensures:

- Reliable prediction availability
- Safe degradation under failure
- Clear ownership of outputs
- Full traceability and auditability

The system guarantees that:
> **Predictions are consistent, explainable, and safe to consume — even when things break.**