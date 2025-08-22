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
    Benchmark: str
    Plan: str

system_prompt = SystemMessage(
    "You are an agent that is connected to a rag tool node."
    "Your goal is to gather as much as relevant information as possible to answer the user's query."
    "Everything that might be relevant to developping a plan to achieve the user's should be retrieved."
)


tool_map = {}
rag_llm = None
graph = None

async def Baseline_model(state: State, config: RunnableConfig):
    model_input = [system_prompt] + state["messages"]
    print(f"--- Sending to model: {model_input}")
    response = await rag_llm.ainvoke(model_input, config)
    return {"messages": [response]}

async def tool_node(state: State):
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
    return {"messages": outputs}

def should_continue(state: State):
    last = state["messages"][-1]
    return "continue" if getattr(last, "tool_calls", []) else "end"

async def run_chat_loop():
    state: State = {"messages": [], "rag_output": "", "Baseline": "", "Benchmark": "", "Plan": ""}
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
                print("Consultant", msg.content)
                break

async def main():
    global tool_map, rag_llm, graph
    async with sse_client("http://localhost:8787/sse") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await load_mcp_tools(session=session)
            tool_map = {t.name: t for t in tools}
            print("Available MCP tools:", list(tool_map.keys()))
    
            rag_llm = model.bind_tools([tool_map["rag_tool"]])

            graph_builder = StateGraph(State)
            graph_builder.add_node("Baseline_model", Baseline_model)
            graph_builder.add_node("tool_node", tool_node)
            graph_builder.add_conditional_edges(
                "Baseline_model",
                should_continue,
                {"continue": "tool_node", "end": END},
            )
            graph_builder.add_edge("tool_node", "Baseline_model")
            graph_builder.set_entry_point("Baseline_model")
            graph = graph_builder.compile()

            try:
                img = graph.get_graph().draw_mermaid_png()
                with open("graph.png", "wb") as f:
                    f.write(img)
                print("Graph saved as graph.png")
            except Exception:
                pass

            await run_chat_loop()

if __name__ == "__main__":
    asyncio.run(main())
