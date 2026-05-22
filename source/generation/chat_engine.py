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
from typing import Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from source.retrieval.search_engine import search_hr_policies
from source.retrieval.excel_reader import search_employee_with_endswith
from source.config import settings

from langfuse.langchain import CallbackHandler

os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.LANGFUSE_PUBLIC_KEY)
os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.LANGFUSE_SECRET_KEY)
os.environ.setdefault("LANGFUSE_HOST", settings.LANGFUSE_BASE_URL)

langfuse_handler = CallbackHandler()

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
    ten_nhan_vien: str = Field(
        ..., 
        description="Tên của nhân viên cần tìm kiếm. Lưu ý: Cần trích xuất đầy đủ tên chính có nghĩa (ví dụ: lấy 'Trang Anh', 'Đức Anh' thay vì chỉ lấy từ cuối cùng là 'Anh') để kết quả tự nhiên và chính xác nhất."
    )
    
    chuc_danh: Optional[str] = Field(
        None, 
        description="Chức danh hoặc vị trí công việc của nhân viên (ví dụ: 'Kỹ sư hệ thống', 'Chuyên viên kinh doanh', 'Trưởng nhóm'). Bỏ trống nếu không rõ."
    )


@tool("tra_cuu_danh_ba", args_schema=TraCuuDanhBaInput)
def tra_cuu_danh_ba(ten_nhan_vien: str, chuc_danh: Optional[str] = None) -> str:
    """Tìm kiếm thông tin nhân viên từ danh bạ (Excel)."""
    return search_employee_with_endswith(
        ten_nhan_vien=ten_nhan_vien, 
        chuc_danh=chuc_danh
    )


class TraCuuChinhSachInput(BaseModel):
    query: str = Field(..., description="Từ khóa hoặc nội dung câu hỏi về chính sách cần tra cứu. Cần được rút gọn và tập trung vào ý chính (ví dụ: 'quy định nghỉ phép năm', 'chế độ thai sản').")
    source_file_filter: Optional[str] = Field(None, description="Tên file tài liệu nếu người dùng có chỉ định cụ thể nguồn cần tra cứu (ví dụ: 'So_tay_nhan_vien_2024.pdf', 'Quy_dinh_nhan_su'). Bỏ trống nếu không nhắc đến.")
    category_filter: Optional[str] = Field(None, description="Danh mục của chính sách nếu có thể phân loại được. Bỏ trống nếu không xác định.")


@tool("tra_cuu_chinh_sach", args_schema=TraCuuChinhSachInput)
def tra_cuu_chinh_sach(query: str, source_file_filter: Optional[str] = None, category_filter: Optional[str] = None) -> str:
    """Tìm kiếm các quy định, chế độ, và chính sách nhân sự của công ty từ cơ sở tri thức (Vector DB)."""
    
    # Truyền thêm các bộ lọc vào hàm search_hr_policies
    search_results = search_hr_policies(
        query=query, 
        top_k=3,
        source_file_filter=source_file_filter,
        category_filter=category_filter
    )

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


def _get_trace_config(session_id: str, user_id: str | None = None):
    handler = CallbackHandler()
    metadata = {
        "langfuse_trace_name": "hr-chatbot-chat",
        "langfuse_session_id": session_id,
        "langfuse_tags": ["hr-chatbot"],
    }
    if user_id:
        metadata["langfuse_user_id"] = user_id
    return handler, metadata


async def stream_hr_chatbot(user_query: str, session_id: str = "default", user_id: str | None = None):
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

    trace_handler, trace_metadata = _get_trace_config(session_id, user_id)

    full_response = ""
    async for event in agent_graph.astream_events(
        {"messages": input_messages},
        version="v2",
        config={"callbacks": [trace_handler], "metadata": trace_metadata},
    ):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                full_response += content
                yield content

    trace_handler._langfuse_client.flush()
    history.add_user_message(user_query)
    history.add_message(AIMessage(content=full_response))