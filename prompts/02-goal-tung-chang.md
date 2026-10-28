# /goal từng chặng (dùng khi không có /teamwork, hoặc làm lại 1 milestone)

Phiên: `agy --model <FLASH> --effort high`. Gõ `/goal` rồi dán MỘT khối. Xong khối này mới sang khối sau.
Mỗi khối đều ngầm hiểu: "Đọc AGENTS.md và prompts/01-teamwork.md mục Mx trước. Chạy lệnh kiểm chứng, sửa tới khi pass, ghi reports/milestones/Mx.md với output nguyên văn. Không làm gì ngoài Mx."

---
**M1** — Đọc AGENTS.md và mục M1 trong prompts/01-teamwork.md. Tạo db/schema.sql, db/views.sql, scripts/etl_import.py, scripts/requirements.txt để nạp 8 sheet của data/[Bản chuẩn] DANH MỤC TƯ LIỆU KHOA.xlsx vào PostgreSQL (DATABASE_URL trong .env) với đúng quy tắc làm sạch. Mục tiêu đạt khi lệnh kiểm chứng M1 pass: đủ 8 loai_hinh, tổng ≈ 3.400–3.470 dòng, tìm "luu tru" không dấu ra kết quả. Ghi reports/milestones/M1.md.

---
**M2** — Đọc AGENTS.md mục 6 và mục M2. Tạo scripts/seed_demo.py sinh người dùng, bản sao, log tìm kiếm Zipf, lượt mượn (seed 42, du_lieu_mau = true). Đạt khi chạy lại 2 lần cho số dòng giống hệt, có log 0 kết quả, có reports/seed/seed_tom_tat.md và reports/seed/zipf.png. Ghi reports/milestones/M2.md.

---
**M3** — Đọc mục M3. Dựng server/ bằng Express + pg với đúng danh sách route và phân quyền. Viết test node --test + supertest cho 5 tình huống bắt buộc. Đạt khi `npm test` pass toàn bộ. Ghi reports/milestones/M3.md.

---
**M4** — Đọc AGENTS.md mục 3 và mục M4. Dựng public/ từ giao diện D:\Courses\Web\tt_gk, đổi toàn bộ màu navy sang đỏ, nối với API. Đạt khi không còn mã màu navy và test Playwright tests/ui/ui.spec.js pass cho 3 vai trò. Ghi reports/milestones/M4.md.

---
**M5** — Đọc mục M5. Hoàn thiện dashboard.html (KPI, word cloud, bar top 15, line theo ngày, bảng 0 kết quả, bảng nên số hóa). Đạt khi test Playwright "số hóa xong thì rời bảng" pass và KPI khớp SQL. Ghi reports/milestones/M5.md.

---
**M6** — Đọc mục M6. Tạo npm scripts demo:reset, screenshots, report và README.md có kịch bản demo 5 phút. Đạt khi chuỗi `npm run demo:reset; npm test; npm run screenshots; npm run report` chạy hết không lỗi và reports/ có đủ file. Ghi reports/milestones/M6.md và reports/TONG_KET.md.
