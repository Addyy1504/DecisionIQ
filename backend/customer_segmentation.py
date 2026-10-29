import pandas as pd

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from backend.db import engine


def load_rfm_data():
    query = """
    SELECT
        customer_id,
        MAX(order_date) AS last_order_date,
        COUNT(DISTINCT order_id) AS frequency,
        SUM(net_revenue) AS monetary
    FROM vw_order_item_metrics
    WHERE order_status <> 'Cancelled'
    GROUP BY customer_id
    """

    df = pd.read_sql(query, engine)

    df["last_order_date"] = pd.to_datetime(
        df["last_order_date"]
    )

    reference_date = (
        df["last_order_date"].max()
        + pd.Timedelta(days=1)
    )

    df["recency"] = (
        reference_date
        - df["last_order_date"]
    ).dt.days

    return df[
        [
            "customer_id",
            "recency",
            "frequency",
            "monetary",
        ]
    ]


def find_best_k(features):
    scores = {}

    for k in range(2, 7):
        model = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10,
        )

        labels = model.fit_predict(
            features
        )

        scores[k] = silhouette_score(
            features,
            labels,
        )

    best_k = max(
        scores,
        key=scores.get,
    )

    return best_k, scores


def assign_business_labels(
    df,
    cluster_profile,
):
    segment_labels = {}

    for _, row in cluster_profile.iterrows():
        cluster = int(row["cluster"])

        if (
            row["avg_recency"] > 250
            and row["avg_frequency"] < 3
        ):
            label = "At Risk"

        elif (
            row["avg_frequency"] >= 5
            and row["avg_monetary"] >= 500000
        ):
            label = "High-Value Loyal"

        else:
            label = "Regular Customers"

        segment_labels[cluster] = label

    df["segment"] = (
        df["cluster"]
        .map(segment_labels)
    )

    cluster_profile["segment"] = (
        cluster_profile["cluster"]
        .map(segment_labels)
    )

    return (
        df,
        cluster_profile,
        segment_labels,
    )


def calculate_segment_value(df):
    total_monetary = df["monetary"].sum()

    segment_value = (
        df.groupby(
            [
                "cluster",
                "segment",
            ]
        )
        .agg(
            customers=(
                "customer_id",
                "count",
            ),
            total_monetary=(
                "monetary",
                "sum",
            ),
            avg_monetary=(
                "monetary",
                "mean",
            ),
        )
        .reset_index()
    )

    segment_value[
        "value_share_pct"
    ] = (
        segment_value[
            "total_monetary"
        ]
        / total_monetary
        * 100
    )

    return segment_value


def run_customer_segmentation():
    df = load_rfm_data()

    feature_columns = [
        "recency",
        "frequency",
        "monetary",
    ]

    scaler = StandardScaler()

    scaled_features = (
        scaler.fit_transform(
            df[feature_columns]
        )
    )

    best_k, silhouette_scores = (
        find_best_k(
            scaled_features
        )
    )

    model = KMeans(
        n_clusters=best_k,
        random_state=42,
        n_init=10,
    )

    df["cluster"] = (
        model.fit_predict(
            scaled_features
        )
    )

    cluster_profile = (
        df.groupby("cluster")
        .agg(
            customers=(
                "customer_id",
                "count",
            ),
            avg_recency=(
                "recency",
                "mean",
            ),
            avg_frequency=(
                "frequency",
                "mean",
            ),
            avg_monetary=(
                "monetary",
                "mean",
            ),
        )
        .reset_index()
    )

    (
        df,
        cluster_profile,
        segment_labels,
    ) = assign_business_labels(
        df,
        cluster_profile,
    )

    segment_value = (
        calculate_segment_value(
            df
        )
    )

    return {
        "best_k": best_k,
        "silhouette_scores": silhouette_scores,
        "customer_segments": df,
        "cluster_profile": cluster_profile,
        "segment_labels": segment_labels,
        "segment_value": segment_value,
    }


def get_segment_customers(
    segment,
    limit=100,
):
    result = run_customer_segmentation()

    df = result["customer_segments"].copy()

    valid_segments = set(
        df["segment"].dropna().unique()
    )

    if segment not in valid_segments:
        raise ValueError(
            f"Unknown segment: {segment}"
        )

    limit = max(
        1,
        min(int(limit), 15000)
    )

    customers = (
        df[df["segment"] == segment]
        .sort_values(
            ["monetary", "frequency"],
            ascending=[False, False],
        )
        .head(limit)
        [
            [
                "customer_id",
                "segment",
                "recency",
                "frequency",
                "monetary",
            ]
        ]
        .copy()
    )

    customers["monetary"] = (
        customers["monetary"]
        .astype(float)
        .round(2)
    )

    return customers


if __name__ == "__main__":
    result = run_customer_segmentation()

    print("\nBest K:")
    print(result["best_k"])

    print("\nSilhouette Scores:")
    print(result["silhouette_scores"])

    print("\nCluster Profiles:")
    print(result["cluster_profile"])

    print("\nSegment Value:")
    print(result["segment_value"])
