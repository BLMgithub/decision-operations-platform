# Semantic Modeling Stage

**Files:**
* **Executor:** [`semantic_executor.py`](../../data_pipeline/semantic/semantic_executor.py)
* **Logic:** [`semantic_logic.py`](../../data_pipeline/semantic/semantic_logic.py)
* **Registry:** [`registry.py`](../../data_pipeline/semantic/registry.py)

**Role:** Analytical Module Construction.

![semantic-stage-diagram](/assets/diagrams/05-semantic-stage-diagram.png)

## System Contract

**Purpose**

Transforms the unified analytical table into entity-centric Fact and Dimension modules. This stage performs temporal aggregations, calculates long-term performance metrics, and applies integer mapping for analytical modeling.

**Invariants**

* **Temporal Grain:** Fact tables are aggregated at the ISO-Week level (`W-MON`).
* **Entity Grain:** 
    * **Fact Tables:** One row per `(Entity_ID, order_year_week)`.
    * **Dimension Tables:** One row per `Entity_ID`.
* **Technical Enforcement:** Output tables are subject to a schema enforcement pass that ensures matching columns and data types as defined in the `SEMANTIC_MODULES` registry.

**Inputs**
* `run_context`: Path resolution and lineage tracking.
* `assembled_events`: Unified analytical source from the Assembly stage.
* `SEMANTIC_MODULES`: Registry defining builders, tables, grains, and schemas.

**Outputs**
* **Semantic Report:** Status of module and table processing.
* **Semantic Modules:** Fact and Dimension tables for Sellers, Customers, and Products in Parquet format.

## Execution Workflow

The executor manages the semantic build through a registry-driven loop:

1.  **Source Verification:** Loads the `assembled_events` dataset. If the source is missing, the stage fails.
2.  **Module Initialization:** Iterates through the `SEMANTIC_MODULES` registry.
3.  **Builder Execution:** Dispatches data to module-specific builder functions.
4.  **Enforcement:** For each table produced, the executor:
    * Verifies grain uniqueness.
    * Projects the defined schema and removes internal helper columns.
    * Enforces data types.
5.  **Export:** Saves artifacts into module-specific subdirectories using a date-partitioned convention.
    *   **Optimization:** Uses `sink_parquet` for streaming exports to maintain a low memory footprint.
6.  **Memory Management:** Triggers garbage collection after each table export to clear intermediate memory.

## Optimization & Resource Management

* **Integer Keys:** Builders use pre-mapped `UInt32/UInt64` keys for grouping operations to reduce memory overhead compared to string-based joins.
* **Aggregated Data Types:** Aggregation results are downcast to smaller types (e.g., `Int16`, `Float32`) within the `agg()` block to reduce the size of the result set.
* **Type Casting:** Durations, counts, and year attributes are cast to `Int16` to reduce row width.
* **Streaming Export:** Employs `sink_parquet()` to stream results directly to storage.

## Boundaries

| This component | This component does NOT |
| :--- | :--- |
| Performs multi-level aggregations. | Filter malformed data (handled in prior stages). |
| Derives entity-level attributes. | Resolve join cardinality issues. |
| Aligns metrics to the ISO Week grain. | Mutate the "Assembled Events" source. |
| Uses integer keys for grouping. | Manage physical publishing or pointer logic. |
| Organizes data into Fact/Dimension modules. | Perform cross-module joins. |

## Failure & Severity Model

### System Failures
* **Missing Source:** Failure to load the input dataset results in an immediate stage failure.
* **Handled Exceptions:** Errors during building or processing are caught, logged to the report, and the stage is marked as failed.
* **Registry Mismatch:** The executor raises an error if a builder returns a table not defined in the registry.

### Data Findings
* **Schema Violation:** If a required column is missing from a builder's output, the enforcement step raises an error that is caught and logged.
