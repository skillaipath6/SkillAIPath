# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # Business Intelligence Apps Deployment Job
# MAGIC
# MAGIC Automated deployment of all 3 Business Intelligence Live Apps using Databricks SDK

# COMMAND ----------

# DBTITLE 1,Auto-configuration: resolve workspace, warehouse, catalog
import time
import json
import os
import re
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.apps import (
    App, AppDeployment, AppDeploymentMode,
    ComputeState, AppDeploymentState
)
from databricks.sdk.service.iam import AccessControlRequest, PermissionLevel

# Create WorkspaceClient - auto-authenticates in Databricks notebook runtime.
# No credentials are hardcoded or overridden: Apps V2 provides
# DATABRICKS_HOST, DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET itself.
w = WorkspaceClient()

# ------------------------------------------------------------------
# Step 1: Identify the CURRENT workspace (never a fixed Workspace ID).
# ------------------------------------------------------------------
WORKSPACE_HOST = (w.config.host or "").replace("https://", "")
try:
    WORKSPACE_ID = dbutils.notebook.getContext().workspaceId().get()
except Exception:
    try:
        WORKSPACE_ID = spark.conf.get("spark.databricks.clusterUsageTags.orgId")
    except Exception:
        WORKSPACE_ID = "unknown"
print(f"🌐 Current workspace: {WORKSPACE_HOST} (id={WORKSPACE_ID})")

# ------------------------------------------------------------------
# Step 2: Resolve the SQL warehouse for THIS workspace.
# Priority: job/widget parameter → env var → deterministic auto-detection
# from the warehouses that actually exist here (no guessed IDs).
# ------------------------------------------------------------------
try:
    WAREHOUSE_ID = dbutils.widgets.get("WAREHOUSE_ID")
except Exception:
    WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "")

if not WAREHOUSE_ID:
    warehouses = list(w.warehouses.list())
    if not warehouses:
        raise RuntimeError(
            "No SQL warehouses exist in this workspace. "
            "Create one or pass WAREHOUSE_ID explicitly.")
    starters = [x for x in warehouses if "starter" in x.name.lower()]
    running = [x for x in warehouses
               if str(getattr(x, "state", "")).upper().endswith("RUNNING")]
    chosen = (starters or running or warehouses)[0]
    WAREHOUSE_ID = chosen.id
    print(f"Warehouse auto-detected: {chosen.name} ({WAREHOUSE_ID}, state={chosen.state})")
else:
    print(f"Warehouse from parameter: {WAREHOUSE_ID}")

# ------------------------------------------------------------------
# Step 3: Resolve the Unity Catalog for THIS workspace.
# Priority: job/widget parameter → env var → the requested catalog if it
# exists here → the workspace's only managed catalog. Never guessed.
# ------------------------------------------------------------------
try:
    CATALOG = dbutils.widgets.get("CATALOG")
except Exception:
    CATALOG = os.getenv("CATALOG", "sap_dev")

_catalogs = {c.name: c for c in w.catalogs.list()}
if CATALOG not in _catalogs:
    managed = [c for c in _catalogs.values()
               if str(getattr(c, "catalog_type", "")).split(".")[-1] == "MANAGED_CATALOG"]
    if len(managed) == 1:
        print(f"⚠️ Catalog '{CATALOG}' does not exist in this workspace — "
              f"resolving to the only managed catalog '{managed[0].name}'")
        CATALOG = managed[0].name
    else:
        raise RuntimeError(
            f"Catalog '{CATALOG}' not found in this workspace "
            f"(available: {sorted(_catalogs)}). Pass the CATALOG parameter explicitly.")

print(f"🔧 Warehouse: {WAREHOUSE_ID} | Catalog: {CATALOG}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## App Configuration

# COMMAND ----------

# DBTITLE 1,App Configuration
# Resolve the target environment from the job's `environment` base parameter.
# DEV deployment uses /Shared/dev/... source; MAIN deployment uses /Shared/main/... source.
try:
    ENVIRONMENT = dbutils.widgets.get("environment")
except Exception:
    ENVIRONMENT = "dev"
if ENVIRONMENT not in ("dev", "main"):
    raise ValueError(f"Unknown environment '{ENVIRONMENT}' — expected 'dev' or 'main'")

LIVE_APPS_ROOT = f"/Workspace/Shared/{ENVIRONMENT}/SkillAIPath/4_Business_Intelligence/3_Live_Apps"
if not os.path.isdir(LIVE_APPS_ROOT):
    raise RuntimeError(
        f"Source root not found: {LIVE_APPS_ROOT}. "
        "Check the 'environment' parameter (dev/main) and that the SkillAIPath "
        "folder is provisioned in this workspace.")
print(f"🌍 Environment: {ENVIRONMENT} | Source root: {LIVE_APPS_ROOT}")

apps_config = [
    {
        "name": "bi-center",
        "display_name": "Business Intelligence Center",
        "source_path": f"{LIVE_APPS_ROOT}/01_BI_Center",
        "description": "Bidirectional data collaboration - read AI data, write business overrides, submit feedback",
        # A NEWLY CREATED app gets a NEW service principal with ZERO access —
        # these grants are re-applied (idempotently) on every deployment.
        "grants": {
            "schemas_read": ["gold", "silver"],
            "tables_write": ["gold.model_feedback", "gold.inventory_adjustments",
                              "gold.data_quality_issues", "gold.customer_priority_flags",
                              "gold.churn_prediction_overrides", "gold.demand_forecast_adjustments"],
            "warehouse": True,
        },
    },
    {
        "name": "team-intelligence-hub",
        "display_name": "Team Intelligence Hub",
        "source_path": f"{LIVE_APPS_ROOT}/02_Team_Intelligence_Hub",
        "description": "Live execution platform - code executor, AI chat, job monitor, team activity",
        "grants": {
            "schemas_read": ["gold"],
            "tables_write": ["gold.skillai_user_activity"],
            "warehouse": True,
        },
    },
    {
        "name": "skillai-execution-support",
        "display_name": "SkillAI Execution Support Agent",
        "source_path": f"{LIVE_APPS_ROOT}/03_SkillAI_Execution_Support",
        "description": "Autonomous AI assistant with persistent memory, user context, and RAG knowledge base"
    }
]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deploy Apps Using Databricks SDK

# COMMAND ----------

# DBTITLE 1,Deploy Apps Using Databricks SDK
from concurrent.futures import ThreadPoolExecutor, as_completed

# Results tracking
deployment_results = []

def state_str(state):
    """Convert state enum or string to string for comparison."""
    if state is None:
        return "UNKNOWN"
    if hasattr(state, 'value'):
        return state.value
    return str(state)

def get_deployment_state(app):
    """Get the deployment state from pending or active deployment."""
    if app.pending_deployment and app.pending_deployment.status:
        return state_str(app.pending_deployment.status.state), app.pending_deployment.status.message or ""
    if app.active_deployment and app.active_deployment.status:
        return state_str(app.active_deployment.status.state), app.active_deployment.status.message or ""
    return "UNKNOWN", ""

print("=" * 80)
print("🚀 DEPLOYING BUSINESS INTELLIGENCE APPS")
print("=" * 80)

def configure_app_yaml(app_config):
    """Right before deploying, rewrite the app.yaml env values
    (WAREHOUSE_ID / CATALOG) with the values resolved for THIS workspace,
    so the same notebook deploys correctly in any Databricks workspace.
    Only values the app.yaml already declares are updated — nothing else is
    touched, and DATABRICKS_HOST / CLIENT_ID / CLIENT_SECRET are never set
    (Apps V2 provides them automatically). MAIN is never auto-modified."""
    yaml_path = app_config["source_path"] + "/app.yaml"
    try:
        with open(yaml_path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("   ℹ️ no app.yaml in source — nothing to configure")
        return
    if ENVIRONMENT == "main":
        print("   ⚠️ MAIN environment — app.yaml NOT auto-modified (explicit approval required)")
        return
    updates = {"WAREHOUSE_ID": WAREHOUSE_ID, "CATALOG": CATALOG}
    lines = content.splitlines()
    out, changed, current = [], [], None
    for ln in lines:
        m = re.match(r"\s*- name:\s*(\w+)", ln)
        if m:
            current = m.group(1) if m.group(1) in updates else None
            out.append(ln)
            continue
        if current and ln.lstrip().startswith("value:"):
            indent = ln[:len(ln) - len(ln.lstrip())]
            if f'"{updates[current]}"' in ln:
                out.append(ln)  # already correct for this workspace
            else:
                out.append(f'{indent}value: "{updates[current]}"')
                changed.append(f"{current}={updates[current]}")
            current = None
            continue
        out.append(ln)
    if changed:
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
        print(f"   ⚙️ app.yaml configured for this workspace: {', '.join(changed)}")
    else:
        print("   ⚙️ app.yaml already matches this workspace (no change)")

def ensure_app_permissions(app_config):
    """A newly created Databricks App gets a NEW service principal with ZERO
    access to Unity Catalog data and NO warehouse CAN_USE — every query fails
    with PERMISSION_DENIED until access is granted. This re-applies the app's
    grants idempotently on every deployment, in any workspace."""
    spec = app_config.get("grants")
    if not spec:
        return
    app = w.apps.get(name=app_config["name"])
    sp = getattr(app, "service_principal_client_id", None) or app.oauth2_app_client_id
    if not sp:
        print("   ⚠️ could not resolve the app's service principal — skipping permissions")
        return
    cat = spec.get("catalog", CATALOG)
    stmts = [f"GRANT USE CATALOG ON CATALOG {cat} TO `{sp}`"]
    for s in spec.get("schemas_read", []):
        stmts.append(f"GRANT USE SCHEMA ON SCHEMA {cat}.{s} TO `{sp}`")
        stmts.append(f"GRANT SELECT ON SCHEMA {cat}.{s} TO `{sp}`")
    for t in spec.get("tables_write", []):
        stmts.append(f"GRANT INSERT, MODIFY ON TABLE {cat}.{t} TO `{sp}`")
    ok = 0
    for stmt in stmts:
        try:
            r = w.statement_execution.execute_statement(
                warehouse_id=WAREHOUSE_ID, statement=stmt, wait_timeout="30s")
            if str(getattr(r.status.state, "name", r.status.state)).upper() == "SUCCEEDED":
                ok += 1
            else:
                print(f"   ⚠️ grant not confirmed: {stmt[:90]}")
        except Exception as e:
            print(f"   ⚠️ grant error on {stmt[:60]}…: {str(e)[:120]}")
    if spec.get("warehouse"):
        try:
            w.permissions.update(
                request_object_type="warehouses", request_object_id=WAREHOUSE_ID,
                access_control_list=[AccessControlRequest(
                    service_principal_name=sp, permission_level=PermissionLevel.CAN_USE)])
            print(f"   🔐 warehouse CAN_USE ensured for app principal `{sp[:12]}…`")
        except Exception as e:
            print(f"   ⚠️ warehouse permission error: {str(e)[:120]}")
    print(f"   🔐 {ok}/{len(stmts)} UC grants ensured for app principal")

def deploy_app(app_config):
    app_name = app_config["name"]
    display_name = app_config["display_name"]
    source_path = app_config["source_path"]

    result = {
        "name": app_name,
        "display_name": display_name,
        "status": "FAILED",
        "message": "",
        "url": ""
    }

    try:
        print(f"\n{'='*60}")
        print(f"📦 Processing: {display_name}")
        print(f"   Name: {app_name}")
        print(f"   Source: {source_path}")

        # Step 0: point the app's app.yaml at THIS workspace's warehouse/catalog
        configure_app_yaml(app_config)

        # Step 1: Check if app exists
        app_exists = False
        try:
            app = w.apps.get(name=app_name)
            app_exists = True
            current_state = state_str(app.compute_status.state) if app.compute_status else "UNKNOWN"
            print(f"   ✅ App exists (Status: {current_state})")
        except Exception as e:
            err_str = str(e)
            err_lower = err_str.lower()
            if any(kw in err_lower for kw in ["notfound", "404", "resource_not_found", "does not exist", "is deleted"]):
                app_exists = False
                print(f"   ➕ App does not exist, will create new")
            else:
                raise

        if not app_exists:
            # Step 2: Create new app
            print(f"   ➕ Creating new app...")
            w.apps.create(app=App(
                name=app_name,
                description=app_config["description"]
            ))
            print(f"   ✅ App created")
            time.sleep(2)

        # Step 1b: ensure the app's (possibly brand-new) service principal
        # can reach the warehouse and UC data — without this, every app
        # query 403s and all sections show "KPI query failed".
        ensure_app_permissions(app_config)

        # Step 3: Ensure app is RUNNING (deploy requires RUNNING state)
        app = w.apps.get(name=app_name)
        current_state = state_str(app.compute_status.state) if app.compute_status else "UNKNOWN"

        if current_state != "ACTIVE":
            if current_state != "STARTING":
                print(f"   ▶️  Starting app (current state: {current_state})...")
                w.apps.start(name=app_name)
            else:
                print(f"   ⏳ App is already STARTING, waiting for ACTIVE...")
            for i in range(60):  # 300 seconds max
                time.sleep(2)
                app = w.apps.get(name=app_name)
                state = state_str(app.compute_status.state) if app.compute_status else "UNKNOWN"
                if state == "ACTIVE":
                    print(f"   ✅ App is running")
                    break
                elif state in ("ERROR", "FAILED"):
                    msg = app.compute_status.message if app.compute_status else ""
                    print(f"   ❌ Could not start app (State: {state})")
                    if msg:
                        print(f"      {msg}")
                    result["message"] = f"Could not start app: {state} - {msg}"
                    break
            else:
                print(f"   ❌ Startup timed out (300s)")
                result["message"] = "Startup timed out"
                return result
        else:
            print(f"   ✅ App already running")

        # Step 3b: Wait for any existing deployment to complete
        app = w.apps.get(name=app_name)
        dep_state, _ = get_deployment_state(app)
        if dep_state not in ("SUCCEEDED", "FAILED", "UNKNOWN"):
            print(f"   ⏳ Waiting for existing deployment ({dep_state})...")
            for i in range(36):
                time.sleep(2)
                app = w.apps.get(name=app_name)
                dep_state, _ = get_deployment_state(app)
                if dep_state in ("SUCCEEDED", "FAILED", "UNKNOWN"):
                    print(f"   ✅ Existing deployment finished ({dep_state})")
                    break
            else:
                print(f"   ⚠️ Existing deployment still in progress, deploying anyway")

        # Step 4: Deploy source code (app must be RUNNING)
        print(f"   🔄 Deploying source code (SNAPSHOT mode)...")
        w.apps.deploy(
            app_name=app_name,
            app_deployment=AppDeployment(
                source_code_path=source_path,
                mode=AppDeploymentMode.SNAPSHOT
            )
        )
        print(f"   ✅ Deploy command sent")

        # Step 5: Wait for deployment to complete (max 180 seconds, poll every 5s)
        print(f"   ⏳ Waiting for deployment...")
        deploy_success = False
        for i in range(36):
            time.sleep(2)
            app = w.apps.get(name=app_name)
            dep_state, dep_msg = get_deployment_state(app)
            if dep_state == "SUCCEEDED":
                print(f"   ✅ Deployment succeeded")
                deploy_success = True
                break
            elif dep_state == "FAILED":
                print(f"   ❌ Deployment failed: {dep_msg}")
                result["message"] = f"Deployment failed: {dep_msg}"
                break
        else:
            print(f"   ❌ Deployment timed out (180s)")
            result["message"] = "Deployment timed out"

        if not deploy_success:
            return result

        # Step 6: Verify app is ACTIVE (skip wait if already active)
        app = w.apps.get(name=app_name)
        state = state_str(app.compute_status.state) if app.compute_status else "UNKNOWN"

        if state == "ACTIVE":
            url = app.url or "N/A"
            print(f"   ✅ App is LIVE!")
            print(f"   🌐 URL: {url}")
            result["status"] = "SUCCESS"
            result["message"] = "Deployed and running"
            result["url"] = url
        else:
            if state != "STARTING":
                print(f"   ▶️  Starting app (current state: {state})...")
                w.apps.start(name=app_name)
            print(f"   ⏳ Waiting for app to be ACTIVE...")
            for i in range(150):  # 300 seconds max (poll every 2s)
                time.sleep(2)
                app = w.apps.get(name=app_name)
                state = state_str(app.compute_status.state) if app.compute_status else "UNKNOWN"
                if state == "ACTIVE":
                    url = app.url or "N/A"
                    print(f"   ✅ App is LIVE!")
                    print(f"   🌐 URL: {url}")
                    result["status"] = "SUCCESS"
                    result["message"] = "Deployed and running"
                    result["url"] = url
                    break
                elif state in ("ERROR", "FAILED"):
                    msg = app.compute_status.message if app.compute_status else ""
                    print(f"   ❌ Startup failed (State: {state})")
                    if msg:
                        print(f"      {msg}")
                    result["message"] = f"Startup failed: {state} - {msg}"
                    break
            else:
                print(f"   ❌ App did not become active (300s)")
                result["message"] = "App did not become active"

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        result["message"] = f"Exception: {str(e)}"

    return result

# Deploy all apps in parallel
with ThreadPoolExecutor(max_workers=len(apps_config)) as executor:
    futures = {executor.submit(deploy_app, cfg): cfg for cfg in apps_config}
    for future in as_completed(futures):
        try:
            result = future.result()
        except Exception as e:
            cfg = futures[future]
            result = {
                "name": cfg["name"],
                "display_name": cfg["display_name"],
                "status": "FAILED",
                "message": f"Exception: {str(e)}",
                "url": ""
            }
        deployment_results.append(result)

print(f"\n{'='*80}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Final Status

# COMMAND ----------

print("=" * 80)
print("📊 FINAL STATUS")
print("=" * 80)

success_count = 0
failure_count = 0

for r in deployment_results:
    icon = "🟢" if r["status"] == "SUCCESS" else "🔴"
    print(f"{icon} {r['display_name']}")
    print(f"   Name: {r['name']}")
    print(f"   Status: {r['status']}")
    if r["url"]:
        print(f"   URL: {r['url']}")
    if r["message"]:
        print(f"   Message: {r['message']}")
    print()

    if r["status"] == "SUCCESS":
        success_count += 1
    else:
        failure_count += 1

print("=" * 80)
print(f"Total: {success_count} succeeded, {failure_count} failed")
print("=" * 80)

if failure_count > 0:
    print("❌ DEPLOYMENT FAILED")
    raise Exception(f"Deployment failed for {failure_count} app(s)")
else:
    print("✅ ALL APPS DEPLOYED SUCCESSFULLY")
