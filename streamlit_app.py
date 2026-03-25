#!/usr/bin/env python3
"""
Sprint Planning Tool - Interactive Web Dashboard
Powered by Streamlit
"""

import streamlit as st
import os
import sys
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load .env file if present (for credentials)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# Ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sprint_planning_tool import (
    JiraClient, VelocityCalculator, BacklogAnalyzer, SprintPlanner, OutputGenerator,
    build_project_filter, build_component_filter, JIRA_URL
)

# --- Page Config ---
st.set_page_config(
    page_title="Sprint Planning Tool",
    page_icon="🎯",
    layout="wide"
)


# --- Sidebar ---
st.sidebar.title("🎯 Sprint Planning Tool")
st.sidebar.markdown("---")

# Credentials - auto-load from environment or .env file
env_email = os.getenv("JIRA_EMAIL", "")
env_token = os.getenv("JIRA_API_TOKEN", "")
has_credentials = bool(env_email and env_token)

if has_credentials:
    jira_email = env_email
    jira_token = env_token
    st.sidebar.success("Jira credentials loaded")
else:
    with st.sidebar.expander("Jira Credentials", expanded=True):
        jira_email = st.text_input("Jira Email", value=env_email)
        jira_token = st.text_input("Jira API Token", value=env_token, type="password")
        st.caption("Tip: create a `.env` file to skip this step. See below.")

st.sidebar.markdown("---")

# Team Configuration
st.sidebar.subheader("Team Configuration")
selected_projects = st.sidebar.multiselect("Project Key(s)", ["RHOAIENG", "RHAIENG"])
project = ",".join(selected_projects) if selected_projects else ""
component = st.sidebar.text_input("Component(s)", placeholder="e.g., Training Kubeflow")
team_name = st.sidebar.text_input("Team Name", placeholder="e.g., Training Kubeflow Team")
sprint_pattern = st.sidebar.text_input("Sprint Pattern", placeholder="e.g., Training Kubeflow Sprint")

st.sidebar.markdown("---")

# Planning Options
st.sidebar.subheader("Planning Options")
num_sprints = st.sidebar.slider("Number of Sprints", 1, 8, 4)
velocity_months = st.sidebar.slider("Velocity History (months)", 1, 12, 3)

# --- Main Content ---
st.title("🎯 Sprint Planning Dashboard")

if not jira_email or not jira_token:
    st.info("Enter your Jira credentials in the sidebar to get started, or create a `.env` file.")
    st.markdown("""
    ### Option 1: Create a `.env` file (recommended, one-time setup)
    Create a file called `.env` in the Sprint-Planning-Tool directory:
    ```
    JIRA_EMAIL=yourname@redhat.com
    JIRA_API_TOKEN=your-token-here
    ```
    Then refresh this page. Credentials will load automatically.

    ### Option 2: Enter credentials in the sidebar
    Expand "Jira Credentials" in the sidebar and enter your email and token.

    ### How to get your Jira API Token:
    1. Go to [Red Hat Jira](https://redhat.atlassian.net)
    2. Click your profile icon → **Personal Access Tokens**
    3. Click **Create token** and copy it
    """)
    st.stop()

if not selected_projects or not component:
    st.warning("Please select at least one Project and fill in the Component field in the sidebar.")
    st.stop()

# Run button
run_button = st.sidebar.button("🚀 Run Sprint Planning", type="primary", use_container_width=True)

if run_button:
    # Set environment variables for the JiraClient
    os.environ["JIRA_EMAIL"] = jira_email
    os.environ["JIRA_API_TOKEN"] = jira_token

    try:
        # Initialize
        progress = st.progress(0, text="Initializing...")
        jira_client = JiraClient()
        velocity_calculator = VelocityCalculator(jira_client)
        backlog_analyzer = BacklogAnalyzer(jira_client)
        sprint_planner = SprintPlanner(jira_client, backlog_analyzer)

        # Step 1: Calculate velocity
        progress.progress(10, text="Calculating team velocity...")
        velocity, completion_rate, num_sprints_analyzed, velocity_unit = velocity_calculator.calculate_velocity(
            project=project,
            component=component,
            sprint_pattern=sprint_pattern,
            months_back=velocity_months
        )

        if velocity == 0:
            velocity = 20.0
            completion_rate = 70.0
            velocity_unit = 'issues'

        # Step 2: Get backlog
        progress.progress(30, text="Fetching backlog...")
        backlog = backlog_analyzer.get_backlog(project, component)

        # Step 3: Detect current sprint
        progress.progress(50, text="Detecting current sprint...")
        current_sprint_num, detected_pattern, current_sprint_end_date, detected_sprint_length = sprint_planner.get_current_sprint_number(
            project, component, sprint_pattern
        )

        sprint_length = detected_sprint_length if detected_sprint_length else 2

        if current_sprint_num == 0:
            detected_pattern = sprint_pattern or "Sprint"

        # Step 4: Plan sprints
        progress.progress(70, text="Planning sprints...")
        plan_data = sprint_planner.plan_sprints(
            backlog=backlog,
            velocity=velocity,
            num_sprints=num_sprints,
            sprint_length_weeks=sprint_length,
            current_sprint_num=current_sprint_num,
            sprint_name_pattern=detected_pattern,
            project=project,
            component=component,
            velocity_unit=velocity_unit,
            current_sprint_end_date=current_sprint_end_date
        )

        progress.progress(100, text="Done!")
        st.session_state["plan_data"] = plan_data
        st.session_state["velocity"] = velocity
        st.session_state["velocity_unit"] = velocity_unit
        st.session_state["completion_rate"] = completion_rate
        st.session_state["num_sprints_analyzed"] = num_sprints_analyzed
        st.session_state["current_sprint_num"] = current_sprint_num
        st.session_state["detected_pattern"] = detected_pattern
        st.session_state["team_name"] = team_name
        st.session_state["backlog_count"] = len(backlog)
        st.session_state["sprint_length"] = sprint_length

    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc())
        st.stop()

# --- Display Results ---
if "plan_data" in st.session_state:
    plan_data = st.session_state["plan_data"]
    velocity = st.session_state["velocity"]
    velocity_unit = st.session_state["velocity_unit"]
    completion_rate = st.session_state["completion_rate"]
    num_sprints_analyzed = st.session_state["num_sprints_analyzed"]
    current_sprint_num = st.session_state["current_sprint_num"]
    detected_pattern = st.session_state["detected_pattern"]
    display_team_name = st.session_state["team_name"]
    backlog_count = st.session_state["backlog_count"]

    st.subheader(f"📊 {display_team_name}")

    sprint_length = st.session_state["sprint_length"]

    # --- Metrics Row ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Velocity", f"{velocity:.1f} {velocity_unit}/sprint")
    col2.metric("Completion Rate", f"{completion_rate:.0f}%")
    col3.metric("Backlog Items", backlog_count)

    col4, col5, col6 = st.columns(3)
    col4.metric("Current Sprint", f"{detected_pattern} {current_sprint_num}" if current_sprint_num > 0 else "N/A")
    col5.metric("Sprint Length", f"{sprint_length} weeks")
    col6.metric("Sprints Analyzed", num_sprints_analyzed)

    st.markdown("---")

    # --- Tabs ---
    tab_plan, tab_timeline, tab_help = st.tabs(["📅 Sprint Plan", "📆 Timeline", "❓ Help"])

    # =====================
    # TAB 1: Sprint Plan
    # =====================
    with tab_plan:

        # --- Sprint Cards ---
        st.subheader("📅 Sprint Assignments")

        sorted_sprints = sorted(plan_data["sprint_assignments"].items(), key=lambda x: x[1]["sprint_number"])

        for sprint_name, sprint_data in sorted_sprints:
            capacity = sprint_data["capacity"]
            used = sprint_data["capacity_used"]
            pct = (used / capacity * 100) if capacity > 0 else 0

            with st.expander(f"**{sprint_name}** — {used:.1f} / {capacity:.1f} {velocity_unit} ({pct:.0f}%)", expanded=(sprint_data["sprint_number"] == current_sprint_num + 1)):
                # Capacity bar
                st.progress(min(pct / 100, 1.0))

                # Warnings
                for warning in sprint_data.get("warnings", []):
                    st.warning(warning)

                # Existing items
                existing_items = [i for i in sprint_data["items"] if i.get("already_planned")]
                recommended_items = [i for i in sprint_data["items"] if not i.get("already_planned")]

                if existing_items:
                    st.markdown(f"**📌 Already Planned ({len(existing_items)})**")
                    existing_df = pd.DataFrame([{
                        "Key": f"{JIRA_URL}/browse/{i['key']}",
                        "Summary": i["summary"][:80],
                        "Priority": i["priority"],
                        "Status": i["status"],
                        "SP": i.get("story_points", 0)
                    } for i in existing_items])
                    st.dataframe(existing_df, use_container_width=True, hide_index=True,
                               column_config={"Key": st.column_config.LinkColumn("Key", display_text=r"browse/(.*)")})

                if recommended_items:
                    st.markdown(f"**✨ Recommended ({len(recommended_items)})**")
                    rec_df = pd.DataFrame([{
                        "Key": f"{JIRA_URL}/browse/{i['key']}",
                        "Summary": i["summary"][:80],
                        "Priority": i["priority"],
                        "Score": f"{i.get('priority_score', 0):.0f}",
                        "SP": i.get("story_points", 0),
                        "Blocked By": ", ".join(i.get("blocked_by", [])) or "-"
                    } for i in recommended_items])
                    st.dataframe(rec_df, use_container_width=True, hide_index=True,
                               column_config={"Key": st.column_config.LinkColumn("Key", display_text=r"browse/(.*)")})

                if not existing_items and not recommended_items:
                    st.info("No items assigned to this sprint")

        st.markdown("---")

        # --- Carry-Overs ---
        carry_overs = plan_data.get("carry_overs", [])
        if carry_overs:
            st.subheader(f"🔄 Chronic Carry-Overs ({len(carry_overs)} items)")
            st.caption("Items stuck in 3+ closed sprints without completion. Consider splitting, descoping, or resolving blockers.")

            co_df = pd.DataFrame([{
                "Key": f"{JIRA_URL}/browse/{c['key']}",
                "Summary": c["summary"][:60],
                "Sprints": c["sprint_count"],
                "Status": c["status"],
                "Priority": c["priority"],
                "Assignee": c["assignee"],
                "SP": c["story_points"] if c["story_points"] > 0 else "-"
            } for c in carry_overs])

            st.dataframe(co_df, use_container_width=True, hide_index=True,
                        column_config={
                            "Key": st.column_config.LinkColumn("Key", display_text=r"browse/(.*)"),
                            "Sprints": st.column_config.ProgressColumn("Sprints", min_value=0, max_value=max(c["sprint_count"] for c in carry_overs), format="%d")
                        })

        st.markdown("---")

        # --- Recommendations ---
        st.subheader("💡 Recommendations")
        recommendations = plan_data.get("recommendations", [])
        if recommendations:
            for rec in recommendations:
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(rec["severity"], "📌")
                if rec["type"] == "RISK":
                    st.error(f"{icon} **{rec['type']}** — {rec['sprint']}: {rec['message']}\n\n**Action:** {rec['action']}")
                elif rec["type"] == "WARNING":
                    st.warning(f"{icon} **{rec['type']}** — {rec['sprint']}: {rec['message']}\n\n**Action:** {rec['action']}")
                else:
                    st.info(f"{icon} **{rec['type']}** — {rec['sprint']}: {rec['message']}\n\n**Action:** {rec['action']}")
        else:
            st.success("No specific recommendations - planning looks good!")

        st.markdown("---")

        # --- Export ---
        st.subheader("📥 Export")
        col1, col2 = st.columns(2)

        html_content = OutputGenerator.generate_html_output(plan_data, display_team_name, JIRA_URL)
        date_str = datetime.now().strftime("%Y-%m-%d")
        col1.download_button(
            "Download HTML Report",
            data=html_content,
            file_name=f"{date_str} {display_team_name} Sprint Planner.html",
            mime="text/html",
            use_container_width=True
        )

        json_content = OutputGenerator.generate_json_output(plan_data)
        col2.download_button(
            "Download JSON Data",
            data=json_content,
            file_name=f"{date_str} {display_team_name} Sprint Planner.json",
            mime="application/json",
            use_container_width=True
        )

    # =====================
    # TAB 2: Timeline
    # =====================
    with tab_timeline:

        st.subheader("📆 Timeline Forecast")
        timeline_data = plan_data.get("timeline", {}).get("sprints", [])
        if timeline_data:
            timeline_df = pd.DataFrame([{
                "Sprint": t["name"],
                "Start Date": t["start_date"],
                "End Date": t["end_date"],
                "Items": t["num_items"],
                "Capacity Used": f"{t['capacity_used']:.1f} / {t['capacity']:.1f} {velocity_unit}"
            } for t in timeline_data])
            st.dataframe(timeline_df, use_container_width=True, hide_index=True)

        # Milestones
        milestones = plan_data.get("timeline", {}).get("milestones", [])
        if milestones:
            st.markdown("---")
            st.subheader("🎯 Key Milestones")
            for m in milestones:
                st.info(f"**{m['sprint']}** ({m['date']}): {m['description']} — {', '.join(m['items'])}")

        # Visual timeline bar chart
        if timeline_data:
            st.markdown("---")
            st.subheader("📊 Capacity Utilization")
            chart_df = pd.DataFrame([{
                "Sprint": t["name"],
                "Used": t["capacity_used"],
                "Available": max(t["capacity"] - t["capacity_used"], 0)
            } for t in timeline_data])
            chart_df = chart_df.set_index("Sprint")
            st.bar_chart(chart_df)

    # =====================
    # TAB 3: Help
    # =====================
    with tab_help:

        st.subheader("❓ How the Sprint Planning Tool Works")
        st.markdown("""
        This tool analyzes your team's Jira data to automatically plan future sprints.
        It pulls real-time backlog and sprint history, calculates your team's velocity,
        and assigns items to upcoming sprints based on priority and capacity.
        """)

        st.markdown("---")

        st.subheader("📊 Metrics Definitions")

        st.markdown("""
        | Metric | Definition |
        |--------|-----------|
        | **Velocity** | Average story points (or issues) completed per sprint, calculated from recent closed sprints. Higher = team delivers more per sprint. |
        | **Completion Rate** | Percentage of planned items that were actually completed in past sprints. A rate below 70% suggests the team is consistently overcommitting. |
        | **Backlog Items** | Total number of unplanned items (not in any sprint, not Done/Closed/Resolved). These are candidates for future sprint assignment. |
        | **Current Sprint** | The active sprint detected from Jira, used as the starting point for planning future sprints. |
        | **Sprint Length** | Auto-detected from the current sprint's start and end dates in Jira. Used to calculate timeline forecasts. |
        | **Story Points (SP)** | A measure of effort/complexity assigned to each issue. Items with 0 SP don't consume capacity but are still included in the plan. |
        """)

        st.markdown("---")

        st.subheader("🧮 Priority Scoring System")
        st.markdown("""
        Each backlog item receives a **priority score** (0-500+ points) that determines which sprint it gets assigned to.
        Items with higher scores are planned into earlier sprints. The score is calculated from 6 factors:
        """)

        score_data = pd.DataFrame([
            {"Factor": "1. Issue Priority", "Max Points": 100, "Description": "Blocker=100, Critical=80, High=60, Major=50, Normal=30, Low=20"},
            {"Factor": "2. Parent Feature Priority", "Max Points": 100, "Description": "Same scale as issue priority, based on the parent Feature"},
            {"Factor": "3. Target End Date", "Max Points": 50, "Description": "Past due=50, <30 days=40, <60 days=30, <90 days=20, >90 days=10"},
            {"Factor": "4. Target Version", "Max Points": 30, "Description": "EA (Early Access)=30, RC=25, GA=20, Other=10"},
            {"Factor": "5. RICE Score", "Max Points": 100, "Description": "Product priority score from parent Feature (if available)"},
            {"Factor": "6. Dependency Boost", "Max Points": "+10 each", "Description": "If this issue blocks other issues, +10 per blocked issue"},
        ])
        st.dataframe(score_data, use_container_width=True, hide_index=True)

        st.markdown("""
        **Score ranges:**
        - **200+** — Urgent items with tight deadlines or Blocker/Critical priority
        - **100-200** — Important items with moderate urgency
        - **<100** — Lower priority or items without parent Feature context
        """)

        st.markdown("---")

        st.subheader("💡 How Recommendations Work")
        st.markdown("""
        The tool automatically generates recommendations based on the sprint plan:

        | Type | Severity | Trigger |
        |------|----------|---------|
        | **Overcommitment** | 🟠 HIGH | A sprint's assigned story points exceed its capacity |
        | **High-Priority Overload** | 🟡 MEDIUM | >80% of a sprint's capacity is Blocker/Critical items |
        | **Low Utilization** | 🟢 LOW | A sprint is less than 50% utilized — room to pull more items |
        | **Blocked Issues** | 🔴 CRITICAL | Risk data shows blocked issues in the current sprint |
        | **Carry-Over (Severe)** | 🟠 HIGH | Items stuck in 5+ closed sprints without completion |
        | **Carry-Over (Moderate)** | 🟡 MEDIUM | Items stuck in 3-4 closed sprints without completion |

        Each recommendation includes a suggested **Action** to help resolve the issue.
        """)

        st.markdown("---")

        st.subheader("🔄 Carry-Over Tracking")
        st.markdown("""
        Items that keep getting carried from sprint to sprint are a planning smell. The tool detects issues
        that have appeared in multiple closed sprints but are still not Done/Closed/Resolved.

        **How it works:**
        1. Queries all issues in closed sprints that match your team's sprint pattern
        2. Counts how many closed sprints each unfinished issue has appeared in
        3. Flags items that meet the threshold (default: 3+ sprints, adjustable in sidebar)

        **What to do about carry-overs:**
        - **Split the item** — It may be too large. Break it into smaller deliverable pieces.
        - **Descope** — If it keeps slipping, it may not be important enough to keep planning.
        - **Escalate blockers** — There may be hidden dependencies or blockers preventing progress.
        - **Re-estimate** — The story points may be underestimated, causing it to not fit in sprints.
        """)

        st.markdown("---")

        st.subheader("📅 Sprint Assignment Logic")
        st.markdown("""
        **How items get assigned to sprints:**

        1. **Already Planned items** are loaded first — issues already in future/active Jira sprints
           that match your team's sprint pattern. Their story points count against sprint capacity.

        2. **Backlog items** are sorted by priority score (highest first) and assigned to the earliest
           sprint with remaining capacity.

        3. **Dependencies are respected** — if an item is blocked by another issue, it won't be placed
           in an earlier sprint than its blocker.

        4. **Zero-point items** (no story points assigned) are included in the plan but don't consume
           capacity. They're highlighted with a warning so you can estimate them.

        **Capacity calculation:**
        - Each sprint's capacity = team velocity (average completed story points per sprint)
        - Capacity used = sum of story points for all items assigned to that sprint
        - The capacity bar shows utilization percentage (green < 100%, red > 100%)
        """)

        st.markdown("---")

        st.subheader("📆 Timeline Forecast")
        st.markdown("""
        The Timeline tab shows projected start and end dates for each planned sprint, calculated from
        the current sprint's end date and the auto-detected sprint length.

        **Key Milestones** are automatically flagged when a sprint contains Blocker-priority items,
        since these typically represent critical deliverables.

        The **Capacity Utilization** chart provides a visual overview of how well each sprint is loaded,
        making it easy to spot imbalances across the planning horizon.
        """)

        st.markdown("---")

        st.subheader("🔧 Sidebar Options")
        st.markdown("""
        | Option | Description |
        |--------|-----------|
        | **Project Key(s)** | Select one or both Jira projects (RHOAIENG, RHAIENG) |
        | **Component(s)** | Jira component filter. Use comma-separated for multiple (e.g., `Data Processing,Kubeflow Spark Operator`) |
        | **Team Name** | Display name used in reports and exports |
        | **Sprint Pattern** | Text pattern to match your team's sprint names (e.g., `DP Sprint`). Used to filter sprints from other teams. |
        | **Number of Sprints** | How many future sprints to plan (1-8) |
        | **Velocity History** | How many months of closed sprint data to use for velocity calculation |
        """)
