#!/bin/bash

# PDF Document Workflow for HPE
# This script helps import and manage PDF documents for the HPE query workflow

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}HPE PDF Document Workflow${NC}"
echo -e "${BLUE}=================================${NC}"

# Install PDF-specific dependencies if needed
echo -e "\n${BLUE}Checking PDF dependencies...${NC}"
python -c "import pypdf" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Installing pypdf library...${NC}"
    pip install pypdf
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ pypdf installed successfully${NC}"
    else
        echo -e "${RED}✗ Error installing pypdf. Some PDF functionality may be limited.${NC}"
    fi
else
    echo -e "${GREEN}✓ pypdf already installed${NC}"
fi

# Display the menu
echo -e "\n${BLUE}What would you like to do?${NC}"
echo -e "1) Import a single PDF document"
echo -e "2) Import all PDFs from the financial docs folder"
echo -e "3) Import all PDFs from a specific folder"
echo -e "4) Show document statistics"
echo -e "5) Process a query using the document knowledge"
echo -e "6) Exit"

read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        echo -e "\n${BLUE}Import a single PDF document${NC}"
        read -p "Enter the path to the PDF file: " pdf_path
        
        if [ ! -f "$pdf_path" ]; then
            echo -e "${RED}Error: File not found${NC}"
            exit 1
        fi
        
        if [[ ! "$pdf_path" == *.pdf ]]; then
            echo -e "${RED}Error: Not a PDF file${NC}"
            exit 1
        fi
        
        read -p "Enter document type (financial, product, press) [financial]: " doc_type
        doc_type=${doc_type:-financial}
        
        echo -e "${GREEN}Importing PDF...${NC}"
        python import_pdf_documents.py "$pdf_path" --type "$doc_type"
        ;;
        
    2)
        echo -e "\n${BLUE}Import all PDFs from financial docs folder${NC}"
        financial_folder="/Users/vishnuadithya/Documents/HPE/hpe_docs/financial"
        
        if [ ! -d "$financial_folder" ]; then
            echo -e "${YELLOW}Creating financial docs folder...${NC}"
            mkdir -p "$financial_folder"
        fi
        
        pdf_count=$(find "$financial_folder" -name "*.pdf" | wc -l)
        if [ $pdf_count -eq 0 ]; then
            echo -e "${YELLOW}No PDF files found in $financial_folder${NC}"
            read -p "Would you like to copy some PDFs there first? (y/n) " copy_pdfs
            
            if [[ $copy_pdfs =~ ^[Yy]$ ]]; then
                read -p "Enter the source folder with PDFs: " source_folder
                if [ -d "$source_folder" ]; then
                    echo -e "${GREEN}Copying PDFs to financial folder...${NC}"
                    cp "$source_folder"/*.pdf "$financial_folder"/ 2>/dev/null
                    if [ $? -eq 0 ]; then
                        echo -e "${GREEN}✓ PDFs copied successfully${NC}"
                    else
                        echo -e "${RED}✗ No PDFs found or error copying files${NC}"
                        exit 1
                    fi
                else
                    echo -e "${RED}Error: Source folder not found${NC}"
                    exit 1
                fi
            else
                echo -e "${YELLOW}Aborting import${NC}"
                exit 0
            fi
        fi
        
        echo -e "${GREEN}Importing PDFs from financial folder...${NC}"
        python import_pdf_documents.py "$financial_folder" --type "financial"
        ;;
        
    3)
        echo -e "\n${BLUE}Import all PDFs from a specific folder${NC}"
        read -p "Enter the folder path: " folder_path
        
        if [ ! -d "$folder_path" ]; then
            echo -e "${RED}Error: Folder not found${NC}"
            exit 1
        fi
        
        read -p "Enter document type (financial, product, press) [financial]: " doc_type
        doc_type=${doc_type:-financial}
        
        echo -e "${GREEN}Importing PDFs from $folder_path...${NC}"
        python import_pdf_documents.py "$folder_path" --type "$doc_type"
        ;;
        
    4)
        echo -e "\n${BLUE}Document statistics${NC}"
        python hpe_query_workflow.py stats
        ;;
        
    5)
        echo -e "\n${BLUE}Process a query${NC}"
        read -p "Enter your query: " query
        
        echo -e "${GREEN}Processing query...${NC}"
        python hpe_query_workflow.py query "$query"
        ;;
        
    6)
        echo -e "\n${GREEN}Exiting...${NC}"
        exit 0
        ;;
        
    *)
        echo -e "\n${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "\n${BLUE}=================================${NC}"
echo -e "${GREEN}Operation completed${NC}"
echo -e "${BLUE}=================================${NC}"
