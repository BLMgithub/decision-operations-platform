# Operational Guide: Product Friction Monitor

## Strategic Intent
The **Product Friction Monitor** identifies physical and structural fulfillment bottlenecks caused by product specifications. This monitoring allows operations teams to intervene before delays impact customer satisfaction and revenue.

## Interface and Navigation
The dashboard uses an interactive interface for diagnostic review and sensitivity adjustment.

*   **Information Pane:** Click the **"i"** icon to view the performance legend and KPI definitions.
*   **Sensitivity Controls:** 
    *   **Slippage Threshold:** Adjust the minimum lead-time delay (0.5 to 5.0 days) required to trigger an alert.
    *   **Statistical Boundary:** Adjust the Standard Deviation multiplier (1.0 to 3.0) to modify the detection logic.
*   **Paging Controls:** Navigate the list of at-risk products using the "Page" and "Items per Page" (located in the Filter Pane) selectors.
*   **Closing Panes:** Click the **"X"** button on the pane or click the workspace background to return to the main view.

## KPI Thresholds
| KPI | Green (Stable) | Orange (Warning) | Red (Critical) |
| :--- | :--- | :--- | :--- |
| **Products at Risk** | 0 – 50 | 51 – 150 | > 150 |
| **Lead Time Volatility** | < 10% | 10% – 25% | > 25% |
| **Revenue at Risk** | < 5% of Total Revenue | 6% – 15% | > 15% |

## Decision Support
| Visual | Indicator | Recommended Action |
| :--- | :--- | :--- |
| **Lead Time Trend** | Rolling average increasing. | Investigate systemic slowdowns or carrier-wide issues. |
| **Weight Analysis** | Outliers clustering in high-weight categories. | Update shipping terms or route to specialized freight services. |
| **Revenue at Risk** | High revenue risk associated with specific suppliers. | Prioritize inventory audits for high-risk suppliers. |
| **Action List** | Product IDs with high statistical deviation (Z-Score). | Initiate direct follow-up with the supplier or courier. |

## Operational Workflow
1. **Performance Check:** Review core KPIs to assess overall network stability.
2. **Category Review:** Use the **Revenue at Risk Bar Chart** to identify specific product categories driving financial exposure.
3. **Friction Analysis:** Use the **Scatter Plot** to determine if delays are related to product weight or volume (e.g., oversize items).
4. **Targeted Follow-up:** Use the **Intervention Action List** to identify the exact Product IDs requiring attention.
