import os
import json
import argparse
import logging
from typing import List, Dict, Any, Tuple
import time

from hpe_document_store import HPEDocumentStore
from hpe_rag_query_refiner import HPERAGQueryRefiner

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PDFAccuracyTest")

class PDFAccuracyTester:
    """
    Tests the accuracy of information extracted from PDF documents
    by running specific queries that target known information in the documents.
    """
    
    def __init__(self):
        """Initialize the accuracy tester."""
        self.doc_store = HPEDocumentStore()
        self.refiner = HPERAGQueryRefiner(doc_store=self.doc_store)
        
        # Get document stats
        self.stats = self.doc_store.get_document_stats()
        logger.info(f"Document store has {self.stats['total_documents']} documents")
        
        # Check for financial documents
        if self.stats["by_type"].get("financial", 0) == 0:
            logger.warning("No financial documents found. Please import some financial PDFs first.")
    
    def build_test_queries(self) -> List[Dict[str, Any]]:
        """
        Build a list of test queries based on available documents.
        Each query includes expected information to look for in the refined result.
        
        Returns:
            List of test query objects
        """
        test_queries = []
        
        # Get all financial documents
        financial_docs = self.doc_store.get_documents_by_type("financial")
        
        # For each document, create targeted queries
        for doc in financial_docs:
            doc_id = doc["id"]
            metadata = doc["metadata"]
            
            # Build queries based on metadata
            if "fiscal_year" in metadata:
                fiscal_year = metadata["fiscal_year"]
                
                # Financial performance query
                test_queries.append({
                    "query": f"What were HPE's financial results in FY{fiscal_year}?",
                    "expected_terms": [fiscal_year, "revenue", "growth"],
                    "document_id": doc_id
                })
            
            if "quarter" in metadata and "fiscal_year" in metadata:
                quarter = metadata["quarter"]
                fiscal_year = metadata["fiscal_year"]
                
                # Quarterly performance query
                test_queries.append({
                    "query": f"What was HPE's performance in {quarter} {fiscal_year}?",
                    "expected_terms": [quarter, fiscal_year, "revenue"],
                    "document_id": doc_id
                })
            
            # Check for specific business segments
            if metadata.get("contains_greenlake", False):
                test_queries.append({
                    "query": "How is HPE's GreenLake business performing?",
                    "expected_terms": ["GreenLake", "as-a-service", "growth"],
                    "document_id": doc_id
                })
            
            if metadata.get("contains_intelligent_edge", False):
                test_queries.append({
                    "query": "What is the revenue for HPE's Intelligent Edge segment?",
                    "expected_terms": ["Intelligent Edge", "revenue", "growth"],
                    "document_id": doc_id
                })
            
            if metadata.get("contains_hpc", False):
                test_queries.append({
                    "query": "How is HPE's HPC & AI business segment performing?",
                    "expected_terms": ["HPC", "AI", "revenue"],
                    "document_id": doc_id
                })
            
            # Add a few generic financial queries
            if metadata.get("contains_arr", False):
                test_queries.append({
                    "query": "What is HPE's ARR?",
                    "expected_terms": ["ARR", "recurring", "revenue"],
                    "document_id": doc_id
                })
        
        # Add some generic queries that don't target specific documents
        test_queries.extend([
            {
                "query": "What was HPE's revenue in the last fiscal year?",
                "expected_terms": ["revenue", "billion", "fiscal"],
                "document_id": None
            },
            {
                "query": "How much did GreenLake revenue grow?",
                "expected_terms": ["GreenLake", "growth", "percent"],
                "document_id": None
            },
            {
                "query": "What is HPE's dividend policy?",
                "expected_terms": ["dividend", "capital", "shareholders"],
                "document_id": None
            }
        ])
        
        return test_queries
    
    def run_accuracy_test(self, test_queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run the accuracy test on a set of test queries.
        
        Args:
            test_queries: List of test query objects
            
        Returns:
            List of test results
        """
        results = []
        
        for i, test in enumerate(test_queries, 1):
            query = test["query"]
            expected_terms = test["expected_terms"]
            
            logger.info(f"Running test {i}/{len(test_queries)}: {query}")
            
            try:
                # Refine the query
                start_time = time.time()
                refinement_result = self.refiner.refine_query(query, use_rag=True)
                end_time = time.time()
                
                refined_query = refinement_result["refined_query"]
                processing_time = end_time - start_time
                
                # Check for expected terms in refined query
                term_matches = []
                for term in expected_terms:
                    if term.lower() in refined_query.lower():
                        term_matches.append(term)
                
                accuracy = len(term_matches) / len(expected_terms) if expected_terms else 0
                
                # Store the results
                result = {
                    "original_query": query,
                    "refined_query": refined_query,
                    "expected_terms": expected_terms,
                    "matched_terms": term_matches,
                    "accuracy": accuracy,
                    "processing_time": processing_time,
                    "document_id": test.get("document_id")
                }
                
                results.append(result)
                
                logger.info(f"Accuracy: {accuracy:.2f} ({len(term_matches)}/{len(expected_terms)} terms)")
                
                # Pause briefly between queries
                if i < len(test_queries):
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
                results.append({
                    "original_query": query,
                    "error": str(e),
                    "expected_terms": expected_terms,
                    "matched_terms": [],
                    "accuracy": 0,
                    "processing_time": 0,
                    "document_id": test.get("document_id")
                })
        
        return results
    
    def generate_accuracy_report(self, results: List[Dict[str, Any]], output_file: str = None) -> str:
        """
        Generate a report on accuracy test results.
        
        Args:
            results: The test results
            output_file: Optional file to save the report to
            
        Returns:
            Report text
        """
        # Calculate statistics
        total_tests = len(results)
        successful_tests = sum(1 for r in results if "error" not in r)
        failed_tests = total_tests - successful_tests
        
        total_accuracy = sum(r.get("accuracy", 0) for r in results) / total_tests if total_tests > 0 else 0
        avg_processing_time = sum(r.get("processing_time", 0) for r in results) / total_tests if total_tests > 0 else 0
        
        # Build the report
        report = []
        report.append("# HPE PDF Document Accuracy Test Report")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Model: {self.refiner.model_name}")
        report.append("")
        
        report.append("## Summary")
        report.append(f"- Total Tests: {total_tests}")
        report.append(f"- Successful Tests: {successful_tests}")
        report.append(f"- Failed Tests: {failed_tests}")
        report.append(f"- Average Accuracy: {total_accuracy:.2f} (0-1 scale)")
        report.append(f"- Average Processing Time: {avg_processing_time:.2f} seconds")
        report.append("")
        
        report.append("## Document Statistics")
        report.append(f"- Total Documents: {self.stats['total_documents']}")
        for doc_type, count in self.stats["by_type"].items():
            report.append(f"- {doc_type.capitalize()}: {count}")
        report.append("")
        
        report.append("## Detailed Results")
        for i, result in enumerate(results, 1):
            report.append(f"### Test {i}")
            report.append(f"- Original Query: {result.get('original_query', 'N/A')}")
            
            if "error" in result:
                report.append(f"- Error: {result['error']}")
            else:
                report.append(f"- Refined Query: {result.get('refined_query', 'N/A')}")
                report.append(f"- Expected Terms: {', '.join(result.get('expected_terms', []))}")
                report.append(f"- Matched Terms: {', '.join(result.get('matched_terms', []))}")
                report.append(f"- Accuracy: {result.get('accuracy', 0):.2f}")
            
            report.append(f"- Processing Time: {result.get('processing_time', 0):.2f} seconds")
            
            if result.get("document_id"):
                report.append(f"- Target Document: {result['document_id']}")
            
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test PDF Document Accuracy")
    parser.add_argument("--output", "-o", help="Output file for the report")
    parser.add_argument("--limit", "-l", type=int, help="Limit the number of test queries to run")
    
    args = parser.parse_args()
    
    # Set output file
    output_file = args.output
    if not output_file:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"pdf_accuracy_report_{timestamp}.md"
    
    # Initialize the tester
    tester = PDFAccuracyTester()
    
    # Build test queries
    test_queries = tester.build_test_queries()
    
    # Apply limit if specified
    if args.limit and args.limit > 0:
        test_queries = test_queries[:args.limit]
    
    print(f"Running {len(test_queries)} accuracy tests...")
    
    # Run the tests
    results = tester.run_accuracy_test(test_queries)
    
    # Generate the report
    report = tester.generate_accuracy_report(results, output_file)
    
    print(f"\nTest complete. Report saved to {output_file}")
