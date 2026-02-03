# Model Design & Selection

---

## 6.1 Baseline Models

Baseline models establish:
- A minimum acceptable performance bar
- Interpretability anchors
- Regression testing references

No advanced model is deployed unless it **clearly outperforms baselines** on business metrics.

## Model Promotion & Gating Criteria

A model is eligible for production deployment only if:

- It outperforms the relevant baseline on **primary business-aligned metrics**
- Performance gains are statistically validated (e.g., backtests or experiments)
- No critical regressions are observed on secondary metrics
- Inference latency and cost remain within defined SLAs

Models failing any gate are rejected regardless of theoretical superiority.

---

### 6.1.1 Rule-Based Baselines

#### Description
Simple heuristics based on business logic.

#### Examples
- Churn if no activity in last N days
- High value if lifetime spend > threshold
- At-risk if engagement drops below baseline

#### Purpose
- Sanity check for ML outputs
- Fallback during system outages
- Business explainability reference

#### Limitations
- Brittle
- Do not generalize across segments
- Poor early-warning capability

---

### 6.1.2 Statistical Baselines (Churn)

#### Logistic Regression

- Inputs: time-windowed behavioral features
- Outputs: churn probability

**Why it exists**
- Strong interpretability
- Fast training
- Robust under data shifts

**Limitations**
- Linear assumptions
- Limited interaction modeling

---

### 6.1.3 Statistical Baselines (CLV)

#### Historical Average / RFM

- CLV approximated from:
  - Past spend
  - Frequency
  - Recency

**Why it exists**
- Transparent
- Low operational cost
- Benchmark for ML uplift

---

### 6.1.4 Survival Analysis Baseline

#### Cox Proportional Hazards

- Models time-to-churn
- Handles censoring explicitly

**Why it exists**
- Time-aware
- Interpretable hazard ratios
- Strong foundation for churn modeling

---

## 6.2 Advanced Models

Advanced models are introduced **only when justified by measurable gains**.

---

### 6.2.1 Tree-Based Models

#### Gradient Boosted Trees (XGBoost / LightGBM)

**Used For**
- Churn classification
- CLV regression

**Why**
- Handles non-linear interactions
- Robust to mixed feature types
- Strong tabular performance

**Trade-offs**
- Reduced interpretability
- More tuning required
- Risk of overfitting without care

---

### 6.2.2 Survival-Based ML Models

#### Random Survival Forests / Gradient Boosted Survival

**Used For**
- Time-to-churn estimation
- Dynamic risk scoring

**Why**
- Better handling of non-proportional hazards
- Flexible risk modeling over time

---

### 6.2.3 Probabilistic CLV Models

#### BG/NBD + Gamma-Gamma

**Used For**
- Transactional CLV estimation
- Low-frequency purchase businesses

**Why**
- Theoretically grounded
- Interpretable parameters
- Handles purchase timing explicitly

**Limitations**
- Assumes stationary behavior
- Less responsive to recent trends

---

### 6.2.4 Deep Learning Models (Optional)

#### Sequence Models (RNN / Transformer)

**Used For**
- Behavior embeddings
- High-frequency event streams

**Why**
- Captures sequential dependencies
- Learns latent behavior patterns

**Constraints**
- High compute cost
- Harder to debug
- Only justified if downstream gains exist

---

### 6.2.5 Model-Specific Failure Modes

Different model families fail in different ways:

- Rule-based:
  - Sudden regime changes break assumptions

- Linear / Cox models:
  - Miss non-linear interactions
  - Underperform for complex behavior patterns

- Tree-based models:
  - Overfit to recent trends
  - Sensitive to feature drift

- Deep learning models:
  - Silent degradation
  - Difficult root-cause analysis

Monitoring strategies are aligned to expected failure modes.

---

## 6.3 Model Selection Rationale

Model choice balances **four competing constraints**.

---

### 6.3.1 Accuracy vs Interpretability

- Baselines provide transparency
- Advanced models provide lift
- Explainability tools used where required

Default preference:
> **Simplest model that meets business KPIs**

## Probability Calibration Requirements

For probabilistic outputs (e.g., churn risk):

- Calibration is mandatory
- Predicted probabilities must align with observed outcomes
- Poorly calibrated models are rejected even if ranking metrics are strong

Calibration quality is monitored continuously post-deployment.

---

### 6.3.2 Stability vs Reactivity

- Statistical models: stable, slow to adapt
- ML models: reactive, sensitive to drift

Production choice depends on:
- Business tolerance for volatility
- Frequency of behavior change

---

### 6.3.3 Cost vs Benefit

| Model Type | Training Cost | Inference Cost | Maintenance |
|----------|--------------|----------------|-------------|
| Rules | Very Low | Very Low | Low |
| Logistic / Cox | Low | Low | Low |
| GBDT | Medium | Medium | Medium |
| Deep Learning | High | High | High |

Models must justify their **total cost of ownership**.

---

### 6.3.4 Organizational Readiness

- Team skillset
- Monitoring maturity
- Debugging capability

A theoretically superior model is rejected if:
- It cannot be reliably operated
- It cannot be explained to stakeholders

---

## Offline vs Online Evaluation Expectations

- Offline evaluation:
  - Used for model screening and regression detection
  - Must respect temporal validation constraints

- Online evaluation:
  - Required for high-impact models
  - Measures real business outcomes (retention, ROI, cost)

Offline performance alone is insufficient for long-term adoption.

---

## 6.4 Retraining Cost & Feasibility

Retraining is treated as a **first-class operational concern**.

---

### 6.4.1 Retraining Frequency

- Churn models: weekly or monthly
- CLV models: monthly or quarterly
- Segmentation: quarterly or on drift detection

---

### 6.4.2 Data Volume & Compute

- Tabular models scale linearly with data
- Deep models scale poorly without sampling
- Historical snapshots stored for reproducibility

---

### 6.4.3 Automation Level

- Fully automated pipelines preferred
- Manual intervention limited to:
  - Model review
  - Promotion decisions

---

### 6.4.4 Rollback & Fallback

- Previous model versions retained
- Baseline models available as fallback
- Rollback must be instantaneous

---

## Safe Deployment & Rollout Strategy

New models are introduced using:
- Shadow deployments
- Canary releases
- Gradual traffic ramp-up

This allows:
- Performance validation without business impact
- Early detection of unexpected behavior

Full rollout occurs only after successful shadow evaluation.

---

## 6.5 Summary

Model design in this system follows **engineering pragmatism**:

- Start simple
- Measure uplift rigorously
- Escalate complexity only when justified
- Optimize for long-term operability

Every model deployed must:
- Solve a clearly defined task
- Outperform a strong baseline
- Be retrainable within operational constraints

## Cross-Model Consistency Expectations

While models are trained independently:

- Outputs must be internally consistent
- Extreme conflicts (e.g., very high CLV + very high churn risk) are reviewed
- Downstream systems are expected to consume signals jointly, not in isolation