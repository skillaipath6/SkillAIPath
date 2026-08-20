# Domain Templates System

**Intelligent Data Modeling & Automation Platform**

## Overview

Production-grade domain automation system that intelligently analyzes data and creates sophisticated dimensional models. Supports end-to-end automation: medallion architecture → dashboards → Genie Spaces → MLOps/RAG → governance.

## Key Features

### 1. **Intelligent Data Modeling** (NEW!)
Located in `intelligent_modeler.py`:

**NOT template-based - TRUE data intelligence:**
- Analyzes raw CSV data to automatically classify facts vs dimensions
- Detects proper grain and primary/foreign keys from actual data
- Discovers relationships by validating referential integrity
- Identifies hierarchies (date, geographic, organizational)
- Recommends SCD types (1, 2, 3) based on data behavior
- Classifies measures (additive, semi-additive, non-additive)
- Designs proper star schemas with conformed dimensions

**Example:**
```python
from intelligent_modeler import IntelligentModeler

# Just point to CSV folder - no YAML config needed!
modeler = IntelligentModeler('/path/to/csvs')
star_schema = modeler.analyze_all()

# OUTPUT: Proper dimensional model with intelligent decisions
# - fact_orders (with validated relationships)
# - dim_customer (SCD2 with tracked attributes)
# - dim_product (with hierarchies)
# - dim_date (auto-generated)
```

### 2. **Output Generator - "Locked Version"** (NEW!)
Located in `output_generator.py`:

**Produces complete, deployable projects** (like cloning SkillAIPath for target domain):
- Generates full medallion architecture (bronze/silver/gold)
- Creates dimension notebooks with proper SCD implementation
- Creates fact notebooks with validated joins to dimensions
- Generates gold layer metrics and aggregations
- Produces dashboard configs for Lakeview
- Creates orchestration job configs
- All relative to target domain (their catalog, schema, terminology)

**Example:**
```python
from intelligent_modeler import IntelligentModeler
from output_generator import OutputGenerator, ProjectConfig

# Step 1: Analyze data
modeler = IntelligentModeler('/path/to/csvs')
star_schema = modeler.analyze_all()

# Step 2: Generate complete project
config = ProjectConfig(
 domain_name='retail',
 catalog='my_catalog',
 environment='dev',
 source_path='/path/to/csvs',
 output_path='/output'
)
generator = OutputGenerator(config)
project_path = generator.generate_project(star_schema)

# OUTPUT: Complete project in /output/retail/
# ├── bronze/ → Ingestion notebooks for all tables
# ├── silver/
# │ ├── dimensions/ → SCD1/SCD2 dimension notebooks
# │ └── facts/ → Fact notebooks with joins
# ├── gold/ → Metric views
# ├── dashboards/ → Lakeview configs
# ├── jobs/ → Orchestration config
# └── README.md → Documentation
```

### 3. **Pattern Replication**
- Replicates proven SkillAIPath patterns to new domains
- SCD1, SCD2, bridge tables, complex joins
- Maintains sophisticated logic

### 4. **Full Domain Automation**
- Bronze → Silver → Gold medallion architecture
- Auto-generated dashboards
- Genie Space setup
- Job scheduling
- Governance tagging

## Production Status **100% Production Ready**

- 29 production files
- Intelligent modeling engine
- Output generator - "Locked Version" (NEW)
- Pattern replication
- Full domain automation
- Archive system
- Comprehensive documentation

## Intelligence Capabilities

### Automatic Classification
- **Fact Detection**: High row count + measures + timestamps → fact
- **Dimension Detection**: Descriptive attributes + low cardinality → dimension
- **Bridge Detection**: Many-to-many junction patterns
- **Reference Detection**: Small lookup tables

### Relationship Discovery
- Analyzes actual data (not just column names)
- Validates referential integrity
- Confidence scoring (0-100%)
- Detects orphaned records

### Hierarchy Detection
- **Date**: Year → Quarter → Month → Week → Day
- **Geographic**: Country → State → City
- **Organizational**: Company → Dept → Team

### SCD Intelligence
- Analyzes change patterns in data
- Recommends SCD type (1, 2, or 3)
- Identifies which attributes to track
- Detects existing effective date patterns

### Measure Classification
- **Additive**: SUM across all dimensions (revenue, quantity)
- **Semi-Additive**: SUM across some dimensions (balance, inventory)
- **Non-Additive**: No SUM (average, ratio, percent)

## SaaS Product Positioning

**Product Name**: Intelligent Domain Modeler 
**Pricing**: $299-$999/month 
**Target**: Data engineering teams, consultancies

### Value Proposition
- **Intelligence**: Analyzes data, not just templates
- **"Locked Version" Output**: Complete, deployable projects (like cloning SkillAIPath)
- **Speed**: CSV to production-ready project in minutes
- **Quality**: Proper dimensional modeling with SCD, grain, relationships
- **Automation**: End-to-end deployment (bronze → silver → gold → dashboards → jobs)

### Competitive Advantage
- Only system with true data modeling intelligence + complete project generation
- Not just search/replace templates - generates relative assets for target domain
- Produces self-contained solutions: all notebooks, configs, orchestration
- Proven patterns from SkillAIPath production systems
- Suitable for daily enterprise use + SaaS productization

---

**Last Updated**: August 7, 2026 
**Version**: 4.0 (Locked Version / Output Generator) 
**Status**: Production Ready - Complete End-to-End Solution
