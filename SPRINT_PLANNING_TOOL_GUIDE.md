# Sprint Planning Tool - Usage Guide

## Overview
Comprehensive sprint planning tool that helps scrum teams plan current and future sprints based on:
- Real-time backlog analysis via Jira API
- Historical velocity calculation
- Intelligent prioritization using parent Feature data
- Integration with sprint health/risk analysis tools
- Dependency-aware scheduling

## Features

### ✅ What It Does
1. **Calculates Team Velocity** - From sprint history (configurable lookback period)
2. **Fetches Real-Time Backlog** - Direct from Jira API
3. **Intelligent Prioritization** - Using multiple factors:
   - Issue's Jira priority
   - Parent Feature's priority
   - Parent Feature's target end date
   - Parent Feature's target version
   - Parent Feature's RICE score
   - Dependency chains (blockers → blocked items)
4. **Plans Multiple Sprints** - 1-4 sprints ahead (configurable)
5. **Generates Recommendations** - Capacity warnings, risk alerts, actions
6. **Creates Timeline Forecasts** - When will critical items complete?
7. **Integrates with Teammate Tools** - Uses risk/health analysis data
8. **Multiple Output Formats** - Python objects, HTML dashboard, JSON

### ✅ Standalone Capability
Works without teammate tools - just needs Jira API access

## Installation

```bash
chmod +x sprint_planning_tool.py
export JIRA_API_TOKEN='your-token-here'
export JIRA_URL='https://issues.redhat.com'  # Optional, defaults to Red Hat Jira
```

## Basic Usage

### Minimal Example
```bash
python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow"
```

### Full Example
```bash
python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --team-name "Training Kubeflow Team" \
  --sprint-pattern "Training Kubeflow Sprint" \
  --num-sprints 4 \
  --sprint-length 2 \
  --velocity-months 3 \
  --output-html sprint_plan.html \
  --output-json sprint_plan.json \
  --risk-data-file risk_analysis.json
```

## Command-Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--project` | Yes | - | Jira project key (e.g., RHOAIENG) |
| `--component` | Yes | - | Team component name (e.g., "Training Kubeflow") |
| `--team-name` | No | component | Team display name for reports |
| `--sprint-pattern` | No | None | Sprint naming pattern for filtering history |
| `--num-sprints` | No | 4 | Number of future sprints to plan (1-4+) |
| `--sprint-length` | No | 2 | Sprint length in weeks |
| `--velocity-months` | No | 3 | Months to look back for velocity calculation |
| `--output-html` | No | None | Path to save HTML dashboard |
| `--output-json` | No | None | Path to save JSON data |
| `--risk-data-file` | No | None | Path to risk analysis JSON from teammate tools |

## How Prioritization Works

The tool calculates a priority score (0-500+ points) for each backlog item:

### Priority Components

1. **Issue's Own Priority** (0-100 points)
   - Blocker: 100
   - Critical: 80
   - High: 60
   - Major: 50
   - Normal: 30
   - Low: 20

2. **Parent Feature's Priority** (0-100 points)
   - Same scale as above
   - Only if issue is linked to a Feature

3. **Parent Feature's Target End Date** (0-50 points)
   - Past due: 50 points
   - Within 30 days: 40 points
   - Within 60 days: 30 points
   - Within 90 days: 20 points
   - Beyond 90 days: 10 points

4. **Parent Feature's Target Version** (0-30 points)
   - EA (Early Access): 30 points
   - RC (Release Candidate): 25 points
   - GA (General Availability): 20 points
   - Other: 10 points

5. **Parent Feature's RICE Score** (0-100 points)
   - Normalized from Feature's RICE score
   - Looks in custom fields, labels, or description

6. **Dependency Boost** (0-N points)
   - +10 points for each issue this one blocks
   - Ensures blockers are prioritized

### Dependency Handling

- **Blockers scheduled first** - Before items they block
- **Blocked items scheduled after** - In sprint after their blockers
- **Respects team dependencies** - Only for team's own blockers

## Integration with Teammate Tools

### Expected Risk Data Format (JSON)

```json
{
  "blocked_issues": [
    {"key": "ISSUE-123", "blocker": "ISSUE-456"}
  ],
  "current_sprint_capacity_used": 0.7,
  "velocity": 25.5,
  "completion_rate": 75,
  "risks": [
    {
      "type": "WARNING",
      "severity": "HIGH",
      "message": "5 blocked issues in current sprint"
    }
  ]
}
```

### How Risk Data Is Used

1. **Adjusts Recommendations** - Considers current sprint health
2. **Capacity Planning** - Uses actual capacity if available
3. **Risk Warnings** - Surfaces critical issues from health analysis
4. **Standalone Mode** - If file not provided, works with Jira data only

## Output Formats

### 1. Console Output
- Summary of each sprint assignment
- Capacity utilization
- Warnings and alerts
- Quick overview for terminal use

### 2. HTML Dashboard (`--output-html`)
- Visual sprint cards with capacity bars
- Color-coded priority items (Red: Blocker, Orange: Critical)
- Recommendations with severity icons
- Timeline table with milestones
- Fully formatted, ready for sharing

### 3. JSON Data (`--output-json`)
- Complete structured data
- Programmatic access
- Can be consumed by other tools
- Includes all metadata

### 4. Python Object (return value)
```python
{
  'sprint_assignments': {
    'Sprint 1': {
      'capacity': 25.5,
      'items': [...],
      'capacity_used': 24.0,
      'warnings': [...]
    }
  },
  'recommendations': [...],
  'timeline': {
    'sprints': [...],
    'milestones': [...]
  },
  'metadata': {...}
}
```

## Example Workflow

### 1. Run Risk Analysis (Teammate's Tool)
```bash
python3 sprint_risk_predictor.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --output-json risk_data.json
```

### 2. Run Sprint Planning
```bash
python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --sprint-pattern "Training Kubeflow Sprint" \
  --risk-data-file risk_data.json \
  --output-html plan.html
```

### 3. Review Plan
- Open `plan.html` in browser
- Review sprint assignments
- Check recommendations
- Verify timeline forecast

### 4. Adjust and Iterate
```bash
# Try different sprint count
python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --num-sprints 6 \
  --output-html plan_6sprints.html

# Try different sprint length
python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --sprint-length 3 \
  --output-html plan_3weeks.html
```

## Understanding the Output

### Sprint Assignments

Each sprint shows:
- **Capacity**: How many issues the team can handle (based on velocity)
- **Items**: Specific issues assigned to this sprint
- **Capacity Used**: How many issues are planned
- **Utilization**: Percentage (100% = fully loaded, >100% = overcommitted)

### Recommendations

Types:
- **🔴 RISK (CRITICAL)**: Immediate attention needed
- **🟠 WARNING (HIGH)**: Important to address
- **🟡 INFO (MEDIUM)**: Consider for optimization
- **🟢 INFO (LOW)**: Nice to know

### Timeline Forecast

Shows:
- Start/end dates for each sprint
- Number of items in each sprint
- Key milestones (Blocker items completing)
- Helps answer: "When will we finish X?"

## Troubleshooting

### No Backlog Items Found
**Problem**: "Found 0 backlog items"

**Solutions**:
1. Check component name matches Jira exactly
2. Verify issues aren't already in sprints
3. Check status filters (excludes Done/Closed/Resolved by default)

### Velocity is 0
**Problem**: "Velocity: 0.0 issues/sprint"

**Solutions**:
1. Check sprint pattern matches your team's naming
2. Verify closed sprints exist in last 3 months
3. Try increasing `--velocity-months` (e.g., 6 months)

### Parent Feature Not Found
**Problem**: Issues not showing parent Feature data

**Solutions**:
1. Verify issues are actually linked to Features in Jira
2. Check if using "Parent Link" field vs direct parent
3. May need to adjust custom field IDs in code

### RICE Score Not Found
**Problem**: RICE scores showing as None

**Solutions**:
1. Check where RICE is stored in your Jira (custom field? label? description?)
2. Verify field ID in code matches your Jira instance
3. Tool looks for: custom fields, labels (RICE:X), description text

## Extending the Tool

### Add New Prioritization Factor

The tool is designed to be extensible. To add new factors:

1. Edit `calculate_priority_score()` in `BacklogAnalyzer` class
2. Add your scoring logic (0-N points)
3. Add to score calculation

Example:
```python
# Add "Epic Link" priority
if parent_feature:
    epic_link = parent_feature['fields'].get('epic_link_field')
    if epic_link:
        score += 25  # Bonus for epic-linked work
```

### Add New What-If Parameter

Current: sprint_length

To add more (e.g., team_size):

1. Add argument in `main()` parser
2. Pass to `plan_sprints()`
3. Use in capacity calculation

### Custom Output Format

Add new method to `OutputGenerator` class:

```python
@staticmethod
def generate_csv_output(plan_data: Dict) -> str:
    # Your CSV generation logic
    pass
```

## Best Practices

1. **Run Weekly** - Keep plans fresh with latest backlog
2. **Review with Team** - Use in sprint planning meetings
3. **Compare Scenarios** - Run with different parameters
4. **Track Accuracy** - Compare plans vs actuals over time
5. **Update Risk Data** - Re-run teammate tools before planning
6. **Save Historical Plans** - Track how planning evolves
7. **Share HTML Reports** - Easy stakeholder communication

## FAQ

**Q: Can I use this for multiple teams?**
A: Yes! Run it once per team with different --component values.

**Q: Does it modify Jira?**
A: No, it's read-only. It only analyzes data, doesn't create/update issues.

**Q: What if I don't have teammate's risk tools?**
A: Tool works standalone - just omit `--risk-data-file`.

**Q: Can I plan more than 4 sprints?**
A: Yes! Use `--num-sprints 6` (or any number).

**Q: How accurate is the velocity?**
A: Based on last 3 months of closed sprints. More history = better accuracy.

**Q: What about epics?**
A: Tool looks for parent Features. Epics can be added similarly.

## Support

For issues:
1. Check Jira API permissions
2. Verify environment variables (JIRA_API_TOKEN, JIRA_URL)
3. Test JQL queries directly in Jira
4. Review error messages for specific issues
