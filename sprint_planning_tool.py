#!/usr/bin/env python3
"""
Sprint Planning Tool
Helps scrum teams plan current and future sprints based on backlog analysis,
velocity, and integration with sprint health/risk analysis tools.
"""

import os
import sys
import json
import base64
import requests
import argparse
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

# Jira Configuration
JIRA_URL = os.getenv('JIRA_URL', 'https://redhat.atlassian.net')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

# Default status mappings
DEFAULT_DONE_STATUSES = ['Done', 'Closed', 'Resolved']
DEFAULT_PROGRESS_STATUSES = ['In Progress', 'Review', 'Testing', 'Code Review', 'QA']
DEFAULT_TODO_STATUSES = ['New', 'Backlog', 'To Do', 'Open']

def build_project_filter(project: str) -> str:
    """
    Build JQL project filter supporting single or multiple projects
    Args:
        project: Single project (e.g., 'RHOAIENG') or comma-separated (e.g., 'RHAIENG,RHOAIENG')
    Returns:
        JQL filter string (e.g., 'project = RHOAIENG' or 'project IN (RHAIENG, RHOAIENG)')
    """
    projects = [p.strip() for p in project.split(',')]
    if len(projects) == 1:
        return f'project = {projects[0]}'
    else:
        return f'project IN ({", ".join(projects)})'

def build_component_filter(component: str) -> str:
    """
    Build JQL component filter supporting single or multiple components
    Args:
        component: Single component (e.g., 'Data Processing') or comma-separated (e.g., 'Data Processing,Kubeflow Spark Operator')
    Returns:
        JQL filter string (e.g., 'component = "Data Processing"' or 'component IN ("Data Processing", "Kubeflow Spark Operator")')
    """
    components = [c.strip() for c in component.split(',')]
    if len(components) == 1:
        return f'component = "{components[0]}"'
    else:
        quoted_components = [f'"{c}"' for c in components]
        return f'component IN ({", ".join(quoted_components)})'

def build_team_filter(team_id: int) -> str:
    """
    Build JQL Team filter using Team ID
    Includes items that match the team OR have no team assigned (Team is EMPTY)
    Excludes items assigned to other teams
    Args:
        team_id: Team ID from Jira Team field (e.g., 4967 for "AIP Training Kubeflow")
    Returns:
        JQL filter string (e.g., '(Team = 4967 OR Team is EMPTY)')
    """
    if team_id:
        return f'(Team = {team_id} OR Team is EMPTY)'
    return None

class JiraClient:
    """Handles all Jira API interactions"""

    def __init__(self):
        if not JIRA_API_TOKEN:
            raise ValueError("JIRA_API_TOKEN environment variable must be set")
        if not JIRA_EMAIL:
            raise ValueError("JIRA_EMAIL environment variable must be set")

        # Use Basic authentication for Atlassian Cloud
        auth_string = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()

        self.headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json"
        }
        self.url = JIRA_URL

    def search_issues(self, jql: str, fields: List[str] = None, max_results: int = 1000) -> List[Dict]:
        """Search for issues using JQL (API v3) with cursor-based pagination"""
        if fields is None:
            fields = ['key', 'summary', 'status', 'priority', 'assignee', 'created',
                     'updated', 'issuetype', 'issuelinks', 'parent', 'customfield_12319940']

        url = f"{self.url}/rest/api/3/search/jql"
        all_issues = []
        next_page_token = None
        page_size = 100  # Jira API max per request

        while len(all_issues) < max_results:
            params = {
                'jql': jql,
                'maxResults': min(page_size, max_results - len(all_issues)),
                'fields': ','.join(fields)
            }

            # Add pagination token if we have one
            if next_page_token:
                params['nextPageToken'] = next_page_token

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code != 200:
                print(f"❌ Error fetching issues from Jira (HTTP {response.status_code})")
                if response.status_code == 400:
                    print("   💡 This usually means:")
                    print("      - Invalid JIRA_API_TOKEN (check your token is correct)")
                    print("      - JQL query syntax error")
                    print(f"   Query: {jql}")
                elif response.status_code == 401:
                    print("   💡 Authentication failed - check your JIRA_API_TOKEN")
                elif response.status_code == 403:
                    print("   💡 Access denied - your token may not have permission to access this project")
                else:
                    print(f"   Query: {jql}")
                return all_issues

            data = response.json()
            issues = data.get('issues', [])
            all_issues.extend(issues)

            # Check if this is the last page
            if data.get('isLast', True):
                break

            # Get next page token
            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break

        return all_issues

    def get_issue(self, issue_key: str) -> Optional[Dict]:
        """Get a single issue by key (API v3)"""
        url = f"{self.url}/rest/api/3/issue/{issue_key}"

        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            return None

        return response.json()

class VelocityCalculator:
    """Calculates team velocity from sprint history"""

    def __init__(self, jira_client: JiraClient):
        self.jira = jira_client

    @staticmethod
    def parse_sprint_string(sprint_data) -> Optional[Dict]:
        """
        Parse Jira sprint data - handles both old string format and new JSON object format
        Args:
            sprint_data: Either a string (old format) or dict (new API v3 format)
        Returns:
            Dict with sprint info (id, state, name, startDate, endDate, completeDate)
        """
        # New API v3 format - already a dict
        if isinstance(sprint_data, dict):
            # Convert to consistent format
            return {
                'id': str(sprint_data.get('id', '')),
                'state': sprint_data.get('state', '').upper(),
                'name': sprint_data.get('name', ''),
                'startDate': sprint_data.get('startDate', ''),
                'endDate': sprint_data.get('endDate', ''),
                'completeDate': sprint_data.get('completeDate', '')
            }

        # Old format - parse string
        if not isinstance(sprint_data, str):
            return None

        sprint_info = {}
        patterns = {
            'id': r'id=(\d+)',
            'state': r'state=([A-Z]+)',
            'name': r'name=([^,\]]+)',
            'startDate': r'startDate=([^,\]]+)',
            'endDate': r'endDate=([^,\]]+)',
            'completeDate': r'completeDate=([^,\]]+)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, sprint_data)
            if match:
                sprint_info[key] = match.group(1)

        return sprint_info if sprint_info else None

    def calculate_velocity(self, project: str, component: str,
                          sprint_pattern: Optional[str] = None,
                          months_back: int = 3,
                          done_statuses: List[str] = None,
                          use_story_points: bool = True,
                          team_id: Optional[int] = None) -> Tuple[float, float, int, str]:
        """
        Calculate team velocity from sprint history
        Returns: (avg_completed_per_sprint, completion_rate_pct, num_sprints, velocity_unit)
        velocity_unit is either 'story points' or 'issues'
        """
        if done_statuses is None:
            done_statuses = DEFAULT_DONE_STATUSES

        # Build JQL for closed sprints
        project_filter = build_project_filter(project)
        component_filter = build_component_filter(component)
        team_filter = build_team_filter(team_id) if team_id else None

        jql = f'{project_filter} AND {component_filter}'
        if team_filter:
            jql += f' AND {team_filter}'
        jql += ' AND sprint in closedSprints()'

        # Story points fields (new Jira instance)
        # customfield_10028 = Story Points (primary field)
        # customfield_10016 = Story point estimate (fallback)
        # customfield_10506 = DEV Story Points (fallback)
        story_points_fields = ['customfield_10028', 'customfield_10016', 'customfield_10506']
        fields = ['key', 'status', 'customfield_10020', 'updated', 'resolutiondate'] + story_points_fields
        issues = self.jira.search_issues(jql, fields=fields)

        if not issues:
            return 0.0, 0.0, 0, 'issues'

        # Filter by date and extract sprint data
        cutoff_date = datetime.now() - timedelta(days=months_back * 30)
        sprint_data_points = defaultdict(lambda: {'total': 0, 'completed': 0})
        sprint_data_count = defaultdict(lambda: {'total': 0, 'completed': 0})
        has_story_points = False

        for issue in issues:
            fields_data = issue['fields']
            sprint_field = fields_data.get('customfield_10020', [])

            if not isinstance(sprint_field, list):
                sprint_field = [sprint_field] if sprint_field else []

            status = fields_data['status']['name']

            # Try to get story points from common fields
            story_points = None
            if use_story_points:
                for sp_field in story_points_fields:
                    sp_value = fields_data.get(sp_field)
                    if sp_value is not None:
                        try:
                            sp_float = float(sp_value)
                            if sp_float > 0:
                                story_points = sp_float
                                has_story_points = True
                                break
                        except (ValueError, TypeError):
                            continue

            # Find the MOST RECENT closed sprint that matches the pattern
            # Only count the issue in that sprint to avoid double-counting
            latest_sprint_name = None
            latest_sprint_date = None

            for sprint_item in sprint_field:
                sprint_info = self.parse_sprint_string(sprint_item)

                if isinstance(sprint_info, dict) and sprint_info.get('state') == 'CLOSED':
                    # Check if sprint matches pattern if provided
                    sprint_name = sprint_info.get('name', '')
                    if sprint_pattern and sprint_pattern not in sprint_name:
                        continue

                    # Check if within time window
                    end_date_str = sprint_info.get('completeDate') or sprint_info.get('endDate')
                    if end_date_str:
                        try:
                            end_date = datetime.strptime(end_date_str[:10], '%Y-%m-%d')
                            if end_date >= cutoff_date:
                                # Track the most recent sprint
                                if latest_sprint_date is None or end_date > latest_sprint_date:
                                    latest_sprint_date = end_date
                                    latest_sprint_name = sprint_name
                        except:
                            pass

            # Only count the issue in the most recent closed sprint
            if latest_sprint_name:
                # Track issue count
                sprint_data_count[latest_sprint_name]['total'] += 1
                if status in done_statuses:
                    sprint_data_count[latest_sprint_name]['completed'] += 1

                # Track story points if available
                if story_points is not None:
                    sprint_data_points[latest_sprint_name]['total'] += story_points
                    if status in done_statuses:
                        sprint_data_points[latest_sprint_name]['completed'] += story_points

        if not sprint_data_count:
            return 0.0, 0.0, 0, 'issues'

        # Decide whether to use story points or issue count
        velocity_unit = 'story points' if (use_story_points and has_story_points) else 'issues'
        sprint_data = sprint_data_points if (use_story_points and has_story_points) else sprint_data_count

        # Calculate averages
        num_sprints = len(sprint_data)
        avg_total = sum(s['total'] for s in sprint_data.values()) / num_sprints
        avg_completed = sum(s['completed'] for s in sprint_data.values()) / num_sprints
        completion_rate = (avg_completed / avg_total * 100) if avg_total > 0 else 0

        return avg_completed, completion_rate, num_sprints, velocity_unit

    def get_carry_over_items(self, project: str, component: str,
                             sprint_pattern: Optional[str] = None,
                             min_sprints: int = 3,
                             team_id: Optional[int] = None) -> List[Dict]:
        """
        Identify items carried over across multiple closed sprints without completion.
        Returns items that appeared in min_sprints or more closed sprints and are still not done.
        """
        project_filter = build_project_filter(project)
        component_filter = build_component_filter(component)
        team_filter = build_team_filter(team_id) if team_id else None

        jql = f'{project_filter} AND {component_filter}'
        if team_filter:
            jql += f' AND {team_filter}'
        jql += ' AND sprint in closedSprints() AND issuetype != Epic AND status NOT IN (Done, Closed, Resolved)'

        story_points_fields = ['customfield_10028', 'customfield_10016', 'customfield_10506']
        fields = ['key', 'summary', 'status', 'priority', 'assignee', 'customfield_10020'] + story_points_fields
        issues = self.jira.search_issues(jql, fields=fields, max_results=1000)

        carry_overs = []

        for issue in issues:
            fields_data = issue['fields']
            sprint_field = fields_data.get('customfield_10020', [])
            if not isinstance(sprint_field, list):
                sprint_field = [sprint_field] if sprint_field else []

            closed_sprint_names = []
            for sprint_item in sprint_field:
                sprint_info = self.parse_sprint_string(sprint_item)
                if sprint_info and sprint_info.get('state') == 'CLOSED':
                    sprint_name = sprint_info.get('name', '')
                    if sprint_pattern and sprint_pattern not in sprint_name:
                        continue
                    closed_sprint_names.append(sprint_name)

            if len(closed_sprint_names) >= min_sprints:
                story_points = 0
                for sp_field in story_points_fields:
                    sp_value = fields_data.get(sp_field)
                    if sp_value is not None:
                        try:
                            sp_float = float(sp_value)
                            if sp_float > 0:
                                story_points = sp_float
                                break
                        except (ValueError, TypeError):
                            continue

                carry_overs.append({
                    'key': issue['key'],
                    'summary': fields_data.get('summary', ''),
                    'status': fields_data['status']['name'],
                    'priority': fields_data.get('priority', {}).get('name', 'Undefined'),
                    'assignee': fields_data.get('assignee', {}).get('displayName', 'Unassigned') if fields_data.get('assignee') else 'Unassigned',
                    'sprint_count': len(closed_sprint_names),
                    'sprints': sorted(closed_sprint_names),
                    'story_points': story_points
                })

        carry_overs.sort(key=lambda x: x['sprint_count'], reverse=True)
        return carry_overs


class BacklogAnalyzer:
    """Analyzes and prioritizes backlog items"""

    def __init__(self, jira_client: JiraClient):
        self.jira = jira_client

    def get_backlog(self, project: str, component: str,
                   exclude_statuses: List[str] = None,
                   team_id: Optional[int] = None) -> List[Dict]:
        """Get all backlog items (not in any sprint)"""
        if exclude_statuses is None:
            exclude_statuses = DEFAULT_DONE_STATUSES

        status_filter = ' AND '.join([f'status != {s}' for s in exclude_statuses])
        project_filter = build_project_filter(project)
        component_filter = build_component_filter(component)
        team_filter = build_team_filter(team_id) if team_id else None

        jql = f'{project_filter} AND {component_filter}'
        if team_filter:
            jql += f' AND {team_filter}'
        jql += f' AND sprint is EMPTY AND issuetype != Epic AND {status_filter}'

        # Include story points fields for velocity calculation
        fields = ['key', 'summary', 'status', 'priority', 'assignee', 'issuetype',
                 'issuelinks', 'parent', 'created', 'updated', 'customfield_12319940',
                 'customfield_10028', 'customfield_10016', 'customfield_10506']

        return self.jira.search_issues(jql, fields=fields)

    def get_parent_feature(self, issue: Dict) -> Optional[Dict]:
        """Get parent Feature for an issue"""
        fields = issue['fields']

        # Check direct parent
        parent = fields.get('parent')
        if parent:
            parent_data = self.jira.get_issue(parent['key'])
            if parent_data and parent_data['fields']['issuetype']['name'] == 'Feature':
                return parent_data

        # Check issue links for Feature relationships
        issue_links = fields.get('issuelinks', [])
        for link in issue_links:
            # Check inward links (parent)
            if 'inwardIssue' in link:
                inward = link['inwardIssue']
                if inward['fields']['issuetype']['name'] == 'Feature':
                    return self.jira.get_issue(inward['key'])

            # Check outward links
            if 'outwardIssue' in link:
                outward = link['outwardIssue']
                link_type = link.get('type', {}).get('name', '')
                # Check if this is a parent-child relationship
                if 'parent' in link_type.lower() or 'feature' in link_type.lower():
                    if outward['fields']['issuetype']['name'] == 'Feature':
                        return self.jira.get_issue(outward['key'])

        # Check Parent Link field
        parent_link = fields.get('customfield_12313140')  # Common Parent Link field
        if parent_link:
            parent_data = self.jira.get_issue(parent_link)
            if parent_data and parent_data['fields']['issuetype']['name'] == 'Feature':
                return parent_data

        return None

    def get_blocked_by(self, issue: Dict) -> List[str]:
        """Get list of issues that block this issue"""
        blockers = []
        issue_links = issue['fields'].get('issuelinks', [])

        for link in issue_links:
            link_type = link.get('type', {}).get('name', '')

            # Check if this is a blocks/depends relationship
            if 'blocks' in link_type.lower() or 'depend' in link_type.lower():
                if 'inwardIssue' in link:
                    blockers.append(link['inwardIssue']['key'])

        return blockers

    def extract_rice_score(self, feature: Dict) -> Optional[float]:
        """Extract RICE score from Feature"""
        # RICE score might be in custom fields or labels
        fields = feature['fields']

        # Check common RICE custom fields
        rice_fields = ['customfield_12315140', 'customfield_12316140']  # Common RICE fields
        for field_id in rice_fields:
            if field_id in fields and fields[field_id]:
                try:
                    return float(fields[field_id])
                except:
                    pass

        # Check labels for RICE score pattern
        labels = fields.get('labels', [])
        for label in labels:
            if label.startswith('RICE:') or label.startswith('rice:'):
                try:
                    return float(label.split(':')[1])
                except:
                    pass

        # Check summary/description for RICE score
        summary = fields.get('summary', '')
        description = fields.get('description', '')

        rice_pattern = r'RICE[:\s]+(\d+\.?\d*)'
        for text in [summary, description]:
            if text:
                match = re.search(rice_pattern, str(text), re.IGNORECASE)
                if match:
                    try:
                        return float(match.group(1))
                    except:
                        pass

        return None

    def calculate_priority_score(self, issue: Dict, parent_feature: Optional[Dict] = None) -> tuple[float, Dict]:
        """
        Calculate priority score for an issue
        Higher score = higher priority
        Returns: (total_score, breakdown_dict)
        """
        score = 0.0
        breakdown = {
            'issue_priority': 0,
            'issue_priority_name': 'Undefined',
            'parent_priority': 0,
            'parent_priority_name': None,
            'target_date': 0,
            'target_date_info': None,
            'target_version': 0,
            'target_version_name': None,
            'rice_score': 0,
            'dependency_boost': 0,
            'blocks_count': 0
        }
        fields = issue['fields']

        # 1. Issue's own priority (0-100 points)
        priority_map = {
            'Blocker': 100,
            'Critical': 80,
            'Highest': 70,
            'High': 60,
            'Major': 50,
            'Medium': 40,
            'Normal': 30,
            'Low': 20,
            'Lowest': 10,
            'Undefined': 0
        }
        issue_priority = fields.get('priority', {}).get('name', 'Undefined')
        issue_priority_score = priority_map.get(issue_priority, 0)
        score += issue_priority_score
        breakdown['issue_priority'] = issue_priority_score
        breakdown['issue_priority_name'] = issue_priority

        # 2. Parent Feature's priority (0-100 points)
        if parent_feature:
            parent_priority = parent_feature['fields'].get('priority', {}).get('name', 'Undefined')
            parent_priority_score = priority_map.get(parent_priority, 0)
            score += parent_priority_score
            breakdown['parent_priority'] = parent_priority_score
            breakdown['parent_priority_name'] = parent_priority

        # 3. Parent Feature's target end date (0-50 points, closer = higher)
        if parent_feature:
            # Check for target end date in custom fields
            target_date_fields = ['customfield_12319940', 'duedate']
            for field_id in target_date_fields:
                target_date_str = parent_feature['fields'].get(field_id)
                if target_date_str:
                    try:
                        target_date = datetime.strptime(target_date_str[:10], '%Y-%m-%d')
                        days_until = (target_date - datetime.now()).days

                        # Score: closer dates get higher scores
                        date_score = 0
                        if days_until < 0:  # Past due
                            date_score = 50
                            breakdown['target_date_info'] = f"Past due ({abs(days_until)} days)"
                        elif days_until < 30:  # Within 30 days
                            date_score = 40
                            breakdown['target_date_info'] = f"Due in {days_until} days"
                        elif days_until < 60:  # Within 60 days
                            date_score = 30
                            breakdown['target_date_info'] = f"Due in {days_until} days"
                        elif days_until < 90:  # Within 90 days
                            date_score = 20
                            breakdown['target_date_info'] = f"Due in {days_until} days"
                        else:
                            date_score = 10
                            breakdown['target_date_info'] = f"Due in {days_until} days"

                        score += date_score
                        breakdown['target_date'] = date_score
                        break
                    except:
                        pass

        # 4. Parent Feature's target version (0-30 points)
        if parent_feature:
            # Check for version in Target Version field
            target_version = parent_feature['fields'].get('customfield_12319940')
            if target_version:
                # Check if version indicates urgency (EA, RC, etc.)
                version_str = str(target_version).lower()
                version_score = 0
                if 'ea' in version_str or 'early access' in version_str:
                    version_score = 30
                    breakdown['target_version_name'] = 'EA'
                elif 'rc' in version_str or 'release candidate' in version_str:
                    version_score = 25
                    breakdown['target_version_name'] = 'RC'
                elif 'ga' in version_str or 'general availability' in version_str:
                    version_score = 20
                    breakdown['target_version_name'] = 'GA'
                else:
                    version_score = 10
                    breakdown['target_version_name'] = str(target_version)

                score += version_score
                breakdown['target_version'] = version_score

        # 5. Parent Feature's RICE score (0-100 points, normalized)
        if parent_feature:
            rice_score = self.extract_rice_score(parent_feature)
            if rice_score is not None:
                # Normalize RICE score (assuming typical range 0-100)
                normalized_rice = min(rice_score, 100)
                score += normalized_rice
                breakdown['rice_score'] = normalized_rice

        # 6. Dependency boost (if this issue blocks others, prioritize it)
        # Check if this issue blocks other issues
        issue_links = fields.get('issuelinks', [])
        blocks_count = 0
        for link in issue_links:
            link_type = link.get('type', {}).get('name', '')
            if 'blocks' in link_type.lower():
                if 'outwardIssue' in link:
                    blocks_count += 1

        dependency_score = blocks_count * 10
        score += dependency_score
        breakdown['dependency_boost'] = dependency_score
        breakdown['blocks_count'] = blocks_count

        return score, breakdown

class SprintPlanner:
    """Plans sprint assignments based on backlog and capacity"""

    def __init__(self, jira_client: JiraClient, backlog_analyzer: BacklogAnalyzer):
        self.jira = jira_client
        self.analyzer = backlog_analyzer

    def get_current_sprint_number(self, project: str, component: str, sprint_pattern: Optional[str] = None, team_id: Optional[int] = None) -> Tuple[int, str, Optional[str], Optional[int]]:
        """
        Get the current sprint number, name, end date, and sprint length for the team
        Returns: (sprint_number, sprint_name_pattern, end_date_string, sprint_length_weeks)
        """
        # Get issues in open sprints
        project_filter = build_project_filter(project)
        component_filter = build_component_filter(component)
        team_filter = build_team_filter(team_id) if team_id else None

        jql = f'{project_filter} AND {component_filter}'
        if team_filter:
            jql += f' AND {team_filter}'
        jql += ' AND sprint in openSprints()'
        issues = self.jira.search_issues(jql, fields=['key', 'customfield_10020'], max_results=10)

        if not issues:
            return 0, sprint_pattern or "Sprint", None, None

        # Extract sprint names from issues
        for issue in issues:
            # Handle cases where issue might not have fields key
            if 'fields' not in issue:
                continue
            sprint_field = issue['fields'].get('customfield_10020', [])
            if not isinstance(sprint_field, list):
                sprint_field = [sprint_field] if sprint_field else []

            for sprint_item in sprint_field:
                if sprint_item:
                    # Parse sprint info (handles both string and dict formats)
                    sprint_info = VelocityCalculator.parse_sprint_string(sprint_item)
                    if sprint_info and sprint_info.get('state', '').upper() in ['ACTIVE', 'FUTURE']:
                        sprint_name = sprint_info.get('name', '')
                        end_date = sprint_info.get('endDate', '')
                        start_date = sprint_info.get('startDate', '')

                        # If sprint_pattern is provided, only consider sprints that match the pattern
                        if sprint_pattern and sprint_pattern not in sprint_name:
                            continue

                        # Calculate sprint length in weeks from start/end dates
                        sprint_length_weeks = None
                        if start_date and end_date:
                            try:
                                start_dt = datetime.strptime(start_date[:10], '%Y-%m-%d')
                                end_dt = datetime.strptime(end_date[:10], '%Y-%m-%d')
                                days = (end_dt - start_dt).days
                                sprint_length_weeks = round(days / 7)
                            except (ValueError, TypeError):
                                pass

                        # Extract sprint number using regex
                        import re
                        # Look for patterns like "Sprint 26", "Training Kubeflow Sprint 26", etc.
                        match = re.search(r'(\d+)$', sprint_name)
                        if match:
                            sprint_num = int(match.group(1))
                            # Extract the pattern (everything before the number)
                            pattern = sprint_name[:match.start()].strip()
                            return sprint_num, pattern, end_date, sprint_length_weeks

        # Fallback to pattern if provided
        return 0, sprint_pattern or "Sprint", None, None

    def get_existing_sprint_items(self, project: str, component: str,
                                  sprint_numbers: List[int],
                                  sprint_name_pattern: str,
                                  verbose: bool = False,
                                  team_id: Optional[int] = None) -> Dict[int, List[Dict]]:
        """
        Get items already planned in specific future sprints that match the team's naming convention
        Excludes items from old/closed sprints and cross-team sprints
        Returns: {sprint_number: [issues]}
        """
        sprint_items = defaultdict(list)
        excluded_old_sprints = set()
        excluded_cross_team = set()

        # Get items in future sprints (not closed)
        # Using openSprints() and futureSprints() to avoid issues with non-existent sprint names
        project_filter = build_project_filter(project)
        component_filter = build_component_filter(component)
        team_filter = build_team_filter(team_id) if team_id else None

        jql = f'{project_filter} AND {component_filter}'
        if team_filter:
            jql += f' AND {team_filter}'
        jql += ' AND issuetype != Epic AND (sprint in futureSprints() OR sprint in openSprints())'

        fields = ['key', 'summary', 'status', 'priority', 'assignee', 'customfield_10020']
        issues = self.jira.search_issues(jql, fields=fields, max_results=1000)

        if not issues:
            return {}

        for issue in issues:
            fields_data = issue['fields']
            sprint_field = fields_data.get('customfield_10020', [])
            if not isinstance(sprint_field, list):
                sprint_field = [sprint_field] if sprint_field else []

            # Find which sprint(s) this issue belongs to
            # We'll only consider the LATEST non-closed sprint that matches the team's pattern
            latest_matching_sprint = None
            latest_sprint_num = -1

            for sprint_item in sprint_field:
                if sprint_item:
                    sprint_info = VelocityCalculator.parse_sprint_string(sprint_item)
                    if sprint_info:
                        sprint_name = sprint_info.get('name', '')
                        sprint_state = sprint_info.get('state', '')

                        # ONLY consider ACTIVE or FUTURE sprints (exclude CLOSED)
                        if sprint_state.upper() not in ['ACTIVE', 'FUTURE']:
                            excluded_old_sprints.add(sprint_name)
                            continue

                        # ONLY consider sprints that match the team's naming pattern
                        if sprint_name_pattern and sprint_name_pattern not in sprint_name:
                            excluded_cross_team.add(sprint_name)
                            continue

                        # Extract sprint number
                        import re
                        match = re.search(r'(\d+)$', sprint_name)
                        if match:
                            sprint_num = int(match.group(1))
                            if sprint_num in sprint_numbers and sprint_num > latest_sprint_num:
                                latest_sprint_num = sprint_num
                                latest_matching_sprint = {
                                    'key': issue['key'],
                                    'summary': fields_data['summary'],
                                    'status': fields_data['status']['name'],
                                    'priority': fields_data.get('priority', {}).get('name', 'Undefined'),
                                    'assignee': fields_data.get('assignee', {}).get('displayName', 'Unassigned') if fields_data.get('assignee') else 'Unassigned',
                                    'already_planned': True
                                }

            # Add the latest matching sprint only
            if latest_matching_sprint and latest_sprint_num > 0:
                sprint_items[latest_sprint_num].append(latest_matching_sprint)

        # Print diagnostic info if verbose
        if verbose and (excluded_old_sprints or excluded_cross_team):
            print("   ℹ️  Excluded from planning:")
            if excluded_old_sprints:
                print(f"      - Old/closed sprints: {', '.join(sorted(excluded_old_sprints))}")
            if excluded_cross_team:
                print(f"      - Cross-team sprints: {', '.join(sorted(excluded_cross_team))}")

        return dict(sprint_items)

    def plan_sprints(self,
                     backlog: List[Dict],
                     velocity: float,
                     num_sprints: int = 4,
                     sprint_length_weeks: int = 2,
                     current_sprint_capacity_used: float = 0.0,
                     risk_data: Optional[Dict] = None,
                     current_sprint_num: int = 0,
                     sprint_name_pattern: str = "Sprint",
                     project: str = "",
                     component: str = "",
                     velocity_unit: str = "issues",
                     current_sprint_end_date: Optional[str] = None,
                     team_id: Optional[int] = None,
                     min_carry_over_sprints: int = 3) -> Dict:
        """
        Plan sprint assignments for backlog items

        Args:
            backlog: List of backlog issues
            velocity: Team's average velocity (story points or issues per sprint)
            num_sprints: Number of future sprints to plan
            sprint_length_weeks: Length of each sprint in weeks
            current_sprint_capacity_used: How much of current sprint is already used (0-1)
            risk_data: Optional risk data from sprint health tools
            project: Jira project key
            component: Team component name
            velocity_unit: Unit of velocity measurement ('story points' or 'issues')
            min_carry_over_sprints: Minimum closed sprints to flag as carry-over (default: 3)

        Returns:
            Dictionary with sprint plans and recommendations
        """

        # Calculate available capacity
        current_sprint_remaining = velocity * (1 - current_sprint_capacity_used)

        # Prioritize backlog
        prioritized_backlog = self._prioritize_backlog(backlog)

        # Determine starting sprint number
        start_sprint_num = current_sprint_num + 1 if current_sprint_num > 0 else 1

        # Get existing items already planned in future sprints
        existing_sprint_items = {}
        if project and component and start_sprint_num > 0:
            sprint_numbers = list(range(start_sprint_num, start_sprint_num + num_sprints))
            existing_sprint_items = self.get_existing_sprint_items(
                project,
                component,
                sprint_numbers,
                sprint_name_pattern,
                verbose=True,
                team_id=team_id
            )

        # Assign to sprints
        sprint_assignments = self._assign_to_sprints(
            prioritized_backlog,
            velocity,
            num_sprints,
            current_sprint_remaining,
            sprint_length_weeks,
            start_sprint_num,
            sprint_name_pattern,
            existing_sprint_items,
            velocity_unit
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            sprint_assignments,
            velocity,
            risk_data
        )

        # Generate timeline forecast
        timeline = self._generate_timeline(sprint_assignments, sprint_length_weeks, current_sprint_end_date)

        # Detect carry-over items
        carry_overs = []
        if project and component:
            velocity_calculator = VelocityCalculator(self.jira)
            carry_overs = velocity_calculator.get_carry_over_items(
                project, component,
                sprint_pattern=sprint_name_pattern,
                min_sprints=min_carry_over_sprints,
                team_id=team_id
            )

            # Add carry-over recommendations
            if carry_overs:
                severe_threshold = max(min_carry_over_sprints + 2, 5)
                severe = [c for c in carry_overs if c['sprint_count'] >= severe_threshold]
                moderate = [c for c in carry_overs if min_carry_over_sprints <= c['sprint_count'] < severe_threshold]

                if severe:
                    recommendations.append({
                        'type': 'WARNING',
                        'severity': 'HIGH',
                        'sprint': 'Backlog Health',
                        'message': f"{len(severe)} item(s) carried over 5+ sprints: {', '.join(c['key'] for c in severe[:5])}",
                        'action': "These items need attention - consider splitting, descoping, or escalating blockers"
                    })
                if moderate:
                    recommendations.append({
                        'type': 'WARNING',
                        'severity': 'MEDIUM',
                        'sprint': 'Backlog Health',
                        'message': f"{len(moderate)} item(s) carried over 3-4 sprints",
                        'action': "Review why these items keep slipping - they may need re-estimation or dependency resolution"
                    })

        return {
            'sprint_assignments': sprint_assignments,
            'recommendations': recommendations,
            'carry_overs': carry_overs,
            'timeline': timeline,
            'metadata': {
                'velocity': velocity,
                'velocity_unit': velocity_unit,
                'num_sprints_planned': num_sprints,
                'sprint_length_weeks': sprint_length_weeks,
                'total_backlog_items': len(backlog),
                'items_planned': sum(len(s['items']) for s in sprint_assignments.values()),
                'carry_over_count': len(carry_overs)
            }
        }

    def _prioritize_backlog(self, backlog: List[Dict]) -> List[Dict]:
        """Prioritize backlog items with scores and parent info"""
        prioritized = []

        for issue in backlog:
            # Get parent feature
            parent_feature = self.analyzer.get_parent_feature(issue)

            # Calculate priority score
            priority_score, score_breakdown = self.analyzer.calculate_priority_score(issue, parent_feature)

            # Get blockers
            blocked_by = self.analyzer.get_blocked_by(issue)

            prioritized.append({
                'issue': issue,
                'priority_score': priority_score,
                'score_breakdown': score_breakdown,
                'parent_feature': parent_feature,
                'blocked_by': blocked_by
            })

        # Sort by priority score (descending)
        prioritized.sort(key=lambda x: x['priority_score'], reverse=True)

        return prioritized

    def _assign_to_sprints(self,
                          prioritized_backlog: List[Dict],
                          velocity: float,
                          num_sprints: int,
                          current_sprint_remaining: float,
                          sprint_length_weeks: int,
                          start_sprint_num: int = 1,
                          sprint_name_pattern: str = "Sprint",
                          existing_sprint_items: Dict[int, List[Dict]] = None,
                          velocity_unit: str = "issues") -> Dict:
        """Assign issues to sprints based on priority and capacity"""

        if existing_sprint_items is None:
            existing_sprint_items = {}

        # Story points fields to check (new Jira instance)
        story_points_fields = ['customfield_10028', 'customfield_10016', 'customfield_10506']

        def get_story_points(issue_dict):
            """Extract story points from issue, return 0 if not found"""
            if velocity_unit != 'story points':
                return 1  # Count as 1 issue if not using story points

            # Check if this is a full issue dict with 'fields' or just metadata
            fields = issue_dict.get('fields', issue_dict)

            for sp_field in story_points_fields:
                sp_value = fields.get(sp_field)
                if sp_value is not None:
                    try:
                        sp_float = float(sp_value)
                        if sp_float > 0:
                            return sp_float
                    except (ValueError, TypeError):
                        continue
            # No story points found - return 0 (will be flagged in HTML)
            return 0

        sprint_assignments = {}

        # Initialize sprints
        for i in range(num_sprints):
            sprint_num = start_sprint_num + i
            capacity = current_sprint_remaining if i == 0 else velocity

            sprint_name = f"{sprint_name_pattern} {sprint_num}".strip()

            # Get existing items for this sprint
            existing_items = existing_sprint_items.get(sprint_num, [])

            # Calculate capacity used by existing items
            existing_capacity = 0
            for existing_item in existing_items:
                # Fetch full issue to get story points
                full_issue = self.jira.get_issue(existing_item['key'])
                if full_issue:
                    sp = get_story_points(full_issue)
                    existing_item['story_points'] = sp
                    existing_capacity += sp
                else:
                    # Fallback to 1 if we can't fetch the issue
                    existing_item['story_points'] = 1 if velocity_unit == 'issues' else 0
                    existing_capacity += existing_item['story_points']

            sprint_assignments[sprint_name] = {
                'capacity': capacity,
                'items': existing_items.copy(),  # Start with existing items
                'capacity_used': existing_capacity,  # Already used capacity (in story points or issues)
                'warnings': [],
                'sprint_number': sprint_num,
                'existing_items_count': len(existing_items),
                'recommended_items_count': 0
            }

        # Track which issues are assigned (including existing ones)
        assigned_keys = set()
        for sprint_data in sprint_assignments.values():
            for existing_item in sprint_data['items']:
                assigned_keys.add(existing_item['key'])

        blocked_items = []  # Items we can't assign yet due to dependencies

        # First pass: assign items respecting dependencies
        for item in prioritized_backlog:
            issue = item['issue']
            issue_key = issue['key']

            # Skip if already in a future sprint
            if issue_key in assigned_keys:
                continue

            blocked_by = item['blocked_by']

            # Check if blockers are assigned or resolved
            unresolved_blockers = []
            for blocker_key in blocked_by:
                if blocker_key not in assigned_keys:
                    # Check if blocker is in a different project or already resolved
                    blocker_issue = self.jira.get_issue(blocker_key)
                    if blocker_issue:
                        blocker_status = blocker_issue['fields']['status']['name']
                        if blocker_status not in ['Done', 'Closed', 'Resolved']:
                            unresolved_blockers.append(blocker_key)
                    else:
                        # Can't fetch blocker, assume it's unresolved
                        unresolved_blockers.append(blocker_key)

            if unresolved_blockers:
                # Store with updated blocker list
                item['blocked_by'] = unresolved_blockers
                blocked_items.append(item)
                continue

            # Find first sprint with capacity
            assigned = False
            item_size = get_story_points(issue)

            for sprint_name, sprint_data in sprint_assignments.items():
                # Items with 0 points don't consume capacity but can still be added
                will_fit = (item_size == 0) or (sprint_data['capacity_used'] + item_size <= sprint_data['capacity'])

                if will_fit:
                    sprint_data['items'].append({
                        'key': issue_key,
                        'summary': issue['fields']['summary'],
                        'priority': issue['fields'].get('priority', {}).get('name', 'Undefined'),
                        'priority_score': item['priority_score'],
                        'score_breakdown': item.get('score_breakdown', {}),
                        'parent_feature': item['parent_feature']['key'] if item['parent_feature'] else None,
                        'blocked_by': blocked_by,
                        'status': issue['fields']['status']['name'],
                        'story_points': item_size,
                        'already_planned': False  # This is a new recommendation
                    })
                    # Only consume capacity if item has story points
                    if item_size > 0:
                        sprint_data['capacity_used'] += item_size
                    sprint_data['recommended_items_count'] += 1
                    assigned_keys.add(issue_key)
                    assigned = True
                    break

            if not assigned:
                # No capacity in any sprint
                break

        # Second pass: try to assign blocked items if their blockers are now assigned
        for item in blocked_items:
            issue = item['issue']
            issue_key = issue['key']
            blocked_by = item['blocked_by']

            # Check if blockers are now assigned
            if all(b in assigned_keys for b in blocked_by):
                # Find first sprint with capacity after the blocker sprints
                min_sprint_num = 0
                for blocker_key in blocked_by:
                    for sprint_name, sprint_data in sprint_assignments.items():
                        if any(i['key'] == blocker_key for i in sprint_data['items']):
                            min_sprint_num = max(min_sprint_num, sprint_data['sprint_number'])

                # Assign to next sprint with capacity
                assigned = False
                item_size = get_story_points(issue)

                for sprint_name, sprint_data in sprint_assignments.items():
                    # Items with 0 points don't consume capacity but can still be added
                    will_fit = (item_size == 0) or (sprint_data['capacity_used'] + item_size <= sprint_data['capacity'])

                    if sprint_data['sprint_number'] > min_sprint_num and will_fit:
                        sprint_data['items'].append({
                            'key': issue_key,
                            'summary': issue['fields']['summary'],
                            'priority': issue['fields'].get('priority', {}).get('name', 'Undefined'),
                            'priority_score': item['priority_score'],
                            'score_breakdown': item.get('score_breakdown', {}),
                            'parent_feature': item['parent_feature']['key'] if item['parent_feature'] else None,
                            'blocked_by': blocked_by,
                            'status': issue['fields']['status']['name'],
                            'story_points': item_size,
                            'already_planned': False  # This is a new recommendation
                        })
                        # Only consume capacity if item has story points
                        if item_size > 0:
                            sprint_data['capacity_used'] += item_size
                        sprint_data['recommended_items_count'] += 1
                        assigned_keys.add(issue_key)
                        assigned = True
                        break

        # Check for overcommitment
        for sprint_name, sprint_data in sprint_assignments.items():
            if sprint_data['capacity_used'] > sprint_data['capacity']:
                sprint_data['warnings'].append(
                    f"Overcommitted by {sprint_data['capacity_used'] - sprint_data['capacity']:.1f} {velocity_unit}"
                )

        return sprint_assignments

    def _generate_recommendations(self,
                                 sprint_assignments: Dict,
                                 velocity: float,
                                 risk_data: Optional[Dict]) -> List[Dict]:
        """Generate planning recommendations"""
        recommendations = []

        # Check for overcommitment
        for sprint_name, sprint_data in sprint_assignments.items():
            if sprint_data['capacity_used'] > sprint_data['capacity']:
                recommendations.append({
                    'type': 'WARNING',
                    'severity': 'HIGH',
                    'sprint': sprint_name,
                    'message': f"{sprint_name} is overcommitted by {sprint_data['capacity_used'] - sprint_data['capacity']:.1f} issues",
                    'action': f"Consider moving {int(sprint_data['capacity_used'] - sprint_data['capacity']) + 1} lower priority items to next sprint"
                })

        # Check for high-priority items not planned
        sprint_1_items = sprint_assignments.get('Sprint 1', {}).get('items', [])
        high_priority_in_sprint_1 = sum(1 for item in sprint_1_items
                                        if item['priority'] in ['Blocker', 'Critical'])

        if high_priority_in_sprint_1 > velocity * 0.8:
            recommendations.append({
                'type': 'WARNING',
                'severity': 'MEDIUM',
                'sprint': 'Sprint 1',
                'message': f"Sprint 1 has {high_priority_in_sprint_1} high-priority items (>80% of capacity)",
                'action': "Consider balancing high and medium priority work to reduce risk"
            })

        # Integration with risk data
        if risk_data:
            blocked_issues = risk_data.get('blocked_issues', [])
            if blocked_issues:
                recommendations.append({
                    'type': 'RISK',
                    'severity': 'CRITICAL',
                    'sprint': 'Current',
                    'message': f"Current sprint has {len(blocked_issues)} blocked issues",
                    'action': "Resolve blockers before planning new work into Sprint 1"
                })

        # Capacity utilization
        for sprint_name, sprint_data in sprint_assignments.items():
            if sprint_data['capacity'] > 0:
                utilization = sprint_data['capacity_used'] / sprint_data['capacity'] * 100
                if utilization < 50:
                    recommendations.append({
                        'type': 'INFO',
                        'severity': 'LOW',
                        'sprint': sprint_name,
                        'message': f"{sprint_name} is only {utilization:.0f}% utilized",
                        'action': "Consider pulling additional items from backlog"
                    })

        return recommendations

    def _generate_timeline(self, sprint_assignments: Dict, sprint_length_weeks: int, current_sprint_end_date: Optional[str] = None) -> Dict:
        """Generate timeline forecast"""
        timeline = {
            'sprints': [],
            'milestones': []
        }

        # Use the current sprint's end date as the starting point for the next sprint
        if current_sprint_end_date:
            try:
                # Parse the end date from Jira format (e.g., "2026-03-26T00:00:00.000Z")
                next_sprint_start = datetime.strptime(current_sprint_end_date[:10], '%Y-%m-%d')
            except:
                # Fallback to today if parsing fails
                next_sprint_start = datetime.now()
        else:
            # Fallback to today if no current sprint end date
            next_sprint_start = datetime.now()

        # Sort by sprint number
        sorted_sprints = sorted(sprint_assignments.items(), key=lambda x: x[1]['sprint_number'])

        for i, (sprint_name, sprint_data) in enumerate(sorted_sprints):
            start_date = next_sprint_start + timedelta(weeks=i * sprint_length_weeks)
            end_date = start_date + timedelta(weeks=sprint_length_weeks)

            timeline['sprints'].append({
                'name': sprint_name,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'num_items': len(sprint_data['items']),
                'capacity_used': sprint_data['capacity_used'],
                'capacity': sprint_data['capacity']
            })

            # Check for milestone items (Blocker priority)
            blocker_items = [item for item in sprint_data['items'] if item['priority'] == 'Blocker']
            if blocker_items:
                timeline['milestones'].append({
                    'sprint': sprint_name,
                    'date': end_date.strftime('%Y-%m-%d'),
                    'description': f"{len(blocker_items)} Blocker item(s) expected to complete",
                    'items': [item['key'] for item in blocker_items]
                })

        return timeline

class OutputGenerator:
    """Generates output in multiple formats"""

    @staticmethod
    def generate_python_output(plan_data: Dict) -> Dict:
        """Generate Python object output"""
        return plan_data

    @staticmethod
    def generate_html_output(plan_data: Dict, team_name: str, jira_url: str = "https://issues.redhat.com") -> str:
        """Generate HTML dashboard output"""

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Sprint Planning - {team_name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        .metadata {{
            background-color: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .metadata-item {{
            display: inline-block;
            margin-right: 30px;
            font-weight: bold;
        }}
        .sprint-card {{
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
            background-color: #fafafa;
        }}
        .sprint-header {{
            font-size: 18px;
            font-weight: bold;
            color: #2196F3;
            margin-bottom: 10px;
        }}
        .capacity-bar {{
            width: 100%;
            height: 25px;
            background-color: #e0e0e0;
            border-radius: 3px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .capacity-fill {{
            height: 100%;
            background-color: #4CAF50;
            text-align: center;
            line-height: 25px;
            color: white;
            font-weight: bold;
        }}
        .capacity-overfill {{
            background-color: #f44336;
        }}
        .issue-list {{
            margin-top: 10px;
        }}
        .issue-item {{
            padding: 8px;
            margin: 5px 0;
            background-color: white;
            border-left: 4px solid #2196F3;
            border-radius: 3px;
        }}
        .issue-item a {{
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .issue-item a:hover {{
            text-decoration: underline !important;
            color: #1976D2 !important;
        }}
        .issue-blocker {{
            border-left-color: #f44336;
        }}
        .issue-critical {{
            border-left-color: #ff9800;
        }}
        .issue-existing {{
            background-color: #e8f4f8;
            border-left: 4px solid #607d8b;
        }}
        .issue-recommended {{
            background-color: #f1f8e9;
            border-left: 4px solid #4CAF50;
        }}
        .no-story-points {{
            background-color: #fff9e6 !important;
            border-left: 4px solid #ff9800 !important;
        }}
        .missing-points {{
            color: #ff9800;
            font-weight: bold;
            background-color: #fff3cd;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        .has-points {{
            color: #4CAF50;
            font-weight: bold;
            background-color: #e8f5e9;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        .section-header {{
            font-weight: bold;
            color: #555;
            margin-top: 10px;
            margin-bottom: 5px;
        }}
        .recommendation {{
            padding: 12px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 5px solid;
        }}
        .rec-warning {{
            background-color: #fff3cd;
            border-left-color: #ff9800;
        }}
        .rec-risk {{
            background-color: #f8d7da;
            border-left-color: #f44336;
        }}
        .rec-info {{
            background-color: #d1ecf1;
            border-left-color: #2196F3;
        }}
        .timeline {{
            margin-top: 20px;
        }}
        .timeline-item {{
            padding: 10px;
            margin: 5px 0;
            background-color: #e3f2fd;
            border-radius: 3px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        .warning {{
            color: #f44336;
            font-weight: bold;
        }}
        details {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
        }}
        summary {{
            font-size: 1.1em;
            font-weight: bold;
            color: #2196F3;
            cursor: pointer;
            padding: 5px;
            user-select: none;
        }}
        summary:hover {{
            color: #1976D2;
        }}
        .scoring-table {{
            margin: 15px 0;
            width: 100%;
        }}
        .scoring-table th {{
            background-color: #2196F3;
            color: white;
        }}
        .scoring-example {{
            background-color: #e3f2fd;
            padding: 10px;
            margin: 10px 0;
            border-left: 4px solid #2196F3;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Sprint Planning - {team_name}</h1>

        <details>
            <summary>ℹ️ How Priority Scoring Works</summary>
            <div style="margin-top: 15px;">
                <p>The tool automatically calculates a <strong>priority score</strong> (0-500+ points) for each backlog item to determine which items should be planned into earlier sprints. Items with <strong>higher scores</strong> are prioritized first.</p>

                <h3 style="color: #2196F3; margin-top: 20px;">Scoring Components</h3>
                <table class="scoring-table">
                    <thead>
                        <tr>
                            <th>Factor</th>
                            <th>Max Points</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>1. Issue's Priority</strong></td>
                            <td>100</td>
                            <td>Blocker=100, Critical=80, High=60, Major=50, Normal=30, Low=20</td>
                        </tr>
                        <tr>
                            <td><strong>2. Parent Feature Priority</strong></td>
                            <td>100</td>
                            <td>Same scale as issue priority, uses the Feature this issue belongs to</td>
                        </tr>
                        <tr>
                            <td><strong>3. Target End Date</strong></td>
                            <td>50</td>
                            <td>Past due=50, &lt;30 days=40, &lt;60 days=30, &lt;90 days=20, &gt;90 days=10</td>
                        </tr>
                        <tr>
                            <td><strong>4. Target Version</strong></td>
                            <td>30</td>
                            <td>EA (Early Access)=30, RC (Release Candidate)=25, GA=20, Other=10</td>
                        </tr>
                        <tr>
                            <td><strong>5. RICE Score</strong></td>
                            <td>100</td>
                            <td>Product priority score from parent Feature (if available)</td>
                        </tr>
                        <tr>
                            <td><strong>6. Dependency Boost</strong></td>
                            <td>+10 per blocked issue</td>
                            <td>If this issue blocks other issues, prioritize it higher</td>
                        </tr>
                    </tbody>
                </table>

                <h3 style="color: #2196F3; margin-top: 20px;">Example Calculations</h3>

                <div class="scoring-example">
                    <strong>High Priority Item (Score: 270)</strong>
                    <ul>
                        <li>Issue Priority: Blocker = 100 points</li>
                        <li>Parent Feature Priority: Critical = 80 points</li>
                        <li>Target End Date: Within 30 days = 40 points</li>
                        <li>Target Version: EA = 30 points</li>
                        <li>RICE Score: 20 points</li>
                        <li><strong>Total: 270 points</strong> → Planned in earliest sprint</li>
                    </ul>
                </div>

                <div class="scoring-example">
                    <strong>Medium Priority Item (Score: 130)</strong>
                    <ul>
                        <li>Issue Priority: Major = 50 points</li>
                        <li>Parent Feature Priority: High = 60 points</li>
                        <li>Target End Date: Within 90 days = 20 points</li>
                        <li><strong>Total: 130 points</strong> → Planned in middle sprint</li>
                    </ul>
                </div>

                <div class="scoring-example">
                    <strong>Lower Priority Item (Score: 60)</strong>
                    <ul>
                        <li>Issue Priority: Normal = 30 points</li>
                        <li>Parent Feature Priority: Normal = 30 points</li>
                        <li><strong>Total: 60 points</strong> → Planned in later sprint</li>
                    </ul>
                </div>

                <h3 style="color: #2196F3; margin-top: 20px;">Score Ranges</h3>
                <ul>
                    <li><strong>200+</strong>: Urgent items with tight deadlines or Blocker/Critical priority</li>
                    <li><strong>100-200</strong>: Important items with moderate urgency</li>
                    <li><strong>&lt;100</strong>: Lower priority or items lacking parent Feature context</li>
                </ul>

                <p style="margin-top: 15px;"><em>💡 Tip: Each recommended item shows its score breakdown so you can see exactly how it was calculated.</em></p>
            </div>
        </details>

        <div class="metadata">
"""

        metadata = plan_data['metadata']
        html += f"""
            <span class="metadata-item">📊 Team Velocity: {metadata['velocity']:.1f} {metadata.get('velocity_unit', 'issues')}/sprint</span>
            <span class="metadata-item">📅 Sprints Planned: {metadata['num_sprints_planned']}</span>
            <span class="metadata-item">📋 Total Backlog: {metadata['total_backlog_items']}</span>
            <span class="metadata-item">✅ Items Planned: {metadata['items_planned']}</span>
        </div>
"""

        # Sprint Assignments
        html += "<h2>📅 Sprint Assignments</h2>"

        for sprint_name, sprint_data in sorted(plan_data['sprint_assignments'].items()):
            if sprint_data['capacity'] > 0:
                capacity_pct = (sprint_data['capacity_used'] / sprint_data['capacity'] * 100)
            else:
                capacity_pct = 0
            capacity_class = 'capacity-overfill' if capacity_pct > 100 else ''

            velocity_unit = plan_data['metadata'].get('velocity_unit', 'issues')
            html += f"""
        <div class="sprint-card">
            <div class="sprint-header">{sprint_name}</div>
            <div>Capacity: {sprint_data['capacity_used']:.1f} / {sprint_data['capacity']:.1f} {velocity_unit} ({capacity_pct:.0f}%)</div>
            <div class="capacity-bar">
                <div class="capacity-fill {capacity_class}" style="width: {min(capacity_pct, 100):.0f}%">
                    {capacity_pct:.0f}%
                </div>
            </div>
"""

            if sprint_data['warnings']:
                for warning in sprint_data['warnings']:
                    html += f'<div class="warning">⚠️ {warning}</div>'

            if sprint_data['items']:
                # Separate existing and recommended items
                existing_items = [item for item in sprint_data['items'] if item.get('already_planned', False)]
                recommended_items = [item for item in sprint_data['items'] if not item.get('already_planned', False)]

                html += '<div class="issue-list">'

                # Show existing items first
                if existing_items:
                    html += '<div class="section-header">📌 Already Planned ({}):</div>'.format(len(existing_items))
                    for item in existing_items:
                        priority_class = 'issue-existing'
                        jira_link = f"{jira_url}/browse/{item['key']}"

                        # Check if story points are missing
                        story_points = item.get('story_points', 0)
                        if story_points == 0 or story_points is None:
                            priority_class += ' no-story-points'
                            sp_display = '<span class="missing-points">⚠️ No story points</span>'
                        else:
                            sp_display = f'<span class="has-points">{story_points:.1f} SP</span>'

                        html += f"""
                <div class="issue-item {priority_class}">
                    <strong><a href="{jira_link}" target="_blank" style="color: inherit; text-decoration: none;">{item['key']}</a></strong>: {item['summary'][:80]}{'...' if len(item['summary']) > 80 else ''}
                    <br><small>Priority: {item['priority']} | Status: {item['status']} | {sp_display}</small>
"""
                        html += "</div>"

                # Show recommended items
                if recommended_items:
                    html += '<div class="section-header">✨ Recommended ({}):</div>'.format(len(recommended_items))
                    for item in recommended_items:
                        priority_class = 'issue-recommended'
                        if item['priority'] == 'Blocker':
                            priority_class += ' issue-blocker'
                        elif item['priority'] == 'Critical':
                            priority_class += ' issue-critical'

                        jira_link = f"{jira_url}/browse/{item['key']}"

                        # Check if story points are missing
                        story_points = item.get('story_points', 0)
                        if story_points == 0 or story_points is None:
                            priority_class += ' no-story-points'
                            sp_display = '<span class="missing-points">⚠️ No story points</span>'
                        else:
                            sp_display = f'<span class="has-points">{story_points:.1f} SP</span>'

                        html += f"""
                <div class="issue-item {priority_class}">
                    <strong><a href="{jira_link}" target="_blank" style="color: inherit; text-decoration: none;">{item['key']}</a></strong>: {item['summary'][:80]}{'...' if len(item['summary']) > 80 else ''}
                    <br><small>Priority: {item['priority']} | Total Score: {item.get('priority_score', 0):.0f} | {sp_display}</small>
"""
                        # Add score breakdown
                        breakdown = item.get('score_breakdown', {})
                        if breakdown:
                            breakdown_parts = []
                            if breakdown.get('issue_priority', 0) > 0:
                                breakdown_parts.append(f"Issue Priority ({breakdown['issue_priority_name']}): {breakdown['issue_priority']:.0f}")
                            if breakdown.get('parent_priority', 0) > 0:
                                breakdown_parts.append(f"Feature Priority ({breakdown['parent_priority_name']}): {breakdown['parent_priority']:.0f}")
                            if breakdown.get('target_date', 0) > 0:
                                breakdown_parts.append(f"Target Date ({breakdown['target_date_info']}): {breakdown['target_date']:.0f}")
                            if breakdown.get('target_version', 0) > 0:
                                breakdown_parts.append(f"Target Version ({breakdown['target_version_name']}): {breakdown['target_version']:.0f}")
                            if breakdown.get('rice_score', 0) > 0:
                                breakdown_parts.append(f"RICE Score: {breakdown['rice_score']:.0f}")
                            if breakdown.get('dependency_boost', 0) > 0:
                                breakdown_parts.append(f"Blocks {breakdown['blocks_count']} issue(s): {breakdown['dependency_boost']:.0f}")

                            if breakdown_parts:
                                html += f"<br><small style='color: #666;'>Score breakdown: {' + '.join(breakdown_parts)}</small>"

                        if item.get('parent_feature'):
                            html += f"<br><small>Feature: {item['parent_feature']}</small>"
                        if item.get('blocked_by'):
                            html += f"<br><small>⛔ Blocked by: {', '.join(item['blocked_by'])}</small>"

                        html += "</div>"

                html += '</div>'
            else:
                html += '<div>No items assigned to this sprint</div>'

            html += "</div>"

        # Recommendations
        html += "<h2>💡 Recommendations</h2>"

        if plan_data['recommendations']:
            for rec in plan_data['recommendations']:
                rec_class = {
                    'WARNING': 'rec-warning',
                    'RISK': 'rec-risk',
                    'INFO': 'rec-info'
                }.get(rec['type'], 'rec-info')

                severity_icon = {
                    'CRITICAL': '🔴',
                    'HIGH': '🟠',
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }.get(rec['severity'], '📌')

                html += f"""
        <div class="recommendation {rec_class}">
            <strong>{severity_icon} {rec['type']}</strong> - {rec['sprint']}<br>
            {rec['message']}<br>
            <small><strong>Action:</strong> {rec['action']}</small>
        </div>
"""
        else:
            html += "<div>No specific recommendations - planning looks good!</div>"

        # Carry-Over Items
        carry_overs = plan_data.get('carry_overs', [])
        if carry_overs:
            html += f"<h2>🔄 Chronic Carry-Overs ({len(carry_overs)} items)</h2>"
            html += """<p style="color: #666;">Items that have been in 3+ closed sprints without completion. Consider splitting, descoping, or resolving blockers.</p>"""
            html += """
        <table>
            <tr>
                <th>Issue</th>
                <th>Summary</th>
                <th>Sprints</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Assignee</th>
                <th>SP</th>
            </tr>
"""
            for item in carry_overs:
                jira_link = f"{jira_url}/browse/{item['key']}"
                sprint_count = item['sprint_count']
                severity_color = '#f44336' if sprint_count >= 5 else '#ff9800'
                sp_display = f"{item['story_points']:.0f}" if item['story_points'] > 0 else '-'
                html += f"""
            <tr>
                <td><a href="{jira_link}" target="_blank">{item['key']}</a></td>
                <td>{item['summary'][:60]}{'...' if len(item['summary']) > 60 else ''}</td>
                <td style="color: {severity_color}; font-weight: bold;">{sprint_count} sprints</td>
                <td>{item['status']}</td>
                <td>{item['priority']}</td>
                <td>{item['assignee']}</td>
                <td>{sp_display}</td>
            </tr>
"""
            html += "</table>"

        # Timeline
        html += "<h2>📆 Timeline Forecast</h2>"

        html += """
        <table>
            <tr>
                <th>Sprint</th>
                <th>Start Date</th>
                <th>End Date</th>
                <th>Items</th>
                <th>Capacity Used</th>
            </tr>
"""

        for sprint_info in plan_data['timeline']['sprints']:
            html += f"""
            <tr>
                <td>{sprint_info['name']}</td>
                <td>{sprint_info['start_date']}</td>
                <td>{sprint_info['end_date']}</td>
                <td>{sprint_info['num_items']}</td>
                <td>{sprint_info['capacity_used']:.1f} / {sprint_info['capacity']:.1f}</td>
            </tr>
"""

        html += "</table>"

        # Milestones
        if plan_data['timeline']['milestones']:
            html += "<h3>🎯 Key Milestones</h3>"
            for milestone in plan_data['timeline']['milestones']:
                html += f"""
        <div class="timeline-item">
            <strong>{milestone['sprint']}</strong> ({milestone['date']}): {milestone['description']}
            <br><small>Items: {', '.join(milestone['items'])}</small>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""

        return html

    @staticmethod
    def generate_json_output(plan_data: Dict) -> str:
        """Generate JSON output"""
        return json.dumps(plan_data, indent=2, default=str)

def main():
    parser = argparse.ArgumentParser(
        description='Sprint Planning Tool - Plan current and future sprints based on backlog analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Required arguments
    parser.add_argument('--project', required=True, help='Jira project key(s) - single (e.g., RHOAIENG) or comma-separated (e.g., RHAIENG,RHOAIENG)')
    parser.add_argument('--component', required=True, help='Team component name(s) - single (e.g., "Data Processing") or comma-separated (e.g., "Data Processing,Kubeflow Spark Operator")')

    # Optional arguments
    parser.add_argument('--team-name', help='Team display name for reports (default: component name)')
    parser.add_argument('--team-id', type=int, help='Jira Team field ID for filtering (e.g., 4967 for "AIP Training Kubeflow")')
    parser.add_argument('--sprint-pattern', help='Sprint naming pattern for filtering (e.g., "Training Kubeflow Sprint")')
    parser.add_argument('--num-sprints', type=int, default=4, help='Number of future sprints to plan (default: 4)')
    parser.add_argument('--sprint-length', type=int, default=2, help='Sprint length in weeks (default: 2)')
    parser.add_argument('--velocity-months', type=int, default=3, help='Months to look back for velocity calculation (default: 3)')
    parser.add_argument('--output-html', help='Path to save HTML output')
    parser.add_argument('--output-json', help='Path to save JSON output')
    parser.add_argument('--risk-data-file', help='Path to risk analysis data file (JSON) from teammate tools')
    parser.add_argument('--carry-over-sprints', type=int, default=3, help='Minimum closed sprints to flag an item as a chronic carry-over (default: 3)')

    args = parser.parse_args()

    team_name = args.team_name or args.component

    print(f"🚀 Sprint Planning Tool - {team_name}")
    print("=" * 80)
    print()

    # Initialize components
    try:
        jira_client = JiraClient()
        velocity_calculator = VelocityCalculator(jira_client)
        backlog_analyzer = BacklogAnalyzer(jira_client)
        sprint_planner = SprintPlanner(jira_client, backlog_analyzer)

        # Calculate velocity
        print(f"📊 Calculating team velocity (last {args.velocity_months} months)...")
        velocity, completion_rate, num_sprints, velocity_unit = velocity_calculator.calculate_velocity(
            project=args.project,
            component=args.component,
            sprint_pattern=args.sprint_pattern,
            months_back=args.velocity_months,
            team_id=args.team_id
        )

        print(f"   Velocity: {velocity:.1f} {velocity_unit}/sprint")
        print(f"   Completion Rate: {completion_rate:.0f}%")
        print(f"   Sprints Analyzed: {num_sprints}")

        # If no velocity, use estimation
        if velocity == 0:
            print(f"   ⚠️  No sprint history found - will estimate velocity from backlog size")
        print()

        # Get backlog
        print("📋 Fetching backlog...")
        backlog = backlog_analyzer.get_backlog(args.project, args.component, team_id=args.team_id)
        print(f"   Found {len(backlog)} backlog items")

        # If no velocity, estimate based on backlog
        if velocity == 0 and len(backlog) > 0:
            # Conservative estimate: assume team can handle 20 items per sprint
            velocity = 20.0
            completion_rate = 70.0
            velocity_unit = 'issues'
            print(f"   📊 Using estimated velocity: {velocity:.1f} {velocity_unit}/sprint (no historical data)")
        elif velocity == 0:
            print(f"   ⚠️  Warning: No backlog items and no sprint history found")

        print()

        # Load risk data if provided
        risk_data = None
        if args.risk_data_file:
            try:
                with open(args.risk_data_file, 'r') as f:
                    risk_data = json.load(f)
                print(f"✅ Loaded risk data from {args.risk_data_file}")
                print()
            except Exception as e:
                print(f"⚠️  Could not load risk data: {e}")
                print()

        # Get current sprint number
        print("🔢 Detecting current sprint...")
        current_sprint_num, detected_pattern, current_sprint_end_date, detected_sprint_length = sprint_planner.get_current_sprint_number(
            args.project,
            args.component,
            args.sprint_pattern,
            args.team_id
        )

        # Use detected sprint length if available, otherwise fall back to CLI arg
        sprint_length = detected_sprint_length if detected_sprint_length else args.sprint_length

        if current_sprint_num > 0:
            print(f"   Current Sprint: {detected_pattern} {current_sprint_num}")
            print(f"   Sprint Length: {sprint_length} weeks" + (" (auto-detected)" if detected_sprint_length else " (default)"))
            print(f"   Planning for: {detected_pattern} {current_sprint_num + 1} - {current_sprint_num + args.num_sprints}")
        else:
            print(f"   No active sprint detected - using default numbering")
            detected_pattern = args.sprint_pattern or "Sprint"
        print()

        # Plan sprints
        print(f"🎯 Planning next {args.num_sprints} sprints...")
        plan_data = sprint_planner.plan_sprints(
            backlog=backlog,
            velocity=velocity,
            num_sprints=args.num_sprints,
            sprint_length_weeks=sprint_length,
            risk_data=risk_data,
            current_sprint_num=current_sprint_num,
            sprint_name_pattern=detected_pattern,
            project=args.project,
            component=args.component,
            velocity_unit=velocity_unit,
            current_sprint_end_date=current_sprint_end_date,
            team_id=args.team_id,
            min_carry_over_sprints=args.carry_over_sprints
        )
        print()

        # Generate outputs
        output_gen = OutputGenerator()

        # Console summary
        print("=" * 80)
        print("📅 SPRINT PLAN SUMMARY")
        print("=" * 80)
        print()

        for sprint_name, sprint_data in sorted(plan_data['sprint_assignments'].items(), key=lambda x: x[1]['sprint_number']):
            if sprint_data['capacity'] > 0:
                capacity_pct = (sprint_data['capacity_used'] / sprint_data['capacity'] * 100)
            else:
                capacity_pct = 0
            print(f"{sprint_name}:")
            print(f"  Capacity: {sprint_data['capacity_used']:.1f} / {sprint_data['capacity']:.1f} {plan_data['metadata'].get('velocity_unit', 'issues')} ({capacity_pct:.0f}%)")

            existing_count = sprint_data.get('existing_items_count', 0)
            recommended_count = sprint_data.get('recommended_items_count', 0)

            if existing_count > 0:
                print(f"  Already Planned: {existing_count} items")
            if recommended_count > 0:
                print(f"  Recommended: {recommended_count} items")
            if existing_count == 0 and recommended_count == 0:
                print(f"  Items: {len(sprint_data['items'])}")

            if sprint_data['warnings']:
                for warning in sprint_data['warnings']:
                    print(f"  ⚠️  {warning}")
            print()

        # Carry-over summary
        carry_overs = plan_data.get('carry_overs', [])
        if carry_overs:
            min_co = args.carry_over_sprints
            print("🔄 CHRONIC CARRY-OVERS")
            print("-" * 40)
            print(f"   {len(carry_overs)} item(s) stuck in {min_co}+ sprints:")
            for item in carry_overs[:10]:
                print(f"   - {item['key']}: {item['sprint_count']} sprints | {item['status']} | {item['summary'][:50]}")
            if len(carry_overs) > 10:
                print(f"   ... and {len(carry_overs) - 10} more (see HTML report)")
            print()

        # Generate default filenames if not provided
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d')

        if not args.output_html:
            # Auto-generate HTML filename: "YYYY-MM-DD <Team Name> Sprint Planner.html"
            args.output_html = f"{date_str} {team_name} Sprint Planner.html"

        if not args.output_json:
            # Auto-generate JSON filename: "YYYY-MM-DD <Team Name> Sprint Planner.json"
            args.output_json = f"{date_str} {team_name} Sprint Planner.json"

        # Save HTML
        html_content = output_gen.generate_html_output(plan_data, team_name, JIRA_URL)
        with open(args.output_html, 'w') as f:
            f.write(html_content)
        print(f"✅ HTML report saved to: {args.output_html}")

        # Save JSON
        json_content = output_gen.generate_json_output(plan_data)
        with open(args.output_json, 'w') as f:
            f.write(json_content)
        print(f"✅ JSON data saved to: {args.output_json}")

        # Return Python object for programmatic use
        return plan_data

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    main()
