def better_churn(new, old):
    return new["pr_auc"] > old["pr_auc"]


def better_clv(new, old):
    return new["rmse"] < old["rmse"]


def better_segmentation(new, old):
    return new["silhouette"] > old["silhouette"]
