# Runtime Contracts

**Last Updated:** 2026-03-04
**Owner:** Platform Team

---

## Overview

This document defines the runtime contracts between system components — i.e., the guaranteed input/output shapes, behavior, and failure modes at component boundaries.

---

## API ↔ Frontend Contract

### Response Format

All API responses are JSON. Successful responses conform to route-specific Pydantic schemas.

Error responses follow this format:
```json
{
  "error": "ExceptionType",
  "detail": "Human-readable message",
  "path": "/api/route"
}
```

### Pagination Contract

Paginated endpoints (`/api/customers/`) **always** return:
```json
{
  "total": 1234,
  "page": 1,
  "page_size": 50,
  "items": [...]
}
```

### Null / Empty Handling

- Missing numeric fields: `0` (not `null`)
- Missing string fields: `""` or `null` (documented per field)
- Empty dataset responses: `[]` (never `null`)
- Failed API calls: `{ "success": false, "data": [] }` shape preserved

---

## DataLoader ↔ Routes Contract

### `get_customer_snapshot()` Guarantees

| Guarantee | Value |
|-----------|-------|
| Return type | `pd.DataFrame` |
| On missing data | Returns empty `DataFrame` — never raises |
| Column availability | Columns sanitized: NaN → 0, categories → str |
| Caching | LRU cache, invalidated on restart |

### Required Snapshot Columns

The following columns must exist in `customer_snapshot.parquet`:

| Column | Type | Nullable |
|--------|------|---------|
| `customer_id` | int | No |
| `segment_name` | str | No |
| `health_band` | str | No |
| `health_score` | float | No |
| `churn_probability` | float | No |
| `clv_12m` | float | Yes → 0 |
| `investment_priority` | str | No |
| `is_active_30d` | bool | Yes → False |
| `recency_days` | int | Yes → 0 |
| `session_frequency_30d` | float | Yes → 0 |
| `snapshot_date` | date | No |

---

## Batch Pipeline ↔ API Contract

### Output Directory Structure
```
backend/data/
├── snapshots/
│   └── customer_snapshot/
│       └── snapshot_date=YYYY-MM-DD/
│           └── customer_snapshot.parquet
└── outputs/
    └── snapshot_date=YYYY-MM-DD/
        ├── kpis.json
        ├── aggregations.parquet
        ├── distributions.parquet
        ├── migrations.parquet
        └── trends.parquet
```

### Contract Rules
- Pipeline **must not** delete previous snapshot until new one is fully written
- Snapshot date folder is written **atomically** — partial writes are rejected
- API reads the **latest** snapshot date folder; fallback to previous on read failure

---

## Model ↔ Inference Contract

| Contract | Detail |
|----------|--------|
| Output type | Probabilities in `[0.0, 1.0]` |
| Segmentation output | Integer cluster labels mapped to named segments |
| CLV output | Non-negative float in currency units |
| Model version | Always recorded in output with `model_version` field |
| Missing prediction | `null` score with `prediction_available: false` flag |
