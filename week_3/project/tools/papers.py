# project/tools/papers.py
import re
import json
import requests
from markdownify import markdownify

BASE_URL = "https://huggingface.co"

def clean_arxiv_id(raw_id: str) -> str:

    # Strip any URL prefixes if the model passes a link
    cleaned = raw_id.split("arxiv.org/abs/")[-1].split("arxiv.org/pdf/")[-1]
   
    cleaned = re.sub(r'v\d+$', '', cleaned)
    return cleaned.strip()

def tool_paper_search(query: str) -> str:
    
    try:
        response = requests.get(f"{BASE_URL}/api/papers/search", params={"q": query}, timeout=15)
        if response.status_code != 200:
            return json.dumps({"error": f"API search request failed with code {response.status_code}"})
            
        data = response.json()
        
        hits = data.get("hits", data) if isinstance(data, dict) else data
        
        results = []
        for item in hits[:8]:  # Keep context light
            paper_data = item.get("paper", item) if isinstance(item, dict) else {}
            if paper_data:
                results.append({
                    "id": paper_data.get("id", ""),
                    "title": paper_data.get("title", ""),
                    "summary": paper_data.get("summary", ""),
                    "publishedAt": paper_data.get("publishedAt", "")
                })
        return json.dumps({"content": results})
    except Exception as e:
        return json.dumps({"error": str(e)})

def tool_read_paper(arxiv_id: str) -> str:
  
    try:
        pid = clean_arxiv_id(arxiv_id)
        
        
        md_url = f"{BASE_URL}/papers/{pid}.md"
        md_res = requests.get(md_url, timeout=15)
        
        if md_res.status_code == 200 and md_res.text.strip():
            content = md_res.text
        else:
            
            api_url = f"{BASE_URL}/api/papers/{pid}"
            api_res = requests.get(api_url, timeout=15)
            if api_res.status_code == 200:
                meta = api_res.json()
                content = f"Title: {meta.get('title')}\nAbstract: {meta.get('summary')}\n\n[Note: Detailed Markdown body was unavailable on HF; parsed abstract only.]"
            else:
                return json.dumps({"error": f"Paper reference ID {pid} not found on Hugging Face index pages."})
                
        
        max_chars = 12000
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[...truncated]"
            
        return json.dumps({"content": content, "arxiv_url": f"https://arxiv.org/abs/{pid}"})
    except Exception as e:
        return json.dumps({"error": str(e)})

PAPERS_TOOLS_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "paper_search",
            "description": "Queries the Hugging Face Papers API index semantically. Use to research papers.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Keywords or partial titles."}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_paper",
            "description": "Fetches markdown content or detailed abstracts using an arXiv ID. Always pass through paper_search first to discover IDs.",
            "parameters": {
                "type": "object",
                "properties": {"arxiv_id": {"type": "string", "description": "e.g., '2205.14135'"}},
                "required": ["arxiv_id"]
            }
        }
    }
]