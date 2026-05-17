18/5:
- Sử dụng Pydantic(BaseModel) thay cho TypedDict, FastAPI được xây dựng trên nền tảng của Pydantic, nên việc dùng BaseModel sẽ giúp:
    - Tự động validate (kiểm tra) dữ liệu: Đảm bảo không truyền nhầm kiểu dữ liệu (ví dụ truyền string vào page thay vì số nguyên).
    - Gán giá trị mặc định dễ dàng: Tự động tạo timestamp created_at mà không cần code thừa.
    - Tích hợp mượt mà với FastAPI: Dễ dàng dùng làm schema trả về hoặc nhận dữ liệu qua API.