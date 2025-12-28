from typing import List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher
from app.core.config import settings


class SimilarityService:
    """Calculate similarity between texts using various algorithms"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
    
    def cosine_similarity_score(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity using TF-IDF"""
        try:
            tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity * 100)  # Convert to percentage
        except Exception as e:
            print(f"Error in cosine similarity: {e}")
            return 0.0
    
    def jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if len(union) == 0:
            return 0.0
        
        return (len(intersection) / len(union)) * 100
    
    def levenshtein_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity using Levenshtein distance"""
        ratio = SequenceMatcher(None, text1, text2).ratio()
        return ratio * 100
    
    def longest_common_subsequence(self, text1: str, text2: str) -> Tuple[float, str]:
        """Find longest common subsequence"""
        words1 = text1.split()
        words2 = text2.split()
        
        m, n = len(words1), len(words2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if words1[i-1].lower() == words2[j-1].lower():
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        lcs_length = dp[m][n]
        similarity = (lcs_length / max(m, n)) * 100 if max(m, n) > 0 else 0
        
        # Reconstruct LCS
        lcs_words = []
        i, j = m, n
        while i > 0 and j > 0:
            if words1[i-1].lower() == words2[j-1].lower():
                lcs_words.append(words1[i-1])
                i -= 1
                j -= 1
            elif dp[i-1][j] > dp[i][j-1]:
                i -= 1
            else:
                j -= 1
        
        lcs_text = ' '.join(reversed(lcs_words))
        return similarity, lcs_text
    
    def calculate_combined_similarity(self, text1: str, text2: str) -> float:
        """Calculate weighted average of multiple similarity metrics"""
        cosine = self.cosine_similarity_score(text1, text2)
        jaccard = self.jaccard_similarity(text1, text2)
        levenshtein = self.levenshtein_similarity(text1, text2)
        
        # Weighted average
        combined = (cosine * 0.5) + (jaccard * 0.3) + (levenshtein * 0.2)
        return combined
    
    def find_matching_segments(
        self, 
        text1: str, 
        text2: str, 
        min_length: int = 10
    ) -> List[Tuple[str, float, int, int]]:
        """Find all matching segments between two texts"""
        words1 = text1.split()
        words2 = text2.split()
        matches = []
        
        for i in range(len(words1) - min_length + 1):
            for j in range(len(words2) - min_length + 1):
                # Try different segment lengths
                for length in range(min_length, min(len(words1) - i, len(words2) - j) + 1):
                    segment1 = ' '.join(words1[i:i+length])
                    segment2 = ' '.join(words2[j:j+length])
                    
                    similarity = self.levenshtein_similarity(segment1, segment2)
                    
                    if similarity >= settings.EXACT_MATCH_THRESHOLD:
                        matches.append((segment1, similarity, i, i+length))
        
        return matches
    
    def vector_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float((dot_product / (norm1 * norm2)) * 100)