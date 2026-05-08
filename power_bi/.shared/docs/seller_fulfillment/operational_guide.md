# Strategic & Operational Guide: Fulfillment Decision Monitor

## Strategic Intent
The **Fulfillment Decision Monitor** is an operational "Smoke Detector" designed to identify logistics partners and sellers requiring immediate intervention. By focusing on statistical deviations rather than absolute failure, it allows teams to catch performance slippage early, preventing systemic delays before they impact the final customer.

## Navigation & Interface Guide
The dashboard utilizes an interactive "Head-Up Display" (HUD) with interactive fly-out panes for a clean workspace.

*   **Information Pane :** Click the "i" icon in the top header to view the performance legend and KPI interpretation guides.
*   **Filter Pane :** Click the funnel icon to open the global controls.
    *   **Focus Views:** Toggle between **Top 10**, **Top 20**, or **All Products at Risk** to change the scope of the analysis.
    *   **Time Selection:** Select the specific Month and Year for historical review.
    *   **Action:** Click **Apply Filters** to update the dashboard.
*   **Closing Panes:** To return to the main view, click the **"X"** button on the pane or click anywhere in the darkened workspace background.

## Smoke Detector Configuration (KPI Thresholds)
| KPI | Green (Stable) | Orange (Warning) | Red (Critical) |
| :--- | :--- | :--- | :--- |
| **Delivery Stability** | 0% – 10% | 11% – 25% | > 25% |
| **Network Slowdown** | 0% – 2% | 3% – 5% | > 5% |
| **Sellers at Risk** | 0 – 10 | 11 – 50 | > 50 |

## Decision Matrix
| Visual | Signal to Watch | Response Action |
| :--- | :--- | :--- |
| **Network Speed Trend** | Line ascending toward 0. | Systemic slowdown; check for carrier strikes or weather events. |
| **Lost Speed History** | Deep blue cells appearing for 3+ weeks. | Chronic failure; initiate Performance Improvement Plan (PIP). |
| **Delay Diagnostics** | Long "Warehouse Lag" bar. | Seller internal issue; audit warehouse staffing/processes. |
| **Priority Targeting** | Large dots in the Top-Right. | High-impact crisis; immediate call to high-volume partner. |
| **Action List** | Specific IDs with "Active" status. | Direct intervention; use Tooltip revenue to prioritize calls. |


## Operational Workflow
1.  **Check the Pulse:** Review the 3 core KPIs. If **Network Slowdown** is > 5%, the issue is systemic (Global).
2.  **Identify Outliers:** If **Sellers at Risk** is high but network slowdown is low, the issues are seller-specific.
3.  **Prioritize Impact:** Use the **Impact vs. Delay Mapping** scatter plot to find high-volume sellers with high slippage.
4.  **Execute Audit:** Select a seller from the **Operation Intervention List** and use the **Delay Diagnostics** to determine if the call should focus on their warehouse (Internal) or their courier (Logistics).
