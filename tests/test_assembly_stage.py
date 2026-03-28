# =============================================================================
# UNIT TESTS FOR assembly_executor.py
# =============================================================================

import pandas as pd
import pytest
from data_pipeline.shared.run_context import RunContext
from data_pipeline.assembly.assembly_logic import log_info, log_error, init_report
from data_pipeline.assembly.assembly_executor import (
    init_stage_report,
    merge_data,
    derive_fields,
    freeze_schema,
    assemble_events,
)
from data_pipeline.shared.modeling_configs import ASSEMBLE_DTYPES
from data_pipeline.assembly.assembly_logic import dimension_references


@pytest.fixture
def empty_report():
    return init_report()


@pytest.fixture
def valid_orders_df():
    return pd.DataFrame(
        {
            "order_id": ["o1", "o2"],
            "customer_id": ["cos1", "cos2"],
            "order_status": ["delivered", "delivered"],
            "order_purchase_timestamp": [
                "2023-01-02 09:00:00",
                "2023-01-10 14:00:00",
            ],
            "order_approved_at": [
                "2023-01-03 09:00:00",
                "2023-01-11 14:00:00",
            ],
            "order_delivered_timestamp": [
                "2023-01-06 09:00:00",
                "2023-01-16 14:00:00",
            ],
            "order_estimated_delivery_date": [
                "2023-01-05",
                "2023-01-15",
            ],
        }
    )


@pytest.fixture
def valid_order_items_df():
    return pd.DataFrame(
        {
            "order_id": ["o1", "o2"],
            "product_id": ["prod1", "prod2"],
            "seller_id": ["seller1", "seller2"],
            "price": [12.3, 45.6],
            "shipping_charges": [1.23, 4.56],
        }
    )


@pytest.fixture
def valid_payments_df():
    return pd.DataFrame(
        {
            "order_id": ["o1", "o2"],
            "payment_sequential": [1, 2],
            "payment_type": ["credit", "cash"],
            "payment_installments": [4, 5],
            "payment_value": [100.1, 50.2],
        }
    )


@pytest.fixture
def valid_customers_df():
    return pd.DataFrame(
        {
            "customer_id": ["cos1", "cos2"],
            "customer_state": ["SP", "RJ"],
        }
    )


@pytest.fixture
def valid_products_df():
    return pd.DataFrame(
        {
            "product_id": ["prod1", "prod2"],
            "product_category_name": ["tech", "home"],
            "product_weight_g": [100.0, 500.0],
        }
    )


@pytest.fixture
def valid_derived_df():
    df = pd.DataFrame(
        {
            "order_id": ["o1", "o2"],
            "seller_id": ["seller1", "seller2"],
            "customer_id": ["cos1", "cos2"],
            "order_revenue": [100.1, 50.2],
            "product_id": ["prod1", "prod2"],
            "order_status": ["delivered", "delivered"],
            "order_purchase_timestamp": [
                "2023-01-02 09:00:00",
                "2023-01-10 14:00:00",
            ],
            "order_approved_at": [
                "2023-01-03 09:00:00",
                "2023-01-11 14:00:00",
            ],
            "order_delivered_timestamp": [
                "2023-01-06 09:00:00",
                "2023-01-16 14:00:00",
            ],
            "order_estimated_delivery_date": [
                "2023-01-05",
                "2023-01-15",
            ],
            "lead_time_days": [3, 5],
            "approval_lag_days": [1, 1],
            "delivery_delay_days": [1, 1],
            "order_date": pd.to_datetime(["2023-01-02", "2023-01-10"]),
            "order_year": [2023, 2023],
            "order_year_week": ["2023-W01", "2023-W02"],
            "run_id": "20230101T120000",
        }
    )
    # Ensure some columns are typed correctly before freeze_schema
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["order_approved_at"] = pd.to_datetime(df["order_approved_at"])
    df["order_delivered_timestamp"] = pd.to_datetime(df["order_delivered_timestamp"])
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df


# =============================================================================
# REPORTING & LOGS
# =============================================================================


def test_init_report_structure():
    report = init_report()
    assert set(report.keys()) == {"status", "errors", "info"}
    assert report["status"] == "success"


def test_init_stage_report_structure():
    report = init_stage_report()
    assert report["status"] == "success"
    assert "steps" in report
    assert "merge_events" in report["steps"]


def test_log_error_appends_only_to_errors(empty_report):
    log_error("test error", empty_report)
    assert empty_report["errors"] == ["test error"]


def test_log_info_appends_only_to_info(empty_report):
    log_info("test info", empty_report)
    assert empty_report["info"] == ["test info"]


# =============================================================================
# MERGING DATA
# =============================================================================


def test_merge_data_preserve_grain(
    valid_orders_df,
    valid_order_items_df,
    valid_payments_df,
):
    result = merge_data(
        {
            "df_orders": valid_orders_df,
            "df_order_items": valid_order_items_df,
            "df_payments": valid_payments_df,
        }
    )
    assert len(result) == 2
    assert result["order_id"].duplicated().any() == False
    assert "order_revenue" in result.columns


def test_merge_detects_cardinality_violation(
    valid_orders_df,
    valid_order_items_df,
):
    # Duplicate item for same order_id
    duplicated_items_df = valid_order_items_df.copy()
    duplicated_items_df.iloc[1] = duplicated_items_df.iloc[0]

    assert (
        duplicated_items_df.iloc[0]["order_id"]
        == duplicated_items_df.iloc[1]["order_id"]
    )

    with pytest.raises(RuntimeError, match="Cardinality violation"):
        merge_data(
            {
                "df_orders": valid_orders_df,
                "df_order_items": duplicated_items_df,
                "df_payments": pd.DataFrame(
                    {"order_id": ["o1", "o2"], "payment_value": [10, 20]}
                ),
            }
        )


# =============================================================================
# DERIVING FIELDS
# =============================================================================


def test_derived_fields_correctness(valid_derived_df):
    source_cols = [
        "order_id",
        "seller_id",
        "product_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_timestamp",
        "order_estimated_delivery_date",
    ]

    source_df = valid_derived_df[source_cols].copy()
    result = derive_fields(source_df, "20230101T120000")

    assert result["lead_time_days"].tolist() == [3, 5]
    assert result["approval_lag_days"].tolist() == [1, 1]
    assert result["delivery_delay_days"].tolist() == [1, 1]
    assert result["run_id"].unique()[0] == "20230101T120000"
    assert "order_year_week" in result.columns


# =============================================================================
# FREEZING SCHEMA
# =============================================================================


def test_freeze_schema_enforces_strict_schema_success(valid_derived_df):
    result = freeze_schema(valid_derived_df)

    for col, expected_dtype in ASSEMBLE_DTYPES.items():
        assert str(result[col].dtype).startswith(str(expected_dtype))


def test_freeze_schema_fails_on_missing_column(valid_derived_df):
    missing_required_column = valid_derived_df.drop(columns="seller_id")
    with pytest.raises(RuntimeError, match="missing required columns"):
        freeze_schema(missing_required_column)


# =============================================================================
# ASSEMBLING DATA
# =============================================================================


def test_assemble_data_success(
    tmp_path,
    valid_orders_df,
    valid_order_items_df,
    valid_payments_df,
    valid_customers_df,
    valid_products_df,
):
    run_id = "20230101T120000"
    run_context = RunContext.create(base=tmp_path, run_id=run_id)
    run_context.initialize_directories()

    # Setup Silver layer
    valid_orders_df.to_parquet(run_context.contracted_path / "df_orders.parquet")
    valid_order_items_df.to_parquet(
        run_context.contracted_path / "df_order_items.parquet"
    )
    valid_payments_df.to_parquet(run_context.contracted_path / "df_payments.parquet")
    valid_customers_df.to_parquet(run_context.contracted_path / "df_customers.parquet")
    valid_products_df.to_parquet(run_context.contracted_path / "df_products.parquet")

    report = assemble_events(run_context)

    assert report["status"] == "success"

    # Check output files
    assert (run_context.assembled_path / "assembled_events_2023_01_01.parquet").exists()
    assert (run_context.assembled_path / "df_customers_2023_01_01.parquet").exists()
    assert (run_context.assembled_path / "df_products_2023_01_01.parquet").exists()


def test_assemble_data_fails_on_missing_column(
    tmp_path,
    valid_orders_df,
    valid_order_items_df,
    valid_payments_df,
):
    run_id = "20230101T120000"
    run_context = RunContext.create(base=tmp_path, run_id=run_id)
    run_context.initialize_directories()

    # Missing seller_id in order_items
    invalid_order_items_df = valid_order_items_df.drop(columns="seller_id")

    valid_orders_df.to_parquet(run_context.contracted_path / "df_orders.parquet")
    invalid_order_items_df.to_parquet(
        run_context.contracted_path / "df_order_items.parquet"
    )
    valid_payments_df.to_parquet(run_context.contracted_path / "df_payments.parquet")

    report = assemble_events(run_context)

    assert report["status"] == "failed"
    assert report["steps"]["freeze_schema"]["status"] == "failed"
    assert any(
        "missing required columns: ['seller_id']" in error
        for error in report["steps"]["freeze_schema"]["errors"]
    )


def test_assemble_data_fails_on_cardinality(
    tmp_path,
    valid_orders_df,
    valid_order_items_df,
):
    run_id = "20230101T120000"
    run_context = RunContext.create(base=tmp_path, run_id=run_id)
    run_context.initialize_directories()

    # Duplicated payments
    duplicated_payments_df = pd.DataFrame(
        {
            "order_id": ["o1", "o1"],
            "payment_value": [100.1, 100.1],
        }
    )

    valid_orders_df.to_parquet(run_context.contracted_path / "df_orders.parquet")
    valid_order_items_df.to_parquet(
        run_context.contracted_path / "df_order_items.parquet"
    )
    duplicated_payments_df.to_parquet(
        run_context.contracted_path / "df_payments.parquet"
    )

    report = assemble_events(run_context)

    assert report["status"] == "failed"
    assert report["steps"]["merge_events"]["status"] == "failed"
    assert any(
        "Cardinality violation" in error
        for error in report["steps"]["merge_events"]["errors"]
    )


# =============================================================================
# DIMENSION EXTRACTION
# =============================================================================


def test_dimension_references_uniqueness():
    df = pd.DataFrame({"id": ["1", "1", "2"], "val": ["a", "a", "b"]})

    # This should work and drop duplicates
    result = dimension_references(df, "test", ["id"], ["id", "val"])
    assert len(result) == 2

    # If duplicates persist (e.g. same ID different values, but logic says drop_duplicates on subset pk)
    # Actually dimension_references uses drop_duplicates(subset=primary_key)
    # and then checks if duplicated.any().
    # So it should never fail unless something is very wrong with pandas.

    df_conflict = pd.DataFrame({"id": ["1", "1"], "val": ["a", "b"]})
    # drop_duplicates(subset=['id']) will keep the first row.
    result = dimension_references(df_conflict, "test", ["id"], ["id", "val"])
    assert len(result) == 1


def test_dimension_references_fails_if_cols_missing():
    df = pd.DataFrame({"id": ["1"]})
    with pytest.raises(KeyError):
        dimension_references(df, "test", ["id"], ["id", "missing"])
