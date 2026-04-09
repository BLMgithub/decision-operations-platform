# =============================================================================
# Semantic Modelinc Stage Logic
# =============================================================================

import polars as pl
from typing import Dict
from data_pipeline.shared.run_context import RunContext
from data_pipeline.shared.loader_exporter import load_historical_table
from data_pipeline.shared.modeling_configs import (
    CUSTOMER_DIM_SCHEMA,
    PRODUCT_DIM_SCHEMA,
)

# ------------------------------------------------------------
# SELLER SEMANTIC BUILDER
# ------------------------------------------------------------


def build_seller_semantic(lf: pl.LazyFrame, run_context: RunContext) -> Dict:
    """
    Constructs the Seller-centric analytical layer from assembled events.

    Contract:
    - Transforms order-grain events into weekly seller performance snapshots.
    - Aggregates metrics including revenue, lead times, and fulfillment lag.

    Optimization Logic:
    - Early Projection: Selects only the subset of columns required for seller
      aggregation to reduce the data volume passed through the streaming engine.
    - Categorical Compression: Casts grouping keys to Categorical to minimize
      the memory footprint of the internal hash tables during streaming aggregation.
    - Narrow Aggregation: Casts counts and sums to Int16/Int16 and revenues to Float32
      immediately within the agg() block to minimize the memory footprint of the result set.

    Invariants:
    - Fact Grain: Strictly 1 row per ('seller_id', 'order_year_week').
    - Dimension Grain: Strictly 1 row per 'seller_id'.
    - Temporal: Aligns all metrics to ISO-week start dates (Monday).
    """

    needed_cols = [
        "seller_id",
        "order_year_week",
        "order_date",
        "order_status",
        "order_id",
        "order_revenue",
        "lead_time_days",
        "delivery_delay_days",
        "approval_lag_days",
        "run_id",
    ]

    lf_filtered = lf.select(needed_cols).with_columns(
        seller_id=pl.col("seller_id").cast(pl.Categorical),
        order_year_week=pl.col("order_year_week").cast(pl.Categorical),
    )

    seller_weekly_fact = (
        lf_filtered.with_columns(
            week_start_date=pl.col("order_date").dt.truncate("1w"),
            is_delivered=pl.col("order_status").eq("delivered"),
            is_cancelled=pl.col("order_status").eq("cancelled"),
        )
        .group_by(["seller_id", "order_year_week"])
        .agg(
            run_id=pl.col("run_id").first().cast(pl.Categorical),
            week_start_date=pl.col("week_start_date").min(),
            weekly_order_count=pl.col("order_id").count().cast(pl.Int16()),
            weekly_delivered_orders=pl.col("is_delivered").sum().cast(pl.Int16()),
            weekly_cancelled_orders=pl.col("is_cancelled").sum().cast(pl.Int16()),
            weekly_revenue=pl.col("order_revenue").sum().cast(pl.Float32()),
            weekly_avg_lead_time=pl.col("lead_time_days").mean().cast(pl.Float32()),
            weekly_total_lead_time=pl.col("lead_time_days").sum().cast(pl.Int16()),
            weekly_avg_delivery_delay=pl.col("delivery_delay_days")
            .mean()
            .cast(pl.Float32()),
            weekly_total_delivery_delay=pl.col("delivery_delay_days")
            .sum()
            .cast(pl.Int16()),
            weekly_avg_approval_lag=pl.col("approval_lag_days")
            .mean()
            .cast(pl.Float32()),
        )
    )

    seller_dim = lf_filtered.group_by("seller_id").agg(
        run_id=pl.col("run_id").first(),
        first_order_date=pl.col("order_date").min(),
        first_order_year_week=pl.col("order_year_week").min(),
    )

    seller_semantic = {
        "seller_weekly_fact": seller_weekly_fact,
        "seller_dim": seller_dim,
    }

    return seller_semantic


# ------------------------------------------------------------
# CUSTOMER SEMANTIC BUILDER
# ------------------------------------------------------------


def build_customer_semantic(lf: pl.LazyFrame, run_context: RunContext) -> Dict:
    """
    Constructs the Customer-centric analytical layer from assembled events.

    Contract:
    - Aggregates consumer behavior metrics into a weekly temporal grain.
    - Calculates lifetime-to-date attributes and first-purchase markers.

    Optimization Logic:
    - Early Projection: Selects only the subset of columns required for customer
      aggregation to reduce the data volume passed through the streaming engine.
    - Categorical Compression: Casts high-cardinality customer_id to Categorical
      to reduce the memory overhead of grouping 36M+ rows.
    - Immediate Dimension Projection: Truncates the dimension table to required
      columns during scan to prevent memory bloat from unused metadata.

    Invariants:
    - Fact Grain: Strictly 1 row per ('customer_id', 'order_year_week').
    - Dimension Grain: Strictly 1 row per 'customer_id'.
    """

    needed_cols = [
        "customer_id",
        "order_year_week",
        "order_date",
        "order_status",
        "order_id",
        "order_revenue",
        "lead_time_days",
        "delivery_delay_days",
        "approval_lag_days",
        "run_id",
    ]

    # Cast grouping keys to Categorical to reduce hash table memory pressure
    lf_filtered = lf.select(needed_cols).with_columns(
        customer_id=pl.col("customer_id").cast(pl.Categorical),
        order_year_week=pl.col("order_year_week").cast(pl.Categorical),
    )

    customer_weekly_fact = (
        lf_filtered.with_columns(
            week_start_date=pl.col("order_date").dt.truncate("1w"),
            is_delivered=pl.col("order_status").eq("delivered"),
            is_cancelled=pl.col("order_status").eq("cancelled"),
        )
        .group_by(["customer_id", "order_year_week"])
        .agg(
            run_id=pl.col("run_id").first().cast(pl.Categorical),
            week_start_date=pl.col("week_start_date").min(),
            weekly_order_count=pl.col("order_id").count().cast(pl.Int16()),
            weekly_delivered_orders=pl.col("is_delivered").sum().cast(pl.Int16()),
            weekly_cancelled_orders=pl.col("is_cancelled").sum().cast(pl.Int16()),
            weekly_revenue=pl.col("order_revenue").sum().cast(pl.Float32()),
            weekly_avg_lead_time=pl.col("lead_time_days").mean().cast(pl.Float32()),
            weekly_total_lead_time=pl.col("lead_time_days").sum().cast(pl.Int16()),
            weekly_avg_delivery_delay=pl.col("delivery_delay_days")
            .mean()
            .cast(pl.Float32()),
            weekly_total_delivery_delay=pl.col("delivery_delay_days")
            .sum()
            .cast(pl.Int16()),
            weekly_avg_approval_lag=pl.col("approval_lag_days")
            .mean()
            .cast(pl.Float32()),
        )
    )

    customer_dim = load_historical_table(
        base_path=run_context.assembled_path, table_name="df_customers"
    ).select([c for c in CUSTOMER_DIM_SCHEMA if c != "run_id"])

    customer_dim = customer_dim.with_columns(
        run_id=pl.lit(run_context.run_id).cast(pl.Categorical)
    )

    customer_semantic = {
        "customer_weekly_fact": customer_weekly_fact,
        "customer_dim": customer_dim,
    }

    return customer_semantic


# ------------------------------------------------------------
# PRODUCT SEMANTIC BUILDER
# ------------------------------------------------------------


def build_product_semantic(lf: pl.LazyFrame, run_context: RunContext) -> Dict:
    """
    Constructs the Product-centric analytical layer from assembled events.

    Contract:
    - Aggregates sales velocity and fulfillment health per product.
    - Merges category metadata with weekly transaction volumes.

    Optimization Logic:
    - Early Projection: Selects only columns required for product aggregation.
    - Categorical Compression: Casts grouping keys to Categorical.
    - Immediate Dimension Projection: Truncates dimension table columns during load.

    Invariants:
    - Fact Grain: Strictly 1 row per ('product_id', 'order_year_week').
    - Dimension Grain: Strictly 1 row per 'product_id'.
    """

    needed_cols = [
        "product_id",
        "order_year_week",
        "order_date",
        "order_status",
        "order_id",
        "order_revenue",
        "lead_time_days",
        "delivery_delay_days",
        "approval_lag_days",
        "run_id",
    ]

    lf_filtered = lf.select(needed_cols).with_columns(
        product_id=pl.col("product_id").cast(pl.Categorical),
        order_year_week=pl.col("order_year_week").cast(pl.Categorical),
    )

    product_weekly_fact = (
        lf_filtered.with_columns(
            week_start_date=pl.col("order_date").dt.truncate("1w"),
            is_delivered=pl.col("order_status").eq("delivered"),
            is_cancelled=pl.col("order_status").eq("cancelled"),
        )
        .group_by(["product_id", "order_year_week"])
        .agg(
            run_id=pl.col("run_id").first().cast(pl.Categorical),
            week_start_date=pl.col("week_start_date").min(),
            weekly_order_count=pl.col("order_id").count().cast(pl.Int16()),
            weekly_delivered_orders=pl.col("is_delivered").sum().cast(pl.Int16()),
            weekly_cancelled_orders=pl.col("is_cancelled").sum().cast(pl.Int16()),
            weekly_revenue=pl.col("order_revenue").sum().cast(pl.Float32()),
            weekly_avg_lead_time=pl.col("lead_time_days").mean().cast(pl.Float32()),
            weekly_total_lead_time=pl.col("lead_time_days").sum().cast(pl.Int16()),
            weekly_avg_delivery_delay=pl.col("delivery_delay_days")
            .mean()
            .cast(pl.Float32()),
            weekly_total_delivery_delay=pl.col("delivery_delay_days")
            .sum()
            .cast(pl.Int16()),
            weekly_avg_approval_lag=pl.col("approval_lag_days")
            .mean()
            .cast(pl.Float32()),
        )
    )

    product_dim = load_historical_table(
        base_path=run_context.assembled_path, table_name="df_products"
    ).select([c for c in PRODUCT_DIM_SCHEMA if c != "run_id"])

    product_dim = product_dim.with_columns(
        run_id=pl.lit(run_context.run_id).cast(pl.Categorical)
    )

    product_semantic = {
        "product_weekly_fact": product_weekly_fact,
        "product_dim": product_dim,
    }

    return product_semantic
