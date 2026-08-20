# Growth Accelerator Architecture Diagrams
## Participant Development & Instructor Resources

**Purpose:** Architecture diagrams for portfolio system, auto-progression, and training infrastructure  
**Audience:** Instructors, coordinators, system architects

---

##  Available Diagrams

### 1. Portfolio Career System
**File:** `Portfolio_Career_System.md` (in 1_Portfolio_System/)  
**Purpose:** Complete participant portfolio tracking architecture  
**Shows:**
- Portfolio project tracking
- Career milestone documentation
- Skill progression mapping
- Learning path recommendations

### 2. Auto-Progression System
**Location:** `2_Auto_Progression/` (app implementation)  
**Purpose:** Automated participant progression tracking  
**Components:**
- Access control gate
- Deployer automation
- Progress monitoring app

### 3. Execution Training System
**Detailed in:** Canvas Architecture Diagrams  
**Reference:** `/1_Canvas/Architecture_Diagrams/Execution_Training_System.md`  
**Shows:**
- 69 task patterns across 11 categories
- 48 training sessions progression
- 5-Day intensive experience
- Autonomous agent integration

### 4. Flash Integrations Flow
**Location:** `4_Flash_Integrations/` (implementation files)  
**Purpose:** 3-minute Google Sheets → Databricks pipeline  
**Steps:**
- Quick start setup
- Google sheet sync
- Curated view builder
- Genie space setup
- Dashboard builder
- Schedule refresh job

---

## Cross-References

### Main Canvas Diagrams
All Growth Accelerator systems integrate with Canvas architecture:
- `/1_Canvas/Architecture_Diagrams/00_Canvas_System_Overview.md` - Master view
- `/1_Canvas/Architecture_Diagrams/08_Training_Task_Patterns_Architecture.md` - 69 tasks
- `/1_Canvas/Architecture_Diagrams/09_Training_Sessions_Architecture.md` - 48 sessions

### Integration Points
- **Data Platform:** Participant progress data flows to medallion architecture
- **AI Platform:** Auto-grading and agent assistance
- **BI Platform:** Portfolio dashboards and progress analytics
- **Canvas:** Training orchestration and task management

---

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│              Growth Accelerator Architecture                  │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Portfolio System          Auto-Progression        Training   │
│  ┌──────────────┐         ┌──────────────┐      ┌─────────┐ │
│  │ Projects     │         │ Gate Check   │      │ 69 Tasks│ │
│  │ Milestones   │────────▶│ Deployer     │◀────▶│ 48 Sess │ │
│  │ Skills       │         │ Monitor App  │      │ 5-Day   │ │
│  └──────────────┘         └──────────────┘      └─────────┘ │
│         │                        │                     │      │
│         └────────────────────────┴─────────────────────┘      │
│                              │                                │
│                    Flash Integrations                         │
│                  ┌──────────────────────┐                     │
│                  │ Google Sheets → DB   │                     │
│                  │ 3-minute setup       │                     │
│                  │ Genie + Dashboard    │                     │
│                  └──────────────────────┘                     │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Future Diagrams (Planned)

### Planning Agent Architecture
**Status:** Planned for Week 1 build  
**Will show:**
- Branch scanning (11 engineers)
- Task allocation algorithm
- Approval workflow
- Progress tracking

### Daily Execution Agent Architecture
**Status:** Planned for Week 2 build  
**Will show:**
- Morning scan (code/data/infra)
- Auto-fix patterns
- PR generation
- Deployment pipeline

### Audience Onboarding System
**Status:** Planned for Week 3 build  
**Will show:**
- Auto-provisioning flow
- Knowledge Hub RAG
- Certificate generation
- Role-based access

---

##  File Organization

```
5_Growth_Accelerator/
├── Architecture_Diagrams/
│   └── README.md (this file)
├── 1_Portfolio_System/
│   └── Portfolio_Career_System.md (actual diagram)
├── 2_Auto_Progression/
│   └── auto-progression-app/ (implementation)
├── 3_Execution_Training/
│   ├── Task_Patterns/ (69 tasks)
│   ├── Training_Sessions/ (48 sessions)
│   └── SPRINT_PLANNING_GUIDE.md (planning)
└── 4_Flash_Integrations/
    └── (6 implementation files)
```

---

## How to Use These Diagrams

### For Instructors
1. Review Portfolio_Career_System.md for participant tracking architecture
2. Reference Planning Cycle Guide for task allocation
3. Use Canvas training diagrams for session planning

### For System Architects
1. Start with Canvas System Overview for complete platform view
2. Deep dive into specific Growth Accelerator components
3. Cross-reference with Data Platform and AI Platform architectures

### For Autonomous Agents
1. Use Planning Cycle Guide for task allocation algorithm
2. Reference Training Task Patterns for work breakdown
3. Integrate with Canvas orchestration patterns

---

**Note:** Most detailed architecture diagrams live in `/1_Canvas/Architecture_Diagrams/` (20 diagrams). Growth Accelerator focuses on implementation with references to those master diagrams.

**Last Updated:** 2026-01-08  
**Maintained By:** Platform Architecture Team
