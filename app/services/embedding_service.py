from typing import List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Global flag and model
_model = None
_model_loaded = False


def _load_model():
    """Lazy load the sentence transformer model"""
    global _model, _model_loaded
    
    if _model_loaded:
        return _model
    
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        _model_loaded = True
        logger.info("✅ Sentence transformer model loaded successfully")
        return _model
    except Exception as e:
        logger.error(f"Failed to load sentence transformer model: {e}")
        _model_loaded = True  # Don't try again
        return None


class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self):
        # Don't load model on init, load it when first used
        pass
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        model = _load_model()
        
        if model is None:
            logger.warning("Embedding model not available")
            # Return a dummy embedding or raise error
            return None
        
        try:
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generate embeddings for multiple texts"""
        model = _load_model()
        
        if model is None:
            logger.warning("Embedding model not available")
            return None
        
        try:
            embeddings = model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def is_available(self) -> bool:
        """Check if embedding service is available"""
        model = _load_model()
        return model is not None