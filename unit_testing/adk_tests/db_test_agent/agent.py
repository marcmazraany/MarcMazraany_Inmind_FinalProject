from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

SSE_URL = "http://localhost:8787/sse"

sql_writer_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="sql_writer_agent",
    instruction=(
        "You write a SINGLE valid SQLite query (SELECT or WITH…SELECT) using ONLY the provided schema.\n"
        "Rules:\n"
        "- No comments or prose. No backticks. No trailing semicolon.\n"
        "- Prefer explicit columns (avoid SELECT *).\n"
        "- Months are TEXT 'YYYY-MM-DD'; filter with lexical ranges.\n"
        "- Use NULLIF to avoid divide-by-zero.\n"
        "Input string format:\n"
        "SCHEMA:\\n<table>(col type, ...)\\n...\\n\n"
        "QUESTION:\\n<Natural-language question>\n"
        "Output: ONLY the SQL string."
    ),
    tools=[]
)

write_sql_tool = AgentTool(sql_writer_agent)

root_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="sql_orchestrator_agent",
    instruction=(
        "You have MCP SQL tools and the write_sql agent-tool.\n"
        "Plan:\n"
        "1) sql_db_list_tables\n2) sql_db_schema (use sample_rows=0)\n"
        "3) write_sql with:\n"
        "   SCHEMA:\\n<one line per table: table(col type, ...)>\\n\\nQUESTION:\\n<user question>\n"
        "4) sql_db_query_checker(dialect='sqlite')\n5) sql_db_query\n"
        "Return a concise table and the final SQL."
    ),
    tools=[
        MCPToolset(
            connection_params=SseConnectionParams(url=SSE_URL),
            tool_filter=[
                "sql_db_list_tables",
                "sql_db_schema",
                "sql_db_query_checker",
                "sql_execute_query",
            ],
        ),
        write_sql_tool
    ],
)
