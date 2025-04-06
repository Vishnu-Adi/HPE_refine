import os
import argparse
import json
import glob
from typing import List, Dict, Any
import logging
import time

from src.hpe_document_store import HPEDocumentStore
from pdf_document_handler import process_pdf_document

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PDFImporter")

def import_pdf_to_document_store(pdf_path: str, doc_store: HPEDocumentStore, doc_type: str = "financial") -> str:
    """
    Import a PDF document into the document store.
    
    Args:
        pdf_path: Path to the PDF file
        doc_store: The document store instance
        doc_type: Type of document (financial, product, press)
        
    Returns:
        Document ID if successful, None otherwise
    """
    logger.info(f"Processing PDF: {pdf_path}")
    
    # Process the PDF
    result = process_pdf_document(pdf_path)
    
    if "error" in result:
        logger.error(f"Error processing PDF: {result['error']}")
        return None
    
    # Extract text and metadata
    extracted_text = result["text"]
    metadata = result["metadata"]
    
    # Add source information to metadata
    metadata["source_file"] = os.path.basename(pdf_path)
    metadata["import_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Add to document store
    doc_id = doc_store.add_document(
        content=extracted_text,
        doc_type=doc_type,
        metadata=metadata
    )
    
    if doc_id:
        logger.info(f"Successfully imported PDF as document ID: {doc_id}")
    else:
        logger.error("Failed to import PDF into document store")
    
    return doc_id


def batch_import_pdfs(directory: str, doc_store: HPEDocumentStore, doc_type: str = None) -> Dict[str, Any]:
    """
    Import all PDF files from a directory.
    
    Args:
        directory: Directory containing PDF files
        doc_store: The document store instance
        doc_type: Type of document (if None, will try to determine)
        
    Returns:
        Dictionary with import statistics
    """
    if not os.path.exists(directory) or not os.path.isdir(directory):
        logger.error(f"Directory not found: {directory}")
        return {"error": "Directory not found", "imported": 0, "failed": 0}
    
    # Find all PDF files in directory
    pdf_files = glob.glob(os.path.join(directory, "*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {directory}")
        return {"imported": 0, "failed": 0, "message": "No PDF files found"}
    
    # Import each PDF
    imported = 0
    failed = 0
    imported_docs = []
    
    for pdf_path in pdf_files:
        # Determine document type if not specified
        if doc_type is None:
            path_lower = pdf_path.lower()
            if any(term in path_lower for term in ['financial', 'earnings', 'revenue', 'quarter', 'fiscal']):
                detected_type = "financial"
            elif any(term in path_lower for term in ['product', 'service', 'greenlake', 'offering']):
                detected_type = "product"
            elif any(term in path_lower for term in ['press', 'news', 'release', 'announcement']):
                detected_type = "press"
            else:
                detected_type = "financial"  # Default for this script
        else:
            detected_type = doc_type
        
        # Import the PDF
        doc_id = import_pdf_to_document_store(pdf_path, doc_store, detected_type)
        
        if doc_id:
            imported += 1
            imported_docs.append({
                "file": os.path.basename(pdf_path),
                "id": doc_id,
                "type": detected_type
            })
        else:
            failed += 1
    
    logger.info(f"Imported {imported} PDFs, {failed} failed")
    
    return {
        "imported": imported,
        "failed": failed,
        "documents": imported_docs
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import PDF documents into HPE Document Store")
    parser.add_argument("source", help="PDF file or directory containing PDFs")
    parser.add_argument("--type", choices=["financial", "product", "press"], 
                        help="Document type (if not specified, will try to determine)")
    
    args = parser.parse_args()
    
    print("HPE PDF Document Importer")
    print("========================")
    
    # Initialize document store
    doc_store = HPEDocumentStore()
    
    # Print initial stats
    print("\nInitial document store statistics:")
    print(json.dumps(doc_store.get_document_stats(), indent=2))
    
    # Process source (file or directory)
    if os.path.isdir(args.source):
        print(f"\nImporting PDFs from directory: {args.source}")
        result = batch_import_pdfs(args.source, doc_store, args.type)
        
        print(f"\nImported {result['imported']} PDFs, {result['failed']} failed")
        if result['imported'] > 0:
            print("\nImported documents:")
            for doc in result['documents']:
                print(f"  - {doc['file']} -> {doc['id']} ({doc['type']})")
    
    elif os.path.isfile(args.source) and args.source.lower().endswith('.pdf'):
        print(f"\nImporting single PDF: {args.source}")
        doc_id = import_pdf_to_document_store(args.source, doc_store, args.type or "financial")
        
        if doc_id:
            print(f"\nSuccessfully imported as document ID: {doc_id}")
        else:
            print("\nFailed to import PDF")
    
    else:
        print(f"\nError: {args.source} is not a PDF file or directory")
    
    # Print final stats
    print("\nFinal document store statistics:")
    print(json.dumps(doc_store.get_document_stats(), indent=2))
