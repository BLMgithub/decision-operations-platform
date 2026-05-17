# DAX Data Dictionary: Customer Experience & Revenue Exposure Dashboard

### <ins>Display Folder - _prerequisite_measures</ins>
*Fundamental building blocks and base aggregations required for higher-level logic. This section includes primary counts, temporal baselines, and period-over-period comparison logic.*

- Measure Name: **`total_revenue`**
- Description: *Gross revenue generated across all customer segments and regions.*
    ```dax
    SUM(customer_weekly_fact[weekly_revenue])
    ```

<br>

- Measure Name: **`total_order`**
- Description: *Aggregate count of orders within the filtered period.*
    ```dax
    SUM(customer_weekly_fact[weekly_order_count])
    ```

<br>

- Measure Name: **`total_delivered`**
- Description: *Count of orders successfully delivered to customers.*
    ```dax
    SUM(customer_weekly_fact[weekly_delivered_orders])
    ```

<br>

- Measure Name: **`total_cancelled`**
- Description: *Volume of orders cancelled by the customer or system.*
    ```dax
    SUM(customer_weekly_fact[weekly_cancelled_orders])
    ```

<br>

- Measure Name: **`active_customer_current`**
- Description: *Distinct count of unique customers who placed an order in the current selected month.*
    ```dax
    CALCULATE(
        DISTINCTCOUNT(customer_weekly_fact[customer_id_int]),
        calendar_table[Month Name] = SELECTEDVALUE(calendar_table[Month Name])
    )
    ```

<br>

- Measure Name: **`active_customer_prev_month`**
- Description: *Baseline count of unique active customers from the previous calendar month.*
    ```dax
    CALCULATE(
        DISTINCTCOUNT(customer_weekly_fact[customer_id_int]),
        DATEADD(calendar_table[Date], -1, MONTH)
    )
    ```

<br>

- Measure Name: **`MoM_drop_off_customers`**
- Description: *Identifies customers active in the previous month who have not placed an order in the current month.*
    ```dax
    VAR prev_period_customer = 
        CALCULATETABLE(
            DISTINCT(customer_weekly_fact[customer_id_int]),
            DATEADD(calendar_table[Date], -1, MONTH)
        )
    VAR current_period_customers =
        CALCULATETABLE(
            DISTINCT(customer_weekly_fact[customer_id_int]),
            calendar_table[Month Name] = SELECTEDVALUE(calendar_table[Month Name])
        )

    VAR lost_customers =
        EXCEPT(prev_period_customer, current_period_customers)

    RETURN
        COUNTROWS(lost_customers)
    ```

<br>

---

<br>

### <ins>Display Folder - KPI_measures</ins>
*High-level performance indicators used for proactive monitoring. These measures quantify financial exposure and customer retention health.*

- Measure Name: **`revenue_at_risk`**
- Description: *Total financial value currently impacted by fulfillment delays exceeding the dynamic threshold.*
    ```dax
    VAR threshold = SELECTEDVALUE(delay_threshold_parameter[threshold_parameter], 3)

    VAR result = 
        CALCULATE(
            [total_revenue],
            FILTER(
                customer_weekly_fact,
                customer_weekly_fact[weekly_avg_delivery_delay] >= threshold
            )
        )

    RETURN
        IF(ISBLANK(result), 0, result)
    ```

<br>

- Measure Name: **`MoM_drop_off_rate`**
- Description: *The percentage of last month's active buyers who failed to return in the current month.*
    ```dax
    DIVIDE([MoM_drop_off_customers], [active_customer_prev_month], 0)
    ```

<br>

- Measure Name: **`cancellation_rate`**
- Description: *The ratio of cancelled orders to total order volume.*
    ```dax
    DIVIDE([total_cancelled], [total_order], 0)
    ```

<br>

---

<br>

### <ins>Display Folder - visual_measures</ins>
*Support measures designed for specific charts and UI elements, including weighted averages and conditional formatting logic.*

- Measure Name: **`weighted_avg_delivery_delay`**
- Description: *Volume-weighted average of delivery delays to ensure accuracy across segments with varying order counts.*
    ```dax
    DIVIDE(
        SUMX(customer_weekly_fact, 
        customer_weekly_fact[weekly_avg_delivery_delay] * customer_weekly_fact[weekly_order_count]),
        [total_order],
        0
    )
    ```

<br>

- Measure Name: **`weighted_avg_approval_lag`**
- Description: *Volume-weighted average of the time taken for order approval.*
    ```dax
    DIVIDE(
        SUMX(customer_weekly_fact, 
        customer_weekly_fact[weekly_avg_approval_lag] * customer_weekly_fact[weekly_order_count]),
        [total_order],
        0
    )
    ```

<br>

- Measure Name: **`weighted_avg_lead_time`**
- Description: *Volume-weighted average of total fulfillment duration (Creation to Delivery).*
    ```dax
    DIVIDE(
        SUMX(customer_weekly_fact,
        customer_weekly_fact[weekly_avg_lead_time] * customer_weekly_fact[weekly_order_count]),
        [total_order],
        0
    )
    ```

<br>

- Measure Name: **`bubble_size_sensitivity`**
- Description: *Scales scatter plot markers to highlight high-revenue segments experiencing extreme delays.*
    ```dax
    [revenue_at_risk] ^ 0.8
    ```

<br>

- Measure Name: **`color_format_revenue_at_risk`**
- Description: *Calculates the percentage of revenue at risk for conditional formatting rules.*
    ```dax
    DIVIDE([revenue_at_risk], [total_revenue])
    ```

<br>

- Measure Name: **`last_source_update`**
- Description: *Displays the most recent data sync timestamp from the BigQuery source.*
    ```dax
    MAX(source_last_update[Last_Update_Time])
    ```

<br>

---

<br>

### <ins>Display Folder - visual_measures_tooltip</ins>
*Context-specific measures optimized for on-hover interactivty, providing granular diagnostics and clean string formatting.*

- Measure Name: **`tooltip_revenue_at_risk`**
- Description: *Smart currency formatting (K/M) for revenue at risk in tooltips.*
    ```dax
    IF(
        [revenue_at_risk] < 1000000, 
        FORMAT([revenue_at_risk], "$#,##0, K"), 
        FORMAT([revenue_at_risk], "$#,##0,, M")
    )
    ```

<br>

- Measure Name: **`tooltip_avg_delivery_delay`**
- Description: *Formatted string for weighted average delivery delay.*
    ```dax
    CONCATENATE(
        FORMAT([weighted_avg_delivery_delay], "0.00"), 
        " Days"
    )
    ```

<br>

- Measure Name: **`tooltip_avg_approval_lag`**
- Description: *Formatted string for weighted average approval lag.*
    ```dax
    CONCATENATE(
        FORMAT([weighted_avg_approval_lag], "0.00"), 
        " Days"
    )
    ```

<br>

- Measure Name: **`tooltip_avg_lead_time`**
- Description: *Formatted string for weighted average lead time.*
    ```dax
    CONCATENATE(
        FORMAT([weighted_avg_lead_time], "0.00"), 
        " Days"
    )
    ```

<br>

- Measure Name: **`tooltip_MoM_drop_off_customer`**
- Description: *Formatted volume of dropped-off customers (K) for hover details.*
    ```dax
    IF(
        FORMAT([MoM_drop_off_customers], "0"), 
        FORMAT([MoM_drop_off_customers], "#,##0,.00 K")
    )
    ```

<br>

- Measure Name: **`tooltip_highlight_top_3`**
- Description: *Conditional formatting hex codes to highlight the top 3 states by revenue risk in bar chart tooltips.*
    ```dax
    VAR state_rank =
        RANKX(
            ALLSELECTED(customer_dim[customer_state]),
            [revenue_at_risk],
            ,
            DESC,
            Dense
        )
    RETURN
        IF(state_rank <= 3, "#5C86A8", "#999999")
    ```
