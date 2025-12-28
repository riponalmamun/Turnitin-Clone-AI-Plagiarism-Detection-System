import re
import hashlib
from typing import List, Tuple
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

# Download NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


class TextProcessor:
    """Process and clean text for plagiarism detection"""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:\-]', '', text)
        return text.strip()
    
    def remove_citations(self, text: str) -> str:
        """Remove common citation patterns"""
        # Remove (Author, Year) patterns
        text = re.sub(r'\([A-Za-z]+,\s*\d{4}\)', '', text)
        # Remove [1], [2] style citations
        text = re.sub(r'\[\d+\]', '', text)
        return text
    
    def chunk_text(self, text: str, chunk_size: int = 100, overlap: int = 20) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk.split()) >= 10:  # Minimum chunk size
                chunks.append(chunk)
        
        return chunks
    
    def extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text"""
        return sent_tokenize(text)
    
    def extract_keywords(self, text: str, top_n: int = 20) -> List[str]:
        """Extract important keywords (non-stop words)"""
        words = word_tokenize(text.lower())
        keywords = [w for w in words if w.isalnum() and w not in self.stop_words]
        
        # Count frequency
        from collections import Counter
        word_freq = Counter(keywords)
        return [word for word, _ in word_freq.most_common(top_n)]
    
    def generate_fingerprint(self, text: str) -> str:
        """Generate unique fingerprint/hash for text"""
        # Normalize text
        normalized = self.clean_text(text.lower())
        # Create hash
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def calculate_word_count(self, text: str) -> int:
        """Calculate word count"""
        return len(text.split())
    
    def create_ngrams(self, text: str, n: int = 3) -> List[str]:
        """Create n-grams from text"""
        words = text.split()
        ngrams = []
        for i in range(len(words) - n + 1):
            ngrams.append(' '.join(words[i:i+n]))
        return ngrams