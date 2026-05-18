# Technical Documentation: Fulfillment Decision Monitor

## Technical Architecture
*   **Data Source:** Google BigQuery (`seller_dim`, `seller_weekly_fact`).
*   **Update Logic:** Performance snapshots are generated weekly. The `last_source_update` metric tracks data refresh timestamps from BigQuery metadata.
*   **Storage Mode:** Import Mode (Power BI).

## Outlier Detection Logic
The dashboard identifies fulfillment risk using a statistical filter based on two parameters:
- **Slippage Threshold:** Uses the `[slippage_threshold Value]` parameter (0.5 – 3.0 days) to define the minimum delivery delay required for an alert.
- **Statistical Boundary:** Uses the `[std_dev_boundary Value]` parameter (1.0 – 3.0) as a multiplier for the standard deviation boundary.
- **Data Filtering:** Historical data from 2022 is excluded to prevent incomplete records from affecting the baseline.

## DAX Data Dictionary
*(See [`dax_dictionary.md`](./dax_dictionary.md) for full expressions)*

### Paging and Navigation

| **Measure Name** | Description |
| --- | --- |
| **item_rank** | Ranks sellers by slippage intensity for sorted lists. |
| **item_rank_filter** | Identifies sellers within the current page range. |
| **max_page** | Calculates total pages based on the count of sellers at risk. |
| **page_filter** | Restricts the paging slicer range. |
| **current_viewed_filter** | Highlights items on the current page. |
| **revenue_at_risk** | Calculates the revenue impact of at-risk sellers. |

### Base Measures

| **Measure Name** | Description |
| --- | --- |
| **latency** | Average delivery delay (Actual vs. Estimated). |
| **latency_current_week** | Latency for the selected week. |
| **latency_previous_week** | Latency for the prior week used for trend analysis. |
| **latency_4w_rolling_avg** | 28-day trailing baseline for fulfillment performance. |
| **is_outlier** | Flags sellers deviating from historical performance baselines. |
| **matrix_slippage_tracker** | Maintains seller visibility in historical heatmaps. |
| **is_outlier_global** | Outlier status ignoring local visual date filters. |

### Key Performance Indicators (KPI)

| **Measure Name** | Description |
| --- | --- |
| **seller_at_risk** | Count of unique sellers flagged for intervention. |
| **network_slowdown** | Percentage of volume trending slower than the baseline. |
| **delivery_stability** | Statistical measure of delivery date variability. |

### Visual and UX Measures

| **Measure Name** | Description |
| --- | --- |
| **latency_slippage** | Magnitude of delay (days) for at-risk sellers. |
| **total_order_volume** | Total count of order items. |
| **logistics_delay** | Average courier performance delay. |
| **internal_delay** | Average warehouse processing or approval lag. |
| **is_new_seller** | Flags sellers in their first 30 days of operation. |
| **bubble_size_sensivity** | Scales scatter plot markers based on revenue risk. |
| **last_source_update** | Timestamp of the most recent data sync. |
| **wrapper_is_outlier** | Status flag ("Active" / "No"). |

### Tooltip Measures

| **Measure Name** | Description |
| --- | --- |
| **revenue_exposed** | Total revenue handled by sellers currently at risk. |
| **tool_tip_week_start_date** | Date context for trend line tooltips. |
| **tooltip_seller_id** | Seller ID associated with a data point. |
