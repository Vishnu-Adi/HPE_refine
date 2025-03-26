import os
import json
import hashlib
from datetime import datetime
import sys
from typing import Dict, Any, List, Tuple

def repair_document_index(hpe_docs_dir: str, verbose: bool = False) -> Tuple[int, int, int]:
    """
    Repair the document index by:
    1. Finding documents in the file system that aren't in the index
    2. Removing index entries for documents that don't exist
    3. Rebuilding the index if it's corrupted
    
    Args:
        hpe_docs_dir: Path to the HPE docs directory
        verbose: Print verbose output
        
    Returns:
        Tuple of (added_count, removed_count, total_docs)
    """
    if not os.path.exists(hpe_docs_dir):
        print(f"Error: HPE docs directory not found at {hpe_docs_dir}")
        return (0, 0, 0)
    
    index_path = os.path.join(hpe_docs_dir, "document_index.json")
    
    # Try to load the existing index
    document_index = {}
    if os.path.exists(index_path):
        try:
            with open(index_path, 'r') as f:
                document_index = json.load(f)
            if verbose:
                print(f"Loaded existing index with {len(document_index)} entries")
        except Exception as e:
            print(f"Error loading document index: {e}")
            print("Creating a new index")
            document_index = {}
    
    # Find subdirectories
    subdirs = [
        os.path.join(hpe_docs_dir, "financial"),
        os.path.join(hpe_docs_dir, "product"), 
        os.path.join(hpe_docs_dir, "press")
    ]
    
    # Make sure subdirectories exist
    for subdir in subdirs:
        if not os.path.exists(subdir):
            os.makedirs(subdir, exist_ok=True)
    
    # Find all document files
    all_files = []
    for root, dirs, files in os.walk(hpe_docs_dir):
        for file in files:
            if file.endswith('.txt') and not file == "document_index.json":
                filepath = os.path.join(root, file)
                all_files.append(filepath)
    
    if verbose:
        print(f"Found {len(all_files)} document files on disk")
    
    # Track document paths in the index
    indexed_paths = set()
    for doc_id, doc_info in document_index.items():
        indexed_paths.add(doc_info["path"])
    
    # Files that exist but aren't in the index
    missing_from_index = []
    for file_path in all_files:
        if file_path not in indexed_paths:
            missing_from_index.append(file_path)
    
    # Files in the index that don't exist
    missing_from_disk = []
    for doc_id, doc_info in list(document_index.items()):
        if not os.path.exists(doc_info["path"]):
            missing_from_disk.append(doc_id)
    
    if verbose:
        print(f"Found {len(missing_from_index)} files missing from index")
        print(f"Found {len(missing_from_disk)} index entries with missing files")
    
    # Add missing files to index
    added_count = 0
    for file_path in missing_from_index:
        try:
            # Determine document type from path
            if "/financial/" in file_path:
                doc_type = "financial"
            elif "/product/" in file_path:
                doc_type = "product"
            elif "/press/" in file_path:
                doc_type = "press"
            else:
                doc_type = "other"
            
            # Generate an ID
            with open(file_path, 'rb') as f:
                content = f.read()
                content_hash = hashlib.md5(content).hexdigest()
            
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            doc_id = f"{doc_type}_{timestamp}_{content_hash[:8]}"
            
            # Add to index
            document_index[doc_id] = {
                "path": file_path,
                "type": doc_type,
                "added": datetime.now().isoformat(),
                "metadata": {
                    "source": "auto_repair",
                    "repaired_at": datetime.now().isoformat()
                }
            }
            
            added_count += 1
            if verbose:
                print(f"Added {file_path} to index as {doc_id}")
        
        except Exception as e:
            print(f"Error adding {file_path} to index: {e}")
    
    # Remove missing files from index
    removed_count = 0
    for doc_id in missing_from_disk:
        if doc_id in document_index:
            if verbose:
                print(f"Removing {doc_id} from index (file not found)")
            del document_index[doc_id]
            removed_count += 1
    
    # Save the repaired index
    try:
        with open(index_path, 'w') as f:
            json.dump(document_index, f, indent=2)
        print(f"Saved repaired index with {len(document_index)} entries")
    except Exception as e:
        print(f"Error saving repaired index: {e}")
    
    return (added_count, removed_count, len(document_index))


if __name__ == "__main__":
    print("HPE Document Index Repair Utility")
    print("================================")
    
    # Determine the HPE docs directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    hpe_docs_dir = os.path.join(script_dir, "hpe_docs")
    
    # Check if verbose flag is set
    verbose = "--verbose" in sys.argv
    
    # Run the repair
    added, removed, total = repair_document_index(hpe_docs_dir, verbose)
    
    print(f"\nRepair summary:")
    print(f"- Added {added} missing documents to index")
    print(f"- Removed {removed} invalid entries from index")
    print(f"- Total documents in repaired index: {total}")
    
    if total == 0 and added == 0:
        print("\nWarning: No documents were found. Make sure you have documents in the hpe_docs directory.")
        print("You can add documents by:")
        print("1. Running the import command: python hpe_query_workflow.py import <filepath> --type financial")
        print("2. Using the scan_documents.py utility to scan directories for documents")
        print("3. Running the interactive mode and using the 'import' command")
    
    print("\nTo verify the repair worked, run:")
    print("python hpe_query_workflow.py stats")
