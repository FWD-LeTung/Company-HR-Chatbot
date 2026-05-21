import sys
import os
from pathlib import Path
from collections import defaultdict

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from source.retrieval.search_engine import search_hr_policies
from source.retrieval.excel_reader import search_employee_with_endswith
from source.config import settings

llm = ChatOpenAI(
    model=settings.OPENAI_LLM_MODEL,
    api_key=settings.OPENAI_API_KEY,
    temperature=0.1
)

CURRENT_DIR = Path(__file__).parent
AGENT_PROMPT_PATH = CURRENT_DIR / "prompts" / "agent_system_prompt.xml"
AGENT_SYSTEM_PROMPT = AGENT_PROMPT_PATH.read_text(encoding="utf-8")

_session_store = defaultdict(InMemoryChatMessageHistory)


def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    return _session_store[session_id]


class TraCuuDanhBaInput(BaseModel):
    ten_nhan_vien: str = Field(..., description="Tên nhân viên cần tìm kiếm")


@tool("tra_cuu_danh_ba", args_schema=TraCuuDanhBaInput)
def tra_cuu_danh_ba(ten_nhan_vien: str) -> str:
    """Tìm kiếm thông tin nhân viên từ danh bạ (Excel)."""
    return search_employee_with_endswith(ten_nhan_vien)


class TraCuuChinhSachInput(BaseModel):
    query: str = Field(..., description="Câu hỏi về chính sách cần tra cứu")


@tool("tra_cuu_chinh_sach", args_schema=TraCuuChinhSachInput)
def tra_cuu_chinh_sach(query: str) -> str:
    """Tìm kiếm thông tin chính sách từ cơ sở kiến thức (Qdrant Vector DB)."""
    search_results = search_hr_policies(query=query, top_k=3)

    if not search_results:
        return "Không tìm thấy tài liệu nào liên quan đến câu hỏi của bạn."

    context_blocks = []
    for doc, score in search_results:
        source = doc.metadata.get('source_file', 'Tài liệu không xác định')
        context_blocks.append(f"--- Trích từ: {source} ---\n{doc.page_content}\n--- Kết thúc ---")

    return "\n\n".join(context_blocks)


tools = [tra_cuu_danh_ba, tra_cuu_chinh_sach]

agent_graph = create_agent(
    model=llm,
    tools=tools,
    system_prompt=AGENT_SYSTEM_PROMPT,
)


async def stream_hr_chatbot(user_query: str, session_id: str = "default"):
    history = get_session_history(session_id)
    messages = history.messages

    if len(messages) > settings.MAX_CHAT_HISTORY_MESSAGES:
        history.clear()
        for msg in messages[-settings.MAX_CHAT_HISTORY_MESSAGES:]:
            history.add_message(msg)

    chat_history = []
    for msg in history.messages:
        if isinstance(msg, HumanMessage):
            chat_history.append(msg)
        elif isinstance(msg, AIMessage):
            chat_history.append(msg)

    input_messages = chat_history + [HumanMessage(content=user_query)]

    async for event in agent_graph.astream_events(
        {"messages": input_messages},
        version="v2",
    ):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                yield content

    history.add_user_message(user_query)