# Training & Pipeline Design

## Purpose

This document defines how models are trained, retrained, reproduced, and
historically reprocessed in a **safe, auditable, and cost-aware** manner.

The goals of this design are:
- Guaranteed reproducibility
- Controlled retraining
- Safe experimentation
- Zero corruption of production history

Training is treated as a **deterministic data pipeline**, not an ad-hoc process.

---

## 1. Training Frequency

Training cadence is explicitly aligned with:
- Demand volatility
- Data freshness
- Business criticality
- Operational cost

Different model classes follow different retraining strategies.

---

### 1.1 Forecasting Models

Forecasting models are retrained based on SKU demand behavior.

#### High-Volume / Fast-Moving SKUs
- Retraining cadence: **Weekly**
- Rationale:
  - Rapid demand shifts
  - Promotion sensitivity
  - High business impact of forecast errors
- Models:
  - Gradient boosting
  - Deep learning (LSTM / GRU)
  - Advanced time-series models

#### Stable / Long-Tail SKUs
- Retraining cadence: **Monthly**
- Rationale:
  - Low volatility
  - Diminishing returns from frequent retraining
- Models:
  - Statistical baselines
  - Lightweight ML models

#### Seasonal Models
- Retraining cadence:
  - Before known seasonal transitions
  - Ahead of major events (festivals, sales periods)
- Rationale:
  - Explicit seasonality recalibration
  - Avoid seasonal drift

Forecast retraining frequency is reviewed quarterly.

---

### 1.2 Stock-Out Risk Models

Stock-out risk models focus on **classification stability**, not raw accuracy.

- Retrained on a rolling historical window (typically **6–12 months**)
- Cadence increases during:
  - Supplier instability
  - Logistics disruptions
  - Rapid lead-time changes

Retraining frequency may be temporarily elevated during crisis periods.

---

### 1.3 Hierarchical Reconciliation

Hierarchical reconciliation is **not trained independently**.

- Recomputed automatically:
  - After each base forecast update
  - After any retraining of forecasting models
- Ensures consistency across:
  - SKU
  - Category
  - Store
  - Region

Reconciliation is deterministic and reproducible.

---

### 1.4 Training Triggers

Training can be initiated by:

- Scheduled retraining (calendar-based)
- Event-driven triggers:
  - Data schema changes
  - Confirmed drift alerts
  - Feature definition updates
  - Major business events

All triggers are logged with cause and scope.

---

## 2. Reproducibility Controls

Every training run is **fully deterministic and auditable**.

The system guarantees that **any model can be rebuilt exactly**.

---

### 2.1 Versioned Inputs

Each training run records immutable input references.

#### Data Snapshots
- Raw data snapshotted by **event time**
- Ingestion-time data is never used for training
- Snapshot boundaries are explicitly defined

#### Feature Versions
- Feature definitions are versioned
- Feature store commit hashes recorded
- Feature logic is immutable once promoted

#### Training Windows
- Explicit start and end timestamps
- No implicit or “latest” data usage

---

### 2.2 Versioned Code

Training code is fully version-controlled.

Tracked artifacts include:
- Model code (Git commit hash)
- Feature transformation logic
- Hyperparameter configurations
- Training scripts and orchestration logic

No training runs use uncommitted code.

---

### 2.3 Versioned Outputs

Every training run produces immutable outputs.

Tracked outputs include:
- Model artifacts (weights, scalers, configs)
- Evaluation and backtesting reports
- Calibration parameters
- Training metadata

Artifacts are stored in a versioned model registry.

---

### 2.4 Randomness Control

All stochastic behavior is controlled.

Controls include:
- Fixed random seeds
- Explicit library versions
- Deterministic data ordering
- Controlled parallelism

This prevents accidental variance across runs.

---

### 2.5 Rebuild Guarantee

Any trained model can be rebuilt using:

(data snapshot + feature version + code commit)


This is a **hard system guarantee**, not best effort.

---

## 3. Backfill & Reprocessing

The system supports full historical replay without production risk.

Backfills are treated as **first-class pipelines**.

---

### 3.1 Backfill Use Cases

Backfills are initiated for:

- New feature introduction
- Bug fixes in feature logic
- New SKU or store onboarding
- Model architecture upgrades
- Evaluation of alternative modeling approaches

Backfills are never ad-hoc.

---

### 3.2 Backfill Mechanics

A backfill follows a controlled sequence:

1. Recompute features for a specified historical range
2. Re-run training using the original historical context
3. Generate predictions for historical periods
4. Compare new outputs against previous versions

Comparisons are mandatory before promotion.

---

### 3.3 Backfill Isolation

Backfills are strictly isolated from live serving.

Isolation guarantees:
- No interference with production inference
- No overwriting of historical predictions
- No silent changes to downstream systems

Backfill outputs are staged separately.

---

### 3.4 Promotion Controls

Backfilled models and predictions:
- Require explicit approval
- Follow the same promotion pipeline as new models
- Are never auto-promoted

Historical predictions remain immutable.

---

## 4. Safety & Governance Guarantees

This training and pipeline design guarantees:

- Deterministic training
- Full auditability
- Safe experimentation
- Zero silent data corruption
- Reproducible historical analysis

Training is treated as **infrastructure**, not experimentation.

---

## End of Document
