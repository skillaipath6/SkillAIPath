# Auto-Documentation Architecture (UPDATE Mode)

## Overview
Incremental documentation update system that maintains existing knowledge base with code changes.

## Key Principle: UPDATE, Not Recreate
- **UPDATE** existing entries when files change
- **ADD** new entries only for new projects/components 
- **PRESERVE** existing documentation for unchanged files
- ❌ **DO NOT** regenerate entire knowledge base

## Current State
- **Knowledge Base:** 7,322 existing entries (chunked code documentation)
- **Location:** `/Workspace/Shared/dev/SkillAIPath/3_AI_Platform/3_AI_Agents/Knowledge_Hub/knowledge_base.json`
- **Output Table:** `sap_dev.gold.knowledge_base`

## Workflow Pipeline

```
Code Changes (modified files)
 ↓
Change Detection (24h window)
 ↓
Re-chunk Modified Files
 ↓
Merge Strategy (update existing, add new)
 ↓
Save to knowledge_base.json (with backup)
 ↓
Sync to UC Table (MERGE upsert)
 ↓
Apps Query Updated Data
```

## Components

### 1. Change Detection
- **Method:** File modification timestamps
- **Window:** Last 24 hours (configurable)
- **Scope:** `.py`, `.sql`, `.md`, `.ipynb` files
- **Skip:** Hidden dirs, `__pycache__`, temp files

### 2. Re-chunking
- **Strategy:** Chunk only changed files
- **Chunk Size:** 500 lines per chunk
- **Metadata:** chunk_id, chunk_type, parent_context, keywords

### 3. Merge Strategy
- **Index:** chunk_id → entry lookup
- **Update:** Replace existing chunks with new content
- **Add:** Insert chunks for new files
- **Preserve:** Keep unchanged chunks as-is

### 4. UC Sync
- **Operation:** MERGE (upsert based on id)
- **Table:** `sap_dev.gold.knowledge_base`
- **Scope:** Only sync changed chunks (not full table)

## Deployment

### Workflow Location
```
/Workspace/Shared/dev/SkillAIPath/1_Canvas/Workflows/Auto_Documentation_Workflow
```

### Schedule
- **Frequency:** Daily @ 2 AM UTC
- **Trigger:** Databricks Job (scheduled)
- **On-Demand:** Manual run via notebook

### Integration Points
- **Team Ops Center:** Search interface
- **PR Reviewer:** Code context
- **Future Apps:** Consistent knowledge access

## Safety Features

### Backup Strategy
- **Before Update:** Create timestamped backup
- **Format:** `knowledge_base.json.backup_YYYYMMDD_HHMMSS`
- **Location:** Same directory as original

### Change Tracking
- **Metrics:** Files changed, chunks updated, chunks added
- **Logs:** Summary report per run
- **Audit:** Git commits track Knowledge Hub changes

## Benefits

1. **Incremental Updates** - Only process changed files
2. **Fast Execution** - No full rebuild needed
3. **Zero Data Loss** - Backups before every update
4. **Automatic Sync** - UC table stays current
5. **Queryable** - Apps access via Team Ops Center

## Usage

### Regular Flow (Existing Projects)
```python
# Runs daily - detects changes automatically
# Updates only what changed
# No manual intervention needed
```

### New Project Onboarding
```python
# Add project files to /Workspace/Shared/dev/SkillAIPath/
# Run Auto_Documentation_Workflow manually
# New chunks added to knowledge base
# UC table updated with new content
```

## Next Steps

1. Schedule daily run (Databricks Job)
2. ⬜ Add Git webhook integration (optional)
3. ⬜ Extend to external sources (Google Sheets, Discord)
4. ⬜ Add deduplication logic for similar content
