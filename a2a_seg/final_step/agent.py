from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from icecream import ic
from langfuse import get_client
from dotenv import load_dotenv
import asyncio

load_dotenv()

langfuse = get_client()

SSE_URL = "http://localhost:8787/sse"


nl2sql_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="nl2sql_agent",
    instruction=(
        "ROLE: You convert a KPI analytics QUESTION into ONE valid SQLite query using ONLY the given SCHEMA.\n"
        "HARD RULES:\n"
        "- Output ONLY the SQL (no prose, no backticks, no trailing semicolon).\n"
        "- One statement only: SELECT or WITH … SELECT. Read-only (no DDL/DML).\n"
        "- Use only tables/columns present in SCHEMA. Prefer explicit column lists (avoid SELECT *).\n"
        "- Dates stored as TEXT 'YYYY-MM-DD' → use lexical ranges for filters (e.g., '2025-01-01' <= date < '2025-02-01').\n"
        "INPUT FORMAT:\n"
        "SCHEMA:\\n<table>(col type, ...)\\n...\\n\\nQUESTION:\\n<user question and any hints>\n"
        "OUTPUT:\n"
        "Only the SQL string."),
    tools=[]
)


data_analyst_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="data_analyst_agent",
    instruction=(
        "ROLE: SQL Orchestrator. You have MCP SQL tools and the write_sql agent-tool.\n"
        "GOAL: Answer the user's KPI question by producing a compact result from the database and return the FINAL SQL used.\n"
        "TOOLS YOU CAN CALL:\n"
        "- sql_db_list_tables\n"
        "- sql_db_schema (use sample_rows=0)\n"
        "- sql_db_query_checker(dialect='sqlite')\n"
        "- write_sql (the nl2sql_agent via AgentTool)\n"
        "- sql_execute_query\n"
        "PROCESS:\n"
        "1) Discover tables with sql_db_list_tables. Identify likely relevant tables from their names.\n"
        "2) Fetch schemas with sql_db_schema(sample_rows=0) for only the relevant tables (cap at ~8). Build a SCHEMA string with one line per table: table(col type, ...).\n"
        "3) Build a precise QUESTION from the user prompt (include KPI name, target, timeframe if mentioned), and use the nl2sql agent tool to create an sql query\n"
        "4) Call write_sql with:\n"
        "   SCHEMA:\\n<one line per table>\\n\\nQUESTION:\\n<precise question>\n"
        "5) Validate with sql_db_query_checker(dialect='sqlite'). If it suggests a fix, adopt the revised SQL. If invalid, apply a minimal correction and re-check at most once.\n"
        "6) Execute with sql_execute_query. If the query returns an unbounded detail set, append LIMIT 200 unless it is an aggregate report.\n"
        "7) RETURN strictly JSON with keys:\n"
        "   {\n"
        "     \"columns\": list[str],\n"
        "     \"rows\": list[list[any]],  # up to 200 rows for previews\n"
        "     \"rowcount\": int,\n"
        "     \"sql_final\": str,\n"
        "     \"tables_used\": list[str],\n"
        "     \"notes\": list[str]        # any caveats or assumptions\n"
        "   }\n"
        "CONSTRAINTS:\n"
        "- always follow use discover tables and fetch schema tools before the rest.\n"
        "- don't return a response without having tried all of your tools and agent tools\n"
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
        AgentTool(nl2sql_agent)
    ],
)


adjustments_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="adjustments_agent",
    instruction=(
        "ROLE: KPI Goal Refiner.\n"
        "INPUT: A user KPI goal, a compact summary of internal data, and web findings.\n"
        "TASKS:\n"
        "1) Parse the goal into: kpi_name, target_value/definition, timeframe, segment/scope.\n"
        "2) Infer or read baseline from provided data summary. If absent, state an assumption.\n"
        "3) Check realism vs. typical improvement ranges and the timeframe.\n"
        "4) Propose 1-3 SMART alternative goals that are:\n"
        "   - Closely related to the original intent,\n"
        "   - Measurable from the available data,\n"
        "   - Progressive if needed (e.g., phased targets).\n"
        "5) Pick the single most reasonable goal for this company as picked_goal and justify briefly.\n"
        "OUTPUT STRICT JSON:\n"
        "{\n"
        "  \"parsed_goal\": {\"kpi\": str, \"target\": str, \"timeframe\": str, \"scope\": str},\n"
        "  \"baseline\": str,\n"
        "  \"picked_goal\": str,\n"
        "  \"alt_goals\": list[str],\n"
        "  \"rationale\": str,\n"
        "  \"assumptions\": list[str]\n"
        "}\n"
        "STYLE: concise, pragmatic, no fluff."
    ),
    tools=[]
)


feasible_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="feasibility_agent",
    instruction=(
        "ROLE: Feasibility Analyst & Benchmarker.\n"
        "TOOLS: web_search → fetch; and the adjustments_agent.\n"
        "OBJECTIVE: Given a user KPI goal and (optionally) a compact internal data summary, determine feasibility and, if weak, propose better goals.\n"
        "SCALE:\n"
        "- 5 = Very feasible; 4 = Feasible (moderate effort); 3 = Borderline/risky; 2 = Unlikely w/o major changes; 1 = Not feasible.\n"
        "PROCESS:\n"
        "1) Parse the goal: KPI, target, timeframe, scope. Note baseline if provided by the orchestrator.\n"
        "2) Evidence gathering:\n"
        "   - use the web_search tool combining the KPI, industry, typical improvement rates, and timelines, and gather around 3 urls on the topic.\n"
        "   - fuse your fetch tool to Extract concrete stats, ranges, and case benchmarks from the provided urls.\n"
        "3) Rate feasibility (difficulty_score 1-5) and produce feasibility_label and a brief rationale. List key blockers and assumptions.\n"
        "4) If difficulty_score <= 2 OR evidence is weak OR internal data contradicts the goal, call adjustments_agent with the goal + data summary + distilled web facts.\n"
        "   - Receive 1-3 alt goals. Briefly re-score each (1 sentence each) and choose a recommended alternative.\n"
        "OUTPUT STRICT JSON:\n"
        "{\n"
        "  \"original_goal\": str,\n"
        "  \"kpi\": str,\n"
        "  \"difficulty_score\": int,\n"
        "  \"feasibility_label\": str,\n"
        "  \"rationale\": str,\n"
        "  \"blockers\": list[str],\n"
        "  \"assumptions\": list[str],\n"
        "  \"evidence\": [ {\"title\": str, \"url\": str, \"key_facts\": list[str]} ],\n"
        "  \"alt_goals_scored\": [ {\"goal\": str, \"score\": int, \"label\": str, \"note\": str} ],\n"
        "  \"recommended_goal\": str\n"
        "}\n"
        "RULES:\n"
        "- Prefer industry/academic sources or vendor blogs with clear data. Avoid forums unless nothing else exists.\n"
        "- Keep total fetches ≤ 4. Be concise. No speculation without marking it as an assumption.\n"
        "- If the feasibility is 2 or lower, always call the adjustments_agent to propose better goals.\n"
    ),
    tools=[
        MCPToolset(
            connection_params=SseConnectionParams(
                url="http://localhost:8787/sse"  
            ),
            tool_filter=["web_search", "fetch"], 
        )
        , AgentTool(adjustments_agent)
    ],
)

lang_agent = RemoteA2aAgent(
    name="Consulting_Agent",
    description= "A multi-agent strategy pipeline that returns an evidence-backed action plan."
                "Given a user goal or query, the graph (1) pulls internal context via RAG and develops a baseline,"
                "(2) discovers & validates competitors via web search + fetch, (3) benchmarks specified competitors" 
                " by deeper fetch/extraction, and (4) synthesizes an actionable consultant-style plan with source " 
                "citations and confidence scores.",
    agent_card="http://localhost:8009/.well-known/agent.json"
)

root_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="adk_root_agent",
    instruction=(
        "ROLE: Orchestrator for a strategy consultant workflow in ADK Web, You should never provide the neede information youtself.\n"
        "YOU CAN CALL: feasible_agent, data_analyst_agent and lang_agent (Consulting Agent).\n"
        "END GOAL: By always relying on tools and tool agent. Return a single structured JSON object that (a) summarizes relevant company data for the KPI, (b) rates feasibility, and (c) proposes adjusted goals if needed.\n"
        "PROCESS:\n"
        "1) Call data_analyst_agent with the user's goal rephrased as an analytics question to compute the most relevant KPI slices (baseline, recent trend, cohort or monthly values as applicable). Capture its JSON output and summarize as DATA_SUMMARY with: columns, key numbers, and any caveats.\n"
        "2) Call feasible_agent with the original goal and the DATA_SUMMARY to benchmark and rate feasibility. Let it call adjustments_agent if needed.\n"
        "3) Call lang_agent (Consulting Agent) with the original goal, DATA_SUMMARY, and feasibility output to synthesize a final action plan.\n"
        "4) Compose FINAL STRICT JSON with keys:\n"
        "{\n"
        "  \"kpi\": str,\n"
        "  \"original_goal\": str,\n"
        "  \"data_summary\": {\"highlights\": list[str], \"tables_used\": list[str], \"sql\": str},\n"
        "  \"feasibility\": {\"score\": int, \"label\": str, \"rationale\": str, \"blockers\": list[str], \"assumptions\": list[str]},\n"
        "  \"adjusted_goals\": list[str],\n"
        "  \"sources\": [ {\"title\": str, \"url\": str} ]\n"
        "   \"Plan\": str,\n"
        "}\n"
        "RULES:\n"
        "- data summary should only be filled by the sql agent tool.\n"
        "- Feasibility should be a score of 1-5 and only filled by the feasibility agent tool, same for adjusted goals.\n"
        "- If the SQL step fails, proceed with feasibility using web evidence and set data_summary.highlights=['No internal data available'].\n"
        "- Plan should only be filled by the Consulting Agent and at the end of the workflow.\n"
    ),
    tools=[
        AgentTool(feasible_agent),
        AgentTool(data_analyst_agent),
        AgentTool(lang_agent)  
    ],
    # sub_agents=[feasible_agent, data_analyst_agent]
)

from google.adk.a2a.utils.agent_to_a2a import to_a2a
a2a_app = to_a2a(root_agent, port=8001)

async def ADK_Run(query : str):
    APP_NAME = "Strategy_Consultant"
    agent = root_agent
    USER_ID = ""
    SESSION_ID = ""

    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    runner = Runner(
        agent=agent, app_name=APP_NAME, session_service=session_service
    )
    new_message = types.Content(
        role="user", parts=[types.Part(text=query)]
    )

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=new_message,
    ):
        final_response = ""
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response += event.content.parts[0].text
                session.state["final_answer"] = final_response
    ic(final_response)
    return {"answer": final_response} 
