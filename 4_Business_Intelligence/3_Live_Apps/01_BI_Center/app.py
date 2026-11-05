import gradio as gr
import pandas as pd
import os
import re
import uuid
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementParameterListItem
from datetime import datetime, timedelta

# Initialize Databricks SDK - Apps V2 auto-configures from environment
# Environment provides: DATABRICKS_HOST, DATABRICKS_CLIENT_ID, DATABRICKS_CLIENT_SECRET
w = WorkspaceClient()

# UC catalog for all BI Center queries — configurable via app.yaml CATALOG env
# (dev=sap_dev, main=sap_main once populated)
CATALOG = os.getenv("CATALOG", "sap_dev")

# IDENTITY: WorkspaceClient() inside a Gradio app authenticates as the app's
# SERVICE PRINCIPAL, not the browsing user. The real user is resolved per
# request from the X-Forwarded-Email header set by the trusted Databricks Apps
# proxy (never client-supplied values).
APP_IDENTITY = w.current_user.me().user_name

def get_user_email(request: gr.Request = None) -> str:
    """Resolve the acting user from Apps-forwarded headers (trusted proxy).
    Falls back to the app service principal, clearly labelled as such."""
    try:
        if request is not None:
            fwd = request.headers.get("x-forwarded-email")
            if fwd:
                return fwd
    except Exception:
        pass
    return f"{APP_IDENTITY} (app identity)"

def get_warehouse_id():
    """Get warehouse ID from env or auto-detect first available warehouse"""
    # 1. Check environment variable (set via app.yaml or deployment)
    warehouse_id = os.getenv("WAREHOUSE_ID")
    if warehouse_id:
        print(f"✅ Using warehouse from WAREHOUSE_ID env: {warehouse_id}")
        return warehouse_id
    
    # 2. Auto-detect first available warehouse
    try:
        warehouses = list(w.warehouses.list())
        if warehouses:
            warehouse_id = warehouses[0].id
            print(f"✅ Auto-detected warehouse: {warehouses[0].name} (ID: {warehouse_id})")
            return warehouse_id
        else:
            raise ValueError("No SQL warehouses available in this workspace")
    except Exception as e:
        raise ValueError(f"Failed to get warehouse: {str(e)}")

WAREHOUSE_ID = get_warehouse_id()

def _fmt_params(params):
    """Convert [{'name':..,'value':..}] dicts to SDK statement parameters"""
    return [StatementParameterListItem(name=p["name"], value=p["value"]) for p in (params or [])]

def _stmt_state(result):
    """Statement state as a plain string ('SUCCEEDED', 'PENDING', …) —
    the SDK returns an enum whose str() is 'StatementState.X', so use .name."""
    st = getattr(result.status, "state", "")
    return str(getattr(st, "name", st)).upper()

def query_uc(sql, params=None):
    """Execute SQL against Unity Catalog - READ operations (parameterized)"""
    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID,
            statement=sql,
            parameters=_fmt_params(params),
            wait_timeout="30s"
        )
        # A statement can still be PENDING/RUNNING when the 30s wait expires
        # (cold serverless warehouse + heavy joins). Poll it to completion
        # instead of misreading an unfinished statement as "no data" — that
        # misread caused the 2026-11-03 forecast_date crash.
        polls = 0
        while _stmt_state(result) in ("PENDING", "RUNNING") and polls < 9:
            time.sleep(10)
            result = w.statement_execution.get_statement(result.statement_id)
            polls += 1
        state = _stmt_state(result)
        if state not in ("SUCCEEDED", "CLOSED"):
            _err = getattr(result.status, "error", None)
            _msg = getattr(_err, "message", None) or f"statement ended in state {state} without a result"
            print(f"❌ SQL read did not complete (state={state}): {str(_msg)[:300]}")
            return pd.DataFrame({"Error": [f"❌ Query did not complete (state={state}) — see app logs"]})
        
        columns = []
        if result.manifest and result.manifest.schema and result.manifest.schema.columns:
            columns = [col.name for col in result.manifest.schema.columns]
        if result.result and result.result.data_array:
            if not columns:
                print("❌ SQL read returned rows without a column manifest")
                return pd.DataFrame({"Error": ["❌ Malformed query result (no column metadata) — see app logs"]})
            return pd.DataFrame(result.result.data_array, columns=columns)
        # Empty result: honest empty frame with correct columns if available
        if columns:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame()
    except Exception as e:
        # Safe logging: SDK error messages carry no credentials; truncate large payloads.
        # Surfaces SQL failures in apps logs instead of silently rendering an Error table.
        print(f"❌ SQL read failed: {type(e).__name__}: {str(e)[:300]}")
        return pd.DataFrame({"Error": [str(e)]})

def execute_uc(sql, params=None):
    """Execute SQL against Unity Catalog - WRITE operations (parameterized)"""
    try:
        w.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID,
            statement=sql,
            parameters=_fmt_params(params),
            wait_timeout="30s"
        )
        return True, "✅ Data written successfully"
    except Exception as e:
        print(f"❌ SQL write failed: {type(e).__name__}: {str(e)[:300]}")
        return False, f"❌ Error: {str(e)}"

# =====================================================================
# TAB 1: ML MODEL FEEDBACK & OVERRIDES
# =====================================================================

def get_churn_predictions():
    """Get current churn predictions from gold (direct model output, dev only)"""
    sql = f"SELECT * FROM {CATALOG}.gold.churn_predictions ORDER BY churn_probability DESC LIMIT 500"
    return query_uc(sql)

def get_recent_feedback():
    """Get recent model feedback"""
    sql = f"""
    SELECT 
        model_name as Model,
        entity_id as EntityID,
        feedback_type as FeedbackType,
        notes as Notes,
        created_by as SubmittedBy,
        created_at as SubmittedAt
    FROM {CATALOG}.gold.model_feedback
    ORDER BY created_at DESC
    LIMIT 50
    """
    return query_uc(sql)

def submit_model_feedback(model_name, entity_id, prediction_value, actual_outcome, feedback_type, notes, request: gr.Request):
    """Submit feedback on ML model prediction (parameterized, per-user audit trail)"""
    if not model_name or not entity_id or not feedback_type:
        return "❌ Please fill in Model Name, Entity ID, and Feedback Type"
    
    user = get_user_email(request)
    sql = f"""
    INSERT INTO {CATALOG}.gold.model_feedback
    (feedback_id, model_name, entity_id, prediction_value, actual_outcome, feedback_type, notes, created_by, created_at)
    VALUES
    (:feedback_id, :model_name, :entity_id, :prediction_value, :actual_outcome, :feedback_type, :notes, :user, CURRENT_TIMESTAMP())
    """
    success, msg = execute_uc(sql, [
        {"name": "feedback_id", "value": str(uuid.uuid4())},
        {"name": "model_name", "value": str(model_name)},
        {"name": "entity_id", "value": str(entity_id)},
        {"name": "prediction_value", "value": float(prediction_value) if prediction_value is not None else None},
        {"name": "actual_outcome", "value": str(actual_outcome) if actual_outcome else None},
        {"name": "feedback_type", "value": str(feedback_type)},
        {"name": "notes", "value": str(notes) if notes else None},
        {"name": "user", "value": user},
    ])
    if success:
        return f"✅ Feedback submitted by {user}\n\nRefresh the 'Recent Feedback' view to see your entry."
    return msg

def get_churn_overrides():
    """Get active churn prediction overrides"""
    sql = f"""
    SELECT 
        customer_id as CustomerID,
        original_churn_probability as OriginalProb,
        override_churn_probability as OverrideProb,
        reason as Reason,
        valid_from as ValidFrom,
        valid_until as ValidUntil,
        created_by as CreatedBy
    FROM {CATALOG}.gold.churn_prediction_overrides
    ORDER BY created_at DESC
    LIMIT 50
    """
    return query_uc(sql)

def override_churn_prediction(customer_id, original_prob, override_prob, reason, valid_days, request: gr.Request):
    """Override churn prediction with business judgment (parameterized)"""
    if customer_id is None or override_prob is None or not reason:
        return "❌ Please fill in Customer ID, Override Probability, and Reason"
    
    try:
        customer_id_int = int(customer_id)
    except (TypeError, ValueError):
        return "❌ Invalid Customer ID - must be a whole number"
    
    try:
        override_prob_float = float(override_prob)
        if not (0 <= override_prob_float <= 1):
            return "❌ Override probability must be between 0 and 1"
    except (TypeError, ValueError):
        return "❌ Invalid override probability - must be a number between 0 and 1"
    
    try:
        original_prob_float = float(original_prob) if original_prob is not None else None
        if original_prob_float is not None and not (0 <= original_prob_float <= 1):
            return "❌ Original probability must be between 0 and 1"
    except (TypeError, ValueError):
        return "❌ Invalid original probability - must be a number between 0 and 1"
    
    # Validity window: strictly validated integer (safe for INTERVAL interpolation)
    valid_days_int = 0
    if valid_days is not None and valid_days != "":
        try:
            valid_days_int = int(valid_days)
        except (TypeError, ValueError):
            return "❌ Invalid validity days - must be a whole number"
        if valid_days_int < 0:
            return "❌ Validity days cannot be negative"
    
    user = get_user_email(request)
    if valid_days_int > 0:
        valid_until_sql = f"CURRENT_TIMESTAMP() + INTERVAL {valid_days_int} DAYS"
    else:
        valid_until_sql = "NULL"
    
    sql = f"""
    INSERT INTO {CATALOG}.gold.churn_prediction_overrides
    (override_id, customer_id, original_churn_probability, override_churn_probability, reason, valid_from, valid_until, created_by, created_at)
    VALUES
    (:override_id, :customer_id, :original_prob, :override_prob, :reason, CURRENT_TIMESTAMP(), {valid_until_sql}, :user, CURRENT_TIMESTAMP())
    """
    success, msg = execute_uc(sql, [
        {"name": "override_id", "value": str(uuid.uuid4())},
        {"name": "customer_id", "value": customer_id_int},
        {"name": "original_prob", "value": original_prob_float},
        {"name": "override_prob", "value": override_prob_float},
        {"name": "reason", "value": str(reason)},
        {"name": "user", "value": user},
    ])
    if success:
        return f"✅ Churn override created by {user}\n\nCustomer {customer_id_int} probability overridden to {override_prob_float}\nReason: {reason}\n\nRefresh 'Active Overrides' to see your entry."
    return msg

# =====================================================================
# TAB 2: INVENTORY ADJUSTMENTS
# =====================================================================

def get_inventory_status():
    """Get current inventory levels from the inventory health mart (source of truth)"""
    sql = f"""
    SELECT 
        ProductSK as ProductID,
        ProductName,
        WarehouseName as WarehouseLocation,
        CurrentStock,
        CurrentStockValue,
        StockStatus,
        CASE WHEN StockStatus = 'Out of Stock' THEN 'Understock' ELSE HealthStatus END AS HealthStatus
    FROM {CATALOG}.gold.mart_inventory_health
    ORDER BY CurrentStock ASC
    """
    return query_uc(sql)

def get_recent_adjustments():
    """Get recent inventory adjustments"""
    sql = f"""
    SELECT 
        product_id as ProductID,
        warehouse_id as WarehouseID,
        old_qty as SystemQty,
        new_qty as PhysicalQty,
        delta as Delta,
        reason_code as Reason,
        adjusted_by as AdjustedBy,
        adjusted_at as AdjustedAt
    FROM {CATALOG}.gold.inventory_adjustments
    ORDER BY adjusted_at DESC
    LIMIT 50
    """
    return query_uc(sql)

def submit_inventory_adjustment(product_id, warehouse_id, old_qty, new_qty, reason_code, location, notes, request: gr.Request):
    """Submit inventory adjustment after physical count (parameterized)"""
    if product_id is None or warehouse_id is None or old_qty is None or new_qty is None or not reason_code:
        return "❌ Please fill in Product ID, Warehouse ID, System Qty, Physical Count, and Reason Code"
    
    try:
        product_id_int = int(product_id)
        warehouse_id_int = int(warehouse_id)
        old_qty_int = int(old_qty)
        new_qty_int = int(new_qty)
        delta = new_qty_int - old_qty_int
    except (TypeError, ValueError):
        return "❌ Invalid values - Product ID, Warehouse ID and quantities must be whole numbers"
    
    user = get_user_email(request)
    sql = f"""
    INSERT INTO {CATALOG}.gold.inventory_adjustments
    (adjustment_id, product_id, warehouse_id, old_qty, new_qty, delta, reason_code, location, adjusted_by, adjusted_at, notes)
    VALUES
    (:adjustment_id, :product_id, :warehouse_id, :old_qty, :new_qty, :delta, :reason_code, :location, :user, CURRENT_TIMESTAMP(), :notes)
    """
    success, msg = execute_uc(sql, [
        {"name": "adjustment_id", "value": str(uuid.uuid4())},
        {"name": "product_id", "value": product_id_int},
        {"name": "warehouse_id", "value": warehouse_id_int},
        {"name": "old_qty", "value": old_qty_int},
        {"name": "new_qty", "value": new_qty_int},
        {"name": "delta", "value": delta},
        {"name": "reason_code", "value": str(reason_code)},
        {"name": "location", "value": str(location) if location else None},
        {"name": "user", "value": user},
        {"name": "notes", "value": str(notes) if notes else None},
    ])
    if success:
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        return f"✅ Inventory adjustment recorded by {user}\n\nProduct {product_id_int} at Warehouse {warehouse_id_int}\nSystem: {old_qty_int} → Physical: {new_qty_int} (Delta: {delta_str})\nReason: {reason_code}\n\nRefresh 'Recent Adjustments' to see your entry."
    return msg

# =====================================================================
# TAB 3: CUSTOMER PRIORITY FLAGS
# =====================================================================

def get_customers():
    """Get customer list"""
    sql = f"""
    SELECT 
        CustomerID,
        CustomerName,
        TotalSpend as TotalRevenue,
        TotalPurchases as TotalOrders,
        AvgOrderValue,
        DaysSinceLastPurchase as RecencyDays
    FROM {CATALOG}.gold.mart_customer_360
    ORDER BY TotalSpend DESC
    LIMIT 100
    """
    return query_uc(sql)

def get_priority_flags():
    """Get active customer priority flags"""
    sql = f"""
    SELECT 
        customer_id as CustomerID,
        priority_level as PriorityLevel,
        flag_type as FlagType,
        reason as Reason,
        valid_from as ValidFrom,
        valid_until as ValidUntil,
        created_by as CreatedBy,
        created_at as CreatedAt
    FROM {CATALOG}.gold.customer_priority_flags
    ORDER BY created_at DESC
    LIMIT 50
    """
    return query_uc(sql)

def set_customer_priority(customer_id, priority_level, flag_type, reason, valid_days, notes, request: gr.Request):
    """Set customer priority flag (parameterized)"""
    if not customer_id or not priority_level or not flag_type or not reason:
        return "❌ Please fill in Customer ID, Priority Level, Flag Type, and Reason"
    
    try:
        customer_id_int = int(customer_id)
    except (TypeError, ValueError):
        return "❌ Invalid Customer ID - must be a whole number"
    
    valid_days_int = 0
    if valid_days is not None and valid_days != "":
        try:
            valid_days_int = int(valid_days)
        except (TypeError, ValueError):
            return "❌ Invalid validity days - must be a whole number"
        if valid_days_int < 0:
            return "❌ Validity days cannot be negative"
    
    user = get_user_email(request)
    if valid_days_int > 0:
        valid_until_sql = f"CURRENT_TIMESTAMP() + INTERVAL {valid_days_int} DAYS"
    else:
        valid_until_sql = "NULL"
    
    sql = f"""
    INSERT INTO {CATALOG}.gold.customer_priority_flags
    (flag_id, customer_id, priority_level, flag_type, reason, valid_from, valid_until, created_by, created_at, notes)
    VALUES
    (:flag_id, :customer_id, :priority_level, :flag_type, :reason, CURRENT_TIMESTAMP(), {valid_until_sql}, :user, CURRENT_TIMESTAMP(), :notes)
    """
    success, msg = execute_uc(sql, [
        {"name": "flag_id", "value": str(uuid.uuid4())},
        {"name": "customer_id", "value": customer_id_int},
        {"name": "priority_level", "value": str(priority_level)},
        {"name": "flag_type", "value": str(flag_type)},
        {"name": "reason", "value": str(reason)},
        {"name": "user", "value": user},
        {"name": "notes", "value": str(notes) if notes else None},
    ])
    if success:
        return f"✅ Customer priority flag set by {user}\n\nCustomer {customer_id_int} marked as '{priority_level}'\nFlag Type: {flag_type}\nReason: {reason}\n\nRefresh 'Active Flags' to see your entry."
    return msg

# =====================================================================
# TAB 4: DATA QUALITY ISSUES
# =====================================================================

def get_data_quality_issues():
    """Get reported data quality issues"""
    sql = f"""
    SELECT 
        table_name as TableName,
        column_name as ColumnName,
        issue_type as IssueType,
        severity as Severity,
        description as Description,
        status as Status,
        reported_by as ReportedBy,
        reported_at as ReportedAt
    FROM {CATALOG}.gold.data_quality_issues
    ORDER BY 
        CASE severity 
            WHEN 'critical' THEN 1
            WHEN 'high' THEN 2
            WHEN 'medium' THEN 3
            WHEN 'low' THEN 4
        END,
        reported_at DESC
    LIMIT 100
    """
    return query_uc(sql)

def report_data_quality_issue(table_name, column_name, issue_type, severity, description, sample_records, request: gr.Request):
    """Report a data quality issue (parameterized, honest messaging)"""
    if not table_name or not issue_type or not severity or not description:
        return "❌ Please fill in Table Name, Issue Type, Severity, and Description"

    # Duplicate-issue validation: reject an identical OPEN issue (same table+type+description)
    dup = query_uc(f"""
        SELECT COUNT(*) AS c
        FROM {CATALOG}.gold.data_quality_issues
        WHERE table_name = :t AND issue_type = :it AND description = :d AND status = 'open'
    """, params=[
        {"name": "t", "value": str(table_name)},
        {"name": "it", "value": str(issue_type)},
        {"name": "d", "value": str(description)},
    ])
    if "Error" not in dup.columns and len(dup) and int(float(dup.iloc[0]["c"])) > 0:
        return "⚠️ An identical open issue already exists for this table — duplicate rejected. Check the issues list first or refine the description."
    
    user = get_user_email(request)
    sql = f"""
    INSERT INTO {CATALOG}.gold.data_quality_issues
    (issue_id, table_name, column_name, issue_type, severity, description, sample_records, reported_by, reported_at, status, assigned_to, resolved_at, resolution_notes)
    VALUES
    (:issue_id, :table_name, :column_name, :issue_type, :severity, :description, :sample_records, :user, CURRENT_TIMESTAMP(), 'open', NULL, NULL, NULL)
    """
    success, msg = execute_uc(sql, [
        {"name": "issue_id", "value": str(uuid.uuid4())},
        {"name": "table_name", "value": str(table_name)},
        {"name": "column_name", "value": str(column_name) if column_name else None},
        {"name": "issue_type", "value": str(issue_type)},
        {"name": "severity", "value": str(severity)},
        {"name": "description", "value": str(description)},
        {"name": "sample_records", "value": str(sample_records) if sample_records else None},
        {"name": "user", "value": user},
    ])
    if success:
        return f"✅ Data quality issue recorded by {user}\n\nTable: {table_name}\nSeverity: {severity}\nStatus: Open\n\nNote: the issue is logged for data-engineering review — no automatic notification is sent yet. Refresh the issues list to see your entry."
    return msg

# =====================================================================
# TAB 5: DEMAND FORECAST ADJUSTMENTS
# =====================================================================

def get_demand_forecasts():
    """Get demand forecasts from the ML demand_forecast table (source of truth)"""
    sql = f"""
    SELECT 
        product_id as ProductID,
        product_name as ProductName,
        forecast_date as ForecastDate,
        predicted_demand as ForecastQty,
        lower_bound as ConfidenceLower,
        upper_bound as ConfidenceUpper
    FROM {CATALOG}.gold.demand_forecast
    ORDER BY forecast_date DESC, predicted_demand DESC
    LIMIT 500
    """
    return query_uc(sql)

def get_forecast_adjustments():
    """Get recent forecast adjustments"""
    sql = f"""
    SELECT 
        product_id as ProductID,
        forecast_date as ForecastDate,
        ml_forecast_qty as MLForecast,
        adjustment_factor as Factor,
        adjusted_forecast_qty as AdjustedForecast,
        reason as Reason,
        adjusted_by as AdjustedBy,
        adjusted_at as AdjustedAt
    FROM {CATALOG}.gold.demand_forecast_adjustments
    ORDER BY adjusted_at DESC
    LIMIT 50
    """
    return query_uc(sql)

def adjust_demand_forecast(product_id, forecast_date, ml_forecast_qty, adjustment_factor, reason, event_type, notes, request: gr.Request):
    """Adjust demand forecast based on business knowledge (parameterized).
    Adjustments are recorded separately — the original ML prediction is never overwritten."""
    if product_id is None or not forecast_date or ml_forecast_qty is None or adjustment_factor is None or not reason:
        return "❌ Please fill in Product ID, Forecast Date, ML Forecast Qty, Adjustment Factor, and Reason"
    
    # Date validation: strict YYYY-MM-DD and a real calendar date
    date_str = str(forecast_date).strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return "❌ Invalid Forecast Date - use YYYY-MM-DD format (e.g., 2026-11-15)"
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return "❌ Invalid Forecast Date - not a real calendar date"
    
    try:
        product_id_int = int(product_id)
        ml_qty = int(ml_forecast_qty)
        adj_factor = float(adjustment_factor)
        if adj_factor <= 0:
            return "❌ Adjustment Factor must be a positive number (e.g., 0.8 or 1.5)"
        adjusted_qty = int(round(ml_qty * adj_factor))
    except (TypeError, ValueError):
        return "❌ Invalid numeric values - ML Forecast must be a whole number, Adjustment Factor must be a decimal (e.g., 1.5)"
    
    user = get_user_email(request)
    sql = f"""
    INSERT INTO {CATALOG}.gold.demand_forecast_adjustments
    (adjustment_id, product_id, forecast_date, ml_forecast_qty, adjustment_factor, adjusted_forecast_qty, reason, event_type, adjusted_by, adjusted_at, notes)
    VALUES
    (:adjustment_id, :product_id, CAST(:forecast_date AS DATE), :ml_qty, :adj_factor, :adjusted_qty, :reason, :event_type, :user, CURRENT_TIMESTAMP(), :notes)
    """
    success, msg = execute_uc(sql, [
        {"name": "adjustment_id", "value": str(uuid.uuid4())},
        {"name": "product_id", "value": product_id_int},
        {"name": "forecast_date", "value": date_str},
        {"name": "ml_qty", "value": ml_qty},
        {"name": "adj_factor", "value": adj_factor},
        {"name": "adjusted_qty", "value": adjusted_qty},
        {"name": "reason", "value": str(reason)},
        {"name": "event_type", "value": str(event_type) if event_type else None},
        {"name": "user", "value": user},
        {"name": "notes", "value": str(notes) if notes else None},
    ])
    if success:
        pct_change = int((adj_factor - 1) * 100)
        pct_str = f"+{pct_change}%" if pct_change > 0 else f"{pct_change}%"
        return f"✅ Demand forecast adjustment recorded by {user}\n\nProduct {product_id_int} on {date_str}\nML Forecast: {ml_qty} → Adjusted: {adjusted_qty} ({pct_str})\nReason: {reason}\n\nNote: the original ML prediction in {CATALOG}.gold.demand_forecast is not modified — this adjustment is a separate business override record."
    return msg

# =====================================================================
# OVERVIEW & UX HELPERS (BI UX upgrade — every value from live UC data)
# =====================================================================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Dark enterprise chart theme (all figures inherit)
plt.rcParams.update({
    "figure.facecolor": "#17233F", "axes.facecolor": "#17233F", "axes.edgecolor": "#3A4C77",
    "axes.labelcolor": "#C9D6EE", "text.color": "#E8EDF7", "axes.titlecolor": "#E8EDF7",
    "xtick.color": "#C9D6EE", "ytick.color": "#C9D6EE", "grid.color": "#223255",
    "font.size": 10, "axes.titlesize": 11.5, "axes.titleweight": "bold", "figure.dpi": 110,
})

HIGH_RISK_THRESHOLD = 0.5  # verified against data: matches model risk_segment split

GOLD_TABLES = [
    "churn_predictions", "mart_customer_360", "mart_inventory_health", "demand_forecast",
    "model_feedback", "churn_prediction_overrides", "inventory_adjustments",
    "customer_priority_flags", "data_quality_issues", "demand_forecast_adjustments",
]

CUSTOM_CSS = """
:root { color-scheme: dark; }
body { background: #0B1020 !important; }
.gradio-container { max-width: 1640px !important; font-size: 14.5px; background: #0B1020 !important;
  color: #E8EDF7 !important; font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
  padding-left: 252px; }
.gradio-container h1, .gradio-container h2, .gradio-container h3 { color: #FFFFFF !important; }

/* ---------- SIDEBAR: native tab nav restyled as fixed professional nav ---------- */
.gradio-container .tabs > nav, .gradio-container div.tab-container > nav {
  position: fixed; top: 68px; left: 0; bottom: 0; width: 236px; margin: 0;
  display: flex; flex-direction: column; gap: 4px; background: #111A35;
  border-right: 1px solid #223255; padding: 14px; z-index: 60; overflow-y: auto;
  box-shadow: 2px 0 18px rgba(0,0,0,0.35); }
.gradio-container .tabs > nav button, .gradio-container div.tab-container > nav button {
  display: flex; align-items: center; gap: 11px; justify-content: flex-start; width: 100%;
  padding: 11px 13px; border-radius: 9px; border: none; background: transparent;
  color: #8CA3C7; font-size: 14px; font-weight: 500; text-align: left; cursor: pointer;
  transition: background .15s, color .15s; white-space: nowrap; }
.gradio-container .tabs > nav button:hover, .gradio-container div.tab-container > nav button:hover { background: #1D2945; color: #E8EDF7; }
.gradio-container .tabs > nav button.selected, .gradio-container div.tab-container > nav button.selected {
  background: #3478F6; color: #FFFFFF !important; font-weight: 600;
  box-shadow: 0 4px 14px rgba(52,120,246,.35); }
/* Lucide-style icons (inline SVG masks, inherit button color) */
.gradio-container nav button::before { content: ""; width: 17px; height: 17px; flex: 0 0 17px;
  background: currentColor; -webkit-mask: var(--tabicon) center / contain no-repeat;
  mask: var(--tabicon) center / contain no-repeat; }
nav button:nth-child(1) { --tabicon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='3' width='7' height='9' rx='1'/><rect x='14' y='3' width='7' height='5' rx='1'/><rect x='14' y='12' width='7' height='9' rx='1'/><rect x='3' y='16' width='7' height='5' rx='1'/></svg>"); }
nav button:nth-child(2) { --tabicon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'/></svg>"); }
nav button:nth-child(3) { --tabicon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M21 8a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2'/><path d='M3 8v8a2 2 0 0 0 2 2h3l3 4 3-4h4a2 2 0 0 0 2-2V8'/><path d='M7 12h.01M11 12h.01M15 12h.01'/></svg>"); }
nav button:nth-child(4) { --tabicon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/><path d='M23 21v-2a4 4 0 0 0-3-3.87'/><path d='M16 3.13a4 4 0 0 1 0 7.75'/></svg>"); }
nav button:nth-child(5) { --tabicon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z'/></svg>"); }
nav button:nth-child(6) { --tabicon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polyline points='22 7 13.5 15.5 8.5 10.5 2 17'/><polyline points='16 7 22 7 22 13'/></svg>"); }

/* ---------- SIDEBAR BRAND (fixed, above nav) ---------- */
.sidebar-brand { position: fixed; top: 0; left: 0; width: 236px; height: 68px; z-index: 70;
  background: #111A35; border-bottom: 1px solid #223255; display: flex; align-items: center;
  gap: 10px; padding: 0 18px; margin: 0 !important; }
.sidebar-brand .brand-mark { width: 30px; height: 30px; border-radius: 8px; background: #3478F6;
  color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 15px;
  box-shadow: 0 4px 14px rgba(52,120,246,.4); }
.sidebar-brand .brand-name { color: #FFFFFF; font-weight: 700; font-size: 14.5px; line-height: 1.15; }
.sidebar-brand .brand-sub { color: #8CA3C7; font-size: 11px; letter-spacing: .05em; text-transform: uppercase; }

/* ---------- CARDS / PANELS / BUTTONS ---------- */
.block, .form, .panel { background: transparent; border-color: #223255 !important; }
.form, [data-testid="block-group"] { border-radius: 12px; }
.gradio-container button.primary, .gradio-container button.lg.primary { background: #3478F6 !important;
  color: #fff !important; border: 1px solid #3478F6 !important; border-radius: 8px !important; }
.gradio-container button.primary:hover { background: #2E6BE0 !important; }
.gradio-container button.secondary, .gradio-container button.lg.secondary { background: #1D2945 !important;
  color: #C9D6EE !important; border: 1px solid #2B3B63 !important; border-radius: 8px !important; }
.gradio-container button.secondary:hover { background: #24335A !important; }
.gradio-container .accordion { background: #1D2945 !important; border: 1px solid #223255; border-radius: 10px; }

/* ---------- KPI CARDS ---------- */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 8px 0 14px 0; }
.kpi-card { border: 1px solid #223255; border-left: 4px solid var(--accent, #3478F6); border-radius: 12px;
  padding: 14px 16px; background: #17233F; box-shadow: 0 2px 10px rgba(0,0,0,.25); }
.kpi-card .kpi-label { color: #8CA3C7; font-size: 12px; text-transform: uppercase; letter-spacing: .06em; }
.kpi-card .kpi-value { font-size: 27px; font-weight: 700; color: #FFFFFF; margin-top: 4px; }
.kpi-card .kpi-sub { color: #8CA3C7; font-size: 11.5px; margin-top: 3px; }

/* ---------- INSIGHTS PANEL ---------- */
.insight-panel { background: #17233F; border: 1px solid #223255; border-radius: 12px; padding: 14px 16px; margin: 6px 0; }
.insight-panel h4 { margin: 0 0 8px; font-size: 12.5px; color: #C9D6EE; text-transform: uppercase; letter-spacing: .06em; }
.insight-item { display: flex; justify-content: space-between; gap: 10px; padding: 7px 0;
  border-bottom: 1px solid #223255; color: #E8EDF7; font-size: 13px; }
.insight-item:last-child { border-bottom: none; }
.insight-sev-critical { color: #F04452; } .insight-sev-warning { color: #FFAA32; } .insight-sev-ok { color: #20C997; }
.insight-empty { color: #8CA3C7; font-size: 12.5px; padding: 4px 0; }

/* ---------- STATUS / TYPOGRAPHY ---------- */
.gradio-container .prose { color: #C9D6EE !important; }
.gradio-container .prose h1, .gradio-container .prose h2, .gradio-container .prose h3 { color: #FFFFFF !important; }

/* ---------- RESPONSIVE ---------- */
@media (max-width: 1100px) {
  .gradio-container { padding-left: 0; }
  .sidebar-brand { display: none; }
  .gradio-container .tabs > nav, .gradio-container div.tab-container > nav {
    position: static; width: auto; flex-direction: row; overflow-x: auto; padding: 8px;
    border-right: none; border-bottom: 1px solid #223255; box-shadow: none; }
  .gradio-container nav button { width: auto; white-space: nowrap; }
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 680px) {
  .kpi-grid { grid-template-columns: 1fr; }
  .gradio-container { font-size: 13.5px; }
}
"""

def _card(label, value, sub="", accent="#3478F6"):
    sub_html = f"<div class='kpi-sub'>{sub}</div>" if sub else ""
    return (f"<div class='kpi-card' style='--accent: {accent}'><div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value'>{value}</div>{sub_html}</div>")

def _fig(title, note="No data available yet"):
    fig, ax = plt.subplots(figsize=(6, 3.2))
    fig.patch.set_facecolor("#17233F")
    ax.text(0.5, 0.5, note, ha="center", va="center", fontsize=10, color="#8CA3C7", wrap=True)
    ax.set_title(title, fontsize=11)
    ax.axis("off")
    fig.tight_layout()
    return fig

def _num(df, col, default=0.0):
    try:
        return float(df.iloc[0][col])
    except Exception:
        return float(default)

def _bar_fig(title, df, x_col, y_col, xlabel, ylabel, order=None, color="#3478F6"):
    """Bar chart from a query_uc DataFrame; honest empty state when no/invalid data."""
    if df is None or len(df) == 0 or "Error" in df.columns:
        return _fig(title)
    try:
        pairs = [(str(x), float(y)) for x, y in zip(df[x_col], df[y_col])]
    except Exception:
        return _fig(title)
    if order:
        pos = {v: i for i, v in enumerate(order)}
        pairs.sort(key=lambda p: pos.get(p[0], 99))
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.bar([p[0] for p in pairs], [p[1] for p in pairs], color=color)
    ax.set_title(title, fontsize=11)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig

def _donut_fig(title, df, labels_col, values_col, colors=None):
    """Donut chart with real percentages + totals; honest empty state when no data."""
    if df is None or len(df) == 0 or "Error" in df.columns:
        return _fig(title)
    try:
        labels = [str(x) for x in df[labels_col]]
        values = [float(y) for y in df[values_col]]
    except Exception:
        return _fig(title)
    total = sum(values)
    if total <= 0:
        return _fig(title)
    palette = colors or ["#20C997", "#FFAA32", "#F04452", "#8655F7", "#3478F6"]
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    fig.patch.set_facecolor("#17233F")
    wedges, _, autotexts = ax.pie(
        values, labels=labels, colors=palette[:len(values)], startangle=90,
        autopct=lambda p: f"{p:.1f}%\n({int(round(p * total / 100)):,})",
        wedgeprops={"width": 0.42, "edgecolor": "#17233F", "linewidth": 2},
        textprops={"color": "#E8EDF7", "fontsize": 9}, pctdistance=0.79)
    for t in autotexts:
        t.set_fontsize(8)
    ax.set_title(f"{title} — total {int(total):,}", fontsize=11)
    ax.set_facecolor("#17233F")
    fig.tight_layout()
    return fig

def get_forecast_accuracy(days=None):
    """Forecast-vs-actual pairs + WMAPE (real gold+silver join, past forecast dates only).
    Optional `days` filters pairs to the selected Overview date range.
    Errors are logged, never silently swallowed."""
    _range_sql = ""
    if days:
        _range_sql = f" AND p.forecast_date >= CURRENT_DATE() - INTERVAL {int(days)} DAYS"
    pairs = query_uc(f"""
      WITH pairs AS (
        SELECT p.forecast_date, p.product_id,
               SUM(s.ProductQuantity) AS actual_qty,
               AVG(p.predicted_demand) AS pred_qty
        FROM {CATALOG}.silver.fact_sales s
        JOIN {CATALOG}.silver.dim_product d ON s.ProductSK = d.ProductSK
        JOIN {CATALOG}.silver.dim_date dt ON s.OrderDateID = dt.DateID
        JOIN {CATALOG}.gold.demand_forecast p ON p.product_id = d.ProductSK AND p.forecast_date = dt.Date
        WHERE p.forecast_date < CURRENT_DATE(){_range_sql}
        GROUP BY p.forecast_date, p.product_id
      )
      SELECT forecast_date, product_id, actual_qty, pred_qty FROM pairs ORDER BY forecast_date, product_id
    """)
    if "Error" in pairs.columns:
        print(f"❌ Overview forecast-accuracy query failed: {pairs.iloc[0, 0]}")
        return None, None
    _need = ("forecast_date", "product_id", "actual_qty", "pred_qty")
    if not all(c in pairs.columns for c in _need):
        print(f"❌ Forecast pairs malformed (columns={list(pairs.columns)[:8]}) — expected {_need}")
        return None, None
    if len(pairs) == 0:
        return None, pairs
    try:
        a = pairs["actual_qty"].astype(float)
        fc = pairs["pred_qty"].astype(float)
    except Exception as e:
        print(f"❌ Forecast pairs conversion failed: {e}")
        return None, pairs
    denom = a.sum()
    wmape = (a - fc).abs().sum() * 100.0 / denom if denom else None
    return wmape, pairs

def get_overview():
    """Overview tab: 8 KPIs + 5 charts, all computed from live UC data (no dummy values)."""
    kpi = query_uc(f"""
      SELECT
        (SELECT COUNT(*) FROM {CATALOG}.gold.mart_customer_360) AS total_customers,
        (SELECT COUNT(DISTINCT customer_id) FROM {CATALOG}.gold.churn_predictions
           WHERE churn_probability >= {HIGH_RISK_THRESHOLD}) AS high_risk,
        (SELECT COUNT(DISTINCT customer_id) FROM {CATALOG}.gold.churn_predictions) AS predicted_customers,
        (SELECT COUNT(*) FROM {CATALOG}.gold.mart_inventory_health WHERE StockStatus = 'In Stock') AS in_stock,
        (SELECT COUNT(*) FROM {CATALOG}.gold.mart_inventory_health) AS inv_rows,
        (SELECT COUNT(*) FROM {CATALOG}.gold.mart_inventory_health WHERE StockStatus = 'Low Stock') AS low_stock,
        (SELECT COUNT(*) FROM {CATALOG}.gold.mart_inventory_health WHERE StockStatus = 'Out of Stock') AS out_stock,
        (SELECT COUNT(*) FROM {CATALOG}.gold.data_quality_issues WHERE status = 'open') AS open_dq,
        (SELECT COUNT(*) FROM {CATALOG}.gold.inventory_adjustments
           WHERE adjusted_at >= CURRENT_TIMESTAMP() - INTERVAL 7 DAYS) AS inv_adj_7d,
        (SELECT COUNT(*) FROM {CATALOG}.gold.demand_forecast_adjustments
           WHERE adjusted_at >= CURRENT_TIMESTAMP() - INTERVAL 7 DAYS) AS fc_adj_7d
    """)
    if "Error" in kpi.columns:
        msg = str(kpi.iloc[0, 0])[:300]
        print(f"❌ Overview KPI query failed: {msg}")
        empty = [_fig("Churn Risk Distribution"), _fig("Inventory Health"),
                 _fig("Forecast vs Actual"), _fig("Customer Segmentation"), _fig("Data Quality")]
        return (f"<div class='kpi-card'><div class='kpi-label'>Overview</div>"
                f"<div class='kpi-value'>Unavailable</div><div class='kpi-sub'>{msg}</div></div>", *empty)
    tc, hr, pc = int(_num(kpi, "total_customers")), int(_num(kpi, "high_risk")), int(_num(kpi, "predicted_customers"))
    isk, ir, ls, os_ = (int(_num(kpi, "in_stock")), int(_num(kpi, "inv_rows")),
                        int(_num(kpi, "low_stock")), int(_num(kpi, "out_stock")))
    dq, ia, fa = int(_num(kpi, "open_dq")), int(_num(kpi, "inv_adj_7d")), int(_num(kpi, "fc_adj_7d"))
    churn_rate = f"{hr * 100.0 / pc:.1f}%" if pc else "N/A"
    inv_health = f"{isk * 100.0 / ir:.0f}%" if ir else "N/A"
    wmape, pairs = get_forecast_accuracy()
    if wmape is not None:
        acc_val = max(0.0, 100.0 - wmape)
        acc_sub = f"derived accuracy {acc_val:.0f}% (100 − WMAPE, floored at 0%) over {len(pairs)} product-day pairs"
        if wmape > 100:
            acc_sub += " — ⚠️ WMAPE above 100%"
        acc_value = f"{wmape:.1f}%"
    else:
        acc_sub = "no past forecast/actual overlap"
        acc_value = "N/A"
    kpi_html = "<div class='kpi-grid'>" + "".join([
        _card("Total Customers", f"{tc:,}", "mart_customer_360"),
        _card("High-Risk Customers", f"{hr:,}", f"churn probability ≥ {HIGH_RISK_THRESHOLD}"),
        _card("Customer Churn Rate", churn_rate, f"of {pc:,} predicted customers"),
        _card("Inventory Health", inv_health, f"{isk:,} of {ir:,} product-warehouse rows in stock"),
        _card("Low Stock Products", f"{ls:,}", f"plus {os_:,} out of stock"),
        _card("Forecast Error (WMAPE)", acc_value, acc_sub),
        _card("Open DQ Issues", f"{dq:,}", "status = open"),
        _card("Recent Adjustments (7d)", f"{ia + fa:,}", f"{ia} inventory · {fa} forecast"),
    ]) + "</div>"

    churn_dist = query_uc(f"""
      SELECT CASE WHEN churn_probability >= 0.7 THEN 'High ≥0.7'
                  WHEN churn_probability >= 0.5 THEN 'Medium 0.5-0.7'
                  ELSE 'Low <0.5' END AS band,
             COUNT(DISTINCT customer_id) AS customers
      FROM {CATALOG}.gold.churn_predictions GROUP BY 1
    """)
    churn_chart = _bar_fig("Customer Churn Risk Distribution", churn_dist, "band", "customers",
                           "Churn probability band", "Customers",
                           order=["Low <0.5", "Medium 0.5-0.7", "High ≥0.7"], color="#c0504d")

    inv_dist = query_uc(f"SELECT StockStatus, COUNT(*) AS products FROM {CATALOG}.gold.mart_inventory_health GROUP BY 1")
    inv_chart = _bar_fig("Inventory Health Distribution", inv_dist, "StockStatus", "products",
                         "Stock status", "Product-warehouse rows",
                         order=["In Stock", "Low Stock", "Out of Stock"], color="#4f81bd")

    if pairs is not None and len(pairs) > 0 and all(c in pairs.columns for c in ("forecast_date", "actual_qty", "pred_qty")):
        try:
            pdf = pd.DataFrame({"date": pd.to_datetime(pairs["forecast_date"]),
                                "actual": pairs["actual_qty"].astype(float),
                                "forecast": pairs["pred_qty"].astype(float)})
            g = pdf.groupby(pdf["date"].dt.date).agg(Actual=("actual", "sum"), Forecast=("forecast", "sum")).reset_index()
            fig, ax = plt.subplots(figsize=(6.4, 3.4))
            xs = list(range(len(g)))
            ax.plot(xs, g["Actual"], marker="o", label="Actual sales", color="#4f81bd")
            ax.plot(xs, g["Forecast"], marker="s", label="ML forecast", color="#c0504d")
            ax.set_xticks(xs); ax.set_xticklabels([str(d) for d in g["date"]], rotation=45, fontsize=8)
            ax.set_title("Demand Forecast vs Actual (past forecast days)", fontsize=11)
            ax.set_ylabel("Units (sum across products)")
            ax.legend(fontsize=9); ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
            fig.tight_layout()
            fc_chart = fig
        except Exception as e:
            print(f"❌ Forecast chart build failed: {e}")
            fc_chart = _fig("Demand Forecast vs Actual")
    else:
        fc_chart = _fig("Demand Forecast vs Actual", "No past forecast dates with actual sales yet")

    seg = query_uc(f"""
      SELECT CustomerSegment, COUNT(*) AS customers
      FROM {CATALOG}.gold.mart_customer_360 GROUP BY 1
    """)
    seg_chart = _bar_fig("Customer Segmentation", seg, "CustomerSegment", "customers",
                         "Segment", "Customers", color="#6d9e5f")

    dq_tr = query_uc(f"""
      SELECT CONCAT(severity, ' · ', status) AS s, COUNT(*) AS c
      FROM {CATALOG}.gold.data_quality_issues GROUP BY 1
    """)
    dq_chart = _bar_fig("Data Quality Issues by Severity & Status", dq_tr, "s", "c",
                        "Severity · status", "Issues", color="#b7a15c")

    return kpi_html, churn_chart, inv_chart, fc_chart, seg_chart, dq_chart

# ---------- Tab helpers (UX upgrade) ----------

def _parse_id(label):
    """Extract a numeric ID from a dropdown label like '16 — Dell Inspiron'."""
    try:
        return int(str(label).split("—")[0].strip())
    except (TypeError, ValueError):
        return None

def get_churn_predictions_display(customer_query=None):
    """Churn predictions with readable column names + risk band; optional customer search (parameterized)."""
    base = f"""
      SELECT customer_id AS `Customer ID`,
             ROUND(churn_probability, 3) AS `Churn Probability`,
             CASE WHEN churn_probability >= 0.7 THEN 'High (>= 0.7)'
                  WHEN churn_probability >= 0.5 THEN 'Medium (0.5 - 0.7)'
                  ELSE 'Low (< 0.5)' END AS `Risk Band`,
             risk_segment AS `Model Segment`,
             is_churned_predicted AS `Predicted Churn`,
             prediction_date AS `Predicted On`
      FROM {CATALOG}.gold.churn_predictions
    """
    if customer_query not in (None, ""):
        try:
            cid = int(str(customer_query).strip())
        except (TypeError, ValueError):
            return pd.DataFrame({"Message": ["Customer search expects a numeric Customer ID."]})
        return query_uc(base + " WHERE customer_id = :cid ORDER BY churn_probability DESC LIMIT 500",
                        params=[{"name": "cid", "value": cid}])
    return query_uc(base + " ORDER BY churn_probability DESC LIMIT 500")

def get_customer_context(customer_query):
    """Customer 360 + churn context panel for the Customer Priority tab (gold-only join)."""
    if customer_query in (None, ""):
        return "*Enter a Customer ID and click Load Context to see revenue, recency and churn risk.*"
    try:
        cid = int(str(customer_query).strip())
    except (TypeError, ValueError):
        return "❌ Customer ID must be a whole number."
    df = query_uc(f"""
      SELECT c.CustomerName AS name, c.City AS city, c.State AS state,
             c.CustomerSegment AS segment, c.ActivityStatus AS activity,
             c.TotalSpend AS spend, c.TotalPurchases AS orders, c.AvgOrderValue AS aov,
             c.DaysSinceLastPurchase AS recency,
             p.churn_probability AS prob, p.risk_segment AS risk
      FROM {CATALOG}.gold.mart_customer_360 c
      LEFT JOIN {CATALOG}.gold.churn_predictions p ON p.customer_id = c.CustomerID
      WHERE c.CustomerID = :cid
      ORDER BY p.churn_probability DESC
      LIMIT 1
    """, params=[{"name": "cid", "value": cid}])
    if "Error" in df.columns:
        return f"❌ {df.iloc[0, 0]}"
    if len(df) == 0:
        return f"No customer found with ID {cid}."
    r = df.iloc[0]
    prob = r["prob"]
    churn_line = "No churn prediction on file" if prob in (None, "None", "") else \
        f"Churn probability: **{float(prob):.3f}** ({r['risk']})"
    return (f"**{r['name']}** — {r['city']}, {r['state']}\n\n"
            f"Segment: {r['segment']} · Activity: {r['activity']}\n\n"
            f"Revenue: ₹{float(r['spend']):,.0f} · Orders: {float(r['orders']):,.0f} · "
            f"Avg order: ₹{float(r['aov']):,.0f} · Last purchase: {float(r['recency']):,.0f} days ago\n\n"
            f"{churn_line}")

def compute_delta(old_qty, new_qty):
    """Auto-calculated adjustment difference (pure Python, no SQL)."""
    try:
        return int(new_qty) - int(old_qty)
    except (TypeError, ValueError):
        return None

def compute_adjusted_qty(ml_qty, factor):
    """Auto-calculated adjusted forecast (pure Python, no SQL)."""
    try:
        return int(round(float(ml_qty) * float(factor)))
    except (TypeError, ValueError):
        return None

def submit_inventory_adjustment_ui(product_label, warehouse_id, old_qty, new_qty, reason_code, location, notes, request: gr.Request):
    """UI wrapper: converts the product dropdown label to a numeric product id."""
    pid = _parse_id(product_label)
    if pid is None:
        return "❌ Please select a product from the dropdown."
    res = submit_inventory_adjustment(pid, warehouse_id, old_qty, new_qty, reason_code, location, notes, request)
    if res.startswith("✅"):
        _CACHE.clear()
    return res

def adjust_demand_forecast_ui(product_label, forecast_date, ml_forecast_qty, adjustment_factor, reason, event_type, notes, request: gr.Request):
    """UI wrapper: converts the product dropdown label to a numeric product id."""
    pid = _parse_id(product_label)
    if pid is None:
        return "❌ Please select a product from the dropdown."
    res = adjust_demand_forecast(pid, forecast_date, ml_forecast_qty, adjustment_factor, reason, event_type, notes, request)
    if res.startswith("✅"):
        _CACHE.clear()
    return res

# =====================================================================
# INSIGHT-FIRST LAYER: TTL read cache, per-tab auto-loaders, distinct states
# (first tab open runs SQL; revisits within TTL reuse cache; Refresh forces)
# =====================================================================
import time

_CACHE = {}        # key -> (unix_ts, DataFrame); only successful reads are cached
CACHE_TTL_S = 300   # 5 minutes: revisits within TTL do not re-execute SQL

def cached_read(key, sql):
    """query_uc + TTL cache. Errors are never cached."""
    ent = _CACHE.get(key)
    now = time.time()
    if ent and (now - ent[0]) < CACHE_TTL_S:
        return ent[1]
    df = query_uc(sql)
    if "Error" not in df.columns:
        _CACHE[key] = (now, df)
    return df

def _safe_section(name, fn, fallback):
    """Run one Overview section independently — a failure in one KPI/chart/insights
    builder shows that section's own error card instead of crashing the whole
    Overview (2026-11-03 incident: one KeyError blanked every output)."""
    try:
        return fn()
    except Exception as e:
        print(f"❌ Overview section '{name}' failed: {type(e).__name__}: {str(e)[:200]}")
        return fallback

def _cached_fn(key, fn):
    """Cache wrapper around an existing read function (its SQL stays untouched)."""
    ent = _CACHE.get(key)
    now = time.time()
    if ent and (now - ent[0]) < CACHE_TTL_S:
        return ent[1]
    df = fn()
    if "Error" not in df.columns:
        _CACHE[key] = (now, df)
    return df

def _stamp(*keys):
    for k in keys:
        ent = _CACHE.get(k)
        if ent:
            return time.strftime("%H:%M:%S UTC", time.gmtime(ent[0]))
    return "not loaded"

def _state_md(df, what):
    """Distinct empty / query-error / permission-error states (the initial
    ⏳ markdown is the loading state, replaced on first auto-load)."""
    if "Error" in df.columns:
        msg = str(df.iloc[0, 0]).upper()
        if "PERMISSION" in msg or "DENIED" in msg or "UNAUTHORIZED" in msg or "403" in msg:
            return f"🔒 **Permission denied** — the app cannot read {what}. Contact your workspace admin. Details are in the app logs."
        return f"❌ **Query error** loading {what} — details are in the app logs."
    if len(df) == 0 or ("Message" in df.columns and len(df) <= 1):
        return f"📭 **No data yet** — {what} returned no rows."
    return f"✅ {len(df):,} rows"

def _forecast_fig(pairs):
    """Forecast-vs-actual line chart from real product-day pairs."""
    if pairs is None or len(pairs) == 0:
        return _fig("Demand Forecast vs Actual",
                   "No forecast-vs-actual pairs in the selected range.\n"
                   "Pairs exist only where forecast_date < today AND matching actual sales exist — "
                   "try a wider range (e.g. Last 30 Days).")
    if not all(c in pairs.columns for c in ("forecast_date", "actual_qty", "pred_qty")):
        return _fig("Demand Forecast vs Actual",
                   "Forecast pairs unavailable (query did not return the expected schema) — "
                   "details are in the app logs.")
    try:
        pdf = pd.DataFrame({"date": pd.to_datetime(pairs["forecast_date"]),
                            "actual": pairs["actual_qty"].astype(float),
                            "forecast": pairs["pred_qty"].astype(float)})
        g = pdf.groupby(pdf["date"].dt.date).agg(Actual=("actual", "sum"), Forecast=("forecast", "sum")).reset_index()
        fig, ax = plt.subplots(figsize=(6.4, 3.4))
        xs = list(range(len(g)))
        ax.plot(xs, g["Actual"], marker="o", label="Actual sales", color="#4f81bd")
        ax.plot(xs, g["Forecast"], marker="s", label="ML forecast", color="#c0504d")
        ax.set_xticks(xs); ax.set_xticklabels([str(d) for d in g["date"]], rotation=45, fontsize=8)
        ax.set_title("Demand Forecast vs Actual (past forecast days)", fontsize=11)
        ax.set_ylabel("Units (sum across products)")
        ax.legend(fontsize=9); ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        fig.tight_layout()
        return fig
    except Exception as e:
        print(f"❌ Forecast chart build failed: {e}")
        return _fig("Demand Forecast vs Actual")

def _wmape_md(wmape, pairs):
    """WMAPE shown SEPARATELY from the derived accuracy; >100% handled explicitly."""
    if wmape is None:
        if pairs is not None and len(pairs) == 0:
            return "📭 **No past forecast dates with actual sales** — accuracy cannot be computed yet."
        return "❌ **Forecast metrics unavailable** — details are in the app logs."
    acc = max(0.0, 100.0 - wmape)
    note = " ⚠️ WMAPE above 100% — derived accuracy floored at 0%" if wmape > 100 else ""
    return (f"**WMAPE (error):** {wmape:.1f}% · **Derived accuracy (100 − WMAPE):** {acc:.0f}% · "
            f"{len(pairs)} product-day pairs with actual sales{note}")

def load_tab1(force=False):
    """Auto-load drives the SAME paged query as Apply/Next so table, status and
    pagination always agree (fixes 'records loaded but pagination 0 of 0')."""
    if force:
        _CACHE.clear()
    fb = _cached_fn("t1_feedback", get_recent_feedback)
    ov = _cached_fn("t1_overrides", get_churn_overrides)
    dist = cached_read("t1_dist", f"""
      SELECT band, COUNT(*) AS customers FROM (
        SELECT CASE WHEN churn_probability >= 0.7 THEN 'High ≥0.7'
                    WHEN churn_probability >= 0.5 THEN 'Medium 0.5-0.7'
                    ELSE 'Low <0.5' END AS band,
               ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY prediction_date DESC) AS rn
        FROM {CATALOG}.gold.churn_predictions
      ) t WHERE t.rn = 1 GROUP BY 1
    """)
    fig = _bar_fig("Prediction Distribution (current band per scored customer)", dist, "band", "customers",
                   "Churn probability band", "Customers", order=["Low <0.5", "Medium 0.5-0.7", "High ≥0.7"], color="#c0504d")
    churn, total, pages, page = _churn_page(None, None, None, "Churn Probability (high first)", 0)
    if churn is None or "Error" in churn.columns:
        status = "❌ Churn query failed — details are in the app logs."
        page_md = status
    else:
        status = f"✅ {total:,} churn predictions available · 50 rows per page · refreshed {time.strftime('%H:%M:%S UTC', time.gmtime())}"
        page_md = f"Page {page + 1} of {pages} · showing {len(churn):,} of {total:,} rows"
    return status, churn, fig, fb, ov, page_md, page

def load_tab1_force():
    return load_tab1(True)

def load_tab2(force=False):
    """Auto-load drives the SAME paged query as Apply/Next (consistent pagination)."""
    if force:
        _CACHE.clear()
    adj = _cached_fn("t2_adjustments", get_recent_adjustments)
    dist = cached_read("t2_dist", f"SELECT StockStatus, COUNT(*) AS products FROM {CATALOG}.gold.mart_inventory_health GROUP BY 1")
    fig = _bar_fig("Stock Status Distribution (product-warehouse rows)", dist, "StockStatus", "products",
                   "Stock status", "Rows", order=["In Stock", "Low Stock", "Out of Stock"], color="#4f81bd")
    inv, total, pages, page = _inv_page(None, None, None, "Current Stock (lowest first)", 0)
    if inv is None or "Error" in inv.columns:
        status = "❌ Inventory query failed — details are in the app logs."
        page_md = status
    else:
        status = f"✅ {total:,} product-warehouse rows · 50 rows per page · refreshed {time.strftime('%H:%M:%S UTC', time.gmtime())}"
        page_md = f"Page {page + 1} of {pages} · showing {len(inv):,} of {total:,} rows"
    return status, fig, inv, adj, page_md, page

def load_tab2_force():
    return load_tab2(True)

def load_tab3(force=False):
    if force:
        _CACHE.clear()
    cust = _cached_fn("t3_customers", get_customers)
    flags = _cached_fn("t3_flags", get_priority_flags)
    seg = cached_read("t3_seg", f"SELECT CustomerSegment, COUNT(*) AS customers FROM {CATALOG}.gold.mart_customer_360 GROUP BY 1")
    act = cached_read("t3_act", f"SELECT ActivityStatus, COUNT(*) AS customers FROM {CATALOG}.gold.mart_customer_360 GROUP BY 1")
    seg_fig = _bar_fig("Customer Segmentation", seg, "CustomerSegment", "customers", "Segment", "Customers", color="#6d9e5f")
    act_fig = _bar_fig("Activity Status", act, "ActivityStatus", "customers", "Status", "Customers",
                       order=["Active", "Inactive"], color="#4f81bd")
    status = f"{_state_md(cust, 'customer analytics')} · refreshed {_stamp('t3_customers')}"
    return status, seg_fig, act_fig, cust, flags

def load_tab3_force():
    return load_tab3(True)

def load_tab4(force=False):
    if force:
        _CACHE.clear()
    issues = _cached_fn("t4_issues", get_data_quality_issues)
    tr = cached_read("t4_tr", f"SELECT CONCAT(severity, ' · ', status) AS s, COUNT(*) AS c FROM {CATALOG}.gold.data_quality_issues GROUP BY 1")
    fig = _bar_fig("Data Quality Issues by Severity & Status", tr, "s", "c", "Severity · status", "Issues", color="#b7a15c")
    status = f"{_state_md(issues, 'data quality issues')} · refreshed {_stamp('t4_issues')}"
    return status, fig, issues

def load_tab4_force():
    return load_tab4(True)

def load_tab5(force=False):
    if force:
        _CACHE.clear()
    fc = _cached_fn("t5_forecasts", get_demand_forecasts)
    adj = _cached_fn("t5_adjustments", get_forecast_adjustments)
    ent = _CACHE.get("t5_accuracy")
    now = time.time()
    if ent and (now - ent[0]) < CACHE_TTL_S:
        wmape, pairs = ent[1]
    else:
        wmape, pairs = get_forecast_accuracy()
        if wmape is not None:
            _CACHE["t5_accuracy"] = (now, (wmape, pairs))
    metrics = _wmape_md(wmape, pairs)
    fig = _forecast_fig(pairs)
    status = f"{_state_md(fc, 'demand forecasts')} · refreshed {_stamp('t5_forecasts')}"
    return status, metrics, fig, fc, adj

def load_tab5_force():
    return load_tab5(True)

# ---- Write wrappers: existing write functions untouched; cache cleared on
# ---- success so a user's new row is immediately visible (no stale reads).

def submit_model_feedback_ui(model_name, entity_id, prediction_value, actual_outcome, feedback_type, notes, request: gr.Request):
    res = submit_model_feedback(model_name, entity_id, prediction_value, actual_outcome, feedback_type, notes, request)
    if res.startswith("✅"):
        _CACHE.clear()
    return res

def override_churn_prediction_ui(customer_id, original_prob, override_prob, reason, valid_days, request: gr.Request):
    res = override_churn_prediction(customer_id, original_prob, override_prob, reason, valid_days, request)
    if res.startswith("✅"):
        _CACHE.clear()
    return res

def set_customer_priority_ui(customer_id, priority_level, flag_type, reason, valid_days, notes, request: gr.Request):
    res = set_customer_priority(customer_id, priority_level, flag_type, reason, valid_days, notes, request)
    if res.startswith("✅"):
        _CACHE.clear()
    return res

def report_data_quality_issue_ui(table_name, column_name, issue_type, severity, description, sample_records, request: gr.Request):
    res = report_data_quality_issue(table_name, column_name, issue_type, severity, description, sample_records, request)
    if res.startswith("✅"):
        _CACHE.clear()
    return res

# =====================================================================
# PREMIUM LAYER — date range, insights, donuts, filtered/paged module tables
# (read-only; every value comes from live UC queries — nothing invented;
#  all column lists mirror the live-validated queries above)
# =====================================================================

def _esc(s):
    """HTML-escape untrusted business text before embedding in panels."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))

def _range_days(mode, custom_from, custom_to):
    """Resolve the Overview date-range selector to (days, label) or (None, error markdown).
    `days` is always an int before it is ever interpolated into SQL."""
    mode = mode or "Last 30 Days"
    presets = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}
    if mode in presets:
        return presets[mode], mode.lower()
    if mode == "Custom Range":
        try:
            f = datetime.strptime((custom_from or "").strip(), "%Y-%m-%d")
            t = datetime.strptime((custom_to or "").strip(), "%Y-%m-%d")
        except ValueError:
            return None, "❌ **Custom range needs two dates formatted YYYY-MM-DD** (e.g. 2026-10-01 and 2026-10-31)"
        if t < f:
            return None, "❌ **Custom range invalid** — the 'to' date is before the 'from' date"
        return max((t - f).days + 1, 1), f"{f:%b %d} – {t:%b %d, %Y} (custom)"
    return 30, "last 30 days"

def _churn_trend():
    """Real high-risk trend vs the previous prediction snapshot. When only one
    snapshot exists, says so honestly — trends are NEVER invented."""
    try:
        df = query_uc(f"""SELECT prediction_date,
               SUM(CASE WHEN churn_probability >= {HIGH_RISK_THRESHOLD} THEN 1 ELSE 0 END) AS high_risk
               FROM {CATALOG}.gold.churn_predictions GROUP BY 1 ORDER BY 1 DESC LIMIT 2""")
        if df is None or "Error" in df.columns or len(df) == 0:
            return ""
        if len(df) < 2:
            return "single prediction snapshot — trend unavailable"
        cur_d, prev_d = str(df.iloc[0]["prediction_date"])[:10], str(df.iloc[1]["prediction_date"])[:10]
        delta = int(float(df.iloc[0]["high_risk"]) - float(df.iloc[1]["high_risk"]))
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "▬")
        return f"{arrow} {delta:+,} vs {prev_d} (latest run {cur_d})"
    except Exception as e:
        print(f"[trend] {e}")
        return ""

def get_insights_html(days, label):
    """Overview insights panel — every item from live queries; a section is
    omitted (or shown as honestly empty) when the data does not support it."""
    secs = []
    try:  # Why the customer counts differ (real reconciliation numbers)
        pops = query_uc(f"""
          SELECT (SELECT COUNT(DISTINCT CustomerID) FROM {CATALOG}.gold.mart_customer_360) AS mart_n,
                 (SELECT COUNT(DISTINCT customer_id) FROM {CATALOG}.gold.churn_predictions) AS scored_n,
                 (SELECT COUNT(DISTINCT p.customer_id) FROM {CATALOG}.gold.churn_predictions p
                    JOIN {CATALOG}.gold.mart_customer_360 m ON p.customer_id = m.CustomerID) AS both_n
        """)
        if pops is not None and "Error" not in pops.columns and len(pops):
            m_n, s_n, b_n = int(_num(pops, "mart_n")), int(_num(pops, "scored_n")), int(_num(pops, "both_n"))
            rows = ("<div class='insight-item'><span>Total Customers card: "
                    f"{m_n:,} customers with purchase history (mart_customer_360)</span></div>"
                    "<div class='insight-item'><span>Churn donut: "
                    f"{s_n:,} customers scored by the churn model (latest prediction each)</span></div>"
                    "<div class='insight-item'><span>Overlap: only "
                    f"{b_n:,} customers are in both — different populations by design, not a calculation error</span></div>")
            secs.append("<div class='insight-panel'><h4>Why the customer counts differ</h4>" + rows + "</div>")
    except Exception as e:
        print(f"[insights-populations] {e}")
    try:  # Products with stock issues
        low = query_uc(f"""SELECT ProductName, WarehouseName, CurrentStock, StockStatus
            FROM {CATALOG}.gold.mart_inventory_health
            WHERE StockStatus IN ('Low Stock', 'Out of Stock')
            ORDER BY CASE StockStatus WHEN 'Out of Stock' THEN 0 ELSE 1 END, CurrentStock ASC LIMIT 3""")
        if low is not None and "Error" not in low.columns and len(low):
            rows = "".join(
                f"<div class='insight-item'><span>{_esc(r.ProductName)} — {_esc(r.WarehouseName)}</span>"
                f"<span class='insight-sev-{'critical' if r.StockStatus == 'Out of Stock' else 'warning'}'>"
                f"{_esc(r.StockStatus)} · {_esc(r.CurrentStock)} units</span></div>" for r in low.itertuples())
            secs.append("<div class='insight-panel'><h4>Products with stock issues</h4>" + rows + "</div>")
        else:
            secs.append("<div class='insight-panel'><h4>Products with stock issues</h4>"
                        "<div class='insight-empty'>No low-stock or out-of-stock products right now.</div></div>")
    except Exception as e:
        print(f"[insights-stock] {e}")
    try:  # Customers requiring attention (highest churn risk)
        risk = query_uc(f"""SELECT c.CustomerName AS nm, c.CustomerSegment AS seg,
               ROUND(MAX(p.churn_probability), 3) AS prob
               FROM {CATALOG}.gold.mart_customer_360 c
               JOIN {CATALOG}.gold.churn_predictions p ON p.customer_id = c.CustomerID
               GROUP BY 1, 2 ORDER BY prob DESC LIMIT 3""")
        if risk is not None and "Error" not in risk.columns and len(risk):
            rows = "".join(
                f"<div class='insight-item'><span>{_esc(r.nm)} · {_esc(r.seg)}</span>"
                f"<span class='insight-sev-critical'>churn risk {_esc(r.prob)}</span></div>" for r in risk.itertuples())
            secs.append("<div class='insight-panel'><h4>Customers requiring attention (highest churn risk)</h4>" + rows + "</div>")
    except Exception as e:
        print(f"[insights-risk] {e}")
    try:  # Data quality warnings (reported within the selected range)
        dq = query_uc(f"""SELECT
              SUM(CASE WHEN severity IN ('critical','high') AND status = 'open' THEN 1 ELSE 0 END) AS serious,
              SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) AS open_all
              FROM {CATALOG}.gold.data_quality_issues
              WHERE reported_at >= CURRENT_TIMESTAMP() - INTERVAL {int(days)} DAYS""")
        if dq is not None and "Error" not in dq.columns and len(dq):
            o = int(float(dq.iloc[0]["open_all"] or 0)); s_ = int(float(dq.iloc[0]["serious"] or 0))
            sev = "insight-sev-critical" if s_ else ("insight-sev-warning" if o else "insight-sev-ok")
            note = f"{o} open ({s_} critical/high)" if o else "no open issues"
            secs.append(f"<div class='insight-panel'><h4>Data quality warnings — {label}</h4>"
                        f"<div class='insight-item'><span>Issues reported in the selected range</span>"
                        f"<span class='{sev}'>{note}</span></div></div>")
    except Exception as e:
        print(f"[insights-dq] {e}")
    try:  # Forecast anomalies (negative predicted demand — real model quality signal)
        neg = query_uc(f"SELECT COUNT(*) AS n, COUNT(DISTINCT product_id) AS p FROM {CATALOG}.gold.demand_forecast WHERE predicted_demand < 0")
        if neg is not None and "Error" not in neg.columns and len(neg):
            n, p = int(float(neg.iloc[0]["n"] or 0)), int(float(neg.iloc[0]["p"] or 0))
            if n:
                secs.append("<div class='insight-panel'><h4>Forecast anomalies</h4>"
                            "<div class='insight-item'><span>Forecasts with negative predicted demand</span>"
                            f"<span class='insight-sev-warning'>{n:,} rows across {p} products</span></div></div>")
    except Exception as e:
        print(f"[insights-neg] {e}")
    try:  # Recent team adjustments within the range
        adj = query_uc(f"""SELECT
              (SELECT COUNT(*) FROM {CATALOG}.gold.inventory_adjustments
                 WHERE adjusted_at >= CURRENT_TIMESTAMP() - INTERVAL {int(days)} DAYS) AS ia,
              (SELECT COUNT(*) FROM {CATALOG}.gold.demand_forecast_adjustments
                 WHERE adjusted_at >= CURRENT_TIMESTAMP() - INTERVAL {int(days)} DAYS) AS fa""")
        if adj is not None and "Error" not in adj.columns and len(adj):
            ia, fa = int(float(adj.iloc[0]["ia"] or 0)), int(float(adj.iloc[0]["fa"] or 0))
            if ia or fa:
                secs.append(f"<div class='insight-panel'><h4>Team activity — {label}</h4>"
                            "<div class='insight-item'><span>Manual adjustments by your team</span>"
                            f"<span class='insight-sev-ok'>{ia} inventory · {fa} forecast</span></div></div>")
    except Exception as e:
        print(f"[insights-adj] {e}")
    if not secs:
        return "<div class='insight-panel'><h4>Business Insights</h4><div class='insight-empty'>No insights available for this range yet.</div></div>"
    return "<div class='kpi-grid' style='grid-template-columns: repeat(2, 1fr)'>" + "".join(secs) + "</div>"

def get_overview_v2(range_mode="Last 30 Days", custom_from=None, custom_to=None, force=False):
    """Landing page: 4 accent KPI cards, churn + inventory donuts, forecast-vs-actual
    line and a real insights panel. The date range genuinely filters every query
    that carries timestamps (WMAPE pairs, DQ issues, team adjustments)."""
    if force:
        for k in [k for k in list(_CACHE) if k.startswith("ov_")]:
            _CACHE.pop(k, None)
    days, label = _range_days(range_mode, custom_from, custom_to)
    if days is None:
        kpi_html = "<div class='kpi-grid'>" + _card("Date Range", "⚠️", label.replace("**", ""), "#FFAA32") + "</div>"
        return (kpi_html, _fig("Customer Churn Risk Distribution"), _fig("Inventory Health"),
                _fig("Demand Forecast vs Actual"),
                "<div class='insight-panel'><h4>Business Insights</h4><div class='insight-empty'>Fix the date range to load insights.</div></div>", label)
    kpi = cached_read(f"ov_kpi_{days}", f"""
      SELECT (SELECT COUNT(*) FROM {CATALOG}.gold.mart_customer_360) AS total_customers,
             (SELECT COUNT(DISTINCT customer_id) FROM {CATALOG}.gold.churn_predictions
                WHERE churn_probability >= {HIGH_RISK_THRESHOLD}) AS high_risk,
             (SELECT COUNT(*) FROM {CATALOG}.gold.mart_inventory_health WHERE StockStatus = 'In Stock') AS in_stock,
             (SELECT COUNT(*) FROM {CATALOG}.gold.mart_inventory_health) AS inv_rows,
             (SELECT COUNT(*) FROM {CATALOG}.gold.mart_inventory_health WHERE StockStatus = 'Low Stock') AS low_stock,
             (SELECT COUNT(*) FROM {CATALOG}.gold.mart_inventory_health WHERE StockStatus = 'Out of Stock') AS out_stock
    """)
    if "Error" in kpi.columns:
        msg = str(kpi.iloc[0, 0])[:300]
        print(f"❌ Overview KPI query failed: {msg}")
        return ("<div class='kpi-grid'>" + _card("Overview", "Unavailable", msg, "#F04452") + "</div>",
                _fig("Customer Churn Risk Distribution"), _fig("Inventory Health"), _fig("Demand Forecast vs Actual"),
                "<div class='insight-panel'><h4>Business Insights</h4><div class='insight-empty'>KPI query failed — details are in the app logs.</div></div>",
                "❌ KPI query failed — details are in the app logs.")
    ent = _CACHE.get(f"ov_acc_{days}")
    now = time.time()
    if ent and (now - ent[0]) < CACHE_TTL_S:
        wmape, pairs = ent[1]
    else:
        wmape, pairs = get_forecast_accuracy(days)
        if wmape is not None:
            _CACHE[f"ov_acc_{days}"] = (now, (wmape, pairs))

    def _kpi_cards():
        tc, hr = int(_num(kpi, "total_customers")), int(_num(kpi, "high_risk"))
        isk, ir = int(_num(kpi, "in_stock")), int(_num(kpi, "inv_rows"))
        ls, os_ = int(_num(kpi, "low_stock")), int(_num(kpi, "out_stock"))
        inv_health = f"{isk * 100.0 / ir:.0f}%" if ir else "N/A"
        if wmape is not None:
            acc = max(0.0, 100.0 - wmape)
            fc_val = f"{wmape:.1f}%"
            fc_sub = f"derived accuracy {acc:.0f}% (100 − WMAPE) · {len(pairs)} product-day pairs in {label}"
            if wmape > 100:
                fc_sub += " — ⚠️ WMAPE above 100%, accuracy floored at 0%"
        else:
            _, pairs_all = get_forecast_accuracy()
            if pairs_all is not None and "forecast_date" in getattr(pairs_all, "columns", []) and len(pairs_all):
                fc_sub = (f"no pairs in {label} — {len(pairs_all)} pairs exist all-time "
                          f"({pairs_all.iloc[0]['forecast_date']} → {pairs_all.iloc[-1]['forecast_date']}); "
                          f"try Last 30 Days")
            else:
                fc_sub = "no past forecast dates with actual sales anywhere yet"
            fc_val = "N/A"
        return "<div class='kpi-grid'>" + "".join([
            _card("Total Customers", f"{tc:,}", "customers with purchase history (mart_customer_360, all-time)", "#3478F6"),
            _card("High-Risk Customers", f"{hr:,}", ((_churn_trend() + " · ") if _churn_trend() else "") +
                  f"churn-scored customers, any prediction ≥ {HIGH_RISK_THRESHOLD}", "#F04452"),
            _card("Inventory Health", inv_health, f"{isk:,} of {ir:,} in stock · {ls:,} low · {os_:,} out of stock", "#20C997"),
            _card("Forecast Error (WMAPE)", fc_val, fc_sub, "#8655F7"),
        ]) + "</div>"

    # Every section renders independently — one failing query can never
    # blank out the whole Overview again (2026-11-03 forecast_date incident).
    kpi_html = _safe_section("kpi_cards", _kpi_cards,
        "<div class='kpi-grid'>" + _card("Overview", "Unavailable",
            "KPI build failed — details are in the app logs.", "#F04452") + "</div>")
    cd = cached_read("ov_churndist", f"""
      SELECT band, COUNT(*) AS customers FROM (
        SELECT CASE WHEN churn_probability >= 0.7 THEN 'High ≥ 0.7'
                    WHEN churn_probability >= 0.5 THEN 'Medium 0.5-0.7'
                    ELSE 'Low <0.5' END AS band,
               ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY prediction_date DESC) AS rn
        FROM {CATALOG}.gold.churn_predictions
      ) t WHERE t.rn = 1 GROUP BY 1
      ORDER BY CASE band WHEN 'Low <0.5' THEN 1 WHEN 'Medium 0.5-0.7' THEN 2 ELSE 3 END
    """)
    churn_fig = _safe_section("churn_donut",
        lambda: _donut_fig("Churn Risk Distribution (current band per scored customer)", cd, "band", "customers",
                           ["#20C997", "#FFAA32", "#F04452"]),
        _fig("Customer Churn Risk Distribution", "Churn data unavailable — details are in the app logs."))
    idist = cached_read("ov_invdist", f"""SELECT StockStatus, COUNT(*) AS products
      FROM {CATALOG}.gold.mart_inventory_health GROUP BY 1
      ORDER BY CASE StockStatus WHEN 'In Stock' THEN 1 WHEN 'Low Stock' THEN 2 ELSE 3 END""")
    inv_fig = _safe_section("inv_donut",
        lambda: _donut_fig("Inventory Health", idist, "StockStatus", "products", ["#20C997", "#FFAA32", "#F04452"]),
        _fig("Inventory Health", "Inventory data unavailable — details are in the app logs."))
    fc_fig = _safe_section("forecast_chart", lambda: _forecast_fig(pairs),
        _fig("Demand Forecast vs Actual", "Forecast chart unavailable — details are in the app logs."))
    ins = _safe_section("insights", lambda: get_insights_html(days, label),
        "<div class='insight-panel'><h4>Business Insights</h4><div class='insight-empty'>Insights unavailable — details are in the app logs.</div></div>")
    status = f"✅ Overview loaded · range: {label} · refreshed {time.strftime('%H:%M:%S UTC', time.gmtime())}"
    return kpi_html, churn_fig, inv_fig, fc_fig, ins, status

# ---------- Filtered / paged module tables (parameterized SQL, whitelisted ORDER BY) ----------

PAGE_SIZE = 50

CHURN_SORTS = {
    "Churn Probability (high first)": "`Churn Probability` DESC",
    "Churn Probability (low first)": "`Churn Probability` ASC",
    "Customer ID": "`Customer ID` ASC",
    "Predicted On (newest)": "`Predicted On` DESC",
}
INV_SORTS = {
    "Current Stock (lowest first)": "`Current Stock` ASC",
    "Current Stock (highest first)": "`Current Stock` DESC",
    "Product Name": "`Product` ASC",
    "Stock Value (highest)": "`Stock Value` DESC",
    "Stock Status": "`Status` ASC",
}

def _paged(base, where, params, order, page):
    """COUNT-then-page read; ORDER BY comes only from the whitelists above.
    Returns (df, total, pages, page) — page is clamped to real bounds."""
    try:
        cnt = query_uc(f"SELECT COUNT(*) AS n FROM ({base} {where}) t", params)
        if cnt is None or "Error" in cnt.columns:
            return (cnt if cnt is not None else pd.DataFrame({"Error": ["count query failed"]})), 0, 1, 0
        total = int(float(cnt.iloc[0]["n"]))
        pages = max(1, -(-total // PAGE_SIZE))
        page = max(0, min(int(page or 0), pages - 1))
        df = query_uc(f"SELECT * FROM ({base} {where}) t ORDER BY {order} LIMIT {PAGE_SIZE} OFFSET {page * PAGE_SIZE}", params)
        return df, total, pages, page
    except Exception as e:
        print(f"❌ Paged query failed: {e}")
        return pd.DataFrame({"Error": [str(e)[:300]]}), 0, 1, 0

def _churn_page(search, risk, segment, sort, page):
    """Churn table with search + risk/segment filters (columns mirror the
    live-validated churn display + the validated mart join)."""
    base = f"""
      SELECT p.customer_id AS `Customer ID`,
             ROUND(p.churn_probability, 3) AS `Churn Probability`,
             CASE WHEN p.churn_probability >= 0.7 THEN 'High (>= 0.7)'
                  WHEN p.churn_probability >= 0.5 THEN 'Medium (0.5 - 0.7)'
                  ELSE 'Low (< 0.5)' END AS `Risk Band`,
             c.CustomerSegment AS `Customer Segment`,
             p.risk_segment AS `Model Segment`,
             p.prediction_date AS `Predicted On`
      FROM {CATALOG}.gold.churn_predictions p
      LEFT JOIN {CATALOG}.gold.mart_customer_360 c ON c.CustomerID = p.customer_id
    """
    where, params = " WHERE 1=1", []
    s = (search or "").strip()
    if s:
        try:
            params.append({"name": "cid", "value": int(s)})
            where += " AND p.customer_id = :cid"
        except ValueError:
            pass  # non-numeric search is ignored (the control hints numeric IDs)
    if risk == "High (>= 0.7)":
        where += " AND p.churn_probability >= 0.7"
    elif risk == "Medium (0.5 - 0.7)":
        where += " AND p.churn_probability >= 0.5 AND p.churn_probability < 0.7"
    elif risk == "Low (< 0.5)":
        where += " AND p.churn_probability < 0.5"
    if segment:
        params.append({"name": "seg", "value": str(segment)})
        where += " AND c.CustomerSegment = :seg"
    order = CHURN_SORTS.get(sort, CHURN_SORTS["Churn Probability (high first)"])
    return _paged(base, where, params, order, page)

def render_churn(search, risk, segment, sort, page):
    df, total, pages, page = _churn_page(search, risk, segment, sort, page)
    if df is None or "Error" in df.columns:
        md = "❌ Query failed — details are in the app logs."
    elif total == 0:
        md = "🔍 **No records match the current filters** — clear filters or widen your search."
    else:
        md = f"Page {page + 1} of {pages} · showing {len(df):,} of {total:,} rows"
    details = get_customer_context(search) if (search or "").strip() else \
        "*Enter a numeric Customer ID above and click Apply to load full customer details here.*"
    return df, md, page, details

def clear_churn_filters():
    """Reset every T1 filter control and re-render the default first page."""
    df, md, page, details = render_churn(None, None, None, "Churn Probability (high first)", 0)
    return (gr.update(value=""), gr.update(value="All"), gr.update(value="All"),
            gr.update(value="Churn Probability (high first)"), df, md, page, details)

def _inv_page(search, warehouse, status, sort, page):
    """Inventory table with search + warehouse/status filters (columns mirror the
    live-validated inventory mart query)."""
    base = f"""
      SELECT ProductSK AS `Product ID`, ProductName AS `Product`,
             WarehouseName AS `Warehouse`, CurrentStock AS `Current Stock`,
             CurrentStockValue AS `Stock Value`, StockStatus AS `Status`,
             CASE WHEN StockStatus = 'Out of Stock' THEN 'Understock' ELSE HealthStatus END AS `Health (aging)`
      FROM {CATALOG}.gold.mart_inventory_health
      -- Health(aging) rule: Understock if Low/Out of Stock, Overstock if snapshot >60d old, else Healthy.
      -- App-side guard: zero stock is never 'Healthy' (upstream dbt CASE gap — see audit 2026-11-03).
    """
    where, params = " WHERE 1=1", []
    s = (search or "").strip()
    if s:
        params.append({"name": "q", "value": f"%{s}%"})
        where += " AND ProductName LIKE :q"
    if warehouse:
        params.append({"name": "wh", "value": str(warehouse)})
        where += " AND WarehouseName = :wh"
    if status:
        params.append({"name": "st", "value": str(status)})
        where += " AND StockStatus = :st"
    order = INV_SORTS.get(sort, INV_SORTS["Current Stock (lowest first)"])
    return _paged(base, where, params, order, page)

def render_inventory(search, warehouse, status, sort, page):
    df, total, pages, page = _inv_page(search, warehouse, status, sort, page)
    if df is None or "Error" in df.columns:
        md = "❌ Query failed — details are in the app logs."
    elif total == 0:
        md = "🔍 **No records match the current filters** — clear filters or widen your search."
    else:
        md = f"Page {page + 1} of {pages} · showing {len(df):,} of {total:,} rows"
    return df, md, page

def clear_inventory_filters():
    """Reset every T2 filter control and re-render the default first page."""
    df, md, page = render_inventory(None, None, None, "Current Stock (lowest first)", 0)
    return (gr.update(value=""), gr.update(value="All"), gr.update(value="All"),
            gr.update(value="Current Stock (lowest first)"), df, md, page)

def render_customers(search, segment):
    """Customer analytics table (columns mirror the live-validated customer query)."""
    base = f"""
      SELECT CustomerID AS `Customer ID`, CustomerName AS `Name`,
             TotalSpend AS `Revenue`, TotalPurchases AS `Orders`,
             AvgOrderValue AS `Avg Order Value`, DaysSinceLastPurchase AS `Recency (days)`,
             CustomerSegment AS `Segment`, ActivityStatus AS `Activity`
      FROM {CATALOG}.gold.mart_customer_360
    """
    where, params = " WHERE 1=1", []
    s = (search or "").strip()
    if s:
        try:
            params.append({"name": "cid", "value": int(s)})
            where += " AND CustomerID = :cid"
        except ValueError:
            params.append({"name": "q", "value": f"%{s}%"})
            where += " AND CustomerName LIKE :q"
    if segment:
        params.append({"name": "seg", "value": str(segment)})
        where += " AND CustomerSegment = :seg"
    return query_uc(base + where + " ORDER BY TotalSpend DESC LIMIT 100", params)

def render_dq(severity, status, issue_type=None, table=None):
    """DQ issues with severity/status/issue-type/affected-table filters (parameterized)."""
    base = f"""
      SELECT table_name AS `Table`, column_name AS `Column`, issue_type AS `Type`,
             severity AS `Severity`, description AS `Description`, status AS `Status`,
             reported_by AS `Reporter`, reported_at AS `Reported`
      FROM {CATALOG}.gold.data_quality_issues
    """
    where, params = " WHERE 1=1", []
    if severity:
        params.append({"name": "sev", "value": str(severity)})
        where += " AND severity = :sev"
    if status:
        params.append({"name": "st", "value": str(status)})
        where += " AND status = :st"
    if issue_type:
        params.append({"name": "it", "value": str(issue_type)})
        where += " AND issue_type = :it"
    if table:
        params.append({"name": "tb", "value": str(table)})
        where += " AND table_name = :tb"
    return query_uc(base + where + """ ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2
               WHEN 'medium' THEN 3 ELSE 4 END, reported_at DESC LIMIT 100""", params)

def render_forecasts(product_label, d_from=None, d_to=None):
    """Product + forecast-date-range filtered forecasts (parameterized; dates validated)."""
    base = f"""
      SELECT product_id AS `Product ID`, product_name AS `Product`,
             forecast_date AS `Forecast Date`, predicted_demand AS `Forecast Qty`,
             lower_bound AS `Confidence Lower`, upper_bound AS `Confidence Upper`
      FROM {CATALOG}.gold.demand_forecast
    """
    where, params = " WHERE 1=1", []
    if product_label and product_label != "All":
        pid = _parse_id(product_label)
        if pid is not None:
            params.append({"name": "pid", "value": pid})
            where += " AND product_id = :pid"
    s = (d_from or "").strip()
    if s:
        try:
            fd = str(datetime.strptime(s, "%Y-%m-%d").date())
        except ValueError:
            return pd.DataFrame({"Error": [f"❌ Invalid 'from' date '{s}' — use YYYY-MM-DD"]})
        params.append({"name": "fd", "value": fd})
        where += " AND forecast_date >= CAST(:fd AS DATE)"
    s = (d_to or "").strip()
    if s:
        try:
            ft = str(datetime.strptime(s, "%Y-%m-%d").date())
        except ValueError:
            return pd.DataFrame({"Error": [f"❌ Invalid 'to' date '{s}' — use YYYY-MM-DD"]})
        params.append({"name": "ft", "value": ft})
        where += " AND forecast_date <= CAST(:ft AS DATE)"
    return query_uc(base + where + " ORDER BY forecast_date DESC, predicted_demand DESC LIMIT 500", params)

def render_flags(priority=None):
    """Active priority flags with optional priority-level filter (parameterized)."""
    base = f"""
      SELECT customer_id AS `CustomerID`, priority_level AS `PriorityLevel`,
             flag_type AS `FlagType`, reason AS `Reason`, valid_from AS `ValidFrom`,
             valid_until AS `ValidUntil`, created_by AS `CreatedBy`, created_at AS `CreatedAt`
      FROM {CATALOG}.gold.customer_priority_flags
    """
    where, params = " WHERE 1=1", []
    if priority:
        params.append({"name": "p", "value": str(priority)})
        where += " AND priority_level = :p"
    return query_uc(base + where + " ORDER BY created_at DESC LIMIT 50", params)

# Dropdown choices loaded once at startup (safe empty fallback on failure)
PRODUCT_CHOICES = []
FC_PRODUCT_CHOICES = []
try:
    _prods = query_uc(f"SELECT DISTINCT ProductSK, ProductName FROM {CATALOG}.gold.mart_inventory_health ORDER BY ProductSK")
    if "Error" not in _prods.columns:
        PRODUCT_CHOICES = [f"{int(float(a))} — {b}" for a, b in zip(_prods["ProductSK"], _prods["ProductName"])]
except Exception as e:
    print(f"⚠️ Product dropdown could not load: {e}")
try:
    _fc = query_uc(f"SELECT product_id, product_name FROM {CATALOG}.gold.demand_forecast ORDER BY product_id")
    if "Error" not in _fc.columns:
        _seen = set()
        for a, b in zip(_fc["product_id"], _fc["product_name"]):
            _pid = int(float(a))
            if _pid not in _seen:
                _seen.add(_pid)
                FC_PRODUCT_CHOICES.append(f"{_pid} — {b}")
except Exception as e:
    print(f"⚠️ Forecast product dropdown could not load: {e}")
SEGMENT_CHOICES = []
try:
    _segs = query_uc(f"SELECT DISTINCT CustomerSegment FROM {CATALOG}.gold.mart_customer_360 ORDER BY 1")
    if "Error" not in _segs.columns:
        SEGMENT_CHOICES = [str(x) for x in _segs["CustomerSegment"] if str(x) not in ("", "None")]
except Exception as e:
    print(f"⚠️ Segment dropdown could not load: {e}")
WAREHOUSE_CHOICES = []
try:
    _whs = query_uc(f"SELECT DISTINCT WarehouseName FROM {CATALOG}.gold.mart_inventory_health ORDER BY 1")
    if "Error" not in _whs.columns:
        WAREHOUSE_CHOICES = [str(x) for x in _whs["WarehouseName"] if str(x) not in ("", "None")]
except Exception as e:
    print(f"⚠️ Warehouse dropdown could not load: {e}")
DQ_ISSUE_TYPES = []
try:
    _dit = query_uc(f"SELECT DISTINCT issue_type AS v FROM {CATALOG}.gold.data_quality_issues ORDER BY 1")
    if "Error" not in _dit.columns:
        DQ_ISSUE_TYPES = [str(x) for x in _dit["v"] if str(x) not in ("", "None")]
except Exception as e:
    print(f"⚠️ DQ issue-type dropdown could not load: {e}")
DQ_TABLES = []
try:
    _dtb = query_uc(f"SELECT DISTINCT table_name AS v FROM {CATALOG}.gold.data_quality_issues ORDER BY 1")
    if "Error" not in _dtb.columns:
        DQ_TABLES = [str(x) for x in _dtb["v"] if str(x) not in ("", "None")]
except Exception as e:
    print(f"⚠️ DQ table dropdown could not load: {e}")

# =====================================================================
# GRADIO UI - PRODUCTION GRADE
# =====================================================================

with gr.Blocks(title="Business Intelligence Center", theme=gr.themes.Soft(), css=CUSTOM_CSS) as demo:
    gr.HTML(
        "<div class='sidebar-brand'><div class='brand-mark'>SP</div>"
        "<div><div class='brand-name'>SkillAIPath</div>"
        "<div class='brand-sub'>BI Center</div></div></div>")
    gr.Markdown("# Business Intelligence Center")
    gr.Markdown("### Explore insights, monitor performance and take action on your business data")
    gr.Markdown(f"*App identity:* `{APP_IDENTITY}` — your actions are recorded under your Databricks login")

    # TAB 0: OVERVIEW — landing page (real data; range filters timestamped queries)
    with gr.Tab("Overview") as tab0:
        ov_status = gr.Markdown("⏳ Loading overview…")
        with gr.Row():
            range_mode = gr.Radio(["Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"],
                                  value="Last 30 Days", label="Date Range", scale=3)
            with gr.Column(scale=2, min_width=190, visible=False):
                custom_from = gr.Textbox(label="From (YYYY-MM-DD)", placeholder="2026-10-01")
                custom_to = gr.Textbox(label="To (YYYY-MM-DD)", placeholder="2026-10-31")
            with gr.Column(scale=1, min_width=170):
                apply_range_btn = gr.Button("Apply Range", variant="primary")
                ov_refresh = gr.Button("🔄 Refresh Overview", variant="secondary")
        kpi_html = gr.HTML()
        with gr.Row():
            churn_fig = gr.Plot(label="Customer Churn Risk Distribution")
            inv_fig = gr.Plot(label="Inventory Health")
            fc_fig = gr.Plot(label="Demand Forecast vs Actual")
        insights_html = gr.HTML()
        ov_out = [kpi_html, churn_fig, inv_fig, fc_fig, insights_html, ov_status]
        apply_range_btn.click(get_overview_v2, inputs=[range_mode, custom_from, custom_to], outputs=ov_out)
        ov_refresh.click(lambda m, f, t: get_overview_v2(m, f, t, force=True),
                         inputs=[range_mode, custom_from, custom_to], outputs=ov_out)
        def _range_ux(mode):
            """Custom-date boxes appear ONLY for Custom Range; presets clear stale values."""
            vis = mode == "Custom Range"
            return gr.update(visible=vis, value=""), gr.update(visible=vis, value="")
        range_mode.change(_range_ux, inputs=range_mode, outputs=[custom_from, custom_to])
    
    # TAB 1: AI MODEL FEEDBACK — insight-first: predictions auto-load; forms collapsed
    with gr.Tab("AI Model Feedback") as tab1:
        gr.Markdown("### AI Churn Predictions")
        t1_status = gr.Markdown("⏳ Loading predictions…")
        with gr.Row():
            churn_search = gr.Textbox(label="Customer ID (numeric)", placeholder="Search by customer ID…", scale=2)
            churn_risk = gr.Dropdown(["All", "High (>= 0.7)", "Medium (0.5 - 0.7)", "Low (< 0.5)"], value="All", label="Risk Level", scale=1)
            churn_segment = gr.Dropdown(["All"] + SEGMENT_CHOICES, value="All", label="Customer Segment", scale=1)
            churn_sort = gr.Dropdown(list(CHURN_SORTS), value="Churn Probability (high first)", label="Sort By", scale=1)
            churn_apply = gr.Button("🔎 Apply", variant="primary", scale=1)
            churn_clear = gr.Button("✖ Clear", scale=1)
            t1_refresh = gr.Button("🔄 Refresh", scale=1)
        t1_dist_fig = gr.Plot(label="Prediction Distribution")
        churn_df = gr.Dataframe(interactive=False, height=300)
        with gr.Row():
            churn_prev = gr.Button("◀ Prev", scale=1)
            churn_page_md = gr.Markdown("Page 1 of …")
            churn_next = gr.Button("Next ▶", scale=1)
        churn_state = gr.State(0)
        churn_details = gr.Markdown("*Enter a numeric Customer ID above and click Apply to load full customer details here.*")
        with gr.Row():
            with gr.Column():
                gr.Markdown("#### Recent Feedback from Team")
                feedback_df = gr.Dataframe(interactive=False, height=250)
            with gr.Column():
                gr.Markdown("#### Active Overrides")
                overrides_df = gr.Dataframe(interactive=False, height=250)
        with gr.Accordion("✍️ Give Feedback / Override Prediction (optional action)", open=False):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("##### Submit Model Feedback")
                    gr.Markdown("*Tell us if the AI got it right or wrong*")
                    fb_model = gr.Dropdown(
                        ["churn_prediction", "demand_forecast", "product_recommendation", "next_purchase"], 
                        label="Model Name"
                    )
                    fb_entity = gr.Textbox(label="Entity ID (Customer/Product ID)", placeholder="e.g., 12345")
                    fb_pred_value = gr.Number(label="Prediction Value (optional)", precision=2, value=None)
                    fb_actual = gr.Textbox(label="Actual Outcome (optional)", placeholder="What actually happened?")
                    fb_type = gr.Dropdown(
                        ["correct_prediction", "wrong_prediction", "override_needed", "edge_case"], 
                        label="Feedback Type"
                    )
                    fb_notes = gr.Textbox(label="Notes", lines=2, placeholder="Add context about why the prediction was right/wrong")
                    fb_submit = gr.Button("✅ Submit Feedback", variant="primary")
                    fb_result = gr.Textbox(label="Result", lines=4)
                
                with gr.Column():
                    gr.Markdown("##### Override AI Prediction")
                    gr.Markdown("*Use your business knowledge to override the AI*")
                    ov_customer_id = gr.Number(label="Customer ID", precision=0, value=None, info="Which customer?")
                    ov_original = gr.Number(label="Original AI Probability (optional)", minimum=0, maximum=1, precision=3, value=None)
                    ov_override = gr.Number(label="Your Override Probability", minimum=0, maximum=1, precision=3, value=None, info="0.0 = will not churn, 1.0 = will definitely churn")
                    ov_reason = gr.Textbox(label="Reason", placeholder="e.g., Just renewed contract, Strategic partnership")
                    ov_valid_days = gr.Number(label="Valid for (days, leave blank = permanent)", precision=0, value=None, info="After X days, AI takes over again")
                    ov_submit = gr.Button("🔄 Submit Override", variant="primary")
                    ov_result = gr.Textbox(label="Result", lines=4)
        _t1_out = [t1_status, churn_df, t1_dist_fig, feedback_df, overrides_df, churn_page_md, churn_state]
        tab1.select(load_tab1, outputs=_t1_out)
        t1_refresh.click(load_tab1_force, outputs=_t1_out)
        _c_f = lambda s, r, sg, so, p: render_churn(s, None if r == "All" else r, None if sg == "All" else sg, so, p)
        _c_a = lambda s, r, sg, so: render_churn(s, None if r == "All" else r, None if sg == "All" else sg, so, 0)
        _c_in = [churn_search, churn_risk, churn_segment, churn_sort, churn_state]
        _c_a_in = [churn_search, churn_risk, churn_segment, churn_sort]
        _c_out = [churn_df, churn_page_md, churn_state, churn_details]
        churn_apply.click(_c_a, inputs=_c_a_in, outputs=_c_out)
        churn_clear.click(clear_churn_filters,
                          outputs=[churn_search, churn_risk, churn_segment, churn_sort] + _c_out)
        churn_prev.click(lambda s, r, sg, so, p: _c_f(s, r, sg, so, max(p - 1, 0)), inputs=_c_in, outputs=_c_out)
        churn_next.click(lambda s, r, sg, so, p: _c_f(s, r, sg, so, p + 1), inputs=_c_in, outputs=_c_out)
        fb_submit.click(
            submit_model_feedback_ui,
            inputs=[fb_model, fb_entity, fb_pred_value, fb_actual, fb_type, fb_notes],
            outputs=fb_result
        )
        ov_submit.click(
            override_churn_prediction_ui,
            inputs=[ov_customer_id, ov_original, ov_override, ov_reason, ov_valid_days],
            outputs=ov_result
        )
    
    # TAB 2: INVENTORY — insight-first: levels auto-load; adjust form collapsed
    with gr.Tab("Inventory Management") as tab2:
        gr.Markdown("### Inventory Health")
        t2_status = gr.Markdown("⏳ Loading inventory…")
        with gr.Row():
            inv_search = gr.Textbox(label="Search product name", placeholder="e.g. Laptop…", scale=2)
            inv_warehouse = gr.Dropdown(["All"] + WAREHOUSE_CHOICES, value="All", label="Warehouse", scale=1)
            inv_status = gr.Dropdown(["All", "In Stock", "Low Stock", "Out of Stock"], value="All", label="Stock Status", scale=1)
            inv_sort = gr.Dropdown(list(INV_SORTS), value="Current Stock (lowest first)", label="Sort By", scale=1)
            inv_apply = gr.Button("🔎 Apply", variant="primary", scale=1)
            inv_clear = gr.Button("✖ Clear", scale=1)
            t2_refresh = gr.Button("🔄 Refresh", scale=1)
        t2_fig = gr.Plot(label="Stock Status Distribution")
        inv_df = gr.Dataframe(interactive=False, height=280)
        with gr.Row():
            inv_prev = gr.Button("◀ Prev", scale=1)
            inv_page_md = gr.Markdown("Page 1 of …")
            inv_next = gr.Button("Next ▶", scale=1)
        inv_state = gr.State(0)
        gr.Markdown("#### Recent Adjustments by Team")
        adj_df = gr.Dataframe(interactive=False, height=220)
        with gr.Accordion("✍️ Adjust Stock (optional action)", open=False):
            gr.Markdown("*When warehouse count doesn't match the system*")
            with gr.Row():
                inv_product_id = gr.Dropdown(choices=PRODUCT_CHOICES, allow_custom_value=True, label="Product", info="Select the product you counted")
                inv_warehouse_id = gr.Number(label="Warehouse ID", precision=0, value=None, info="Numeric warehouse ID (e.g. 1)")
                inv_old_qty = gr.Number(label="System Quantity", precision=0, value=None, info="What the system shows")
                inv_new_qty = gr.Number(label="Physical Count", precision=0, value=None, info="What you actually counted")
            
            with gr.Row():
                inv_reason = gr.Dropdown(
                    ["shrinkage", "damage", "theft", "miscount", "cycle_count"], 
                    label="Reason Code",
                    info="Why is there a difference?"
                )
                inv_location = gr.Textbox(label="Location (optional)", placeholder="Aisle 3, Bin 12")
                inv_notes = gr.Textbox(label="Notes (optional)", lines=2, placeholder="Additional details")
            
            inv_delta = gr.Number(label="Δ Difference (auto)", precision=0, interactive=False, info="Auto-calculated: Physical − System")
            inv_submit = gr.Button("✅ Submit Adjustment", variant="primary")
            inv_result = gr.Textbox(label="Result", lines=4)
        _t2_out = [t2_status, t2_fig, inv_df, adj_df, inv_page_md, inv_state]
        tab2.select(load_tab2, outputs=_t2_out)
        t2_refresh.click(load_tab2_force, outputs=_t2_out)
        _i_f = lambda s, w, st, so, p: render_inventory(s, None if w == "All" else w, None if st == "All" else st, so, p)
        _i_a = lambda s, w, st, so: render_inventory(s, None if w == "All" else w, None if st == "All" else st, so, 0)
        _i_in = [inv_search, inv_warehouse, inv_status, inv_sort, inv_state]
        _i_a_in = [inv_search, inv_warehouse, inv_status, inv_sort]
        _i_out = [inv_df, inv_page_md, inv_state]
        inv_apply.click(_i_a, inputs=_i_a_in, outputs=_i_out)
        inv_clear.click(clear_inventory_filters,
                        outputs=[inv_search, inv_warehouse, inv_status, inv_sort] + _i_out)
        inv_prev.click(lambda s, w, st, so, p: _i_f(s, w, st, so, max(p - 1, 0)), inputs=_i_in, outputs=_i_out)
        inv_next.click(lambda s, w, st, so, p: _i_f(s, w, st, so, p + 1), inputs=_i_in, outputs=_i_out)
        inv_old_qty.change(compute_delta, inputs=[inv_old_qty, inv_new_qty], outputs=inv_delta)
        inv_new_qty.change(compute_delta, inputs=[inv_old_qty, inv_new_qty], outputs=inv_delta)
        inv_submit.click(
            submit_inventory_adjustment_ui,
            inputs=[inv_product_id, inv_warehouse_id, inv_old_qty, inv_new_qty, inv_reason, inv_location, inv_notes],
            outputs=inv_result
        )
    
    # TAB 3: CUSTOMER PRIORITY — insight-first: analytics auto-load; flag form collapsed
    with gr.Tab("Customer Priority") as tab3:
        gr.Markdown("### Customer Analytics")
        t3_status = gr.Markdown("⏳ Loading customers…")
        with gr.Row():
            cust_filter = gr.Textbox(label="Search by name or Customer ID", placeholder="e.g. 123 or part of a name…", scale=3)
            cust_segment_dd = gr.Dropdown(["All"] + SEGMENT_CHOICES, value="All", label="Segment", scale=1)
            cust_apply = gr.Button("🔎 Apply", variant="primary", scale=1)
            cust_clear = gr.Button("✖ Clear", scale=1)
            t3_refresh = gr.Button("🔄 Refresh", scale=1)
        with gr.Row():
            t3_seg_fig = gr.Plot(label="Customer Segmentation")
            t3_act_fig = gr.Plot(label="Activity Status")
        cust_df = gr.Dataframe(interactive=False, height=300)
        with gr.Row():
            with gr.Column():
                gr.Markdown("#### Customer Lookup")
                with gr.Row():
                    cust_search = gr.Textbox(label="Customer ID", placeholder="e.g. 123", scale=2)
                    cust_context_btn = gr.Button("🔎 Load Context", variant="primary", scale=1)
                cust_context = gr.Markdown("*Enter a Customer ID to see revenue, recency and churn risk.*")
            
            with gr.Column():
                gr.Markdown("#### Active Priority Flags")
                with gr.Row():
                    flags_priority_dd = gr.Dropdown(["All", "VIP", "Strategic", "At-Risk", "White-Glove", "Standard"],
                                                     value="All", label="Priority Level", scale=2)
                    flags_apply = gr.Button("🔎 Apply", variant="primary", scale=1)
                flag_df = gr.Dataframe(interactive=False, height=250)
        with gr.Accordion("✍️ Flag Customer (optional action)", open=False):
            gr.Markdown("*Mark VIP, Strategic, or At-Risk customers*")
            with gr.Row():
                cp_customer_id = gr.Number(label="Customer ID", precision=0, value=None, info="Which customer?")
                cp_priority = gr.Dropdown(
                    ["VIP", "Strategic", "At-Risk", "White-Glove", "Standard"], 
                    label="Priority Level",
                    info="How important is this customer?"
                )
                cp_flag_type = gr.Dropdown(
                    ["strategic_account", "high_value", "retention_focus", "support_priority"], 
                    label="Flag Type",
                    info="What kind of special treatment?"
                )
            
            with gr.Row():
                cp_reason = gr.Textbox(label="Reason", placeholder="e.g., Top revenue account, Partnership opportunity, Risk of leaving")
                cp_valid_days = gr.Number(label="Valid for (days, leave blank = permanent)", precision=0, value=None, info="After X days, flag expires")
                cp_notes = gr.Textbox(label="Notes (optional)", lines=2, placeholder="Additional context")
            
            cp_submit = gr.Button("✅ Set Priority", variant="primary")
            cp_result = gr.Textbox(label="Result", lines=4)
        tab3.select(load_tab3, outputs=[t3_status, t3_seg_fig, t3_act_fig, cust_df, flag_df])
        t3_refresh.click(load_tab3_force, outputs=[t3_status, t3_seg_fig, t3_act_fig, cust_df, flag_df])
        cust_apply.click(lambda s, sg: render_customers(s, None if sg == "All" else sg),
                         inputs=[cust_filter, cust_segment_dd], outputs=cust_df)
        cust_clear.click(lambda: (gr.update(value=""), gr.update(value="All"), render_customers(None, None)),
                         outputs=[cust_filter, cust_segment_dd, cust_df])
        flags_apply.click(lambda p: render_flags(None if p == "All" else p),
                          inputs=flags_priority_dd, outputs=flag_df)
        cust_context_btn.click(get_customer_context, inputs=cust_search, outputs=cust_context)
        cp_submit.click(
            set_customer_priority_ui,
            inputs=[cp_customer_id, cp_priority, cp_flag_type, cp_reason, cp_valid_days, cp_notes],
            outputs=cp_result
        )
    
    # TAB 4: DATA QUALITY — insight-first: issues auto-load; report form collapsed
    with gr.Tab("Data Quality Issues") as tab4:
        gr.Markdown("### Data Quality — Detected & Reported Issues")
        t4_status = gr.Markdown("⏳ Loading issues…")
        with gr.Row():
            dq_sev_dd = gr.Dropdown(["All", "critical", "high", "medium", "low"], value="All", label="Severity", scale=1)
            dq_status_dd = gr.Dropdown(["All", "open", "resolved"], value="All", label="Status", allow_custom_value=True, scale=1)
            dq_issue_dd = gr.Dropdown(["All"] + DQ_ISSUE_TYPES, value="All", label="Issue Type", allow_custom_value=True, scale=1)
            dq_table_dd = gr.Dropdown(["All"] + DQ_TABLES, value="All", label="Affected Table", allow_custom_value=True, scale=1)
            dq_apply = gr.Button("🔎 Apply", variant="primary", scale=1)
            dq_clear = gr.Button("✖ Clear", scale=1)
            t4_refresh = gr.Button("🔄 Refresh", scale=1)
        t4_fig = gr.Plot(label="Issues by Severity & Status")
        dq_issues_df = gr.Dataframe(interactive=False, height=300)
        with gr.Accordion("✍️ Report Issue (optional action)", open=False):
            gr.Markdown("*Help keep our data clean — report what's wrong*")
            with gr.Row():
                dq_table = gr.Dropdown(
                    choices=[f"{CATALOG}.gold.{t}" for t in GOLD_TABLES],
                    label="Table Name",
                    info="Which table has the problem? (or type a custom value)",
                    allow_custom_value=True
                )
                dq_column = gr.Textbox(
                    label="Column Name (optional)", 
                    placeholder="ChurnProbability",
                    info="Which column? Leave blank if table-level issue"
                )
                dq_issue_type = gr.Dropdown(
                    ["missing_data", "incorrect_value", "duplicate", "formatting", "logic_error"], 
                    label="Issue Type",
                    info="What kind of problem?"
                )
                dq_severity = gr.Dropdown(
                    ["critical", "high", "medium", "low"], 
                    label="Severity",
                    info="How serious is it?"
                )
            
            dq_description = gr.Textbox(
                label="Description", 
                lines=3, 
                placeholder="Describe the issue: What's wrong? When did you notice it? What should it be?"
            )
            dq_samples = gr.Textbox(
                label="Sample Records (optional)", 
                lines=2, 
                placeholder="CustomerID=123 has probability=2.5 (should be 0-1), OrderID=456 is duplicated"
            )
            
            dq_submit = gr.Button("✅ Report Issue", variant="primary")
            dq_result = gr.Textbox(label="Result", lines=4)
        tab4.select(load_tab4, outputs=[t4_status, t4_fig, dq_issues_df])
        t4_refresh.click(load_tab4_force, outputs=[t4_status, t4_fig, dq_issues_df])
        dq_apply.click(lambda sv, st, it, tb: render_dq(None if sv == "All" else sv, None if st == "All" else st,
                                                        None if it == "All" else it, None if tb == "All" else tb),
                       inputs=[dq_sev_dd, dq_status_dd, dq_issue_dd, dq_table_dd], outputs=dq_issues_df)
        dq_clear.click(lambda: (gr.update(value="All"), gr.update(value="All"), gr.update(value="All"),
                                gr.update(value="All"), render_dq(None, None, None, None)),
                       outputs=[dq_sev_dd, dq_status_dd, dq_issue_dd, dq_table_dd, dq_issues_df])
        dq_submit.click(
            report_data_quality_issue_ui,
            inputs=[dq_table, dq_column, dq_issue_type, dq_severity, dq_description, dq_samples],
            outputs=dq_result
        )
    
    # TAB 5: DEMAND FORECAST — insight-first: forecasts auto-load; adjust form collapsed
    with gr.Tab("Demand Forecast") as tab5:
        gr.Markdown("### AI Demand Forecasts")
        t5_status = gr.Markdown("⏳ Loading forecasts…")
        with gr.Row():
            t5_product = gr.Dropdown(["All"] + FC_PRODUCT_CHOICES, value="All", label="Product", allow_custom_value=True, scale=2)
            t5_from = gr.Textbox(label="Forecast From (YYYY-MM-DD)", placeholder="2026-11-01", scale=1)
            t5_to = gr.Textbox(label="Forecast To (YYYY-MM-DD)", placeholder="2026-11-30", scale=1)
            t5_apply = gr.Button("🔎 Apply", variant="primary", scale=1)
            t5_clear = gr.Button("✖ Clear", scale=1)
            t5_refresh = gr.Button("🔄 Refresh", scale=1)
        t5_metrics = gr.Markdown("⏳ Computing forecast accuracy…")
        t5_fig = gr.Plot(label="Demand Forecast vs Actual")
        df_df = gr.Dataframe(interactive=False, height=300)
        gr.Markdown("#### Historical Adjustments by Team")
        dfa_df = gr.Dataframe(interactive=False, height=220)
        with gr.Accordion("✍️ Adjust Forecast (optional action)", open=False):
            gr.Markdown("*Factor in promotions, market events, competitive actions the AI doesn't know about*")
            with gr.Row():
                dfa_product_id = gr.Dropdown(choices=FC_PRODUCT_CHOICES, allow_custom_value=True, label="Product", info="Select the forecast product")
                dfa_date = gr.Textbox(label="Forecast Date", placeholder="2026-12-31", info="Format: YYYY-MM-DD")
                dfa_ml_qty = gr.Number(label="AI Forecast Qty", precision=0, value=None, info="What the AI predicts")
                dfa_factor = gr.Number(
                    label="Adjustment Factor", 
                    value=1.0, 
                    precision=2,
                    info="1.0=no change, 1.5=+50% increase, 0.8=-20% decrease"
                )
            
            with gr.Row():
                dfa_reason = gr.Dropdown(
                    ["promotion", "market_event", "competitor_action", "supply_constraint"], 
                    label="Reason",
                    info="Why are you adjusting?"
                )
                dfa_event = gr.Textbox(
                    label="Event Type (optional)", 
                    placeholder="Black Friday, Product Launch, Seasonal Sale"
                )
                dfa_notes = gr.Textbox(label="Notes (optional)", lines=2, placeholder="Additional details about the adjustment")
            
            dfa_adjusted = gr.Number(label="Adjusted Forecast (auto)", precision=0, interactive=False, info="Auto-calculated: AI Qty × Factor")
            dfa_submit = gr.Button("✅ Submit Adjustment", variant="primary")
            dfa_result = gr.Textbox(label="Result", lines=4)
        tab5.select(load_tab5, outputs=[t5_status, t5_metrics, t5_fig, df_df, dfa_df])
        t5_refresh.click(load_tab5_force, outputs=[t5_status, t5_metrics, t5_fig, df_df, dfa_df])
        t5_apply.click(render_forecasts, inputs=[t5_product, t5_from, t5_to], outputs=df_df)
        t5_clear.click(lambda: (gr.update(value="All"), gr.update(value=""), gr.update(value=""),
                                render_forecasts("All", None, None)),
                       outputs=[t5_product, t5_from, t5_to, df_df])
        dfa_ml_qty.change(compute_adjusted_qty, inputs=[dfa_ml_qty, dfa_factor], outputs=dfa_adjusted)
        dfa_factor.change(compute_adjusted_qty, inputs=[dfa_ml_qty, dfa_factor], outputs=dfa_adjusted)
        dfa_submit.click(
            adjust_demand_forecast_ui,
            inputs=[dfa_product_id, dfa_date, dfa_ml_qty, dfa_factor, dfa_reason, dfa_event, dfa_notes],
            outputs=dfa_result
        )
    
    # Load Overview landing page on startup (default 30-day range)
    demo.load(get_overview_v2, inputs=[range_mode, custom_from, custom_to], outputs=ov_out)

# Mount Gradio on FastAPI (required for Databricks Apps proxy)
from fastapi import FastAPI
import uvicorn

fastapi_app = FastAPI()
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("DATABRICKS_APP_PORT", "8000")))
