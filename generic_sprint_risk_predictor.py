#!/usr/bin/env python3
"""
Generic Sprint Risk Predictor and Mitigation Tool
Works with any Jira instance and any team configuration.

Usage:
    python3 generic_sprint_risk_predictor.py --project MYPROJECT --component "My Team"
    python3 generic_sprint_risk_predictor.py --jql "project = MYPROJECT AND assignee = currentUser()"
    python3 generic_sprint_risk_predictor.py --project MYPROJECT --team-name "Platform Team" --sprint-names "Sprint 1,Sprint 2,Sprint 3"
"""

import os
import requests
import json
import argparse
from collections import defaultdict
from datetime import datetime

JIRA_URL = os.getenv('JIRA_URL', 'https://issues.redhat.com')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

# Default statuses - can be overridden
DEFAULT_DONE_STATUSES = ['Done', 'Closed', 'Resolved']
DEFAULT_PROGRESS_STATUSES = ['In Progress', 'Review', 'Testing', 'Code Review', 'QA']
DEFAULT_TODO_STATUSES = ['New', 'Backlog', 'To Do', 'Open']

def get_jira_headers():
    """Create authenticated Jira headers"""
    if not JIRA_API_TOKEN:
        print("Error: JIRA_API_TOKEN environment variable must be set")
        print("Set it with: export JIRA_API_TOKEN='your-token'")
        exit(1)

    headers = {
        "Authorization": f"Bearer {JIRA_API_TOKEN}",
        "Content-Type": "application/json"
    }
    return headers

def build_team_jql(project=None, component=None, assignee=None, label=None, custom_jql=None):
    """Build JQL filter for team"""
    filters = []

    if custom_jql:
        return custom_jql

    if project:
        filters.append(f'project = {project}')

    if component:
        if isinstance(component, list):
            component_filter = ' OR '.join([f'component = "{c}"' for c in component])
            filters.append(f'({component_filter})')
        else:
            filters.append(f'component = "{component}"')

    if assignee:
        filters.append(f'assignee = {assignee}')

    if label:
        if isinstance(label, list):
            label_filter = ' AND '.join([f'labels = "{l}"' for l in label])
            filters.append(f'({label_filter})')
        else:
            filters.append(f'labels = "{label}"')

    if not filters:
        print("Error: Must specify at least one filter (project, component, assignee, label, or custom JQL)")
        exit(1)

    return ' AND '.join(filters)

def get_current_sprint_data(team_jql, sprint_name=None):
    """Get current sprint data for a team"""
    headers = get_jira_headers()

    if sprint_name:
        jql = f'({team_jql}) AND sprint = "{sprint_name}"'
    else:
        jql = f'({team_jql}) AND sprint in openSprints()'

    url = f"{JIRA_URL}/rest/api/2/search"
    params = {
        'jql': jql,
        'maxResults': 1000,
        'fields': 'key,summary,status,priority,assignee,created,updated,sprint,issuetype,issuelinks'
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Error fetching sprint data: {response.status_code}")
        print(f"JQL: {jql}")
        return []

    return response.json()['issues']

def get_backlog_data(team_jql):
    """Get backlog data for a team (not in any sprint)"""
    headers = get_jira_headers()

    jql = f'({team_jql}) AND sprint is EMPTY AND status != Closed AND status != Done AND status != Resolved'

    url = f"{JIRA_URL}/rest/api/2/search"
    params = {
        'jql': jql,
        'maxResults': 1000,
        'fields': 'key,summary,status,priority,assignee,created,updated,issuetype'
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Error fetching backlog data: {response.status_code}")
        return []

    return response.json()['issues']

def parse_sprint_string(sprint_str):
    """Parse Jira sprint string format to extract sprint info"""
    import re

    if not isinstance(sprint_str, str):
        return None

    sprint_info = {}

    # Extract key fields using regex
    patterns = {
        'id': r'id=(\d+)',
        'state': r'state=([A-Z]+)',
        'name': r'name=([^,\]]+)',
        'startDate': r'startDate=([^,\]]+)',
        'endDate': r'endDate=([^,\]]+)',
        'completeDate': r'completeDate=([^,\]]+)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, sprint_str)
        if match:
            sprint_info[key] = match.group(1)

    return sprint_info if sprint_info else None

def get_sprint_history(team_jql, sprint_names=None, num_sprints=4, months_back=3):
    """Get historical sprint data for velocity calculation"""
    headers = get_jira_headers()

    if sprint_names:
        sprint_filter = ' OR '.join([f'sprint = "{name}"' for name in sprint_names])
        jql = f'({team_jql}) AND ({sprint_filter})'
    else:
        # Get recent closed sprints
        jql = f'({team_jql}) AND sprint in closedSprints()'

    url = f"{JIRA_URL}/rest/api/2/search"
    params = {
        'jql': jql,
        'maxResults': 1000,
        'fields': 'key,status,sprint,customfield_12310940,created,updated,resolutiondate'
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return []

    issues = response.json()['issues']

    # Filter by date if months_back is specified
    if months_back and not sprint_names:
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=months_back * 30)

        # Filter issues based on sprint end dates from customfield_12310940
        filtered_issues = []
        for issue in issues:
            fields = issue['fields']

            # Try to get sprint info from customfield_12310940
            sprint_field = fields.get('customfield_12310940', [])
            if not isinstance(sprint_field, list):
                sprint_field = [sprint_field] if sprint_field else []

            # Check if any sprint ended within the time window
            include_issue = False
            for sprint_item in sprint_field:
                sprint_info = parse_sprint_string(sprint_item) if isinstance(sprint_item, str) else sprint_item

                if sprint_info and isinstance(sprint_info, dict):
                    # Check sprint end date or complete date
                    end_date_str = sprint_info.get('completeDate') or sprint_info.get('endDate')
                    if end_date_str:
                        try:
                            # Handle ISO format date
                            end_date = datetime.strptime(end_date_str[:10], '%Y-%m-%d')
                            if end_date >= cutoff_date:
                                include_issue = True
                                break
                        except:
                            pass

            if include_issue:
                filtered_issues.append(issue)

        return filtered_issues

    return issues

def analyze_current_sprint_risks(sprint_issues, done_statuses=None, progress_statuses=None, todo_statuses=None):
    """Analyze risks in the current sprint"""
    if done_statuses is None:
        done_statuses = DEFAULT_DONE_STATUSES
    if progress_statuses is None:
        progress_statuses = DEFAULT_PROGRESS_STATUSES
    if todo_statuses is None:
        todo_statuses = DEFAULT_TODO_STATUSES

    risks = {
        'blocked': [],
        'high_priority_not_started': [],
        'unassigned': [],
        'dependent': [],
        'in_progress_too_long': []
    }

    for issue in sprint_issues:
        fields = issue['fields']
        key = issue['key']
        status = fields['status']['name']
        priority = fields.get('priority', {}).get('name', 'Undefined')
        assignee = fields.get('assignee')

        # Check for blocked issues
        for link in fields.get('issuelinks', []):
            link_type = link.get('type', {}).get('name', '')
            if 'Blocks' in link_type or 'Depend' in link_type:
                if 'inwardIssue' in link:
                    blocker = link['inwardIssue']
                    blocker_status = blocker['fields']['status']['name']
                    if blocker_status not in done_statuses:
                        risks['blocked'].append({
                            'key': key,
                            'summary': fields['summary'],
                            'blocker': blocker['key'],
                            'blocker_status': blocker_status
                        })

        # High priority not started
        if priority in ['Blocker', 'Critical', 'Highest'] and status in todo_statuses:
            risks['high_priority_not_started'].append({
                'key': key,
                'summary': fields['summary'],
                'priority': priority
            })

        # Unassigned issues
        if not assignee:
            risks['unassigned'].append({
                'key': key,
                'summary': fields['summary'],
                'priority': priority,
                'status': status
            })

        # Issues in progress for too long (updated > 7 days ago)
        if status in progress_statuses:
            updated = datetime.strptime(fields['updated'][:10], '%Y-%m-%d')
            days_since_update = (datetime.now() - updated).days
            if days_since_update > 7:
                risks['in_progress_too_long'].append({
                    'key': key,
                    'summary': fields['summary'],
                    'days_stale': days_since_update,
                    'assignee': assignee['displayName'] if assignee else 'Unassigned'
                })

    return risks

def analyze_backlog_risks(backlog_issues, sprint_capacity):
    """Analyze risks in the backlog"""
    risks = {
        'high_priority_unplanned': [],
        'unassigned_ready': [],
        'capacity_shortage': False,
        'backlog_size': len(backlog_issues)
    }

    high_priority_count = 0
    ready_for_dev_count = 0
    ready_statuses = ['Ready for Dev', 'Ready', 'Refined', 'Ready for Development']

    for issue in backlog_issues:
        fields = issue['fields']
        priority = fields.get('priority', {}).get('name', 'Undefined')
        status = fields['status']['name']
        assignee = fields.get('assignee')

        if priority in ['Blocker', 'Critical', 'Highest']:
            high_priority_count += 1
            risks['high_priority_unplanned'].append({
                'key': issue['key'],
                'summary': fields['summary'],
                'priority': priority,
                'status': status
            })

        if status in ready_statuses and not assignee:
            ready_for_dev_count += 1
            risks['unassigned_ready'].append({
                'key': issue['key'],
                'summary': fields['summary'],
                'priority': priority
            })

    # Check if high priority backlog exceeds sprint capacity
    if high_priority_count > sprint_capacity:
        risks['capacity_shortage'] = True
        risks['high_priority_overflow'] = high_priority_count - sprint_capacity

    return risks

def calculate_velocity(sprint_history, done_statuses=None):
    """Calculate average velocity from sprint history"""
    if done_statuses is None:
        done_statuses = DEFAULT_DONE_STATUSES

    sprint_data = defaultdict(lambda: {'total': 0, 'completed': 0})

    for issue in sprint_history:
        # Try customfield_12310940 first (more reliable), then fall back to sprint field
        sprint_field = issue['fields'].get('customfield_12310940') or issue['fields'].get('sprint', [])
        if not isinstance(sprint_field, list):
            sprint_field = [sprint_field] if sprint_field else []

        status = issue['fields']['status']['name']

        for sprint_item in sprint_field:
            if sprint_item:
                # Parse sprint info from string format if needed
                sprint_info = parse_sprint_string(sprint_item) if isinstance(sprint_item, str) else sprint_item

                if isinstance(sprint_info, dict):
                    sprint_name = sprint_info.get('name', 'Unknown')
                    sprint_state = sprint_info.get('state', '')

                    # Only count closed/completed sprints for velocity
                    if sprint_state in ['CLOSED', 'closed']:
                        sprint_data[sprint_name]['total'] += 1
                        if status in done_statuses:
                            sprint_data[sprint_name]['completed'] += 1

    # Calculate average velocity
    if not sprint_data:
        return 0, 0

    avg_total = sum(s['total'] for s in sprint_data.values()) / len(sprint_data)
    avg_completed = sum(s['completed'] for s in sprint_data.values()) / len(sprint_data)

    completion_rate = (avg_completed / avg_total * 100) if avg_total > 0 else 0

    return avg_completed, completion_rate

def generate_mitigation_strategies(risks, velocity, completion_rate):
    """Generate specific mitigation strategies based on identified risks"""
    strategies = []

    # Current sprint risks
    if risks['current']['blocked']:
        count = len(risks['current']['blocked'])
        strategies.append({
            'risk': f"🚨 {count} blocked issue(s) in current sprint",
            'severity': 'CRITICAL',
            'mitigation': [
                f"Immediately unblock {count} issues by resolving blockers",
                "Daily standup focus on blocked items",
                "Assign dedicated resources to resolve blocking issues",
                "Consider scope reduction if blockers cannot be resolved quickly"
            ],
            'if_ignored': [
                f"Sprint goal failure - {count} issues will not complete",
                "Team morale impact from blocked work",
                f"Potential {count * 2} issue cascade into next sprint",
                "Loss of stakeholder confidence"
            ],
            'timeline': 'IMMEDIATE (24-48 hours)'
        })

    if risks['current']['high_priority_not_started']:
        count = len(risks['current']['high_priority_not_started'])
        strategies.append({
            'risk': f"⚠️  {count} high-priority issue(s) not started in current sprint",
            'severity': 'HIGH',
            'mitigation': [
                f"Assign {count} engineers to start high-priority work immediately",
                "Re-prioritize current work - pause lower priority items",
                "Hold emergency planning meeting to redistribute work",
                "Consider moving non-critical items out of sprint"
            ],
            'if_ignored': [
                f"High-priority work will miss sprint deadline",
                f"Estimated {int(count * 0.8)} items will roll to next sprint",
                "Commitment reliability drops, affecting team predictability",
                "Risk of missing release milestones"
            ],
            'timeline': 'URGENT (2-3 days)'
        })

    if risks['current']['unassigned']:
        count = len(risks['current']['unassigned'])
        strategies.append({
            'risk': f"⚠️  {count} unassigned issue(s) in current sprint",
            'severity': 'MEDIUM',
            'mitigation': [
                "Assign all sprint issues within 24 hours",
                "Review team capacity - may be overcommitted",
                "Consider if scope reduction is needed",
                "Pair junior engineers with seniors for quicker assignment"
            ],
            'if_ignored': [
                f"{count} issues will remain incomplete",
                "Team velocity will drop",
                "Planning accuracy will decline",
                f"Sprint completion rate may drop by {int((count/risks['current']['total_issues'])*100)}%" if risks['current']['total_issues'] > 0 else "Sprint completion rate will drop"
            ],
            'timeline': 'HIGH PRIORITY (1-2 days)'
        })

    if risks['current']['in_progress_too_long']:
        count = len(risks['current']['in_progress_too_long'])
        avg_days = sum(i['days_stale'] for i in risks['current']['in_progress_too_long']) / count
        strategies.append({
            'risk': f"⚠️  {count} issue(s) stuck in progress (avg {avg_days:.0f} days)",
            'severity': 'MEDIUM',
            'mitigation': [
                "1:1 with engineers to identify blockers",
                "Consider pairing or swarming to complete stale work",
                "Break down large issues into smaller tasks",
                "Implement WIP limits to prevent overcommitment"
            ],
            'if_ignored': [
                f"{count} issues at risk of not completing",
                "Work-in-progress bloat continues to grow",
                "Team efficiency degrades",
                f"Completion rate may drop from {completion_rate:.0f}% to {max(0, completion_rate-15):.0f}%"
            ],
            'timeline': 'MODERATE (3-5 days)'
        })

    # Backlog risks
    if risks['backlog']['high_priority_unplanned']:
        count = len(risks['backlog']['high_priority_unplanned'])
        strategies.append({
            'risk': f"🔴 {count} high-priority issue(s) in backlog (not in sprint)",
            'severity': 'HIGH',
            'mitigation': [
                "Emergency backlog refinement session",
                f"Pull top {min(3, count)} priorities into current sprint",
                "Negotiate scope reduction with stakeholders",
                "Plan dedicated sprint for high-priority backlog items"
            ],
            'if_ignored': [
                f"{count} critical items remain unplanned",
                "Risk of missing release commitments",
                "Reactive fire-fighting when priorities escalate",
                "Technical debt accumulation"
            ],
            'timeline': 'URGENT (within 1 week)'
        })

    if risks['backlog']['capacity_shortage']:
        overflow = risks['backlog'].get('high_priority_overflow', 0)
        strategies.append({
            'risk': f"📊 Capacity shortage: {overflow} more high-priority items than sprint capacity",
            'severity': 'HIGH',
            'mitigation': [
                "Prioritize ruthlessly - defer lower priority work",
                "Request additional resources or contractors",
                "Negotiate timeline extensions with stakeholders",
                "Implement strict WIP limits to improve throughput"
            ],
            'if_ignored': [
                "Chronic overcommitment and underdelivery",
                f"Team velocity drops by estimated {int((overflow/velocity)*100)}%" if velocity > 0 else "Team velocity will drop significantly",
                "Burnout risk increases significantly",
                "Stakeholder trust erodes over multiple sprints"
            ],
            'timeline': 'STRATEGIC (1-2 sprints)'
        })

    # Velocity-based risks
    if completion_rate < 60:
        strategies.append({
            'risk': f"📉 Low completion rate: {completion_rate:.0f}% (target: 80%+)",
            'severity': 'CRITICAL',
            'mitigation': [
                "Reduce sprint commitment by 30-40%",
                "Implement daily WIP limits (2-3 items per person)",
                "Focus on completing work before starting new items",
                "Weekly backlog grooming to right-size issues"
            ],
            'if_ignored': [
                f"Completion rate continues declining to {max(0, completion_rate-20):.0f}%",
                "Chronic sprint failure becomes normalized",
                "Team loses ability to make reliable commitments",
                "Quality suffers as incomplete work accumulates"
            ],
            'timeline': 'IMMEDIATE (this sprint)'
        })

    # Sort by severity
    severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    strategies.sort(key=lambda x: severity_order[x['severity']])

    return strategies

def print_risk_analysis(team_name, risks, strategies, velocity, completion_rate):
    """Print comprehensive risk analysis and mitigation report"""
    print("=" * 120)
    print(f"SPRINT RISK ANALYSIS & MITIGATION STRATEGIES: {team_name}")
    print("=" * 120)
    print()

    # Executive Summary
    print("📊 EXECUTIVE SUMMARY")
    print("-" * 120)
    print(f"Team Velocity: {velocity:.1f} issues/sprint | Completion Rate: {completion_rate:.0f}%")
    print(f"Current Sprint Issues: {risks['current']['total_issues']}")
    print(f"Backlog Issues: {risks['backlog']['backlog_size']}")

    total_risks = 0
    for r in risks['current'].values():
        if isinstance(r, list):
            total_risks += len(r)
        elif isinstance(r, bool) and r:
            total_risks += 1
    for r in risks['backlog'].values():
        if isinstance(r, list):
            total_risks += len(r)
        elif isinstance(r, bool) and r:
            total_risks += 1

    print(f"Total Risk Items Identified: {total_risks}")
    print()

    # Risk Details
    print("=" * 120)
    print("🚨 DETAILED RISK ANALYSIS")
    print("=" * 120)
    print()

    # Current Sprint Risks
    print("CURRENT SPRINT RISKS")
    print("-" * 120)

    if risks['current']['blocked']:
        print(f"\n🚫 BLOCKED ISSUES ({len(risks['current']['blocked'])})")
        for item in risks['current']['blocked']:
            print(f"   {item['key']}: {item['summary'][:60]}")
            print(f"      Blocked by: {item['blocker']} (Status: {item['blocker_status']})")

    if risks['current']['high_priority_not_started']:
        print(f"\n⚠️  HIGH PRIORITY NOT STARTED ({len(risks['current']['high_priority_not_started'])})")
        for item in risks['current']['high_priority_not_started']:
            print(f"   {item['key']}: {item['summary'][:60]}")
            print(f"      Priority: {item['priority']}")

    if risks['current']['unassigned']:
        print(f"\n👤 UNASSIGNED ISSUES ({len(risks['current']['unassigned'])})")
        for item in risks['current']['unassigned']:
            print(f"   {item['key']}: {item['summary'][:60]}")
            print(f"      Priority: {item['priority']} | Status: {item['status']}")

    if risks['current']['in_progress_too_long']:
        print(f"\n⏰ STALE IN-PROGRESS ISSUES ({len(risks['current']['in_progress_too_long'])})")
        for item in risks['current']['in_progress_too_long']:
            print(f"   {item['key']}: {item['summary'][:60]}")
            print(f"      Stale for: {item['days_stale']} days | Assignee: {item['assignee']}")

    if not any(risks['current'].values()):
        print("\n✅ No current sprint risks identified!")

    # Backlog Risks
    print()
    print("BACKLOG RISKS")
    print("-" * 120)

    if risks['backlog']['high_priority_unplanned']:
        print(f"\n🔴 HIGH PRIORITY IN BACKLOG ({len(risks['backlog']['high_priority_unplanned'])})")
        for item in risks['backlog']['high_priority_unplanned'][:5]:  # Show top 5
            print(f"   {item['key']}: {item['summary'][:60]}")
            print(f"      Priority: {item['priority']} | Status: {item['status']}")
        if len(risks['backlog']['high_priority_unplanned']) > 5:
            print(f"   ... and {len(risks['backlog']['high_priority_unplanned']) - 5} more")

    if risks['backlog']['capacity_shortage']:
        overflow = risks['backlog'].get('high_priority_overflow', 0)
        print(f"\n📊 CAPACITY WARNING")
        print(f"   High-priority backlog items: {len(risks['backlog']['high_priority_unplanned'])}")
        print(f"   Average sprint capacity: {velocity:.1f} issues")
        print(f"   Overflow: {overflow} high-priority items beyond capacity")

    if not risks['backlog']['high_priority_unplanned'] and not risks['backlog']['capacity_shortage']:
        print("\n✅ No significant backlog risks identified!")

    # Mitigation Strategies
    print()
    print("=" * 120)
    print("💡 MITIGATION STRATEGIES & PREDICTED OUTCOMES")
    print("=" * 120)
    print()

    if strategies:
        for i, strategy in enumerate(strategies, 1):
            severity_icon = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }

            print(f"{severity_icon[strategy['severity']]} RISK #{i}: {strategy['risk']}")
            print(f"Severity: {strategy['severity']} | Timeline: {strategy['timeline']}")
            print()

            print("   ✅ MITIGATION STRATEGIES:")
            for action in strategy['mitigation']:
                print(f"      • {action}")
            print()

            print("   ❌ IF IGNORED - PREDICTED OUTCOMES:")
            for outcome in strategy['if_ignored']:
                print(f"      • {outcome}")
            print()
            print("-" * 120)
            print()
    else:
        print("✅ No mitigation strategies needed - team is performing well!")
        print()

    # Summary Recommendations
    print("=" * 120)
    print("📋 IMMEDIATE ACTION ITEMS")
    print("=" * 120)
    print()

    immediate_actions = []
    if risks['current']['blocked']:
        immediate_actions.append(f"1. CRITICAL: Unblock {len(risks['current']['blocked'])} blocked issues within 24-48 hours")
    if risks['current']['high_priority_not_started']:
        immediate_actions.append(f"2. URGENT: Assign and start {len(risks['current']['high_priority_not_started'])} high-priority issues within 2-3 days")
    if risks['current']['unassigned']:
        immediate_actions.append(f"3. HIGH: Assign all {len(risks['current']['unassigned'])} unassigned sprint issues within 24 hours")
    if completion_rate < 60:
        immediate_actions.append(f"4. CRITICAL: Reduce sprint scope by 30-40% to improve {completion_rate:.0f}% completion rate")
    if risks['backlog']['high_priority_unplanned']:
        immediate_actions.append(f"5. URGENT: Hold backlog refinement for {len(risks['backlog']['high_priority_unplanned'])} high-priority items")

    if immediate_actions:
        for action in immediate_actions:
            print(f"   {action}")
    else:
        print("   ✅ No critical immediate actions required - team is on track!")

    print()

def main():
    parser = argparse.ArgumentParser(
        description='Generic Sprint Risk Predictor - Analyze sprint and backlog risks for any Jira team',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze by project and component
  python3 generic_sprint_risk_predictor.py --project MYPROJ --component "Backend Team"

  # Analyze multiple components
  python3 generic_sprint_risk_predictor.py --project MYPROJ --component "API,Database,Auth"

  # Analyze by assignee
  python3 generic_sprint_risk_predictor.py --project MYPROJ --assignee "john.doe"

  # Use custom JQL
  python3 generic_sprint_risk_predictor.py --jql "project = MYPROJ AND team = Platform"

  # Specify sprint history for velocity
  python3 generic_sprint_risk_predictor.py --project MYPROJ --component "Team A" --sprint-names "Sprint 10,Sprint 11,Sprint 12"

  # Customize team name in report
  python3 generic_sprint_risk_predictor.py --project MYPROJ --component "Backend" --team-name "Backend Engineering"
        """
    )

    parser.add_argument('--project', help='Jira project key (e.g., MYPROJECT)')
    parser.add_argument('--component', help='Component name(s), comma-separated for multiple')
    parser.add_argument('--assignee', help='Assignee username')
    parser.add_argument('--label', help='Label name(s), comma-separated for multiple')
    parser.add_argument('--jql', help='Custom JQL query for team filter')
    parser.add_argument('--team-name', help='Team name for report (default: derived from filters)')
    parser.add_argument('--sprint-names', help='Comma-separated sprint names for velocity calculation')
    parser.add_argument('--current-sprint', help='Specific current sprint name (e.g., "Team Sprint 26")')
    parser.add_argument('--velocity-months', type=int, default=3, help='Number of months to look back for velocity calculation (default: 3)')
    parser.add_argument('--done-statuses', help='Comma-separated done statuses (default: Done,Closed,Resolved)')
    parser.add_argument('--progress-statuses', help='Comma-separated in-progress statuses (default: In Progress,Review,Testing)')
    parser.add_argument('--todo-statuses', help='Comma-separated todo statuses (default: New,Backlog,To Do)')

    args = parser.parse_args()

    # Parse custom statuses
    done_statuses = args.done_statuses.split(',') if args.done_statuses else DEFAULT_DONE_STATUSES
    progress_statuses = args.progress_statuses.split(',') if args.progress_statuses else DEFAULT_PROGRESS_STATUSES
    todo_statuses = args.todo_statuses.split(',') if args.todo_statuses else DEFAULT_TODO_STATUSES

    # Parse components and labels
    components = args.component.split(',') if args.component else None
    labels = args.label.split(',') if args.label else None
    sprint_names = args.sprint_names.split(',') if args.sprint_names else None

    # Build team JQL
    team_jql = build_team_jql(
        project=args.project,
        component=components,
        assignee=args.assignee,
        label=labels,
        custom_jql=args.jql
    )

    # Determine team name for report
    if args.team_name:
        team_name = args.team_name
    elif args.component:
        team_name = args.component
    elif args.project:
        team_name = args.project
    else:
        team_name = "Team"

    print(f"Analyzing sprint risks for: {team_name}")
    print(f"Team Filter: {team_jql}")
    if args.current_sprint:
        print(f"Current Sprint: {args.current_sprint}")
    print()

    # Get data
    sprint_issues = get_current_sprint_data(team_jql, args.current_sprint)
    backlog_issues = get_backlog_data(team_jql)

    if not sprint_issues:
        print(f"⚠️  No current sprint data found for team filter: {team_jql}")
        print("This could mean:")
        print("  - Team has no open sprints")
        print("  - JQL filter doesn't match any issues")
        print("  - Authentication issue")
        print()
        print("Analyzing backlog only...")
        print()

    # Analyze current sprint risks
    current_risks = analyze_current_sprint_risks(sprint_issues, done_statuses, progress_statuses, todo_statuses)
    current_risks['total_issues'] = len(sprint_issues)

    # Calculate velocity
    sprint_history = get_sprint_history(team_jql, sprint_names, months_back=args.velocity_months)
    velocity, completion_rate = calculate_velocity(sprint_history, done_statuses)

    # Use current sprint size as fallback if no history
    if velocity == 0 and len(sprint_issues) > 0:
        velocity = len(sprint_issues) * 0.7
        completion_rate = 70
        print(f"ℹ️  Note: Using estimated velocity based on current sprint (no historical data from last {args.velocity_months} months)")
        print()
    elif velocity > 0:
        print(f"ℹ️  Velocity calculated from sprints in the last {args.velocity_months} months")
        print()

    # Analyze backlog risks
    backlog_risks = analyze_backlog_risks(backlog_issues, velocity)

    # Combine risks
    all_risks = {
        'current': current_risks,
        'backlog': backlog_risks
    }

    # Generate mitigation strategies
    strategies = generate_mitigation_strategies(all_risks, velocity, completion_rate)

    # Print report
    print_risk_analysis(team_name, all_risks, strategies, velocity, completion_rate)

if __name__ == '__main__':
    main()
