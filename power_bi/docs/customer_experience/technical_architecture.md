# Technical Documentation: Customer Experience & Revenue Exposure

## Technical Architecture
*   **Data Source:** Google BigQuery (`customer_dim`, `customer_weekly_fact`).
*   **Update Logic:** The `Source Last Update` metric uses BigQuery schema metadata from the `source_last_update` table.
*   **Storage Mode:** Import Mode (Power BI).
*   **Time Grain:** Weekly aggregation for fact data; monthly aggregation for retention and drop-off analysis.

## Core Logic & Calculations

### Revenue At Risk
The dashboard identifies financial exposure using parameter-driven filtering logic in the `revenue_at_risk` measure:
- **Delay Threshold:** Uses the `[delay_threshold_parameter]` (1–14 days) to define the delivery delay required to flag revenue as at risk.

### Buyer Drop-off Monitoring
Tracks customer abandonment using month-over-month (MoM) logic:
- **Identification:** Uses `EXCEPT` logic to identify customers active in the previous month who are absent in the current month.

## DAX Data Dictionary
*(See [`dax_dictionary.md`](./dax_dictionary.md) for full expressions)*

### Base Measures

| **Measure Name** | Description |
| --- | --- |
| **total_revenue** | Gross financial value of all transactions. |
| **total_order** | Total count of orders. |
| **total_delivered** | Count of orders with a delivery status. |
| **total_cancelled** | Count of cancelled orders. |
| **active_customer_current** | Distinct count of customers in the selected month. |
| **active_customer_prev_month** | Distinct count of customers in the previous month. |
| **MoM_drop_off_customers** | Count of customers active last month but not the current month. |

### Key Performance Indicators (KPI)

| **Measure Name** | Description |
| --- | --- |
| **revenue_at_risk** | Revenue associated with delivery delays exceeding the threshold. |
| **MoM_drop_off_rate** | Percentage of last month's buyers who have not returned. |
| **cancellation_rate** | Ratio of cancelled orders to total order volume. |

### Visual and UX Measures

| **Measure Name** | Description |
| --- | --- |
| **weighted_avg_delivery_delay** | Volume-weighted mean of delivery delays. |
| **weighted_avg_approval_lag** | Volume-weighted mean of order processing time. |
| **weighted_avg_lead_time** | Volume-weighted mean of total fulfillment duration. |
| **bubble_size_sensitivity** | Scaled markers for scatter plot visualization. |
| **color_format_revenue_at_risk** | Logic for conditional formatting. |
| **last_source_update** | Timestamp of the most recent data refresh. |

### Tooltip Measures

| **Measure Name** | Description |
| --- | --- |
| **tooltip_revenue_at_risk** | Formatted currency for hover details. |
| **tooltip_avg_delivery_delay** | Formatted string for delay diagnostics. |
| **tooltip_avg_approval_lag** | Formatted string for processing diagnostics. |
| **tooltip_avg_lead_time** | Formatted string for fulfillment diagnostics. |
| **tooltip_MoM_drop_off_customer** | Formatted headcount for retention tooltips. |
| **tooltip_highlight_top_3** | Logic for ranking highlights. |
