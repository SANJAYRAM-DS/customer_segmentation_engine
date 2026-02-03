# Problem Formulation & ML Tasks

---

## 2.1 ML Tasks

This system is **not a single ML problem**.  
It is a **composed intelligence system** consisting of multiple, explicitly scoped ML tasks.

Each task has:
- A distinct objective
- A distinct target
- A distinct evaluation lens
- A distinct failure mode

---

### 2.1.1 Churn Prediction (Supervised Classification / Survival)

#### Task Definition
Predict the likelihood that a customer will **churn within a defined future time window**, given their historical behavior.

This is formulated as:
- Binary classification **OR**
- Time-to-event (survival analysis), depending on business maturity

#### Why This Exists
To enable **early intervention** before the customer becomes inactive or disengages.
#### Modeling Maturity Considerations

Binary classification is sufficient when:
- Decision timing is coarse (e.g., monthly interventions)
- Data volume is limited

Survival-based approaches are introduced when:
- Time-to-event precision is required
- Data volume supports stable hazard estimation
- Intervention timing materially impacts outcomes


#### Output
- `churn_probability` (e.g., P(churn in next 30/60/90 days))
- Optional: survival curve or hazard rate

#### Key Clarification
This task predicts **risk**, not certainty.  
It is **directional intelligence**, not a churn guarantee.

---

### 2.1.2 Customer Lifetime Value (CLV) Estimation

#### Task Definition
Estimate the **expected future monetary value** of a customer over a defined horizon.

This may be implemented as:
- Regression on future revenue
- Probabilistic CLV (BG/NBD + Gamma-Gamma)
- Survival-based revenue modeling

#### Why This Exists
To guide **economic prioritization**, not just churn prevention.

#### Output
- `predicted_clv`
- Optional confidence intervals or distributional estimates

#### Key Clarification
CLV is **forward-looking**, not historical spend.
High past spend ≠ high future value.

---

### 2.1.3 Customer Segmentation (Unsupervised Learning)

#### Task Definition
Group customers into **behaviorally meaningful segments** based on observed patterns.

Typical approaches:
- KMeans (fixed segments, interpretable)
- HDBSCAN (adaptive segments, noise-aware)
- Embedding + clustering (advanced)

#### Why This Exists
To:
- Interpret customer heterogeneity
- Enable segment-level strategies
- Improve explainability of churn & CLV outputs

#### Output
- `customer_segment_id`
- Segment descriptors (post-hoc)

#### Key Clarification
Segmentation is **descriptive**, not predictive.
It does not directly predict churn or revenue.

---

### 2.1.4 Behavior Embeddings (Optional, Advanced)

#### Task Definition
Learn dense vector representations of customer behavior over time.

Examples:
- Sequence models over sessions/orders
- Autoencoders on aggregated behavior
- Representation learning for personalization

#### Why This Exists
To:
- Capture non-linear behavior patterns
- Power downstream personalization systems
- Improve clustering or similarity search

#### Output
- `behavior_embedding_vector`

#### Key Clarification
Embeddings are **enablers**, not business outputs.
They must be justified by downstream use.

---

## 2.1.5 Task-Level Evaluation Metrics

Each ML task is evaluated using **task-appropriate metrics**, not a single global score.

### Churn Prediction

Primary evaluation focuses on **decision usefulness**, not raw accuracy.

- Calibration (predicted risk vs observed churn)
- Recall at top-K highest risk customers
- Stability across time windows

Secondary metrics:
- AUROC
- Precision-Recall AUC

### Customer Lifetime Value (CLV)

CLV models are evaluated over the defined horizon.

- Mean Absolute Error (MAE) or RMSE on realized future revenue
- Bias analysis at high-value percentiles
- Longitudinal error tracking over time

### Customer Segmentation

Segmentation quality is evaluated qualitatively and quantitatively.

- Segment stability across retraining cycles
- Segment size distribution monitoring
- Business interpretability and actionability
- Downstream usefulness in campaigns or CRM workflows

---

## 2.1.6 Prediction Confidence & Coverage

Model outputs may include **confidence, uncertainty, or coverage indicators**.

- Low-confidence predictions must be identifiable downstream
- Downstream systems may:
  - Suppress automated actions
  - Apply conservative thresholds
  - Route cases for human review

Confidence indicators are designed to reduce risk from sparse or ambiguous data.

---

## 2.2 Target Variables

This section defines **what the models are trained to predict** and **how labels are constructed**.

---

### 2.2.1 Churn Target

#### Definition
A customer is considered churned if they meet **inactivity or disengagement criteria** within a future window.

Example definitions:
- No orders for 90 days
- No sessions + no purchases for 60 days
- Explicit account closure

#### Target Variable
- Binary label: `churned_{window}` ∈ {0, 1}
- OR event time: `time_to_churn`

#### Observation Window
- Labels are generated **strictly after the feature window**
- Lookahead window must be fixed and versioned

#### Important Constraint
⚠ **No future information is allowed in features**
Label leakage invalidates the system.

---

### 2.2.2 CLV Target

#### Definition
Total realized revenue from a customer **after a cutoff date**, over a defined horizon.

#### Target Variable
- Continuous value: `future_revenue_{horizon}`

#### Horizon Examples
- 6 months
- 12 months
- Lifetime (censored)

#### Censoring
- Customers still active at horizon end are right-censored
- Survival-aware modeling may be required

---

### 2.2.3 Segmentation Target

#### Definition
There is **no ground-truth label**.

Segments are derived from:
- Behavioral features
- Value metrics
- Engagement patterns

#### Post-hoc Validation
- Stability over time
- Business interpretability
- Downstream usefulness

---

## 2.3 Temporal Nature of the Problem

This system is **fundamentally time-dependent**.

Static modeling assumptions **do not apply**.

---

### 2.3.1 Time as a First-Class Axis

Every customer observation is tied to:
- An **as-of date**
- A **historical feature window**
- A **future prediction window**

Example:
- Features: last 90 days
- Prediction: next 30 days churn risk

---

### 2.3.2 Sliding Window Behavior

Customer behavior evolves:
- New sessions
- New orders
- Returns
- Changes in engagement intensity

Predictions must:
- Be refreshed periodically (daily/weekly)
- Reflect recent behavior more strongly

---

### 2.3.3 Concept Drift

Over time:
- Customer behavior changes
- Business policies change
- Seasonality impacts engagement

Implications:
- Models must be retrained
- Segments must be revalidated
- Thresholds must be monitored

---

### 2.3.4 Temporal Consistency Requirement

At any prediction time `T`:
- Features must use data ≤ `T`
- Labels must be derived from data > `T`

This applies to:
- Training
- Validation
- Backtesting
- Online inference

---

## 2.3.5 Cold-Start & Sparse History Customers

Customers with insufficient behavioral history may not support reliable predictions.

Handling strategies include:
- Default baseline estimates
- Reduced-confidence outputs
- Delayed prediction until minimum data thresholds are met

Cold-start handling is treated as a **first-class system concern**, not an edge case.

---

## 2.4 Explicit Non-Goals

This section prevents **scope creep and misuse**.

---

### 2.4.1 What This System Does NOT Do

- Does not explain *why* an individual customer churned causally
- Does not optimize marketing strategy automatically
- Does not select incentives or discounts
- Does not replace experimentation or A/B testing
- Does not predict exact future customer actions
- Does not operate as a real-time recommender system

---

### 2.4.2 What This System Is NOT Evaluated On

- Not judged solely by model accuracy
- Not required to be perfectly interpretable at feature level
- Not required to predict rare edge-case behavior

---

### 2.4.3 Responsibility Boundaries

This system provides:
> **Signals and estimates**

Other systems or humans decide:
- What action to take
- How much to spend
- When to intervene

---

## 2.5 Summary

This Customer Intelligence System is a **multi-task, time-aware ML system** composed of:

- Predictive tasks (churn, CLV)
- Descriptive tasks (segmentation)
- Optional representation learning (embeddings)

Each task:
- Has a clearly defined target
- Respects temporal causality
- Serves a distinct business purpose

By explicitly defining **what is predicted, when, and why**, this section prevents:
- Problem confusion
- Label leakage
- Over-claiming model capability

### Relationship Between Predictive Tasks

Churn risk and CLV are **related but independent signals**.

- High churn risk does not imply low future value
- Low churn risk does not imply high economic value

Downstream decision systems must consider **both dimensions jointly** when prioritizing actions.
