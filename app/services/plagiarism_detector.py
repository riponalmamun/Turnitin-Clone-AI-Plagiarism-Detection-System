from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.match import Match, MatchType, SourceType
from app.services.text_processor import TextProcessor
from app.services.search_service import SearchService
from app.services.similarity_service import SimilarityService
from app.services.ai_service import AIService
from app.services.embedding_service import EmbeddingService
from app.database.vector_db import vector_db
from app.core.config import settings


class PlagiarismDetector:
    """Main plagiarism detection engine"""
    
    def __init__(self, db: Session):
        self.db = db
        self.text_processor = TextProcessor()
        self.search_service = SearchService()
        self.similarity_service = SimilarityService()
        self.ai_service = AIService()
        self.embedding_service = EmbeddingService()
    
    def check_plagiarism(
        self,
        document: Document,
        check_web: bool = True,
        check_database: bool = True,
        check_institution: bool = True
    ) -> Tuple[float, List[Dict]]:
        """
        Main plagiarism checking function
        Returns: (originality_score, matches_list)
        """
        all_matches = []
        
        # Clean and process text
        clean_text = self.text_processor.clean_text(document.content)
        chunks = self.text_processor.chunk_text(
            clean_text,
            settings.CHUNK_SIZE,
            settings.OVERLAP
        )
        
        # 1. Check against database
        if check_database:
            db_matches = self._check_database(document, chunks)
            all_matches.extend(db_matches)
        
        # 2. Check against web
        if check_web:
            web_matches = self._check_web(chunks)
            all_matches.extend(web_matches)
        
        # 3. Check institution database (if applicable)
        if check_institution and document.institution_id:
            inst_matches = self._check_institution(document, chunks)
            all_matches.extend(inst_matches)
        
        # Calculate originality score
        originality_score = self._calculate_originality_score(
            document.content,
            all_matches
        )
        
        return originality_score, all_matches
    
    def _check_database(self, document: Document, chunks: List[str]) -> List[Dict]:
        """Check against stored documents"""
        matches = []
        
        try:
            # Generate embedding for each chunk
            for idx, chunk in enumerate(chunks):
                if len(chunk.split()) < settings.MIN_MATCH_LENGTH:
                    continue
                
                embedding = self.embedding_service.generate_embedding(chunk)
                
                # Search in vector database
                results = vector_db.search_similar(
                    query_embedding=embedding,
                    n_results=5
                )
                
                if results and results['ids']:
                    for i, doc_id in enumerate(results['ids'][0]):
                        # Skip if same document
                        if doc_id == str(document.id):
                            continue
                        
                        distance = results['distances'][0][i]
                        similarity = (1 - distance) * 100  # Convert distance to similarity
                        
                        if similarity >= settings.SEMANTIC_SIMILARITY_THRESHOLD * 100:
                            source_text = results['documents'][0][i]
                            
                            matches.append({
                                'match_type': MatchType.SEMANTIC,
                                'source_type': SourceType.DATABASE,
                                'matched_text': chunk,
                                'source_text': source_text,
                                'similarity_score': similarity,
                                'source_document_id': int(doc_id),
                                'start_position': idx * settings.CHUNK_SIZE,
                                'end_position': idx * settings.CHUNK_SIZE + len(chunk.split())
                            })
        
        except Exception as e:
            print(f"Error checking database: {e}")
        
        return matches
    
    def _check_web(self, chunks: List[str]) -> List[Dict]:
        """Check against web sources"""
        matches = []
        
        try:
            # Select important chunks to search (to save API calls)
            important_chunks = self._select_important_chunks(chunks, limit=10)
            
            for idx, chunk in enumerate(important_chunks):
                if len(chunk.split()) < settings.MIN_MATCH_LENGTH:
                    continue
                
                # Create search query from chunk
                keywords = self.text_processor.extract_keywords(chunk, top_n=5)
                query = ' '.join(keywords[:3])  # Use top 3 keywords
                
                # Search web
                search_results = self.search_service.search(query, num_results=5)
                
                for result in search_results:
                    # Fetch content from URL
                    source_content = self.search_service.fetch_url_content(result['url'])
                    
                    if source_content:
                        # Calculate similarity
                        similarity = self.similarity_service.cosine_similarity_score(
                            chunk,
                            source_content[:1000]  # Compare with first 1000 chars
                        )
                        
                        if similarity >= settings.EXACT_MATCH_THRESHOLD:
                            # Check if it's a paraphrase using AI
                            is_paraphrase = False
                            if similarity < 95:  # Not exact match
                                ai_result = self.ai_service.detect_paraphrase(
                                    chunk,
                                    source_content[:500]
                                )
                                is_paraphrase = ai_result['is_paraphrase']
                            
                            match_type = MatchType.EXACT if similarity >= 95 else (
                                MatchType.PARAPHRASE if is_paraphrase else MatchType.SEMANTIC
                            )
                            
                            matches.append({
                                'match_type': match_type,
                                'source_type': SourceType.WEB,
                                'matched_text': chunk,
                                'source_text': source_content[:500],
                                'similarity_score': similarity,
                                'source_url': result['url'],
                                'source_title': result['title'],
                                'start_position': idx * settings.CHUNK_SIZE,
                                'end_position': idx * settings.CHUNK_SIZE + len(chunk.split())
                            })
        
        except Exception as e:
            print(f"Error checking web: {e}")
        
        return matches
    
    def _check_institution(self, document: Document, chunks: List[str]) -> List[Dict]:
        """Check against institution's document database"""
        matches = []
        
        try:
            # Query documents from same institution
            institution_docs = self.db.query(Document).filter(
                Document.institution_id == document.institution_id,
                Document.id != document.id
            ).all()
            
            for chunk in chunks:
                if len(chunk.split()) < settings.MIN_MATCH_LENGTH:
                    continue
                
                for inst_doc in institution_docs:
                    similarity = self.similarity_service.cosine_similarity_score(
                        chunk,
                        inst_doc.content
                    )
                    
                    if similarity >= settings.EXACT_MATCH_THRESHOLD:
                        matches.append({
                            'match_type': MatchType.EXACT,
                            'source_type': SourceType.INSTITUTION,
                            'matched_text': chunk,
                            'source_text': inst_doc.content[:500],
                            'similarity_score': similarity,
                            'source_document_id': inst_doc.id,
                            'start_position': 0,
                            'end_position': len(chunk.split())
                        })
        
        except Exception as e:
            print(f"Error checking institution: {e}")
        
        return matches
    
    def _select_important_chunks(self, chunks: List[str], limit: int = 10) -> List[str]:
        """Select most important chunks for checking (to save API calls)"""
        # Score chunks based on length and keyword density
        scored_chunks = []
        
        for chunk in chunks:
            words = chunk.split()
            # Longer chunks with more unique words are more important
            unique_words = len(set(words))
            score = len(words) * (unique_words / len(words) if len(words) > 0 else 0)
            scored_chunks.append((score, chunk))
        
        # Sort by score and take top N
        scored_chunks.sort(reverse=True, key=lambda x: x[0])
        return [chunk for _, chunk in scored_chunks[:limit]]
    
    def _calculate_originality_score(self, full_text: str, matches: List[Dict]) -> float:
        """Calculate overall originality score"""
        if not matches:
            return 100.0
        
        total_words = len(full_text.split())
        
        # Calculate matched words (avoid double counting)
        matched_positions = set()
        for match in matches:
            start = match.get('start_position', 0)
            end = match.get('end_position', 0)
            matched_positions.update(range(start, end))
        
        matched_words = len(matched_positions)
        plagiarism_percentage = (matched_words / total_words * 100) if total_words > 0 else 0
        
        originality_score = 100 - plagiarism_percentage
        return max(0, min(100, originality_score))  # Clamp between 0-100