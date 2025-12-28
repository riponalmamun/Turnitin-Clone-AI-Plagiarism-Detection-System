from typing import List, Dict, Optional
import requests
from duckduckgo_search import DDGS
from app.core.config import settings


class SearchService:
    """Search the web using multiple search APIs"""
    
    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search using priority order"""
        for search_method in settings.SEARCH_PRIORITY.split(","):
            try:
                if search_method == "duckduckgo" and settings.USE_DUCKDUCKGO:
                    return self._search_duckduckgo(query, num_results)
                elif search_method == "serper" and settings.SERPER_API_KEY:
                    return self._search_serper(query, num_results)
                elif search_method == "serpapi" and settings.SERPAPI_KEY:
                    return self._search_serpapi(query, num_results)
            except Exception as e:
                print(f"Error with {search_method}: {e}")
                continue
        
        return []
    
    def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict]:
        """Search using DuckDuckGo (Free, No API key)"""
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=num_results):
                results.append({
                    'title': r.get('title', ''),
                    'url': r.get('href', ''),
                    'snippet': r.get('body', '')
                })
        return results
    
    def _search_serper(self, query: str, num_results: int) -> List[Dict]:
        """Search using Serper API"""
        url = "https://google.serper.dev/search"
        headers = {
            'X-API-KEY': settings.SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        payload = {
            'q': query,
            'num': num_results
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get('organic', []):
            results.append({
                'title': item.get('title', ''),
                'url': item.get('link', ''),
                'snippet': item.get('snippet', '')
            })
        
        return results
    
    def _search_serpapi(self, query: str, num_results: int) -> List[Dict]:
        """Search using SerpAPI"""
        from serpapi import GoogleSearch
        
        params = {
            "q": query,
            "num": num_results,
            "api_key": settings.SERPAPI_KEY
        }
        
        search = GoogleSearch(params)
        data = search.get_dict()
        
        results = []
        for item in data.get('organic_results', []):
            results.append({
                'title': item.get('title', ''),
                'url': item.get('link', ''),
                'snippet': item.get('snippet', '')
            })
        
        return results
    
    def fetch_url_content(self, url: str) -> Optional[str]:
        """Fetch and extract text from URL"""
        try:
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        
        except Exception as e:
            print(f"Error fetching URL {url}: {e}")
            return None