# https://github.com/ConechoAI/openai-websearch-mcp/blob/main/src/openai_websearch_mcp/server.py
# https://github.com/modelcontextprotocol/servers/blob/main/src/fetch/src/mcp_server_fetch/server.py
import os
from typing import List, Dict, Literal, Optional, Any
from pydantic import BaseModel, AnyUrl, Field
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from functools import lru_cache
from google import genai
import traceback
# load web functions:
from web_server_fct import html_to_markdown, http_get_text, looks_like_html, web_search, web_search_api, fetch
# load sql functions:
from sql_tools import sql_db_list_tables, sql_db_schema, sql_execute_query, sql_db_query_checker, sql_db_explain
# load rag tool:
from rag import run_rag_for_question, load_index

load_dotenv() 
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DEFAULT_UA = "FastMCP/1.0 (+https://example.com)"
DB_PATH = "data/company_data/Company_data.db"
# https://www.sqlite.org/uri.html
DB_URI = f"file:{os.path.abspath(DB_PATH)}?mode=ro&immutable=1&cache=shared"


mcp = FastMCP(
    name="combined-fast-mcp",
    instructions="Simple search + fetch tools for internship demo.",
    host="0.0.0.0",
    port=8787,
)

models = ["gpt-4o-mini-search-preview", "gpt-5","gpt-5-mini", "gpt-40","gpt-4o-mini"]
default_model = models[1]

class FetchRequest(BaseModel):
    url: AnyUrl
    max_length: int = Field(5000, gt=0, lt=1_000_000)
    start_index: int = Field(0, ge=0)
    raw: bool = False

class SearchRequest(BaseModel):
    query: str
    max_results: int = 5
    model: Literal["gpt-4o-mini-search-preview", "gpt-5","gpt-5-mini", "gpt-40","gpt-4o-mini"] = "gpt-5" 

# ---------------------------------------------------------WEB SEARCH API-----------------------------------------------------------
@mcp.tool(
    name="web_search_api",
    description="Search the web and return candidate URLs with short snippets.",
)
def web_search_api_tool(query: str, max_results: int = 5, model: str = default_model) -> List[Dict[str, str]]:
    """Minimal web_search: returns [{'url': str, 'snippet': str}, ...]."""
    return web_search_api(query, max_results, model)

# -------------------------------------------------------------FETCH----------------------------------------------------------------
@mcp.tool(
    name="fetch",
    description="Fetch a URL. For HTML, returns simplified Markdown; else returns raw text. Supports pagination.",
)
async def fetch_tool(url: str, max_length: int = 5000, start_index: int = 0, raw: bool = False) -> Dict:
    return await fetch(url=url, max_length=max_length, start_index=start_index, raw=raw)

# -----------------------------------------------------------WEB SEARCH-----------------------------------------------------------------

@lru_cache(maxsize=256)
def web_search_cached(query: str, max_results: int = 5) -> List[Dict[str,str]]:
    urls = web_search(query, max_results=max_results)
    if not urls:
        return [{"url": "", "snippet": "No results"}]
    return [{"url": u, "snippet": ""} for u in urls]

@mcp.tool(
    name="web_search",
    description="Search the web and return candidate URLs (no API key).",
)
def web_search_tool(query: str, max_results: int = 5, model: str = default_model) -> List[Dict[str,str]]:
    return web_search_cached(query, max_results)

# -----------------------------------------------------------SQL: List Tables-----------------------------------------------------------------
@mcp.tool(name = "sql_db_list_tables", description= "List all tables in the current database.")
def sql_db_list_tables_tool() -> List[str]:
    """
    Return the list of table names in the current database.
    """
    return sql_db_list_tables()

# -----------------------------------------------------------SQL: Tables's Schema-----------------------------------------------------------------
@mcp.tool(
        name="sql_db_schema",
        description="Return schema info (DDL + columns) and sample rows for each table."
)
def sql_db_schema_tool(tables: Optional[List[str]] = None, sample_rows: int = 3) -> Dict[str, Dict[str, Any]]:
    """
    Return schema info (DDL + columns) and up to `sample_rows` sample rows for each table.
    """
    return sql_db_schema(tables=tables, sample_rows=sample_rows)

# -----------------------------------------------------------SQL: Execute Query-----------------------------------------------------------------
@mcp.tool(
    name="sql_execute_query",
    description="Execute a SQL query and return rows.",
)
def sql_execute_query_tool(query: str, params: Optional[Dict[str, Any]] = None, max_rows: int = 1000) -> Dict[str, Any]:
    """
    Execute a provided SQL query (SQLite) safely and return rows.
    Input to this tool is a detailed and correct SQL query (use :name parameters).
    Output is {cols, rows, row_count, duration_ms, truncated}.
    """
    return sql_execute_query(query=query, params=params, row_limit=max_rows)

# -----------------------------------------------------------SQL: Validate SQL-----------------------------------------------------------------
@mcp.tool(
    name="sql_db_query_checker",
    description="double-check a SQL query before execution.",
)
def sql_db_query_checker_tool(
    dialect: str,
    query: str,
    schema_snippet: Optional[str] = None
) -> Dict[str, str]:
    """
    LLM-style query checker used BEFORE execution.
    API, but this server
    does NOT call an LLM. It returns the same query and notes.
    Use an LLM-based checker in your agent if desired.
    """
    return sql_db_query_checker(dialect=dialect, query=query, schema_snippet=schema_snippet)

# -----------------------------------------------------------SQL: Explain Query-----------------------------------------------------------------
@mcp.tool(
    name="sql_db_explain",
    description="Get SQLite EXPLAIN QUERY PLAN for a SELECT/WITH query.",
)
def sql_db_explain(query: str) -> Dict[str, Any]:
    """
    Return SQLite EXPLAIN QUERY PLAN for the provided SELECT/WITH query.
    """
    return sql_db_explain(query=query)

# ------------------------------------------------------------------RAG-------------------------------------------------------------------------

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
db_dir = "data/rag_documents/faiss_index"
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
rag_model = "gemini-2.0-flash"
threshold = 0.5
top_k = 5

db = FAISS.load_local(db_dir, embeddings, allow_dangerous_deserialization=True)
retriever = db.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": threshold}
)

@mcp.tool(
    name="rag_tool",
    description="""
    Answers from a vector DB built over: company profile, constraints/policies, current tactics, experiments log, KPI definitions, and data dictionary (`monthly_kpis`, 2015-2025).
    Use when the question touches policies/limits, KPI formulas, experiment outcomes, cadences, previous strategies, company baseline, or table coverage/keys.
    Rules: Use only retrieved text; if weak recall, say “I don't know.”.
    Inputs: query.
    Outputs: answer.
    """
)
def rag_tool(question: str) -> str:
    """
    Answers from a vector DB built over: company profile, constraints/policies, current tactics, experiments log, KPI definitions, and data dictionary (`monthly_kpis`, 2015-2025).
    Use when the question touches policies/limits, KPI formulas, experiment outcomes, cadences, previous strategies, company baseline, or table coverage/keys.
    Rules: Use only retrieved text; if weak recall, say “I don't know.”.
    Inputs: query.
    Outputs: answer.
    """
    try:
        docs = retriever.get_relevant_documents(question) or []
        docs = docs[:top_k]  
        context = "\n\n".join(d.page_content for d in docs)
        if not context.strip():
            return "I don't know from the knowledge base."

        prompt = (
            "You are a data retriever. Use only the context to answer.\n"
            "If the answer isn't in the context, say you don't know.\n"
            "Gather as much as relevant info as you can.\n"
            "Context:\n" + context + "\n"
            "Question: " + question + "\n"
            "Answer:"
        )
        resp = client.models.generate_content(model=rag_model, contents=prompt)
        text = getattr(resp, "text", "") or ""
        return text.strip() or "I don't know from the knowledge base."
    except Exception:   # exception handling given by chatgpt
        return "ERROR:\n" + traceback.format_exc()

# -----------------------------------------------------------Run Server-----------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="sse")
