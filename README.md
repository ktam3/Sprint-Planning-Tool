# Sprint Planning Tool

Automated sprint planning tool that analyzes your Jira backlog and creates data-driven sprint plans in seconds.

## 🚀 Quick Start (5 Minutes)

**1. Get your Jira API token:**
- Go to https://redhat.atlassian.net
- Profile → Personal Access Tokens → Create token
- Copy the token

**2. Run the tool:**
```bash
cd Sprint-Planning-Tool
export JIRA_EMAIL='your-email@redhat.com'
export JIRA_API_TOKEN='your-token-here'

python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --sprint-pattern "Training Kubeflow Sprint"
```

**3. Open the HTML report:**
```bash
open "2026-03-13 Training Kubeflow Sprint Planner.html"
```

**Done!** You now have a professional sprint plan based on your team's actual velocity and backlog.

---

## 📊 What It Does

- **Calculates Team Velocity** from sprint history using story points (e.g., 47.2 story points/sprint)
- **Analyzes Backlog** in real-time from Jira (e.g., 100+ items)
- **Plans Multiple Sprints** ahead (default: 4 sprints)
- **Prioritizes Intelligently** using dependencies, deadlines, and RICE scores
- **Generates HTML Dashboards** with capacity bars and clickable issue links
- **Provides Recommendations** for capacity warnings and risks
- **Supports Story Points** - automatically uses story points if available, falls back to issue count

**Time Savings:** Manual sprint planning (~2-3 hours) → Automated (~30 seconds) = **99% faster!**

---

## 📚 Documentation

| Document | Purpose | Who Should Read |
|----------|---------|-----------------|
| **[EXECUTIVE_QUICK_START.md](EXECUTIVE_QUICK_START.md)** | Simple guide for non-technical users | Executives, Managers |
| **[SPRINT_PLANNING_TOOL_GUIDE.md](SPRINT_PLANNING_TOOL_GUIDE.md)** | Complete usage guide with all options | Team Leads, Scrum Masters |
| **[SPRINT_RISK_TOOL_GUIDE.md](SPRINT_RISK_TOOL_GUIDE.md)** | Risk analysis companion tool | Advanced Users |
| **[MONDAY_DEMO_SCRIPT.md](MONDAY_DEMO_SCRIPT.md)** | 5-minute demo walkthrough | Anyone demoing the tool |
| **[NEW_USER_WALKTHROUGH.md](NEW_USER_WALKTHROUGH.md)** | Step-by-step new user experience | First-time users |

---

## 💡 Key Features

### Intelligent Prioritization
Uses 6 factors to prioritize your backlog:
- Issue priority (Blocker, Critical, High, etc.)
- Parent Feature priority
- Target end dates
- Target version (EA, RC, GA)
- RICE scores
- Dependencies (blockers prioritized first)

### Team ID Filtering
**Note**: Team IDs changed with the Jira migration. The old numeric IDs (e.g., 4967) no longer work.
For now, omit the `--team-id` parameter and rely on the component filter:
```bash
# Component filter is usually sufficient
--component "Training Kubeflow"
```

### Carry-Over Tracking
Automatically detects items stuck in 3+ closed sprints that are still not done, and flags them in the console output, HTML dashboard, and recommendations. Tune the threshold with:
```bash
--carry-over-sprints 2   # Flag items in 2+ closed sprints (default: 3)
```

### What-If Analysis
Try different scenarios:
```bash
--num-sprints 6        # Plan 6 sprints ahead
--sprint-length 3      # Try 3-week sprints
--velocity-months 6    # Use 6 months of history
```

### Multi-Project/Component Support
```bash
--project "RHAIENG,RHOAIENG"
--component "Data Processing,Kubeflow Spark Operator"
```

---

## 🎯 Example: Training Kubeflow Team

```bash
python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --sprint-pattern "Training Kubeflow Sprint" \
  --num-sprints 4
```

**Results:**
- ✅ Velocity: 47.2 story points/sprint (based on last 5 sprints)
- ✅ Completion Rate: 86%
- ✅ Backlog: 100 items analyzed
- ✅ Current Sprint: Training Kubeflow Sprint 27
- ✅ Planning: Sprints 28-31
- ✅ Sprint 28: 47 story points planned (15 items)

**Output:**
- Professional HTML dashboard
- JSON data for integration
- Capacity warnings and recommendations

---

## 🌐 Web Dashboard (Easiest)

Launch the interactive Streamlit dashboard:
```bash
pip3 install streamlit python-dotenv
streamlit run streamlit_app.py
```

Features:
- No command-line arguments needed — configure everything in the sidebar
- Tabbed interface: Sprint Plan, Timeline, and Help
- Clickable Jira links, capacity bars, and downloadable reports
- Auto-detects sprint length from Jira
- Credentials load automatically from a `.env` file (no export needed)

## 🛠️ Interactive CLI Mode

For a terminal menu-driven experience:
```bash
./run_sprint_planner.sh
```

Select your team from the menu and get results instantly!

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/ktam3/Sprint-Planning-Tool.git
cd Sprint-Planning-Tool

# Make scripts executable
chmod +x sprint_planning_tool.py
chmod +x run_sprint_planner.sh

# Set your Jira token
export JIRA_API_TOKEN='your-token-here'

# Run it!
python3 sprint_planning_tool.py --project YOUR_PROJECT --component "Your Component"
```

**Requirements:**
- Python 3.x
- Jira API token
- `streamlit` and `python-dotenv` (for web dashboard only)
- Network access to Jira instance

---

## 🔒 Security Notice

⚠️ **INTERNAL USE ONLY** - This tool is currently for internal use. It will undergo security audit before public release.

- ✅ Read-only access to Jira (doesn't modify data)
- ✅ Uses personal API tokens (not shared credentials)
- ✅ No data sent to external services
- ⏳ Security audit pending before public release

---

## 🧪 Testing Status

| Test Suite | Status | Coverage |
|-------------|--------|----------|
| Core Functionality | ✅ PASS (6/6) | 100% |
| Error Handling | ✅ PASS | 100% |
| New User Experience | ✅ PASS | Validated |
| Executive Demo Ready | ✅ READY | Tested |

**Test Results:**
- All critical tests passed
- Fresh demo reports generated
- Error handling validated
- Professional output verified

See [FRIDAY_TEST_RESULTS_COMPLETE.md](FRIDAY_TEST_RESULTS_COMPLETE.md) for detailed test results.

---

## 🤝 Support

**Getting Started:**
1. Read [EXECUTIVE_QUICK_START.md](EXECUTIVE_QUICK_START.md)
2. Try the minimal example above
3. Review [SPRINT_PLANNING_TOOL_GUIDE.md](SPRINT_PLANNING_TOOL_GUIDE.md) for advanced options

**Troubleshooting:**
- Check the Troubleshooting section in [SPRINT_PLANNING_TOOL_GUIDE.md](SPRINT_PLANNING_TOOL_GUIDE.md)
- Verify your JIRA_API_TOKEN is set correctly
- Ensure component name matches Jira exactly

**Questions?**
- Open an issue on GitHub
- Review the comprehensive documentation

---

## 📈 Success Stories

**Training Kubeflow Team:**
- Before: Manual planning took 2-3 hours
- After: Automated planning takes 30 seconds
- Impact: 99% time savings per sprint

**Data Processing Team:**
- Multi-component support (Data Processing + Kubeflow Spark Operator)
- Multi-project filtering (RHAIENG + RHOAIENG)
- Sprint pattern filtering for accurate velocity

---

## 🎓 Learning Resources

**For New Users:**
1. Start with [EXECUTIVE_QUICK_START.md](EXECUTIVE_QUICK_START.md) (5 min read)
2. Follow [NEW_USER_WALKTHROUGH.md](NEW_USER_WALKTHROUGH.md) (10 min hands-on)
3. Explore [SPRINT_PLANNING_TOOL_GUIDE.md](SPRINT_PLANNING_TOOL_GUIDE.md) (complete reference)

**For Demos:**
1. Review [MONDAY_DEMO_SCRIPT.md](MONDAY_DEMO_SCRIPT.md)
2. Generate fresh demo reports
3. Practice the 2-minute walkthrough

---

## 🚀 Quick Commands

```bash
# Training Kubeflow Team
export JIRA_EMAIL='your-email@redhat.com'
export JIRA_API_TOKEN='your-token'

python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --sprint-pattern "Training Kubeflow Sprint"

# Data Processing Team
python3 sprint_planning_tool.py \
  --project "RHAIENG,RHOAIENG" \
  --component "Data Processing,Kubeflow Spark Operator" \
  --sprint-pattern "DP Sprint"

# Interactive Mode
./run_sprint_planner.sh
```

---

## 📝 License

Internal Red Hat use only. Security audit pending before public release.

---

## 🎯 Key Takeaways

✅ **Saves Time:** 2-3 hours → 30 seconds (99% faster)
✅ **Data-Driven:** Uses real velocity, not guesses
✅ **Professional Output:** HTML dashboards ready to share
✅ **Easy to Use:** Works on first try for new users
✅ **Flexible:** What-if analysis, multi-team support
✅ **Well-Tested:** 100% test pass rate

**Ready to try it? Start with the [EXECUTIVE_QUICK_START.md](EXECUTIVE_QUICK_START.md)!** 🚀

---

**Last Updated:** March 26, 2026
**Version:** 2.3 (Streamlit web dashboard)
**Status:** Production Ready for Internal Use

## 🔄 What's New in v2.3 (March 26, 2026)

**Streamlit Web Dashboard**
- ✅ **Interactive web UI** - `streamlit run streamlit_app.py` for a browser-based experience
- ✅ **Tabbed interface** - Sprint Plan, Timeline, and Help tabs
- ✅ **Auto-detect sprint length** - Calculated from current sprint start/end dates in Jira
- ✅ **Exclude Epics** - Epic issue types filtered out of all results
- ✅ **`.env` credential support** - No need to export tokens every session
- ✅ **Project multiselect** - Checkbox selection for RHOAIENG and RHAIENG

## 🔄 What's New in v2.2 (March 24, 2026)

**Carry-Over Tracking**
- ✅ **Chronic carry-over detection** - Flags items stuck in 3+ closed sprints that are still not done
- ✅ **HTML dashboard section** - Carry-over table with clickable Jira links, color-coded sprint counts, and assignee info
- ✅ **Automated recommendations** - HIGH severity for 5+ sprints, MEDIUM for 3-4 sprints
- ✅ **Configurable threshold** - `--carry-over-sprints N` to tune sensitivity (default: 3)
- ✅ **Cleanup** - Removed leftover debug scripts

## 🔄 What's New in v2.1 (March 18, 2026)

**Critical Bug Fixes:**
- ✅ **Fixed case-sensitive sprint state check** - Now properly detects future/active sprints (was missing items)
- ✅ **Fixed pagination duplicates** - Implemented cursor-based pagination with `nextPageToken`
- ✅ **Fixed velocity inflation** - Issues now only counted once in most recent sprint (was 200-300% inflated)

**Impact:**
- Velocity calculations now accurate (e.g., Llama Stack: 95.8 pts vs incorrectly 129.2 pts)
- Sprint item detection working correctly (e.g., now detects all 4 items in Sprint 14 vs only 1)
- Pagination now fetches all issues beyond first 100

See [BUG_FIXES_2026-03-18.md](BUG_FIXES_2026-03-18.md) for detailed information.

## 🔄 What's New in v2.0 (March 16, 2026)

Updated for Red Hat's migration to Atlassian Cloud (redhat.atlassian.net):
- ✅ Updated authentication to use Basic auth (email + API token)
- ✅ Migrated to Jira API v3 (`/rest/api/3/search/jql`)
- ✅ Updated Sprint field ID (customfield_10020)
- ✅ **Updated Story Points field ID (customfield_10028) - now calculates velocity in story points!**
- ✅ Added support for new JSON sprint data format
- ✅ Team ID filtering temporarily disabled (IDs changed from numeric to UUIDs)
