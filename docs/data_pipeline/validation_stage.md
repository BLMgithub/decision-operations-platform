# Validation Stage

**Files:** 
* **Executor:** [`validation_executor.py`](../../data_pipeline/validation/validation_executor.py)
* **Logic:** [`validation_logic.py`](../../data_pipeline/validation/validation_logic.py)

**Role:** Structural Data Quality Gatekeeper.

![validation-stage-diagram](/assets/diagrams/02-validation-stage-diagram.png)

## System Contract

**Purpose** 

The validation stage evaluates raw datasets against structural contracts before processing. It identifies schema violations, structural inconsistencies, and referential integrity issues to prevent malformed data from entering the pipeline.

**Invariants** 
* **Read-Only Operation:** This stage is strictly read-only. It does not modify values, remove rows, or cast data types.
* **Resolution Verification:** Verifies that timestamps are normalized to microsecond (us) resolution.
* **Severity Hierarchy:** 
    * `errors`: Fatal structural violations (e.g., missing columns, duplicate Primary Keys).
    * `warnings`: Integrity issues (e.g., orphaned records, chronological anomalies).
* **Sequential Execution:** Base structural validations must pass for a table before role-specific or cross-table validations occur.

**Inputs:** 
* `run_context`: Configuration object for path resolution.
* `TABLE_CONFIG`: Registry defining Primary Keys, Required Columns, and Entity Roles.
* `base_path`: Optional override; defaults to the run-scoped snapshot directory.

**Outputs** 
* **Validation Report:** Standardized dictionary containing `status`, `errors`, `warnings`, and `info`.

## Execution Workflow

The executor coordinates the validation lifecycle through these steps:

1.  **Table Discovery:** Iterates through logical tables registered in `TABLE_CONFIG`.
2.  **Data Loading:** Loads each table as a DataFrame. Logs an error if a table is missing.
3.  **Base Validation:** Checks for required columns, Primary Key uniqueness, and non-nullable constraints using Polars expressions.
4.  **Role-Specific Rules:**
    * `event_fact`: Verifies temporal chronology and microsecond resolution.
    * `transaction_detail`: Performs numeric range checks.
5.  **Cross-Table Integrity:** Evaluates Foreign Key relationships once individual table processing is complete.

## Boundaries

| This component | This component does NOT |
| :--- | :--- |
| Loads tables from the snapshot zone. | Remove rows or filter data. |
| Detects schema and primary key violations. | Correct or impute missing values. |
| Verifies microsecond (us) timestamp resolution. | Deduplicate records. |
| Evaluates temporal chronology. | Perform data type casting. |
| Detects numeric anomalies. | Mutate data state. |
| Produces structured reports. | Halt the pipeline independently. |

## Failure & Severity Model

### System Failures
* **Missing Table:** Logged as a fatal error; the table is marked as unprocessable.
* **Corrupted Data:** Catches file-loading exceptions and logs them as errors.

### Data Validation Findings
* **Status Flags:** Structural violations or integrity issues set the stage status to `failed`. The orchestrator determines whether to proceed based on the run phase.
* **Phase-Based Halting:** 
    * **Initial Validation:** The orchestrator allows the run to continue if only `warnings` are present, delegating cleanup to the Contract Stage.
    * **Post-Contract Revalidation:** Any remaining `warnings` are treated as fatal errors to prevent downstream corruption.
* **Contextual Dependencies:** Cross-table validation is skipped and logged as `info` if a required parent table is missing.
