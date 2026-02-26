# =============================================================================
# BUILD BI-TOOL SEMANTIC LAYER
# =============================================================================
# - Produce contract-compliant facts and dimensions safe for direct BI consumption
# - Define and lock analytical grains for consistent aggregation and reporting
# - Enforce referential integrity between fact and dimension tables

import pandas as pd
from typing import Dict, List
from data_pipeline.shared.run_context import RunContext
from data_pipeline.shared.raw_loader_exporter import load_logical_table, export_file


# ------------------------------------------------------------
# SEMANTIC REPORT & LOGS
# ------------------------------------------------------------


def init_report():
    return {"status": "success", "errors": [], "info": []}


def log_info(message: str, report: Dict[str, List[str]]) -> None:
    print(f"[INFO] {message}")
    report["info"].append(message)


def log_error(message: str, report: Dict[str, List[str]]) -> None:
    print(f"[ERROR] {message}")
    report["errors"].append(message)


# ------------------------------------------------------------
# SEMANTIC LAYERING AND SCHEMA ENFORCEMENT
# ------------------------------------------------------------


# ------------------------------------------------------------
# BUILD BI SEMANTIC
# ------------------------------------------------------------


def build_semantic_layer(run_context: RunContext) -> Dict:

    report = init_report()

    def info(msg):
        log_info(msg, report)

    def error(msg):
        log_error(msg, report)

    assembled_path = run_context.assembled_path

    df = load_logical_table(
        assembled_path,
        "assembled_events",
        log_info=info,
        log_error=error,
    )

    if df is None or df.empty:
        error("assembled events is empty")
        report["status"] = "failed"

        return report

    fact_seller = pd.DataFrame()
    dim_seller = pd.DataFrame()

    fulfillment_tables = {
        "seller_week_fulfillment_fact.parquet": fact_seller,
        "dim_seller.parquet": dim_seller,
    }

    for table_name, table in fulfillment_tables.items():

        output_path = run_context.semantic_path / table_name

        if not export_file(table, output_path):
            error(f"{table_name}: Export failed")
            report["status"] = "failed"
            break

        info(f"Export success: {table_name} ({len(table)} rows)")

    return report


# =============================================================================
# END OF SCRIPT
# =============================================================================
