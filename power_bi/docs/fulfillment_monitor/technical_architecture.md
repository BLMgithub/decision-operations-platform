# Technical Documentation: Fulfillment Decision Monitor

## Technical Architecture
*   **Data Source:** Google BigQuery (`seller_dim`, `seller_weekly_fact`).
*   **Update Logic:** Performance snapshots are generated weekly; the `last_source_update` metric tracks data freshness from the BigQuery metadata.
*   **Storage Mode:** Import Mode (Power BI).

## Dynamic Outlier Detection (The "Smoke Detector")
The dashboard identifies risk using a dual-layer **parameter-driven** statistical filter (`is_outlier` measure):
- **Dynamic Slippage Threshold:** Uses the `[slippage_threshold Value]` parameter (range 0.5 – 3.0 days) to set the minimum speed loss *(Delivery Delay)* required for an alert.
- **Dynamic Statistical Boundary:** Uses the `[std_dev_boundary Value]` parameter (range 1.0 – 3.0) as a multiplier for the standard deviation boundary.
- **Exclusion Logic:** The `is_valid_year` variable excludes 2022 records to prevent incomplete historical data from skewing the baseline.

## DAX Data Dictionary
*(See [`dax_dictionary.md`](./dax_dictionary.md) for full expressions)*

### Measures Group: Paging & Navigation

| **Measure Name** | Description |
| --- | --- |
| **item_rank** | Ranks sellers by slippage intensity for sorted lists. |
| **item_rank_filter** | Logic for identifying sellers within the current page range. |
| **max_page** | Dynamic calculation of total pages based on at-risk count. |
| **page_filter** | Global logic used to restrict the paging slicer range. |
| **current_viewed_filter** | Color-based logic for highlighting current page items. |
| **revenue_at_risk** | Additive revenue impact calculation for at-risk sellers. |

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
| **network_slowdown** | Percentage of volume currently trending slower than baseline. |
| **delivery_stability** | Statistical measure of delivery date unpredictability. |

### Measures Group: Visual Measures (UX)

| **Measure Name** | Description |
| --- | --- |
| **latency_slippage** | The magnitude of speed loss (days) for at-risk sellers. |
| **total_order_volume** | Aggregate count of all order items. |
| **logistics_delay** | Isolated courier performance (Total - Warehouse). |
| **internal_delay** | Average warehouse processing/approval lag. |
| **is_new_seller** | Flags sellers in their first 30 days of operation. |
| **bubble_size_sensivity** | Exponential scaling for scatter plot markers. |
| **last_source_update** | Displays the most recent data sync timestamp. |
| **wrapper_is_outlier** | String-based status flag ("Active" / "No"). |

### Measures Group: Tooltip Visual Measures (UX)

| **Measure Name** | Description |
| --- | --- |
| **revenue_exposed** | Total financial value handled by sellers currently at risk. |
| **tool_tip_week_start_date** | Temporal context for trend line hover details. |
| **tooltip_seller_id** | Specific Seller ID associated with a data point. |