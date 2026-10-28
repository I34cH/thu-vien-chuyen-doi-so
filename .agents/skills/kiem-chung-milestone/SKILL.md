---
name: kiem-chung-milestone
description: Dùng trước khi báo một milestone (M1–M6) của web thư viện là xong — chạy lệnh kiểm chứng, audit theo AGENTS.md, ghi reports/milestones/Mx.md.
---

# Kiểm chứng milestone

1. Mở `prompts/01-teamwork.md`, tìm mục của milestone, chép LỆNH KIỂM CHỨNG.
2. Chạy lệnh trong PowerShell tại thư mục gốc CK. Lưu toàn bộ output.
3. Nếu lỗi: KHÔNG ghi "xong". Trả lỗi cho implement, quay lại bước 2. Quá 3 vòng → ghi trạng thái "kẹt" và đề nghị /boost.
4. Audit nhanh theo checklist:
   - [ ] Không có tính năng ngoài AGENTS.md mục 4.
   - [ ] Mọi SQL dùng tham số `$1`.
   - [ ] Route mới có middleware `yeuCauVaiTro` đúng vai trò.
   - [ ] API thống kê không trả `nguoi_dung_id`, `ma_phien`.
   - [ ] Dữ liệu sinh ra có `du_lieu_mau = true`.
   - [ ] Không còn mã màu navy trong `public/`.
   - [ ] Không commit `.env`, không ghi đè `data/`.
5. Ghi `reports/milestones/Mx.md`:
   ```
   # Mx — <tên>
   Trạng thái: xong | kẹt
   Số vòng sửa: n
   File tạo/sửa: ...
   Lệnh kiểm chứng: ...
   Output (nguyên văn): ...
   Checklist audit: ...
   Còn tồn tại: ...
   ```
