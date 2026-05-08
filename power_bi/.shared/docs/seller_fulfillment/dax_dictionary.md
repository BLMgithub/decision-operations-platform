# DAX Data Dictionary: Fulfillment Decision Monitor Dashboard

### <ins>Display Folder - Prerequisites Measures</ins>
*Fundamental building blocks and base aggregations required for higher-level logic. This section includes primary counts, temporal baselines, and the core outlier detection engine.*

- Measure Name: **`latency`**
- Description: *Basic average of the delivery delay (Estimated vs. Actual delivery dates).*
    ```dax
    AVERAGE(seller_weekly_fact[weekly_avg_delivery_delay])
    ```

<br>

- Measure Name: **`latency_current_week`**
- Description: *Retrieves the average latency for the most recent week in the current filter context.*
    ```dax
    CALCULATE([latency], calendar_dates[Date])
    ```

<br>

- Measure Name: **`latency_previous_week`**
- Description: *Retrieves the latency from exactly seven days prior to the current selection for trend analysis.*
    ```dax
    CALCULATE(
        [latency],
        DATEADD('calendar_dates'[Date], -7, DAY)
    )
    ```

<br>

- Measure Name: **`latency_4w_rolling_avg`**
- Description: *Smoothed fulfillment performance baseline using a 28-day trailing window to establish "Normal" behavior.*
    ```dax
    AVERAGEX(
        DATESINPERIOD('calendar_dates'[Date], 
        LASTDATE('calendar_dates'[Date]), -28, DAY),
        [latency]
    )
    ```

<br>

- Measure Name: **`is_outlier`**
- Description: *Core "Smoke Detector" logic; flags sellers where current latency exceeds the 4-week baseline + 1 StdDev and the slip is > 0.5 days.*
    ```dax
    VAR current_latency = [latency_current_week]
    VAR _4w_avg_latency = [latency_4w_rolling_avg]
    VAR current_year = SELECTEDVALUE(calendar_dates[Year])
    VAR is_valid_year = IF(current_year > 2022, TRUE(), FALSE())

     VAR slippage_delta = current_latency - _4w_avg_latency
    VAR is_meaningful = IF(slippage_delta > 0.5, 1, 0)

    VAR _stdev=
        CALCULATE(
            STDEVX.S(
                seller_weekly_fact,
                seller_weekly_fact[weekly_avg_delivery_delay]
            ),
            KEEPFILTERS(calendar_dates[Year] > 2022),
            ALLEXCEPT(seller_weekly_fact, seller_weekly_fact[seller_id_int])
        )

    VAR outlier_flags =
        IF(
            is_meaningful &&
            is_valid_year &&
            current_latency > (_4w_avg_latency + (1 * _stdev)),
         1, 0
         )

    RETURN
        outlier_flags
    ```

<br>

- Measure Name: **`matrix_slippage_tracker`**
- Description: *Ensures sellers remain visible in history heatmaps if they are outliers in the current global selection.*
    ```dax
    VAR global_flag = [is_outlier_global]
    VAR cell_slippage = [latency_current_week] - [latency_4w_rolling_avg]
    VAR result = 
        IF(
            global_flag = 1 &&
            cell_slippage > 0,
            cell_slippage,
            BLANK()
        )
    RETURN
        result
    ```

<br>

- Measure Name: **`internal_delay`**
- Description: *Calculates the average time taken by sellers to approve/process orders (Warehouse Lag).*
    ```dax
    VAR result = AVERAGE(seller_weekly_fact[weekly_avg_approval_lag])
    RETURN
        IF([seller_at_risk] > 0, result, BLANK())
    ```
<br>

- Measure Name: **`logistics_delay`**
- Description: *Isolates the courier's portion of the delay by removing internal warehouse processing time.*
    ```dax
    VAR total_delay = [latency_current_week]
    VAR result = total_delay - [internal_delay]
    RETURN
        IF([seller_at_risk] > 0, result, BLANK())
    ```

<br>

- Measure Name: **`latency_slippage`**
- Description: *Quantifies the exact "speed loss" in days only for sellers currently flagged as outliers.*
    ```dax
    VAR delta = [latency_current_week] - [latency_4w_rolling_avg]
    RETURN
        IF([is_outlier] = 1, delta, BLANK())
    ```

<br>

- Measure Name: **`total_order_volume`**
- Description: *Aggregate count of all order items across the filtered dataset.*
    ```dax
    SUM(seller_weekly_fact[weekly_order_count])
    ```

<br>

---

<br>

### Display Folder - <ins>KPI Measures</ins>
*High-level performance indicators used in cards and executive summaries. These measures quantify systemic health and the scale of active bottlenecks.*

- Measure Name: **`seller_at_risk`**
- Description: *Count of unique Seller IDs currently flagged by the outlier detection logic.*
    ```dax
    COUNTROWS(
        FILTER(
            VALUES(seller_weekly_fact[seller_id_int]),
            [is_outlier] = 1
        )
    )
    ```

<br>

- Measure Name: **`systemic_drift_pct`** (Network Slowdown)
- Description: *Percentage of total order volume currently losing speed compared to the 4-week baseline.*
    ```dax
    VAR _slipping_vol =
        SUMX(
            VALUES(calendar_dates[Week Start Date]),
            CALCULATE(
                [total_order_volume],
                FILTER(VALUES(seller_weekly_fact[seller_id_int]), [latency_slippage] > 0)
            )
        )
    RETURN
        DIVIDE(_slipping_vol, [total_order_volume], 0)
    ```

<br>

- Measure Name: **`fulfillment_instability_index`** (Delivery Stability)
- Description: *Measures statistical unpredictability; high values indicate delivery dates are becoming inconsistent.*
    ```dax
    VAR _4w_avg_latency = [latency_4w_rolling_avg]
    VAR _stddev =
        CALCULATE(
            STDEVX.S(seller_weekly_fact, seller_weekly_fact[weekly_avg_delivery_delay]),
            KEEPFILTERS(calendar_dates[Year] > 2022)
        )
    VAR result = DIVIDE(_stddev, ABS(_4w_avg_latency), 0 )
    RETURN
        IF([seller_at_risk] > 0, result, BLANK())
    ```

<br>

---

<br>

### <ins>Display Folder - Visual Measures</ins>
*Support measures designed for specific charts and UI elements, including diagnostic isolation, ranking, and conditional formatting.*

- Measure Name: **`top_10_filter_color`**
- Description: *Conditional formatting hex codes for highlighting top 10 impact outliers in visuals.*
    ```dax
    VAR CurrentRank = 
        RANKX(
            ALLSELECTED('seller_dim'[seller_id_int]),
            [latency_slippage],
            ,
            DESC,
            Dense
        )
    RETURN 
        IF(CurrentRank <= 10, "#5C86A8", "#999999")
    ```

<br>

- Measure Name: **`top_20_filter_color`**
- Description: *Conditional formatting hex codes for highlighting top 20 impact outliers in visuals.*
    ```dax
    VAR CurrentRank = 
        RANKX(
            ALLSELECTED('seller_dim'[seller_id_int]),
            [latency_slippage],
            ,
            DESC,
            Dense
        )
    RETURN 
        IF(CurrentRank <= 20, "#5C86A8", "#999999")
    ```

<br>

- Measure Name: **`is_new_seller`**
- Description: *Flags sellers in their first 30 days of operation to provide onboarding context.*
    ```dax
    VAR first_order = SELECTEDVALUE(seller_dim[first_order_date])
    VAR current_date = MAX(calendar_dates[Date])

    RETURN
        IF(
            DATEDIFF(first_order, current_date, DAY) <= 30,
            "Yes", "No"
        )
    ```

<br>

- Measure Name: **`last_source_update`**
- Description: *Displays the most recent data sync timestamp from the source metadata.*
    ```dax
    MAX(source_last_update_time[Last_Update_Time])
    ```

<br>

- Measure Name: **`top_10_seller_id`**
- Description: *Visual-level filter logic that enforces a strict 10-row limit for intervention lists.*
    ```dax
    VAR _rank = 
        RANK(
            DENSE,
            FILTER(
                ALLSELECTED('seller_dim'[seller_id_int]),
                [seller_at_risk] = 1
                ),
            ORDERBY([latency_slippage], 
            DESC)
        )

    VAR _top_10 = 
        IF(
            _rank <= 10 
            && [seller_at_risk] = 1, 
            1, BLANK()
        )

    RETURN
        _top_10
    ```

<br>

- Measure Name: **`top_20_seller_id`**
- Description: *Visual-level filter logic that enforces a strict 20-row limit for intervention lists.*
    ```dax
    VAR _rank = 
        RANK(
            DENSE,
            FILTER(
                ALLSELECTED('seller_dim'[seller_id_int]),
                [seller_at_risk] = 1
                ),
            ORDERBY([latency_slippage], 
            DESC)
        )

    VAR _top_10 = 
        IF(
            _rank <= 20 
            && [seller_at_risk] = 1, 
            1, BLANK()
        )

    RETURN
        _top_10
    ```

<br>

- Measure Name: **`bubble_size_sensivity`**
- Description: *Exponentially scales scatter plot markers to improve visual differentiation of high-slippage sellers.*
    ```dax
    [latency_slippage] ^ 4.5
    ```

<br>

- Measure Name: **`is_outlier_global`**
- Description: *Calculates outlier status ignoring local visual date filters to support matrix row persistence.*
    ```dax
    CALCULATE(
        [is_outlier],
        ALLSELECTED(calendar_dates)
    )
    ```

<br>

---

<br>

### <ins>Display Folder -Tooltip Visual Measures</ins>
*Context-specific measures optimized for tooltips to provide granular impact details without cluttering the primary UI.*

- Measure Name: **`tooltip_revenue_exposed`**
- Description: *Total financial value currently handled by sellers flagged as outliers.*
    ```dax
    VAR result = 
    SUMX(
        VALUES(calendar_dates[Week Start Date]),
        CALCULATE(
            SUM(seller_weekly_fact[weekly_revenue]),
            KEEPFILTERS(
                FILTER(
                    VALUES(seller_weekly_fact[seller_id_int]),
                    [is_outlier] = 1 
                )
            )
        )
    )
    RETURN COALESCE(result, 0)
    ```

<br>

- Measure Name: **`tooltip_week_start_date`**
- Description: *Provides specific week context during hover-over analysis on trend lines.*
    ```dax
    SELECTEDVALUE(calendar_dates[Week Start Date])
    ```
<br>

- Measure Name: **`tooltip_is_new_seller`**
- Description: *Tooltip-specific flag to identify new sellers during hover-over diagnostics.*
    ```dax
    VAR first_order = SELECTEDVALUE(seller_dim[first_order_date])
    VAR current_date = MAX(calendar_dates[Date])

    RETURN
        IF(
            DATEDIFF(first_order, current_date, DAY) <= 30,
            "Yes", "No"
        )
    ```

<br>

- Measure Name: **`tooltip_seller_id`**
- Description: *Retrieves the specific Seller ID in context for detailed tooltip labels.*
    ```dax
    SELECTEDVALUE(seller_dim[seller_id_int])
    ```
