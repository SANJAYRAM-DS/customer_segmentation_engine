#PAGE 1
# 1. Load model outputs
base_df = customer_predictions_df

# 2. Materialize system table
from outputs.materialize import materialize_customer_risk_scores
risk_df = materialize_customer_risk_scores(base_df)

# 3. Serve Page 1
from outputs.page_1_overview import page_1_outputs
page_1 = page_1_outputs(risk_df)
