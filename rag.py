import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import re

# Load a small local embedding model
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Expanded data structure for comparison, fees, and courses
sample_data = [
    {
        "id": 1, 
        "name": "Anna University",
        "keywords": ["anna university", "ceg", "mit", "act"],
        "basic": "Anna University is a premier engineering institution located in Chennai. It offers top-tier B.E./B.Tech and M.E./M.Tech programs across its famous campuses like CEG, MIT, and ACT.",
        "detailed": "### Anna University Achievements & Information\n\nAnna University is globally recognized for its research output and strong alumni network (including Dr. A.P.J. Abdul Kalam from MIT).\n\n**Key Highlights:**\n- Ranked among the Top 20 Engineering Institutions in India.\n- Home to advanced drone research (Kalam Advanced UAV Research Centre).\n- Excellent sports facilities including a massive swimming pool and stadium at CEG.\n\n![Anna University Campus](https://upload.wikimedia.org/wikipedia/en/4/4c/Anna_University_Logo.svg)\n\n[Visit Official Website](https://www.annauniv.edu/)",
        "courses": "B.E. Computer Science, B.E. Mechanical, B.E. Electronics, B.Tech Information Technology, M.E., MBA",
        "fees": "₹40,000 - ₹60,000 per year (Government Quota)"
    },
    {
        "id": 2, 
        "name": "SRM Institute of Technology",
        "keywords": ["srm", "srmist"],
        "basic": "SRM Institute of Science and Technology (SRMIST) is a top-ranked private deemed university known for its massive infrastructure, diverse student body, and excellent placement records.",
        "detailed": "### SRM Achievements & Information\n\nSRM is famous not just for academics, but for its incredibly vibrant campus life.\n\n**Key Highlights:**\n- Hosts 'Milan', one of the largest national-level cultural fests.\n- Massive global alumni network and semester-abroad programs.\n- Winner of multiple inter-university sports trophies.\n\n![SRM University](https://upload.wikimedia.org/wikipedia/en/f/fe/Srmseal.png)\n\n[Apply to SRM](https://www.srmist.edu.in/)",
        "courses": "B.Tech CSE, B.Tech AI & Data Science, MBBS, BDS, BBA, MBA, Ph.D.",
        "fees": "₹2,50,000 - ₹4,50,000 per year (Varies by course)"
    },
    {
        "id": 3, 
        "name": "Madras Medical College",
        "keywords": ["madras medical college", "mmc"],
        "basic": "Madras Medical College (MMC) is one of the oldest and most prestigious medical colleges in India, offering top UG (MBBS) and PG medical programs.",
        "detailed": "### MMC Achievements & Information\n\nMMC is a pioneer in medical education in Asia, associated with the Rajiv Gandhi Government General Hospital.\n\n**Key Highlights:**\n- Over 185 years of legacy in medical excellence.\n- Produces top-tier doctors and researchers globally.\n- State-of-the-art medical research facilities.\n\n![MMC Logo](https://upload.wikimedia.org/wikipedia/en/e/ed/Madras_Medical_College_Logo.png)\n\n[Visit MMC Website](http://www.mmc.ac.in/)",
        "courses": "MBBS, MD, MS, B.Pharm, B.Sc Nursing",
        "fees": "₹13,610 per year (State Quota)"
    }
]

# Extract texts for embeddings
texts = [doc["basic"] for doc in sample_data]

print("Generating FAISS embeddings...")
embeddings = embedder.encode(texts)
embedding_dim = embeddings.shape[1]

index = faiss.IndexFlatL2(embedding_dim)
index.add(np.array(embeddings))
print(f"Added {index.ntotal} documents to the FAISS index.")

def detect_intent(query: str):
    query_lower = query.lower()
    
    if "compare" in query_lower or "vs" in query_lower or "difference" in query_lower:
        return "compare"
    elif "fee" in query_lower or "cost" in query_lower or "price" in query_lower:
        return "fees"
    elif "course" in query_lower or "program" in query_lower or "degree" in query_lower:
        return "courses"
    elif any(keyword in query_lower for keyword in ["more", "detail", "achievements", "trophy", "trophies", "picture", "photo", "link", "about"]):
        return "detailed"
    
    return "basic"

def generate_comparison_table(doc1, doc2):
    return f"""### Comparison: {doc1['name']} vs {doc2['name']}

| Feature | **{doc1['name']}** | **{doc2['name']}** |
| :--- | :--- | :--- |
| **Courses** | {doc1['courses']} | {doc2['courses']} |
| **Fees** | {doc1['fees']} | {doc2['fees']} |
| **Highlights** | {doc1['basic']} | {doc2['basic']} |
"""

def generate_response(query: str) -> str:
    intent = detect_intent(query)
    
    # Handle Comparative Intent
    if intent == "compare":
        # Search for top 2 matches to compare
        query_emb = embedder.encode([query])
        distances, indices = index.search(np.array(query_emb), 2)
        
        idx1, idx2 = indices[0][0], indices[0][1]
        if idx1 == -1 or idx2 == -1 or idx1 >= len(sample_data) or idx2 >= len(sample_data):
            return "I couldn't find enough matching colleges to make a comparison."
            
        return generate_comparison_table(sample_data[idx1], sample_data[idx2])

    # Handle standard lookup
    query_emb = embedder.encode([query])
    distances, indices = index.search(np.array(query_emb), 1)
    
    idx = indices[0][0]
    
    if idx == -1 or idx >= len(sample_data):
        return "I'm sorry, I don't have information about that in my academic database."
    
    matched_doc = sample_data[idx]
    
    if intent == "fees":
        return f"**Fees for {matched_doc['name']}:**\n{matched_doc['fees']}"
    elif intent == "courses":
        return f"**Courses at {matched_doc['name']}:**\n{matched_doc['courses']}"
    elif intent == "detailed":
        return matched_doc["detailed"]
    else:
        return matched_doc["basic"] + "\n\n*(Hint: Try asking 'Compare Anna University and SRM' or 'What are the fees for MMC?')*"
