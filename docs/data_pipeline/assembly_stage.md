# **Assembly Stage**

**Files:**
* **Executor:** [`assembly_executor.py`](../data_pipeline/assembly/assembly_executor.py)
* **Logic:** [`assembly_logic.py`](../data_pipeline/assembly/assembly_logic.py)

**Role:** Data Integration and Analytical Flattening.

## **System Contract**

**Purpose**

Integrates multiple normalized relational tables into a unified, analytical "Event" dataset and extracts high-fidelity "Dimension" references. It transforms raw business facts into a ready-to-model state by enforcing cardinality rules and calculating temporal performance metrics.

**Invariants**
* **Strict Order-ID Grain:** The primary event output is guaranteed to be exactly 1 row per `order_id`. Any operation causing cardinality explosion triggers a terminal failure.
* **Inner-Join Priority:** To maintain analytical integrity, orders without corresponding items are purged.
* **Temporal Determinism:** All lead times, lags, and delays are calculated as integer-day durations based on validated UTC timestamps.
* **Reference Uniqueness:** Dimension reference tables (Customers, Products) are strictly deduplicated by their primary keys.

**Inputs**
* `run_context`: `RunContext` (Path resolution for Silver/contracted and Gold/assembled zones).
* **Source Tables:** `df_orders`, `df_order_items`, `df_payments` (from the contracted layer).

**Outputs**
* **Assembly Report:** `dict` (Step-level status and informational logs).
* **Assembled Events:** `parquet` (The unified analytical order-grain table).
* **Dimension Refs:** `parquet` (Unique snapshots of customer and product attributes).

## **Execution Workflow**

The **Executor** coordinates two distinct sub-orchestrations:

### **Workflow I: Event Assembly**
1.  **Batch Load:** Fetches the required triplet (`orders`, `items`, `payments`) from the Silver zone.
2.  **Merge:** Joins datasets using `merge_data`. It performs an inner join on items and a left join on payments to preserve financial data without losing order context.
3.  **Derivation:** Executes `derive_fields` to calculate fulfillment lead times and extract ISO-calendar attributes.
4.  **Schema Freeze:** Projects the final `ASSEMBLE_SCHEMA` and casts all columns to `ASSEMBLE_DTYPES`.
5.  **Export & Clean:** Persists the table and triggers `gc.collect()` to free memory before dimension processing.

### **Workflow II: Dimension Reference Extraction**
1.  **Selection:** Iterates through the `DIMENSION_REFERENCES` registry.
2.  **Deduplication:** Extracts the required column subset and drops duplicate primary keys.
3.  **Export:** Persists each dimension (e.g., `df_customers`) as an independent artifact.

## **Boundaries**

| This component **DOES** | This component **DOES NOT** |
| :--- | :--- |
| Join multiple relational tables into a flat grain. | Perform data cleaning (handled in Contract stage). |
| Calculate time-deltas (e.g., `lead_time_days`). | Perform complex multi-stage aggregations (delegated to Semantic stage). |
| Enforce 1:1 cardinality for the final event grain. | Handle schema validation of raw data. |
| Deduplicate dimension attributes. | Manage partitioning logic (managed by the loader/exporter). |
| Manage peak memory via explicit `gc` triggers. | Change historical values or re-map IDs. |

## **Failure & Severity Model**

### **Operational Failures (System Level)**
* **Loading Missing Table:** If a required table (e.g., `df_orders`) is missing from the Silver zone, the stage returns `failed` immediately.
* **Export Failure:** Disk I/O errors or path resolution issues during the `export_file` call halt the lifecycle.

### **Functional Findings (Data Level)**

* **Cardinality Explosion:** If `merge_data` detects multiple rows for a single `order_id`, it raises a `RuntimeError`, treating it as a fatal violation of the analytical grain.
* **Reference Duplication:** If a dimension table contains duplicate primary keys after extraction, it raises a `RuntimeError` to prevent downstream join corruption.
* **Partial Payments:** Orders without payments are allowed (via Left Join); the system fills these with `None/NaN`, which is considered a valid business state rather than a failure.