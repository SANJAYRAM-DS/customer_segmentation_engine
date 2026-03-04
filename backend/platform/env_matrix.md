# Environment Matrix

**Last Updated:** 2026-03-04
**Owner:** Platform Team

---

## Overview

This document defines the configuration differences across the three deployment environments: **Development**, **Staging**, and **Production**.

---

## Environment Comparison

| Setting | Development | Staging | Production |
|---------|------------|---------|-----------|
| `ENVIRONMENT` | `development` | `staging` | `production` |
| `DEBUG` | `true` | `false` | `false` |
| `RELOAD` | `true` | `false` | `false` |
| `ENABLE_DOCS` | `true` | `true` | `false` |
| `ENABLE_CORS_ALL` | Optional `true` | `false` | `false` |
| `ENABLE_AUTHENTICATION` | `false` | `true` | `true` |
| `ENABLE_RATE_LIMITING` | Optional | `true` | `true` |
| `ENABLE_AUDIT_LOGGING` | `false` | `true` | `true` |
| `ENABLE_METRICS` | `true` | `true` | `true` |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `WARNING` |
| `LOG_FORMAT` | `text` | `json` | `json` |
| `WORKERS` | `1` | `2` | `4+` |
| `REDIS_ENABLED` | `false` | `true` | `true` |

---

## Secret Strength by Environment

| Secret | Development | Staging | Production |
|--------|------------|---------|-----------|
| `SECRET_KEY` | `dev-secret-key` (weak OK) | Auto-generated 256-bit | Auto-generated 256-bit via secret manager |
| `API_KEY` | `dev-api-key` | Rotated monthly | Rotated every 90 days |
| `DATABASE_URL` | SQLite / local Postgres | Shared staging DB | Production DB (separate credentials) |

---

## Data Paths by Environment

| Path Variable | Development | Staging | Production |
|--------------|------------|---------|-----------|
| `SNAPSHOTS_DIR` | `./backend/data/snapshots` | `/data/snapshots` | `/mnt/data/snapshots` |
| `OUTPUTS_DIR` | `./backend/data/outputs` | `/data/outputs` | `/mnt/data/outputs` |
| `MODELS_DIR` | `./backend/models/model_registry` | `/models` | `/mnt/models` |

---

## CORS Origins by Environment

| Environment | `CORS_ORIGINS` |
|------------|----------------|
| Development | `http://localhost:3000,http://localhost:5173,http://localhost:5174` |
| Staging | `https://staging.yourdomain.com` |
| Production | `https://yourdomain.com,https://www.yourdomain.com` |

> **Never** set `ENABLE_CORS_ALL=true` in staging or production.

---

## Deployment Targets

| Environment | Platform | Config Method |
|------------|---------|---------------|
| Development | Local machine | `.env` file |
| Staging | Render (preview) | Environment variables in dashboard |
| Production | Render / Hugging Face Spaces | Environment variables + secret manager |
