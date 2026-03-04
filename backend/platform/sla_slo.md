# SLA / SLO Definitions

**Last Updated:** 2026-03-04
**Owner:** Platform Team

---

## Service Level Objectives (SLOs)

| Signal | Metric | Target | Measurement Window |
|--------|--------|--------|-------------------|
| **API Availability** | Uptime | ≥ 99.5% | 30-day rolling |
| **API Response Time** | p50 latency | ≤ 200ms | Per request |
| **API Response Time** | p99 latency | ≤ 1000ms | Per request |
| **Data Freshness** | Snapshot age | ≤ 24 hours | Continuous |
| **Prediction Coverage** | % customers scored | ≥ 95% | Per batch run |
| **Batch Pipeline Runtime** | End-to-end | ≤ 2 hours | Per run |

---

## Service Level Agreements (SLAs)

| Consumer | SLA | Notes |
|----------|-----|-------|
| Internal dashboards | 99.0% uptime | Business hours priority |
| External API consumers | 99.5% uptime | Full SLA applies |
| Batch pipeline outputs | T+2h freshness | Outputs available within 2h of scheduled run |

---

## Error Budgets

| SLO | Monthly Budget (minutes) | Burn Rate Alert |
|-----|--------------------------|-----------------|
| 99.5% availability | 216 min/month | Alert if > 50% consumed in 7 days |
| p99 latency ≤ 1s | ≤ 5% of requests exceed | Alert if > 2% in any 1-hour window |

---

## Incident Response Targets

| Severity | Response Time | Resolution Time |
|----------|--------------|-----------------|
| P0 — Service Down | 5 minutes | 1 hour |
| P1 — Degraded | 15 minutes | 4 hours |
| P2 — Minor Issue | 1 hour | 24 hours |
| P3 — Cosmetic | Next business day | 1 week |

---

## Exclusions

- Scheduled maintenance windows (communicated 24h in advance)
- Force majeure events
- Issues caused by upstream data source failures (outside system boundary)
