# Strategic & Operational Guide: Customer Experience & Revenue Exposure

## Strategic Intent
The **Customer Experience & Revenue Exposure** dashboard is a decision-support system designed to monitor financial risk driven by fulfillment failures. By correlating delivery delays with buyer drop-off rates and cancellations, it allows leadership to quantify the "cost of friction" and prioritize interventions in high-value segments or regions.

## Navigation & Interface Guide
The dashboard uses a "Head-Up Display" (HUD) style with interactive fly-out panes for a clean workspace.

*   **Information Pane:** Click the "i" icon in the top header to view the performance legend and KPI interpretation guides.
*   **Filter Pane:** Click the funnel icon to open global controls.
    *   **Threshold Control:** Use the **Delay Threshold Parameter** to define what constitutes a "Danger Zone" (Default: 3 Days).
    *   **Time Selection:** Select the specific Month and Year for historical review.
    *   **Action:** Click **Apply Filters** to update the dashboard.
*   **Closing Panes:** To return to the main view, click the **"X"** button on the pane or click anywhere in the darkened workspace background.

## Smoke Detector Configuration (KPI Thresholds)
| KPI | Green (Natural) | Orange (Alarming) | Red (Critical) |
| :--- | :--- | :--- | :--- |
| **Revenue at Risk** | < 5% of Total Revenue | 6% – 15% | > 15% |
| **MoM Buyer Drop-off** | < 15% | 16% – 30% | > 30% |
| **Cancellation Rate** | < 2% | 3% – 5% | > 5% |

## Decision Matrix
| Visual | Signal to Watch | Response Action |
| :--- | :--- | :--- |
| **Active Buyer Trend** | Widening gap between current and previous month lines. | Identifying mass abandonment; trigger LTV recovery strategy. |
| **Segment Health Matrix** | High-revenue segments (e.g., D2C) drifting right (higher delay). | Critical revenue threat; investigate segment-specific fulfillment hubs. |
| **Danger Zone Breakdown** | Heavy concentration in "5+ Days Late" bracket. | Systemic failure; escalate for carrier reallocation or capacity audit. |
| **Geographic Risk** | High revenue exposure concentrated in specific States. | Regional bottleneck; check for local warehouse or courier disruptions. |

## Operational Workflow
1. **Daily Pulse:** Check the 3 core KPIs to identify if the system is within healthy baselines.
2. **Exposure Analysis:** Use the **Severity Exposure** bar chart to see if delays are escalating or clearing.
3. **Segment Prioritization:** Use the **Segment Health** scatter plot to identify which customer group (SMB, D2C, Enterprise) requires immediate communication.
4. **Regional Deep-Dive:** Use the **Geographic Risk** bar chart and its city-level tooltips to pinpoint the exact failure hub.
