# AI Assistant Test Queries for Renewable Energy Asset Management

## Test Queries for Underperformance Analysis

### 1. Basic Underperformance Query
**Query:** "Give me the 3 most underperforming sites"

**Expected Response:**
- Top 3 sites ranked by R-squared (lowest first)
- Each site shows: R², RMSE, Revenue Impact, Status (CRITICAL/WARNING/MONITOR)
- Portfolio insights with average metrics
- Actionable recommendations

### 2. RMSE-Specific Query
**Query:** "Which sites have RMSE above 2.0 MW?"

**Expected Response:**
- List of sites with RMSE > 2.0 MW
- Sorted by RMSE (highest first)
- Financial impact calculations
- Root cause analysis for each site

### 3. R-Squared Threshold Query
**Query:** "Show me sites with less than 80% R-squared"

**Expected Response:**
- Sites with R² < 0.8
- Alert levels (WARNING or CRITICAL)
- Specific interventions recommended
- ROI estimates for improvements

### 4. Financial Impact Query
**Query:** "What's the financial impact of our worst performers?"

**Expected Response:**
- Top underperforming sites with revenue impact
- Monthly and annualized revenue loss
- Total portfolio revenue at risk
- Cost recovery recommendations

### 5. Comparative Analysis Query
**Query:** "Compare Q3 vs Q4 performance"

**Expected Response:**
- Quarter-over-quarter comparison
- Performance trend analysis
- Sites with improving/declining performance
- Seasonal patterns identified

### 6. Immediate Attention Query
**Query:** "Which sites need immediate attention?"

**Expected Response:**
- CRITICAL status sites (R² < 0.7)
- Prioritized action list
- Estimated downtime costs
- Emergency response recommendations

## Example Response Format

When user asks: "Give me the 3 most underperforming sites"

```markdown
🎯 **TOP 3 UNDERPERFORMING SITES**
*Analysis Period: Last 30 days*

**1. Assembly 2** - 🚨 CRITICAL
   • R²: 0.652 | RMSE: 3.45 MW
   • Revenue Impact: $124,200/month
   • Root Cause: Severe underperformance - possible equipment failure or degradation

**2. Highland** - ⚠️ WARNING
   • R²: 0.743 | RMSE: 2.78 MW
   • Revenue Impact: $100,080/month
   • Root Cause: Significant deviation - check for controller issues or shading

**3. Big River** - ⚠️ WARNING
   • R²: 0.789 | RMSE: 2.12 MW
   • Revenue Impact: $76,320/month
   • Root Cause: Significant deviation - check for controller issues or shading

💡 **PORTFOLIO INSIGHTS:**
• Total Sites Analyzed: 12
• Average R²: 0.821
• Total Revenue at Risk: $300,600/month
• Sites Below Target (R² < 0.8): 3

📋 **RECOMMENDED ACTIONS:**
1. Immediate inspection required for critical sites
2. Consider O&M contract review for cost recovery
3. Focus on top 3 underperforming sites for maximum ROI
```

## Visualization Support

The AI Assistant supports these chart types:
- **performance_metrics**: R² vs RMSE scatter plot with sites
- **financial_impact**: Horizontal bar chart of revenue impact
- **scatter**: POA irradiance vs actual power
- **bar**: Component performance comparison
- **multi-scatter**: Multiple series comparison

## Alert Level Definitions

- 🚨 **CRITICAL**: R² < 0.7 or RMSE > 3.0 MW - Immediate action required
- ⚠️ **WARNING**: R² < 0.8 or RMSE > 2.0 MW - Scheduled maintenance needed
- 📌 **MONITOR**: R² < 0.9 or RMSE > 1.5 MW - Keep under observation
- ✅ **GOOD**: R² ≥ 0.9 and RMSE ≤ 1.5 MW - Operating normally

## Root Cause Categories

1. **Equipment Degradation**: Module degradation, inverter efficiency loss
2. **Controller Issues**: Power plant controller not optimizing, curtailment problems
3. **Reactive Power**: VAR requirements affecting active power output
4. **Shading/Soiling**: Environmental factors reducing irradiance
5. **Communication Failures**: Data gaps, stuck sensors, SCADA issues

## Financial Calculations

```
Monthly Revenue Impact = RMSE (MW) × Operational Hours (720) × PPA Rate ($/MWh)
Annual Revenue Impact = Monthly Revenue Impact × 12
ROI = (Expected Revenue Recovery - Intervention Cost) / Intervention Cost
Payback Period = Intervention Cost / Monthly Revenue Recovery
```