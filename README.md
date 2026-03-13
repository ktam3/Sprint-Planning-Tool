# Sprint Planning Tool

Automated sprint planning tool that analyzes your Jira backlog and creates data-driven sprint plans in seconds.

## 🚀 Quick Start (5 Minutes)

**1. Get your Jira API token:**
- Go to https://issues.redhat.com
- Profile → Personal Access Tokens → Create token
- Copy the token

**2. Run the tool:**
```bash
cd Sprint-Planning-Tool
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

- **Calculates Team Velocity** from sprint history (e.g., 48.3 story points/sprint)
- **Analyzes Backlog** in real-time from Jira (e.g., 109 items)
- **Plans Multiple Sprints** ahead (default: 4 sprints)
- **Prioritizes Intelligently** using dependencies, deadlines, and RICE scores
- **Generates HTML Dashboards** with capacity bars and clickable issue links
- **Provides Recommendations** for capacity warnings and risks

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
Filter to your team's items only:
```bash
--team-id 4967  # Excludes cross-team items
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
  --team-id 4967 \
  --sprint-pattern "Training Kubeflow Sprint" \
  --num-sprints 4
```

**Results:**
- ✅ Velocity: 48.3 story points/sprint (based on last 6 sprints)
- ✅ Completion Rate: 87%
- ✅ Backlog: 109 items analyzed
- ✅ Current Sprint: Training Kubeflow Sprint 27
- ✅ Planning: Sprints 28-31

**Output:**
- Professional HTML dashboard
- JSON data for integration
- Capacity warnings and recommendations

---

## 🛠️ Interactive Mode (Easiest)

For a menu-driven experience:
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
python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --team-id 4967 \
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

**Last Updated:** March 13, 2026
**Version:** 1.0
**Status:** Production Ready for Internal Use
