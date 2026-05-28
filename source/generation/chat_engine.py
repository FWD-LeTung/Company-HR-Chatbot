import sys
import os
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from pydantic import BaseModel, Field
from typing import Optional
from langgraph.checkpoint.memory import MemorySaver

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from source.retrieval.search_engine import search_hr_policies, hybrid_search_hr_policies
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
    """Tìm kiếm các quy định, chế độ, và chính sách nhân sự của công ty từ cơ sở tri thức (Vector DB + BM25)."""

    search_results = hybrid_search_hr_policies(
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

memory = MemorySaver()

agent_graph = create_agent(
    model=llm,
    tools=tools,
    system_prompt=AGENT_SYSTEM_PROMPT,
    checkpointer=memory,
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


FALLBACK_MSG = ("Tôi không có câu trả lời cho câu hỏi này. "
                "Các thông tin về hành chính vui lòng liên hệ HR Admin Nguyễn Thị Quỳnh Anh - SĐT 0913244513. "
                "Các thông tin về chương trình đào tạo và học tập vui lòng liên hệ HR L&D Bùi Thị Hà - SĐT 0313214512")


async def stream_hr_chatbot(user_query: str, session_id: str = "default", user_id: str | None = None):
    trace_handler, trace_metadata = _get_trace_config(session_id, user_id)

    config = {
        "callbacks": [trace_handler],
        "metadata": trace_metadata,
        "configurable": {"thread_id": session_id}
    }

    tool_was_called = False
    tool_results = {}

    async for state_update in agent_graph.astream(
        {"messages": [("user", user_query)]},
        config=config,
    ):
        for node_name, node_state in state_update.items():
            if "messages" not in node_state:
                continue

            for msg in node_state["messages"]:
                msg_type = type(msg).__name__

                # Track tool calls
                if msg_type == "AIMessage" and hasattr(msg, 'tool_calls') and len(msg.tool_calls) > 0:
                    tool_was_called = True

                # Track tool results
                if msg_type == "ToolMessage":
                    tool_results[msg.name] = msg.content

                # Chỉ stream AIMessage có text content, bỏ qua tool_calls
                if msg_type == "AIMessage":
                    has_tool_calls = hasattr(msg, 'tool_calls') and len(msg.tool_calls) > 0
                    if not has_tool_calls and hasattr(msg, 'content') and isinstance(msg.content, str) and msg.content:
                        if not tool_was_called:
                            yield FALLBACK_MSG
                            trace_handler._langfuse_client.flush()
                            return

                        if tool_results and all("Không tìm thấy" in r for r in tool_results.values()):
                            yield FALLBACK_MSG
                            trace_handler._langfuse_client.flush()
                            return

                        yield msg.content

    trace_handler._langfuse_client.flush()