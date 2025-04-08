from sentence_transformers import SentenceTransformer, util

# Load a pre-trained Sentence Transformer model (choose one appropriate for semantic similarity)
semantic_model = SentenceTransformer('all-mpnet-base-v2') # Good balance of speed and accuracy

def semantic_synonym_expansion(query, domain_keywords, top_n=3, similarity_threshold=0.7):
    """
    Expands a query with semantically similar keywords from a domain-specific list
    using Sentence Transformers for semantic similarity.

    Args:
        query (str): The user query.
        domain_keywords (list): A list of domain-specific keywords and phrases.
        top_n (int): Number of top similar keywords to add.
        similarity_threshold (float): Minimum cosine similarity to consider a keyword relevant.

    Returns:
        str: Query expanded with semantic synonyms.
    """
    query_embedding = semantic_model.encode(query, convert_to_tensor=True)
    keyword_embeddings = semantic_model.encode(domain_keywords, convert_to_tensor=True)

    # Compute cosine similarity between query and keywords
    cosine_scores = util.cos_sim(query_embedding, keyword_embeddings)[0]

    # Get top N most similar keywords
    top_results = sorted(range(len(cosine_scores)), key=lambda i: cosine_scores[i], reverse=True)[0:top_n]

    expanded_query_parts = [query] # Start with the original query
    for idx in top_results:
        if cosine_scores[idx] >= similarity_threshold: # Apply similarity threshold
            expanded_query_parts.append(domain_keywords[idx])

    return " ".join(list(set(expanded_query_parts))) # Join and remove duplicates

# --- Example Usage ---
if __name__ == "__main__":
    domain_financial_keywords = [
        "Annual Recurring Revenue", "ARR", "Quarterly Revenue", "Q3 2024 Financial Results",
        "Capital Expenditure", "Shareholder Returns", "HPE Performance", "Fiscal Year 2023",
        "Server Segment Performance", "HPC and AI Group", "Compute Segment", "Merger Impact"
        # ... Add more domain-specific keywords and phrases
    ]

    sample_query = "HPE ARR in third quarter"
    expanded_query = semantic_synonym_expansion(sample_query, domain_financial_keywords)
    print(f"Original Query: {sample_query}")
    print(f"Semantic Expanded Query: {expanded_query}")