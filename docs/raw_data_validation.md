# Raw Data Validation — CI Gate

## Purpose

Enforce **structural and semantic integrity** of raw fulfillment data before any merge, aggregation, or BI ingestion.

This script is a **hard CI/CD gate**.  
If it fails, the pipeline stops.

Passing means the data is **structurally usable**, not analytically correct.

## Scope

Validates raw CSV data in: `data/raw/train/`

All files belonging to the same logical table are loaded via **filename prefix** (e.g. `df_Orders*.csv`) and validated as a single dataset.

This script does **not**:
- clean or modify data
- filter records
- apply thresholds
- encode business logic
- produce output files

## Validation Layers

### Base Validations (All Tables)
**CI-blocking**
- Empty dataset
- Duplicate column names
- Missing primary key columns
- Null primary key values
- Duplicated primary keys

Guarantees identity and join safety.

### Event Fact Validations (`df_Orders`)
**CI-blocking**
- Missing required timestamps
- Unparsable timestamps
- Approval before purchase
- Delivery before purchase

Guarantees temporal correctness.

### Transaction Detail Validations  (`df_OrderItems`, `df_payments`)
**CI-blocking**
- Negative numeric values

Prevents corrupted aggregations.

### Cross-Table Validations
**CI-blocking**
- Order items referencing missing orders
- Payments referencing missing orders
- Missing required parent tables

Guarantees referential integrity.

## Control Flow

- Validation functions detect and log errors
- Local checks may stop early when further validation is invalid
- CI outcome is decided **once**, at script end

exit 0 → validation passed
exit 1 → validation failed

Warnings and info logs do not affect CI outcome.

## Design Principles

- Fail fast only when continuation is unsafe
- Accumulate errors when diagnostics remain meaningful
- Enforce structure, not judgment
- Validation ≠ preparation ≠ analytics

## Downstream Contract

Only data that passes this script may be used by:
1. Merge / enrichment pipeline
2. Fact table derivation
3. BI ingestion

This script defines the **raw data contract** for the pipeline.