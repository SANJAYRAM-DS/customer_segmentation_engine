# Secrets Management Policy

**Last Updated:** 2026-02-12  
**Owner:** Security Team  
**Version:** 1.0

---

## Overview

This document defines the policy and procedures for managing secrets, API keys, credentials, and other sensitive configuration data in the Customer Intelligence API.

---

## Principles

### 1. Never Commit Secrets to Version Control
- ❌ No secrets in code
- ❌ No secrets in configuration files
- ❌ No secrets in comments or documentation
- ✅ Use environment variables
- ✅ Use secret management systems

### 2. Least Privilege Access
- Secrets should only be accessible to systems/users that need them
- Use role-based access control for secret access
- Regularly audit secret access

### 3. Rotation and Expiration
- All secrets must have an expiration date
- Secrets should be rotated regularly
- Compromised secrets must be rotated immediately

### 4. Encryption
- Secrets must be encrypted at rest
- Secrets must be encrypted in transit
- Use strong encryption algorithms (AES-256, RSA-2048+)

---

## Types of Secrets

### 1. Application Secrets

| Secret Type | Example | Rotation Period | Storage |
|-------------|---------|-----------------|---------|
| JWT Secret Key | `SECRET_KEY` | 90 days | Environment variable |
| API Keys | `API_KEY` | 90 days | Environment variable |
| Database Passwords | `DATABASE_PASSWORD` | 90 days | Secret manager |
| Redis Password | `REDIS_PASSWORD` | 90 days | Environment variable |
| Encryption Keys | Data encryption keys | 180 days | Key management service |

### 2. Third-Party Credentials

| Service | Secret | Rotation Period |
|---------|--------|-----------------|
| Sentry | `SENTRY_DSN` | On compromise |
| Email Service | `EMAIL_API_KEY` | 90 days |
| SMS Service | `SMS_API_KEY` | 90 days |
| Cloud Provider | Service account keys | 90 days |

### 3. Development vs Production

| Environment | Secret Strength | Storage Method |
|-------------|----------------|----------------|
| Development | Weak (for testing) | `.env` file (gitignored) |
| Staging | Medium | Environment variables |
| Production | Strong | Secret management system |

---

## Secret Storage

### Development Environment

**Method:** `.env` file (gitignored)

```bash
# .env (NEVER commit this file)
SECRET_KEY=dev-secret-key-change-in-production
API_KEY=dev-api-key
DATABASE_URL=postgresql://localhost/dev_db
```

**Requirements:**
- Must be in `.gitignore`
- Use `.env.example` for template
- Weak secrets are acceptable for local development

### Staging/Production Environment

**Method:** Environment variables or secret management system

**Options:**
1. **Environment Variables** (Simple)
   - Set in deployment platform (Vercel, Heroku, etc.)
   - Not visible in code or logs
   
2. **Secret Management Systems** (Recommended)
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - Google Secret Manager

---

## Secret Generation

### JWT Secret Key

```bash
# Generate strong secret key
openssl rand -hex 32
# Output: 64-character hexadecimal string
```

**Requirements:**
- Minimum 256 bits (32 bytes)
- Cryptographically random
- Unique per environment

### API Keys

```bash
# Generate API key
openssl rand -base64 32
# Output: 44-character base64 string
```

**Requirements:**
- Minimum 256 bits
- Include prefix for identification (e.g., `api_live_...`)
- Unique per client

### Passwords

**Requirements:**
- Minimum 16 characters
- Mix of uppercase, lowercase, numbers, symbols
- Use password manager to generate

---

## Secret Rotation

### Rotation Schedule

| Secret Type | Rotation Frequency | Trigger |
|-------------|-------------------|---------|
| JWT Secret | Every 90 days | Scheduled |
| API Keys | Every 90 days | Scheduled |
| Database Passwords | Every 90 days | Scheduled |
| All Secrets | Immediately | On compromise |

### Rotation Procedure

1. **Generate New Secret**
   ```bash
   openssl rand -hex 32
   ```

2. **Update Secret in Secret Manager**
   - Add new secret with version tag
   - Keep old secret active temporarily

3. **Deploy New Secret**
   - Update environment variables
   - Deploy application with new secret
   - Verify functionality

4. **Deactivate Old Secret**
   - Wait for grace period (24-48 hours)
   - Remove old secret
   - Monitor for errors

5. **Document Rotation**
   - Log rotation date
   - Update secret inventory
   - Notify relevant teams

### Emergency Rotation (Compromise)

If a secret is compromised:

1. **Immediate Actions** (< 5 minutes)
   - Generate new secret
   - Update production immediately
   - Revoke old secret

2. **Investigation** (< 1 hour)
   - Review access logs
   - Identify scope of compromise
   - Check for unauthorized access

3. **Remediation** (< 24 hours)
   - Rotate all related secrets
   - Update security policies
   - Notify affected parties

4. **Post-Mortem** (< 1 week)
   - Document incident
   - Identify root cause
   - Implement preventive measures

---

## Access Control

### Who Can Access Secrets?

| Role | Development | Staging | Production |
|------|-------------|---------|------------|
| Developer | ✅ | ✅ | ❌ |
| DevOps | ✅ | ✅ | ✅ |
| Security Team | ✅ | ✅ | ✅ |
| Admin | ✅ | ✅ | ✅ |

### Access Methods

1. **Environment Variables**
   ```python
   import os
   secret_key = os.getenv("SECRET_KEY")
   ```

2. **Secret Manager (AWS Example)**
   ```python
   import boto3
   client = boto3.client('secretsmanager')
   secret = client.get_secret_value(SecretId='prod/api/secret_key')
   ```

---

## Secret Usage Best Practices

### ✅ DO

- Use environment variables
- Use secret management systems
- Rotate secrets regularly
- Log secret access (not values)
- Use different secrets per environment
- Validate secrets on startup
- Fail fast if secrets are missing

### ❌ DON'T

- Commit secrets to git
- Log secret values
- Share secrets via email/chat
- Hardcode secrets in code
- Use same secret across environments
- Store secrets in plain text files
- Include secrets in error messages

---

## Code Examples

### Loading Secrets Safely

```python
import os
from typing import Optional

def get_secret(key: str, default: Optional[str] = None, required: bool = False) -> str:
    """
    Safely load secret from environment
    
    Args:
        key: Environment variable name
        default: Default value if not found
        required: Raise error if not found
        
    Returns:
        Secret value
        
    Raises:
        ValueError: If required secret is missing
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Required secret '{key}' not found in environment")
    
    return value

# Usage
SECRET_KEY = get_secret("SECRET_KEY", required=True)
API_KEY = get_secret("API_KEY", default="dev-key")
```

### Validating Secrets on Startup

```python
def validate_secrets():
    """Validate all required secrets are present"""
    required_secrets = [
        "SECRET_KEY",
        "DATABASE_URL",
    ]
    
    missing = []
    for secret in required_secrets:
        if not os.getenv(secret):
            missing.append(secret)
    
    if missing:
        raise ValueError(f"Missing required secrets: {', '.join(missing)}")

# Call on startup
validate_secrets()
```

### Never Log Secrets

```python
import logging

logger = logging.getLogger(__name__)

# ❌ BAD - Logs secret value
logger.info(f"Using API key: {api_key}")

# ✅ GOOD - Logs masked value
logger.info(f"Using API key: {api_key[:8]}...")

# ✅ BETTER - Don't log at all
logger.info("API key loaded successfully")
```

---

## Secret Inventory

Maintain an inventory of all secrets:

| Secret Name | Type | Environment | Owner | Last Rotated | Next Rotation |
|-------------|------|-------------|-------|--------------|---------------|
| SECRET_KEY | JWT Key | Production | DevOps | 2026-01-15 | 2026-04-15 |
| API_KEY | API Key | Production | DevOps | 2026-01-15 | 2026-04-15 |
| DATABASE_URL | DB Password | Production | DevOps | 2026-02-01 | 2026-05-01 |
| REDIS_PASSWORD | Redis Password | Production | DevOps | 2026-02-01 | 2026-05-01 |
| SENTRY_DSN | Sentry DSN | Production | DevOps | 2026-01-01 | On compromise |

---

## Incident Response

### If a Secret is Compromised

1. **Detect**
   - Monitor for unusual access patterns
   - Alert on failed authentication attempts
   - Review audit logs regularly

2. **Respond**
   - Follow emergency rotation procedure
   - Enable kill switch if necessary
   - Notify security team

3. **Recover**
   - Rotate all potentially compromised secrets
   - Review and update access controls
   - Monitor for unauthorized access

4. **Learn**
   - Conduct post-mortem
   - Update policies
   - Implement preventive measures

---

## Compliance

### Regulatory Requirements

- **GDPR:** Protect customer data with encryption
- **PCI DSS:** Secure payment-related secrets
- **SOC 2:** Implement access controls and audit logging

### Audit Requirements

- Log all secret access (not values)
- Retain logs for 1 year
- Regular security audits
- Annual penetration testing

---

## Tools and Resources

### Recommended Tools

1. **Secret Generation**
   - `openssl` - Command-line tool
   - `secrets` - Python module
   - Password managers (1Password, LastPass)

2. **Secret Management**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - Google Secret Manager

3. **Secret Scanning**
   - git-secrets
   - truffleHog
   - GitHub secret scanning

### Useful Commands

```bash
# Generate JWT secret
openssl rand -hex 32

# Generate API key
openssl rand -base64 32

# Generate strong password
openssl rand -base64 24

# Check for secrets in git history
git log -p | grep -i "password\|secret\|key"
```

---

## Review and Updates

- **Review Frequency:** Quarterly
- **Update Trigger:** Security incidents, new secrets, policy changes
- **Approval Required:** Security team + Engineering lead

---

## Contact

For secret management questions or incidents:
- **Security Team:** security@example.com
- **DevOps Team:** devops@example.com
- **Emergency:** Use incident management system
