
import pandas as pd

# -----------------------
# GLOBAL KPIs
# -----------------------

def customer_base_summary(df):
    return {
        "total_customers": len(df),
        "active_customers": (df["segment"] != "Churned").sum(),
        "at_risk_customers": (df["health_band"] == "Critical").sum(),
        "churned_customers": (df["segment"] == "Churned").sum(),
    }


def risk_outputs(df):
    return {
        "avg_churn_probability": round(df["churn_probability"].mean(), 3),
        "at_risk_percentage": round(
            (df["health_band"] == "Critical").mean() * 100, 2
        ),
    }


def value_outputs(df):
    return {
        "avg_clv_12m": round(df["clv_12m"].mean(), 2),
        "median_clv": round(df["clv_12m"].median(), 2),
    }


# -----------------------
# DISTRIBUTIONS
# -----------------------

def health_band_distribution(df):
    dist = df["health_band"].value_counts(normalize=True).reset_index()
    dist.columns = ["health_band", "percentage"]
    dist["percentage"] *= 100
    return dist.to_dict(orient="records")


def investment_priority_distribution(df):
    return (
        df.groupby("investment_priority")
        .agg(
            customer_count=("customer_id", "count"),
            total_future_value=("clv_12m", "sum"),
            avg_churn_risk=("churn_probability", "mean"),
        )
        .reset_index()
        .to_dict(orient="records")
    )


# -----------------------
# PAGE 1 OUTPUT
# -----------------------

def page_1_outputs(df: pd.DataFrame):
    return {
        "customer_base_summary": customer_base_summary(df),
        "risk_outputs": risk_outputs(df),
        "value_outputs": value_outputs(df),
        "health_band_distribution": health_band_distribution(df),
        "investment_priority_distribution": investment_priority_distribution(df),
    }
