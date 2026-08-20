 DEVOPS AUTO SETUP - GitHub Repo Initialization

WHAT THIS JOB DOES:
Creates a complete GitHub repository setup for students automatically with zero manual work.

STUDENT PROVIDES (as job parameters):
- GitHub Personal Access Token (via secret scope OR direct parameter)
- Desired repo name (e.g., "john-skillai-path")
- GitHub username

JOB EXECUTES:
1. Creates new GitHub repository under student's account
2. Forks SkillAI Path template structure (source encrypted - not revealed to students)
3. Sets up two branches:
   - main (default branch) - contains base template
   - dev (development branch) - for daily work
4. Initializes folder structure:
   - 1_Canvas/ (notebooks & orchestration)
   - 2_Data/ (datasets)
   - 3_Models/ (ML experiments)
   - 4_Apps/ (application templates)
5. Makes first commit & creates PROGRESS.md tracker in dev branch
6. Opens first Pull Request (dev → main) ready for student to review & merge

SECURITY:
- Student's GitHub token handled via Databricks secrets (recommended) OR job parameter
- Template source repo is encrypted - students don't see our original repo
- Each student gets their own independent fork

USE CASE:
- Run ONCE per student at Investigation Case start
- Sets up complete GitHub workflow in <2 minutes
- Student learns PR workflow by merging their first PR
- Ready for daily commits during 5-day case

OUTPUT:
- Repo URL
- Branch names
- First PR link
- Success/failure status

SCHEDULE: On-demand (triggered per student)
