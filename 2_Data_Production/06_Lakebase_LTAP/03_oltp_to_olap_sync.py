# Databricks notebook source
# DBTITLE 1,OLTP to OLAP Sync Documentation
# 21 Daily Lakebase Sync - OLTP to OLAP Sync Documentation

print("="*80)
print("OLTP to OLAP Sync - Configuration Documentation")
print("="*80)
print("\n📋 Purpose:")
print("   Sync transactional data from Lakebase OLTP to Delta Lake OLAP")
print("\n📊 Data Flow:")
print("   Lakebase (sap_oltp.user_sessions)")
print("   ↓  Transform & Aggregate")
print("   Delta Lake (sap_dev.gold.user_analytics)")
print("\n⚠️  CONFIGURATION REQUIRED")
print("   1. Create source Lakebase tables in sap-oltp project")
print("   2. Update table references in this notebook")
print("   3. Configure Unity Catalog target schema")
print("\n💡 Current Status:")
print("   Documentation mode - awaiting sap-oltp project setup")
print("   Job 21.1 (retail-ops-apps) is fully configured")
print("\n✅ Job execution successful (documentation mode)")
print("="*80)