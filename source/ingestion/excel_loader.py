import json
from pathlib import Path
from typing import Any
import polars as pl
from langchain_core.documents import Document


def load_allowlist() -> dict[str, dict[str, Any]]:
    """Đọc file cấu hình allowlist từ raw-data/excel_allowlist.json"""
    # Lấy thư mục gốc của dự án (giả định chạy từ thư mục gốc)
    project_root = Path(__file__).parent.parent.parent
    allowlist_path = project_root / "raw-data" / "excel_allowlist.json"

    if not allowlist_path.exists():
        return {}

    with open(allowlist_path, "r", encoding="utf-8") as f:
        return json.load(f)


def process_excel_polars(path: Path) -> list[Document]:
    """
    Đọc file Excel với Polars + Calamine engine, có kiểm soát Allowlist.

    Args:
        path: Đường dẫn đến file Excel

    Returns:
        Danh sách Document chứa các bản ghi từ Excel
    """
    filename = path.name
    allowlist = load_allowlist()

    # Kiểm tra file có trong allowlist không
    if filename not in allowlist:
        print(f"  -> [Polars/Calamine] Bỏ qua file không có trong allowlist: {filename}")
        return []

    file_config = allowlist[filename]
    allowed_sheets = file_config.get("allowed_sheets", [])
    allowed_columns = file_config.get("allowed_columns", [])

    if not allowed_sheets:
        print(f"  -> [Polars/Calamine] Không có sheet nào được phép trong allowlist cho: {filename}")
        return []

    if not allowed_columns:
        print(f"  -> [Polars/Calamine] Không có cột nào được phép trong allowlist cho: {filename}")
        return []

    documents = []

    for sheet_name in allowed_sheets:
        print(f"  -> [Polars/Calamine] Đang đọc sheet '{sheet_name}' từ {filename}")

        try:
            # Đọc Excel với engine calamine, filter columns ngay từ đầu
            df = pl.read_excel(
                path,
                engine="calamine",
                sheet_name=sheet_name,
                columns=allowed_columns,
            )

            # Xóa các dòng bị null hoàn toàn
            df = df.filter(~pl.all_horizontal(pl.all().is_null()))

            if df.is_empty():
                print(f"  -> [Polars/Calamine] Sheet '{sheet_name}' không có dữ liệu sau khi filter")
                continue

            # Lặp qua từng dòng và tạo Document
            for row_idx in range(df.height):
                row_data = df.row(row_idx, named=True)

                # Lọc bỏ các giá trị null
                filtered_data = {k: v for k, v in row_data.items() if v is not None}

                if not filtered_data:
                    continue

                # Gộp nội dung thành text thân thiện với LLM
                parts = [f"[Bản ghi Nhân sự | Dòng: {row_idx + 2}]"]  # +2 vì row 0 là header, row_idx bắt đầu từ 0
                for col_name, value in filtered_data.items():
                    parts.append(f"{col_name}: {value}")

                text_content = " | ".join(parts)

                documents.append(
                    Document(
                        page_content=text_content,
                        metadata={
                            "source_file": filename,
                            "file_type": "xlsx",
                            "sheet": sheet_name,
                            "row_range": row_idx + 2,
                            "parser": "polars_calamine",
                        }
                    )
                )

            print(f"  -> [Polars/Calamine] Đã xử lý {len(documents)} bản ghi từ sheet '{sheet_name}'")

        except Exception as e:
            print(f"  -> [Polars/Calamine ERROR] Không thể đọc sheet '{sheet_name}' trong {filename}: {e}")
            continue

    return documents