# Operational Guide: Fulfillment Decision Monitor

## Strategic Intent
The **Fulfillment Decision Monitor** identifies logistics partners and sellers requiring immediate attention. By focusing on statistical deviations in performance, it allows teams to identify delays early and intervene before they impact customers.

## Interface and Navigation
The dashboard uses an interactive interface for diagnostic review and sensitivity adjustment.

*   **Information Pane:** Click the **"i"** icon to view the performance legend and KPI definitions.
*   **Sensitivity Controls:** 
    *   **Slippage Threshold:** Adjust the minimum delivery delay (0.5 to 3.0 days) required to trigger an alert.
    *   **Statistical Boundary:** Adjust the Standard Deviation multiplier (1.0 to 3.0) to modify the detection logic.
*   **Paging Controls:** Navigate the list of at-risk sellers using the "Page" and "Items per Page" (located in the Filter Pane) selectors.
*   **Closing Panes:** Click the **"X"** button on the pane or click the workspace background to return to the main view.

## KPI Thresholds
| KPI | Green (Stable) | Orange (Warning) | Red (Critical) |
| :--- | :--- | :--- | :--- |
| **Delivery Stability** | 0% – 10% | 11% – 25% | > 25% |
| **Network Slowdown** | 0% – 2% | 3% – 5% | > 5% |
| **Sellers at Risk** | 0 – 10 | 11 – 50 | > 50 |

## Decision Support
| Visual | Indicator | Recommended Action |
| :--- | :--- | :--- |
| **Network Speed Trend** | Increasing trend line. | Assess for systemic issues such as carrier disruptions or regional events. |
| **Lost Speed History** | Consistent high-delay markers for 3+ weeks. | Address chronic performance failures with the partner. |
| **Delay Diagnostics** | Long "Warehouse Lag" bar. | Investigate seller internal issues, such as warehouse staffing or processes. |
| **Priority Targeting** | Large markers in the top-right quadrant. | Prioritize high-impact partners for immediate review. |
| **Action List** | IDs with "Active" status. | Use revenue impact tooltips to prioritize direct intervention. |

## Operational Workflow
1. **Performance Check:** Review core KPIs. A high **Network Slowdown** indicates a systemic issue.
2. **Outlier Identification:** If **Sellers at Risk** is high but network slowdown is low, the issues are likely seller-specific.
3. **Impact Prioritization:** Use the **Impact vs. Delay** scatter plot to identify high-volume sellers with significant delays.
4. **Root Cause Audit:** Select a seller from the **Operation Intervention List** and use **Delay Diagnostics** to determine if the issue is internal (warehouse) or logistical (courier).
