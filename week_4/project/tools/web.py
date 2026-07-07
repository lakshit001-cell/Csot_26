# project/tools/web.py
import os
import json
import requests
import trafilatura

def execute_web_search(query: str) -> str:
    
    api_key = os.environ.get("SERPER_API_KEY")
    
    # --- THE DEBUG TRAP ---
    if not api_key:
        return json.dumps({"error": "CRITICAL FAILURE: api_key is None! Python is still not reading the .env file."})
    try:
        response = requests.post("https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": 10},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            })
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"})

def execute_web_fetch(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        response.raise_for_status()
        
        text = trafilatura.extract(response.text, include_comments=False, include_tables=True)
        if not text:
            return json.dumps({"error": "Cannot extract text from page"})
            
        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[...truncated]"
            
        return text
    except Exception as e:
        return json.dumps({"error": f"Fetch failed: {str(e)}"})

WEB_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web in real time for current and latest information.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "The search query."}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch and read the full text content of a web page URL.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "The full URL to read."}},
                "required": ["url"],
            },
        },
    }
]