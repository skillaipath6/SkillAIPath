# Auto_Reviewer System Guide
**Version:** Production v14 | **Status:** ✅ RUNNING  
**URL:** https://pr-review-webhook-deploy-7474646215602371.aws.databricksapps.com

---

## 📌 Quick Reference

**Core Files:**
- `app.py` - Gradio UI (14KB)
- `pr_reviewer.py` - Self-contained review logic (9.7KB)
- `app.yaml` - App configuration
- `requirements.txt` - Dependencies
- `google_sheet_handler.py` - Google Sheets integration

**Features:** Readable reviews • Line numbers • Context-aware • Editable output • Google Sheets integration

---

## 🏗 Architecture

### Self-Contained Design

Databricks Apps run in containers where `/Workspace` paths are **NOT accessible at runtime**.

```python
# ✅ Works (current)
from pr_reviewer import review_pr_code

# ❌ Doesn't work in deployed apps
sys.path.append('/Workspace/...')
from central_reviewer import review_pr_code
```

**All logic is embedded in `pr_reviewer.py` (9.7KB)** - no workspace dependencies.

---

## 🎯 Review Capabilities

### Common Sense Checks
- What happens when I/O fails?
- Will this fit in memory?
- Can you debug this in production?
- Have you tested edge cases?

### Domain-Specific
- **EduFin:** CIBIL nulls, DPD thresholds
- **SAP:** Connection pooling, RFC efficiency
- **Pipelines:** Idempotency, data quality

### Technical
- GroupBy without aggregation
- Destructive SQL without WHERE
- Hardcoded credentials
- Missing error handling/logging

### Output Format
```
Reviewed 15 files. Here's what needs attention:

──────────────────────────────────────────────────────────────
1. I/O operations without error handling
   → customer_analytics.py (lines 15, 42, 67)
   → data_pipeline.py (line 23)
   
   Wrap spark.read and API calls in try/except with logging.

2. CIBIL scores used without null handling
   → risk_scoring.py (lines 102, 156)
   
   30% of EduFin records have null CIBIL. Add .fillna().
──────────────────────────────────────────────────────────────
```

---

## 📚 Context Training System

Enables **situational awareness** - reviews feel like they're from a **Senior Lead** who knows the team.

### Features
1. **Discord Integration** - Paste channel updates directly
2. **Sprint Plan Tracking** - Import from Google Sheets
3. **Roadmap Tracking** - Strategic initiatives
4. **Smart Reviews** - Adds context like:

```
### 🤝 Quick Context Check

📋 I see you're working on: VDP Implementation, Dashboard Cleanup
🔥 Heads up: You've got 3 P0 task(s) on your plate right now
💬 Last update: Today completed VDP for 3 dashboards...
```

### How to Use Context Training

**Discord Updates:**
```
Vikas Ray — 8/7/26, 10:19 AM
P0 - VDP - Check already created ones
P0 - Dashboards cleanup
```

**Sprint Plan (from Google Sheet):**
```
Developer | Task | Priority | Status | Due Date
Vikas | VDP Implementation | P0 | In Progress | 2026-08-15
```

Click **"Update Training Context"** - system parses and stores in Unity Catalog table `sap_prod.ai_ops.pr_context_training`.

---

## 🔗 Google Sheets Integration

### Setup

**Sheet Format (columns A-D):**
| Column | Name | Required | Example |
|--------|------|----------|---------|
| A | Timestamp | Yes | 2024/08/12 3:45 PM |
| B | Email | Yes | user@example.com |
| C | PR URL | Yes | github.com/owner/repo/pull/123 |
| D | Token | **Optional** | ghp_xxxxx OR *empty* |

**Configuration (`app.yaml`):**
```yaml
env:
  - name: GOOGLE_SERVICE_ACCOUNT_JSON
    valueFrom: google_creds
  - name: GOOGLE_SHEET_ID
    value: "1Dlf1QVlrI6Zgw_L0EMh7..."
  - name: GITHUB_TOKEN
    value: github_pat_xxx  # Fallback
  - name: ENABLE_GOOGLE_SHEETS_POLLING
    value: "true"  # Optional auto-polling
```

### How It Works

**Automatic Polling (if enabled):**
1. Polls sheet every 30 seconds
2. Reads PR URL + optional token
3. Generates review
4. Posts to GitHub
5. **Deletes row** (GDPR compliance)

**Manual Mode:**
- Use UI to review PRs directly
- Token from sheet used if provided

### Security
✅ Tokens never printed to logs (masked)  
✅ Tokens deleted after processing  
✅ Graceful error handling  
✅ No tokens stored in code

---

## 🚀 Deployment & Operations

### Deploy
```bash
# Auto-deploys on code changes
# Manual restart:
databricks apps stop pr-review-webhook-deploy
databricks apps start pr-review-webhook-deploy

# Check logs:
databricks apps logs pr-review-webhook-deploy --follow
```

### Making Changes

**Update Review Logic:**
- Edit `pr_reviewer.py` → auto-deploys

**Update UI:**
- Edit `app.py` → auto-deploys

**Add Dependencies:**
1. Edit `requirements.txt`
2. `databricks apps restart pr-review-webhook-deploy`

### Environment Variables
Set in Databricks Apps UI:
- `GITHUB_TOKEN` - GitHub PAT for posting comments
- `GOOGLE_SERVICE_ACCOUNT_JSON` - For Sheets access
- `GOOGLE_SHEET_ID` - Target sheet
- `ENABLE_GOOGLE_SHEETS_POLLING` - Enable/disable auto-polling

---

## 🐛 Troubleshooting

**App crashes on start:**
- Check logs: `databricks apps logs pr-review-webhook-deploy`
- Common cause: Workspace path imports
- Solution: Keep logic in `pr_reviewer.py`

**Review quality issues:**
- Edit `pr_reviewer.py` logic
- Changes auto-deploy

**Google Sheets not working:**
- Verify service account JSON is set
- Check sheet ID matches
- Confirm sheet has columns A-D with header row
- Test connection in UI

**Token not being used:**
- Verify token column (D) has value
- Check logs for "Using provided token: ghp_****"
- Ensure `submit_review()` receives token parameter

---

## 📦 File Structure

```
2_Auto_Reviewer/
├── app.py                    # Gradio UI
├── pr_reviewer.py            # Core review logic
├── google_sheet_handler.py   # Sheets integration
├── app.yaml                  # App config
├── requirements.txt          # Dependencies
├── AUTO_REVIEWER_GUIDE.md    # This file
└── Archive/                  # 21 backup files
    ├── backup_versions/      # Old versions
    └── old_rag_system/       # Deprecated
```

**Archived files can be deleted** once you're confident current version works.

---

## 🔄 Related Systems

- **SAP Dashboard** - `/4_Business_Intelligence/3_Live_Apps/SAP Dashboard`
- **Intelligence Hub** - `/4_Business_Intelligence/3_Live_Apps/Intelligence_Hub`
- **SAP Knowledge Agent** - `/3_AI_Platform/3_AI_Agents/SAP Knowledge Agent` (reference only, not used by PR Reviewer)

---

## 📊 Context Data Storage

**Unity Catalog Table:**
- `sap_prod.ai_ops.pr_context_training`
- Stores: Discord updates, sprint plans, roadmap, developer priorities
- Queried during review generation for context injection

---

## ✨ Version History

- **v14** - Current production (readable format, line numbers, context-aware)
- **v9** - Old verbose format (archived)
- Earlier versions in `Archive/backup_versions/`

---

## 💡 Best Practices

1. **Don't add workspace imports to `pr_reviewer.py`** - won't work in deployed apps
2. **Test locally first** - verify in notebooks before deploying
3. **Keep self-contained** - all logic in `pr_reviewer.py` or packages
4. **Archive old versions** - don't delete until confident
5. **Use provided tokens** - respect user's GitHub permissions
6. **Update context regularly** - keeps reviews relevant to current sprint

---

✨ **Clean, maintainable, production-ready!**
