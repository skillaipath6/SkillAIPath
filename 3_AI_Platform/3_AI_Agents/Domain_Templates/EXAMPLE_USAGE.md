# Domain Templates - Complete Workflow

## The "Locked Version" Concept

Domain Templates produces **complete, self-contained projects** - like cloning SkillAIPath but adapted to your domain.

## End-to-End Workflow

### Step 1: Analyze Data
```python
from intelligent_modeler import IntelligentModeler

modeler = IntelligentModeler('/my-data/')
star_schema = modeler.analyze_all()
```

### Step 2: Generate Complete Project
```python
from output_generator import OutputGenerator, ProjectConfig

config = ProjectConfig(
 domain_name='retail',
 catalog='my_catalog',
 environment='dev',
 source_path='/my-data',
 output_path='/output'
)

generator = OutputGenerator(config)
project_path = generator.generate_project(star_schema)
```

### Step 3: Generated Structure
```
/output/retail/
├── bronze/ → Ingestion notebooks
├── silver/
│ ├── dimensions/ → SCD1/SCD2 dims
│ └── facts/ → Facts with joins
├── gold/ → Metric views
├── dashboards/ → Lakeview configs
├── jobs/ → Orchestration
└── README.md
```

### Step 4: Deploy
1. Run bronze notebooks
2. Run silver dimensions
3. Run silver facts
4. Execute gold SQL
5. Create job
6. Build dashboards

## What You Get **Self-Contained**: Everything for deployment **Relative Assets**: YOUR catalog, schema, terminology **Business Context**: Adapted to YOUR domain **Production-Ready**: Works out of the box **Complete Stack**: Bronze → Gold → Dashboards → Jobs

**Like cloning SkillAIPath, but tailored to your data!**
