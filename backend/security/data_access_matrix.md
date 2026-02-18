# Data Access Control Matrix

**Last Updated:** 2026-02-12  
**Owner:** Security Team  
**Version:** 1.0

---

## Overview

This document defines the data access control matrix for the Customer Intelligence API. It specifies who can access what data and under what conditions.

---

## Access Levels

### 1. Public (No Authentication Required)
- Health check endpoints (`/health`, `/health/ready`, `/health/live`)
- API documentation (`/docs`, `/redoc`) - Development only
- Root endpoint (`/`)

### 2. Authenticated User
- All API endpoints require authentication when `ENABLE_AUTHENTICATION=true`
- Users must provide valid JWT token in Authorization header

### 3. Role-Based Access

| Role | Description | Access Level |
|------|-------------|--------------|
| **viewer** | Read-only access to dashboards and reports | Read customer data, segments, predictions |
| **analyst** | Data analysis and export capabilities | All viewer permissions + export data |
| **admin** | Full system access | All permissions + kill switch, configuration |
| **system** | Automated systems and integrations | API access with API key |

---

## Resource Access Matrix

| Resource | Endpoint | Public | Viewer | Analyst | Admin | System |
|----------|----------|--------|--------|---------|-------|--------|
| **Health Checks** | `/health/*` | ✅ | ✅ | ✅ | ✅ | ✅ |
| **API Docs** | `/docs` | ✅ (dev) | ✅ (dev) | ✅ (dev) | ✅ | ❌ |
| **Overview** | `/api/v1/overview` | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Segments** | `/api/v1/segments` | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Risk Analysis** | `/api/v1/risk` | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Value Analysis** | `/api/v1/value` | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Customer List** | `/api/v1/customers` | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Customer Details** | `/api/v1/customers/{id}` | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Alerts** | `/api/v1/alerts` | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Export Data** | `/api/v1/export/*` | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Kill Switch** | `/api/admin/kill-switch/*` | ❌ | ❌ | ❌ | ✅ | ❌ |

---

## Data Field Access

### Customer Data Fields

| Field | Viewer | Analyst | Admin | Notes |
|-------|--------|---------|-------|-------|
| `customer_id` | ✅ | ✅ | ✅ | Anonymized ID |
| `segment_name` | ✅ | ✅ | ✅ | Segment classification |
| `health_band` | ✅ | ✅ | ✅ | Health status |
| `churn_probability` | ✅ | ✅ | ✅ | Churn risk score |
| `clv_12m` | ✅ | ✅ | ✅ | Customer lifetime value |
| `investment_priority` | ✅ | ✅ | ✅ | Priority classification |
| `email` | ❌ | ❌ | ✅ | PII - Admin only |
| `phone` | ❌ | ❌ | ✅ | PII - Admin only |
| `address` | ❌ | ❌ | ✅ | PII - Admin only |

---

## API Key Access

### System Integration Keys

API keys are used for system-to-system integration:

- **Scope:** Read-only access to prediction endpoints
- **Rate Limits:** Higher limits than user accounts
- **Rotation:** Every 90 days
- **Storage:** Environment variables only, never in code

### API Key Permissions

| Permission | Description | Included |
|------------|-------------|----------|
| `read:customers` | Read customer data | ✅ |
| `read:predictions` | Read predictions | ✅ |
| `read:segments` | Read segments | ✅ |
| `write:customers` | Modify customer data | ❌ |
| `export:data` | Export data | ❌ |
| `admin:*` | Admin operations | ❌ |

---

## Data Sensitivity Classification

### Level 1: Public
- Aggregated statistics
- Health check status
- API version information

### Level 2: Internal
- Customer segments (anonymized)
- Prediction scores
- Aggregated metrics

### Level 3: Confidential
- Individual customer predictions
- Detailed customer profiles
- Business metrics

### Level 4: Restricted (PII)
- Customer email addresses
- Phone numbers
- Physical addresses
- Payment information

---

## Access Control Implementation

### 1. Authentication Methods

```python
# JWT Token (Primary)
Authorization: Bearer <jwt_token>

# API Key (System Integration)
X-API-Key: <api_key>
```

### 2. Token Claims

JWT tokens must include:
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "roles": ["viewer", "analyst"],
  "permissions": ["read:customers", "read:predictions"],
  "exp": 1234567890
}
```

### 3. Role Assignment

Roles are assigned by administrators and stored in the user management system.

---

## Audit Requirements

### Logged Events

All data access must be logged with:
- User ID or API key
- Timestamp
- Resource accessed
- Action performed (read, write, export)
- IP address
- Request ID

### Retention

- Access logs: 90 days
- Security events: 1 year
- Admin actions: 2 years

---

## Compliance

### GDPR Considerations

- Customer data includes PII
- Data access must be logged
- Users have right to access their data
- Data retention policies apply

### Data Minimization

- Only request necessary data
- Limit data exposure based on role
- Anonymize data when possible

---

## Emergency Access

### Break-Glass Procedure

In emergencies, administrators can:
1. Enable kill switch to stop all access
2. Review audit logs
3. Revoke compromised credentials
4. Rotate API keys

### Kill Switch Access

Only administrators can control the kill switch:
```bash
# Enable kill switch
python -m backend.api.middleware.kill_switch enable "Security incident"

# Disable kill switch
python -m backend.api.middleware.kill_switch disable
```

---

## Review and Updates

- **Review Frequency:** Quarterly
- **Update Trigger:** New features, security incidents, compliance changes
- **Approval Required:** Security team + Engineering lead

---

## Contact

For access requests or security concerns:
- **Security Team:** security@example.com
- **On-Call:** Use incident management system
