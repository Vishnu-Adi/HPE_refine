#!/bin/bash

# Batch Query Runner for HPE Query Refinement System
# Run different sets of test queries and compare results

# Define colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}HPE Query Test Runner${NC}"
echo -e "${BLUE}=================================${NC}"

# Create reports directory if it doesn't exist
mkdir -p reports

# Get timestamp for report naming
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Display menu
echo -e "\n${BLUE}What type of test would you like to run?${NC}"
echo "1) Run all query categories"
echo "2) Run financial queries only"
echo "3) Run product queries only"
echo "4) Run comparative queries only"
echo "5) Run informal queries only"
echo "6) Run ambiguous queries only"
echo "7) Run PDF accuracy test"
echo "8) Compare RAG vs. non-RAG performance"
echo "9) Run custom query"
echo "0) Exit"

read -p "Enter your choice (0-9): " choice

case $choice in
    1)
        echo -e "\n${GREEN}Running all query categories...${NC}"
        python test_queries.py --output reports/all_queries_${TIMESTAMP}.md
        ;;
    2)
        echo -e "\n${GREEN}Running financial queries...${NC}"
        python test_queries.py --category financial --output reports/financial_queries_${TIMESTAMP}.md
        ;;
    3)
        echo -e "\n${GREEN}Running product queries...${NC}"
        python test_queries.py --category product --output reports/product_queries_${TIMESTAMP}.md
        ;;
    4)
        echo -e "\n${GREEN}Running comparative queries...${NC}"
        python test_queries.py --category comparative --output reports/comparative_queries_${TIMESTAMP}.md
        ;;
    5)
        echo -e "\n${GREEN}Running informal queries...${NC}"
        python test_queries.py --category informal --output reports/informal_queries_${TIMESTAMP}.md
        ;;
    6)
        echo -e "\n${GREEN}Running ambiguous queries...${NC}"
        python test_queries.py --category ambiguous --output reports/ambiguous_queries_${TIMESTAMP}.md
        ;;
    7)
        echo -e "\n${GREEN}Running PDF accuracy test...${NC}"
        python test_pdf_accuracy.py --output reports/pdf_accuracy_${TIMESTAMP}.md
        ;;
    8)
        echo -e "\n${GREEN}Comparing RAG vs. non-RAG performance...${NC}"
        echo -e "${YELLOW}Running with RAG enabled...${NC}"
        python test_queries.py --limit 10 --output reports/rag_enabled_${TIMESTAMP}.md
        
        echo -e "\n${YELLOW}Running with RAG disabled...${NC}"
        python test_queries.py --limit 10 --no-rag --output reports/rag_disabled_${TIMESTAMP}.md
        
        echo -e "\n${GREEN}Comparison complete. Reports saved to reports/ directory.${NC}"
        ;;
    9)
        echo -e "\n${BLUE}Run custom query:${NC}"
        read -p "Enter your query: " query
        
        echo -e "\n${GREEN}Running query: ${query}${NC}"
        python test_queries.py --query "$query" --output reports/custom_query_${TIMESTAMP}.md
        ;;
    0)
        echo -e "\n${GREEN}Exiting...${NC}"
        exit 0
        ;;
    *)
        echo -e "\n${RED}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac

echo -e "\n${BLUE}=================================${NC}"
echo -e "${GREEN}Operation completed.${NC}"
echo -e "${BLUE}Test reports saved to the reports/ directory.${NC}"
echo -e "${BLUE}=================================${NC}"
