# Feature Engineering & Feature Store

---

## 5.1 Feature Categories

Features are designed at the **customer level** and computed relative to an **as-of time `T`**.

Each feature belongs to a **semantic category**, which defines:
- Its business meaning
- Its stability expectations
- Its allowed usage

## Feature Eligibility & Usage Constraints

Not all features are permitted for all model types.

### Usage Rules (Non-Exhaustive)

- Churn models:
  - Allowed: behavioral, trend, satisfaction proxy features
  - Restricted: pure lifetime aggregates without temporal bounds

- CLV models:
  - Allowed: transactional, lifecycle, long-term behavioral features
  - Restricted: short-term volatility-only signals

- Segmentation:
  - Prioritizes stable, long-horizon features
  - Avoids short-term shock-sensitive features

Feature eligibility is enforced during:
- Model training
- Feature selection reviews
- Production deployment checks

---

### 5.1.1 Behavioral / Engagement Features

#### Description
Capture how actively and recently a customer interacts with the product.

#### Examples
- Sessions in last 7 / 30 / 90 days
- Days since last session
- Engagement trend (recent vs prior window)
- Active days ratio

#### Usage
- Primary signals for churn risk
- Early indicators of disengagement

#### Stability Profile
- Highly responsive
- Expected to change rapidly
- Sensitive to short-term shocks

---

### 5.1.2 Transactional / Value Features

#### Description
Capture monetary behavior and purchasing patterns.

#### Examples
- Total spend in last 30 / 90 / 180 days
- Average order value
- Purchase frequency
- Revenue velocity

#### Usage
- CLV estimation
- Customer prioritization
- Segment differentiation

#### Stability Profile
- Moderately stable
- Changes reflect real economic behavior

---

### 5.1.3 Returns & Satisfaction Proxy Features

#### Description
Capture negative experiences and dissatisfaction signals.

#### Examples
- Return rate (last 90 days)
- Refund amount ratio
- Time since last return
- Return reason frequency

#### Usage
- Churn risk amplification
- Segment interpretation

#### Stability Profile
- Sparse but high-impact
- Sensitive to policy changes

---

### 5.1.4 Lifecycle & Tenure Features

#### Description
Capture where the customer is in their lifecycle.

#### Examples
- Customer tenure (days since signup)
- Time since first purchase
- Lifecycle stage indicator

#### Usage
- Cold-start handling
- Normalizing expectations across cohorts

#### Stability Profile
- Highly stable
- Monotonic by design

---

### 5.1.5 Channel & Acquisition Features

#### Description
Capture how the customer was acquired and how they engage.

#### Examples
- Acquisition channel
- Primary device type
- Preferred platform

#### Usage
- Segment enrichment
- Bias awareness

#### Stability Profile
- Mostly static
- May drift slowly over time

---

### 5.1.6 Derived Risk & Trend Features

#### Description
Features that capture **change**, not just level.

#### Examples
- Spend drop percentage
- Engagement decay rate
- Volatility in activity
- Rolling z-scores

#### Usage
- Leading indicators of churn
- Sensitivity detection

#### Stability Profile
- Sensitive but informative
- Require careful smoothing

---

## 5.2 Feature Stability

Feature stability is explicitly designed to avoid **spurious churn signals** during abnormal periods.

---

### 5.2.1 Demand & Engagement Shocks

Examples:
- Marketing campaigns
- Product outages
- Seasonality spikes
- External events

#### Design Principles
- Use rolling averages instead of point-in-time values
- Normalize by customer baselines
- Compare relative change, not absolute values

---

### 5.2.2 Outlier Handling

- Extreme values capped using:
  - Percentile winsorization
  - Log transforms
- Long-tail behaviors preserved where meaningful

---

### 5.2.3 Feature Smoothing

- Short-term features may be:
  - Exponentially smoothed
  - Aggregated over overlapping windows
- Prevents overreaction to one-off events

---

### 5.2.4 Segment Stability Considerations

- Segmentation features prioritize:
  - Long-term behavior
  - Aggregated metrics
- Avoids segment churn driven by noise

---

## 5.3 Missing Data Handling

Missing data is treated as **information**, not an error.

---

### 5.3.1 Missingness Semantics

Missing values may indicate:
- True inactivity
- New customer (cold start)
- Tracking failure

These cases are **distinguished where possible**.

---

### 5.3.2 Default Values

#### Behavioral Features
- Defaults represent **zero activity**, not null
- Example: `sessions_last_30d = 0`

#### Monetary Features
- Defaults treated cautiously
- Zero ≠ missing
- Separate missing indicators used

---

### 5.3.3 Cold-Start Strategy

For new customers:
- Rely on:
  - Lifecycle features
  - Acquisition channel priors
- Avoid overconfident predictions

---

### 5.3.4 Online Inference Fallbacks

If features are unavailable:
- Use last known values (within TTL)
- Apply conservative defaults
- Reduce prediction confidence if needed

---

## 5.4 Feature Store Design

This system assumes a **centralized feature store**.

---

### 5.4.1 Feature Granularity

- Primary entity: `customer_id`
- Time-aware features keyed by:
  - `customer_id`
  - `as_of_time`

---

### 5.4.2 Offline & Online Parity

- Features computed once
- Served consistently to:
  - Training pipelines
  - Real-time inference APIs
- No dual logic paths

---

### 5.4.3 Feature Documentation

Every feature includes:
- Name & description
- Source tables
- Lookback window
- Update frequency
- Owner

## Feature Validation & Quality Monitoring

Automated checks are applied to all features, including:
- Range and type validation
- Null and missingness rates
- Distribution drift over time
- Sudden volatility detection

Validation failures:
- Block feature promotion
- Trigger alerts
- Require investigation before deployment

## Feature Ownership & Accountability

Each feature has a clearly defined owner responsible for:
- Correctness and definition
- Monitoring alerts
- Change approvals
- Deprecation decisions

Unowned features are not eligible for production use.

---

### 5.4.4 Feature Freshness & Staleness Guarantees

Each feature declares:
- Expected update frequency
- Maximum allowable staleness (TTL)

If staleness exceeds tolerance:
- Feature is excluded or downgraded
- Prediction confidence is reduced
- Alerts are raised for investigation

No silently stale features are served to models.

---

## 5.5 Feature Versioning

Feature evolution is inevitable and explicitly managed.

---

### 5.5.1 Versioning Strategy

- Semantic versioning:
  - MAJOR: breaking changes
  - MINOR: additive changes
  - PATCH: bug fixes

---

### 5.5.2 Backward Compatibility

- Old feature versions retained
- Models pinned to specific feature versions
- No silent changes

---

### 5.5.3 Change Management

Feature changes require:
- Impact analysis
- Backtesting on historical data
- Explicit rollout approval

---

### 5.5.4 Feature Deprecation

- Deprecated features:
  - Marked clearly
  - Supported for defined sunset period
- Prevents breaking downstream systems

---

## 5.6 Explainability & Interpretability

Feature design prioritizes:
- Business meaning
- Consistent definitions
- Clear units and scales

This enables:
- Model debugging
- Stakeholder trust
- Safer decision-making

## Feature Interaction & Redundancy Management

To preserve interpretability and stability:
- Highly correlated features are reviewed
- Redundant aggregates are pruned where possible
- Proxy features closely tied to labels are audited

This reduces overfitting and improves explanation reliability.

---

## 5.7 Summary

This feature framework ensures:

- Stable signals under real-world noise
- Explainable inputs tied to business behavior
- Reproducibility across time
- Safe evolution through versioning

The feature store acts as the **contract** between data, models, and consumers — making the Customer Intelligence System reliable at scale.