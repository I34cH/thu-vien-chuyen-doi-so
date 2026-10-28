# Hướng dẫn chạy luồng agent (Antigravity CLI `agy`)

```
Claude Opus (tổng chỉ huy)   → đã chốt AGENTS.md, ERD, prompt từng chặng
        ↓
agy /teamwork  (Argon, effort MEDIUM)  → chia milestone M1–M6, điều phối, tích hợp
        ↓
Subagent Gemini 3.8 Flash (effort HIGH) → Implement · Test · Audit
        ↕
/goal  (vòng kiểm chứng: chạy lệnh kiểm chứng → sửa → chạy lại → báo cáo)
/boost (chỉ khi kẹt lỗi khó, Argon MEDIUM)
        ↓
Claude Opus final audit  → chấp nhận / yêu cầu sửa / quay lại lập kế hoạch
```

## 0. Chuẩn bị (1 lần)
1. Mở PowerShell tại `D:\Courses\datavisualize\btth\CK`.
2. Tạo database: `psql -U postgres -c "CREATE DATABASE thu_vien_ck;"`
3. Copy `.env.example` → `.env` (agent sẽ tạo `.env.example`), điền `DATABASE_URL=postgres://postgres:<mật_khẩu>@localhost:5432/thu_vien_ck`.
4. Kiểm tra tên model chính xác: chạy `agy`, gõ `/model`, ghi lại slug của **Argon** và **Gemini 3.8 Flash**. Các lệnh dưới dùng `<ARGON>` và `<FLASH>` làm chỗ thay.
5. (Tuỳ chọn) đổi `.agents/mcp_config.example.json` → `.agents/mcp_config.json` để agent đọc trực tiếp PostgreSQL và điều khiển trình duyệt.

## 1. Chạy teamwork (cách chính)
```powershell
agy --model <ARGON> --effort medium
```
Trong phiên: gõ `/teamwork` rồi dán toàn bộ nội dung `01-teamwork.md`.
Khi agent hỏi cấp quyền ghi file/chạy lệnh: chỉ duyệt trong thư mục CK.

## 2. Nếu tài khoản không có /teamwork (gói trả phí) hoặc một milestone chưa xong
Chạy từng milestone bằng Flash + /goal:
```powershell
agy --model <FLASH> --effort high
```
Gõ `/goal` rồi dán khối của milestone tương ứng trong `02-goal-tung-chang.md`.
Làm tuần tự M1 → M6; mỗi chặng xong mới sang chặng sau.

## 3. Khi kẹt
Lỗi lặp lại ≥ 2 vòng /goal mà chưa pass → mở `03-boost.md`, chạy `/boost` với khung tương ứng (Argon, medium).

## 4. Gửi về Claude Opus để audit
Sau M6, làm theo `04-opus-audit.md`: gửi thư mục `reports/` + `git diff --stat` cho Claude trong cuộc trò chuyện này.

## Lệnh hằng ngày sau khi xong
| Lệnh | Việc |
|---|---|
| `npm run demo:reset` | Xoá DB, tạo lại schema, nạp Excel, sinh dữ liệu mẫu (seed 42) |
| `npm run dev` | Chạy web ở http://localhost:3000 |
| `npm test` | Kiểm thử API |
| `npm run screenshots` | Chụp toàn bộ màn hình theo từng vai trò vào `reports/screenshots/` |
| `npm run report` | Xuất số liệu, biểu đồ, ERD, từ điển dữ liệu cho báo cáo vào `reports/` |
