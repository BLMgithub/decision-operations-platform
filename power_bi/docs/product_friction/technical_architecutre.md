# Technical Documentation: Product Friction Monitor

## Technical Architecture
*   **Data Source:** Google BigQuery (`published_product_dim`, `published_product_weekly_fact`).
*   **Update Logic:** The `Source Last Update` metric is driven by the BigQuery schema metadata, (`source_last_update` table), ensuring users know the exact freshness of the snapshot.
*   **Storage Mode:** Import Mode (Power BI).
*   **Size Buckets:** Standardized weight classifications (Small < 1kg, Standard < 5kg, Heavy < 10kg, Oversize > 10kg).

## Dynamic Outlier Detection (The "Smoke Detector")
The dashboard identifies risk using a dual-layer **parameter-driven** statistical filter (`is_outlier` measure):
- **Dynamic Slippage Threshold:** Uses the `[slippage_threshold Value]` parameter (range 0.5 – 5.0 days) to set the minimum speed loss *(Lead Time)* required for an alert.
- **Dynamic Statistical Boundary:** Uses the `[std_dev_boundary Value]` parameter (range 1.0 – 3.0) as a multiplier for the standard deviation boundary.

## DAX Data Dictionary
*(See [`dax_data_dictionary.md`](../product_friction/dax_dictionary.md) for full expressions)*

### Measures Group: Paging & Navigation

| **Measure Name** | Description |
| --- | --- |
| **item_rank** | Ranks products by slippage intensity for sorted lists. |
| **item_rank_filter** | Logic for identifying products within the current page range. |
| **max_page** | Dynamic calculation of total pages based on at-risk count. |
| **page_filter** | Global logic used to restrict the paging slicer range. |
| **current_viewed_filter** | Color-based logic for highlighting current page items. |

### Measures Group: Prerequisites Measures (Base Measures)

| **Measure Name** | Description |
| --- | --- |
| **total_orders** | Aggregate count of order items within the filtered period. |
| **avg_delivery_delay** | Mean days of delay for delivered orders. |
| **total_cancelled** | Aggregate volume of cancelled orders. |
| **total_revenue** | Gross revenue generated across all categories. |
| **avg_lead_time** | Mean duration from order creation to delivery. |
| **lead_time_4w_rolling_avg** | 28-day trailing baseline for fulfillment performance. |
| **is_outlier** | Core logic flagging products deviating from historical norms. |
| **current_lead_time** | Context-aware lead time for the specific date selection. |
| **lead_time_slippage** | The magnitude of speed loss (days) for at-risk products. |

### Measures Group: Key Performance Indicator (KPI)

| **Measure Name** | Description 
| --- | --- |
| **product_at_risk** | Count of unique Product IDs flagged for intervention. |
| **lead_time_volatility** | Statistical measure of delivery date unpredictability. |
| **revenue_at_risk** | Total financial value currently impacted by fulfillment friction. |

### Measures Group: Visual Measures (UX)

| **Measure Name** | Description |
| --- | --- |
| **product_weight** | Static gram weight for the product in visual context. |
| **product_volume_categ** | Weight-based classification (Small, Heavy, etc.) for grouping. |
| **category_range_view** | Dynamic Y-Axis buffer for the Category Revenue chart. |
| **bubble_size_sensitivity** | Exponential scaling for scatter plot markers. |
| **format_product_id_count** | String-formatted count of at-risk products for slicers. |
| **format_total_orders** | Smart-formatted order volume (K/M) for display. |
| **last_source_update** | Displays the most recent data sync timestamp. |

### Measures Group: Visual Tooltip Measures (UX)

| **Measure Name** | Description |
| --- | --- |
| **tooltip_format_revenue** | Precision formatting for revenue metrics in tooltips. |
| **tooltip_oversize** | Outlier count within the "Oversize" weight bucket. |
| **tooltip_heavy** | Outlier count within the "Heavy" weight bucket. |
| **tooltip_standard** | Outlier count within the "Standard" weight bucket. |
| **tooltip_small** | Outlier count within the "Small" weight bucket. |
| **tooltip_week_start** | Temporal context for trend line hover details. |
| **tooltip_product_id** | Specific Product ID associated with a data point. |
