# **Semantic Modeling Stage**

**Files:**
* **Executor:** [`semantic_executor.py`](../data_pipeline/semantic/semantic_executor.py)
* **Logic:** [`semantic_logic.py`](../data_pipeline/semantic/semantic_logic.py)
* **Registry:** [`registry.py`](../data_pipeline/semantic/registry.py)

**Role:** Analytical Module Construction.

## **System Contract**

**Purpose**

Transforms the unified Gold-layer "Order-Grain" event table into entity-centric Fact and Dimension modules. It performs temporal aggregations, calculates long-term performance metrics, and organizes data into a schema optimized for time-series and cohort analysis.

**Invariants**

* **Lineage Integrity:** Strictly enforces that all data within a builder execution belongs to a single `run_id`. Cross-run data contamination triggers a terminal failure.
* **Temporal Grain:** All fact tables are aggregated at the ISO-Week level, aligned deterministically to the Monday of each week (`W-MON`).
* **Entity Grain:** 
    * **Fact Tables:** Strictly 1 row per `(Entity_ID, order_year_week)`.
    * **Dimension Tables:** Strictly 1 row per `Entity_ID`.
* **Technical Contract:** Every output table is subject to a "Freeze" pass that guarantees 1:1 schema matching and strict dtype casting as defined in the `SEMANTIC_MODULES` registry.

**Inputs**
* `run_context`: `RunContext` (Path resolution and `run_id` lineage).
* `assembled_events`: `pd.DataFrame` (The unified analytical source from the Assembly stage).
* `SEMANTIC_MODULES`: `Registry` (Defines builders, expected tables, grains, and technical schemas).

**Outputs**
* **Semantic Report:** `dict` (Hierarchical status of module-level and table-level processing).
* **Semantic Modules:** `parquet` (Fact and Dimension tables for Sellers, Customers, and Products).

## **Execution Workflow**

The **Executor** coordinates the semantic build through a modular, registry-driven loop:

1.  **Source Verification:** Loads the `assembled_events` table. If the source is missing or contains zero rows, the stage terminates with a `failed` status.
2.  **Module Initialization:** Iterates through `SEMANTIC_MODULES` defined in the registry.
3.  **Builder Execution:** Dispatches the source data to the module's `builder` function (e.g., `build_seller_semantic`).
4.  **Contract Enforcement:** For every table returned by a builder, the executor calls `validate_and_freeze_table` to:
    * Assert the uniqueness of the defined **Grain**.
    * Project the exact **Schema** (dropping internal helper columns).
    * Enforce strict **Data Types**.
5.  **Partitioned Export:** Persists artifacts into module-specific subdirectories within the semantic zone, using a date-partitioned naming convention.
6.  **Memory Management:** Explicitly deletes DataFrames and triggers `gc.collect()` after every individual table export (Fact and Dim) to prevent memory accumulation during large-scale aggregations.


## **Boundaries**

| This component **DOES** | This component **DOES NOT** |
| :--- | :--- |
| Perform multi-level aggregations (Sum, Mean, Count). | Filter "bad" data (handled in Validation/Contract stages). |
| Derive entity-level attributes (e.g., `first_order_date`). | Resolve order-item join cardinality. |
| Align all temporal metrics to the ISO Week grain. | Mutate the "Assembled Events" source. |
| Enforce technical schemas and data types. | Manage the physical publish/pointer logic. |
| Organize data into Fact/Dimension modules. | Perform cross-module joins. |

## **Failure & Severity Model**

### **Operational Failures (System Level)**
* **Missing Source:** Failure to load `assembled_events` results in an immediate stage failure.
* **Registry Mismatch:** If a builder returns a table name not defined in the `SEMANTIC_MODULES` registry, the executor raises a `RuntimeError`.

### **Functional Findings (Data Level)**
* **Lineage Violation:** If the source data contains more than one `run_id`, the logic builders raise a `RuntimeError` to prevent multi-run pollution.
* **Grain Breach:** If a builder produces duplicate rows for the defined primary grain (e.g., multiple rows for the same Seller/Week), the validation step raises a `RuntimeError`.
* **Schema Violation:** If a required column defined in the registry is missing from the builder's output, the freeze step raises a `KeyError`.