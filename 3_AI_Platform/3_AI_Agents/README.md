# AI Agents Platform

## Production Agents

**GrowthAccelerator_Monitor** - Proactive monitoring agent for Growth Accelerator dashboards
- Monitors 4 dashboards every 6 hours
- Detects anomalies in Revenue, DBU consumption, Performance scores
- Auto-alerts to #growth-accelerator-alerts Slack channel

**SkillAI_Analyst** - Interactive data analysis agent
- Unity Catalog integration
- DBRX-powered insights
- Ad-hoc SQL and data exploration

## Deployment

**Supervizor (GrowthAccelerator_Monitor):**
1. Open notebook → ML → Agents → Create Agent
2. Connect tools and dashboard permissions
3. Set 6-hour recurring schedule

**Data Analysis (SkillAI_Analyst):**
1. Deploy via MLflow
2. Create serving endpoint
3. Use for interactive analysis

---
**Status:** Production 
**Owner:** SkillAI Platform Team
