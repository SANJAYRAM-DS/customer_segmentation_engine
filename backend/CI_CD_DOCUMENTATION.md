# CI/CD Pipeline Documentation

## Overview

The Customer Intelligence Platform uses **GitHub Actions** for continuous integration and deployment. The pipeline includes:

- ✅ Code quality checks (linting, formatting)
- ✅ Automated testing with coverage
- ✅ Security scanning
- ✅ Docker image building
- ✅ Automated deployment (staging & production)
- ✅ Model training automation
- ✅ Drift monitoring

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CI/CD PIPELINE FLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Code Push (main/develop)                                    │
│         │                                                     │
│         ▼                                                     │
│  ┌──────────────┐                                            │
│  │   Linting    │ (Black, Flake8, MyPy, Pylint)             │
│  └──────┬───────┘                                            │
│         │                                                     │
│         ├────────┬────────┐                                  │
│         ▼        ▼        ▼                                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                       │
│  │  Tests  │ │Security │ │  Build  │                       │
│  │ (pytest)│ │(Bandit) │ │ Docker  │                       │
│  └────┬────┘ └────┬────┘ └────┬────┘                       │
│       │           │           │                              │
│       └───────────┴───────────┘                              │
│                   │                                           │
│                   ▼                                           │
│         ┌─────────────────┐                                  │
│         │ Deploy Staging  │ (if develop branch)             │
│         └────────┬────────┘                                  │
│                  │                                            │
│                  ▼                                            │
│         ┌─────────────────┐                                  │
│         │Performance Tests│                                  │
│         └────────┬────────┘                                  │
│                  │                                            │
│                  ▼                                            │
│         ┌─────────────────┐                                  │
│         │Deploy Production│ (if main branch)                │
│         └─────────────────┘                                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  SCHEDULED WORKFLOWS                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Weekly (Sunday 1 AM)                                        │
│         │                                                     │
│         ▼                                                     │
│  ┌──────────────┐                                            │
│  │Model Training│ (Churn, CLV, Segmentation)                │
│  └──────────────┘                                            │
│                                                               │
│  Daily (6 AM)                                                │
│         │                                                     │
│         ▼                                                     │
│  ┌──────────────┐                                            │
│  │Drift Monitor │ (Trigger retraining if needed)            │
│  └──────────────┘                                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Workflows

### 1. Main CI/CD Pipeline (`ci-cd.yml`)

**Trigger:** Push to `main` or `develop`, Pull Requests

**Jobs:**

#### Job 1: Lint
- Black (code formatting)
- isort (import sorting)
- Flake8 (linting)
- MyPy (type checking)
- Pylint (code analysis)

#### Job 2: Test
- pytest with coverage
- Upload coverage to Codecov
- Generate test reports

#### Job 3: Security
- Safety (dependency vulnerabilities)
- Bandit (security issues)

#### Job 4: Build
- Build Docker images (API, batch, training, monitoring)
- Push to GitHub Container Registry
- Tag with branch, PR, SHA

#### Job 5: Deploy Staging
- Deploy to Kubernetes (staging namespace)
- Run smoke tests
- **Trigger:** Push to `develop`

#### Job 6: Deploy Production
- Deploy to Kubernetes (production namespace)
- Run smoke tests
- Send Slack notification
- **Trigger:** Push to `main`

#### Job 7: Performance Tests
- Run k6 load tests
- Upload performance results

---

### 2. Model Training Pipeline (`model-training.yml`)

**Trigger:** 
- Weekly (Sunday 1 AM UTC)
- Manual trigger

**Steps:**
1. Download training data
2. Train churn model
3. Train CLV model
4. Train segmentation model
5. Evaluate all models
6. Upload model artifacts
7. Notify completion

---

### 3. Drift Monitoring (`drift-monitoring.yml`)

**Trigger:**
- Daily (6 AM UTC)
- Manual trigger

**Steps:**
1. Download current data
2. Run drift detection
3. Check for critical alerts
4. Trigger retraining if drift detected
5. Upload drift reports
6. Send Slack notification if drift found

---

## Setup Instructions

### 1. GitHub Secrets

Add these secrets to your GitHub repository:

```bash
# Kubernetes
KUBE_CONFIG_STAGING      # Base64-encoded kubeconfig for staging
KUBE_CONFIG_PRODUCTION   # Base64-encoded kubeconfig for production

# Notifications
SLACK_WEBHOOK            # Slack webhook URL for notifications

# Optional
AWS_ACCESS_KEY_ID        # For S3 data access
AWS_SECRET_ACCESS_KEY    # For S3 data access
CODECOV_TOKEN            # For code coverage reporting
```

### 2. Enable GitHub Actions

1. Go to repository Settings → Actions
2. Enable "Allow all actions and reusable workflows"
3. Set workflow permissions to "Read and write permissions"

### 3. Configure Branch Protection

**Main branch:**
- Require pull request reviews
- Require status checks (lint, test, security)
- Require branches to be up to date

**Develop branch:**
- Require status checks
- Allow force pushes (for rebasing)

---

## Local Development

### Run Linting Locally

```bash
# Install dev dependencies
pip install black flake8 isort mypy pylint

# Format code
black backend/
isort backend/

# Check linting
flake8 backend/ --max-line-length=100
mypy backend/ --ignore-missing-imports
```

### Run Tests Locally

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run tests
pytest backend/tests/ --cov=backend --cov-report=html

# View coverage
open htmlcov/index.html
```

### Build Docker Images Locally

```bash
# Build API image
docker build -f backend/docker/api.Dockerfile -t ci-api:local .

# Run locally
docker run -p 8000:8000 ci-api:local
```

---

## Deployment Process

### Staging Deployment (Automatic)

1. Create feature branch from `develop`
2. Make changes
3. Push to GitHub
4. Create PR to `develop`
5. Wait for CI checks to pass
6. Merge PR
7. **Automatic deployment to staging**
8. Smoke tests run automatically

### Production Deployment (Automatic)

1. Create PR from `develop` to `main`
2. Get approval from team
3. Merge PR
4. **Automatic deployment to production**
5. Smoke tests run automatically
6. Slack notification sent

### Manual Deployment

```bash
# Trigger workflow manually
gh workflow run ci-cd.yml --ref main

# Trigger model training
gh workflow run model-training.yml

# Trigger drift monitoring
gh workflow run drift-monitoring.yml
```

---

## Monitoring & Alerts

### Slack Notifications

Notifications are sent for:
- ✅ Production deployments (success/failure)
- ⚠️ Critical drift detected
- ❌ Model training failures
- ❌ CI/CD pipeline failures

### Metrics Tracked

- Test coverage percentage
- Build success rate
- Deployment frequency
- Time to deploy
- Drift detection rate
- Model training duration

---

## Rollback Procedure

### Automatic Rollback

If smoke tests fail after deployment:
```bash
# Rollback is automatic via Kubernetes
kubectl rollout undo deployment/customer-intelligence-api -n ml-platform
```

### Manual Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/customer-intelligence-api -n ml-platform

# Rollback to specific revision
kubectl rollout undo deployment/customer-intelligence-api --to-revision=2 -n ml-platform

# Check rollout history
kubectl rollout history deployment/customer-intelligence-api -n ml-platform
```

---

## Troubleshooting

### Pipeline Fails at Linting

```bash
# Fix formatting
black backend/
isort backend/

# Commit and push
git add .
git commit -m "fix: code formatting"
git push
```

### Pipeline Fails at Tests

```bash
# Run tests locally
pytest backend/tests/ -v

# Fix failing tests
# Commit and push
```

### Pipeline Fails at Security

```bash
# Check security issues
safety check
bandit -r backend/

# Fix vulnerabilities
pip install --upgrade <package>

# Commit and push
```

### Deployment Fails

```bash
# Check pod status
kubectl get pods -n ml-platform

# Check logs
kubectl logs deployment/customer-intelligence-api -n ml-platform

# Describe deployment
kubectl describe deployment/customer-intelligence-api -n ml-platform
```

---

## Best Practices

### 1. Commit Messages

Follow conventional commits:
```
feat: add online learning module
fix: correct CORS configuration
docs: update API documentation
test: add drift detection tests
chore: update dependencies
```

### 2. Pull Requests

- Keep PRs small and focused
- Write descriptive PR descriptions
- Link to related issues
- Wait for CI checks before merging
- Get code review from team member

### 3. Testing

- Write tests for new features
- Maintain >80% code coverage
- Test edge cases
- Add integration tests for critical paths

### 4. Deployment

- Deploy to staging first
- Test thoroughly in staging
- Deploy to production during low-traffic hours
- Monitor metrics after deployment
- Have rollback plan ready

---

## Performance Benchmarks

### CI/CD Pipeline Times

- Linting: ~2 minutes
- Tests: ~5 minutes
- Security: ~3 minutes
- Build: ~10 minutes per image
- Deploy: ~5 minutes
- **Total: ~30 minutes** (with parallel jobs)

### Model Training

- Churn model: ~15 minutes
- CLV model: ~20 minutes
- Segmentation: ~10 minutes
- **Total: ~45 minutes**

---

## Future Enhancements

### Planned Improvements

1. **Automated A/B Testing**
   - Deploy canary with traffic splitting
   - Automated metric comparison
   - Auto-promotion if metrics improve

2. **Advanced Security**
   - Container scanning (Trivy)
   - SAST (Static Application Security Testing)
   - DAST (Dynamic Application Security Testing)

3. **Performance Testing**
   - Automated load testing
   - Latency benchmarks
   - Resource usage profiling

4. **Multi-Environment**
   - Dev, staging, production
   - Environment-specific configs
   - Promotion gates

---

## Summary

The CI/CD pipeline provides:

- ✅ **Automated quality checks** (linting, testing, security)
- ✅ **Automated deployments** (staging & production)
- ✅ **Automated model training** (weekly)
- ✅ **Automated drift monitoring** (daily)
- ✅ **Rollback capability** (instant)
- ✅ **Notifications** (Slack)
- ✅ **Metrics tracking** (coverage, performance)

**This ensures fast, safe, and reliable deployments!** 🚀

---

**Last Updated:** 2026-02-05  
**Maintained By:** ML Engineering Team
