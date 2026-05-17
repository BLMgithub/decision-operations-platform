# Technical Documentation: Customer Experience & Revenue Exposure

## Technical Architecture
*   **Data Source:** Google BigQuery (`customer_dim`, `customer_weekly_fact`).
*   **Update Logic:** The `Source Last Update` metric is driven by the BigQuery schema metadata (`source_last_update` table), ensuring data freshness transparency.
*   **Storage Mode:** Import Mode (Power BI).
*   **Time Grain:** Weekly aggregation for fact data; Monthly aggregation for retention/drop-off analysis.

## Core Logic & Calculations

### Proactive Danger Zone (Revenue at Risk)
The dashboard identifies financial exposure using a **parameter-driven** filtering logic (`revenue_at_risk` measure):
- **Dynamic Delay Threshold:** Uses the `[delay_threshold_parameter]` (range 1 – 14 days) to define the minimum delivery delay required to flag revenue as "At Risk."

### MoM Buyer Drop-off (Retention Monitor)
Tracks short-term customer abandonment using month-over-month set-based logic:
- **Set-Based Identification:** Employs `EXCEPT` logic to isolate customers active in the previous month who are absent in the current month selection.

## DAX Data Dictionary
*(See [`dax_dictionary.md`](./dax_dictionary.md) for full expressions)*

### Measures Group: Prerequisites Measures (Base Measures)

| **Measure Name** | Description |
| --- | --- |
| **total_revenue** | Gross financial value across all transactions. |
| **total_order** | Aggregate count of orders placed. |
| **total_delivered** | Count of orders with a successful delivery status. |
| **total_cancelled** | Volume of orders cancelled by customers or the system. |
| **active_customer_current** | Distinct count of customers buying in the selected month. |
| **active_customer_prev_month** | Distinct count of customers buying in the previous month. |
| **MoM_drop_off_customers** | Headcount of customers active last month but not this month. |

### Measures Group: Key Performance Indicator (KPI)

| **Measure Name** | Description |
| --- | --- |
| **revenue_at_risk** | Total revenue trapped in delivery delays > threshold. |
| **MoM_drop_off_rate** | Percentage of last month's buyers who haven't returned. |
| **cancellation_rate** | Ratio of lost orders to total order volume. |

### Measures Group: Visual Measures (UX)

| **Measure Name** | Description |
| --- | --- |
| **weighted_avg_delivery_delay** | Volume-weighted mean of delivery delays. |
| **weighted_avg_approval_lag** | Volume-weighted mean of order processing time. |
| **weighted_avg_lead_time** | Volume-weighted mean of total fulfillment duration. |
| **bubble_size_sensitivity** | Power-scaled markers for high-impact scatter plot points. |
| **color_format_revenue_at_risk** | Drive-ratio for conditional formatting (Green/Orange/Red). |
| **last_source_update** | Timestamp of the most recent BigQuery data refresh. |

### Measures Group: Visual Tooltip Measures (UX)

| **Measure Name** | Description |
| --- | --- |
| **tooltip_revenue_at_risk** | Formatted currency (K/M) for hover details. |
| **tooltip_avg_delivery_delay** | String-formatted delay diagnostic. |
| **tooltip_avg_approval_lag** | String-formatted processing diagnostic. |
| **tooltip_avg_lead_time** | String-formatted fulfillment diagnostic. |
| **tooltip_MoM_drop_off_customer** | Formatted headcount for retention tooltips. |
| **tooltip_highlight_top_3** | Logic for state-level ranking highlights. |
