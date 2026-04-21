# =============================================================================
# UNIT TESTS FOR contract_logic.py and contract_executor.py
# =============================================================================

import polars as pl
import pytest
from data_pipeline.shared.run_context import RunContext
from data_pipeline.contract.contract_executor import apply_contract
from data_pipeline.contract.contract_logic import (
    deduplicate_exact_events,
    remove_unparsable_timestamps,
    remove_impossible_timestamps,
    remove_rows_with_null_constraint,
    cascade_drop_by_order_id,
    enforce_parent_reference,
    enforce_schema,
)

# ------------------------------------------------------------
# FIXTURES
# ------------------------------------------------------------


@pytest.fixture
def sample_orders_df():
    return pl.DataFrame(
        {
            "order_id": ["o1", "o2", "o3"],
            "customer_id": ["c1", "c2", "c3"],
            "order_status": ["delivered", "delivered", "delivered"],
            "order_purchase_timestamp": [
                "2026-03-25 10:00:00",
                "2026-03-25 11:00:00",
                "2026-03-25 12:00:00",
            ],
            "order_approved_at": [
                "2026-03-25 10:05:00",
                "2026-03-25 11:05:00",
                "2026-03-25 12:05:00",
            ],
            "order_delivered_timestamp": [
                "2026-03-27 10:00:00",
                "2026-03-27 11:00:00",
                "2026-03-27 12:00:00",
            ],
            "order_estimated_delivery_date": ["2026-03-28", "2026-03-28", "2026-03-28"],
        }
    )


@pytest.fixture
def sample_payments_df():
    return pl.DataFrame(
        {
            "order_id": ["o1", "o2", "o3"],
            "payment_sequential": [1, 1, 1],
            "payment_value": [100.0, 200.0, 300.0],
        }
    )


# ------------------------------------------------------------
# LOGIC UNIT TESTS
# ------------------------------------------------------------


def test_deduplicate_exact_events():
    df = pl.DataFrame({"a": [1, 1, 2], "b": [2, 2, 3]})
    filtered, removed = deduplicate_exact_events(df)
    assert len(filtered) == 2
    assert removed == 1


def test_remove_unparsable_timestamps():
    df = pl.DataFrame(
        {
            "order_id": ["o1", "o2"],
            "order_purchase_timestamp": ["2026-01-01 10:00:00", "garbage"],
            "order_approved_at": ["2026-01-01 10:05:00", "2026-01-01 10:05:00"],
            "order_delivered_timestamp": ["2026-01-02 10:00:00", "2026-01-02 10:00:00"],
            "order_estimated_delivery_date": ["2026-01-03", "2026-01-03"],
        }
    )
    filtered, removed, inv_ids = remove_unparsable_timestamps(df)
    assert len(filtered) == 1
    assert removed == 1
    assert "o2" in inv_ids


def test_remove_impossible_timestamps():
    # Delivered before purchase
    df = pl.DataFrame(
        {
            "order_id": ["o1"],
            "order_purchase_timestamp": ["2026-03-25 10:00:00"],
            "order_approved_at": ["2026-03-25 10:05:00"],
            "order_delivered_timestamp": ["2026-03-24 10:00:00"],
        }
    )
    filtered, removed, inv_ids = remove_impossible_timestamps(df)
    assert len(filtered) == 0
    assert removed == 1
    assert "o1" in inv_ids


def test_cascade_drop_by_order_id():
    df = pl.DataFrame({"order_id": ["o1", "o2", "o3"]})
    invalid = {"o1", "o3"}

    filtered, removed = cascade_drop_by_order_id(df, invalid)

    assert len(filtered) == 1
    assert removed == 2
    assert filtered[0, "order_id"] == "o2"


def test_enforce_parent_reference():
    df = pl.DataFrame({"order_id": ["o1", "o2", "ghost"]})
    valid = {"o1", "o2"}

    filtered, removed = enforce_parent_reference(df, valid)

    assert len(filtered) == 2
    assert removed == 1
    assert "ghost" not in filtered["order_id"].to_list()


def test_remove_rows_with_null_constraint():
    df = pl.DataFrame({"order_id": ["o1", "o2", None, "o4"]})
    non_nullable = ["order_id"]

    filtered, removed, invalid_ids = remove_rows_with_null_constraint(df, non_nullable)

    assert len(filtered) == 3
    assert len(invalid_ids) == 1
    assert removed == 1


def test_enforce_schema():
    df = pl.DataFrame(
        {
            "order_id": ["o1", "o2", "o3"],
            "customer_id": ["c1", "c2", "c3"],
            "extra_col": [1, 2, 3],
            "state": ["ST", "NT", "NK"],
        }
    )
    req_col = ["order_id", "customer_id", "state"]
    dtype = {"order_id": pl.String, "customer_id": pl.String, "state": pl.Categorical}

    filtered, removed = enforce_schema(df, req_col, dtype)

    assert len(filtered) == 3
    assert removed == 1
    assert filtered["order_id"].dtype == pl.String
    assert filtered["state"].dtype == pl.Categorical


# ------------------------------------------------------------
# EXECUTOR INTEGRATION TESTS
# ------------------------------------------------------------


def test_apply_contract_orders_success(tmp_path, sample_orders_df):
    run_context = RunContext.create(base=tmp_path, storage=tmp_path / "storage")
    run_context.initialize_directories()

    suffix = "2026_03_25"
    sample_orders_df.write_csv(
        run_context.raw_snapshot_path / f"df_orders_{suffix}.csv"
    )

    # New 3-tuple return signature
    report, inv_ids, val_ids = apply_contract(run_context, "df_orders")

    assert report["status"] == "success"
    assert report["final_rows"] == 3
    assert len(val_ids) == 3
    assert not inv_ids
    assert (run_context.contracted_path / f"df_orders_{suffix}.parquet").exists()


def test_apply_contract_cascade_and_valid_propagation(
    tmp_path, sample_orders_df, sample_payments_df
):
    run_context = RunContext.create(base=tmp_path, storage=tmp_path / "storage")
    run_context.initialize_directories()

    # o1: valid, o2: unparsable, o3: impossible
    sample_orders_df = sample_orders_df.with_columns(
        pl.when(pl.col("order_id") == "o2")
        .then(pl.lit("garbage"))
        .otherwise(pl.col("order_purchase_timestamp"))
        .alias("order_purchase_timestamp"),
        pl.when(pl.col("order_id") == "o3")
        .then(pl.lit("2026-01-01 00:00:00"))
        .otherwise(pl.col("order_delivered_timestamp"))
        .alias("order_delivered_timestamp"),
    )

    suffix = "2026_03_25"
    sample_orders_df.write_csv(
        run_context.raw_snapshot_path / f"df_orders_{suffix}.csv"
    )
    sample_payments_df.write_csv(
        run_context.raw_snapshot_path / f"df_payments_{suffix}.csv"
    )

    # 1. Process Orders
    rep_o, inv_o, val_o = apply_contract(run_context, "df_orders")
    assert "o2" in inv_o  # unparsable
    assert "o3" in inv_o  # impossible
    assert "o1" in val_o  # only one valid

    # 2. Process Payments (should cascade drop o2, o3 and only keep o1)
    rep_p, inv_p, val_p = apply_contract(
        run_context, "df_payments", invalid_order_ids=inv_o, valid_order_ids=val_o
    )

    assert rep_p["removed_cascade_rows"] == 2  # o2 and o3 dropped
    assert rep_p["final_rows"] == 1
    assert "o1" in set(
        pl.read_parquet(run_context.contracted_path / f"df_payments_{suffix}.parquet")[
            "order_id"
        ].to_list()
    )


def test_apply_contract_unknown_table(tmp_path):
    run_context = RunContext.create(base=tmp_path)
    run_context.initialize_directories()

    report, inv, val = apply_contract(run_context, "non_existent")
    assert report["status"] == "failed"
    assert "Unknown table" in report["errors"][0]
