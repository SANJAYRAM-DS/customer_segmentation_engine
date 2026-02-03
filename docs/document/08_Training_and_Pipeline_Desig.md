# Training & Pipeline Design

---

## 8.1 Training Frequency

Model retraining is driven by **data evolution**, not arbitrary schedules.

Different tasks have different cadences based on:
- Behavioral volatility
- Data volume
- Business risk tolerance

---

### 8.1.1 Churn Model Retraining

#### Cadence
- **Weekly or bi-weekly** retraining

#### Rationale
- Churn signals are sensitive to recent behavior
- Engagement patterns can shift quickly due to:
  - Campaigns
  - Product changes
  - External events

#### Constraints
- Retraining must complete within a fixed SLA
- Retraining failure should not block inference

---

### 8.1.2 CLV Model Retraining

#### Cadence
- **Monthly or quarterly** retraining

#### Rationale
- CLV is a long-horizon signal
- Short-term noise should not dominate predictions

---

### 8.1.3 Segmentation Retraining

#### Cadence
- **Quarterly**, or triggered by drift detection

#### Rationale
- Segments should be stable and interpretable
- Frequent changes reduce trust and usability

---

### 8.1.4 Retraining Triggers & Suppression Rules

Retraining is initiated when one or more of the following occur:

- Significant data distribution drift detected
- Sustained degradation in online or offline metrics
- Feature schema or logic changes
- Explicit business-driven events (e.g., major product change)

Retraining may be suppressed if:
- Input data quality checks fail
- Feature availability SLAs are violated
- Previous model has not yet stabilized

Retraining is never purely schedule-driven.

---

## 8.2 Reproducibility Controls

Every training run must be **fully reproducible**.

Reproducibility is treated as a **hard requirement**, not best practice.

---

### 8.2.1 Data Snapshotting

For each training run:
- Input datasets are snapshotted
- Snapshots are immutable
- Snapshot IDs are stored with the model

This includes:
- Raw source tables
- Feature tables
- Label datasets

---

### 8.2.2 Feature Version Pinning

Models are trained against:
- Explicit feature versions
- Fixed feature definitions

No model trains against “latest” features.

---

### 8.2.3 Code Versioning

Each training run records:
- Git commit hash
- Training configuration
- Hyperparameters

Any change in code or config produces a new model version.

---

### 8.2.4 Randomness Control

- Random seeds are fixed where applicable
- Stochastic components documented
- Non-determinism explicitly acknowledged

---

### 8.2.5 Model Artifacts

Each trained model produces:
- Serialized model artifact
- Feature importance metadata
- Training metrics
- Validation reports

All artifacts are versioned and retained.

---

### 8.2.6 Training Resource Isolation & Cost Controls

Training workloads are isolated from inference workloads.

Controls include:
- Dedicated compute pools
- Resource quotas per pipeline
- Cost monitoring per training run

Training jobs exceeding resource limits are terminated or throttled.

---

## 8.3 Backfill & Reprocessing

The system supports **historical replay**.

This is essential for:
- Debugging
- Auditing
- Retrospective analysis
- Model improvement

---

### 8.3.1 Full Historical Reprocessing

Capabilities include:
- Recomputing features for past as-of times
- Regenerating labels with corrected logic
- Retraining models on historical snapshots

---

### 8.3.2 Partial Backfills

Partial reprocessing supported for:
- Specific customer cohorts
- Specific time ranges
- Specific feature versions

This avoids unnecessary full replays.

---

### 8.3.3 Backfill Safety Controls

Backfills are:
- Isolated from production inference
- Executed in separate environments
- Explicitly approved when touching past predictions

---

### 8.3.4 Schema & Logic Changes

When schema or label logic changes:
- Old models remain reproducible
- New models trained on updated logic
- Comparisons performed before promotion

---

## Experimentation vs Production Training

- Experimental runs:
  - Clearly labeled
  - Isolated from production pipelines
  - Never promoted automatically

- Production training runs:
  - Follow full reproducibility and approval requirements
  - Produce deployable artifacts

No experimental artifact is used in production inference.

---

## 8.4 Pipeline Structure

Training pipelines follow a **modular, auditable structure**.

---

### 8.4.1 Pipeline Stages

1. Data extraction & validation  
2. Feature computation (point-in-time correct)  
3. Label generation  
4. Dataset assembly  
5. Model training  
6. Evaluation & baseline comparison  
7. Artifact registration  

Each stage:
- Has explicit inputs and outputs
- Can be rerun independently

---

### 8.4.2 Failure Handling

- Pipeline failures are:
  - Logged
  - Alerted
  - Non-destructive
- Partial outputs are not promoted

### Degradation & Recovery Strategy

If retraining fails repeatedly:
- Existing production model remains active
- Alerts are escalated
- Root-cause analysis is required before retry

Prolonged inability to retrain triggers:
- Model risk review
- Potential fallback to simpler baselines

---

### 8.4.3 Model Promotion & Approval Workflow

Model promotion to production requires:

- Successful completion of evaluation stages
- No regression against baselines
- Approval from:
  - ML owner
  - Business stakeholder (where applicable)

Automated pipelines may prepare models, but promotion is a controlled action.

--

## 8.5 Versioning & Lineage

Every prediction can be traced back to:

- Data snapshot
- Feature version
- Model version
- Training run

This ensures:
- Debuggability
- Regulatory readiness
- Long-term maintainability

### Lineage Enforcement

Models or predictions lacking complete lineage metadata are:
- Blocked from promotion
- Excluded from production serving

Lineage completeness is a hard requirement, not advisory.

---

## 8.6 Summary

This training and pipeline design ensures:

- Deterministic, repeatable model builds
- Safe evolution over time
- Full auditability of predictions
- Reliable backtesting and experimentation

The system is designed so that:
> **Any prediction can be recreated exactly, months or years later.**