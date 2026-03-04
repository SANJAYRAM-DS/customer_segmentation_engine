# Kill Switch Matrix

**Last Updated:** 2026-03-04
**Owner:** Platform / Security Team

---

## Overview

The kill switch is a lightweight emergency mechanism to disable specific features or entire API surfaces without redeployment. It is controlled via environment variable and optionally via the admin API.

---

## Kill Switch States

| State | Effect | How to Activate |
|-------|--------|----------------|
| `DISABLED` (default) | All features operate normally | `ENABLE_KILL_SWITCH=false` |
| `PARTIAL` | Specific routes/features disabled | Set individual feature flags |
| `FULL` | Entire API returns 503 | `ENABLE_KILL_SWITCH=true` + admin call |

---

## Feature-Level Kill Switches

Controlled via environment variables (set on platform dashboard without redeployment):

| Kill Switch | Env Variable | Default | Effect When `false` |
|-------------|-------------|---------|---------------------|
| Authentication | `ENABLE_AUTHENTICATION` | `false` | All endpoints are public |
| Rate Limiting | `ENABLE_RATE_LIMITING` | `true` | No rate limits enforced |
| Audit Logging | `ENABLE_AUDIT_LOGGING` | `false` | Access not logged |
| Metrics | `ENABLE_METRICS` | `true` | Prometheus endpoint disabled |
| API Docs | `ENABLE_DOCS` | `true` | `/docs` and `/redoc` hidden |
| CORS All Origins | `ENABLE_CORS_ALL` | `false` | NEVER enable in production |

---

## Full Kill Switch Procedure

### Activate (Emergency)
```bash
# Via environment variable (platform dashboard)
ENABLE_KILL_SWITCH=true

# Via admin API (when running)
POST /api/admin/kill-switch/enable
Body: { "reason": "Security incident detected" }
```

### Deactivate
```bash
ENABLE_KILL_SWITCH=false
# or
POST /api/admin/kill-switch/disable
```

---

## Kill Switch Decision Matrix

| Situation | Recommended Action |
|-----------|-------------------|
| Data breach suspected | Full kill switch → rotate secrets → investigate |
| Model producing bad predictions | Disable specific model route; keep health/overview up |
| High traffic spike | Enable rate limiting; scale up |
| Upstream data failure | Let API serve cached snapshot; add `data_stale` warning |
| Authentication compromise | Rotate JWT secret; restart API to invalidate tokens |

---

## Logging Requirements

Every kill switch activation/deactivation must be logged with:
- Timestamp
- Actor (who activated it)
- Reason
- Duration

Logs must be retained for **2 years** per audit policy.
