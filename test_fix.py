import asyncio
from source.generation.chat_engine import stream_hr_chatbot, get_session_history

async def test_chat():
    session_id = "test_session"

    # Test 1: First question
    print("\n=== Câu hỏi 1: Quy chuẩn định dạng văn bản ===")
    response1 = ""
    async for chunk in stream_hr_chatbot("Quy chuẩn định dạng văn bản", session_id):
        response1 += chunk
    print(f"Response: {response1[:200]}...")

    # Test 2: Second question (should maintain context)
    print("\n=== Câu hỏi 2: Chấm công ngày công tác như thế nào ===")
    response2 = ""
    async for chunk in stream_hr_chatbot("Chấm công ngày công tác như thế nào", session_id):
        response2 += chunk
    print(f"Response: {response2[:200]}...")

    # Test 3: Third question (checking if history works correctly)
    print("\n=== Câu hỏi 3: Contact câu lạc bộ bơi ===")
    response3 = ""
    async for chunk in stream_hr_chatbot("Contact câu lạc bộ bơi", session_id):
        response3 += chunk
    print(f"Response: {response3[:200]}...")

    # Check history
    history = get_session_history(session_id)
    print(f"\n=== Total messages in history: {len(history.messages)} ===")
    for i, msg in enumerate(history.messages):
        msg_type = type(msg).__name__
        content = str(msg.content)[:100] if hasattr(msg, 'content') else 'N/A'
        print(f"{i}. [{msg_type}] {content}...")

if __name__ == "__main__":
    asyncio.run(test_chat())