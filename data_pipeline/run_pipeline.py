# =============================================================================
# PIPELINE EXECUTOR
# =============================================================================

from pathlib import Path
from datetime import datetime as dt
import json
import os
import shutil
import gc
from memory_profiler import profile

from data_pipeline.shared.table_configs import TABLE_CONFIG
from data_pipeline.shared.run_context import RunContext
from data_pipeline.stages.validate_raw_data import apply_validation
from data_pipeline.stages.apply_raw_data_contract import apply_contract
from data_pipeline.stages.assemble_validated_events import assemble_events
from data_pipeline.stages.build_bi_semantic_layer import build_semantic_layer
from data_pipeline.stages.publish_lifecycle import execute_publish_lifecycle

from data_pipeline.shared.storage_adapter import (
    download_raw_snapshot,
    upload_run_artifacts,
    upload_contracted_directory,
    download_contracted_datasets,
)


# ------------------------------------------------------------
# SUPPORTING UTILITIES
# ------------------------------------------------------------

# REPLACED with GCS adapter

# def snapshot_raw_storage(run_context: RunContext) -> None:
#     """
#     Creates a run-scoped raw snapshot by copying the entire source raw
#     directory into the run context.
#     """

#     source = run_context.storage_raw_path
#     destination = run_context.raw_snapshot_path

#     if not source.exists():
#         raise FileNotFoundError(f"Raw source path not found: {source}")

#     copytree(source, destination, dirs_exist_ok=True)


def persist_json(path: Path, payload: dict) -> None:
    """
    Writes the stage report to a JSON file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


def initiliaze_metadata(run_context: RunContext) -> None:
    """
    Run metadata initializer.

    Creates the run-scoped metadata record at pipeline start to
    establish lifecycle tracking and publish eligibility state.
    """

    run_dt = dt.strptime(run_context.run_id[:15], "%Y%m%dT%H%M%S")

    payload = {
        "run_id": run_context.run_id,
        "pipeline_version": "v3.1",
        "status": "RUNNING",
        "started_at": dt.utcnow().isoformat(),
        "run_year": run_dt.year,
        "run_month": run_dt.month,
        "run_week_of_month": (run_dt.day - 1) // 7 + 1,
        "completed_at": None,
        "published": False,
    }

    persist_json(run_context.metadata_path, payload)


def finalize_metadata(run_context: RunContext, status: str) -> None:
    """
    Run metadata finalizer.

    Updates the run metadata record with terminal status and
    completion timestamp.
    """

    if not run_context.metadata_path.exists():
        raise RuntimeError("metadata.json missing during finalization")

    with open(run_context.metadata_path, "r") as file:
        payload = json.load(file)

    payload["status"] = status
    payload["completed_at"] = dt.utcnow().isoformat()

    if status == "SUCCESS":
        payload["published"] = True

    else:
        payload["published"] = False

    persist_json(run_context.metadata_path, payload)


# ------------------------------------------------------------
# PIPELINE ORCHESTRATOR
# ------------------------------------------------------------


@profile
def main() -> None:
    """
    Pipeline orchestrator.

    Execution order:
    1. Snapshot raw data
    2. Initialize metadata (RUNNING)
    3. Validation → halt on errors
    4. Contract enforcement
        - Apply role-driven repair
        - Propagate invalid order_ids (parent → child)
    5. Re-validation → halt on errors/warnings
    6. Assemble event table
    7. Build semantic layer
    8. Pre-publish integrity gate
    9. Promote version
    10. Finalize metadata (SUCCESS)
    11. Atomic activation

    Guarantees:
    - Deterministic forward-only execution
    - Single run isolation
    - Only Contract stage mutates data
    - Activation occurs only after SUCCESS

    Failure behavior:
    - Any stage failure → metadata FAILED → process exits
    """

    run_context = RunContext.create()

    # Clean any leftover from previous run
    # if os.path.exists(run_context.workspace_root):
    #     shutil.rmtree(run_context.workspace_root, ignore_errors=True)

    try:

        download_raw_snapshot(run_context)
        initiliaze_metadata(run_context)

        # ------------------------------------------------------------
        # VALIDATIONS AND CONTRACT APPLICATION STAGES
        # ------------------------------------------------------------

        # INITIAL VALIDATION
        validation_initial = apply_validation(run_context)

        persist_json(
            path=run_context.logs_path / "validation_initial.json",
            payload={"run_id": run_context.run_id, "report": validation_initial},
        )

        if validation_initial["errors"]:
            raise RuntimeError("Stage failure: Initial Validation")

        report_contract = []

        # Accumulates set of invalid order_ids and valid order_ids, and apply to child tables.
        invalid_order_ids = set()
        valid_order_ids = set()

        # NOTE: TABLE_CONFIG order must list parent first before its children.
        for table_name in TABLE_CONFIG:

            # CONTRACT APPLICATION
            contract, new_invalid_ids, new_valid_ids = apply_contract(
                run_context,
                table_name,
                invalid_order_ids,
                valid_order_ids,
            )

            # Cascade invalid ids in parent to child
            invalid_order_ids |= new_invalid_ids

            # Remove ghost ids on child tables
            if new_valid_ids:
                valid_order_ids = new_valid_ids

            report_contract.append(contract)

        persist_json(
            path=run_context.logs_path / "contract_report.json",
            payload={"run_id": run_context.run_id, "report": report_contract},
        )

        # VALIDATE CONTRACT OUPUT
        validation_post_contract = apply_validation(
            run_context,
            base_path=run_context.contracted_path,
        )

        persist_json(
            path=run_context.logs_path / "validation_post_contract.json",
            payload={"run_id": run_context.run_id, "report": validation_post_contract},
        )

        if validation_post_contract["errors"] or validation_post_contract["warnings"]:
            raise RuntimeError("Stage failure: Post Contract Validation")

        # ------------------------------------------------------------
        # ASSEMBLE EVENTS, SEMANTIC MODELING, PUBLISHING STAGES
        # ------------------------------------------------------------

        # Persist contracted datasets
        upload_contracted_directory(run_context)

        # Clear RAM memory from previous stages
        if os.path.exists(run_context.raw_snapshot_path):
            shutil.rmtree(run_context.raw_snapshot_path)
            shutil.rmtree(run_context.contracted_path)
            gc.collect()

        # Recreate path and download contracted dataset from storage
        run_context.contracted_path.mkdir(parents=True, exist_ok=True)
        download_contracted_datasets(run_context)

        # ASSEMBLE EVENTS
        assemble = assemble_events(run_context)

        persist_json(
            path=run_context.logs_path / "assemble_report.json",
            payload={"run_id": run_context.run_id, "report": assemble},
        )

        if assemble["status"] == "failed":
            raise RuntimeError("Stage failure: Assemble Events")

        # Clear RAM memory after merging
        if os.path.exists(run_context.contracted_path):
            shutil.rmtree(run_context.contracted_path)
            gc.collect()

        # SEMANTIC MODELING
        semantic = build_semantic_layer(run_context)

        persist_json(
            path=run_context.logs_path / "semantic_report.json",
            payload={"run_id": run_context.run_id, "report": semantic},
        )

        if semantic["status"] == "failed":
            raise RuntimeError("Stage failure: Semantic Modeling")

        # PRE-PUBLISHING VALIDATION
        publish = execute_publish_lifecycle(run_context)

        persist_json(
            path=run_context.logs_path / "publish_report.json",
            payload={"run_id": run_context.run_id, "report": publish},
        )

        if publish["status"] == "failed":
            raise RuntimeError("Stage failure: Semantic Publishing")

        finalize_metadata(run_context, status="SUCCESS")

    except Exception:

        finalize_metadata(run_context, status="FAILED")
        raise

    # PERSIST RUN ARTIFACTS PASS or FAIL
    finally:
        upload_run_artifacts(run_context)

        # Clean RAM memory for next run
        if os.path.exists(run_context.workspace_root):
            shutil.rmtree(run_context.workspace_root)
            gc.collect()


if __name__ == "__main__":
    main()

# =============================================================================
# END OF SCRIPT
# =============================================================================
