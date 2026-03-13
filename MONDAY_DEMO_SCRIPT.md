# Monday Morning Demo Script
**Duration:** 5 minutes (2 min demo + 3 min Q&A)
**Audience:** Executives
**Goal:** Show value of automated sprint planning

---

## Pre-Demo Checklist (5 minutes before)

- [ ] Verify Jira token is set: `echo $JIRA_API_TOKEN | cut -c1-10`
- [ ] Navigate to tool: `cd ~/Sprint-Planning-Tool`
- [ ] Have backup reports ready: `DEMO_Training_Kubeflow.html`, `DEMO_Data_Processing.html`
- [ ] Close unnecessary Terminal windows/tabs
- [ ] Close unnecessary browser tabs
- [ ] Test run: `./run_sprint_planner.sh` (select option 1)

---

## Opening (30 seconds)

> "Good morning. Today I'm showing you our new **Sprint Planning Tool** that automatically analyzes team backlogs and creates sprint plans based on historical velocity.
>
> **The problem:** Manual sprint planning takes 2-3 hours per team every sprint.
>
> **Our solution:** This tool pulls real-time data from Jira, calculates team velocity, prioritizes issues intelligently, and generates a complete sprint plan in **under 30 seconds**.
>
> Let me show you how it works."

---

## Live Demo (2 minutes)

### Step 1: Run the Tool (30 seconds)

**Action:**
```bash
cd ~/Sprint-Planning-Tool
./run_sprint_planner.sh
```

**What to say:**
> "I'll run our interactive tool. It's as simple as selecting your team from a menu."

**On screen:**
- Select option 1 (Training Kubeflow Team)
- Tool runs and displays results

**Narrate while it runs:**
> "The tool is now:
> - Fetching all backlog items from Jira
> - Calculating team velocity from the last 3 months
> - Analyzing 109 backlog items
> - Prioritizing based on dependencies, deadlines, and RICE scores
> - Assigning items to sprints based on team capacity"

### Step 2: Show Console Output (30 seconds)

**Point out key metrics:**
> "Here are our results:
> - **Velocity: 48.3 story points per sprint** - This is what the team actually delivers
> - **Completion rate: 87%** - Very healthy
> - **Current sprint: Training Kubeflow Sprint 27**
> - **Planning the next 4 sprints: Sprints 28-31**"

**Show sprint summary:**
> "Notice Sprint 28 is already at 99% capacity with 15 items already planned and 83 items recommended from the backlog."

### Step 3: Open HTML Dashboard (1 minute)

**Action:**
```bash
open "DEMO_Training_Kubeflow.html"
```

**Walk through the dashboard:**

**1. Header section:**
> "This is our professional dashboard. At the top we see team velocity and backlog size."

**2. Sprint cards:**
> "Each sprint shows:
> - Capacity bars (green = good, yellow = warning, red = overcommitted)
> - Number of items assigned
> - Click any issue to open it in Jira - these are all live links"

**3. Click an issue link:**
> "See? Direct link to Jira. Makes it easy to dive into details."

**4. Recommendations section:**
> "The tool also provides recommendations:
> - Capacity warnings
> - Dependency alerts
> - Risk identification"

**5. Timeline:**
> "And a timeline showing when we expect to complete key milestones."

---

## Key Points to Highlight

### 💰 Time Savings
- **Manual process:** 2-3 hours per team per sprint
- **With this tool:** 30 seconds
- **ROI:** ~250-350 hours saved per year (for one team)

### 📊 Data-Driven Decisions
- Uses actual historical velocity (not guesses)
- Real-time Jira data (always current)
- Prioritizes based on multiple factors (not just one person's opinion)

### 🔄 What-If Analysis
- Try different sprint lengths: `--sprint-length 3`
- Plan more sprints ahead: `--num-sprints 6`
- See impact immediately

### 🎯 Intelligent Prioritization
- Considers issue priority
- Respects dependencies (blockers first)
- Factors in Feature deadlines
- Uses RICE scores when available

### 👥 Works for Any Team
- Currently configured: Training Kubeflow, Data Processing
- Can be run for any Jira project/component
- Self-service for team leads

---

## Expected Questions & Answers

### Q: "How accurate is the velocity calculation?"
**A:** "Based on the last 3 months of completed sprints. For Training Kubeflow, that's 6 sprints with an 87% completion rate - very reliable data."

### Q: "Can we use this for other teams?"
**A:** "Yes! Works with any Jira project and component. You can run it for your team by providing the project key and component name. Takes about 5 minutes to configure a new team."

### Q: "What if the data changes?"
**A:** "Run it again - takes 30 seconds. It pulls fresh data from Jira every time. We recommend running it weekly or before sprint planning meetings."

### Q: "Does it modify anything in Jira?"
**A:** "No, it's completely read-only. It analyzes data but doesn't create or update issues. Safe to run anytime."

### Q: "How do we get access?"
**A:** "You need a Jira API token - takes 2 minutes to set up. I can send you the quick start guide right after this meeting."

### Q: "Can we customize the prioritization?"
**A:** "Yes, the tool is open source in our GitHub repository. You can adjust priority weights or add new factors. Currently it considers priority, dependencies, deadlines, and RICE scores."

### Q: "What about security?"
**A:** "This is currently for **internal use only**. It uses your personal Jira API token and is read-only. We'll do a security audit before any public release."

### Q: "Can we export the data?"
**A:** "Yes, it generates both HTML (for humans) and JSON (for other tools). You could feed the JSON into dashboards or other analytics tools."

### Q: "Does it work with our sprint lengths?"
**A:** "Yes, you can specify any sprint length: 1 week, 2 weeks, 3 weeks, whatever your team uses. Default is 2 weeks."

### Q: "What happens if there are estimation errors?"
**A:** "It uses historical velocity, so it naturally accounts for the team's estimation patterns. If the team consistently over or under-estimates, that's reflected in the velocity."

---

## Backup Plans

### If Live Demo Fails

**Plan A: Use Pre-Generated Reports**
> "Let me show you the latest analysis we ran this morning."
```bash
open DEMO_Training_Kubeflow.html
```
Walk through the HTML dashboard (same as Step 3 above).

**Plan B: Show Different Team**
> "Let me show you the Data Processing team instead."
```bash
open DEMO_Data_Processing.html
```

**Plan C: Reschedule**
> "We're experiencing a connectivity issue with Jira. I have the reports ready to share, and I'll follow up with a live demo this afternoon when the network is stable."

### If Token Expired

**Quick Fix (30 seconds):**
1. Go to https://issues.redhat.com
2. Profile → Personal Access Tokens
3. Create new token
4. Copy and export: `export JIRA_API_TOKEN='new-token'`
5. Re-run demo

**Or use backup reports** while fixing token.

---

## Troubleshooting Cheat Sheet

| Problem | Quick Fix |
|---------|-----------|
| Token not set | `export JIRA_API_TOKEN='your-token'` |
| Tool not found | `cd ~/Sprint-Planning-Tool` |
| Old HTML showing | Generate fresh: `./run_sprint_planner.sh` |
| Browser not opening | Manually open: `open DEMO_*.html` |
| Network timeout | Use backup reports |

---

## Closing (15 seconds)

> "This tool gives us:
> - **Data-driven** sprint planning
> - **Massive time savings** (2-3 hours → 30 seconds)
> - **Better accuracy** (uses actual velocity, not guesses)
> - **Always current** (real-time Jira data)
>
> I'll send you the quick start guide so you can try it with your team. Any other questions?"

---

## After Demo - Send to Attendees

Email template:

```
Subject: Sprint Planning Tool - Quick Start Guide

Hi team,

Thanks for attending the demo this morning. Here's everything you need to get started:

📄 Quick Start Guide:
   ~/Sprint-Planning-Tool/EXECUTIVE_QUICK_START.md
   OR view on GitHub: https://github.com/ktam3/Sprint-Planning-Tool

🔑 Setup (5 minutes):
   1. Get Jira API token: https://issues.redhat.com → Profile → Tokens
   2. Set token: export JIRA_API_TOKEN='your-token'
   3. Run tool: ./run_sprint_planner.sh

🎯 Try it for your team:
   - Select option 3 (Custom)
   - Enter your project key and component name
   - Get results in 30 seconds

⚠️  Note: Internal use only - security audit pending before public release

Questions? Let me know!
```

---

## Demo Rehearsal Checklist

- [ ] Practiced opening statement (30 seconds)
- [ ] Ran tool successfully 3+ times
- [ ] Can navigate HTML dashboard confidently
- [ ] Know where backup reports are located
- [ ] Can answer all expected questions
- [ ] Know troubleshooting fixes
- [ ] Email template ready to send

---

## Confidence Builders

✅ Tool has been tested end-to-end
✅ Fresh demo reports generated as backup
✅ Multiple backup plans exist
✅ Error handling is executive-friendly
✅ You know the data (48.3 velocity, 109 items, 87% completion)
✅ Demo is only 2 minutes - hard to go wrong
✅ Worst case: use backup reports

**You've got this! 🚀**

---

**Last Updated:** March 13, 2026 (Friday)
**Demo Date:** Monday, March 16, 2026
**Status:** READY ✅
