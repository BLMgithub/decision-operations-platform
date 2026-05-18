# Pipeline Orchestrator

**File:** [`run_pipeline.py`](../../data_pipeline/run_pipeline.py)

**Role:** End-to-End Lifecycle, Resource, and Persistence Manager.

![pipeline-orchestration-diagram](/assets/diagrams/01-pipeline-orchestration-diagram.png)

## System Contract

**Purpose**

The orchestration layer coordinates data movement between cloud storage and local compute, enforces the chronological execution of processing stages, and manages system resource cleanup.

**Invariants**
* **Stage Gating:** Stages execute sequentially. Processing halts if a preceding stage does not return a "SUCCESS" signal.
* **Resource Isolation:** Each execution occurs within an isolated `run_id` workspace.
* **Silver Persistence:** The local `contracted/` directory is transient. Data must synchronize to the authoritative Cloud Silver Store before the local environment is cleared.
* **Resource Cleanup:** The local `workspace_root` is cleared at the end of every lifecycle via `finally` blocks to prevent resource saturation and data contamination.
* **Lineage Tracking:** The `run_id` is propagated through every stage, metadata file, and published artifact to maintain lineage.

**Inputs**
* `RunContext`: Configuration object containing IDs and path mappings.
* **Cloud State**: Raw snapshots and historical Silver deltas stored in Google Cloud Storage.

**Outputs**
* **Operational Telemetry**: `run_metadata.json` and stage-specific reports.
* **Persistent Silver Store**: Validated datasets in the cloud `contract/` directory.
* **Semantic Artifacts**: Fact and Dimension tables in the production zone.
* **System State**: Updated `latest_version.json` pointer in the production zone.

## Execution Workflow

The orchestrator manages the lifecycle through a 13-step sequence:

### Phase I: Environment Initialization
1.  **Resolve**: Instantiates `RunContext` and starts background memory telemetry for benchmarking.
2.  **Hydrate (Raw)**: Synchronizes the raw data snapshot from Cloud Storage to the local workspace.
3.  **Initialize**: Logs run start by creating `run_metadata.json` with a "RUNNING" status.

### Phase II: Processing & Memory Reclamation
4.  **Validate (Raw)**: Verifies raw data snapshots; fails on structural errors.
5.  **Contract Processing**: Executes subtractive filtering and saves results to the local `contracted/` path.
6.  **Gate II (Revalidation)**: Verifies contracted data meets downstream semantic requirements.
7.  **Promote (Silver)**: Synchronizes contracted datasets to Cloud Silver Storage.
8.  **Synchronize (BQ)**: Refreshes BigQuery External Table metadata for immediate visibility.
9.  **Purge (Local)**: Deletes local `raw/` and `contracted/` directories and triggers garbage collection to reclaim RAM before the Assembly stage.
10. **Assemble**: Flattens relational data into a Gold-layer dataset using the BigQuery Storage Read API.
11. **Modeling (Semantic)**: Constructs entity-centric analytical modules.

### Phase III: Activation & Finalization
12. **Publish**: Executes final integrity gates, performs BigQuery View swaps, and updates the atomic pointer (`_latest.json`).
13. **Finalize**: Updates status and duration metadata, uploads reports to Cloud Storage, and clears the local workspace.

## Boundaries

| This component | This component does NOT |
| :--- | :--- |
| Coordinates executor sequencing. | Modify data values or logic. |
| Manages cloud synchronization and BQ caching. | Implement business or aggregation rules. |
| Enforces memory optimization strategies. | Define technical schemas for Fact/Dim tables. |
| Manages resource safety via `finally` blocks. | Direct file-level I/O within stages. |
| Aggregates reports into a run summary. | Perform granular row-level validation. |
| Monitors memory telemetry. | Execute SQL transformations directly. |

## Failure & Severity Model

### System Failures
* **Sync Failure**: If cloud synchronization fails, the pipeline halts to prevent processing with stale or missing data.
* **Stage Failure**: Unhandled exceptions within executors trigger immediate termination to prevent partial data processing.

### Resource Recovery
* **Workspace Purge**: The orchestrator clears the local workspace at completion. This ensures subsequent runs do not encounter residual data from previous executions.

### Telemetry on Failure
* **Log Retention**: The orchestrator attempts to upload available stage reports to cloud storage upon failure to preserve diagnostic data.
