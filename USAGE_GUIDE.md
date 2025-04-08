# HPE Query Workflow: User Guide

This guide explains how to run and use the HPE Query Workflow system for refining queries using HPE document context.

## Setup Steps

1. **Install Requirements**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Environment File**:
   Make sure your `.env` file contains your Gemini API key:
   ```
   GEMINI_API_KEY="your-api-key-here"
   ```

3. **Optional: Create Sample Document Folder**:
   Create the sample_docs directory if not already created:
   ```bash
   mkdir -p /Users/vishnuadithya/Documents/HPE/sample_docs
   ```

## Running the Workflow

### Method 1: Interactive Mode (Recommended for First-Time Users)

The interactive mode provides a command-line interface to interact with the system:

