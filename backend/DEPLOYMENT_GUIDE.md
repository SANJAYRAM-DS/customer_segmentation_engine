# 🚀 Backend Deployment Guide

**Last Updated:** 2026-02-14  
**Status:** Production-Ready Infrastructure

---

## 📋 Table of Contents

1. [Quick Start Options](#quick-start-options)
2. [Option 1: Deploy to Render (Easiest)](#option-1-deploy-to-render-easiest)
3. [Option 2: Deploy to Railway](#option-2-deploy-to-railway)
4. [Option 3: Deploy to AWS (Production)](#option-3-deploy-to-aws-production)
5. [Option 4: Deploy to DigitalOcean](#option-4-deploy-to-digitalocean)
6. [Option 5: Deploy with Docker](#option-5-deploy-with-docker)
7. [Option 6: Deploy to Kubernetes](#option-6-deploy-to-kubernetes)
8. [Environment Variables Setup](#environment-variables-setup)
9. [Post-Deployment Checklist](#post-deployment-checklist)

---

## 🎯 Quick Start Options

| Platform | Difficulty | Cost | Best For | Time to Deploy |
|----------|-----------|------|----------|----------------|
| **Render** | ⭐ Easy | Free tier available | Quick demos, MVPs | 5 minutes |
| **Railway** | ⭐ Easy | $5/month | Small projects | 5 minutes |
| **DigitalOcean** | ⭐⭐ Medium | $12/month | Growing apps | 15 minutes |
| **AWS** | ⭐⭐⭐ Advanced | Variable | Production scale | 30 minutes |
| **Docker** | ⭐⭐ Medium | Your server | Self-hosted | 10 minutes |
| **Kubernetes** | ⭐⭐⭐ Advanced | Variable | Enterprise | 30 minutes |

---

## Option 1: Deploy to Render (Easiest) ⭐

**Perfect for:** Quick deployment, free tier, automatic HTTPS

### Step 1: Prepare Your Repository

```bash
# Make sure your code is pushed to GitHub
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### Step 2: Create `render.yaml` in project root

```yaml
# render.yaml
services:
  - type: web
    name: customer-intelligence-api
    env: python
    region: oregon
    plan: free  # or starter ($7/month) for better performance
    buildCommand: pip install -r backend/requirements.txt
    startCommand: uvicorn backend.api.app:app --host 0.0.0.0 --port $PORT --workers 2
    healthCheckPath: /health
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: CORS_ORIGINS
        value: https://your-frontend-domain.com
      - key: SECRET_KEY
        generateValue: true
      - key: LOG_LEVEL
        value: INFO
      - key: WORKERS
        value: 2
```

### Step 3: Deploy on Render

1. Go to [render.com](https://render.com)
2. Sign up/Login with GitHub
3. Click **"New +"** → **"Blueprint"**
4. Connect your repository
5. Render will auto-detect `render.yaml`
6. Click **"Apply"**
7. Wait 3-5 minutes for deployment

### Step 4: Get Your API URL

```
Your API will be available at:
https://customer-intelligence-api.onrender.com
```

### Step 5: Test Deployment

```bash
curl https://customer-intelligence-api.onrender.com/health
```

**✅ Pros:**
- Free tier available
- Automatic HTTPS
- Auto-deploy on git push
- Zero configuration

**❌ Cons:**
- Free tier spins down after 15 min inactivity
- Limited resources on free tier

---

## Option 2: Deploy to Railway ⭐

**Perfect for:** Affordable, fast deployment, good performance

### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
```

### Step 2: Login and Initialize

```bash
railway login
cd e:\ecom
railway init
```

### Step 3: Create `railway.json`

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn backend.api.app:app --host 0.0.0.0 --port $PORT --workers 2",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 4: Create `nixpacks.toml`

```toml
[phases.setup]
nixPkgs = ["python310"]

[phases.install]
cmds = ["pip install -r backend/requirements.txt"]

[start]
cmd = "uvicorn backend.api.app:app --host 0.0.0.0 --port $PORT --workers 2"
```

### Step 5: Deploy

```bash
railway up
```

### Step 6: Set Environment Variables

```bash
railway variables set ENVIRONMENT=production
railway variables set CORS_ORIGINS=https://your-frontend.com
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set LOG_LEVEL=INFO
```

### Step 7: Get Domain

```bash
railway domain
# Or create custom domain in Railway dashboard
```

**✅ Pros:**
- $5/month for 500 hours
- Fast deployment
- Great developer experience
- Built-in metrics

**❌ Cons:**
- No free tier
- Limited to 8GB RAM on starter plan

---

## Option 3: Deploy to AWS (Production) ⭐⭐⭐

**Perfect for:** Production workloads, scalability, enterprise

### Option 3A: AWS Elastic Beanstalk (Easier)

#### Step 1: Install EB CLI

```bash
pip install awsebcli
```

#### Step 2: Initialize Elastic Beanstalk

```bash
cd e:\ecom
eb init -p python-3.10 customer-intelligence-api --region us-east-1
```

#### Step 3: Create `.ebextensions/python.config`

```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: backend.api.app:app
  aws:elasticbeanstalk:application:environment:
    ENVIRONMENT: production
    WORKERS: 4
```

#### Step 4: Create `Procfile`

```
web: uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Step 5: Deploy

```bash
eb create customer-intelligence-env
eb deploy
```

#### Step 6: Set Environment Variables

```bash
eb setenv ENVIRONMENT=production \
  CORS_ORIGINS=https://your-domain.com \
  SECRET_KEY=$(openssl rand -hex 32) \
  LOG_LEVEL=INFO
```

### Option 3B: AWS ECS with Fargate (Advanced)

#### Step 1: Build and Push Docker Image

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repository
aws ecr create-repository --repository-name customer-intelligence-api

# Build image
docker build -f backend/docker/api.Dockerfile -t customer-intelligence-api:latest .

# Tag image
docker tag customer-intelligence-api:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/customer-intelligence-api:latest

# Push image
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/customer-intelligence-api:latest
```

#### Step 2: Create ECS Task Definition

```json
{
  "family": "customer-intelligence-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/customer-intelligence-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "WORKERS",
          "value": "4"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:api-secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/customer-intelligence-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Step 3: Create ECS Service with Load Balancer

```bash
aws ecs create-service \
  --cluster customer-intelligence-cluster \
  --service-name customer-intelligence-api \
  --task-definition customer-intelligence-api:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=api,containerPort=8000"
```

**✅ Pros:**
- Highly scalable
- Enterprise-grade
- Full control
- Integrated AWS services

**❌ Cons:**
- More complex setup
- Higher cost
- Requires AWS knowledge

---

## Option 4: Deploy to DigitalOcean ⭐⭐

**Perfect for:** Simple VPS deployment, good balance of cost/performance

### Step 1: Create Droplet

1. Go to [DigitalOcean](https://digitalocean.com)
2. Create Droplet → Ubuntu 22.04 → $12/month (2GB RAM)
3. Add SSH key

### Step 2: Connect to Server

```bash
ssh root@YOUR_DROPLET_IP
```

### Step 3: Install Dependencies

```bash
# Update system
apt update && apt upgrade -y

# Install Python and dependencies
apt install -y python3.10 python3-pip python3-venv nginx git

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### Step 4: Clone Repository

```bash
cd /var/www
git clone https://github.com/YOUR_USERNAME/customer-segmentation-engine.git
cd customer-segmentation-engine
```

### Step 5: Setup Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Step 6: Create Environment File

```bash
nano .env
# Copy from .env.example and fill in values
```

### Step 7: Create Systemd Service

```bash
nano /etc/systemd/system/customer-intelligence-api.service
```

```ini
[Unit]
Description=Customer Intelligence API
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/customer-segmentation-engine
Environment="PATH=/var/www/customer-segmentation-engine/venv/bin"
EnvironmentFile=/var/www/customer-segmentation-engine/.env
ExecStart=/var/www/customer-segmentation-engine/venv/bin/uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

### Step 8: Setup Nginx Reverse Proxy

```bash
nano /etc/nginx/sites-available/customer-intelligence-api
```

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/customer-intelligence-api /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Step 9: Start Service

```bash
systemctl enable customer-intelligence-api
systemctl start customer-intelligence-api
systemctl status customer-intelligence-api
```

### Step 10: Setup SSL with Let's Encrypt

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d YOUR_DOMAIN
```

**✅ Pros:**
- Full control
- Predictable pricing ($12/month)
- Good performance
- Easy to scale

**❌ Cons:**
- Manual server management
- Need to handle updates
- No auto-scaling

---

## Option 5: Deploy with Docker 🐳

**Perfect for:** Any server with Docker installed

### Step 1: Build Docker Image

```bash
cd e:\ecom
docker build -f backend/docker/api.Dockerfile -t customer-intelligence-api:latest .
```

### Step 2: Create `.env` File

```bash
cp backend/.env.example .env
# Edit .env with your production values
```

### Step 3: Run Container

```bash
docker run -d \
  --name customer-intelligence-api \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  customer-intelligence-api:latest
```

### Step 4: Check Logs

```bash
docker logs -f customer-intelligence-api
```

### Step 5: Test

```bash
curl http://localhost:8000/health
```

### Option: Use Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: backend/docker/api.Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Add Redis for caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

Run with:

```bash
docker-compose up -d
```

---

## Option 6: Deploy to Kubernetes ☸️

**Perfect for:** Enterprise production, high availability

### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or local)
- kubectl configured
- Docker images pushed to registry

### Step 1: Build and Push Images

```bash
# Build
docker build -f backend/docker/api.Dockerfile -t YOUR_REGISTRY/customer-intelligence-api:v1.0.0 .

# Push
docker push YOUR_REGISTRY/customer-intelligence-api:v1.0.0
```

### Step 2: Create Namespace

```bash
kubectl create namespace ml-platform
```

### Step 3: Create Secrets

```bash
# Generate secrets
kubectl create secret generic api-secrets \
  --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
  --from-literal=API_KEY=$(openssl rand -base64 32) \
  -n ml-platform
```

### Step 4: Apply Kubernetes Manifests

```bash
# Apply all configurations
kubectl apply -f backend/k8s/configmaps/ -n ml-platform
kubectl apply -f backend/k8s/deployments/ -n ml-platform
kubectl apply -f backend/k8s/services/ -n ml-platform
kubectl apply -f backend/k8s/cronjobs/ -n ml-platform
```

### Step 5: Check Deployment

```bash
# Check pods
kubectl get pods -n ml-platform

# Check services
kubectl get services -n ml-platform

# View logs
kubectl logs -f deployment/customer-intelligence-api -n ml-platform
```

### Step 6: Get External IP

```bash
kubectl get service customer-intelligence-api -n ml-platform
```

### Step 7: Setup Ingress (Optional)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: customer-intelligence-ingress
  namespace: ml-platform
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - api.yourdomain.com
      secretName: api-tls
  rules:
    - host: api.yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: customer-intelligence-api
                port:
                  number: 80
```

---

## 🔐 Environment Variables Setup

### Required Variables

```bash
# Application
ENVIRONMENT=production
APP_NAME="Customer Intelligence API"
APP_VERSION=1.0.0

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Security (IMPORTANT!)
SECRET_KEY=<generate-with-openssl-rand-hex-32>
CORS_ORIGINS=https://your-frontend-domain.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Generate Secrets

```bash
# Secret key
openssl rand -hex 32

# API key
openssl rand -base64 32

# JWT secret
openssl rand -hex 32
```

---

## ✅ Post-Deployment Checklist

### Immediate (Day 1)

- [ ] Test `/health` endpoint
- [ ] Test `/docs` endpoint (then disable in production)
- [ ] Verify CORS settings
- [ ] Check logs for errors
- [ ] Test all API endpoints
- [ ] Verify environment variables loaded correctly

### Week 1

- [ ] Setup monitoring (Sentry, Prometheus)
- [ ] Configure alerts
- [ ] Setup log aggregation
- [ ] Load testing
- [ ] Security scan
- [ ] Backup strategy

### Ongoing

- [ ] Monitor error rates
- [ ] Monitor response times
- [ ] Monitor resource usage
- [ ] Regular security updates
- [ ] Database backups (if applicable)
- [ ] SSL certificate renewal

---

## 🆘 Troubleshooting

### API Not Starting

```bash
# Check logs
docker logs customer-intelligence-api
# or
kubectl logs -f deployment/customer-intelligence-api -n ml-platform

# Common issues:
# 1. Missing environment variables
# 2. Port already in use
# 3. Import errors (missing dependencies)
```

### CORS Errors

```bash
# Make sure CORS_ORIGINS is set correctly
echo $CORS_ORIGINS

# Should be:
CORS_ORIGINS=https://your-frontend.com,https://www.your-frontend.com
```

### High Memory Usage

```bash
# Reduce workers
WORKERS=2

# Or increase memory limit in Docker/K8s
```

---

## 📞 Support

- **Documentation**: Check `backend/README.md`
- **Issues**: Create GitHub issue
- **Logs**: Always check application logs first

---

**Deployment Guide Version:** 1.0.0  
**Last Updated:** 2026-02-14  
**Next Review:** After first production deployment
