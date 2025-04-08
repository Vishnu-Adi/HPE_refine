# HPE Query Workflow

This project provides a system for refining user queries related to HPE financial documents using Retrieval-Augmented Generation (RAG) techniques.

## Table of Contents

1.  [Overview](#overview)
2.  [Prerequisites](#prerequisites)
3.  [Setup](#setup)
4.  [Document Loading](#document-loading)
5.  [Running the Workflow](#running-the-workflow)
6.  [Key Files](#key-files)
7.  [Troubleshooting](#troubleshooting)
8.  [Contributing](#contributing)
9.  [License](#license)

## Overview

The HPE Query Workflow system is designed to:

*   Ingest and process HPE financial documents, product specifications, and press releases.
*   Refine user queries using RAG to provide more accurate and contextually relevant results.
*   Provide an interactive command-line interface for document management and query processing.

## Prerequisites

*   [Git](https://git-scm.com/)
*   [Python 3.7+](https://www.python.org/)
*   [Gemini API Key](https://ai.google.dev/)

## Setup

1.  **Clone the Repository:**

    ```bash
    git clone <repository_url>
    cd HPE
    ```
    Replace `<repository_url>` with the actual URL of your GitHub repository.

2.  **Set Up the Environment:**

    *   **Create a Virtual Environment (Recommended):**
        ```bash
        python -m venv .venv
        source .venv/bin/activate  # On macOS/Linux
        # .venv\Scripts\activate  # On Windows
        ```

    *   **Install Dependencies:**
        ```bash
        pip install -r requirements.txt
        ```

    *   **Configure API Key:**
        ```bash
        cp .env.example .env
        nano .env  # Or your preferred text editor
        ```
        Edit the [.env](http://_vscodecontentref_/0) file and replace `GEMINI_API_KEY="your-api-key-here"` with your actual Gemini API key.

## Document Loading

1.  **Organize Documents:**

    Create the following directories under [hpe_docs](http://_vscodecontentref_/1) and place your documents accordingly:

    ```bash
    mkdir -p hpe_docs/financial
    mkdir -p hpe_docs/product
    mkdir -p hpe_docs/press
    # Copy your PDFs into these directories
    ```

2.  **Choose an Import Method:**

    *   **Option 1: Using [pdf_workflow.sh](http://_vscodecontentref_/2) (Interactive PDF Import):**
        ```bash
        chmod +x pdf_workflow.sh
        ./pdf_workflow.sh
        ```
        Follow the menu options to import PDFs.

    *   **Option 2: Using [import_pdf_documents.py](http://_vscodecontentref_/3) (Command-Line Import):**
        ```bash
        python import_pdf_documents.py hpe_docs/financial --type financial
        ```
        Replace [financial](http://_vscodecontentref_/4) with the actual path to your PDF documents, and `--type financial` with the appropriate document type (`financial`, `product`, or `press`).

    *   **Option 3: Using [scan_documents.py](http://_vscodecontentref_/5) (Directory Scanning):**
        ```bash
        python scan_documents.py hpe_docs
        ```
        This will scan the [hpe_docs](http://_vscodecontentref_/6) directory and attempt to import any found documents.

3.  **Verify Document Loading:**

    *   **Using [hpe_query_workflow.py](http://_vscodecontentref_/7):**
        ```bash
        python hpe_query_workflow.py stats
        ```
        This will print statistics about the documents currently loaded in the document store.

    *   **Using [fix_document_index.py](http://_vscodecontentref_/8):**
        ```bash
        python fix_document_index.py
        ```
        This script checks for inconsistencies between the files in [hpe_docs](http://_vscodecontentref_/9) and the `document_index.json` file, and attempts to repair the index.

## Running the Workflow

1.  **Interactive Mode:**

    ```bash
    ./start_workflow.sh
    # Choose option 1 to enter interactive mode
    ```
    Then, type your queries at the prompt.

2.  **Direct Query:**

    ```bash
    python hpe_query_workflow.py query "HPE GreenLake ARR"
    ```

## Key Files

*   [hpe_query_workflow.py](http://_vscodecontentref_/10): The main script that orchestrates the workflow.
*   [hpe_document_store.py](http://_vscodecontentref_/11): Manages the document index and provides search functionality.
*   [hpe_rag_query_refiner.py](http://_vscodecontentref_/12): Refines queries using the RAG approach.
*   [start_workflow.sh](http://_vscodecontentref_/13): A convenience script that provides an interactive menu.
*   [pdf_workflow.sh](http://_vscodecontentref_/14): A script to help import and manage PDF documents.
*   [import_pdf_documents.py](http://_vscodecontentref_/15): A script to import PDF documents into the document store.
*   [scan_documents.py](http://_vscodecontentref_/16): A script to scan directories for documents and import them.
*   [fix_document_index.py](http://_vscodecontentref_/17): A script to fix inconsistencies in the document index.
*   [requirements.txt](http://_vscodecontentref_/18): Lists the Python packages that need to be installed.
*   [.env](http://_vscodecontentref_/19): Stores the Gemini API key.

## Troubleshooting

*   **PDF Support:** If you encounter errors related to PDF processing, make sure you have installed the necessary PDF libraries (e.g., `pypdf`, `pdfminer.six`, or `textract`). The [pdf_workflow.sh](http://_vscodecontentref_/20) script attempts to install `pypdf` automatically.
*   **File Paths:** Double-check that all file paths are correct.
*   **Permissions:** Make sure that the shell scripts (`.sh` files) have execute permissions (`chmod +x script_name.sh`).
*   **API Key:** Verify that your Gemini API key is correctly set in the [.env](http://_vscodecontentref_/21) file.
*   **Document Index:** If you suspect that the document index is corrupted, run `python fix_document_index.py`.

