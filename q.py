import google.generativeai as genai
from dotenv import load_dotenv
import os
import time

class HPEQueryRefiner:
    def __init__(self, api_key=None, model_name="gemini-1.5-flash"):
        """
        Initializes the HPE Query Refiner using Gemini API.
        Uses the free tier model by default.

        Args:
            api_key (str, optional): Gemini API key. If None, tries to load from environment.
            model_name (str): The Gemini model to use - free tier supports gemini-1.5-flash
        """
        load_dotenv()  # Load environment variables
        
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Gemini API key not provided and not found in environment variable 'GEMINI_API_KEY'.")
        
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Create the model
        try:
            self.model = genai.GenerativeModel(model_name=model_name)
            self.model_name = model_name
            print(f"Successfully initialized model: {model_name}")
        except Exception as e:
            print(f"Error initializing model {model_name}: {e}")
            print("Falling back to gemini-1.0-pro model...")
            self.model = genai.GenerativeModel("gemini-1.0-pro")
            self.model_name = "gemini-1.0-pro"

    def refine_query(self, user_query):
        """
        Refines an HPE-related user query using Gemini LLM.
        
        Args:
            user_query (str): The original query from the user
            
        Returns:
            str: The refined query
        """
        prompt = f"""
        You are an expert in refining search queries specifically for HPE (Hewlett Packard Enterprise) business and financial data.
        Your task is to transform the user's raw query into a more effective search query that will yield better results.
        
        Guidelines for refinement:
        
        1. Financial terminology standardization:
           - ARR = Annual Recurring Revenue
           - GreenLake = HPE's as-a-service platform
           - HPC = High Performance Computing
           - EPS = Earnings Per Share
           - ACM = HPE Aruba Networking, HPE Cray, and HPE Athonet
        
        2. Quarter and fiscal year standardization:
           - Use "Q1 FY24" format for fiscal quarters
           - Convert written quarters ("third quarter") to "Q3"
           - Convert written years ("twenty twenty four") to "2024"
           - HPE's fiscal year ends October 31
        
        3. Improve query quality:
           - Fix typos and grammatical errors
           - Make abbreviations consistent (HPE, AI, etc.)
           - Replace vague terms with specific ones
           - Add contextual keywords if needed
           - Ensure technical accuracy for HPE-specific terms
        
        4. Format:
           - Maintain brevity while improving precision
           - Use proper capitalization for product names and business segments
           - Keep financial metrics clearly identifiable
        
        Original Query: "{user_query}"
        
        Refined Query (ONLY provide the refined query, no explanations):
        """

        try:
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.1,
                            "max_output_tokens": 100,
                            "top_p": 0.95,
                        }
                    )
                    
                    # Extract and clean the refined query
                    refined_query = response.text.strip()
                    # Remove any quotes if they were added by the model
                    refined_query = refined_query.strip('"\'')
                    return refined_query
                
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"Error after {max_retries} attempts: {e}")
                        return user_query
                    
                    print(f"Attempt {retry_count} failed: {e}. Retrying in 2 seconds...")
                    time.sleep(2)
        
        except Exception as e:
            print(f"Error during query refinement: {e}")
            return user_query  # Return original query in case of error


# --- Example Usage ---
if __name__ == "__main__":
    refiner = HPEQueryRefiner()  # API key will be loaded from environment

    test_queries = [
        "HPE ARR Q3 2024",
        "which quarter has highest ARR Global",
        "How was HPE's performance compared to prior year",
        "why did HPE's arr grow in q3 2024",
        "capital returned shareholders ARR reached 1.7B",
        "When HPC & Al merged compute server segment upcoming quarters after reorganization",
        "tell me about hpe annual reocurring revenue in third quater twenty twenty four",
        "What is the captial expenditure in q2 fy23 for HPE?",
        "how much did greenlake grow in recent quarter",
        "comparison of HPE segments performance in latest earnings",
        "where does aruba sit in HPE portfolio"
    ]

    print("\n" + "="*80)
    print(f"QUERY REFINEMENT USING {refiner.model_name.upper()}")
    print("="*80 + "\n")

    for idx, query in enumerate(test_queries, 1):
        print(f"\n{idx}. ORIGINAL: {query}")
        try:
            start_time = time.time()
            refined_query = refiner.refine_query(query)
            end_time = time.time()
            
            print(f"   REFINED : {refined_query}")
            print(f"   TIME    : {(end_time - start_time):.2f} seconds")
        except Exception as e:
            print(f"   ERROR   : {e}")
        print("-" * 80)