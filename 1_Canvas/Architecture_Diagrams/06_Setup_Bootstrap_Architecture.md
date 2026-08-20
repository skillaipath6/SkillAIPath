# Setup & Bootstrap Architecture
## Environment Configuration | 5 Config Files | Foundation Layer

The Setup module provides environment detection, configuration management, and bootstrap scripts for the entire platform.

---

## Setup Architecture

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        SETUP & BOOTSTRAP SYSTEM                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│  CONFIGURATION FILES (5 Files)                                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │  1. environment_config.json                                      │         │
│  │     • Workspace detection (DEV/UAT/PROD)                         │         │
│  │     • Catalog mappings per environment                           │         │
│  │     • Compute cluster configurations                             │         │
│  └─────────────────────────────────────────────────────────────────┘         │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │  2. catalog_mappings.yaml                                        │         │
│  │     • Unity Catalog structure (dev/uat/prod)                     │         │
│  │     • Schema definitions                                         │         │
│  │     • Volume paths                                               │         │
│  └─────────────────────────────────────────────────────────────────┘         │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │  3. bootstrap_init.py                                            │         │
│  │     • Auto-detect current environment                            │         │
│  │     • Initialize catalogs/schemas                                │         │
│  │     • Set up service principals                                  │         │
│  └─────────────────────────────────────────────────────────────────┘         │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │  4. secrets_config.json                                          │         │
│  │     • API key management (Databricks Secrets)                    │         │
│  │     • External service credentials                               │         │
│  │     • LLM provider tokens                                        │         │
│  └─────────────────────────────────────────────────────────────────┘         │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │  5. validation_checks.py                                         │         │
│  │     • Environment health checks                                  │         │
│  │     • Permission validation                                      │         │
│  │     • Connectivity tests                                         │         │
│  └─────────────────────────────────────────────────────────────────┘         │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘

BOOTSTRAP FLOW:
  1. Detect Environment → 2. Load Config → 3. Initialize Resources →
  4. Validate Setup → 5. Ready for Orchestration
```

---

## Key Setup Capabilities

### Environment Detection
* Automatic DEV/UAT/PROD detection based on workspace URL
* Config file selection per environment
* Catalog namespace isolation

### Bootstrap Process
* One-command initialization: `python bootstrap_init.py`
* Idempotent (safe to re-run)
* Validation reporting

---

**Version**: 2.0  
**Last Updated**: 2026-08-04  
**Status**: Production Setup System (ASCII Format)
