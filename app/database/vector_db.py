from typing import List, Dict, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Try to import chromadb, make it optional
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not installed. Vector search functionality will be disabled.")


class VectorDB:
    """ChromaDB wrapper for vector storage and similarity search"""
    
    def __init__(self):
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB is not available. Vector operations will be disabled.")
            self.client = None
            self.collection = None
            return
            
        try:
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.client = None
            self.collection = None
    
    def _check_availability(self):
        """Check if ChromaDB is available"""
        if not CHROMADB_AVAILABLE or self.collection is None:
            raise RuntimeError(
                "ChromaDB is not available. "
                "Install it with: pip install chromadb"
            )
    
    def add_document(
        self,
        doc_id: str,
        text: str,
        embedding: List[float],
        metadata: Dict
    ):
        """Add document to vector database"""
        self._check_availability()
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
    
    def search_similar(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict] = None
    ) -> Dict:
        """Search for similar documents"""
        self._check_availability()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        return results
    
    def delete_document(self, doc_id: str):
        """Delete document from vector database"""
        self._check_availability()
        self.collection.delete(ids=[doc_id])
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get document by ID"""
        self._check_availability()
        results = self.collection.get(ids=[doc_id])
        if results and results['ids']:
            return {
                'id': results['ids'][0],
                'document': results['documents'][0],
                'metadata': results['metadatas'][0]
            }
        return None
    
    def is_available(self) -> bool:
        """Check if vector database is available"""
        return CHROMADB_AVAILABLE and self.collection is not None


# Global instance
vector_db = VectorDB()