# HPE Query Refinement Workflow

A comprehensive system for refining HPE (Hewlett Packard Enterprise) related search queries using Retrieval Augmented Generation (RAG) techniques and the Gemini API.

## Overview

This project provides a workflow for:

1. **Document Management**: Import and organize HPE-related documents (financial reports, product information, press releases)
2. **Query Refinement**: Transform raw user queries into more precise search queries specifically tailored for HPE business and financial data
3. **RAG Enhancement**: Use relevant documents to provide context for improved query refinement

## Components

- **Document Store** (`hpe_document_store.py`): Manages and indexes document collection
- **RAG Query Refiner** (`hpe_rag_query_refiner.py`): Refines user queries using Gemini API and document context
- **Workflow** (`hpe_query_workflow.py`): Integrates all components with a CLI interface

## Setup

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your Gemini API key:
   - Create a `.env` file with your API key:
     ```
     GEMINI_API_KEY="your-api-key-here"
     ```

## Usage

### Interactive Mode

Run the workflow in interactive mode:

