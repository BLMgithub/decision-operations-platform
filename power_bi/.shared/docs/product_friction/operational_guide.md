# Strategic & Operational Guide: Product Friction Monitor

## Strategic Intent
The **Product Friction Monitor** is an early-warning system designed to identify physical and structural fulfillment bottlenecks driven by product specifications. The proactive "friction" detection, allows operations teams to intervene before systemic delays impact customer satisfaction and revenue.

## Navigation & Interface Guide
The dashboard uses a "Head-Up Display" (HUD) style with interactive fly-out panes for a clean workspace.

*   **Information Pane :** Click the "i" icon in the top header to view the performance legend and KPI interpretation guides.
*   **Filter Pane :** Click the funnel icon to open the global controls.
    *   **Focus Views:** Toggle between **Top 10**, **Top 20**, or **All Products at Risk** to change the scope of the analysis.
    *   **Time Selection:** Select the specific Month and Year for historical review.
    *   **Action:** Click **Apply Filters** to update the dashboard.
*   **Closing Panes:** To return to the main view, click the **"X"** button on the pane or click anywhere in the darkened workspace background.

## Smoke Detector Configuration (KPI Thresholds)
| KPI | Green (Stable) | Orange (Warning) | Red (Critical) |
| :--- | :--- | :--- | :--- |
| **Products at Risk** | 0 – 50 | 51 – 150 | > 150 |
| **Lead Time Volatility** | < 10% | 10% – 25% | > 25% |
| **Revenue Exposure** | < $250K | $250K – $1M | > $1M |

## Decision Matrix
| Visual | Signal to Watch | Response Action |
| :--- | :--- | :--- |
| **Lead Time Trend** | Rolling average drifting upward. | Systemic slowdown; check for carrier-wide issues. |
| **Breaking Point Curve** | Outliers clustering above specific weights. | Update shipping terms; route to specialized freight. |
| **Revenue Exposure** | High revenue tied to Tier 3 suppliers. | High-risk cash flow; prioritize Tier 3 inventory audits. |
| **Action List** | Specific Product IDs with High Z-Scores. | Immediate intervention; contact supplier/courier. |


## Operational Workflow
1. **Daily Pulse:** Check **Network Stability** (Details via Info Pane) and the 3 core KPIs.
2. **Impact Check:** Use the **Bar Chart** to see if a specific Category (e.g., Electronics) is driving the Revenue Exposure.
3. **Root Cause:** Use the **Scatter Plot** to see if the friction is weight-driven (e.g., Oversize items).
4. **Execute:** Use the **Intervention Action List** to identify the specific Product IDs requiring follow-up.
