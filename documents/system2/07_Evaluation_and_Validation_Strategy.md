# Evaluation & Validation Strategy

## Purpose

This document defines how models are evaluated, compared, and validated
before being allowed into production.

The evaluation framework is designed to:
- Reflect real business costs
- Prevent metric gaming
- Surface tail and segment failures
- Enforce baseline accountability

Evaluation correctness is treated as a **safety requirement**, not a preference.

---

## 1. Offline Metrics

Metrics are selected based on **business impact**, **scale sensitivity**, and
**failure cost** — not leaderboard appeal.

No single metric is used in isolation.
All evaluation dashboards present **multiple complementary metrics**.

---

### 1.1 Forecasting Metrics

#### Mean Absolute Error (MAE)
- Measures average absolute deviation
- Interpretable in original demand units
- Stable across demand regimes

Used as a primary sanity-check metric.

---

#### Root Mean Squared Error (RMSE)
- Penalizes large errors more heavily
- Sensitive to extreme misses

Critical for identifying:
- Potential stock-outs
- Overstocking risk from large forecast errors

---

#### Weighted Absolute Percentage Error (WAPE)
- Scale-aware and aggregation-friendly
- Suitable for comparing SKUs of different volumes

Primary metric for **inventory planning** decisions.

---

#### Mean Absolute Percentage Error (MAPE)
- Used cautiously and selectively
- Excluded for:
  - Low-volume SKUs
  - Intermittent demand

MAPE is never used as a sole decision metric.

---

#### Quantile Loss (Pinball Loss)
- Evaluates probabilistic forecasts
- Measures forecast uncertainty calibration
- Supports safety stock and risk-aware planning

Required for models producing prediction intervals.

---

### 1.2 Stock-Out Risk Metrics

Stock-out risk is an asymmetric classification problem.

#### Recall (Primary)
- Measures missed stock-out events
- Prioritized due to high business cost of false negatives

Recall thresholds are strict and enforced.

---

#### Precision (Secondary)
- Controls false alarm rates
- Prevents operational fatigue

Precision is monitored but never optimized at the expense of recall.

---

#### Cost-Weighted Loss
- Explicitly models asymmetric business costs
- Penalizes false negatives more heavily than false positives

Used for final model ranking and approval.

---

## 2. Backtesting Methodology

All evaluation uses **strict time-based validation**.
Random splits are explicitly forbidden.

---

### 2.1 Rolling-Origin Backtesting

Backtesting follows a rolling-origin framework:

1. Train on a fixed historical window
2. Predict a fixed forecast horizon (e.g., 7, 14, 30 days)
3. Advance the origin forward
4. Repeat across multiple time windows

This mirrors real production usage.

---

### 2.2 Seasonal Coverage

Backtests are designed to cover:
- Multiple seasonal cycles
- Known holiday periods
- Promotion-heavy intervals

Seasonal blind spots are treated as critical evaluation failures.

---

### 2.3 Cold-Start Simulation

Cold-start scenarios are explicitly tested.

Methods include:
- Artificial truncation of SKU history
- Limited data availability simulations
- Fallback model evaluation

Cold-start behavior must be stable and explainable.

---

### 2.4 Pipeline Parity

All evaluation:
- Uses production-identical feature pipelines
- Shares the same data cleaning logic
- Enforces identical time semantics

No evaluation shortcuts are allowed.

---

## 3. Segment-Level Analysis

Performance is analyzed across **business-relevant segments**, not global averages.

---

### 3.1 Segmentation Dimensions

Models are evaluated across:

- High-volume vs low-volume SKUs
- Intermittent vs stable demand
- Promotional vs non-promotional periods
- Long vs short lead-time items
- High-margin vs low-margin categories (if applicable)

---

### 3.2 Why Segment Analysis Matters

Global averages can hide:
- Catastrophic failures in tail SKUs
- Systematic underperformance in promotions
- Risk amplification in long lead-time items

Inventory cost is driven by **tail errors**, not mean accuracy.

---

### 3.3 Segment Eligibility Gates

For production eligibility:
- Models must meet minimum thresholds per segment
- Failing any critical segment blocks promotion
- Exceptions require explicit business sign-off

Segment-level failures are not ignored.

---

## 4. Baseline Comparison

Every model is evaluated against **explicit baselines**.

---

### 4.1 Baseline Models

Baselines include:
- Naive forecast (last value)
- Seasonal naive
- Simple moving averages
- Historical averages

Baselines are versioned and reproducible.

---

### 4.2 Baseline Rules

A model is only considered for production if:

- It outperforms baselines consistently
- Improvements persist across time windows
- Gains hold under distribution shifts
- Performance does not degrade in critical segments

One-off improvements are insufficient.

---

### 4.3 Improvement Reporting

Improvements are reported using:

- Absolute metric deltas
- Percentage improvements
- Business impact simulations, such as:
  - Stock-out reduction
  - Inventory turnover improvement
  - Safety stock reduction

Model improvements must translate to business value.

---

## 5. Evaluation Governance

Evaluation outcomes are:
- Logged and versioned
- Reviewed before deployment
- Stored alongside model artifacts

Models that fail evaluation are **not promoted**, regardless of complexity.

---

## End of Document
