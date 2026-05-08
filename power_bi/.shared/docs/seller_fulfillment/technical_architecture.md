# Technical Documentation: Fulfillment Decision Monitor

## Technical Architecture
*   **Data Source:** Google BigQuery (`seller_dim`, `seller_weekly_fact`).
*   **Update Logic:** Performance snapshots are generated weekly; the `last_source_update` metric tracks data freshness from the BigQuery metadata.
*   **Storage Mode:** Import Mode (Power BI).

## Outlier Detection Logic (The "Smoke Detector")
The dashboard identifies risk using a dual-layer statistical filter (`is_outlier` measure):
- **Meaningful Slippage:** A seller must be at least **0.5 days** slower than their own 4-week rolling average.
- **Statistical Deviation:** The current latency must exceed **1 Standard Deviation** of that specific seller's historical performance (excluding the 2022 baseline period).

## DAX Data Dictionary
*(See [`dax_dictionary.md`](./dax_dictionary.md) for full expressions)*

### Measures Group: Prerequisites Measures

| **Measure Name** | Description |
| --- | --- |
| **latency** | Basic average of the delivery delay (Estimated vs. Actual). |
| **latency_current_week** | Context-aware latency for the specific date selection. |
| **latency_previous_week** | Prior week latency for trend analysis. |
| **latency_4w_rolling_avg** | 28-day trailing baseline for fulfillment performance. |
| **is_outlier** | Core logic flagging sellers deviating from historical norms. |
| **matrix_slippage_tracker** | Logic for maintaining seller visibility in historical heatmaps. |
| **is_outlier_global** | Outlier status ignoring local visual date filters. |

### Measures Group: Key Performance Indicator (KPI)

| **Measure Name** | Description |
| --- | --- |
| **seller_at_risk** | Count of unique Seller IDs flagged for intervention. |
| **systemic_drift_pct** | Percentage of volume currently trending slower than baseline. |
| **fulfillment_instability_index** | Statistical measure of delivery date unpredictability. |

### Measures Group: Visual Measures (UX)

| **Measure Name** | Description |
| --- | --- |
| **latency_slippage** | The magnitude of speed loss (days) for at-risk sellers. |
| **total_order_volume** | Aggregate count of all order items. |
| **logistics_delay** | Isolated courier performance (Total - Warehouse). |
| **internal_delay** | Average warehouse processing/approval lag. |
| **is_new_seller** | Flags sellers in their first 30 days of operation. |
| **top_10_filter_color** | Conditional formatting for highlighting top impact sellers. |
| **top_20_filter_color** | Conditional formatting for top 20 impact sellers. |
| **top_10_seller_id** | Visual-level filter logic for strict 10-row limits. |
| **top_20_seller_id** | Visual-level filter logic for strict 20-row limits. |
| **bubble_size_sensivity** | Exponential scaling for scatter plot markers. |
| **last_source_update** | Displays the most recent data sync timestamp. |

### Measures Group: Tooltip Visual Measures (UX)

| **Measure Name** | Description |
| --- | --- |
| **revenue_exposed** | Total financial value handled by sellers currently at risk. |
| **tool_tip_week_start_date** | Temporal context for trend line hover details. |
| **tooltip_is_new_seller** | Onboarding context for hover-over diagnostics. |
| **tooltip_seller_id** | Specific Seller ID associated with a data point. |

## Maintenance Notes
*   **Threshold Calibration:** To adjust sensitivity, modify the `is_outlier` measure (adjust `0.5` for slippage or `1 * _stddev` for the statistical boundary).
*   **Baseline Exclusion:** The `is_valid_year` variable currently excludes 2022 records to prevent incomplete historical data from skewing the standard deviation.
