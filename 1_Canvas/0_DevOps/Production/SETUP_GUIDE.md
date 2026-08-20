# Student Setup Guide - GitHub Integration

## ONE-TIME SETUP (5 minutes)

### Step 1: Create GitHub Personal Access Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click **"Generate new token (classic)"**
3. Name: `SkillAI-Path-Databricks`
4. Expiration: **90 days** (or custom)
5. Select scopes:
   - `repo` (all sub-items)
   - `workflow`
   - `admin:repo_hook`
6. Click **"Generate token"**
7. **COPY THE TOKEN** (you won't see it again!)
   - Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### Step 2: Store Token in Databricks Secrets

**Option A: Using Databricks CLI** (Recommended)
```bash
# Install Databricks CLI (if not already)
pip install databricks-cli

# Configure CLI with your workspace
databricks configure --token

# Create secret scope (ONE TIME)
databricks secrets create-scope skillai-students

# Store your GitHub token
databricks secrets put-secret skillai-students github-token
# Paste your token when prompted
```

**Option B: Using Databricks UI** (If available)
1. Go to Workspace → Settings → Secrets
2. Create scope: `skillai-students`
3. Add secret: `github-token` with your token value

---

### Step 3: Verify Setup

Run this in a Databricks notebook:
```python
# Test secret retrieval
token = dbutils.secrets.get(scope="skillai-students", key="github-token")
print(f"Token starts with: {token[:10]}...")
``` If you see `ghp_xxxxxx...` → Setup complete!

---

## RUNNING THE DEVOPS JOB

### Every Time You Need a New Repo:

1. Go to Job: **01_OnDemand_DevOps**
2. Click **"Run now"**
3. Provide ONLY these parameters:
   ```
   secret_scope: skillai-students
   secret_key: github-token
   repo_name: your-name-skillai-path
   github_username: your-github-username
   ```
   (Leave `github_token` empty - we're using secrets!)

4. Click **Run** → Job completes in <2 minutes

5. You get:
   - New repo created
   - main + dev branches ready
   - First PR waiting for you to merge
   - Folder structure initialized

---

## SECURITY BEST PRACTICES

### DO:
- Store tokens in Databricks secrets (encrypted at rest)
- Use token expiration (90 days recommended)
- Rotate tokens every 3 months
- Use minimal required scopes

### ❌ DON'T:
- Hardcode tokens in notebooks
- Share tokens in Slack/WhatsApp
- Use tokens with `admin:org` scope (too powerful)
- Store tokens in git repos

---

## TROUBLESHOOTING

### "Secret not found"
- Check scope name: `skillai-students` (exact spelling)
- Check key name: `github-token` (exact spelling)
- Re-run Step 2 if needed

### "Token invalid"
- Token may have expired
- Create new token (Step 1)
- Update secret (Step 2)

### "Repo already exists"
- Job will use existing repo (won't fail)
- Or use different repo name

### "Permission denied"
- Check token scopes include `repo` + `workflow`
- Regenerate with correct scopes

---

## WHAT HAPPENS BEHIND THE SCENES

1. Job retrieves your token from secrets (encrypted)
2. Creates repo under YOUR GitHub account
3. Forks SkillAI template (source hidden from you)
4. Sets up branches: main (default) + dev
5. Initializes folder structure
6. Creates first PR for you to practice Git workflow
7. Returns repo URL + PR link

**Your GitHub token never leaves Databricks secrets storage.**

---

## NEXT STEPS AFTER REPO SETUP

1. Visit your new repo
2. Review and merge your first PR
3. Clone repo locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   cd YOUR_REPO_NAME
   git checkout dev
   ```
4. Start Investigation Case work in `dev` branch
5. Daily commits → PRs → merge to main

---

**Questions?** Ask in Investigation Case WhatsApp group or Graphy community.
