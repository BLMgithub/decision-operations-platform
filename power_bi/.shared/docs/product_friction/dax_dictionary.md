# DAX Data Dictionary: Product Fulfillment Friction Dashboard

### <ins>Display Folder - Prerequisites Measures</ins>
*Fundamental building blocks and base aggregations required for higher-level logic. This section includes primary counts, temporal baselines, and the core outlier detection engine.*

- Measure Name: **`total_orders`**
- Description: *Aggregate count of order items within the filtered period.*
    ```dax
    SUM(product_weekly_fact[weekly_order_count])
    ```

<br>

- Measure Name: **`avg_delivery_delay`**
- Description: *Mean days of delay for delivered orders; negative values indicate early delivery.*
    ```dax
    AVERAGE(product_weekly_fact[weekly_avg_delivery_delay])
    ```

<br>

- Measure Name: **`total_cancelled`**
- Description: *Aggregate volume of orders cancelled during the reporting week.*
    ```dax
    SUM(product_weekly_fact[weekly_cancelled_orders])
    ```

<br>

- Measure Name: **`total_revenue`**
- Description: *Gross revenue generated across all product categories.*
    ```dax
    SUM(product_weekly_fact[weekly_revenue])
    ```

<br>

- Measure Name: **`avg_lead_time`**
- Description: *Mean duration from order creation to final delivery.*
    ```dax
    AVERAGE(product_weekly_fact[weekly_avg_lead_time])
    ```

<br>

- Measure Name: **`current_lead_time`**
- Description: *Context-aware lead time for the specific date selection in visual filters.*
    ```dax
    CALCULATE([avg_lead_time], calendar_date[Date])
    ```

<br>

- Measure Name: **`lead_time_4w_rolling_avg`**
- Description: *Smoothed fulfillment performance baseline using a 28-day trailing window.*
    ```dax
    AVERAGEX(
        DATESINPERIOD('calendar_date'[Date], 
        LASTDATE('calendar_date'[Date]), -28, DAY),
        [avg_lead_time]
    )
    ```

<br>

- Measure Name: **`is_outlier`**
- Description: *Core "Smoke Detector" logic; flags products where current lead time exceeds the 4-week baseline + 1 StdDev.*
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
- Description: *Calculates the lead time "Gap" only for products currently flagged as outliers.*
    ```dax
    VAR delta = [current_lead_time] - [lead_time_4w_rolling_avg] 
    RETURN 
        IF([is_outlier] = 1, delta, BLANK())
    ```

<br>

---

<br>

### <ins>Display Folder - KPI Measures</ins>
*High-level performance indicators used in cards and executive summaries. These measures quantify the scale of friction by aggregating risk across products and revenue.*

- Measure Name: `product_at_risk`
- Description: *Count of unique Product IDs currently flagged by the outlier detection logic.*
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
- Description: *Statistical unpredictability (StdDev) restricted only to the subset of at-risk products.*
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
- Description: *Total financial value currently impacted by fulfillment friction and outliers.*
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

### <ins>Display Folder - Visual Measures</ins>
*Support measures designed for specific charts and UI elements. This includes conditional formatting logic, dynamic axis scaling, and ranking filters for top-impact visuals.*

- Measure Name: `product_weight`
- Description: *Retrieves the static gram weight for the current product in the visual context.*
    ```dax
    LOOKUPVALUE(
        product_dim[product_weight_g], 
        product_dim[product_id_int], 
        MAX(product_weekly_fact[product_id_int])
    )
    ```

<br>

- Measure Name: `product_volume_categ`
- Description: *Retrieves the weight-based classification (Small, Heavy, etc.) for categorical grouping.*
    ```dax
    LOOKUPVALUE(
        product_dim[size_bucket], 
        product_dim[product_id_int], 
        MAX(product_weekly_fact[product_id_int])
    )
    ```

<br>

- Measure Name: `category_range_view`
- Description: *Dynamic Y-Axis buffer calculation for the Category Revenue bar chart.*
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
- Description: *Exponentially scales marker sizes in scatter plots to enhance visibility of high-impact outliers.*
    ```dax
    [revenue_at_risk] ^ 1.5
    ```

<br>

- Measure Name: `top_10_filter_color`
- Description: *Conditional formatting hex codes for highlighting the Top 10 revenue-at-risk outliers.*
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

- Measure Name: `top_20_filter_color`
- Description: *Conditional formatting hex codes for highlighting the Top 20 revenue-at-risk outliers.*
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
        IF(CurrentRank <= 20, "#5C86A8", "#999999")
    ```

<br>

- Measure Name: `top_10_product_id`
- Description: *Visual-level filter logic that enforces a strict 10-row limit regardless of ranking ties.*
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

- Measure Name: `top_20_product_id`
- Description: *Visual-level filter logic that enforces a strict 20-row limit regardless of ranking ties.*
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
        
    VAR _top_20 = 
        IF(
            _rank <= 20 && 
            [product_at_risk] = 1, 
            1, BLANK()
        ) 

    RETURN 
        _top_20
    ```

<br>

- Measure Name: `format_product_id_count`
- Description: *String-formatted count of at-risk products for use in text-based slicers.*
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
- Description: *Smart-formatted order volume (K/M) for clean label display.*
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
- Description: *Displays the most recent data sync timestamp from the BigQuery source.*
    ```dax
    MAX(source_last_update_time[Last_Update_Time])
    ```

<br>

---

<br>

### <ins>Display Folder: Tooltip Visual Measures</ins>
*Context-specific measures optimized for tooltips. These provide granular details, such as segment breakdowns by weight bucket and formatted currency values, to enhance on-hover interactivity.*

- Measure Name: `tooltip_format_revenue`
- Description: Precision formatting for revenue metrics specifically for hover-over details.
    ```dax
    IF(
        [revenue_at_risk] < 1000000, 
        FORMAT([revenue_at_risk], "#,##0,.00 K"), 
        FORMAT([revenue_at_risk], "#,##0,,.00 M")
    )
    ```

<br>

- Measure Name: `tooltip_oversize`
- Description: *Count of outliers within the "Oversize" weight bucket for tooltip summaries.*
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
- Description: *Count of outliers within the "Heavy" weight bucket for tooltip summaries.*
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
- Description: *Count of outliers within the "Standard" weight bucket for tooltip summaries.*
    ```dax
    COUNTROWS(FILTER(VALUES(product_dim), product_dim[size_bucket] = "Standard" && [is_outlier] = 1))
    ```

<br>

- Measure Name: `tooltip_small`
- Description: *Count of outliers within the "Small" weight bucket for tooltip summaries.*
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
- Description: *Provides the specific week start date context during bar/line hover.*
    ```dax
    SELECTEDVALUE(calendar_date[Week Start Date])
    ```

<br>

- Measure Name: `tooltip_product_id`
- Description: *Displays the specific Product ID associated with a scatter plot data point.*
    ```dax
    SELECTEDVALUE(product_dim[product_id_int])
    ```