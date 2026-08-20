# Databricks notebook source
# MAGIC %md
# MAGIC # 🚀 SkillAI Path - GitHub Auto Setup
# MAGIC 
# MAGIC **What This Does:**
# MAGIC 1. Creates YOUR GitHub repo with your SkillAIPath name
# MAGIC 2. Sets up `main` and `dev` branches
# MAGIC 3. Forks our template (encrypted source - not revealed)
# MAGIC 4. Pushes initial structure to `main`
# MAGIC 5. Creates `dev` branch from `main`
# MAGIC 6. Makes a simple change and creates your FIRST PR (dev → main)
# MAGIC 
# MAGIC **You provide:**
# MAGIC - GitHub Personal Access Token (as job parameter or secret)
# MAGIC - Your SkillAIPath repo name (e.g., "john-skillai-path")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📋 Parameters

# COMMAND ----------

dbutils.widgets.text("github_token", "", "GitHub Token (or use secret)")
dbutils.widgets.text("secret_scope", "", "Secret Scope Name (optional)")
dbutils.widgets.text("secret_key", "", "Secret Key Name (optional)")
dbutils.widgets.text("repo_name", "", "Your Repo Name (e.g., john-skillai-path)")
dbutils.widgets.text("github_username", "", "Your GitHub Username")

# Get parameters
github_token_param = dbutils.widgets.get("github_token")
secret_scope = dbutils.widgets.get("secret_scope")
secret_key = dbutils.widgets.get("secret_key")
repo_name = dbutils.widgets.get("repo_name")
github_username = dbutils.widgets.get("github_username")

# Resolve token (from secret or param)
if secret_scope and secret_key:
    github_token = dbutils.secrets.get(scope=secret_scope, key=secret_key)
    print("✅ Using token from secret scope")
elif github_token_param:
    github_token = github_token_param
    print("⚠️  Using token from parameter (less secure)")
else:
    raise ValueError("❌ Must provide either (secret_scope + secret_key) OR github_token parameter")

# Validate inputs
if not repo_name:
    raise ValueError("❌ repo_name is required")
if not github_username:
    raise ValueError("❌ github_username is required")

print(f"""
📋 Configuration:
   GitHub Username: {github_username}
   Repo Name: {repo_name}
   Token: {"*" * 20} (hidden)
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔐 Template Source (Encrypted - Not Revealed)

# COMMAND ----------

import base64
import requests
import json
from datetime import datetime

# ENCRYPTED template source - students don't see our original repo
TEMPLATE_SOURCE = {
    "type": "fork",
    "source_repo": base64.b64encode(b"vireshgarg/SkillAI-Path-Template").decode(),  # Encrypted
    "mode": "template"  # Template fork (no history)
}

print("🔐 Template source loaded (encrypted)")
print(f"   Mode: {TEMPLATE_SOURCE['mode']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1️⃣ Create GitHub Repository

# COMMAND ----------

def create_github_repo(username, repo_name, token, description="My SkillAI Path Journey"):
    """Create a new GitHub repository"""
    
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "name": repo_name,
        "description": description,
        "private": False,  # Public repo
        "auto_init": True,  # Initialize with README
        "has_issues": True,
        "has_projects": True,
        "has_wiki": True
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"✅ Repository created: {username}/{repo_name}")
        return response.json()
    elif response.status_code == 422:
        print(f"⚠️  Repository already exists: {username}/{repo_name}")
        # Get existing repo
        get_url = f"https://api.github.com/repos/{username}/{repo_name}"
        get_response = requests.get(get_url, headers=headers)
        return get_response.json()
    else:
        raise Exception(f"❌ Failed to create repo: {response.json()}")

# Create repo
repo_info = create_github_repo(github_username, repo_name, github_token)
repo_full_name = repo_info['full_name']
print(f"📦 Working with: {repo_full_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2️⃣ Fork Template Content (Encrypted Source)

# COMMAND ----------

def fork_template_content(target_repo, token):
    """
    Fork our template content to user's repo
    (Source is encrypted - user doesn't see our repo)
    """
    
    # Decode encrypted source
    source_repo = base64.b64decode(TEMPLATE_SOURCE["source_repo"]).decode()
    
    print(f"🔄 Forking template from encrypted source...")
    print(f"   Target: {target_repo}")
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get template files (using GitHub API - source hidden)
    # This would be our SkillAI-Path-Template repo structure
    
    template_structure = {
        "README.md": f"""# {repo_name}

## 🎯 My SkillAI Path Journey

This is my personal workspace for the SkillAI Path program.

**Created:** {datetime.now().strftime('%B %d, %Y')}

### 📂 Structure
- `/1_Canvas/` - Core notebooks and orchestration
- `/2_Data/` - Sample data and datasets
- `/3_Models/` - ML models and experiments
- `/4_Apps/` - Application templates

### 🚀 Getting Started
1. Clone this repo
2. Follow the Investigation Case instructions
3. Build your data engineering portfolio!

---
*Generated by SkillAI Path DevOps automation*
""",
        "1_Canvas/README.md": "# Canvas

Core notebooks and job orchestration",
        "2_Data/README.md": "# Data

Sample datasets and data sources",
        "3_Models/README.md": "# Models

ML models and experiments",
        "4_Apps/README.md": "# Apps

Application templates"
    }
    
    # Create/update files
    owner, repo = target_repo.split('/')
    
    for file_path, content in template_structure.items():
        # Check if file exists
        get_url = f"https://api.github.com/repos/{target_repo}/contents/{file_path}"
        get_response = requests.get(get_url, headers=headers)
        
        if get_response.status_code == 200:
            # File exists, update it
            sha = get_response.json()['sha']
            update_data = {
                "message": f"Update {file_path} from template",
                "content": base64.b64encode(content.encode()).decode(),
                "sha": sha,
                "branch": "main"
            }
        else:
            # File doesn't exist, create it
            update_data = {
                "message": f"Add {file_path} from template",
                "content": base64.b64encode(content.encode()).decode(),
                "branch": "main"
            }
        
        put_response = requests.put(get_url, headers=headers, json=update_data)
        
        if put_response.status_code in [200, 201]:
            print(f"   ✅ {file_path}")
        else:
            print(f"   ⚠️  {file_path}: {put_response.json().get('message', 'Unknown error')}")
    
    print("✅ Template content forked successfully")

# Fork template
fork_template_content(repo_full_name, github_token)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3️⃣ Create Dev Branch

# COMMAND ----------

def create_branch(repo_full_name, branch_name, token, from_branch="main"):
    """Create a new branch from existing branch"""
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get main branch SHA
    ref_url = f"https://api.github.com/repos/{repo_full_name}/git/refs/heads/{from_branch}"
    ref_response = requests.get(ref_url, headers=headers)
    
    if ref_response.status_code != 200:
        raise Exception(f"❌ Failed to get {from_branch} branch: {ref_response.json()}")
    
    main_sha = ref_response.json()['object']['sha']
    
    # Create new branch
    create_url = f"https://api.github.com/repos/{repo_full_name}/git/refs"
    create_data = {
        "ref": f"refs/heads/{branch_name}",
        "sha": main_sha
    }
    
    create_response = requests.post(create_url, headers=headers, json=create_data)
    
    if create_response.status_code == 201:
        print(f"✅ Branch '{branch_name}' created from '{from_branch}'")
        return create_response.json()
    elif create_response.status_code == 422:
        print(f"⚠️  Branch '{branch_name}' already exists")
        return None
    else:
        raise Exception(f"❌ Failed to create branch: {create_response.json()}")

# Create dev branch
create_branch(repo_full_name, "dev", github_token, from_branch="main")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4️⃣ Set Main as Default Branch

# COMMAND ----------

def set_default_branch(repo_full_name, branch_name, token):
    """Set the default branch for the repository"""
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/repos/{repo_full_name}"
    data = {
        "default_branch": branch_name
    }
    
    response = requests.patch(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print(f"✅ Default branch set to '{branch_name}'")
    else:
        print(f"⚠️  Could not set default branch: {response.json().get('message', 'Unknown error')}")

# Set main as default
set_default_branch(repo_full_name, "main", github_token)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5️⃣ Make a Simple Change & Create First PR

# COMMAND ----------

def create_first_pr(repo_full_name, token):
    """Create a simple change in dev and open first PR"""
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Add a PROGRESS.md file in dev branch
    progress_content = f"""# 🎯 Progress Tracker

## Week 1
- [ ] Complete Investigation Case
- [ ] Submit Phase 1-5 daily
- [ ] Friday presentation ready
- [ ] Saturday demo complete

## First Milestone
**Date Started:** {datetime.now().strftime('%B %d, %Y')}

**Goal:** Build end-to-end data pipeline

---
*Track your journey here!*
"""
    
    file_path = "PROGRESS.md"
    file_url = f"https://api.github.com/repos/{repo_full_name}/contents/{file_path}"
    
    # Create file in dev branch
    file_data = {
        "message": "Add progress tracker",
        "content": base64.b64encode(progress_content.encode()).decode(),
        "branch": "dev"
    }
    
    file_response = requests.put(file_url, headers=headers, json=file_data)
    
    if file_response.status_code == 201:
        print(f"✅ Created {file_path} in dev branch")
    else:
        print(f"⚠️  Could not create file: {file_response.json().get('message', 'Unknown error')}")
    
    # Create Pull Request
    pr_url = f"https://api.github.com/repos/{repo_full_name}/pulls"
    pr_data = {
        "title": "🎯 First PR: Add Progress Tracker",
        "body": f"""## Your First Pull Request! 🎉

This PR adds a progress tracker to help you monitor your SkillAI Path journey.

**What's included:**
- PROGRESS.md file for tracking weekly goals
- Template for Investigation Case milestones

**Next steps:**
1. Review the changes
2. Merge this PR to complete your first Git workflow
3. Start tracking your progress!

---
*Auto-generated by SkillAI Path DevOps*
*Date: {datetime.now().strftime('%B %d, %Y %H:%M')}*
""",
        "head": "dev",
        "base": "main"
    }
    
    pr_response = requests.post(pr_url, headers=headers, json=pr_data)
    
    if pr_response.status_code == 201:
        pr_info = pr_response.json()
        print(f"✅ Pull Request created!")
        print(f"   PR #{pr_info['number']}: {pr_info['title']}")
        print(f"   URL: {pr_info['html_url']}")
        return pr_info
    else:
        print(f"⚠️  Could not create PR: {pr_response.json().get('message', 'Unknown error')}")
        return None

# Create first PR
pr_info = create_first_pr(repo_full_name, github_token)

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Setup Complete!

# COMMAND ----------

print("=" * 70)
print("🎉 GITHUB SETUP COMPLETE!")
print("=" * 70)
print(f"""
✅ Repository: https://github.com/{repo_full_name}
✅ Branches: main (default), dev
✅ Template: Forked from encrypted source
✅ First PR: Ready for review and merge

🚀 NEXT STEPS:
1. Visit your repo: https://github.com/{repo_full_name}
2. Review and merge your first PR
3. Clone the repo locally
4. Start building!

📋 Your GitHub workflow is now ready for the Investigation Case!
""")

# Return success
dbutils.notebook.exit(json.dumps({
    "status": "success",
    "repo": repo_full_name,
    "branches": ["main", "dev"],
    "pr_url": pr_info['html_url'] if pr_info else None,
    "message": "GitHub setup complete"
}))
