# https://github.com/modelcontextprotocol/servers/blob/main/src/fetch/src/mcp_server_fetch/server.py
import httpx
import markdownify
from readabilipy.simple_json import simple_json_from_html_string
import re
from typing import List, Dict, Literal
from pydantic import BaseModel, AnyUrl, Field
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv() 
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DEFAULT_UA = "FastMCP/1.0 (+https://example.com)"
DEFAULT_UA_BROWSER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class FetchRequest(BaseModel):
    url: AnyUrl
    max_length: int = Field(5000, gt=0, lt=1_000_000)
    start_index: int = Field(0, ge=0)
    raw: bool = False
    
class SearchRequest(BaseModel):
    query: str
    max_results: int = 5
    model: Literal["gpt-4o-mini-search-preview", "gpt-5","gpt-5-mini", "gpt-40","gpt-4o-mini"] = "gpt-5" 

def html_to_markdown(html: str) -> str:
    """Extract main content (Readability) then convert to Markdown."""
    data = simple_json_from_html_string(html, use_readability=True)
    content_html = (data or {}).get("content") or ""
    if not content_html:
        return "<error>Page could not be simplified; returning nothing.</error>"
    md = markdownify.markdownify(content_html, heading_style=markdownify.ATX)
    return md

async def http_get_text(url: str, timeout_s: int = 20) -> (str, str):
    """Fetch URL and return (text, content_type). Raises for HTTP errors."""
    async with httpx.AsyncClient(follow_redirects=True, headers={"User-Agent": DEFAULT_UA}, timeout=timeout_s) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text, r.headers.get("content-type", "")
    
def looks_like_html(body: str, content_type: str) -> bool:
    if "text/html" in content_type.lower():
        return True
    return "<html" in body[:500].lower()

# ----------------------------------------------------------------------------------------------------------------------------
def web_search_api(query: str, max_results: int , model: str ) -> List[Dict[str, str]]:
    """Minimal web_search: returns [{'url': str, 'snippet': str}, ...]."""
    if not OPENAI_API_KEY:
        return [{"url": "", "snippet": "OPENAI_API_KEY not set."}]
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        resp = client.responses.create(
            model=model,
            tools=[{"type": "web_search_preview", "search_context_size": "medium"}],
            input=query,
        )
    except Exception as e:
        return [{"url": "", "snippet": f"Search failed: {e}"}]
    text = getattr(resp, "output_text", "") or ""
    urls = re.findall(r"https?://[^\s)\"'>]+", text)

    results: List[Dict[str, str]] = []
    for u in urls[:max_results]:
        i = text.find(u)
        start = max(i - 80, 0)
        end = i + len(u) + 80
        results.append({"url": u, "snippet": text[start:end]})
    if not results:
        results.append({"url": "", "snippet": text[:1000]})
    return results

# ----------------------------------------------------------------------------------------------------------------------------

async def fetch(url: str, max_length: int = 5000, start_index: int = 0, raw: bool = False) -> Dict:
    try:
        args = FetchRequest(url=url, max_length=max_length, start_index=start_index, raw=raw)
    except Exception as e:
        return {"error": f"Invalid arguments: {e}"}
    try:
        body, ctype = await http_get_text(str(args.url))
    except httpx.HTTPStatusError as e:
        return {"url": str(args.url), "error": f"HTTP {e.response.status_code} while fetching."}
    except Exception as e:
        return {"url": str(args.url), "error": f"Fetch failed: {e}"}

    if not args.raw and looks_like_html(body, ctype):
        content = html_to_markdown(body)
        prefix = ""
    else:
        content = body
        prefix = f"Content-Type: {ctype or 'unknown'} (raw)\n\n"
    total = len(content)
    if args.start_index >= total:
        final = "<error>No more content available.</error>"
    else:
        chunk = content[args.start_index : args.start_index + args.max_length]
        final = chunk if chunk else "<error>No more content available.</error>"
        if len(chunk) == args.max_length and (args.start_index + len(chunk)) < total:
            next_start = args.start_index + len(chunk)
            final += f"\n\n<error>Content truncated. Call fetch with start_index={next_start} to continue.</error>"
    return {"url": str(args.url), "prefix": prefix, "content": final}

# ----------------------------------------------------------------------------------------------------------------------------

def web_search(query: str, max_results: int = 5) -> List[str]:
    """Return a plain list of URLs (strings)."""
    try:
        r = httpx.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={
                "User-Agent": DEFAULT_UA_BROWSER,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://duckduckgo.com/",
            },
            timeout=20,
            follow_redirects=True,
        )
        r.raise_for_status()
    except Exception:
        return []
    html = r.text
    anchors = re.findall(r'href="([^"]+)"', html)
    urls = []
    for a in anchors:
        if "uddg=" in a or a.startswith("/l/"):
            try:
                full = a if a.startswith("http") else "https://duckduckgo.com" + a
                u = urllib.parse.unquote(urllib.parse.parse_qs(urllib.parse.urlparse(full).query).get("uddg", [full])[0])
            except Exception:
                u = a
            if u.startswith("http") and "duckduckgo.com" not in u and u not in urls:
                urls.append(u)
        elif a.startswith("http") and "duckduckgo.com" not in a:
            if a not in urls:
                urls.append(a)
        if len(urls) >= max_results:
            break

    return urls[:max_results]