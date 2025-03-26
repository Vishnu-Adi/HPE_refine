#!/bin/bash

# HPE Workflow Setup Script
# This script will:
# 1. Install required dependencies
# 2. Ensure directories exist
# 3. Fix document index issues
# 4. Make helper scripts executable

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}HPE Workflow Setup${NC}"
echo -e "${BLUE}=================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 1. Install dependencies
echo -e "\n${BLUE}Step 1: Installing dependencies${NC}"
if [ ! -f "requirements.txt" ]; then
    echo -e "${YELLOW}Warning: requirements.txt not found${NC}"
else
    echo -e "Installing required packages..."
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
    else
        echo -e "${RED}✗ Error installing dependencies${NC}"
    fi
fi

# 2. Ensure directories exist
echo -e "\n${BLUE}Step 2: Creating required directories${NC}"
mkdir -p hpe_docs/financial
mkdir -p hpe_docs/product
mkdir -p hpe_docs/press
mkdir -p sample_docs
echo -e "${GREEN}✓ Directories created${NC}"

# 3. Fix document index issues
echo -e "\n${BLUE}Step 3: Repairing document index${NC}"
if [ -f "fix_document_index.py" ]; then
    python fix_document_index.py --verbose
else
    echo -e "${RED}✗ fix_document_index.py not found${NC}"
fi

# 4. Make helper scripts executable
echo -e "\n${BLUE}Step 4: Making helper scripts executable${NC}"
chmod +x start_workflow.sh
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Made start_workflow.sh executable${NC}"
else
    echo -e "${RED}✗ Error making start_workflow.sh executable${NC}"
fi

# 5. Scan for documents
echo -e "\n${BLUE}Step 5: Scanning for documents${NC}"
if [ -f "scan_documents.py" ]; then
    python scan_documents.py hpe_docs sample_docs --recursive --verbose
else
    echo -e "${RED}✗ scan_documents.py not found${NC}"
fi

# 6. Show document stats
echo -e "\n${BLUE}Step 6: Checking document stats${NC}"
python hpe_query_workflow.py stats

echo -e "\n${GREEN}Setup completed!${NC}"
echo -e "You can now run the workflow with: ${YELLOW}./start_workflow.sh${NC}"
echo -e "Or directly with: ${YELLOW}python hpe_query_workflow.py interactive${NC}"

# Ask if user wants to try the workflow now
echo -e "\nWould you like to start the workflow now? (y/n)"
read -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./start_workflow.sh
fi
