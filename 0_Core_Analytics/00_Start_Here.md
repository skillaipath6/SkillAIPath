# START HERE — EduFin Portfolio Analysis

**5-Day Analytics Data & AI Analytics Experience**

---

## You Are Here

You're an analytics engineer for **EduFin**, an education lender with ₹150 crore deployed.

The CFO needs a portfolio assessment before approving ₹50 crore expansion.

**Your task:** Complete 4 analyses in 5 days.

---

## By the End of Your 5-Day Experience

You'll build a portfolio that reflects how engineering work is actually delivered. **Business Portfolio Analysis** 
Present recommendations backed by business decisions, trade-offs, and data. **Professional GitHub Repository** 
Build a repository structured for your engineering portfolio. **Engineering Commit History** 
Every improvement is committed, creating a visible record of your engineering journey. **Pull Requests & Engineering Reviews** 
Receive technical feedback through Pull Requests and improve your work through review iterations. **Business Decision Documentation** 
Learn to explain not only what you built, but why you made each engineering decision. **5-Day Analytics Experience Certificate** 
Demonstrate hands-on experience working through a real business case.

**Your portfolio shouldn't just show completed notebooks. It should show how you think, build, improve, and communicate as an engineer.**

Anyone can upload a finished project. Your GitHub should tell the story of how you built it, improved it through reviews, and made engineering decisions with confidence.

---

## Choose Your Path

### Path A: SQL Beginner (3–4 hour prerequisite)

**Start here if:**
* You're new to SQL
* Last used SQL >6 months ago
* Want a structured refresh on JOINs, WHERE, GROUP BY, HAVING

**→ Go to:** `01_SQL_Fundamentals` notebook and execute it one by one, actively learning SQL.

**Then:** Return here and take Path B

---

### Path B: Ready Engineer (Start immediately)

**Start here if:**
* Comfortable with SQL JOINs, aggregations, CTEs
* Ready to analyze real portfolio data
* Want to jump into business decisions

**→ Follow this sequence:**

#### Step 1: Prepare Your Environment (2–3 minutes)
**Run:** `0_Data_Setup` notebook

**This is your production environment.** Every engineer begins by preparing their environment before solving business problems.

It will automatically: Generate EduFin portfolio data (5,000 loans, 3,000 customers) Create `sap_dev` schema (small dataset for testing) Create `sap_main` schema (national scale dataset) Validate data quality 

#### Step 2: Complete Any Analysis (No required order!)

**Complete all 4 notebooks. Work in parallel.**

### 1. Portfolio Health

**Questions answered:** Is the portfolio healthy enough for expansion? What are the default rates by risk band? Should we approve expansion? What's the maximum loan size? 

### 2. Customer Risk

**Questions answered:** Which customer segments create the most risk? Which segments should we stop lending to? Where should approval cut-offs be drawn? 

### 3. Time Analysis

**Questions answered:** Are defaults improving or worsening over time? Is recent data reliable? Should we trust current trends? 

### 4. Cost Tracking

**Questions answered:** How much DBU usage are we consuming? Can we optimize our queries? Can we stay below the ₹1,000 DBU budget?

---

## Engineering Review Journey

| Stage | What Happens |
|-------|-------------|
| **First PR** | Initial engineering review |
| **Feedback** | Improve your analysis and update your PR |
| **Final Review** | Submit your final business recommendation |
| **Completion** | Receive your 5-Day Experience Certificate |

---

## Engineering Completion Checklist

**Successful completion requires:** Make business recommendations, not just calculations Commit your work regularly Raise Pull Requests Address engineering review comments Track DBU usage Present your final recommendation 

---

 **Engineering Rule**

Every meaningful change should end with: Commit Push Pull Request 

This is how engineering work is tracked.
---

## Engineering Office

**Workspace:** Databricks Free Edition GitHub Repository `dev` & `main` branches 

**Support:** Engineering Community (WhatsApp) DM Support 

**Engineering Review Hours:**

 **10:00 AM – 6:00 PM IST**

Outside these hours we'll continue responding whenever the team is online. 

---

## ❌ Avoid

 Waiting for the "right answer" 
 Solving notebooks sequentially 
 Reporting numbers without recommendations 
 Ignoring DBU usage 

---

## Engineering Mindset

**Always:** Recommend even with uncertainty Justify with data and trade-off analysis Show your work (SQL + interpretation) Ask "what assumptions am I making?" Write clean PR updates (2–3 sentences explaining what changed) Share Pull Request links for technical discussions Use WhatsApp for coordination, announcements, and review slots
---

## What Makes This Different

**This is how engineering decisions are made.**

### ❌ Homework

*Default Rate = 14%*

### Engineering

*Default rate is 14%, which is 2x the 7% industry median for edu loans. I recommend pausing expansion until we:*

*1. Tighten CIBIL cutoff from 600 → 650 (reduces defaults to 9%, costs ₹8 crore revenue)*

*2. Cap loan size at ₹5L (protects from tail risk, costs ₹2 crore revenue)*

*Trade-off: Slower growth vs safer portfolio. Given 14% current rate, I prioritize safety.*

---

**The difference:** Judgment, trade-offs, recommendations.

---

## Next Steps **1⃣ Create GitHub Repository** (fork SkillAIPath template) **2⃣ Create branches** (dev and main) **3⃣ Connect Databricks** to your GitHub repository **4⃣ Choose your path** (SQL Beginner → 01_SQL_Fundamentals OR Ready Engineer → skip to step 5) **5⃣ Run Data Setup** (0_Data_Setup notebook, 2–3 min) **6⃣ Begin Analysis** (pick any of the 4 notebooks) **7⃣ Commit Daily** (every change goes to GitHub) **8⃣ Share Pull Request** (2-line summary + PR link in Engineering Community)

---

## Need Help?

 Search the Engineering Community first. 
 Share your Pull Request when requesting technical reviews. 
 DM us if you're blocked. 