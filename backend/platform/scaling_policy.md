# Scaling Policy

**Last Updated:** 2026-03-04
**Owner:** Platform Team

---

## Overview

This document defines how the Customer Intelligence API scales in response to load, and the configuration thresholds that govern scaling decisions.

---

## Current Deployment Model

**Model:** Single-instance batch-first API  
**Host:** Render / Hugging Face Spaces (Docker)  
**Scaling type:** Vertical (upgrade instance tier) → Horizontal (replicas)

---

## API Scaling

### Horizontal Scaling Triggers

| Metric | Scale-Up Threshold | Scale-Down Threshold |
|--------|-------------------|---------------------|
| CPU utilization | > 70% for 5 min | < 30% for 15 min |
| Request queue depth | > 50 pending | < 10 pending |
| p99 latency | > 800ms for 5 min | < 200ms for 15 min |

### Configuration

```bash
# Gunicorn workers (set in Procfile / Dockerfile)
WORKERS=4                # Recommended: 2 × CPU cores + 1
WORKER_CLASS=uvicorn.workers.UvicornWorker
TIMEOUT=120
KEEPALIVE=5
```

---

## Batch Pipeline Scaling

| Dataset Size | Recommended Configuration | Est. Runtime |
|-------------|--------------------------|--------------|
| < 10K customers | Single process | < 10 min |
| 10K – 100K customers | Parallel feature engineering | < 30 min |
| > 100K customers | Distributed compute (Spark/Dask) | < 2 hours |

---

## Caching Strategy

- **In-memory loader cache:** `@lru_cache(maxsize=1)` on snapshot — single-instance safe
- **Redis cache:** Available via `REDIS_ENABLED=true` — recommended for multi-instance deployments
- **Cache TTL:** 1 hour for snapshot data, 5 minutes for aggregations
- **Cache invalidation:** On new snapshot date detected

### Multi-Instance Note

> When running multiple API replicas, enable Redis to share snapshot cache.  
> Without Redis, each replica loads its own copy, increasing memory usage proportionally.

---

## Resource Limits

| Resource | Development | Production |
|----------|-------------|-----------|
| RAM | 512 MB | 2 GB minimum |
| CPU | 1 core | 2 cores minimum |
| Disk | 1 GB | 10 GB (for snapshot history) |
| Network | n/a | 100 Mbps |
