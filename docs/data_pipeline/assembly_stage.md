# Assembly Stage

**Files:**
* **Executor:** [`assembly_executor.py`](../../data_pipeline/assembly/assembly_executor.py)
* **Logic:** [`assembly_logic.py`](../../data_pipeline/assembly/assembly_logic.py)

**Role:** Data Integration and Analytical Flattening.

![assembled-stage-diagram](/assets/diagrams/04-assemble-stage-diagram.png)

## System Contract

**Purpose**

Integrates normalized relational tables into a unified analytical dataset and extracts dimension references. This stage enforces cardinality rules, applies integer mapping for memory efficiency, and calculates temporal performance metrics.

**Invariants**
* **Order-ID Grain:** The primary event output maintains a 1:1 grain per `order_id_int`. Cardinality issues trigger a terminal failure.
* **Join Logic:** Orders without corresponding items are removed to maintain integrity.
* **Temporal Calculations:** Lead times and delays are calculated as integer-day durations using UTC timestamps.
* **Reference Uniqueness:** Dimension tables (Customers, Products) are deduplicated by their primary keys.

**Inputs**
* `run_context`: Path resolution for Silver and Gold zones.
* **Source Tables:** `df_orders`, `df_order_items`, `df_payments` from the Silver layer.

**Outputs**
* **Assembly Report:** Status and informational logs for each step.
* **Assembled Events:** Unified analytical table at the order grain.
* **Dimension Refs:** Deduplicated snapshots of customer and product attributes.

## Execution Workflow

The executor manages two distinct workflows:

### Workflow I: Event Assembly
1.  **Load:** Retrieves `orders`, `items`, and `payments` from the Silver zone.
2.  **Merge:** Joins datasets using an inner join for items and a left join for payments.
    *   **Optimization:** Uses integer joins on `UInt32/UInt64` IDs to reduce memory overhead. Pre-aggregates payments and items to ensure a 1:1 grain.
3.  **Derivation:** Calculates fulfillment lead times and extracts ISO-calendar attributes.
    *   **Optimization:** Applies data type casting (e.g., `Int16` for durations, `Categorical` for repetitive strings) and drops intermediate columns to reduce memory footprint.
4.  **Schema Enforcement:** Projects the final `ASSEMBLE_SCHEMA` and casts to `ASSEMBLE_DTYPES`.
    *   **Optimization:** Skips sorting to enable streaming and non-blocking execution.
5.  **Export:** Saves the table using `sink_parquet()` for streaming output and triggers garbage collection.

### Workflow II: Dimension Reference Extraction
1.  **Selection:** Iterates through the `DIMENSION_REFERENCES` registry.
2.  **Deduplication:** Extracts required columns and removes duplicate primary keys.
3.  **Export:** Saves each dimension table as an independent artifact.

## Optimization & Resource Management

* **Integer Mapping:** Converts UUID strings to `UInt64` hashes for joins and `UInt32` for payloads. This reduces memory overhead when processing large datasets.
* **Streaming Joins:** Defers aggregations until after joins, leveraging the Polars streaming engine to avoid large materialized tables.
* **Memory Reclamation:** Uses `malloc_trim(0)` during high-water mark transitions to release free memory back to the OS.
* **Zero-Copy Streaming:** Employs `sink_parquet()` to avoid materializing the entire result set in memory.

## Boundaries

| This component | This component does NOT |
| :--- | :--- |
| Joins relational tables into a flat grain. | Perform data cleaning (handled in Contract stage). |
| Calculates time-deltas (e.g., lead times). | Perform multi-stage aggregations (delegated to Semantic stage). |
| Enforces 1:1 cardinality for the event grain. | Validate raw data schemas. |
| Deduplicates dimension attributes. | Manage partitioning logic. |
| Manages peak memory and garbage collection. | Change historical values or re-map IDs. |
| Uses Hash-Joins for high-cardinality keys. | Perform blocking sorts on large datasets. |

## Failure & Severity Model

### System Failures
* **Task Failure:** Transformation steps are wrapped in a handler that logs exceptions and returns a failure status.
* **Executor Safety:** Top-level orchestration uses `try-except-finally` blocks to catch crashes and ensure resource cleanup.
* **Missing Data:** If a required table is missing from the Silver zone, the stage fails.
* **I/O Failure:** Storage or path errors during export halt the lifecycle.

### Data Findings
* **Optional Joins:** Orders without payments are allowed; the system fills missing values with nulls, which is treated as a valid state.
