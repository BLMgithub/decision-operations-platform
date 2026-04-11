# Data & Synthetic Benchmarks

This directory serves as the local state provider for the pipeline when executing in a non-cloud environment. It mimics the structure of the Google Cloud Storage (GCS) buckets, allowing for high-fidelity local simulation and performance benchmarking.

## Synthetic Dataset
To replicate the high-volume environment described in the [GCP Stress-Test Metrics (Scaling Efficiency)](/README.md#gcp-stress-test-metrics-scaling-efficiency) section, you can download the 36M-row synthetic dataset here: [**Kaggle Dataset Link**](https://www.kaggle.com/datasets/melvidabryan/e-commerce-synthetic-dataset)

>*Note: This upload contains the **Contracted Version** of the dataset. The original "Raw" state—totaling approximately 24GB of unrefined CSVs was omitted to prioritize transfer efficiency.*

### File Structure & Purpose
The dataset is divided into two primary directories to facilitate different stages of pipeline testing:

| Directory | Files | Description |
| :--- | :--- | :--- |
| `contracted/` | 110 files | **Production-Scale Test:** The full 36M row dataset (~4.04 GB) formatted to strict enterprise schema requirements. |
| `raw/` | 5 files | **Delta Sample (Validation):** Small-scale samples (~10k rows each) representing **daily incoming deltas**. These files are intentionally "noisy" to exhibit the full range of injected data quality errors. |

### Included Tables

The dataset provides a complete relational snapshot of an e-commerce ecosystem:

  * **`df_orders`**: Fact table with lifecycle timestamps (Purchase, Approved, Delivered, Estimated).
  * **`df_order_items`**: Bridge table linking orders to products and sellers.
  * **`df_payments`**: Transactional data including sequential payment tracking.
  * **`df_products`**: Dimensions including weight, dimensions, and fragility indexes.
  * **`df_customers`**: Geographic data and business segments (D2C, SMB, Enterprise).

## Local Execution Setup
1.  Extract the downloaded dataset archive.
2.  Copy the `raw/` and `contracted/` directories into this `data/` folder.
3.  The `RunContext` manager is configured to strictly recognize `.parquet` and `.csv` extensions; all other file types are ignored to prevent ingestion noise.

**Execute the local pipeline:**
```
python -m data_pipeline.run_pipeline
```