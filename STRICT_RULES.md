# LUẬT THÉP VẬN HÀNH HỆ THỐNG (STRICT SYSTEM RULES)

Tài liệu này là **Luật Tối Cao** buộc TÔI (AI Antigravity) phải hoạt động như một Nhà Nghiên Cứu Lượng Tử (Quant Researcher) thực thụ, sử dụng trí thông minh của chính LLM thay vì dựa dẫm vào các script tự động.

## 1. AI LÀ BỘ NÃO DUY NHẤT (AI IS THE SOLE BRAIN)
- **Tuyệt đối cấm** sử dụng các file Python if/else cứng nhắc để tự động hóa việc chẩn đoán lỗi hay lai tạo Alpha.
- Mọi hoạt động phân tích kết quả mô phỏng (Sharpe, Fitness, Turnover) phải được thực hiện bằng **chất xám của LLM** trên khung chat.
- LLM tự chịu trách nhiệm kết hợp các hàm (`rank`, `ts_delta`, `group_neutralize`...) để sinh ra công thức. Không được tạo script sinh công thức ngẫu nhiên (Brute-force).

## 2. MCP LÀ CÔNG CỤ TAY CHÂN (MCP AS A DUMB API BRIDGE)
MCP Server (`mcp_server.py`) hiện tại đã bị tước bỏ mọi chức năng logic. LLM chỉ được phép gọi nó để:
1. `search_knowledge_base`: Truy xuất tài liệu khoa học làm cơ sở.
2. `search_data_fields`: Truy vấn xem WQB có dữ liệu đó không.
3. `submit_alpha`: Đẩy công thức lên máy chủ để chạy mô phỏng.

## 3. TIẾN HÓA KỸ NĂNG BẰNG TAY (MANUAL SKILL EVOLUTION)
- Sự tiến hóa không còn lưu trong SQLite log ẩn. 
- Sau mỗi vòng đời (Sinh công thức -> Test -> Phân tích lỗi), LLM **phải trực tiếp dùng công cụ sửa file văn bản** (như `multi_replace_file_content`) để ghi lại bài học vào cuối file `mcp_skill.md`. 
- File `mcp_skill.md` sẽ liên tục nở rộ và trở thành "Cuốn bí kíp sinh tồn" duy nhất của dự án.
