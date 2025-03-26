import json
import time
import os
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any

from hpe_rag_query_refiner import HPERAGQueryRefiner
from hpe_document_store import HPEDocumentStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("query_tests.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("QueryTests")

class QueryTester:
    """
    Runs a battery of test queries against the HPE document database
    and evaluates the performance of the query refinement system.
    """
    
    def __init__(self, use_rag: bool = True):
        """
        Initialize the query tester.
        
        Args:
            use_rag: Whether to use RAG for query refinement
        """
        self.doc_store = HPEDocumentStore()
        self.refiner = HPERAGQueryRefiner(doc_store=self.doc_store)
        self.use_rag = use_rag
        
        # Check if we have documents
        stats = self.doc_store.get_document_stats()
        logger.info(f"Document store has {stats['total_documents']} documents")
        
        if stats['total_documents'] == 0:
            logger.warning("No documents found in store. Results may be limited.")
    
    def run_test_query(self, query: str) -> Dict[str, Any]:
        """
        Run a single test query and return results.
        
        Args:
            query: The query to test
            
        Returns:
            Dictionary with test results
        """
        start_time = time.time()
        result = self.refiner.refine_query(query, use_rag=self.use_rag)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Add processing time to result
        result["processing_time"] = processing_time
        
        return result
    
    def run_test_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Run a batch of test queries.
        
        Args:
            queries: List of queries to test
            
        Returns:
            List of test results
        """
        results = []
        
        for i, query in enumerate(queries, 1):
            logger.info(f"Running test query {i}/{len(queries)}: {query}")
            
            try:
                result = self.run_test_query(query)
                results.append(result)
                
                logger.info(f"Original: {query}")
                logger.info(f"Refined : {result['refined_query']}")
                logger.info(f"Time    : {result['processing_time']:.2f} seconds")
                
                # Pause briefly between queries to avoid rate limiting
                if i < len(queries):
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
                results.append({
                    "original_query": query,
                    "refined_query": query,
                    "error": str(e),
                    "processing_time": 0
                })
        
        return results
    
    def generate_report(self, results: List[Dict[str, Any]], output_file: str = None) -> str:
        """
        Generate a report of test results.
        
        Args:
            results: The test results
            output_file: Optional file to save the report to
            
        Returns:
            Report text
        """
        # Calculate statistics
        total_queries = len(results)
        successful_queries = sum(1 for r in results if "error" not in r)
        failed_queries = total_queries - successful_queries
        
        avg_time = sum(r.get("processing_time", 0) for r in results) / total_queries if total_queries > 0 else 0
        
        # Count how many used RAG
        rag_used = sum(1 for r in results if r.get("used_rag", False))
        
        # Build the report
        report = []
        report.append("# HPE Query Refinement Test Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"RAG Enabled: {self.use_rag}")
        report.append(f"Model: {self.refiner.model_name}")
        report.append("")
        
        report.append("## Summary")
        report.append(f"- Total Queries: {total_queries}")
        report.append(f"- Successful: {successful_queries}")
        report.append(f"- Failed: {failed_queries}")
        report.append(f"- Average Processing Time: {avg_time:.2f} seconds")
        report.append(f"- RAG Used: {rag_used}/{total_queries} queries")
        report.append("")
        
        report.append("## Detailed Results")
        for i, result in enumerate(results, 1):
            report.append(f"### Query {i}")
            report.append(f"- Original: {result.get('original_query', 'N/A')}")
            report.append(f"- Refined: {result.get('refined_query', 'N/A')}")
            
            if "error" in result:
                report.append(f"- Error: {result['error']}")
            
            report.append(f"- Processing Time: {result.get('processing_time', 0):.2f} seconds")
            report.append(f"- RAG Used: {result.get('used_rag', False)}")
            
            if "context_length" in result:
                report.append(f"- Context Length: {result['context_length']} characters")
            
            report.append("")
        
        report_text = "\n".join(report)
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, "w") as f:
                    f.write(report_text)
                logger.info(f"Report saved to {output_file}")
            except Exception as e:
                logger.error(f"Error saving report to {output_file}: {e}")
        
        return report_text


# Test query sets
FINANCIAL_QUERIES = [
    "What is the ARR growth in Q3 2024?",
    "How did HPE perform in the latest quarter?",
    "What is the revenue for Intelligent Edge business?",
    "What are the key financial metrics for HPE in fiscal 2023?",
    "How much did GreenLake revenue grow year over year?",
    "What was HPE's EPS in the latest reported quarter?",
    "How is the HPC & AI segment performing?",
    "What is the outlook for HPE's next fiscal year?",
    "What is the capital return strategy for HPE?",
    "How much cash did HPE generate in fiscal 2023?",
]

PRODUCT_QUERIES = [
    "What is HPE GreenLake?",
    "Tell me about HPE's Intelligent Edge offerings",
    "What AI solutions does HPE offer?",
    "How does HPE's as-a-service strategy work?",
    "What is HPE's position in the HPC market?",
]

COMPARATIVE_QUERIES = [
    "How does HPE compare to Dell in the server market?",
    "What is HPE's market share in networking vs Cisco?",
    "How does HPE's cloud strategy differ from AWS and Azure?",
    "Compare HPE's storage business to NetApp",
    "How does HPE's financial performance compare to industry peers?",
]

INFORMAL_QUERIES = [
    "hpe latest earnings",
    "greenlake revenue growth",
    "how much did hpe make last quarter",
    "intelligent edge business performance",
    "hpe stock buybacks",
]

AMBIGUOUS_QUERIES = [
    "HPE Q3 results",
    "HPE revenue",
    "HPE strategy",
    "HPE growth areas",
    "HPE challenges",
]


def get_all_test_queries() -> List[str]:
    """Get all test queries combined."""
    return (
        FINANCIAL_QUERIES + 
        PRODUCT_QUERIES + 
        COMPARATIVE_QUERIES + 
        INFORMAL_QUERIES + 
        AMBIGUOUS_QUERIES
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test HPE Query Refinement System")
    parser.add_argument("--no-rag", action="store_true", help="Disable RAG for testing")
    parser.add_argument("--output", "-o", help="Output file for the report")
    parser.add_argument("--category", "-c", choices=["all", "financial", "product", "comparative", "informal", "ambiguous"],
                        default="all", help="Query category to test")
    parser.add_argument("--limit", "-l", type=int, help="Limit the number of queries to run")
    parser.add_argument("--query", "-q", help="Run a specific query")
    
    args = parser.parse_args()
    
    # Determine which queries to run
    test_queries = []
    
    if args.query:
        test_queries = [args.query]
    else:
        if args.category == "all":
            test_queries = get_all_test_queries()
        elif args.category == "financial":
            test_queries = FINANCIAL_QUERIES
        elif args.category == "product":
            test_queries = PRODUCT_QUERIES
        elif args.category == "comparative":
            test_queries = COMPARATIVE_QUERIES
        elif args.category == "informal":
            test_queries = INFORMAL_QUERIES
        elif args.category == "ambiguous":
            test_queries = AMBIGUOUS_QUERIES
    
    # Apply limit if specified
    if args.limit and args.limit > 0:
        test_queries = test_queries[:args.limit]
    
    # Set output file
    output_file = args.output
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"query_test_report_{timestamp}.md"
    
    # Initialize and run the tests
    tester = QueryTester(use_rag=not args.no_rag)
    
    print(f"Running {len(test_queries)} test queries...")
    
    # Run the queries
    results = tester.run_test_queries(test_queries)
    
    # Generate the report
    report = tester.generate_report(results, output_file)
    
    print(f"\nTest complete. Report saved to {output_file}")
