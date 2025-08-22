# https://python.langchain.com/docs/tutorials/sql_qa/
from __future__ import annotations
import os, re, time, sqlite3, json
from typing import Any, Dict, List, Optional, Tuple
from mcp.server.fastmcp import FastMCP

DB_PATH = "data/company_data/Company_data.db"

if not DB_PATH:
    raise RuntimeError(
        "Set SQLITE_DB_PATH to your SQLite file, e.g. export SQLITE_DB_PATH=/mnt/data/monthly_kpis.db"
    )

# https://www.sqlite.org/uri.html
DB_URI = f"file:{os.path.abspath(DB_PATH)}?mode=ro&immutable=1&cache=shared"

DISALLOWED = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|ATTACH|DETACH|VACUUM|PRAGMA)\b",
    re.IGNORECASE
)

def ro_connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_URI, uri=True, check_same_thread=False)

def validate_sql(sql: str, allow_explain: bool = False) -> Tuple[bool, List[str]]:
    errs: List[str] = []
    if ";" in sql.strip():
        errs.append("Semicolons not allowed (single-statement only).")
    if DISALLOWED.search(sql):
        errs.append("Disallowed keyword detected (DML/DDL/PRAGMA/etc.).")
    s = sql.strip().lower()
    allowed_starts = ["select", "with"]
    if allow_explain:
        allowed_starts.append("explain")
    if not any(s.startswith(p) for p in allowed_starts):
        errs.append("Only SELECT/WITH are allowed.")
    return (len(errs) == 0, errs)

def sql_db_list_tables() -> List[str]:
    """
    Return the list of table names in the current database.
    """
    with ro_connect() as conn:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        return [r[0] for r in cur.fetchall()]

def sql_db_schema(
    tables: Optional[List[str]] = None,
    sample_rows: int = 3
) -> Dict[str, Dict[str, Any]]:
    """
    Return schema info (DDL + columns) and up to `sample_rows` sample rows for each table.
    """
    out: Dict[str, Dict[str, Any]] = {}
    with ro_connect() as conn:
        all_tables = set(sql_db_list_tables()) 
        target = all_tables if not tables else set(tables) & all_tables
        for t in sorted(target):
            ddl_row = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (t,)
            ).fetchone()
            ddl = ddl_row[0] if ddl_row else None
            cols = conn.execute(f"PRAGMA table_info('{t}')").fetchall()
            col_info = [
                {
                    "cid": c[0],
                    "name": c[1],
                    "type": c[2],
                    "notnull": c[3],
                    "default": c[4],
                    "pk": bool(c[5]),
                }
                for c in cols
            ]
            try:
                samp = conn.execute(f"SELECT * FROM '{t}' LIMIT ?;", (max(sample_rows, 0),)).fetchall()
                samp_cols = [d[0] for d in conn.execute(f"SELECT * FROM '{t}' LIMIT 0").description]
                samples = [dict(zip(samp_cols, r)) for r in samp]
            except Exception as e:
                samples = [{"error": str(e)}]
            out[t] = {"ddl": ddl, "columns": col_info, "samples": samples}
    return out

def sql_execute_query(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    row_limit: int = 10000
) -> Dict[str, Any]:
    """
    Execute a provided SQL query (SQLite) safely and return rows.
    Input to this tool is a detailed and correct SQL query (use :name parameters).
    Output is {cols, rows, row_count, duration_ms, truncated}.
    """
    params = params or {}
    ok, errs = validate_sql(query, allow_explain=False)
    if not ok:
        return {"ok": False, "error": "validation_failed", "details": errs}

    if row_limit and not re.search(r"\blimit\s+\d+\b", query, re.IGNORECASE):
        query = f"SELECT * FROM ({query}) __sub LIMIT {int(row_limit)}"
    t0 = time.time()
    try:
        with ro_connect() as conn:
            cur = conn.execute(query, params)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchall()
        ms = int((time.time() - t0) * 1000)
        return {
            "ok": True,
            "cols": cols,
            "rows": [dict(zip(cols, r)) for r in rows],
            "row_count": len(rows),
            "duration_ms": ms,
            "truncated": bool(row_limit and len(rows) >= row_limit),
        }
    except Exception as e:
        return {"ok": False, "error": "execution_error", "message": str(e)}


def sql_db_query_checker(
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
    ok, errs = validate_sql(query, allow_explain=True)
    notes = []
    if not ok:
        notes.extend(errs)
    if "select *" in query.lower():
        notes.append("Consider selecting only relevant columns (avoid SELECT *).")
    if " not in " in query.lower():
        notes.append("Check NOT IN vs NULL semantics for your dialect.")
    return {"fixed_query": query, "notes": "; ".join(notes) or "no changes"}

def sql_db_explain(query: str) -> Dict[str, Any]:
    """
    Return SQLite EXPLAIN QUERY PLAN for the provided SELECT/WITH query.
    """
    ok, errs = validate_sql(query, allow_explain=True)
    if not ok:
        return {"ok": False, "error": "validation_failed", "details": errs}
    try:
        with ro_connect() as conn:
            plan_rows = conn.execute("EXPLAIN QUERY PLAN " + query).fetchall()
        return {"ok": True, "plan": [tuple(r) for r in plan_rows]}
    except Exception as e:
        return {"ok": False, "error": "execution_error", "message": str(e)}
