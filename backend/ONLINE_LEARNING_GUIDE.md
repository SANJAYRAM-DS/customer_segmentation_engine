# Online Learning Implementation Guide

## Overview

Online learning (incremental learning) allows models to update continuously as new data arrives, without requiring full retraining. This is particularly useful for:

- **Adapting to drift gradually** - Models stay fresh as customer behavior changes
- **Reducing training costs** - No need to retrain on full dataset
- **Faster updates** - Can update daily or even hourly
- **Continuous improvement** - Models learn from recent data

---

## How It Works

### Traditional Batch Learning:
```
Week 1: Train on all historical data (expensive)
Week 2: Retrain on all data + new week (expensive)
Week 3: Retrain on all data + new weeks (expensive)
...
```

### Online Learning:
```
Week 1: Train on historical data (one-time)
Week 2: Update with just new week's data (cheap)
Week 3: Update with just new week's data (cheap)
...
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  ONLINE LEARNING FLOW                    │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐                                        │
│  │ Batch Model  │ (Initial training on historical data)  │
│  │  (Week 0)    │                                        │
│  └──────┬───────┘                                        │
│         │                                                 │
│         ▼                                                 │
│  ┌──────────────┐                                        │
│  │Online Learner│ (Initialize from batch model)          │
│  └──────┬───────┘                                        │
│         │                                                 │
│         ▼                                                 │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │ New Data     │ -> │ Partial Fit  │ (Incremental)      │
│  │ (Week 1)     │    │              │                    │
│  └──────────────┘    └──────┬───────┘                   │
│                              │                            │
│                              ▼                            │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │ New Data     │ -> │ Partial Fit  │ (Incremental)      │
│  │ (Week 2)     │    │              │                    │
│  └──────────────┘    └──────┬───────┘                   │
│                              │                            │
│                              ▼                            │
│                         [Continue...]                     │
│                                                           │
│  Every N weeks: Full retrain to reset                    │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation

### 1. Basic Usage

```python
from backend.models.online_learning import OnlineLearner
import numpy as np

# Create online learner
learner = OnlineLearner(
    model_type="churn",
    learning_rate=0.01,
)

# Initial training (or load from batch model)
X_initial = np.random.randn(10000, 50)
y_initial = np.random.randint(0, 2, 10000)
learner.partial_fit(X_initial, y_initial, classes=[0, 1])

# Save initial model
learner.save(version="v1_initial")

# Daily updates
for day in range(7):
    # Get new day's data
    X_new = np.random.randn(1000, 50)
    y_new = np.random.randint(0, 2, 1000)
    
    # Incremental update
    learner.partial_fit(X_new, y_new)
    
    # Save updated model
    learner.save(version=f"v1_day{day+1}")

# Make predictions
X_test = np.random.randn(100, 50)
predictions = learner.predict(X_test)
```

### 2. With Orchestration

```python
from backend.models.online_learning import OnlineLearningOrchestrator
from pathlib import Path

# Create orchestrator
orchestrator = OnlineLearningOrchestrator(
    model_type="churn",
    update_frequency="daily",
    min_samples_per_update=1000,
    drift_threshold=0.1,
)

# Initialize from batch model
orchestrator.initialize_from_batch_model(
    batch_model_path=Path("models/churn/champion.pkl"),
    feature_names=feature_names,
)

# Daily update job
def daily_update_job():
    # Get new data since last update
    X_new, y_new = get_new_data_since_last_update()
    
    # Check for drift
    drift_score = calculate_drift(X_new)
    
    # Update if needed
    result = orchestrator.update(
        X=X_new,
        y=y_new,
        drift_score=drift_score,
    )
    
    if result["updated"]:
        print(f"Model updated: {result['reason']}")
        print(f"Samples: {result['samples']}")
    else:
        print(f"No update: {result['reason']}")
```

### 3. Integration with Drift Detection

```python
from backend.monitoring import DriftMonitor
from backend.models.online_learning import OnlineLearningOrchestrator

# Drift monitor
drift_monitor = DriftMonitor(
    reference_data=reference_df,
    feature_names=feature_names,
)

# Online learner
orchestrator = OnlineLearningOrchestrator(
    model_type="churn",
    drift_threshold=0.15,  # PSI threshold
)

# Daily monitoring + update
def daily_monitoring_and_update():
    # Get new data
    current_data = get_todays_data()
    
    # Detect drift
    drift_report = drift_monitor.detect_drift(current_data)
    
    # Calculate max PSI
    max_psi = max([
        alert["psi"] 
        for alert in drift_report["alerts"] 
        if "psi" in alert
    ], default=0)
    
    # Update if drift detected
    if max_psi > 0.15:
        print(f"⚠️  Drift detected (PSI={max_psi:.3f})")
        
        # Incremental update to adapt
        X_new, y_new = prepare_data(current_data)
        result = orchestrator.update(
            X=X_new,
            y=y_new,
            drift_score=max_psi,
        )
        
        print(f"Model updated with {result['samples']} samples")
```

---

## Algorithms Supported

### 1. Churn Prediction (Classification)
**Algorithm:** SGDClassifier with log loss (Logistic Regression)

```python
learner = OnlineLearner(model_type="churn")
# Uses SGDClassifier internally
# - Loss: log_loss (logistic regression)
# - Learning rate: constant
# - Warm start: enabled
```

### 2. CLV Prediction (Regression)
**Algorithm:** SGDRegressor with squared error

```python
learner = OnlineLearner(model_type="clv")
# Uses SGDRegressor internally
# - Loss: squared_error
# - Learning rate: constant
# - Warm start: enabled
```

---

## Best Practices

### 1. Start with Batch Model
Always start with a batch-trained model on historical data, then use online learning for updates.

```python
# Week 0: Batch training
batch_model = train_batch_model(historical_data)

# Week 1+: Online updates
learner = OnlineLearner(model_type="churn")
# Initialize from batch model (future enhancement)
```

### 2. Regular Full Retraining
Online learning can drift over time. Reset with full retraining periodically.

```python
# Every 4 weeks: Full retrain
if weeks_since_full_retrain >= 4:
    batch_model = train_batch_model(all_data)
    learner = OnlineLearner(model_type="churn")
    # Restart online learning
```

### 3. Monitor Performance
Track online model performance vs batch model.

```python
# Compare online vs batch
online_auc = evaluate_model(online_learner, X_test, y_test)
batch_auc = evaluate_model(batch_model, X_test, y_test)

if online_auc < batch_auc - 0.05:
    print("⚠️  Online model degraded, trigger full retrain")
```

### 4. Learning Rate Tuning
Adjust learning rate based on drift severity.

```python
if drift_score > 0.3:
    # High drift - faster learning
    learner.learning_rate = 0.05
elif drift_score > 0.15:
    # Medium drift - normal learning
    learner.learning_rate = 0.01
else:
    # Low drift - slower learning
    learner.learning_rate = 0.001
```

---

## Advantages

### 1. Cost Efficiency ✅
- No need to retrain on full dataset
- Faster training (minutes vs hours)
- Lower compute costs

### 2. Freshness ✅
- Models stay up-to-date
- Adapt to recent trends
- Respond to drift quickly

### 3. Scalability ✅
- Can update daily or hourly
- Handles streaming data
- Low memory footprint

### 4. Continuous Improvement ✅
- Always learning from new data
- No waiting for weekly retraining
- Gradual adaptation

---

## Limitations

### 1. Catastrophic Forgetting ⚠️
Online models can "forget" old patterns.

**Solution:** Periodic full retraining (every 4-8 weeks)

### 2. Limited Algorithms ⚠️
Not all algorithms support online learning.

**Supported:**
- ✅ Logistic Regression (SGDClassifier)
- ✅ Linear Regression (SGDRegressor)
- ✅ Neural Networks (with partial_fit)

**Not Supported:**
- ❌ Random Forests
- ❌ Gradient Boosting (XGBoost, LightGBM)
- ❌ K-Means (for segmentation)

### 3. Hyperparameter Drift ⚠️
Learning rate may need adjustment over time.

**Solution:** Monitor and tune learning rate

---

## Production Deployment

### Daily Update CronJob

```yaml
# k8s/cronjobs/online-learning.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: online-learning-update
  namespace: ml-platform
spec:
  # Run daily at 4 AM UTC
  schedule: "0 4 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: online-update
            image: customer-intelligence-training:latest
            command: ["python", "-m", "backend.models.online_learning_job"]
            env:
            - name: MODEL_TYPE
              value: "churn"
            - name: UPDATE_FREQUENCY
              value: "daily"
```

### Monitoring Dashboard

Track online learning metrics:
- Samples processed per day
- Model performance over time
- Drift scores
- Update frequency
- Learning rate adjustments

---

## Example: Complete Workflow

```python
from backend.models.online_learning import OnlineLearningOrchestrator
from backend.monitoring import DriftMonitor
from pathlib import Path

# 1. Initialize (one-time)
orchestrator = OnlineLearningOrchestrator(
    model_type="churn",
    update_frequency="daily",
    min_samples_per_update=1000,
    drift_threshold=0.15,
)

orchestrator.initialize_from_batch_model(
    batch_model_path=Path("models/churn/champion.pkl"),
    feature_names=feature_names,
)

# 2. Daily update job
def daily_job():
    # Get yesterday's data with labels
    df = get_yesterdays_data_with_labels()
    
    # Prepare features
    X = df[feature_names].values
    y = df['churned'].values
    
    # Detect drift
    drift_monitor = DriftMonitor(reference_data=reference_df)
    drift_report = drift_monitor.detect_drift(df)
    
    max_psi = max([
        alert.get("psi", 0) 
        for alert in drift_report["alerts"]
    ], default=0)
    
    # Update model
    result = orchestrator.update(
        X=X,
        y=y,
        drift_score=max_psi,
    )
    
    # Log results
    print(f"Update result: {result}")
    
    # Evaluate
    if result["updated"]:
        X_test, y_test = get_test_data()
        predictions = orchestrator.learner.predict(X_test)
        auc = roc_auc_score(y_test, predictions)
        print(f"Updated model AUC: {auc:.3f}")

# 3. Run daily
daily_job()
```

---

## Summary

**Online Learning** is now integrated into your Customer Intelligence Platform!

### Key Features:
- ✅ Incremental updates (partial_fit)
- ✅ Drift-aware learning
- ✅ Automatic model versioning
- ✅ Performance tracking
- ✅ Cost-efficient updates

### When to Use:
- Daily/hourly updates needed
- Drift is gradual
- Cost is a concern
- Freshness is important

### When NOT to Use:
- Need complex models (GBM, RF)
- Drift is sudden/severe
- Full retraining is cheap
- Accuracy is critical

**This completes your ML platform with both batch and online learning capabilities!** 🚀
