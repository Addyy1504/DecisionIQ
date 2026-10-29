import pandas as pd
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)

from backend.db import engine


# =========================================================
# LOAD DATA
# =========================================================

def load_return_data():
    query = """
    SELECT
        order_item_id,
        order_id,
        customer_id,
        order_date,
        product_id,
        category,
        subcategory,
        quantity,
        unit_price,
        discount_pct,
        discounted_sales,
        is_returned
    FROM vw_order_item_metrics
    WHERE order_status <> 'Cancelled'
    """

    df = pd.read_sql(query, engine)

    df["order_date"] = pd.to_datetime(
        df["order_date"]
    )

    df["is_returned"] = (
        df["is_returned"]
        .astype(int)
    )

    return df


# =========================================================
# BASE FEATURES
# =========================================================

def add_base_features(df):
    df = df.copy()

    df["order_month"] = (
        df["order_date"].dt.month
    )

    df["order_day_of_week"] = (
        df["order_date"].dt.dayofweek
    )

    df["order_quarter"] = (
        df["order_date"].dt.quarter
    )

    df["item_value"] = (
        df["quantity"]
        * df["unit_price"]
    )

    return df


# =========================================================
# TEMPORAL SPLIT
# =========================================================

def temporal_split(df):
    df = (
        df.sort_values(
            [
                "order_date",
                "order_id",
                "order_item_id",
            ]
        )
        .reset_index(drop=True)
    )

    split_index = int(
        len(df) * 0.80
    )

    train_df = (
        df.iloc[:split_index]
        .copy()
    )

    test_df = (
        df.iloc[split_index:]
        .copy()
    )

    return train_df, test_df


# =========================================================
# GLOBAL HISTORICAL RETURN RATE
# Training rows only use earlier dates.
# =========================================================

def add_training_global_history(df):
    df = df.copy()

    daily = (
        df.groupby(
            "order_date",
            as_index=False,
        )
        .agg(
            daily_items=(
                "order_item_id",
                "count",
            ),
            daily_returns=(
                "is_returned",
                "sum",
            ),
        )
        .sort_values(
            "order_date"
        )
    )

    daily[
        "global_prev_items"
    ] = (
        daily["daily_items"]
        .cumsum()
        .shift(1)
    )

    daily[
        "global_prev_returns"
    ] = (
        daily["daily_returns"]
        .cumsum()
        .shift(1)
    )

    daily[
        "global_hist_return_rate"
    ] = (
        daily["global_prev_returns"]
        / daily["global_prev_items"]
    )

    df = df.merge(
        daily[
            [
                "order_date",
                "global_hist_return_rate",
            ]
        ],
        on="order_date",
        how="left",
    )

    df[
        "global_hist_return_rate"
    ] = (
        df[
            "global_hist_return_rate"
        ]
        .fillna(0)
    )

    return df


# =========================================================
# CUSTOMER HISTORY — TRAIN
# =========================================================

def add_training_customer_history(df):
    df = df.copy()

    daily = (
        df.groupby(
            [
                "customer_id",
                "order_date",
            ],
            as_index=False,
        )
        .agg(
            daily_orders=(
                "order_id",
                "nunique",
            ),
            daily_items=(
                "order_item_id",
                "count",
            ),
            daily_returns=(
                "is_returned",
                "sum",
            ),
            daily_spend=(
                "discounted_sales",
                "sum",
            ),
        )
        .sort_values(
            [
                "customer_id",
                "order_date",
            ]
        )
    )

    group = daily.groupby(
        "customer_id"
    )

    daily[
        "customer_prev_orders"
    ] = group[
        "daily_orders"
    ].transform(
        lambda s: (
            s.cumsum().shift(1)
        )
    )

    daily[
        "customer_prev_items"
    ] = group[
        "daily_items"
    ].transform(
        lambda s: (
            s.cumsum().shift(1)
        )
    )

    daily[
        "customer_prev_returns"
    ] = group[
        "daily_returns"
    ].transform(
        lambda s: (
            s.cumsum().shift(1)
        )
    )

    daily[
        "customer_prev_spend"
    ] = group[
        "daily_spend"
    ].transform(
        lambda s: (
            s.cumsum().shift(1)
        )
    )

    daily[
        "previous_order_date"
    ] = group[
        "order_date"
    ].shift(1)

    daily[
        "days_since_previous_order"
    ] = (
        daily["order_date"]
        - daily["previous_order_date"]
    ).dt.days

    daily[
        "customer_hist_return_rate"
    ] = (
        daily[
            "customer_prev_returns"
        ]
        / daily[
            "customer_prev_items"
        ]
    )

    columns = [
        "customer_id",
        "order_date",
        "customer_prev_orders",
        "customer_prev_items",
        "customer_prev_returns",
        "customer_prev_spend",
        "days_since_previous_order",
        "customer_hist_return_rate",
    ]

    df = df.merge(
        daily[columns],
        on=[
            "customer_id",
            "order_date",
        ],
        how="left",
    )

    return df


# =========================================================
# ENTITY RETURN HISTORY — TRAIN
# Product / Category
# =========================================================

def add_training_entity_history(
    df,
    entity_column,
    output_column,
):
    df = df.copy()

    daily = (
        df.groupby(
            [
                entity_column,
                "order_date",
            ],
            as_index=False,
        )
        .agg(
            daily_items=(
                "order_item_id",
                "count",
            ),
            daily_returns=(
                "is_returned",
                "sum",
            ),
        )
        .sort_values(
            [
                entity_column,
                "order_date",
            ]
        )
    )

    group = daily.groupby(
        entity_column
    )

    daily["prev_items"] = (
        group["daily_items"]
        .transform(
            lambda s: (
                s.cumsum().shift(1)
            )
        )
    )

    daily["prev_returns"] = (
        group["daily_returns"]
        .transform(
            lambda s: (
                s.cumsum().shift(1)
            )
        )
    )

    daily[output_column] = (
        daily["prev_returns"]
        / daily["prev_items"]
    )

    df = df.merge(
        daily[
            [
                entity_column,
                "order_date",
                output_column,
            ]
        ],
        on=[
            entity_column,
            "order_date",
        ],
        how="left",
    )

    return df


# =========================================================
# BUILD TRAIN FEATURES
# =========================================================

def build_training_history_features(
    train_df,
):
    train_df = (
        add_training_global_history(
            train_df
        )
    )

    train_df = (
        add_training_customer_history(
            train_df
        )
    )

    train_df = (
        add_training_entity_history(
            train_df,
            "product_id",
            "product_hist_return_rate",
        )
    )

    train_df = (
        add_training_entity_history(
            train_df,
            "category",
            "category_hist_return_rate",
        )
    )

    # First-time customers/products/categories
    # fall back to historical global information.

    train_df[
        "customer_hist_return_rate"
    ] = (
        train_df[
            "customer_hist_return_rate"
        ]
        .fillna(
            train_df[
                "global_hist_return_rate"
            ]
        )
    )

    train_df[
        "product_hist_return_rate"
    ] = (
        train_df[
            "product_hist_return_rate"
        ]
        .fillna(
            train_df[
                "global_hist_return_rate"
            ]
        )
    )

    train_df[
        "category_hist_return_rate"
    ] = (
        train_df[
            "category_hist_return_rate"
        ]
        .fillna(
            train_df[
                "global_hist_return_rate"
            ]
        )
    )

    fill_zero = [
        "customer_prev_orders",
        "customer_prev_items",
        "customer_prev_returns",
        "customer_prev_spend",
        "days_since_previous_order",
    ]

    train_df[
        fill_zero
    ] = (
        train_df[
            fill_zero
        ]
        .fillna(0)
    )

    return train_df


# =========================================================
# BUILD TEST FEATURES USING TRAIN ONLY
# This keeps the holdout clean.
# =========================================================

def build_test_history_features(
    train_df,
    test_df,
):
    test_df = test_df.copy()

    global_return_rate = (
        train_df[
            "is_returned"
        ].mean()
    )

    # -------------------------
    # Customer historical data
    # -------------------------

    customer_history = (
        train_df.groupby(
            "customer_id",
            as_index=False,
        )
        .agg(
            customer_prev_orders=(
                "order_id",
                "nunique",
            ),
            customer_prev_items=(
                "order_item_id",
                "count",
            ),
            customer_prev_returns=(
                "is_returned",
                "sum",
            ),
            customer_prev_spend=(
                "discounted_sales",
                "sum",
            ),
            previous_order_date=(
                "order_date",
                "max",
            ),
        )
    )

    customer_history[
        "customer_hist_return_rate"
    ] = (
        customer_history[
            "customer_prev_returns"
        ]
        / customer_history[
            "customer_prev_items"
        ]
    )

    test_df = test_df.merge(
        customer_history,
        on="customer_id",
        how="left",
    )

    test_df[
        "days_since_previous_order"
    ] = (
        test_df["order_date"]
        - test_df[
            "previous_order_date"
        ]
    ).dt.days

    # -------------------------
    # Product historical data
    # -------------------------

    product_history = (
        train_df.groupby(
            "product_id",
            as_index=False,
        )
        .agg(
            product_prev_items=(
                "order_item_id",
                "count",
            ),
            product_prev_returns=(
                "is_returned",
                "sum",
            ),
        )
    )

    product_history[
        "product_hist_return_rate"
    ] = (
        product_history[
            "product_prev_returns"
        ]
        / product_history[
            "product_prev_items"
        ]
    )

    test_df = test_df.merge(
        product_history[
            [
                "product_id",
                "product_hist_return_rate",
            ]
        ],
        on="product_id",
        how="left",
    )

    # -------------------------
    # Category historical data
    # -------------------------

    category_history = (
        train_df.groupby(
            "category",
            as_index=False,
        )
        .agg(
            category_prev_items=(
                "order_item_id",
                "count",
            ),
            category_prev_returns=(
                "is_returned",
                "sum",
            ),
        )
    )

    category_history[
        "category_hist_return_rate"
    ] = (
        category_history[
            "category_prev_returns"
        ]
        / category_history[
            "category_prev_items"
        ]
    )

    test_df = test_df.merge(
        category_history[
            [
                "category",
                "category_hist_return_rate",
            ]
        ],
        on="category",
        how="left",
    )

    # -------------------------
    # Missing / new entities
    # -------------------------

    test_df[
        "customer_hist_return_rate"
    ] = (
        test_df[
            "customer_hist_return_rate"
        ]
        .fillna(
            global_return_rate
        )
    )

    test_df[
        "product_hist_return_rate"
    ] = (
        test_df[
            "product_hist_return_rate"
        ]
        .fillna(
            global_return_rate
        )
    )

    test_df[
        "category_hist_return_rate"
    ] = (
        test_df[
            "category_hist_return_rate"
        ]
        .fillna(
            global_return_rate
        )
    )

    fill_zero = [
        "customer_prev_orders",
        "customer_prev_items",
        "customer_prev_returns",
        "customer_prev_spend",
        "days_since_previous_order",
    ]

    test_df[
        fill_zero
    ] = (
        test_df[
            fill_zero
        ]
        .fillna(0)
    )

    return test_df


# =========================================================
# PREPROCESSOR
# =========================================================

def build_preprocessor():
    categorical_features = [
        "category",
        "subcategory",
    ]

    numerical_features = [
        "quantity",
        "unit_price",
        "discount_pct",
        "item_value",
        "order_month",
        "order_day_of_week",
        "order_quarter",

        # Historical features
        "customer_prev_orders",
        "customer_prev_items",
        "customer_prev_returns",
        "customer_prev_spend",
        "days_since_previous_order",
        "customer_hist_return_rate",
        "product_hist_return_rate",
        "category_hist_return_rate",
    ]

    preprocessor = (
        ColumnTransformer(
            transformers=[
                (
                    "categorical",
                    OneHotEncoder(
                        handle_unknown="ignore"
                    ),
                    categorical_features,
                ),
                (
                    "numeric",
                    StandardScaler(),
                    numerical_features,
                ),
            ]
        )
    )

    return (
        preprocessor,
        categorical_features,
        numerical_features,
    )


# =========================================================
# EVALUATION
# =========================================================

def evaluate_model(
    model,
    X_test,
    y_test,
):
    predictions = (
        model.predict(
            X_test
        )
    )

    probabilities = (
        model.predict_proba(
            X_test
        )[:, 1]
    )

    metrics = {
        "accuracy": float(
            accuracy_score(
                y_test,
                predictions,
            )
        ),
        "precision": float(
            precision_score(
                y_test,
                predictions,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                y_test,
                predictions,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                y_test,
                predictions,
                zero_division=0,
            )
        ),
        "roc_auc": float(
            roc_auc_score(
                y_test,
                probabilities,
            )
        ),
        "confusion_matrix": (
            confusion_matrix(
                y_test,
                predictions,
            ).tolist()
        ),
    }

    return (
        metrics,
        predictions,
        probabilities,
    )


# =========================================================
# FEATURE IMPORTANCE
# =========================================================

def get_feature_importance(
    model,
    model_name,
    top_n=20,
):
    preprocessor = (
        model.named_steps[
            "preprocessor"
        ]
    )

    classifier = (
        model.named_steps[
            "classifier"
        ]
    )

    feature_names = (
        preprocessor
        .get_feature_names_out()
    )

    clean_names = [
        name
        .replace(
            "categorical__",
            "",
        )
        .replace(
            "numeric__",
            "",
        )
        for name in feature_names
    ]

    if (
        model_name
        == "Logistic Regression"
    ):
        coefficients = (
            classifier.coef_[0]
        )

        importance_df = (
            pd.DataFrame(
                {
                    "feature": (
                        clean_names
                    ),
                    "coefficient": (
                        coefficients
                    ),
                    "importance": (
                        np.abs(
                            coefficients
                        )
                    ),
                }
            )
        )

    else:
        importance_df = (
            pd.DataFrame(
                {
                    "feature": (
                        clean_names
                    ),
                    "importance": (
                        classifier
                        .feature_importances_
                    ),
                }
            )
        )

    importance_df = (
        importance_df
        .sort_values(
            "importance",
            ascending=False,
        )
        .head(top_n)
        .reset_index(drop=True)
    )

    return importance_df


# =========================================================
# HIGH-RISK ITEMS
# =========================================================

def create_high_risk_table(
    test_df,
    probabilities,
    limit=100,
):
    result = test_df[
        [
            "order_item_id",
            "order_id",
            "customer_id",
            "order_date",
            "product_id",
            "category",
            "subcategory",
            "quantity",
            "unit_price",
            "discount_pct",
            "customer_prev_orders",
            "customer_hist_return_rate",
            "product_hist_return_rate",
            "category_hist_return_rate",
            "is_returned",
        ]
    ].copy()

    result[
        "return_probability"
    ] = probabilities

    result[
        "return_risk_pct"
    ] = (
        result[
            "return_probability"
        ]
        * 100
    )

    result["risk_level"] = (
        pd.cut(
            result[
                "return_probability"
            ],
            bins=[
                -np.inf,
                0.30,
                0.60,
                np.inf,
            ],
            labels=[
                "Low",
                "Medium",
                "High",
            ],
        )
    )

    result = (
        result.sort_values(
            "return_probability",
            ascending=False,
        )
        .head(limit)
        .reset_index(drop=True)
    )

    result[
        "return_probability"
    ] = (
        result[
            "return_probability"
        ]
        .round(4)
    )

    result[
        "return_risk_pct"
    ] = (
        result[
            "return_risk_pct"
        ]
        .round(2)
    )

    return result


# =========================================================
# MAIN
# =========================================================

def run_return_risk_model():
    df = load_return_data()

    df = add_base_features(
        df
    )

    raw_train, raw_test = (
        temporal_split(
            df
        )
    )

    # Historical features for training
    # only use earlier training dates.
    train_df = (
        build_training_history_features(
            raw_train
        )
    )

    # Test historical return features
    # are built ONLY from the training set.
    test_df = (
        build_test_history_features(
            raw_train,
            raw_test,
        )
    )

    feature_columns = [
        "category",
        "subcategory",

        "quantity",
        "unit_price",
        "discount_pct",
        "item_value",

        "order_month",
        "order_day_of_week",
        "order_quarter",

        "customer_prev_orders",
        "customer_prev_items",
        "customer_prev_returns",
        "customer_prev_spend",
        "days_since_previous_order",

        "customer_hist_return_rate",
        "product_hist_return_rate",
        "category_hist_return_rate",
    ]

    X_train = (
        train_df[
            feature_columns
        ]
    )

    y_train = (
        train_df[
            "is_returned"
        ]
    )

    X_test = (
        test_df[
            feature_columns
        ]
    )

    y_test = (
        test_df[
            "is_returned"
        ]
    )

    # =====================================================
    # LOGISTIC REGRESSION
    # =====================================================

    logistic_preprocessor, _, _ = (
        build_preprocessor()
    )

    logistic_model = Pipeline(
        steps=[
            (
                "preprocessor",
                logistic_preprocessor,
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1500,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )

    logistic_model.fit(
        X_train,
        y_train,
    )

    (
        logistic_metrics,
        _,
        logistic_probabilities,
    ) = evaluate_model(
        logistic_model,
        X_test,
        y_test,
    )

    # =====================================================
    # RANDOM FOREST
    # =====================================================

    rf_preprocessor, _, _ = (
        build_preprocessor()
    )

    random_forest_model = (
        Pipeline(
            steps=[
                (
                    "preprocessor",
                    rf_preprocessor,
                ),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=200,
                        max_depth=14,
                        min_samples_leaf=5,
                        class_weight="balanced",
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        )
    )

    random_forest_model.fit(
        X_train,
        y_train,
    )

    (
        rf_metrics,
        _,
        rf_probabilities,
    ) = evaluate_model(
        random_forest_model,
        X_test,
        y_test,
    )

    # =====================================================
    # BEST MODEL
    # =====================================================

    if (
        logistic_metrics[
            "roc_auc"
        ]
        >= rf_metrics[
            "roc_auc"
        ]
    ):
        best_model_name = (
            "Logistic Regression"
        )

        best_model = (
            logistic_model
        )

        best_metrics = (
            logistic_metrics
        )

        best_probabilities = (
            logistic_probabilities
        )

    else:
        best_model_name = (
            "Random Forest"
        )

        best_model = (
            random_forest_model
        )

        best_metrics = (
            rf_metrics
        )

        best_probabilities = (
            rf_probabilities
        )

    # =====================================================
    # FEATURE IMPORTANCE FOR WINNING MODEL
    # =====================================================

    feature_importance = (
        get_feature_importance(
            best_model,
            best_model_name,
        )
    )

    # =====================================================
    # HIGH-RISK ITEMS
    # =====================================================

    high_risk_items = (
        create_high_risk_table(
            test_df,
            best_probabilities,
        )
    )

    # =====================================================
    # SUMMARY
    # =====================================================

    dataset_summary = {
        "total_rows": int(
            len(df)
        ),
        "train_rows": int(
            len(train_df)
        ),
        "test_rows": int(
            len(test_df)
        ),
        "overall_return_rate_pct": float(
            df[
                "is_returned"
            ].mean()
            * 100
        ),
        "train_return_rate_pct": float(
            y_train.mean()
            * 100
        ),
        "test_return_rate_pct": float(
            y_test.mean()
            * 100
        ),
        "train_start": str(
            train_df[
                "order_date"
            ].min().date()
        ),
        "train_end": str(
            train_df[
                "order_date"
            ].max().date()
        ),
        "test_start": str(
            test_df[
                "order_date"
            ].min().date()
        ),
        "test_end": str(
            test_df[
                "order_date"
            ].max().date()
        ),
    }

    return {
        "dataset_summary": (
            dataset_summary
        ),

        "model_metrics": {
            "Logistic Regression": (
                logistic_metrics
            ),
            "Random Forest": (
                rf_metrics
            ),
        },

        "best_model_name": (
            best_model_name
        ),

        "best_metrics": (
            best_metrics
        ),

        "feature_importance": (
            feature_importance
        ),

        "high_risk_items": (
            high_risk_items
        ),

        "model": (
            best_model
        ),
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":
    result = (
        run_return_risk_model()
    )

    print(
        "\nDATASET SUMMARY"
    )
    print(
        result[
            "dataset_summary"
        ]
    )

    print(
        "\nMODEL METRICS"
    )

    for (
        model_name,
        metrics,
    ) in result[
        "model_metrics"
    ].items():

        print(
            f"\n{model_name}"
        )

        for (
            metric,
            value,
        ) in metrics.items():

            print(
                f"{metric}: {value}"
            )

    print(
        "\nBEST MODEL"
    )
    print(
        result[
            "best_model_name"
        ]
    )

    print(
        "\nBEST MODEL FEATURE IMPORTANCE"
    )
    print(
        result[
            "feature_importance"
        ]
    )

    print(
        "\nTOP HIGH-RISK ITEMS"
    )
    print(
        result[
            "high_risk_items"
        ].head(10)
    )