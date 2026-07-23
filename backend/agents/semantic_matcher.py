import httpx
import math
import logging
import asyncio
from config import HUGGINGFACE_API_KEY

# Using the Alibaba GTE model (created by the Qwen team) as the embedding backend
HF_API_URL = "https://api-inference.huggingface.co/models/Alibaba-NLP/gte-large-en-v1.5"

# Cache the resume embedding to avoid re-computing it for every job
_cached_resume_emb = None
_cached_resume_text = None

async def get_embedding(text: str) -> list[float]:
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"} if HUGGINGFACE_API_KEY else {}
    
    async with httpx.AsyncClient() as client:
        try:
            # We wrap in a loop to handle model loading (503)
            for _ in range(2):
                response = await client.post(
                    HF_API_URL, 
                    headers=headers, 
                    json={"inputs": text},
                    timeout=15.0
                )
                
                if response.status_code == 503:
                    # Model is loading, wait a bit and retry
                    await asyncio.sleep(2)
                    continue
                    
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    if isinstance(data[0], list):
                        return data[0]
                    return data
                return []
            return []
        except Exception as e:
            logging.error(f"HF Embedding Error: {e}")
            return []

def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)

async def calculate_semantic_similarity(resume_text: str, jd_text: str) -> float:
    global _cached_resume_emb, _cached_resume_text
    
    # Clean and truncate texts
    resume_clean = resume_text.strip()[:4000]
    jd_clean = jd_text.strip()[:4000]
    
    if not resume_clean or not jd_clean:
        return 0.8
        
    # Reuse resume embedding if possible
    if _cached_resume_text == resume_clean and _cached_resume_emb:
        resume_emb = _cached_resume_emb
    else:
        resume_emb = await get_embedding(resume_clean)
        if resume_emb:
            _cached_resume_text = resume_clean
            _cached_resume_emb = resume_emb
            
    jd_emb = await get_embedding(jd_clean)
    
    # If the API fails (e.g. rate limit, no key, model unavailable), 
    # we return a passing baseline so we don't break the whole pipeline.
    if not resume_emb or not jd_emb:
        logging.warning("Failed to fetch embeddings. Bypassing semantic filter.")
        return 0.8 
        
    return cosine_similarity(resume_emb, jd_emb)
