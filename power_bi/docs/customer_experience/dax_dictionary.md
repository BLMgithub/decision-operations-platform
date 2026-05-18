# DAX Data Dictionary: Customer Experience & Revenue Exposure

### Base Measures
*Foundational aggregations and counts used for period-over-period comparison and KPI calculation.*

- Measure Name: **`total_revenue`**
- Description: *Total revenue across all customer segments and regions.*
    ```dax
    SUM(customer_weekly_fact[weekly_revenue])
    ```

<br>

- Measure Name: **`total_order`**
- Description: *Total count of orders within the selected period.*
    ```dax
    SUM(customer_weekly_fact[weekly_order_count])
    ```

<br>

- Measure Name: **`total_delivered`**
- Description: *Count of successfully delivered orders.*
    ```dax
    SUM(customer_weekly_fact[weekly_delivered_orders])
    ```

<br>

- Measure Name: **`total_cancelled`**
- Description: *Total count of cancelled orders.*
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
- Description: *Distinct count of unique customers who placed an order in the previous calendar month.*
    ```dax
    CALCULATE(
        DISTINCTCOUNT(customer_weekly_fact[customer_id_int]),
        DATEADD(calendar_table[Date], -1, MONTH)
    )
    ```

<br>

- Measure Name: **`MoM_drop_off_customers`**
- Description: *Count of customers active in the previous month who have not placed an order in the current month.*
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

### KPI Measures
*Performance indicators used to track financial exposure and customer retention.*

- Measure Name: **`revenue_at_risk`**
- Description: *Total revenue associated with delivery delays exceeding the defined threshold.*
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
- Description: *Percentage of buyers from the previous month who did not return in the current month.*
    ```dax
    DIVIDE([MoM_drop_off_customers], [active_customer_prev_month], 0)
    ```

<br>

- Measure Name: **`cancellation_rate`**
- Description: *Ratio of cancelled orders to total order volume.*
    ```dax
    DIVIDE([total_cancelled], [total_order], 0)
    ```

<br>

---

<br>

### Visual and UI Measures
*Measures supporting visualizations, including weighted averages and conditional formatting logic.*

- Measure Name: **`weighted_avg_delivery_delay`**
- Description: *Volume-weighted average of delivery delays.*
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
- Description: *Volume-weighted average of order processing time (lag).*
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
- Description: *Volume-weighted average of total fulfillment duration.*
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
- Description: *Scales markers in the scatter plot visualization.*
    ```dax
    [revenue_at_risk] ^ 0.8
    ```

<br>

- Measure Name: **`color_format_revenue_at_risk`**
- Description: *Calculates the ratio of revenue at risk for conditional formatting rules.*
    ```dax
    DIVIDE([revenue_at_risk], [total_revenue])
    ```

<br>

- Measure Name: **`last_source_update`**
- Description: *Most recent data refresh timestamp from the BigQuery source.*
    ```dax
    MAX(source_last_update[Last_Update_Time])
    ```

<br>

---

<br>

### Tooltip Measures
*Measures optimized for on-hover interactivty and formatting.*

- Measure Name: **`tooltip_revenue_at_risk`**
- Description: *Currency formatting for revenue at risk in tooltips.*
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
- Description: *Formatted count of dropped-off customers.*
    ```dax
    IF(
        FORMAT([MoM_drop_off_customers], "0"), 
        FORMAT([MoM_drop_off_customers], "#,##0,.00 K")
    )
    ```

<br>

- Measure Name: **`tooltip_highlight_top_3`**
- Description: *Hex codes to highlight the top 3 states by revenue risk.*
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
