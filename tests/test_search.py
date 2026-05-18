import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from source.retrieval.search_engine import search_hr_policies

def in_ket_qua(results):
    for i, (doc, score) in enumerate(results, 1):
        print(f"\nTOP {i} | Độ tin cậy (Score): {score:.4f}")
        print(f"Nguồn: {doc.metadata.get('source_file')}")
        print(f"Danh mục: {doc.metadata.get('category', 'Không có')}")
        print("-" * 40)
        # In 200 ký tự đầu tiên để xem trước
        print(f"{doc.page_content[:200]}...")
    print("="*60)

if __name__ == "__main__":
    # Câu hỏi từ người dùng
    user_query = "Chính sách thi chứng chỉ được hỗ trợ bao nhiêu tiền?"
    
    print("============================================================")
    print("TEST CASE 1: TÌM KIẾM VECTOR THUẦN TÚY (KHÔNG LỌC)")
    print("============================================================")
    # Tìm tự do trên toàn bộ kho dữ liệu
    results_no_filter = search_hr_policies(query=user_query, top_k=2)
    in_ket_qua(results_no_filter)
    
    
    print("\n============================================================")
    print("TEST CASE 2: TÌM KIẾM VECTOR KÈM BỘ LỌC METADATA (Lọc đúng file)")
    print("============================================================")
    target_file = "12.CS.SVTECH_Chinh sach phat trien nang luc chung chi ky thuat v1.6.pdf"
    
    results_with_filter = search_hr_policies(
        query=user_query, 
        top_k=2,
        source_file_filter=target_file
    )
    in_ket_qua(results_with_filter)