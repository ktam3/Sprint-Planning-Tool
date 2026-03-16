#!/bin/bash

# Sprint Planning Tool - Executive Wrapper Script
# Simplifies running the sprint planning tool

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Sprint Planning Tool${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if JIRA_API_TOKEN is set
if [ -z "$JIRA_API_TOKEN" ]; then
    echo -e "${RED}❌ ERROR: JIRA_API_TOKEN not set${NC}"
    echo ""
    echo -e "${YELLOW}Please set your Jira API token:${NC}"
    echo -e "  export JIRA_API_TOKEN='your-token-here'"
    echo -e "  export JIRA_EMAIL='your-email@redhat.com'"
    echo ""
    echo -e "${YELLOW}Or run this script with:${NC}"
    echo -e "  JIRA_API_TOKEN='your-token' JIRA_EMAIL='your-email' $0"
    echo ""
    exit 1
fi

# Check if JIRA_EMAIL is set
if [ -z "$JIRA_EMAIL" ]; then
    echo -e "${RED}❌ ERROR: JIRA_EMAIL not set${NC}"
    echo ""
    echo -e "${YELLOW}Please set your Jira email:${NC}"
    echo -e "  export JIRA_EMAIL='your-email@redhat.com'"
    echo ""
    exit 1
fi

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ ERROR: Python 3 is not installed${NC}"
    echo ""
    echo -e "${YELLOW}Please install Python 3:${NC}"
    echo -e "  https://www.python.org/downloads/"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Environment check passed${NC}"
echo ""

# Menu of common teams
echo -e "${BLUE}Select a team to analyze:${NC}"
echo ""
echo "  1) Training Kubeflow Team"
echo "  2) Data Processing Team"
echo "  3) Custom (I'll provide my own parameters)"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}Running analysis for Training Kubeflow Team...${NC}"
        echo ""
        python3 sprint_planning_tool.py \
            --project RHOAIENG \
            --component "Training Kubeflow" \
            --team-name "Training Kubeflow Team" \
            --sprint-pattern "Training Kubeflow Sprint" \
            --num-sprints 4
        ;;
    2)
        echo ""
        echo -e "${GREEN}Running analysis for Data Processing Team...${NC}"
        echo ""
        python3 sprint_planning_tool.py \
            --project "RHAIENG,RHOAIENG" \
            --component "Data Processing,Kubeflow Spark Operator" \
            --team-name "Data Processing Team" \
            --sprint-pattern "DP Sprint" \
            --num-sprints 4
        ;;
    3)
        echo ""
        echo -e "${YELLOW}Custom mode - please provide parameters${NC}"
        echo ""
        read -p "Project key (e.g., RHOAIENG): " project
        read -p "Component name (e.g., Training Kubeflow): " component
        read -p "Team name (optional): " team_name
        read -p "Number of sprints to plan [4]: " num_sprints
        num_sprints=${num_sprints:-4}

        echo ""
        echo -e "${GREEN}Running analysis...${NC}"
        echo ""
        python3 sprint_planning_tool.py \
            --project "$project" \
            --component "$component" \
            ${team_name:+--team-name "$team_name"} \
            --num-sprints "$num_sprints"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Success message
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Sprint planning complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Output files:${NC}"
ls -lth *.html 2>/dev/null | head -1 | awk '{print "  📄 " $9 " (HTML report)"}'
ls -lth *.json 2>/dev/null | head -1 | awk '{print "  📊 " $9 " (JSON data)"}'
echo ""
echo -e "${BLUE}To open the HTML report:${NC}"
ls -t *.html 2>/dev/null | head -1 | awk '{print "  open \"" $1 "\""}'
echo ""
