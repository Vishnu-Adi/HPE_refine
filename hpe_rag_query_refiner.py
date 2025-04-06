import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
import logging
from typing import List, Dict, Any, Optional

from hpe_document_store import HPEDocumentStore

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("HPEQueryRefiner")

class HPERAGQueryRefiner:
    """
    Enhanced HPE Query Refiner using Retrieval Augmented Generation (RAG) techniques
    to leverage HPE-specific knowledge for better query refinement.
    """
    
    def __init__(self, 
                 api_key: str = None, 
                 model_name: str = "gemini-1.5-flash",
                 doc_store: HPEDocumentStore = None):
        """
        Initialize the RAG Query Refiner.
        
        Args:
            api_key: Gemini API key (optional, will load from environment if None)
            model_name: The Gemini model to use
            doc_store: Document store instance (will create a new one if None)
        """
        load_dotenv()
        
        # Set up API key
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Gemini API key not provided and not found in environment")
        
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Initialize model
        try:
            self.model = genai.GenerativeModel(model_name=model_name)
            self.model_name = model_name
            logger.info(f"Initialized model: {model_name}")
        except Exception as e:
            logger.error(f"Error initializing model {model_name}: {e}")
            logger.info("Falling back to gemini-1.0-pro model")
            self.model = genai.GenerativeModel("gemini-1.0-pro")
            self.model_name = "gemini-1.0-pro"
        
        # Set up document store
        if doc_store is None:
            self.doc_store = HPEDocumentStore()
        else:
            self.doc_store = doc_store
    
    def retrieve_relevant_context(self, query: str, max_docs: int = 3) -> str:
        """
        Retrieve relevant context from the document store for the query.
        
        Args:
            query: The user query
            max_docs: Maximum number of documents to retrieve
            
        Returns:
            Relevant context as a string
        """
        results = self.doc_store.search_documents(query, limit=max_docs)
        
        if not results:
            logger.info("No relevant documents found for context")
            return ""
        
        # Extract content from results
        context_parts = []
        for result in results:
            # Get full document content
            doc = self.doc_store.get_document(result["id"])
            if doc:
                # Add metadata
                meta_str = ", ".join([f"{k}: {v}" for k, v in doc["metadata"].items()])
                context_parts.append(f"Document ({meta_str}):\n{doc['content']}\n")
        
        return "\n".join(context_parts)
    
    def refine_query(self, user_query: str, use_rag: bool = True) -> Dict[str, Any]:
        """
        Refine a user query, optionally using RAG techniques.
        
        Args:
            user_query: The original user query
            use_rag: Whether to use RAG for enhanced refinement
            
        Returns:
            Dictionary containing refined query and optional context
        """
        # Retrieve relevant context if using RAG
        context = ""
        if use_rag:
            context = self.retrieve_relevant_context(user_query)
            logger.info(f"Retrieved context of length {len(context)}")
        
        # Determine which prompt to use based on available context
        if context:
            prompt = self._create_rag_prompt(user_query, context)
        else:
            prompt = self._create_basic_prompt(user_query)
        
        # Generate refined query
        try:
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.1,
                            "max_output_tokens": 150,
                            "top_p": 0.95,
                        }
                    )
                    
                    # Extract and clean the refined query
                    refined_query = response.text.strip()
                    refined_query = refined_query.strip('"\'')
                    
                    return {
                        "original_query": user_query,
                        "refined_query": refined_query,
                        "used_rag": use_rag and bool(context),
                        "context_length": len(context)
                    }
                
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"Error after {max_retries} attempts: {e}")
                        return {
                            "original_query": user_query,
                            "refined_query": user_query,  # Return original as fallback
                            "used_rag": False,
                            "error": str(e)
                        }
                    
                    logger.warning(f"Attempt {retry_count} failed: {e}. Retrying in 2 seconds...")
                    time.sleep(2)
        
        except Exception as e:
            logger.error(f"Error during query refinement: {e}")
            return {
                "original_query": user_query,
                "refined_query": user_query,
                "used_rag": False,
                "error": str(e)
            }
    
    def _create_basic_prompt(self, user_query: str) -> str:
        """Create a prompt for basic query refinement that outputs a single line refined query."""
        return f"""
        Transform ambiguous user queries into precise, contextual questions in a single line.
        Example: "HPE ARR Q3 2024" → "What is the Annual Recurring Revenue of HPE in the third quarter of 2024?"
        Original Query: "{user_query}"
        Refined Query (ONLY provide a single line refined query, no explanations):
        """
    
    def _create_rag_prompt(self, user_query: str, context: str) -> str:
        """Create a prompt for RAG-enhanced query refinement that outputs a single line refined query."""
        return f"""
        Using the relevant context provided below, transform the ambiguous user query into a single line, precise, and contextual question.
        Example: "HPE ARR Q3 2024" → "What is the Annual Recurring Revenue of HPE in the third quarter of 2024?"
        Relevant Context:
        {context}
        Original Query: "{user_query}"
        Refined Query (ONLY provide a single line refined query, no explanations):
        """


# Example usage
if __name__ == "__main__":
    # Initialize the document store and add some example documents
    doc_store = HPEDocumentStore()
    
    # Check if document store is empty and add example documents if needed
    if doc_store.get_document_stats()["total_documents"] == 0:
        # Add some HPE financial documents
        doc_store.add_document(
            content=""" 
            HPE Q3 FY24 Financial Results Summary:
            - Annual Recurring Revenue (ARR): $1.7 billion, up 33% from prior year
            - GreenLake cloud services orders: $2.5 billion, up 22% from prior year
            - Total Revenue: $7.2 billion, up 5% from prior year
            - Intelligent Edge revenue: $1.3 billion, up 8% from prior year
            - Compute revenue: $3.2 billion, up 4% from prior year
            - HPC & AI revenue: $840 million, up 26% from prior year
            - Storage revenue: $1.1 billion, down 3% from prior year
            """,
            doc_type="financial",
            metadata={"quarter": "Q3", "fiscal_year": "2024", "report_type": "earnings"}
        )
        
        doc_store.add_document(
            content="""
            HPE GreenLake Cloud Services Platform:
            HPE GreenLake is a cloud services platform that brings the cloud experience to apps and data everywhere.
            It delivers a consistent cloud operating model for all applications and data, with the benefits of cloud efficiency,
            agility, and simplified IT operations. GreenLake services include compute, storage, database, containers,
            data protection, and more, delivered as a service in your environment with pay-per-use billing.
            """,
            doc_type="product",
            metadata={"product": "GreenLake", "category": "cloud"}
        )
        
        doc_store.add_document(
            content="""
            HPE Segment Reorganization - FY2023:
            In 2023, HPE merged its HPC business with its AI initiatives and Compute business to form the new HPC & AI segment.
            This change reflects HPE's strategic focus on AI-native solutions and high-performance computing capabilities.
            The reorganization aims to better position HPE in the rapidly growing AI infrastructure market.
            """,
            doc_type="press",
            metadata={"topic": "reorganization", "year": "2023"}
        )
    
    # Initialize the RAG query refiner
    refiner = HPERAGQueryRefiner(doc_store=doc_store)
    
    # Test queries
    test_queries = [
        "HPE ARR Q3 2024",
        "which quarter has highest ARR Global",
        "How was HPE's performance compared to prior year",
        "why did HPE's arr grow in q3 2024",
        "When HPC & Al merged compute server segment",
        "tell me about hpe greenlake service",
    ]
    
    print("\n" + "="*80)
    print(f"HPE RAG QUERY REFINEMENT USING {refiner.model_name.upper()}")
    print("="*80 + "\n")
    
    for idx, query in enumerate(test_queries, 1):
        print(f"\n{idx}. ORIGINAL: {query}")
        
        try:
            start_time = time.time()
            result = refiner.refine_query(query)
            end_time = time.time()
            
            print(f"   REFINED : {result['refined_query']}")
            print(f"   USED RAG: {result['used_rag']}")
            if 'context_length' in result:
                print(f"   CONTEXT : {result['context_length']} characters")
            print(f"   TIME    : {(end_time - start_time):.2f} seconds")
        except Exception as e:
            print(f"   ERROR   : {e}")
        
        print("-" * 80)
