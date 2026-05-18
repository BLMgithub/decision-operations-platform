# Publish Stage

**Files:**
* **Executor:** [`publish_executor.py`](../../data_pipeline/publish/publish_executor.py)
* **Logic:** [`publish_logic.py`](../../data_pipeline/publish/publish_logic.py)

**Role:** Production Promotion and Versioning.

## System Contract

**Purpose**

The publish stage serves as the final deployment mechanism for the pipeline. It transitions validated semantic artifacts into versioned storage and updates a dual-pointer system: a `latest_version.json` manifest for automated systems and BigQuery Authorized Views for BI tools.

**Invariants**
* **Integrity Gates:** Promotion to the production zone is prevented if any table defined in the `SEMANTIC_MODULES` registry is missing or inaccessible.
* **Coordinated Update:** The transition to a new version occurs across both Cloud Storage and BigQuery. The BigQuery View swap ensures that BI tools do not encounter partial data during the file promotion phase.
* **Version Immutability:** Files archived in a `v{run_id}` directory are read-only and are not overwritten by subsequent runs.
* **SQL Decoupling:** Dashboards connect to stable Views (e.g., `published_seller_weekly_fact`) which are redirected to version-specific External Tables.

**Inputs**
* `run_context`: Configuration containing the `run_id` and path settings.
* `SEMANTIC_MODULES`: Registry defining the required artifacts for a successful release.

**Outputs**
* **Publish Report:** Status of integrity checks, file promotions, and pointer updates.
* **Versioned Artifacts:** A new `/published/v{run_id}/` directory containing semantic Fact and Dimension tables.
* **BigQuery Pointers:** Updated External Tables and Authorized Views.
* **Latest Pointer:** Updated `latest_version.json` file in the published zone root.

## Execution Workflow

The executor manages the production release through a four-phase sequence:

1.  **Integrity Gate:** Scans the semantic zone to verify that all expected tables defined in the registry exist.
2.  **Promotion:** Transfers verified artifacts from the run-scoped directory to a permanent versioned path (`/published/v{run_id}`).
3.  **SQL Sync:** Executes DDL commands to create versioned External Tables and redirect the Authorized Views.
4.  **Activation:** Updates the `latest_version.json` file to point to the new version.

## Boundaries

| This component | This component does NOT |
| :--- | :--- |
| Verifies the existence of semantic artifacts. | Re-validate data quality (handled in prior stages). |
| Copies files to the versioned production path. | Perform data transformation or aggregation. |
| Manages BigQuery DDL for tables and views. | Manage historical version cleanup. |
| Updates production pointers (SQL and JSON). | Handle automated rollbacks. |
| Captures publication metadata. | Modify the contents of Parquet files. |

## Failure & Severity Model

### System Failures
* **Storage Access Failure:** If write permissions are missing for the published zone, the lifecycle halts before activation.
* **BigQuery DDL Error:** If the SQL swap fails, the `latest_version.json` is not updated to keep pointers synchronized.
* **I/O Interruptions:** Errors during file transfer result in a failure status, leaving pointers on the previous stable version.
