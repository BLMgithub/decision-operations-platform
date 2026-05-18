# Technical Documentation: Product Friction Monitor

## Technical Architecture
*   **Data Source:** Google BigQuery (`published_product_dim`, `published_product_weekly_fact`).
*   **Update Logic:** The `Source Last Update` metric tracks data refresh timestamps from the `source_last_update` BigQuery metadata table.
*   **Storage Mode:** Import Mode (Power BI).
*   **Weight Classifications:**
    *   Small: < 1kg
    *   Standard: < 5kg
    *   Heavy: < 10kg
    *   Oversize: > 10kg

## Outlier Detection Logic
The dashboard identifies fulfillment risk using a statistical filter based on two parameters:
- **Slippage Threshold:** Uses the `[slippage_threshold Value]` parameter (0.5 – 5.0 days) to define the minimum lead-time delay required for an alert.
- **Statistical Boundary:** Uses the `[std_dev_boundary Value]` parameter (1.0 – 3.0) as a multiplier for the standard deviation boundary.

## DAX Data Dictionary
*(See [`dax_dictionary.md`](../product_friction/dax_dictionary.md) for full expressions)*

### Paging and Navigation

| **Measure Name** | Description |
| --- | --- |
| **item_rank** | Ranks products by slippage intensity for sorted lists. |
| **item_rank_filter** | Identifies products within the current page range. |
| **max_page** | Calculates total pages based on the count of products at risk. |
| **page_filter** | Restricts the paging slicer range. |
| **current_viewed_filter** | Highlights items on the current page. |

### Base Measures

| **Measure Name** | Description |
| --- | --- |
| **total_orders** | Total count of order items. |
| **avg_delivery_delay** | Mean days of delay for delivered orders. |
| **total_cancelled** | Total volume of cancelled orders. |
| **total_revenue** | Gross revenue across all categories. |
| **avg_lead_time** | Mean duration from order creation to delivery. |
| **lead_time_4w_rolling_avg** | 28-day trailing baseline for fulfillment performance. |
| **is_outlier** | Flags products deviating from historical performance baselines. |
| **current_lead_time** | Lead time for the selected date. |
| **lead_time_slippage** | Magnitude of lead-time delay (days) for at-risk products. |

### Key Performance Indicators (KPI)

| **Measure Name** | Description |
| --- | --- |
| **product_at_risk** | Count of unique products flagged for intervention. |
| **lead_time_volatility** | Statistical measure of delivery date variability. |
| **revenue_at_risk** | Total revenue associated with fulfillment delays. |

### Visual and UX Measures

| **Measure Name** | Description |
| --- | --- |
| **product_weight** | Product weight in grams. |
| **product_volume_categ** | Weight-based classification for grouping. |
| **category_range_view** | Logic for the Category Revenue chart Y-axis. |
| **bubble_size_sensitivity** | Scales scatter plot markers based on revenue risk. |
| **format_product_id_count** | Formatted count of at-risk products. |
| **format_total_orders** | Formatted order volume for display. |
| **last_source_update** | Timestamp of the most recent data refresh. |

### Tooltip Measures

| **Measure Name** | Description |
| --- | --- |
| **tooltip_format_revenue** | Formatted revenue metrics for tooltips. |
| **tooltip_oversize** | Outlier count within the "Oversize" weight bucket. |
| **tooltip_heavy** | Outlier count within the "Heavy" weight bucket. |
| **tooltip_standard** | Outlier count within the "Standard" weight bucket. |
| **tooltip_small** | Outlier count within the "Small" weight bucket. |
| **tooltip_week_start** | Date context for trend line tooltips. |
| **tooltip_product_id** | Product ID associated with a data point. |
