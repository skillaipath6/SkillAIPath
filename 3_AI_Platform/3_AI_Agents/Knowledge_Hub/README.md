# Central AI Agent

One AI reviewer for all apps - trained on real feedback patterns.

## Architecture

```
_Shared_Agent/
├── central_reviewer.py    ← Common-sense code reviewer
├── rag_system.py          ← RAG knowledge base
├── knowledge_base.json    ← Training data
└── README.md              ← This file
```

## Used By

1. **PR Reviewer** - GitHub PR reviews
2. **SAP Dashboard** - SAP code analysis
3. **Intelligence Hub** - General code intelligence

## How to Use

```python
# Import the central agent
import sys
sys.path.append('/Workspace/Shared/dev/SkillAIPath/4_Business_Intelligence/3_Live_Apps/_Shared_Agent')
from central_reviewer import review_pr_code

# Review code
result = review_pr_code(
    file_path="my_script.py",
    code="<your code>",
    pr_context={
        "title": "Add new feature",
        "author": "developer",
        "project_type": "edufin"  # or "sap", etc.
    }
)

# Result contains:
# - status: "NEEDS_REVIEW" or "LOOKS_GOOD"
# - feedback: Human-readable review text
# - inline_comments: List of line-specific comments
```

## What It Checks

### Common Sense Logic
- What happens when I/O fails?
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

## Updating the Agent

All apps use the same agent. Update once, improves everywhere.

1. Edit `central_reviewer.py`
2. All apps automatically use the new logic
3. No need to redeploy each app separately
