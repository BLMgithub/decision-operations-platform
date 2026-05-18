# DAX Data Dictionary: Product Fulfillment Friction

### Paging and Navigation
*Measures supporting dynamic paging and ranking for large datasets.*

- Measure Name: **`item_rank`**
- Description: *Ranks products by revenue at risk (descending).*
    ```dax
    CALCULATE(
        RANKX(
            FILTER(
                ALL(product_dim[product_id_int]),
                [revenue_at_risk] > 0
            ),                
            [revenue_at_risk],
            ,
            DESC
        )
    )
    ```

<br>

- Measure Name: **`item_rank_filter`**
- Description: *Binary flag (1/0) identifying if a product's rank falls within the selected page and page size.*
    ```dax
    VAR _page = [paging_helper Value]
    VAR _page_size = [table_items Value]

    VAR item_rank = [item_rank]

    VAR _start = (_page - 1) * _page_size + 1
    VAR _end = _page * _page_size

    VAR is_in_range = 
        IF(
            item_rank >= _start && 
            item_rank <= _end, 
            1, 
            0
        )

    RETURN
        is_in_range
    ```

<br>

- Measure Name: **`max_page`**
- Description: *Calculates total pages based on the count of products at risk and the selected page size.*
    ```dax
    ROUNDUP(
        DIVIDE(VALUE([product_at_risk]), [table_items Value]), 
        0
    )
    ```

<br>

- Measure Name: **`current_viewed_filter`**
- Description: *Logic used to highlight products that are at risk and on the currently viewed page.*
    ```dax
    VAR _is_at_risk = [product_at_risk]
    VAR _is_on_page = [item_rank_filter]

    RETURN
    IF(
        _is_at_risk = 1 && _is_on_page = 1,
        "#5C86A8",
        "#999999"
    )
    ```

<br>

- Measure Name: **`page_filter`**
- Description: *Restricts the paging slicer to the available data range.*
    ```dax
    VAR _total_items = VALUE([product_at_risk])
    VAR items_per_page = [table_items Value]
    VAR max_page = 
        ROUNDUP(
            DIVIDE(_total_items, items_per_page),
            0
        )
    VAR _page_filter =
        IF(
            paging_helper[paging_helper Value] <= max_page,
            1, 0
        )
    RETURN
        _page_filter
    ```

<br>

### Base Measures
*Aggregations and counts used for temporal baselines and outlier detection.*

- Measure Name: **`total_orders`**
- Description: *Total count of order items within the selected period.*
    ```dax
    SUM(product_weekly_fact[weekly_order_count])
    ```

<br>

- Measure Name: **`avg_delivery_delay`**
- Description: *Average delivery delay in days.*
    ```dax
    AVERAGE(product_weekly_fact[weekly_avg_delivery_delay])
    ```

<br>

- Measure Name: **`total_cancelled`**
- Description: *Total volume of cancelled orders.*
    ```dax
    SUM(product_weekly_fact[weekly_cancelled_orders])
    ```

<br>

- Measure Name: **`total_revenue`**
- Description: *Gross revenue across all product categories.*
    ```dax
    SUM(product_weekly_fact[weekly_revenue])
    ```

<br>

- Measure Name: **`avg_lead_time`**
- Description: *Average duration from order creation to delivery.*
    ```dax
    AVERAGE(product_weekly_fact[weekly_avg_lead_time])
    ```

<br>

- Measure Name: **`current_lead_time`**
- Description: *Average lead time for the selected date.*
    ```dax
    CALCULATE([avg_lead_time], calendar_date[Date])
    ```

<br>

- Measure Name: **`lead_time_4w_rolling_avg`**
- Description: *Fulfillment performance baseline using a 28-day trailing window.*
    ```dax
    AVERAGEX(
        DATESINPERIOD('calendar_date'[Date], 
        LASTDATE('calendar_date'[Date]), -28, DAY),
        [avg_lead_time]
    )
    ```

<br>

- Measure Name: **`is_outlier`**
- Description: *Flags products where lead time exceeds the 28-day baseline + 1 StdDev and the delay is > 0.5 days.*
    ```dax
    VAR slippage_delta = [current_lead_time] - [lead_time_4w_rolling_avg] 
    VAR is_meaningful = IF(slippage_delta > 0.5, 1, 0)

    VAR _stddev = 
        CALCULATE(
            STDEV.S(product_weekly_fact[weekly_avg_lead_time]), 
            ALLEXCEPT(product_weekly_fact, product_weekly_fact[product_id_int])
        )

    VAR outlier_flags = 
        IF(
            is_meaningful = 1 && 
            [current_lead_time] > ([lead_time_4w_rolling_avg] + (1 * _stddev)), 
            1, 0
        ) 

    RETURN outlier_flags
    ```

<br>

- Measure Name: **`lead_time_slippage`**
- Description: *Quantifies lead-time delay in days for products identified as outliers.*
    ```dax
    VAR delta = [current_lead_time] - [lead_time_4w_rolling_avg] 
    RETURN 
        IF([is_outlier] = 1, delta, BLANK())
    ```

<br>

---

<br>

### KPI Measures
*Performance indicators used to track fulfillment friction and financial exposure.*

- Measure Name: `product_at_risk`
- Description: *Count of unique Product IDs identified as outliers.*
    ```dax
    COUNTROWS(
        FILTER(
            VALUES(product_dim[product_id_int]), 
            [is_outlier]=1
        )
    )
    ```

<br>

- Measure Name: `lead_time_volatility`
- Description: *Statistical measure of lead-time variability for at-risk products.*
    ```dax
    VAR at_risk_products = 
        FILTER(
            VALUES(product_dim[product_id_int]), 
            [is_outlier]=1
        ) 

    VAR result = 
        CALCULATE(
            STDEV.S(product_weekly_fact[weekly_avg_lead_time]), 
            at_risk_products
        ) 

    RETURN result
    ```

<br>

- Measure Name: `revenue_at_risk`
- Description: *Total revenue associated with fulfillment delays and outliers.*
    ```dax
    CALCULATE(
        [total_revenue], 
        FILTER(
            VALUES(product_dim[product_id_int]), 
            [is_outlier] = 1
        )
    )
    ```

<br>

---

<br>

### Visual and UI Measures
*Measures supporting specific charts and UI elements.*

- Measure Name: `product_weight`
- Description: *Weight (in grams) for the selected product.*
    ```dax
    LOOKUPVALUE(
        product_dim[product_weight_g], 
        product_dim[product_id_int], 
        MAX(product_weekly_fact[product_id_int])
    )
    ```

<br>

- Measure Name: `product_volume_categ`
- Description: *Weight-based classification (e.g., Small, Heavy) for grouping.*
    ```dax
    LOOKUPVALUE(
        product_dim[size_bucket], 
        product_dim[product_id_int], 
        MAX(product_weekly_fact[product_id_int])
    )
    ```

<br>

- Measure Name: `category_range_view`
- Description: *Calculates the Y-Axis range for the Category Revenue chart.*
    ```dax
    VAR highest_value = 
        MAXX(
            ALL(product_dim[product_category_name]), 
            [revenue_at_risk]
        ) 
    VAR adjustment = highest_value * 1.05 
    RETURN 
        adjustment
    ```

<br>

- Measure Name: `bubble_size_sensitivity`
- Description: *Scales markers in scatter plots based on revenue risk.*
    ```dax
    [revenue_at_risk] ^ 1.5
    ```

<br>

- Measure Name: `top_10_filter_color`
- Description: *Conditional formatting for the top 10 revenue-at-risk outliers.*
    ```dax
    VAR CurrentRank = 
        RANKX(
            ALLSELECTED(product_dim[product_id_int]), 
            [revenue_at_risk],
            ,
            DESC,
            Dense
            ) 

    RETURN 
        IF(CurrentRank <= 10, "#5C86A8", "#999999")
    ```

<br>

- Measure Name: `top_10_product_id`
- Description: *Visual filter enforcing a 10-row limit for the top outliers.*
    ```dax
    VAR _rank = 
        RANK(
            DENSE, 
            FILTER(
                ALLSELECTED(product_dim[product_id_int]), 
                [product_at_risk] = 1
                ), 
            ORDERBY([revenue_at_risk], DESC)
        ) 

    VAR _top_10 = 
        IF(
            _rank <= 10 && 
            [product_at_risk] = 1, 
            1, BLANK()
        ) 

    RETURN 
        _top_10
    ```

<br>

- Measure Name: `format_product_id_count`
- Description: *Formatted count of at-risk products for slicers.*
    ```dax
    VAR _distinct_count = [product_at_risk] 
    VAR format_count = 
        IF(_distinct_count < 1000, 
        FORMAT(_distinct_count, "0"), 
        FORMAT(_distinct_count, "#,000")
    ) 

    RETURN 
        format_count
    ```

<br>

- Measure Name: `format_total_orders`
- Description: *Formatted order volume (K/M) for display.*
    ```dax
    VAR order_at_risk = 
        CALCULATE([total_orders], 
        FILTER(
            VALUES(product_dim[product_id_int]), 
            [is_outlier] = 1)
        ) 
        
    VAR _format = 
        IF(
            order_at_risk < 1000, 
            FORMAT(order_at_risk, "0"), 
            FORMAT(order_at_risk, "#,##0,.00 K")
        ) 
        
    RETURN 
        _format
    ```

<br>

- Measure Name: `last_source_update`
- Description: *Timestamp of the most recent data sync.*
    ```dax
    MAX(source_last_update_time[Last_Update_Time])
    ```

<br>

---

<br>

### Tooltip Measures
*Measures optimized for formatting and tooltip interactivity.*

- Measure Name: `tooltip_format_revenue`
- Description: *Formatted revenue metrics for tooltips.*
    ```dax
    IF(
        [revenue_at_risk] < 1000000, 
        FORMAT([revenue_at_risk], "#,##0,.00 K"), 
        FORMAT([revenue_at_risk], "#,##0,,.00 M")
    )
    ```

<br>

- Measure Name: `tooltip_oversize`
- Description: *Count of outliers in the "Oversize" weight bucket.*
    ```dax
    COUNTROWS(
        FILTER(
            VALUES(product_dim), 
            product_dim[size_bucket] = "Oversize" &&
            [is_outlier] = 1
        )
    )
    ```

<br>

- Measure Name: `tooltip_heavy`
- Description: *Count of outliers in the "Heavy" weight bucket.*
    ```dax
    COUNTROWS(
        FILTER(
            VALUES(product_dim), 
            product_dim[size_bucket] = "Heavy" && 
            [is_outlier] = 1
            )
        )
    ```

<br>

- Measure Name: `tooltip_standard`
- Description: *Count of outliers in the "Standard" weight bucket.*
    ```dax
    COUNTROWS(FILTER(VALUES(product_dim), product_dim[size_bucket] = "Standard" && [is_outlier] = 1))
    ```

<br>

- Measure Name: `tooltip_small`
- Description: *Count of outliers in the "Small" weight bucket.*
    ```dax
    COUNTROWS(
            FILTER(
                VALUES(product_dim), 
                product_dim[size_bucket] = "Small" &&
                [is_outlier] = 1
            )
        )
    ```

<br>

- Measure Name: `tooltip_week_start`
- Description: *Week start date context for trend line tooltips.*
    ```dax
    SELECTEDVALUE(calendar_date[Week Start Date])
    ```

<br>

- Measure Name: `tooltip_product_id`
- Description: *Retrieves the Product ID for tooltip labels.*
    ```dax
    SELECTEDVALUE(product_dim[product_id_int])
    ```
