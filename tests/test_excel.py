import os
import sys
from pathlib import Path

# Đảm bảo import đúng đường dẫn root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from source.ingestion.loaders import load_file

def test_excel_pipeline():
    print("\n" + "="*60)
    print("🚀 BẮT ĐẦU TEST LUỒNG XỬ LÝ EXCEL (POLARS + ALLOWLIST)")
    print("="*60)

    # Khai báo đường dẫn tới file Excel thực tế của bạn
    # Sửa lại tên file dưới đây cho khớp với file trong raw-data của bạn
    excel_filename = "Project_Employee_Contact_List_Updated.xlsx" 
    
    # Tìm đường dẫn tuyệt đối tới file
    root_dir = Path(__file__).parent.parent
    file_path = root_dir / "raw-data" / excel_filename

    if not file_path.exists():
        print(f"❌ LỖI: Không tìm thấy file thử nghiệm tại:\n{file_path}")
        print("Vui lòng copy một file Excel vào đó hoặc sửa lại tên file trong script này.")
        return

    print(f"📂 Đang nạp file: {file_path.name}")
    
    # Kích hoạt Loader
    documents = load_file(file_path)

    if not documents:
        print("\n⚠️ Kết quả: 0 Documents.")
        print("Nguyên nhân có thể do: Tên file không có trong excel_allowlist.json, hoặc file trống.")
        return

    print(f"\n✅ THÀNH CÔNG! Đã trích xuất {len(documents)} bản ghi an toàn.")
    print("-" * 60)
    
    # In ra 3 bản ghi đầu tiên để kiểm tra trực quan
    for i, doc in enumerate(documents[:3], 1):
        print(f"🎯 BẢN GHI SỐ {i}:")
        print(f"[Nội dung LLM sẽ đọc]:\n{doc.page_content}")
        print(f"\n[Metadata ẩn]:")
        for key, value in doc.metadata.items():
            print(f"  - {key}: {value}")
        print("-" * 60)

if __name__ == "__main__":
    test_excel_pipeline()