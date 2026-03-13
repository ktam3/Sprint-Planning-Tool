# Sprint Planning Tool - Reliability Test Plan
## Friday Testing Checklist for Monday Executive Demo

### Pre-Test Setup
- [ ] Confirm JIRA_API_TOKEN is valid and has read access
- [ ] Confirm Jira URL is accessible (default: https://issues.redhat.com)
- [ ] Python 3 is installed (`python3 --version`)
- [ ] All required libraries are available (requests, json, argparse, re, datetime)

---

## Test Suite 1: Core Functionality Tests

### Test 1.1: Single Team - Training Kubeflow (YOUR WORKING EXAMPLE)
**Command:**
```bash
cd ~/Sprint-Planning-Tool
JIRA_API_TOKEN='your-jira-token-here' python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --team-name "Training Kubeflow Team" \
  --team-id 4967 \
  --sprint-pattern "Training Kubeflow Sprint" \
  --num-sprints 4
```

**Expected Results:**
- ✅ Velocity: ~48.3 story points/sprint
- ✅ Backlog: ~109 items
- ✅ Current Sprint: Training Kubeflow Sprint 27
- ✅ HTML file generated
- ✅ JSON file generated
- ✅ No Python errors or tracebacks

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________

---

### Test 1.2: Multi-Component Team - Data Processing
**Command:**
```bash
cd ~/Sprint-Planning-Tool
JIRA_API_TOKEN='your-jira-token-here' python3 sprint_planning_tool.py \
  --project "RHAIENG,RHOAIENG" \
  --component "Data Processing,Kubeflow Spark Operator" \
  --team-name "Data Processing Team" \
  --sprint-pattern "DP Sprint" \
  --num-sprints 4
```

**Expected Results:**
- ✅ Velocity calculated from DP Sprint history
- ✅ Backlog includes items from both components
- ✅ HTML file generated
- ✅ No errors

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________

---

### Test 1.3: Team Without Team ID Filter (Fallback Case)
**Command:**
```bash
cd ~/Sprint-Planning-Tool
JIRA_API_TOKEN='your-jira-token-here' python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --team-name "Training Kubeflow Team" \
  --sprint-pattern "Training Kubeflow Sprint" \
  --num-sprints 4
```

**Expected Results:**
- ✅ Should work WITHOUT team-id parameter
- ✅ May show more items (120 instead of 109) but still functional
- ✅ HTML file generated

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________

---

## Test Suite 2: Edge Cases & Error Handling

### Test 2.1: Invalid Jira Token
**Command:**
```bash
cd ~/Sprint-Planning-Tool
JIRA_API_TOKEN='INVALID_TOKEN' python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --num-sprints 4
```

**Expected Results:**
- ✅ Clear error message about invalid token
- ✅ No Python traceback that confuses users
- ✅ Exits gracefully

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________

---

### Test 2.2: Non-Existent Component
**Command:**
```bash
cd ~/Sprint-Planning-Tool
JIRA_API_TOKEN='your-jira-token-here' python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Fake Component That Does Not Exist" \
  --num-sprints 4
```

**Expected Results:**
- ✅ Should report 0 backlog items found
- ✅ Should report velocity: 0
- ✅ Should provide helpful warning message
- ✅ Should NOT crash

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________

---

### Test 2.3: Missing Required Arguments
**Command:**
```bash
cd ~/Sprint-Planning-Tool
JIRA_API_TOKEN='your-jira-token-here' python3 sprint_planning_tool.py \
  --project RHOAIENG
```

**Expected Results:**
- ✅ Clear error: "the following arguments are required: --component"
- ✅ Shows usage help

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________

---

## Test Suite 3: Output Quality Tests

### Test 3.1: HTML Output Opens in Browser
**Command:**
```bash
cd ~/Sprint-Planning-Tool
JIRA_API_TOKEN='your-jira-token-here' python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --team-id 4967 \
  --sprint-pattern "Training Kubeflow Sprint" \
  --output-html test_output.html

open test_output.html
```

**Expected Results:**
- ✅ HTML file opens in default browser
- ✅ All issue links are clickable and go to correct Jira issues
- ✅ Sprint capacity bars are visible
- ✅ Priority colors show correctly (Red: Blocker, Orange: Critical)
- ✅ Unestimated items show orange "No Story Points" badge
- ✅ Formatting is clean and professional

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________

---

### Test 3.2: JSON Output is Valid
**Command:**
```bash
cd ~/Sprint-Planning-Tool
JIRA_API_TOKEN='your-jira-token-here' python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --team-id 4967 \
  --output-json test_output.json

python3 -m json.tool test_output.json > /dev/null && echo "Valid JSON"
```

**Expected Results:**
- ✅ JSON is valid (no parsing errors)
- ✅ Contains sprint_assignments, recommendations, timeline, metadata

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________

---

## Test Suite 4: Executive Use Cases

### Test 4.1: Quick Team Health Check (Simple Command)
**Command:**
```bash
cd ~/Sprint-Planning-Tool
export JIRA_API_TOKEN='your-jira-token-here'

python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --team-id 4967 \
  --num-sprints 2
```

**Expected Results:**
- ✅ Runs in < 30 seconds
- ✅ Clear console output with capacity summary
- ✅ Auto-generated HTML file with timestamp
- ✅ Easy to understand for non-technical users

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________

---

### Test 4.2: Multi-Sprint Planning (What-If Scenario)
**Command:**
```bash
cd ~/Sprint-Planning-Tool
export JIRA_API_TOKEN='your-jira-token-here'

python3 sprint_planning_tool.py \
  --project RHOAIENG \
  --component "Training Kubeflow" \
  --team-id 4967 \
  --num-sprints 6 \
  --sprint-length 3
```

**Expected Results:**
- ✅ Plans 6 sprints instead of 4
- ✅ Uses 3-week sprint length
- ✅ Timeline adjusted accordingly
- ✅ Demonstrates "what-if" capability

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________

---

## Test Suite 5: Performance & Stability

### Test 5.1: Run Same Command 3 Times
**Command:**
```bash
cd ~/Sprint-Planning-Tool
export JIRA_API_TOKEN='your-jira-token-here'

for i in 1 2 3; do
  echo "=== Run $i ==="
  python3 sprint_planning_tool.py \
    --project RHOAIENG \
    --component "Training Kubeflow" \
    --team-id 4967 \
    --num-sprints 4
  echo ""
done
```

**Expected Results:**
- ✅ All 3 runs complete successfully
- ✅ Results are consistent (same velocity, same backlog count)
- ✅ No degradation in performance

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________

---

## Critical Issues to Fix Before Monday

### Priority 1 (Must Fix):
- [ ] Issue: _______________________________________
- [ ] Fix: _______________________________________

### Priority 2 (Should Fix):
- [ ] Issue: _______________________________________
- [ ] Fix: _______________________________________

### Priority 3 (Nice to Have):
- [ ] Issue: _______________________________________
- [ ] Fix: _______________________________________

---

## Final Sign-Off Checklist

- [ ] All "PASS" tests marked in Test Suite 1 (Core Functionality)
- [ ] All "PASS" tests marked in Test Suite 2 (Error Handling)
- [ ] HTML output looks professional and is executive-ready
- [ ] No Python tracebacks or confusing error messages
- [ ] Executive documentation created and reviewed
- [ ] Example commands tested and verified
- [ ] Token/credential instructions are clear
- [ ] Tool runs in < 30 seconds for typical use case

**Tested By:** _______________________
**Date:** _______________________
**Ready for Monday:** [ ] YES / [ ] NO

---

## Notes & Observations

