import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from source.generation.chat_engine import stream_hr_chatbot

if __name__ == "__main__":
    print("\n" + "="*50)
    print(" HỆ THỐNG RAG CHATBOT - PHIÊN BẢN STREAMING")
    print("="*50)
    
    while True:
        user_input = input("\n[Nhân viên]: ")
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Tạm biệt!")
            break
            
        if not user_input.strip():
            continue
            
        print("\n [Trợ lý HR]:\n")
        
        # Bắt đầu nhận luồng Stream
        for text_chunk in stream_hr_chatbot(user_input):
            print(text_chunk, end="", flush=True)
            
        print("\n\n" + "-"*50)