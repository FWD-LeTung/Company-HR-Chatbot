import os 
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from source.retrieval.search_engine import search_hr_policies
LLM_MODEL = os.getenv("OPENAI_CHAT_MODEL")
llm = ChatOpenAI(model=LLM_MODEL, temperature=0.1)

CURRENT_DIR = Path(__file__).parent
PROMPT_PATH = CURRENT_DIR / "prompts" / "system_prompt_v1.xml"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")
prompt_template = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

def stream_hr_chatbot(user_query: str):
    # 1. Retrieval
    search_results = search_hr_policies(query=user_query, top_k=4)
    
    if not search_results:
        yield "Xin lỗi, tôi không tìm thấy tài liệu nào liên quan đến câu hỏi của bạn."
        return
    
    # 2. Format Context
    context_blocks = []
    for doc, score in search_results:
        source = doc.metadata.get('source_file', 'Tài liệu không xác định')
        context_blocks.append(f"--- Trích từ: {source} ---\n{doc.page_content}\n--- Kết thúc ---")
    
    formatted_context = "\n\n".join(context_blocks)

    # 3. Generation
    chain = prompt_template | llm
    response_stream = chain.stream({
        "context": formatted_context,
        "question": user_query
    })
    
    for chunk in response_stream:
        if chunk.content:
            yield chunk.content