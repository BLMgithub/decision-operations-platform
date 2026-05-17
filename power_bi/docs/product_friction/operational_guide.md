# Strategic & Operational Guide: Product Friction Monitor

## Strategic Intent
The **Product Friction Monitor** is an early-warning system designed to identify physical and structural fulfillment bottlenecks driven by product specifications. The proactive "friction" detection, allows operations teams to intervene before systemic delays impact customer satisfaction and revenue.

## Navigation & Interface Guide
The dashboard utilizes an interactive "Head-Up Display" (HUD) architecture for rapid diagnostic review and **Dynamic Sensitivity Calibration**.

*   **Information Pane :** Click the "i" icon in the top header to view the performance legend and KPI interpretation guides.
*   **Sensitivity Controls (Slicer Pane):** 
    *   **Slippage Threshold:** Adjust the minimum "speed loss *in Lead Time*" (0.5 to 5.0 days) required to trigger an alert.
    *   **Statistical Boundary:** Adjust the Standard Deviation multiplier (1.0 to 3.0) to tighten or loosen the detection logic.
*   **Paging Controls:** Navigate large lists of at-risk products using the "Page" and "Items per Page" (Inside Filter Pane) selectors.
*   **Closing Panes:** To return to the main view, click the **"X"** button on the pane or click anywhere in the darkened workspace background.

## Smoke Detector Configuration (KPI Thresholds)
| KPI | Green (Stable) | Orange (Warning) | Red (Critical) |
| :--- | :--- | :--- | :--- |
| **Products at Risk** | 0 – 50 | 51 – 150 | > 150 |
| **Lead Time Volatility** | < 10% | 10% – 25% | > 25% |
| **Revenue at Risk** | < 5% of Total Revenue | 6% – 15% | > 15% |

## Decision Matrix
| Visual | Signal to Watch | Response Action |
| :--- | :--- | :--- |
| **Lead Time Trend** | Rolling average drifting upward. | Systemic slowdown; check for carrier-wide issues. |
| **Breaking Point Curve** | Outliers clustering above specific weights. | Update shipping terms; route to specialized freight. |
| **Revenue at Risk** | High revenue tied to Tier 3 suppliers. | High-risk cash flow; prioritize Tier 3 inventory audits. |
| **Action List** | Specific Product IDs with High Z-Scores. | Immediate intervention; contact supplier/courier. |


## Operational Workflow
1. **Daily Pulse:** Check **Network Stability** (Details via Info Pane) and the 3 core KPIs.
2. **Impact Check:** Use the **Bar Chart** to see if a specific Category (e.g., Electronics) is driving the Revenue at Risk.
3. **Root Cause:** Use the **Scatter Plot** to see if the friction is weight-driven (e.g., Oversize items).
4. **Execute:** Use the **Intervention Action List** to identify the specific Product IDs requiring follow-up.
