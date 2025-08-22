# in the following file some of the exception hnadling was done through chatgpt
from typing import Annotated
import os, json, traceback, asyncio
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp import ClientSession
from mcp.client.sse import sse_client
from langchain_mcp_adapters.tools import load_mcp_tools

load_dotenv()
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.1,
    max_retries=5,
    google_api_key=GOOGLE_API_KEY,
)

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    rag_output: str
    Baseline: str
    Competitors: str
    Benchmark: str
    Plan: str

system_prompt = SystemMessage(
    "You are an agent that is connected to a web search tool and fecth tool"
    "You should primarly research the stated similar competitors to the company and use the web search to get the relevant urls"
    "Once you have used the web search tool, you should use the fetch tool to get the content of the urls."
    "Your goal is to gather relevant information from the web to answer the user's query."
    "Everything that might be relevant to developping a plan to achieve the user's goal should be retrieved."
)

Competitor_system_prompt = SystemMessage(
    "You are an agent that is connected to a web search tool and fecth tool"
    "You should primarly search for similar competitors to the company"
    "and use the web search to get the relevant urls and fecth to validate the competitors"
)


tool_map = {}
web_llm = None
graph = None

async def Benchmark_model(state: State, config: RunnableConfig):
    model_input = [system_prompt] + state["messages"]
    print(f"--- Sending to model: {model_input}")
    response = await web_llm.ainvoke(model_input, config)
    return {"messages": [response]}

async def ben_tool_node(state: State):
    outputs = []
    last = state["messages"][-1]
    for call in getattr(last, "tool_calls", []) or []:
        name = call["name"]; args = call.get("args", {}) or {}
        try:
            result = await tool_map[name].ainvoke(args)
            content = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
            outputs.append(ToolMessage(content=content, name=name, tool_call_id=call["id"]))
        except Exception as e:
            err_text = f"CLIENT TOOL ERROR: {repr(e)}\n{traceback.format_exc()}"
            outputs.append(ToolMessage(content=err_text, name=name, tool_call_id=call["id"]))
    return {"Benchmark": outputs}


async def Competitors_model(state: State, config: RunnableConfig):
    model_input = [Competitor_system_prompt] + state["messages"]
    print(f"--- Sending to model: {model_input}")
    response = await web_llm.ainvoke(model_input, config)
    return {"messages": [response]}

async def comp_tool_node(state: State):
    outputs = []
    last = state["messages"][-1]
    for call in getattr(last, "tool_calls", []) or []:
        name = call["name"]; args = call.get("args", {}) or {}
        try:
            result = await tool_map[name].ainvoke(args)
            content = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
            outputs.append(ToolMessage(content=content, name=name, tool_call_id=call["id"]))
        except Exception as e:
            err_text = f"CLIENT TOOL ERROR: {repr(e)}\n{traceback.format_exc()}"
            outputs.append(ToolMessage(content=err_text, name=name, tool_call_id=call["id"]))
    return {"Competitors": outputs}

def should_continue(state: State):
    last = state["messages"][-1]
    return "continue" if getattr(last, "tool_calls", []) else "end"

async def run_chat_loop():
    state: State = {"messages": [], "rag_output": "", "Baseline": "", "Competitors":"", "Benchmark": "", "Plan": ""}
    while True:
        user_input = input("Message: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting chatbot.")
            break
        if not user_input:
            continue
        state["messages"] = state.get("messages", []) + [HumanMessage(content=user_input)]
        state = await graph.ainvoke(state)
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage):
                print("Assistant:", msg.content)
                break

async def main():
    global tool_map, web_llm, graph
    async with sse_client("http://localhost:8787/sse") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await load_mcp_tools(session=session)
            tool_map = {t.name: t for t in tools}
            print("MCP tools:", list(tool_map.keys()))

            web_llm = model.bind_tools([tool_map["web_search"], tool_map["fetch"]])

            graph_builder = StateGraph(State)
            graph_builder.add_node("Benchmark_model", Benchmark_model)
            graph_builder.add_node("ben_tool_node", ben_tool_node)
            graph_builder.add_node("comp_model", Competitors_model)
            graph_builder.add_node("comp_tool_node", comp_tool_node)

            graph_builder.add_conditional_edges(
                "Benchmark_model",
                should_continue,
                {"continue": "ben_tool_node", "end": END},
            )
            graph_builder.add_conditional_edges(
                "comp_model",
                should_continue,
                {"continue": "comp_tool_node", "end": "Benchmark_model"},
            )
            graph_builder.add_edge("ben_tool_node", "Benchmark_model")
            graph_builder.add_edge("comp_tool_node", "comp_model")
            graph_builder.set_entry_point("comp_model")
            graph = graph_builder.compile()

            try:
                img = graph.get_graph().draw_mermaid_png()
                with open("graph_web.png", "wb") as f:
                    f.write(img)
                print("Graph saved as graph.png")
            except Exception:
                pass

            await run_chat_loop()

if __name__ == "__main__":
    asyncio.run(main())
