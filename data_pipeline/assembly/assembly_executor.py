# =============================================================================
# Assemble Events Stage Executor
# =============================================================================

import gc
from typing import Dict
from data_pipeline.shared.run_context import RunContext
from data_pipeline.shared.loader_exporter import load_historical_table, export_file
from data_pipeline.assembly.assembly_logic import (
    init_report,
    DIMENSION_REFERENCES,
    dimension_references,
    merge_data,
    derive_fields,
    freeze_schema,
    load_event_table,
    task_wrapper,
    export_path,
)


def init_stage_report():
    return {
        "status": "success",
        "steps": {
            "load_tables": init_report(),
            "merge_events": init_report(),
            "derive_fields": init_report(),
            "freeze_schema": init_report(),
            "dim_reference": init_report(),
            "export": init_report(),
        },
    }


# ------------------------------------------------------------
# EVENT ASSEMBLY ORCHESTRATION
# ------------------------------------------------------------


def orchestrate_event_assembly(run_context: RunContext, report: Dict) -> bool:
    """
    Coordinates the linear transformation pipeline for order-grain events.

    Execution Flow:
    1. Load: Fetch 'orders', 'items', and 'payments'.
    2. Merge: Join into a single row-per-order grain.
    3. Derive: Calculate analytical time-deltas and lineage.
    4. Freeze: Enforce semantic schema and dtypes.
    5. Export: Persist to the assembly zone.

    Memory Management:
    - Explicitly deletes intermediate DataFrames and triggers gc.collect()
      after export to minimize peak memory footprint.

    Failures:
    - Returns False immediately (fail-fast) if any sub-task wrapper fails.
    """

    tables = load_event_table(run_context, report["steps"]["load_tables"])
    if not tables:
        return False

    # Merging data
    ok, df = task_wrapper("merge_events", report, merge_data, tables)
    if not ok:
        return False
    del tables

    # Derive fields
    ok, df = task_wrapper(
        "derive_fields", report, derive_fields, df, run_context.run_id
    )
    if not ok:
        return False

    # Freeze schema
    ok, df = task_wrapper("freeze_schema", report, freeze_schema, df)
    if not ok:
        return False

    # Export Assembled events
    path = export_path(run_context, "assembled_events")
    if not export_file(df, path):
        return False

    gc.collect()
    return True


# ------------------------------------------------------------
# DIMENSION REFERENCE ORCHESTRATION
# ------------------------------------------------------------


def orchestrate_dimension_refs(run_context: RunContext, report: Dict) -> bool:
    """
    Iteratively extracts and exports dimension reference tables.

    Contract:
    - Processes every table defined in the DIMENSION_REFERENCES registry.
    - Performs one-to-one extraction from Silver (contracted) to Gold (assembled).

    Invariants:
    - Fail-Fast: If a single dimension fails to load or validate, the
      entire orchestration terminates and returns False.

    Side Effects:
    - Performs per-iteration memory cleanup (del/gc.collect) to prevent
      accumulation of large dimension frames.
    """

    for table, config in DIMENSION_REFERENCES.items():
        df_raw = load_historical_table(run_context.contracted_path, table)
        if df_raw is None:
            return False

        ok, df_dim = task_wrapper(
            "dim_reference",
            report,
            dimension_references,
            df_raw,
            table,
            config["primary_key"],
            config["required_column"],
        )

        if not ok:
            return False

        # Export
        path = export_path(run_context, table)
        if not export_file(df_dim, path):
            return False

        del df_raw, df_dim
        gc.collect()

    return True


# ------------------------------------------------------------
# DATA ASSEMBLING
# ------------------------------------------------------------


def assemble_events(run_context: RunContext) -> dict:
    """
    Main entry point for the Silver-to-Gold Assembly stage.

    This component coordinates the transformation of normalized relational
    tables into contract-compliant analytical datasets.

    Workflow I: Event Assembly (Order Grain)
    1. Load: Fetches core event tables (Orders, Items, Payments).
    2. Merge: Join datasets with strict 1:1 order_id cardinality enforcement.
    3. Derive: Calculate temporal metrics (lead times) and lineage attributes.
    4. Freeze: Project final schema and enforce strictly defined dtypes.
    5. Export: Persist the unified event table to the Gold zone.

    Workflow II: Dimension Reference Extraction
    1. Iterate: Process Customer and Product registries.
    2. Extract: Select required columns and deduplicate by primary key.
    3. Export: Persist independent reference tables to the Gold zone.

    Operational Guarantees:
    - Grain: Strictly one row per 'order_id' for the event dataset.
    - Failure: Fail-fast; any task failure halts the stage and returns a 'failed' status.
    - Context: Relies on 'run_context' for deterministic path resolution.

    Returns:
        dict: A stage report containing 'status' and step-level execution logs.
    """

    report = init_stage_report()

    if not orchestrate_event_assembly(run_context, report):
        report["status"] = "failed"
        return report

    if not orchestrate_dimension_refs(run_context, report):
        report["status"] = "failed"
        return report

    return report
