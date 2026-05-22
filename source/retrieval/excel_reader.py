import polars as pl
from pathlib import Path
from source.ingestion.excel_loader import load_allowlist

_Employee_DF = None


def _get_employee_df() -> pl.DataFrame:
    """Load and cache employee DataFrame once."""
    global _Employee_DF
    if _Employee_DF is not None:
        return _Employee_DF

    allowlist = load_allowlist()
    excel_file = "Project_Employee_Contact_List_Updated.xlsx"

    if excel_file not in allowlist:
        raise ValueError(f"Excel file not in allowlist: {excel_file}")

    config = allowlist[excel_file]
    sheet_name = config["allowed_sheets"][0]
    columns = config["allowed_columns"]

    df = pl.read_excel(
        Path("raw-data") / excel_file,
        engine="calamine",
        sheet_name=sheet_name,
        columns=columns,
    )

    _Employee_DF = df
    return _Employee_DF


def search_employee_with_endswith(ten_nhan_vien: str, chuc_danh: str = None) -> str:
    df = _get_employee_df()

    normalized_query = ten_nhan_vien.lower().strip()
    mask = df["Full name"].str.to_lowercase().str.strip_chars().str.ends_with(normalized_query)
    results = df.filter(mask)
        
    # Thêm bộ lọc Chức danh nếu LLM trích xuất được
    if chuc_danh:
        results = results.filter(
            pl.col("Chức danh tiếng Việt").str.to_lowercase().str.contains(chuc_danh.lower().strip())
        )

    count = len(results)

    if count == 0:
        return f"Không tìm thấy nhân viên nào có tên '{ten_nhan_vien}' phù hợp với tiêu chí công việc/chức danh."

    if count == 1:
        row = results.row(0, named=True)
        parts = [f"{k}: {v}" for k, v in row.items()]
        return " | ".join(parts)

    # LẤY DANH SÁCH TÊN VÀ CHỨC DANH ĐỂ HIỂN THỊ
    names = results["Full name"].to_list()
    roles = results["Chức danh tiếng Việt"].to_list()
    
    # Kẹp Tên đi kèm với Chức danh để Agent dễ hỏi lại người dùng
    name_list = ", ".join([f"'{n}' (Chức danh: {r})" for n, r in zip(names, roles)])

    return (
        f"Hệ thống tìm thấy {count} người trùng khớp là: {name_list}. "
        f"Bạn hãy dừng lại ngay lập tức và yêu cầu người dùng xác nhận rõ họ muốn tìm ai trong số này "
        f"(gợi ý người dùng cung cấp thêm Công việc người đó làm hoặc Chức danh). "
        f"Tuyệt đối chưa được cung cấp thông tin liên hệ ở bước này."
    )