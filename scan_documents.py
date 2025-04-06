import os
import argparse
import json
import sys
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.hpe_document_store import HPEDocumentStore

def scan_directory_for_documents(directory: str) -> List[Dict[str, Any]]:
    """
    Scan a directory for document files.
    
    Args:
        directory: Directory to scan
        
    Returns:
        List of document info dictionaries
    """
    if not os.path.exists(directory) or not os.path.isdir(directory):
        print(f"Directory not found: {directory}")
        return []
    
    documents = []
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        # Skip directories and non-text files
        if os.path.isdir(file_path):
            continue
        
        if not filename.endswith(('.txt', '.md', '.csv', '.json')):
            continue
            
        # Get file stats
        file_stats = os.stat(file_path)
        file_size = file_stats.st_size
        
        # Only process reasonable sized files (up to 10MB)
        if file_size > 10 * 1024 * 1024:
            print(f"Skipping large file: {file_path} ({file_size / 1024 / 1024:.2f} MB)")
            continue
            
        # Basic file info
        doc_info = {
            "path": file_path,
            "filename": filename,
            "size": file_size,
            "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
        }
        
        documents.append(doc_info)
    
    return documents

def determine_doc_type(file_path: str) -> str:
    """
    Try to determine document type based on path and content.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Document type string
    """
    # Try to determine type from path
    path_lower = file_path.lower()
    
    if any(term in path_lower for term in ['financial', 'earnings', 'revenue', 'quarter', 'fiscal']):
        return "financial"
    elif any(term in path_lower for term in ['product', 'service', 'greenlake', 'offering']):
        return "product"
    elif any(term in path_lower for term in ['press', 'news', 'release', 'announcement']):
        return "press"
    
    # Try to read content to determine type
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(4096)  # Read first 4KB
            
            # Check for financial indicators
            if any(term in content.lower() for term in ['revenue', 'quarterly results', 'fiscal', 'earnings', 'eps', 'arr']):
                return "financial"
            
            # Check for product indicators
            if any(term in content.lower() for term in ['product', 'service', 'greenlake', 'platform', 'solution']):
                return "product"
            
            # Check for press release indicators
            if any(term in content.lower() for term in ['announces', 'today announced', 'press release']):
                return "press"
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    
    # Default to "other" if type couldn't be determined
    return "other"

def extract_metadata(file_path: str, doc_type: str) -> Dict[str, Any]:
    """
    Extract metadata from document content.
    
    Args:
        file_path: Path to the document file
        doc_type: Document type
        
    Returns:
        Metadata dictionary
    """
    metadata = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(8192)  # Read first 8KB
            
            # Extract quarter and year for financial documents
            if doc_type == "financial":
                # Look for quarter references like Q1, Q2, etc.
                quarter_match = re.search(r'Q([1-4])\s+FY?(\d{2,4})', content, re.IGNORECASE)
                if quarter_match:
                    metadata["quarter"] = f"Q{quarter_match.group(1)}"
                    year = quarter_match.group(2)
                    if len(year) == 2:
                        year = f"20{year}"
                    metadata["fiscal_year"] = year
                
                # Look for ARR mentions
                if 'annual recurring revenue' in content.lower() or 'arr' in content.lower():
                    metadata["includes_arr"] = True
                
            # Extract product name for product documents
            elif doc_type == "product":
                # Look for GreenLake mentions
                if 'greenlake' in content.lower():
                    metadata["product"] = "GreenLake"
                
                # Look for Aruba mentions
                if 'aruba' in content.lower():
                    metadata["product"] = "Aruba"
                
            # Extract announcement date for press releases
            elif doc_type == "press":
                # Try to find a date pattern
                date_match = re.search(r'(\w+ \d{1,2},? \d{4})', content)
                if date_match:
                    metadata["publication_date"] = date_match.group(1)
    
    except Exception as e:
        print(f"Error extracting metadata from {file_path}: {e}")
    
    return metadata

def import_files_to_store(doc_store: HPEDocumentStore, 
                         files: List[Dict[str, Any]], 
                         dry_run: bool = False) -> int:
    """
    Import found files into the document store.
    
    Args:
        doc_store: Document store instance
        files: List of file info dictionaries
        dry_run: If True, don't actually import files
        
    Returns:
        Number of files imported
    """
    imported_count = 0
    
    for file_info in files:
        file_path = file_info["path"]
        
        # Determine document type
        doc_type = determine_doc_type(file_path)
        
        # Extract metadata
        metadata = extract_metadata(file_path, doc_type)
        
        # Add filename to metadata
        metadata["source_filename"] = file_info["filename"]
        metadata["last_modified"] = file_info["last_modified"]
        
        print(f"Found document: {file_path}")
        print(f"  Type: {doc_type}")
        print(f"  Metadata: {metadata}")
        
        if not dry_run:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                doc_id = doc_store.add_document(
                    content=content,
                    doc_type=doc_type,
                    metadata=metadata
                )
                
                if doc_id:
                    imported_count += 1
                    print(f"  Imported as: {doc_id}")
                else:
                    print(f"  Failed to import")
            except Exception as e:
                print(f"  Error importing: {e}")
        else:
            print("  [DRY RUN] Would import this document")
    
    return imported_count


# Add support for importing documents from this module
import re  # Add this import at the top of the file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan and import documents into HPE Document Store")
    parser.add_argument("directories", nargs="*", default=["hpe_docs"], help="Directories to scan for documents")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually import documents")
    parser.add_argument("--recursive", action="store_true", help="Scan directories recursively")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    
    args = parser.parse_args()
    
    print("HPE Document Scanner")
    print("===================")
    
    doc_store = HPEDocumentStore()
    
    # Print current stats
    print("\nCurrent document store statistics:")
    print(json.dumps(doc_store.get_document_stats(), indent=2))
    
    # Collect all files to scan
    all_files = []
    
    for directory in args.directories:
        if args.recursive:
            # Walk directory recursively
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Basic file info
                    try:
                        file_stats = os.stat(file_path)
                        all_files.append({
                            "path": file_path,
                            "filename": file,
                            "size": file_stats.st_size,
                            "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                        })
                    except Exception as e:
                        print(f"Error getting file info for {file_path}: {e}")
        else:
            # Just scan top level
            files = scan_directory_for_documents(directory)
            all_files.extend(files)
    
    print(f"\nFound {len(all_files)} potential documents")
    
    # Filter out files that likely aren't documents
    valid_files = [f for f in all_files if f["path"].endswith(('.txt', '.md', '.csv', '.json'))]
    
    print(f"After filtering, {len(valid_files)} documents will be processed")
    
    # Import files
    if args.dry_run:
        print("\nDRY RUN MODE - No documents will actually be imported")
    
    imported_count = import_files_to_store(doc_store, valid_files, args.dry_run)
    
    # Print final stats
    if not args.dry_run:
        print(f"\nImported {imported_count} documents")
        print("\nUpdated document store statistics:")
        print(json.dumps(doc_store.get_document_stats(), indent=2))
    else:
        print(f"\nWould have imported {imported_count} documents")
    
    print("\nScan completed")
