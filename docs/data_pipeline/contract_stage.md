# Data Contract Stage

**Files:**
* **Executor:** [`contract_executor.py`](../../data_pipeline/contract/contract_executor.py)
* **Logic:** [`contract_logic.py`](../../data_pipeline/contract/contract_logic.py)
* **Registrar:** [`id_registrar.py`](../../data_pipeline/contract/id_registrar.py)
* **Registry:** [`registry.py`](../../data_pipeline/contract/registry.py)

**Role:** Structural Enforcement, Subtractive Filtering, and ID Mapping.

![contract-stage-diagram](/assets/diagrams/03-contract-stage-diagram.png)

## System Contract

**Purpose**
Enforces role-based structural rules and referential integrity on raw snapshots. This stage removes non-compliant records, propagates invalidated IDs to maintain integrity across tables, and applies technical schemas through an integer mapping process.

**Invariants**
* **Subtractive Row Logic:** This stage does not modify business values or impute data. Non-compliant rows are removed.
* **Structural Parity:** Files within a logical table's contracted zone share identical schema widths and data types to support concatenation in the Assembly stage.
* **ID Propagation:** If an ID is invalidated (e.g., due to nulls or unparsable dates), that ID is propagated to related tables to ensure a clean cascade removal.
* **Deterministic Mapping:** Resolves and maps UUIDs to `UInt32` integers before table enforcement to prevent join collisions and schema drift.
* **Schema Enforcement:** The final step for every role executes `enforce_schema` to project required columns and cast to defined types.

**Inputs**
* `run_context`: Path resolution for raw snapshots and the contracted zone.
* `table_name`: Logical identifier for role-based rule lookup.
* `master_mappings`: Pre-resolved dictionary of UUID-to-Integer mappings.
* `invalid_order_ids`: IDs from preceding tables to be removed.
* `valid_order_ids`: IDs used to maintain child-parent referential integrity.

**Outputs**
* **Contract Report:** Telemetry including `initial_rows`, `final_rows`, and rule application counts.
* **Invalidated IDs:** IDs identified as non-compliant during the current run.
* **Valid IDs:** Whitelist of parent IDs emitted by the `orders` table.
* **Side Effect:** Writes schema-enforced and integer-mapped Parquet files to the `contracted/` directory.

## Execution Workflow

The Contract stage consists of a global Discovery phase and a table-specific Enforcement phase:

### Phase A: Global Discovery
1. **Scan:** Identifies unique UUIDs across all raw sources in the current run.
2. **Lookup:** Retrieves existing mappings from Cloud Storage.
3. **Generate:** Maps new UUIDs to a continuous integer sequence.
4. **Persist:** Saves new mapping deltas to local disk and synchronizes them to central storage.

### Phase B: Table Enforcement
1. **Load:** Retrieves the raw snapshot from the source zone.
2. **Rule Application:** Executes rules (deduplication, null checks, cascade removals) defined in `ROLE_STEPS`.
3. **Filtering:** Iteratively applies rules and captures IDs triggering violations for `event_fact` roles.
4. **Schema Projection:** Executes `enforce_schema` to project the required columns.
5. **ID Mapping:** Joins the filtered DataFrame against `master_mappings` to attach integer IDs.
6. **Persistence:** Saves the compliant and mapped dataset to the Silver layer.

## Boundaries

| This component | This component does NOT |
| :--- | :--- |
| Identifies UUIDs across raw sources before processing. | Calculate business metrics or aggregates. |
| Removes rows violating structural or temporal rules. | Impute missing values or repair records. |
| Propagates ID invalidations to child tables. | Perform cross-table business joins. |
| Enforces fixed-width schemas. | Alter business definitions or rename columns. |
| Maps UUIDs to UInt32 primitives. | Manage global state across runs. |

## Failure & Severity Model

### System Failures
* **Mapping Failure:** If UUID mappings cannot be resolved, the pipeline halts to prevent corruption.
* **Schema Violation:** Occurs if a required column is missing from the source data during `enforce_schema`.
* **I/O Failure:** Triggered by disk or cloud storage errors during the write phase.

### Data Findings
* **Contract Violations:** Data issues result in row removal and are logged in the report.
* **Referential Integrity:** 
    * **Cascade:** Dropped child records are logged under `removed_cascade_rows`.
    * **Orphans:** Records without parent references are removed and logged under `removed_ghost_orphan_rows`.
