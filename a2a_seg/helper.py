# langgraph server
import click, asyncio, uvicorn, httpx, sys
from icecream import ic
from dotenv import load_dotenv
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage, ToolMessage
from a2a.types import (
    InternalError,
    InvalidParamsError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
    AgentCapabilities, AgentCard, AgentSkill
)
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    TaskUpdater,
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.utils import new_task, new_agent_text_message
from a2a.utils.errors import ServerError
# from lang_workflow import graph as Consultant  
from lang_workflow import init_graph_and_tools, State

load_dotenv()

class ConsultantWrapper:
    def __init__(self):
        self.graph = None
        self._lock = asyncio.Lock()

    async def _ensure_ready(self):
        if self.graph is None:
            async with self._lock:
                if self.graph is None:
                    self.graph = await init_graph_and_tools()

    async def run(self, query: str, context_id: str):
        await self._ensure_ready()
        state: State = {
            "messages": [HumanMessage(content=query)],
            "rag_output": "",
            "Baseline": "",
            "Competitors": "",
            "Benchmark": "",
            "Plan": "",
        }
        final_state = await self.graph.ainvoke(state)
        msg_content = ""
        for m in reversed(final_state["messages"]):
            if isinstance(m, AIMessage):
                msg_content = m.content
                break
        yield {
            "is_task_complete": True,
            "require_user_input": False,
            "content": msg_content or "[empty response]",
        }

class ConsultantExecutor(AgentExecutor):
    def __init__(self):
        self.agent = ConsultantWrapper()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            async for item in self.agent.run(query, task.context_id):
                is_task_complete = item["is_task_complete"]
                require_user_input = item["require_user_input"]
                content = item["content"]

                if not is_task_complete and not require_user_input:
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(content, task.context_id, task.id),
                    )
                elif require_user_input:
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(content, task.context_id, task.id),
                        final=True,
                    )
                    break
                else:
                    await updater.add_artifact(
                        [Part(root=TextPart(text=content))], name="consultant_response"
                    )
                    await updater.complete()
                    break

        except Exception as e:
            ic(f"Error while streaming response: {e}")
            raise ServerError(error=InternalError()) from e
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())

        
@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=8009)
def main(host, port):
    """Starts the Consultant Agent server."""
    try:
        agent_card = AgentCard(
            name='Consultant Agent',
            description="A multi-agent strategy pipeline that returns an evidence-backed action plan."
                "Given a user goal or query, the graph (1) pulls internal context via RAG and develops a baseline,"
                "(2) discovers & validates competitors via web search + fetch, (3) benchmarks specified competitors" 
                " by deeper fetch/extraction, and (4) synthesizes an actionable consultant-style plan with source " 
                "citations and confidence scores.",
            url=f'http://{host}:{port}/',
            version='1.0.0',
            default_input_modes=["text"],
            default_output_modes=["text"],
            capabilities= AgentCapabilities(streaming=True, push_notifications=True),
            skills=[AgentSkill(
                id='consultant_advice',
                name='Consultant Tool',
                description=
                "A multi-agent strategy pipeline that returns an evidence-backed action plan."
                "Given a user goal or query, the graph (1) pulls internal context via RAG and develops a baseline,"
                "(2) discovers & validates competitors via web search + fetch, (3) benchmarks specified competitors" 
                " by deeper fetch/extraction, and (4) synthesizes an actionable consultant-style plan with source " 
                "citations and confidence scores.",
                tags=['legal', 'compliance', 'guidance'],
                examples=['I want to reach a 30% reduction in cost to serve how could i execute this plan?']
            )]
        )

        httpx_client = httpx.AsyncClient()
        push_config_store = InMemoryPushNotificationConfigStore()
        push_sender = BasePushNotificationSender(
            httpx_client=httpx_client,
            config_store=push_config_store
        )
        try:
            request_handler = DefaultRequestHandler(
                agent_executor=ConsultantExecutor(),
                task_store=InMemoryTaskStore(),
                push_config_store=push_config_store,
                push_sender=push_sender
            )
        except Exception as e:
            ic(f'Error initializing request handler: {e}')
            sys.exit(1)

        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler
        )
        uvicorn.run(server.build(), host=host, port=port)
    except Exception as e:
        ic(f'An error occurred during server startup: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
