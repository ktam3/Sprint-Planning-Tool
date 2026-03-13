# Generic Sprint Risk Predictor - Usage Guide

A universal Jira risk analysis tool that works with any team, project, or Jira instance.

## Features

- ✅ **Universal**: Works with any Jira project and team configuration
- 🎯 **Flexible Filtering**: Filter by project, component, assignee, label, or custom JQL
- 📊 **Risk Detection**: Identifies blocked issues, high-priority not started, unassigned work, stale items
- 💡 **Actionable Strategies**: Provides specific mitigation steps with timelines
- ⚠️ **Outcome Prediction**: Shows consequences if risks are ignored
- 📈 **Velocity Analysis**: Calculates team velocity and completion rates

## Setup

### Prerequisites

1. **Jira API Token**
   - Generate from your Jira account settings
   - Set as environment variable:
   ```bash
   export JIRA_API_TOKEN='your-token-here'
   ```

2. **Jira URL** (optional, defaults to https://issues.redhat.com)
   ```bash
   export JIRA_URL='https://your-jira-instance.com'
   ```

### Installation

```bash
chmod +x generic_sprint_risk_predictor.py
```

## Usage Examples

### Basic Usage

**Analyze by Project and Component:**
```bash
python3 generic_sprint_risk_predictor.py \
  --project MYPROJECT \
  --component "Backend Team"
```

**Multiple Components:**
```bash
python3 generic_sprint_risk_predictor.py \
  --project MYPROJECT \
  --component "API,Database,Authentication"
```

**Filter by Assignee:**
```bash
python3 generic_sprint_risk_predictor.py \
  --project MYPROJECT \
  --assignee "john.doe"
```

**Filter by Label:**
```bash
python3 generic_sprint_risk_predictor.py \
  --project MYPROJECT \
  --label "platform-team"
```

### Advanced Usage

**Custom JQL Query:**
```bash
python3 generic_sprint_risk_predictor.py \
  --jql "project = PLATFORM AND team = 'Core Services'"
```

**Specify Sprint History for Accurate Velocity:**
```bash
python3 generic_sprint_risk_predictor.py \
  --project MYPROJECT \
  --component "Frontend" \
  --sprint-names "Sprint 10,Sprint 11,Sprint 12,Sprint 13"
```

**Custom Team Name in Report:**
```bash
python3 generic_sprint_risk_predictor.py \
  --project MYPROJECT \
  --component "BE" \
  --team-name "Backend Engineering Team"
```

**Custom Status Definitions:**
```bash
python3 generic_sprint_risk_predictor.py \
  --project MYPROJECT \
  --component "QA" \
  --done-statuses "Completed,Verified,Closed" \
  --progress-statuses "In Testing,In Review,QA" \
  --todo-statuses "Open,New,Planned"
```

## Command-Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--project` | Jira project key | `--project PLATFORM` |
| `--component` | Component name(s), comma-separated | `--component "API,Auth"` |
| `--assignee` | Filter by assignee username | `--assignee john.doe` |
| `--label` | Filter by label(s), comma-separated | `--label "backend,critical"` |
| `--jql` | Custom JQL query (overrides other filters) | `--jql "project = X AND team = Y"` |
| `--team-name` | Team name for report header | `--team-name "Platform Engineering"` |
| `--sprint-names` | Sprint names for velocity calculation | `--sprint-names "Sprint 1,Sprint 2"` |
| `--done-statuses` | Custom done statuses | `--done-statuses "Done,Closed"` |
| `--progress-statuses` | Custom in-progress statuses | `--progress-statuses "In Progress,Review"` |
| `--todo-statuses` | Custom todo statuses | `--todo-statuses "New,Backlog"` |

## Output Sections

### 1. Executive Summary
- Team velocity (issues/sprint)
- Completion rate percentage
- Current sprint and backlog size
- Total risk items identified

### 2. Detailed Risk Analysis

**Current Sprint Risks:**
- 🚫 **Blocked Issues**: Issues waiting on incomplete dependencies
- ⚠️ **High Priority Not Started**: Critical/Blocker items not begun
- 👤 **Unassigned Issues**: Work without owners
- ⏰ **Stale In-Progress**: Items unchanged for 7+ days

**Backlog Risks:**
- 🔴 **High Priority Unplanned**: Critical items not in any sprint
- 📊 **Capacity Shortage**: When backlog exceeds team capacity

### 3. Mitigation Strategies

For each risk:
- ✅ **Specific action steps** with clear ownership
- ⏱️ **Timeline** (Immediate, Urgent, High Priority, etc.)
- 🎯 **Severity** level (Critical, High, Medium, Low)
- ❌ **Predicted outcomes** if ignored

### 4. Immediate Action Items

Prioritized list of critical next steps sorted by urgency.

## Risk Severity Levels

| Severity | Timeline | Example |
|----------|----------|---------|
| 🔴 **CRITICAL** | IMMEDIATE (24-48 hours) | Blocked issues, low completion rate |
| 🟠 **HIGH** | URGENT (2-3 days to 1 week) | High-priority not started, capacity shortage |
| 🟡 **MEDIUM** | MODERATE (3-5 days) | Stale items, unassigned work |
| 🟢 **LOW** | STRATEGIC (1-2 sprints) | Minor backlog issues |

## Common Use Cases

### Use Case 1: Team Sprint Health Check
```bash
python3 generic_sprint_risk_predictor.py \
  --project PLATFORM \
  --component "Backend API" \
  --team-name "Backend Team"
```
**When**: Run at sprint mid-point and before sprint close
**Goal**: Identify risks before they impact sprint delivery

### Use Case 2: Cross-Team Analysis
```bash
# Frontend
python3 generic_sprint_risk_predictor.py --project APP --component "Frontend"

# Backend
python3 generic_sprint_risk_predictor.py --project APP --component "Backend"

# DevOps
python3 generic_sprint_risk_predictor.py --project APP --component "DevOps"
```
**When**: Weekly or bi-weekly across all teams
**Goal**: Portfolio-level risk visibility

### Use Case 3: Individual Contributor View
```bash
python3 generic_sprint_risk_predictor.py \
  --project PLATFORM \
  --assignee currentUser() \
  --team-name "My Work"
```
**When**: Daily personal planning
**Goal**: Individual workload risk assessment

### Use Case 4: Release Risk Assessment
```bash
python3 generic_sprint_risk_predictor.py \
  --jql "project = PLATFORM AND fixVersion = '3.4.0'" \
  --team-name "Release 3.4.0"
```
**When**: Before release planning and during release cycle
**Goal**: Release-level risk tracking

## Interpreting Results

### Healthy Team Indicators ✅
- Completion rate: 80%+
- 0 blocked issues
- <5% unassigned issues
- <10% stale items
- Backlog within 2x sprint capacity

### Warning Signs ⚠️
- Completion rate: 60-79%
- 1-3 blocked issues
- 5-15% unassigned
- 10-20% stale items
- Backlog 2-3x capacity

### Critical Risks 🚨
- Completion rate: <60%
- 4+ blocked issues
- >15% unassigned
- >20% stale items
- Backlog >3x capacity

## Automation Tips

### Daily Slack Report
```bash
#!/bin/bash
# daily_risk_report.sh

OUTPUT=$(JIRA_API_TOKEN=$JIRA_TOKEN python3 generic_sprint_risk_predictor.py \
  --project MYPROJ \
  --component "My Team")

# Post to Slack
curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"Daily Risk Report:\n\`\`\`$OUTPUT\`\`\`\"}" \
  $SLACK_WEBHOOK_URL
```

### CI/CD Integration
```yaml
# .github/workflows/sprint-risk-check.yml
name: Sprint Risk Check
on:
  schedule:
    - cron: '0 9 * * 1-5'  # Weekdays at 9 AM

jobs:
  risk-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Risk Analysis
        env:
          JIRA_API_TOKEN: ${{ secrets.JIRA_TOKEN }}
        run: |
          python3 generic_sprint_risk_predictor.py \
            --project MYPROJ \
            --component "CI/CD Team" > risk-report.txt
      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: risk-report
          path: risk-report.txt
```

### Multi-Team Weekly Report
```bash
#!/bin/bash
# weekly_team_reports.sh

TEAMS=(
  "Frontend:FE"
  "Backend:BE"
  "DevOps:OPS"
  "QA:QA"
)

for team_config in "${TEAMS[@]}"; do
  IFS=':' read -r team_name component <<< "$team_config"

  echo "=== $team_name Team ===" >> weekly_report.txt

  JIRA_API_TOKEN=$JIRA_TOKEN python3 generic_sprint_risk_predictor.py \
    --project PLATFORM \
    --component "$component" \
    --team-name "$team_name" >> weekly_report.txt

  echo "" >> weekly_report.txt
done

# Email the report
cat weekly_report.txt | mail -s "Weekly Sprint Risk Report" team-leads@company.com
```

## Troubleshooting

### No Sprint Data Found
**Problem**: "No current sprint data found"

**Solutions**:
1. Check if team has open sprints: Verify in Jira UI
2. Verify JQL filter: Test the filter directly in Jira
3. Check authentication: Ensure JIRA_API_TOKEN is set correctly
4. Verify permissions: Ensure token has read access to project

### Inaccurate Velocity
**Problem**: Velocity calculation seems wrong

**Solutions**:
1. Specify sprint names explicitly with `--sprint-names`
2. Verify sprint naming convention matches your team's
3. Check if closed sprints are available in Jira
4. Customize done statuses with `--done-statuses` if needed

### Missing Risks
**Problem**: Known risks not appearing in report

**Solutions**:
1. Adjust stale threshold (currently hardcoded to 7 days)
2. Customize status definitions with `--done-statuses`, `--progress-statuses`, `--todo-statuses`
3. Verify priority levels match your Jira configuration
4. Check if issues are actually in current sprint

## Best Practices

1. **Run Regularly**: Daily for active sprints, weekly for backlog
2. **Customize Statuses**: Match your team's workflow states
3. **Track Trends**: Save reports to compare week-over-week
4. **Act Quickly**: Address CRITICAL risks within 24-48 hours
5. **Share Widely**: Make reports visible to whole team
6. **Calibrate Thresholds**: Adjust for your team's normal velocity
7. **Combine with Retros**: Use insights in retrospectives

## Support

For issues or feature requests:
- Review the JQL query being generated
- Test the JQL directly in Jira's issue navigator
- Check Jira API permissions
- Verify environment variables are set correctly
