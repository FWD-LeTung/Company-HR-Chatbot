import sys
import os
from pathlib import Path
from typing import List
from collections import defaultdict

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables import RunnableConfig

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from source.retrieval.search_engine import search_hr_policies
from source.config import settings

llm = ChatOpenAI(model=settings.OPENAI_LLM_MODEL,
                 api_key=settings.OPENAI_API_KEY
                 ,temperature=0.1
                 )

CURRENT_DIR = Path(__file__).parent
PROMPT_PATH = CURRENT_DIR / "prompts" / "system_prompt_v1.xml"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")

prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])

_session_store = defaultdict(InMemoryChatMessageHistory)


def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    return _session_store[session_id]


base_chain = prompt_template | llm

chain = RunnableWithMessageHistory(
    base_chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="chat_history",
)


def stream_hr_chatbot(user_query: str, session_id: str = "default"):
    search_results = search_hr_policies(query=user_query, top_k=3)

    if not search_results:
        yield "Xin lỗi, tôi không tìm thấy tài liệu nào liên quan đến câu hỏi của bạn."
        return

    context_blocks = []
    for doc, score in search_results:
        source = doc.metadata.get('source_file', 'Tài liệu không xác định')
        context_blocks.append(f"--- Trích từ: {source} ---\n{doc.page_content}\n--- Kết thúc ---")

    formatted_context = "\n\n".join(context_blocks)

    history = get_session_history(session_id)
    messages = history.messages

    if len(messages) > settings.MAX_CHAT_HISTORY_MESSAGES:
        history.clear()
        for msg in messages[-settings.MAX_CHAT_HISTORY_MESSAGES:]:
            history.add_message(msg)

    config: RunnableConfig = {"configurable": {"session_id": session_id}}

    response_stream = chain.stream(
                        {
                            "context": formatted_context,
                            "question": user_query,
                        },
                        config=config,
        )

    for chunk in response_stream:
        if chunk.content:
            yield chunk.content