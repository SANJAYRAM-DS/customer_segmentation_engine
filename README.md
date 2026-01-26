# Gravity - Customer Intelligence Dashboard

Gravity is a comprehensive Customer Intelligence Platform designed to analyze customer behavior, predict churn, and segment users through advanced analytics.

## Project Structure

- **`backend/`**: A Python FastAPI application providing analytics endpoints, data processing, and ML models.
- **`frontend/`**: A React (Vite) application providing a responsive, interactive dashboard.
- **`data/`**: (Inside backend) Contains the raw parquet data files used for analysis.

## Quick Start

### Backend
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn api.app:app --reload
   ```

### Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

## Deployment

Detailed deployment instructions for Render (Backend) and Vercel (Frontend) can be found in [DEPLOYMENT.md](./DEPLOYMENT.md).

## Features
- **Executive Overview**: High-level KPIs and metrics.
- **Customer Segmentation**: K-Means clustering of customer base.
- **Churn Risk Analysis**: Predictive models for identifying at-risk customers.
- **Customer CLV**: Lifetime value prediction.
- **Interactive Graphs**: Visualizations using Recharts.
