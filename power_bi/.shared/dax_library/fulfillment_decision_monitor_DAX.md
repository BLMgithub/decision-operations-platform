# DAX Documentation: Fulfillment Decision Monitor

Technical document reference for the proactive "Smoke Detector" measures implemented in the [`fulfillment_decision_monitor`](../../releases/ ### To be Filled) dashboard.

## 1. Prerequisites & Base Measures
These measures form the foundation for performance tracking but are generally hidden from the main report UI.

### latency
Basic average of the delivery delay (Estimated vs. Actual).
```dax
latency = AVERAGE(seller_weekly_fact[weekly_avg_delivery_delay])
```

### latency_current_week
Retrieves the latency for the most recent week in the current filter context.
```dax
latency_current_week = 
VAR max_date = MAX(seller_weekly_fact[week_start_date])
RETURN
    CALCULATE([latency], calendar_dates[Date])
```

### latency_4w_rolling_avg
Smooths out weekly noise to establish the "Baseline Health" of the supply chain.
```dax
latency_4w_rolling_avg = 
AVERAGEX(
    DATESINPERIOD('calendar_dates'[Date], LASTDATE('calendar_dates'[Date]), -28, DAY),
    [latency]
)
```

---

## 2. Core KPIs (Fulfillment Health Pulse)

### Delivery Stability (Instability Index)
Measures how unpredictable the network is. High instability indicates that delivery dates are becoming inconsistent.
```dax
fulfillment_instability_index = 
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

### Network Slowdown (Systemic Drift %)
Measures the percentage of total order volume currently losing speed compared to the 4-week baseline.
```dax
systemic_drift_pct = 
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

### Sellers at Risk (Outlier Count)
Counts unique sellers who have deviated significantly from their personal performance history.
```dax
seller_at_risk = 
COUNTROWS(
    FILTER(
        VALUES(seller_weekly_fact[seller_id_int]),
        [is_outlier] = 1
    )
)
```

---

## 3. Statistical Detection Logic

### is_outlier
The central "Gatekeeper" logic. Flags a seller if their slippage is > 0.5 days AND they are > 1 standard deviation from their historical mean.
```dax
is_outlier = 
VAR current_latency = [latency_current_week]
VAR _4w_avg_latency = [latency_4w_rolling_avg]
VAR current_year = SELECTEDVALUE(calendar_dates[Year])
VAR is_valid_year = IF(current_year > 2022, TRUE(), FALSE())

VAR slippage_delta = current_latency - _4w_avg_latency
VAR is_meaningful = IF(slippage_delta > 0.5, 1, 0)

VAR _stdev =
    CALCULATE(
        STDEVX.S(seller_weekly_fact, seller_weekly_fact[weekly_avg_delivery_delay]),
        KEEPFILTERS(calendar_dates[Year] > 2022),
        ALLEXCEPT(seller_weekly_fact, seller_weekly_fact[seller_id_int])
    )

RETURN
    IF(is_meaningful && is_valid_year && current_latency > (_4w_avg_latency + (1 * _stdev)), 1, 0)
```

### latency_slippage
Quantifies the exact "speed loss" for flagged sellers.
```dax
latency_slippage = 
VAR delta = [latency_current_week] - [latency_4w_rolling_avg]
RETURN
    IF([is_outlier] = 1, delta, BLANK())
```

---

## 4. Diagnostic & Visual Measures

### Logistics Delay vs. Internal Delay
Isolates if a failure is caused by the Courier or the Warehouse.
```dax
logistics_delay = 
VAR total_delay = [latency_current_week]
VAR result = total_delay - [internal_delay]
RETURN
    IF([seller_at_risk] > 0, result, BLANK())

internal_delay = 
VAR result = AVERAGE(seller_weekly_fact[weekly_avg_approval_lag])
RETURN
    IF([seller_at_risk] > 0, result, BLANK())
```

### matrix_slippage_tracker
Ensures sellers remain visible in the Heatmap even if they weren't outliers in every specific week shown.
```dax
matrix_slippage_tracker = 
VAR global_flag = CALCULATE([is_outlier], ALLSELECTED(calendar_dates))
VAR cell_slippage = [latency_current_week] - [latency_4w_rolling_avg]
RETURN
    IF(global_flag = 1 && cell_slippage > 0, cell_slippage, BLANK())
```
