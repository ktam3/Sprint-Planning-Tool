# Sprint Planning Tool - Executive Quick Start Guide

> ⚠️ **INTERNAL USE ONLY** - This tool is not yet public and will be audited for security prior to being moved to public access.

## What This Tool Does

The Sprint Planning Tool analyzes your team's Jira backlog and automatically plans future sprints based on:
- **Historical velocity** - How fast your team actually delivers
- **Smart prioritization** - Uses priority, deadlines, dependencies, and RICE scores
- **Real-time data** - Pulls current backlog directly from Jira

**Output:** Professional HTML dashboard showing which issues to work on in each upcoming sprint.

---

## Prerequisites (One-Time Setup)

### 1. **Jira API Token** (Required)
You need a Jira API token to access Red Hat's Jira instance.

**To get your token:**
1. Log into Red Hat Jira: https://redhat.atlassian.net
2. Click your profile icon (top right) → **Personal Access Tokens**
3. Click **Create token**
4. Give it a name: "Sprint Planning Tool"
5. Copy the token (starts with something like `ATATT3xFfGF0...`)
6. **Save it securely** - you'll need it every time

**Note:** You'll also need your Red Hat email address (e.g., `yourname@redhat.com`)

### 2. **Python 3** (Usually Already Installed)
Check if you have it:
```bash
python3 --version
```

If not installed, download from: https://www.python.org/downloads/

### 3. **Download the Tool**
Clone or download this repository to your computer:
```bash
git clone https://github.com/ktam3/Sprint-Planning-Tool.git
cd Sprint-Planning-Tool
```

---

## Quick Start (2 Methods)

### Method 1: Interactive Menu (Easiest)

1. **Open Terminal** (Mac: Cmd+Space → type "Terminal")

2. **Navigate to tool directory:**
   ```bash
   cd ~/Sprint-Planning-Tool
   ```

3. **Set your Jira credentials:**
   ```bash
   export JIRA_EMAIL='yourname@redhat.com'
   export JIRA_API_TOKEN='your-token-here'
   ```

4. **Run the interactive script:**
   ```bash
   ./run_sprint_planner.sh
   ```

5. **Follow the prompts** - choose your team from the menu

6. **Open the HTML report** when complete

**That's it!** The tool will create a file like `2026-03-13 Training Kubeflow Team Sprint Planner.html`

---

### Method 2: Direct Command (Faster for Repeated Use)

For **Training Kubeflow Team:**
```bash
cd ~/Sprint-Planning-Tool

export JIRA_EMAIL='yourname@redhat.com'
export JIRA_API_TOKEN='your-token-here'

python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --team-name "Training Kubeflow Team" \
  --sprint-pattern "Training Kubeflow Sprint" \
  --num-sprints 4
```

For **Data Processing Team:**
```bash
cd ~/Sprint-Planning-Tool

export JIRA_EMAIL='yourname@redhat.com'
export JIRA_API_TOKEN='your-token-here'

python3 sprint_planning_tool.py \
  --project "RHAIENG,RHOAIENG" \
  --component "Data Processing,Kubeflow Spark Operator" \
  --team-name "Data Processing Team" \
  --sprint-pattern "DP Sprint" \
  --num-sprints 4
```

---

## Understanding the Output

### Console Output
You'll see a summary like this:
```
📊 Calculating team velocity (last 3 months)...
   Velocity: 47.2 story points/sprint
   Completion Rate: 86%
   Sprints Analyzed: 5

📋 Fetching backlog...
   Found 100 backlog items

🔢 Detecting current sprint...
   Current Sprint: Training Kubeflow Sprint 27
   Planning for: Training Kubeflow Sprint 28 - 31

📅 SPRINT PLAN SUMMARY
Training Kubeflow Sprint 28:
  Capacity: 47.0 / 47.2 story points (100%)
  Already Planned: 15 items
  Recommended: 87 items
```

### HTML Dashboard
- **Sprint Cards**: Each sprint shows assigned items, capacity bars
- **Clickable Jira Links**: Click any issue to open in Jira
- **Priority Colors**: Red = Blocker, Orange = Critical, etc.
- **Recommendations**: Warnings about capacity, risks, dependencies

### JSON Data
- Machine-readable format for integration with other tools
- Contains complete planning data, metadata, recommendations

---

## Common Scenarios

### Scenario 1: "How many sprints until we finish the backlog?"
```bash
python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --sprint-pattern "Training Kubeflow Sprint" \
  --num-sprints 8
```
Increase `--num-sprints` to see longer-term planning.

---

### Scenario 2: "What if we switch to 3-week sprints?"
```bash
python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --sprint-pattern "Training Kubeflow Sprint" \
  --sprint-length 3
```
Change `--sprint-length` to model different sprint durations.

---

### Scenario 3: "Show me just the next 2 sprints"
```bash
python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --sprint-pattern "Training Kubeflow Sprint" \
  --num-sprints 2
```
Fewer sprints = faster results for quick checks.

---

## Troubleshooting

### ❌ "JIRA_API_TOKEN environment variable must be set"
**Fix:** You forgot to set your credentials. Run:
```bash
export JIRA_EMAIL='yourname@redhat.com'
export JIRA_API_TOKEN='your-token-here'
```

### ❌ "JIRA_EMAIL environment variable must be set"
**Fix:** You need to set your Red Hat email address:
```bash
export JIRA_EMAIL='yourname@redhat.com'
```

---

### ❌ "Error fetching issues (HTTP 400)"
**Possible causes:**
1. **Invalid token** - Check you copied the full token correctly
2. **Expired token** - Generate a new token from Jira
3. **Wrong project/component name** - Verify the exact name in Jira

---

### ❌ "Found 0 backlog items"
**Possible causes:**
1. **Wrong component name** - Check exact spelling in Jira
2. **All items already in sprints** - Tool only shows unassigned backlog
3. **Team filter too restrictive** - Try removing `--team-id` parameter

---

### ❌ "Velocity: 0.0 story points/sprint"
**Possible causes:**
1. **No sprint history** - New team or sprint pattern doesn't match
2. **Wrong sprint pattern** - Verify your team's sprint naming (e.g., "DP Sprint", "Training Kubeflow Sprint")
3. **Need more history** - Add `--velocity-months 6` to look back further
4. **No story points on issues** - Tool will fall back to issue count if no story points are found

**Fix:** The tool will still work but will use estimated velocity.

---

## Advanced Options

| Option | Description | Example |
|--------|-------------|---------|
| `--num-sprints` | Number of future sprints to plan | `--num-sprints 6` |
| `--sprint-length` | Sprint length in weeks | `--sprint-length 3` |
| `--velocity-months` | Months of history to analyze | `--velocity-months 6` |
| `--output-html` | Custom HTML filename | `--output-html my_plan.html` |
| `--output-json` | Custom JSON filename | `--output-json my_plan.json` |
| `--sprint-pattern` | Sprint naming pattern (recommended) | `--sprint-pattern "DP Sprint"` |

**Note:** `--team-id` parameter has been temporarily disabled due to Jira migration changes. Use `--component` for team filtering.

---

## Best Practices

### ✅ DO:
- Run weekly to keep plans fresh
- Use for sprint planning meetings
- Try different scenarios (what-if analysis)
- Share HTML reports with stakeholders
- Keep your Jira token secure

### ❌ DON'T:
- Share your API token with others
- Commit tokens to git/code repositories
- Assume the tool modifies Jira (it's read-only)
- Ignore capacity warnings in the output

---

## Support

### For Issues:
1. Check this guide's troubleshooting section
2. Verify your JIRA_API_TOKEN is valid
3. Test your parameters directly in Jira
4. Check the detailed guide: `SPRINT_PLANNING_TOOL_GUIDE.md`

### For New Features:
Contact the tool maintainer or create an issue in the repository.

---

## Security Notes

⚠️ **This tool is currently for INTERNAL USE ONLY**

- Not yet reviewed for public release
- Will undergo security audit before public availability
- Keep API tokens secure and private
- Do not commit tokens to version control
- Do not share tokens via email/chat

**Credential Best Practices:**
- Use environment variables (not hardcoded tokens)
- Generate new tokens periodically
- Revoke old tokens when no longer needed
- Never commit `.git-credentials` or similar files

---

## Example Workflow for Monday Morning

**Goal:** Review Training Kubeflow team's sprint planning

1. **Open Terminal**

2. **Navigate to tool:**
   ```bash
   cd ~/Sprint-Planning-Tool
   ```

3. **Set credentials** (if not already set in your shell profile):
   ```bash
   export JIRA_EMAIL='yourname@redhat.com'
   export JIRA_API_TOKEN='your-token-here'
   ```

4. **Run analysis:**
   ```bash
   python3 sprint_planning_tool.py \
     --project RHOAIENG \
     --component "Training Kubeflow" \
     --sprint-pattern "Training Kubeflow Sprint" \
     --num-sprints 4
   ```

5. **Open HTML report:**
   ```bash
   open "2026-03-16 Training Kubeflow Team Sprint Planner.html"
   ```

6. **Review in browser:**
   - Check sprint capacity utilization
   - Review recommended items for next sprint
   - Note any warnings/risks
   - Click through to Jira issues as needed

**Total time:** ~30 seconds

---

## Quick Reference Card

```bash
# Set credentials (once per session)
export JIRA_EMAIL='yourname@redhat.com'
export JIRA_API_TOKEN='your-token-here'

# Navigate to tool
cd ~/Sprint-Planning-Tool

# Run for Training Kubeflow (copy-paste ready)
python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --sprint-pattern "Training Kubeflow Sprint" \
  --num-sprints 4

# Open latest report
open "$(ls -t *.html | head -1)"
```

---

**Last Updated:** March 16, 2026
**Version:** 2.0 (Updated for new Jira instance)
**Status:** Internal Use Only - Security Audit Pending

---

## 🔄 Version 2.0 Updates (March 16, 2026)

**What Changed:**
- ✅ Updated for Red Hat's Jira migration to Atlassian Cloud (redhat.atlassian.net)
- ✅ Now requires both JIRA_EMAIL and JIRA_API_TOKEN
- ✅ Calculates velocity using **story points** instead of issue count
- ✅ Removed `--team-id` parameter (temporarily disabled due to ID format change)
- ✅ Updated to Jira API v3

**Impact on Results:**
- More accurate velocity calculations (47.2 story points/sprint vs. 17 issues/sprint)
- Better capacity planning based on actual effort/complexity
- Improved sprint planning accuracy
