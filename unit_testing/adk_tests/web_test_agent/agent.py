from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

root_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="mcp_client_agent",
    instruction=(
        "You have access to two MCP tools: web_search and fetch. "
        "Use web_search to find candidate URLs, then fetch to read a page."
    ),
    tools=[
        MCPToolset(
            connection_params=SseConnectionParams(
                url="http://localhost:8787/sse"  
            ),
            tool_filter=["web_search", "fetch"], 
        )
    ],
)
