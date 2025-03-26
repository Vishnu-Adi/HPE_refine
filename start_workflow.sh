#!/bin/bash

# Easy launcher script for HPE Query Workflow

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}HPE Query Workflow Launcher${NC}"
echo -e "${BLUE}=================================${NC}"

# Check if requirements are installed
if [ ! -f "requirements.txt" ]; then
    echo -e "${YELLOW}Warning: requirements.txt not found${NC}"
else
    echo -e "Checking requirements..."
    pip install -r requirements.txt > /dev/null
    echo -e "${GREEN}✓ Requirements checked${NC}"
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating template...${NC}"
    echo 'GEMINI_API_KEY="your-api-key-here"' > .env
    echo -e "${YELLOW}Please edit .env with your actual API key${NC}"
else
    echo -e "${GREEN}✓ Environment file found${NC}"
fi

# Create sample_docs directory if it doesn't exist
if [ ! -d "sample_docs" ]; then
    echo "Creating sample_docs directory..."
    mkdir -p sample_docs
    echo -e "${GREEN}✓ Created sample_docs directory${NC}"
else
    echo -e "${GREEN}✓ Sample docs directory exists${NC}"
fi

# Ask user what they want to do
echo ""
echo -e "What would you like to do?"
echo -e "1) Start interactive mode"
echo -e "2) Refine a single query"
echo -e "3) Import a document"
echo -e "4) Search documents"
echo -e "5) Show document statistics"
echo -e "6) Exit"

read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        echo -e "${GREEN}Starting interactive mode...${NC}"
        python hpe_query_workflow.py interactive
        ;;
    2)
        read -p "Enter your query: " query
        echo -e "${GREEN}Refining query...${NC}"
        python hpe_query_workflow.py query "$query"
        ;;
    3)
        read -p "Enter document path: " doc_path
        read -p "Enter document type (financial, product, press): " doc_type
        echo -e "${GREEN}Importing document...${NC}"
        python hpe_query_workflow.py import "$doc_path" --type "$doc_type"
        ;;
    4)
        read -p "Enter search keywords: " keywords
        echo -e "${GREEN}Searching documents...${NC}"
        python hpe_query_workflow.py search "$keywords"
        ;;
    5)
        echo -e "${GREEN}Showing document statistics...${NC}"
        python hpe_query_workflow.py stats
        ;;
    6)
        echo -e "${GREEN}Exiting...${NC}"
        exit 0
        ;;
    *)
        echo -e "${YELLOW}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}Operation completed.${NC}"
echo -e "${BLUE}=================================${NC}"
