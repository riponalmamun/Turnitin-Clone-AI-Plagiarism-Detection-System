from typing import Optional, Dict
import openai
from groq import Groq
import google.generativeai as genai
from app.core.config import settings


class AIService:
    """AI service for paraphrase detection and semantic analysis"""
    
    def __init__(self):
        self.openai_client = None
        self.groq_client = None
        self.gemini_model = None
        
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            self.openai_client = openai
        
        if settings.GROQ_API_KEY:
            self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
    
    def detect_paraphrase(self, text1: str, text2: str) -> Dict:
        """Detect if text2 is a paraphrase of text1 using AI"""
        prompt = f"""
Compare these two texts and determine if they convey the same meaning (paraphrase).
Respond with a JSON object containing:
- is_paraphrase (boolean)
- confidence (0-100)
- explanation (brief)

Text 1: {text1}

Text 2: {text2}

Response:"""
        
        for ai_method in settings.AI_PRIORITY.split(","):
            try:
                if ai_method == "groq" and self.groq_client:
                    return self._detect_with_groq(prompt)
                elif ai_method == "gemini" and self.gemini_model:
                    return self._detect_with_gemini(prompt)
                elif ai_method == "openai" and self.openai_client:
                    return self._detect_with_openai(prompt)
            except Exception as e:
                print(f"Error with {ai_method}: {e}")
                continue
        
        # Fallback
        return {"is_paraphrase": False, "confidence": 0, "explanation": "AI detection failed"}
    
    def _detect_with_openai(self, prompt: str) -> Dict:
        """Detect paraphrase using OpenAI"""
        response = self.openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        result = response.choices[0].message.content
        return self._parse_ai_response(result)
    
    def _detect_with_groq(self, prompt: str) -> Dict:
        """Detect paraphrase using Groq"""
        response = self.groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        result = response.choices[0].message.content
        return self._parse_ai_response(result)
    
    def _detect_with_gemini(self, prompt: str) -> Dict:
        """Detect paraphrase using Gemini"""
        response = self.gemini_model.generate_content(prompt)
        result = response.text
        return self._parse_ai_response(result)
    
    def _parse_ai_response(self, response: str) -> Dict:
        """Parse AI response to extract structured data"""
        import json
        import re
        
        try:
            # Try to extract JSON
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback parsing
            is_paraphrase = "true" in response.lower() or "yes" in response.lower()
            confidence_match = re.search(r'(\d+)%?', response)
            confidence = int(confidence_match.group(1)) if confidence_match else 50
            
            return {
                "is_paraphrase": is_paraphrase,
                "confidence": confidence,
                "explanation": response[:200]
            }
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return {"is_paraphrase": False, "confidence": 0, "explanation": "Parse error"}
    
    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate summary of text using AI"""
        prompt = f"Summarize the following text in {max_length} characters or less:\n\n{text}"
        
        for ai_method in settings.AI_PRIORITY.split(","):
            try:
                if ai_method == "groq" and self.groq_client:
                    response = self.groq_client.chat.completions.create(
                        model=settings.GROQ_MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=100
                    )
                    return response.choices[0].message.content
                
                elif ai_method == "gemini" and self.gemini_model:
                    response = self.gemini_model.generate_content(prompt)
                    return response.text
                
                elif ai_method == "openai" and self.openai_client:
                    response = self.openai_client.chat.completions.create(
                        model=settings.OPENAI_MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=100
                    )
                    return response.choices[0].message.content
            except Exception as e:
                print(f"Error with {ai_method}: {e}")
                continue
        
        # Fallback: return first N characters
        return text[:max_length] + "..." if len(text) > max_length else text