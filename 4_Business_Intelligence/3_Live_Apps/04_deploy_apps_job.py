# Databricks notebook source
# MAGIC %md
# MAGIC # App Deployment Job
# MAGIC 
# MAGIC Automated deployment of all 3 Retail Ops Apps using Databricks CLI

# COMMAND ----------

import subprocess
import time
import json

# COMMAND ----------

# MAGIC %md
# MAGIC ## App Configuration

# COMMAND ----------

apps_config = [
    {
        "name": "inventory-command-center",
        "display_name": "Inventory Command Center",
        "source_path": "/Workspace/Shared/dev/SkillAIPath/4_Business_Intelligence/3_Live_Apps/01_Inventory_Command_Center",
        "description": "Real-time inventory monitoring with reorder approval workflow"
    },
    {
        "name": "demand-forecasting-dashboard", 
        "display_name": "Demand Forecasting Dashboard",
        "source_path": "/Workspace/Shared/dev/SkillAIPath/4_Business_Intelligence/3_Live_Apps/02_Demand_Forecasting_Dashboard",
        "description": "Predictive analytics for inventory planning"
    },
    {
        "name": "dynamic-pricing-api",
        "display_name": "Dynamic Pricing API", 
        "source_path": "/Workspace/Shared/dev/SkillAIPath/4_Business_Intelligence/3_Live_Apps/03_Dynamic_Pricing_API",
        "description": "Real-time pricing optimization API"
    }
]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deploy Apps Using CLI

# COMMAND ----------

def run_cli_command(command):
    """Run databricks CLI command and return output"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

# COMMAND ----------

print("="*80)
print("🚀 DEPLOYING RETAIL OPS APPS")
print("="*80)

for app_config in apps_config:
    app_name = app_config["name"]
    source_path = app_config["source_path"]
    
    print(f"\n📦 Processing: {app_config['display_name']}")
    print(f"   Name: {app_name}")
    print(f"   Source: {source_path}")
    
    # Check if app exists
    success, stdout, stderr = run_cli_command(f"databricks apps get {app_name} --output json")
    
    if success:
        print(f"   ✅ App exists")
        app_info = json.loads(stdout)
        print(f"   Current status: {app_info.get('compute_status', {}).get('state', 'UNKNOWN')}")
        
        # Stop if running
        if app_info.get('compute_status', {}).get('state') == 'RUNNING':
            print(f"   🛑 Stopping app...")
            run_cli_command(f"databricks apps stop {app_name}")
            time.sleep(5)
        
        # Deploy update
        print(f"   🔄 Deploying update...")
        success, stdout, stderr = run_cli_command(f"databricks apps deploy {app_name} --source-code-path {source_path}")
        if success:
            print(f"   ✅ Deploy command sent")
        else:
            print(f"   ❌ Deploy failed: {stderr}")
            continue
    else:
        # Create new app
        print(f"   ➕ Creating new app...")
        success, stdout, stderr = run_cli_command(
            f'databricks apps create {app_name} --description "{app_config["description"]}"'
        )
        
        if success:
            print(f"   ✅ App created")
        else:
            print(f"   ❌ Create failed: {stderr}")
            continue
        
        # Deploy source code
        print(f"   📦 Deploying source code...")
        success, stdout, stderr = run_cli_command(f"databricks apps deploy {app_name} --source-code-path {source_path}")
        if success:
            print(f"   ✅ Deploy command sent")
        else:
            print(f"   ❌ Deploy failed: {stderr}")
            continue
    
    # Wait for deployment (check status)
    print(f"   ⏳ Waiting for deployment...")
    for i in range(24):  # 2 minutes max
        success, stdout, stderr = run_cli_command(f"databricks apps get {app_name} --output json")
        if success:
            app_info = json.loads(stdout)
            status = app_info.get('compute_status', {}).get('state', 'UNKNOWN')
            if status in ['IDLE', 'RUNNING']:
                print(f"   ✅ Deployment complete (Status: {status})")
                break
            elif 'ERROR' in status or 'FAILED' in status:
                print(f"   ❌ Deployment failed (Status: {status})")
                msg = app_info.get('compute_status', {}).get('message', '')
                if msg:
                    print(f"      {msg}")
                break
        time.sleep(5)
    
    # Start app
    print(f"   ▶️  Starting app...")
    success, stdout, stderr = run_cli_command(f"databricks apps start {app_name}")
    if success:
        print(f"   ✅ Start command sent")
    else:
        print(f"   ❌ Start failed: {stderr}")
        continue
    
    # Wait for startup
    print(f"   ⏳ Waiting for startup...")
    for i in range(24):  # 2 minutes max
        success, stdout, stderr = run_cli_command(f"databricks apps get {app_name} --output json")
        if success:
            app_info = json.loads(stdout)
            status = app_info.get('compute_status', {}).get('state', 'UNKNOWN')
            if status == 'RUNNING':
                url = app_info.get('url', 'N/A')
                print(f"   ✅ App is LIVE!")
                print(f"   🌐 URL: {url}")
                break
            elif 'ERROR' in status or 'FAILED' in status:
                print(f"   ❌ Startup failed (Status: {status})")
                break
        time.sleep(5)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Final Status

# COMMAND ----------

print("="*80)
print("📊 FINAL STATUS")  
print("="*80)

for app_config in apps_config:
    app_name = app_config["name"]
    success, stdout, stderr = run_cli_command(f"databricks apps get {app_name} --output json")
    
    if success:
        app_info = json.loads(stdout)
        status = app_info.get('compute_status', {}).get('state', 'UNKNOWN')
        url = app_info.get('url', 'N/A')
        
        icon = "🟢" if status == "RUNNING" else "🔴" if "ERROR" in status else "🟡"
        print(f"{icon} {app_config['display_name']}")
        print(f"   Status: {status}")
        print(f"   URL: {url}")
    else:
        print(f"🔴 {app_config['display_name']}: Not found")
    print()

print("="*80)
print("✅ DEPLOYMENT COMPLETE!")
print("="*80)
