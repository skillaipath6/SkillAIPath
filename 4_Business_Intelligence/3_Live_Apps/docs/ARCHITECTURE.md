# Unified AI Agent Architecture

## Design Goal

**One central AI agent that all apps call** - instead of duplicating logic across apps.

## Structure

```
4_Business_Intelligence/3_Live_Apps/
│
├── _Shared_Agent/ ← ⭐ Central AI Agent
│ ├── central_reviewer.py ← One reviewer logic for all apps
│ ├── rag_system.py ← One RAG system for all apps
│ ├── knowledge_base.json ← Shared training data (7.8MB)
│ └── README.md ← Usage guide
│
├── PR Reviewer/
│ ├── app.py ← Gradio UI for GitHub PR reviews
│ ├── pr_reviewer.py ← Imports from _Shared_Agent
│ └── ...
│
├── SAP Dashboard/
│ ├── app.py ← Flask UI for orchestration
│ ├── central_agent_integration.py ← Shows how to add code review
│ └── ...
│
└── Intelligence_Hub/
 ├── app.py ← Streamlit UI for RAG Q&A
 ├── central_agent_integration.py ← Shows how to add code review
 └── ...
```

## How It Works

### Before (Duplicated Logic)
```
PR Reviewer → own reviewer logic → own RAG → own knowledge base
SAP Dashboard → own reviewer logic → own RAG → own knowledge base
Intelligence Hub → own reviewer logic → own RAG → own knowledge base
```
**Problems:**
- Logic duplicated 3x
- Updates need 3 changes
- Inconsistent reviews
- Wasted maintenance

### After (Unified System)
```
 ┌─────────────────────┐
 │ _Shared_Agent/ │
 │ central_reviewer │
 │ rag_system │
 │ knowledge_base │
 └─────────────────────┘
 ▲
 ┌────────────┼────────────┐
 │ │ │
 ┌───────▼──────┐ ┌──▼──────┐ ┌──▼──────────┐
 │ PR Reviewer │ │ SAP │ │Intelligence │
 │ │ │Dashboard│ │ Hub │
 └──────────────┘ └─────────┘ └─────────────┘
```
**Benefits:**
- One source of truth
- Update once, improves everywhere
- Consistent reviews across all apps
- Easy to maintain

## Usage

### PR Reviewer (Already Integrated)
```python
# pr_reviewer.py
import sys
sys.path.append('/Workspace/Shared/dev/SkillAIPath/4_Business_Intelligence/3_Live_Apps/_Shared_Agent')
from central_reviewer import review_pr_code

# Just call the central agent
result = review_pr_code(file_path, code, pr_context)
```

### SAP Dashboard (Integration Ready)
```python
# See: SAP Dashboard/central_agent_integration.py
from central_agent_integration import review_sap_code

result = review_sap_code(file_path, code)
```

### Intelligence Hub (Integration Ready)
```python
# See: Intelligence_Hub/central_agent_integration.py
from central_agent_integration import review_code_with_rag

result = review_code_with_rag(file_path, code, project_type)
```

## What the Central Agent Checks

### Common Sense Logic
- ❓ What happens when I/O fails?
- Will this fit in memory?
- Can you debug this in production?
- Have you tested edge cases?
- Does the business logic make sense?

### Domain-Specific
- **EduFin**: CIBIL null handling, DPD thresholds
- **SAP**: Connection pooling, RFC efficiency
- **Pipelines**: Idempotency, data quality checks

### Technical Accuracy
- GroupBy without aggregation
- Destructive SQL without WHERE
- Hardcoded credentials
- Missing error handling
- Missing logging/tests

## Output Format

Readable, conversational reviews with line numbers:

```
Reviewed 15 files. Here's what needs attention:

──────────────────────────────────────────────────────────────────────

1. I/O operations without error handling

 → 0_Core_Analytics/01_SQL_Fundamentals.py (lines 15, 42, 67)
 → 0_Core_Analytics/02_EduFin/0_Data_Setup.py (line 23)

 These will crash the pipeline when data sources are unavailable.
 Wrap spark.read and API calls in try/except blocks with logging.

2. CIBIL scores used without null handling

 → 0_Core_Analytics/02_EduFin/2_Customer_Risk.py (lines 102, 156)
 → ...and 2 more files

 About 30% of EduFin records have null CIBIL scores.
 Add .fillna() or .coalesce() with your business rule.

──────────────────────────────────────────────────────────────────────

Let me know if you want details on any specific file.
```

## Updating the Agent

**Update once, improves everywhere:**

1. Edit `_Shared_Agent/central_reviewer.py`
2. All apps automatically use the new logic
3. No need to redeploy each app separately

## Current Status

| App | Status | Location |
|-----|--------|----------|
| **PR Reviewer** | Integrated | Uses central agent directly |
| **SAP Dashboard** | Ready | Integration guide created |
| **Intelligence Hub** | Ready | Integration guide created |

## Next Steps

1. Central agent created
2. PR Reviewer integrated
3. SAP Dashboard - Add code review tab (optional)
4. Intelligence Hub - Add code review tab (optional)

## Training Data

The central agent is trained on your feedback patterns:
- Check logic, not just rules
- Ask "what happens when this fails?"
- Verify business logic makes sense
- Think about production debugging
- Check for edge cases
- Validate domain-specific logic (EduFin, SAP)

All stored in `_Shared_Agent/knowledge_base.json` (7.8MB)
