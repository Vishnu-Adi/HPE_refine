import argparse
import sys
import os
import time
import json
import logging
from typing import List, Dict, Any

from hpe_document_store import HPEDocumentStore
from hpe_rag_query_refiner import HPERAGQueryRefiner

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hpe_query_workflow.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("HPEQueryWorkflow")

class HPEQueryWorkflow:
    """
    Complete workflow for HPE query processing:
    1. Document management (import, organize)
    2. Query refinement using RAG techniques
    3. CLI interface for interactive use
    """
    
    def __init__(self):
        """Initialize the workflow components."""
        # Initialize document store
        self.doc_store = HPEDocumentStore()
        
        # Initialize RAG query refiner
        self.query_refiner = HPERAGQueryRefiner(doc_store=self.doc_store)
        
        logger.info("HPE Query Workflow initialized")
        logger.info(f"Document store has {self.doc_store.get_document_stats()['total_documents']} documents")
    
    def import_document(self, filepath: str, doc_type: str, metadata: Dict[str, Any] = None) -> str:
        """
        Import a document from a file.
        
        Args:
            filepath: Path to the document file
            doc_type: Type of document (financial, product, press)
            metadata: Additional metadata
            
        Returns:
            Document ID if successful, None otherwise
        """
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            doc_id = self.doc_store.add_document(
                content=content,
                doc_type=doc_type,
                metadata=metadata or {}
            )
            
            logger.info(f"Imported document {filepath} as {doc_id}")
            return doc_id
        
        except Exception as e:
            logger.error(f"Error importing document {filepath}: {e}")
            return None
    
    def process_query(self, query: str, use_rag: bool = True) -> Dict[str, Any]:
        """
        Process a user query through the workflow.
        
        Args:
            query: The user query
            use_rag: Whether to use RAG techniques
            
        Returns:
            Result dictionary with refined query and processing info
        """
        logger.info(f"Processing query: {query}")
        
        start_time = time.time()
        result = self.query_refiner.refine_query(query, use_rag=use_rag)
        end_time = time.time()
        
        result["processing_time"] = end_time - start_time
        
        logger.info(f"Query processed in {result['processing_time']:.2f} seconds")
        logger.info(f"Original: {query}")
        logger.info(f"Refined: {result['refined_query']}")
        
        return result
    
    def run_cli(self):
        """Run an interactive CLI for the workflow."""
        print("\n" + "="*80)
        print("HPE QUERY WORKFLOW - INTERACTIVE MODE")
        print("="*80 + "\n")
        
        print("Document store statistics:")
        print(json.dumps(self.doc_store.get_document_stats(), indent=2))
        print("\nType 'exit' or 'quit' to end the session.")
        print("Type 'import' to import a document.")
        print("Type 'stats' to see document statistics.")
        print("Type 'help' for more commands.")
        print("\nEnter your query when ready...\n")
        
        while True:
            try:
                user_input = input("\nQuery> ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    break
                
                elif user_input.lower() == 'help':
                    print("\nAvailable commands:")
                    print("  exit, quit - End the session")
                    print("  import - Import a document")
                    print("  stats - Show document statistics")
                    print("  search <keywords> - Search for documents")
                    print("  norag <query> - Process query without RAG")
                    print("  <query> - Process a regular query with RAG")
                
                elif user_input.lower() == 'import':
                    filepath = input("Document filepath: ").strip()
                    doc_type = input("Document type (financial, product, press): ").strip()
                    
                    metadata = {}
                    print("Enter metadata (empty line to finish):")
                    while True:
                        meta_input = input("  key=value: ").strip()
                        if not meta_input:
                            break
                        
                        if '=' in meta_input:
                            key, value = meta_input.split('=', 1)
                            metadata[key.strip()] = value.strip()
                    
                    doc_id = self.import_document(filepath, doc_type, metadata)
                    if doc_id:
                        print(f"Document imported successfully. ID: {doc_id}")
                    else:
                        print("Document import failed.")
                
                elif user_input.lower() == 'stats':
                    print("\nDocument store statistics:")
                    print(json.dumps(self.doc_store.get_document_stats(), indent=2))
                
                elif user_input.lower().startswith('search '):
                    keywords = user_input[7:].strip()
                    results = self.doc_store.search_documents(keywords)
                    
                    print(f"\nSearch results for '{keywords}':")
                    if results:
                        for i, result in enumerate(results, 1):
                            print(f"{i}. Document: {result['id']} (Score: {result['score']})")
                            print(f"   Type: {result['type']}")
                            print(f"   Preview: {result['content']}")
                            print()
                    else:
                        print("No matching documents found.")
                
                elif user_input.lower().startswith('norag '):
                    query = user_input[6:].strip()
                    print("\nProcessing without RAG...")
                    result = self.process_query(query, use_rag=False)
                    
                    print(f"\nOriginal Query: {result['original_query']}")
                    print(f"Refined Query : {result['refined_query']}")
                    print(f"Processing Time: {result['processing_time']:.2f} seconds")
                
                elif user_input:
                    # Process as a regular query
                    result = self.process_query(user_input)
                    
                    print(f"\nOriginal Query: {result['original_query']}")
                    print(f"Refined Query : {result['refined_query']}")
                    print(f"Used RAG      : {result['used_rag']}")
                    
                    if 'context_length' in result:
                        print(f"Context Length: {result['context_length']} characters")
                    
                    print(f"Processing Time: {result['processing_time']:.2f} seconds")
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            
            except Exception as e:
                print(f"Error: {e}")
        
        print("\nThank you for using the HPE Query Workflow!")


def run_from_cli():
    """Run the workflow from command line arguments."""
    parser = argparse.ArgumentParser(description="HPE Query Workflow")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Interactive mode
    interactive_parser = subparsers.add_parser("interactive", help="Run in interactive mode")
    
    # Query refinement
    query_parser = subparsers.add_parser("query", help="Refine a query")
    query_parser.add_argument("query", help="The query to refine")
    query_parser.add_argument("--no-rag", action="store_true", help="Disable RAG")
    
    # Import document
    import_parser = subparsers.add_parser("import", help="Import a document")
    import_parser.add_argument("filepath", help="Path to the document file")
    import_parser.add_argument("--type", default="financial", help="Document type")
    import_parser.add_argument("--metadata", action="append", help="Metadata in key=value format")
    
    # Stats
    subparsers.add_parser("stats", help="Show document statistics")
    
    # Search
    search_parser = subparsers.add_parser("search", help="Search for documents")
    search_parser.add_argument("keywords", help="Keywords to search for")
    
    args = parser.parse_args()
    
    workflow = HPEQueryWorkflow()
    
    if args.command == "interactive" or not args.command:
        workflow.run_cli()
    
    elif args.command == "query":
        result = workflow.process_query(args.query, use_rag=not args.no_rag)
        print(f"Original Query: {result['original_query']}")
        print(f"Refined Query : {result['refined_query']}")
        print(f"Used RAG      : {result['used_rag']}")
        print(f"Processing Time: {result['processing_time']:.2f} seconds")
    
    elif args.command == "import":
        metadata = {}
        if args.metadata:
            for meta_item in args.metadata:
                if '=' in meta_item:
                    key, value = meta_item.split('=', 1)
                    metadata[key.strip()] = value.strip()
        
        doc_id = workflow.import_document(args.filepath, args.type, metadata)
        if doc_id:
            print(f"Document imported successfully. ID: {doc_id}")
        else:
            print("Document import failed.")
    
    elif args.command == "stats":
        print(json.dumps(workflow.doc_store.get_document_stats(), indent=2))
    
    elif args.command == "search":
        results = workflow.doc_store.search_documents(args.keywords)
        print(f"Search results for '{args.keywords}':")
        if results:
            for i, result in enumerate(results, 1):
                print(f"{i}. Document: {result['id']} (Score: {result['score']})")
                print(f"   Type: {result['type']}")
                print(f"   Preview: {result['content']}")
                print()
        else:
            print("No matching documents found.")


if __name__ == "__main__":
    run_from_cli()
