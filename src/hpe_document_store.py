import os
import json
import re
from datetime import datetime
import hashlib
import logging
from typing import List, Dict, Any, Optional

# Try to import the PDF handler
PDF_SUPPORT = False
try:
    from pdf_document_handler import process_pdf_document
    PDF_SUPPORT = True
except ImportError:
    pass  # PDF support will be disabled if the handler is not available

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("HPEDocStore")

class HPEDocumentStore:
    """
    Manages a collection of HPE documents for use in query refinement and RAG workflows.
    Documents can be financial reports, press releases, product documentation, etc.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the document store.
        
        Args:
            data_dir: Directory to store document data. Defaults to "hpe_docs" in the current directory.
        """
        if data_dir is None:
            # Use a default directory in the current path
            self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hpe_docs")
        else:
            self.data_dir = data_dir
            
        # Create directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create subdirectories for different document types
        self.financial_dir = os.path.join(self.data_dir, "financial")
        self.product_dir = os.path.join(self.data_dir, "product")
        self.press_dir = os.path.join(self.data_dir, "press")
        
        for directory in [self.financial_dir, self.product_dir, self.press_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Load document index if it exists
        self.index_path = os.path.join(self.data_dir, "document_index.json")
        self.document_index = self._load_index()
        
        logger.info(f"Initialized HPE Document Store at {self.data_dir}")
        logger.info(f"Document index contains {len(self.document_index)} documents")
    
    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load document index from disk or create a new one if it doesn't exist."""
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading document index: {e}")
                return {}
        return {}
    
    def _save_index(self) -> None:
        """Save document index to disk."""
        try:
            with open(self.index_path, 'w') as f:
                json.dump(self.document_index, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving document index: {e}")
    
    def add_document(self, 
                     content: str, 
                     doc_type: str = "financial", 
                     metadata: Dict[str, Any] = None,
                     doc_id: str = None) -> str:
        """
        Add a document to the store.
        
        Args:
            content: The document content
            doc_type: Type of document (financial, product, press)
            metadata: Additional metadata about the document
            doc_id: Optional document ID. If not provided, one will be generated.
            
        Returns:
            The document ID
        """
        if metadata is None:
            metadata = {}
        
        # Generate document ID if not provided
        if doc_id is None:
            content_hash = hashlib.md5(content.encode()).hexdigest()
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            doc_id = f"{doc_type}_{timestamp}_{content_hash[:8]}"
        
        # Determine document directory based on type
        if doc_type == "financial":
            doc_dir = self.financial_dir
        elif doc_type == "product":
            doc_dir = self.product_dir
        elif doc_type == "press":
            doc_dir = self.press_dir
        else:
            doc_dir = self.data_dir
        
        # Save document content
        doc_path = os.path.join(doc_dir, f"{doc_id}.txt")
        try:
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Error saving document content: {e}")
            return None
        
        # Add to index
        self.document_index[doc_id] = {
            "path": doc_path,
            "type": doc_type,
            "added": datetime.now().isoformat(),
            "metadata": metadata
        }
        
        # Save updated index
        self._save_index()
        
        logger.info(f"Added document {doc_id} of type {doc_type}")
        return doc_id
    
    def add_document_from_file(self, file_path: str, doc_type: str = None, metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Add a document from a file (supports PDF and text files).
        
        Args:
            file_path: Path to the file
            doc_type: Type of document (financial, product, press)
            metadata: Additional metadata
            
        Returns:
            Document ID if successful, None otherwise
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
            
        if metadata is None:
            metadata = {}
            
        # Add file metadata
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        metadata["source_file"] = filename
        metadata["file_size"] = file_size
        
        # Handle PDF files
        if file_path.lower().endswith('.pdf'):
            if not PDF_SUPPORT:
                logger.error("PDF support not available. Install pdf_document_handler dependencies.")
                return None
                
            # Process PDF using the handler
            try:
                pdf_result = process_pdf_document(file_path)
                
                if "error" in pdf_result:
                    logger.error(f"Error processing PDF: {pdf_result['error']}")
                    return None
                    
                # Extract text and merge metadata
                content = pdf_result["text"]
                pdf_metadata = pdf_result.get("metadata", {})
                metadata.update(pdf_metadata)
                
                # Determine document type if not specified
                if doc_type is None:
                    if "quarter" in metadata or "fiscal_year" in metadata:
                        doc_type = "financial"
                    elif "product" in metadata:
                        doc_type = "product"
                    else:
                        doc_type = "financial"  # Default for this operation
                
                # Add to store
                return self.add_document(content, doc_type, metadata)
            
            except Exception as e:
                logger.error(f"Error adding PDF document: {e}")
                return None
        
        # Handle text files
        else:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Determine document type if not specified
                if doc_type is None:
                    path_lower = file_path.lower()
                    if any(term in path_lower for term in ['financial', 'earnings', 'revenue']):
                        doc_type = "financial"
                    elif any(term in path_lower for term in ['product', 'service', 'greenlake']):
                        doc_type = "product"
                    elif any(term in path_lower for term in ['press', 'news', 'release']):
                        doc_type = "press"
                    else:
                        doc_type = "other"
                
                # Add to store
                return self.add_document(content, doc_type, metadata)
            
            except Exception as e:
                logger.error(f"Error adding text document: {e}")
                return None
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID.
        
        Args:
            doc_id: The document ID
            
        Returns:
            A dictionary with document content and metadata
        """
        if doc_id not in self.document_index:
            logger.warning(f"Document {doc_id} not found in index")
            return None
        
        doc_info = self.document_index[doc_id]
        doc_path = doc_info["path"]
        
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "id": doc_id,
                "content": content,
                "type": doc_info["type"],
                "metadata": doc_info["metadata"],
                "added": doc_info["added"]
            }
        except Exception as e:
            logger.error(f"Error reading document {doc_id}: {e}")
            return None
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the store.
        
        Args:
            doc_id: The document ID
            
        Returns:
            True if successfully deleted, False otherwise
        """
        if doc_id not in self.document_index:
            logger.warning(f"Document {doc_id} not found in index")
            return False
        
        doc_path = self.document_index[doc_id]["path"]
        
        # Delete file
        try:
            if os.path.exists(doc_path):
                os.remove(doc_path)
        except Exception as e:
            logger.error(f"Error deleting document file {doc_id}: {e}")
            return False
        
        # Remove from index
        del self.document_index[doc_id]
        self._save_index()
        
        logger.info(f"Deleted document {doc_id}")
        return True
    
    def search_documents(self, query: str, doc_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Simple keyword search across documents.
        
        Args:
            query: The search query
            doc_type: Optional filter by document type
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        results = []
        search_terms = query.lower().split()
        
        # For each document in the index
        for doc_id, doc_info in self.document_index.items():
            # Filter by type if specified
            if doc_type and doc_info["type"] != doc_type:
                continue
            
            # Load document content
            doc = self.get_document(doc_id)
            if not doc:
                continue
            
            content = doc["content"].lower()
            
            # Simple matching algorithm - count term occurrences
            score = sum(content.count(term) for term in search_terms)
            
            if score > 0:
                results.append({
                    "id": doc_id,
                    "score": score,
                    "content": doc["content"][:200] + "...",  # Preview
                    "type": doc["type"],
                    "metadata": doc["metadata"]
                })
        
        # Sort by score and limit results
        sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
        return sorted_results[:limit]
    
    def get_documents_by_type(self, doc_type: str) -> List[Dict[str, Any]]:
        """
        Get all documents of a specific type.
        
        Args:
            doc_type: The document type
            
        Returns:
            List of documents
        """
        results = []
        
        for doc_id, doc_info in self.document_index.items():
            if doc_info["type"] == doc_type:
                doc = self.get_document(doc_id)
                if doc:
                    results.append(doc)
        
        return results

    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about the document store."""
        stats = {
            "total_documents": len(self.document_index),
            "by_type": {
                "financial": 0,
                "product": 0,
                "press": 0,
                "other": 0
            }
        }
        
        for doc_info in self.document_index.values():
            doc_type = doc_info.get("type", "other")
            if doc_type in stats["by_type"]:
                stats["by_type"][doc_type] += 1
            else:
                stats["by_type"]["other"] += 1
        
        return stats


# Example usage
if __name__ == "__main__":
    store = HPEDocumentStore()
    
    # Print if PDF support is available
    if PDF_SUPPORT:
        print("PDF support is enabled.")
    else:
        print("PDF support is not available. Install pypdf to enable it.")
    
    # Add some example documents
    financial_example = """
    HPE Q3 FY24 Financial Results:
    Annual Recurring Revenue (ARR): $1.7 billion, up 33% from prior year
    GreenLake cloud services orders: $2.5 billion, up 22% from prior year
    Revenue: $7.2 billion, up 5% from prior year
    """
    
    product_example = """
    HPE GreenLake for Private Cloud Enterprise:
    A complete as-a-service platform that brings the cloud experience to applications and data everywhere
    with automated, absorbable, pay-per-use services for VMs, containers, and bare metal.
    """
    
    # Check for PDF files in the financial directory
    financial_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hpe_docs/financial")
    pdf_files = [f for f in os.listdir(financial_dir) if f.lower().endswith('.pdf')] if os.path.exists(financial_dir) else []
    
    if pdf_files and PDF_SUPPORT:
        print(f"Found {len(pdf_files)} PDF files in financial directory. Would you like to import them? (y/n)")
        response = input().lower()
        if response == 'y':
            for pdf_file in pdf_files:
                pdf_path = os.path.join(financial_dir, pdf_file)
                print(f"Importing {pdf_file}...")
                doc_id = store.add_document_from_file(pdf_path, "financial")
                if doc_id:
                    print(f"  Imported as document ID: {doc_id}")
                else:
                    print(f"  Failed to import")
    
    # Add text examples
    store.add_document(
        content=financial_example,
        doc_type="financial",
        metadata={"quarter": "Q3", "fiscal_year": "2024", "report_type": "earnings"}
    )
    
    store.add_document(
        content=product_example,
        doc_type="product",
        metadata={"product": "GreenLake", "category": "cloud"}
    )
    
    # Print statistics
    print(json.dumps(store.get_document_stats(), indent=2))
    
    # Search for documents
    results = store.search_documents("ARR revenue")
    for result in results:
        print(f"Document ID: {result['id']}")
        print(f"Score: {result['score']}")
        print(f"Preview: {result['content']}")
        print("-" * 50)
