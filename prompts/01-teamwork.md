Bạn là Argon, điều phối viên của đội. Đọc kỹ `AGENTS.md` và `docs/erd.mmd` trong thư mục hiện tại trước khi chia việc. Đó là đặc tả đã được chốt; không đổi công nghệ, không thêm tính năng ngoài phạm vi.

THÀNH PHẦN ĐỘI
- Bạn (Argon, effort medium): chia milestone, giao việc, tích hợp, quyết định khi có xung đột.
- Subagent dùng Gemini 3.8 Flash, effort HIGH, ba vai:
  - implement: viết code theo milestone.
  - test: viết và chạy kiểm thử, chỉ báo pass khi lệnh kiểm chứng thực sự pass.
  - audit: đọc lại code đã xong, đối chiếu AGENTS.md (phân quyền, SQL tham số, cờ du_lieu_mau, màu đỏ, phạm vi), liệt kê lỗi cho implement sửa.
- Không để một subagent vừa implement vừa tự audit chính phần của nó.

QUY TẮC VÒNG KIỂM CHỨNG (mỗi milestone)
implement → test chạy LỆNH KIỂM CHỨNG → lỗi thì trả implement sửa → chạy lại → audit → ghi `reports/milestones/Mx.md` gồm: file đã tạo, output lệnh kiểm chứng (dán nguyên văn), vấn đề còn lại. Quá 3 vòng chưa pass: dừng milestone đó, ghi rõ lỗi, chuyển sang /boost.

MÔI TRƯỜNG: Windows + PowerShell. Lệnh kiểm chứng viết kiểu POSIX cho dễ đọc; khi chạy hãy chuyển sang PowerShell: `$env:DATABASE_URL` thay cho `%DATABASE_URL%`, `Select-String -Pattern ... -Path public\* -Recurse` (hoặc `rg`) thay cho `grep`, nối lệnh bằng `;` và kiểm tra `$LASTEXITCODE`. Đọc `.env` bằng `dotenv` trong Node và `python-dotenv` trong Python.

MILESTONE (tuần tự, M3 và M4 có thể song song sau khi M2 xong)

M1 — CSDL + nạp dữ liệu thật
- `db/schema.sql`: bảng theo ERD, `CREATE EXTENSION IF NOT EXISTS unaccent, pg_trgm`, hàm `f_unaccent` IMMUTABLE, index GIN trên `tsv` và trigram trên `f_unaccent(lower(tieu_de))`, index `log_tim_kiem(tu_khoa_chuan)`, `log_tim_kiem(thoi_diem)`.
- `db/views.sql`: view `v_tu_khoa_top`, `v_tim_theo_ngay`, `v_khong_ket_qua`, `v_nen_so_hoa` (công thức ở AGENTS.md mục 4.6), `v_tinh_trang_tai_lieu` (so_ban, so_ban_con).
- `scripts/etl_import.py` + `scripts/requirements.txt`: đọc 8 sheet, làm sạch theo AGENTS.md mục 5, ghi `reports/etl/etl_tom_tat.csv` (sheet, số dòng gốc, số dòng nạp, số dòng bỏ, số ô đã làm sạch) và `reports/etl/etl_bi_bo.csv`.
- LỆNH KIỂM CHỨNG:
  `psql "%DATABASE_URL%" -f db/schema.sql && python scripts/etl_import.py && psql "%DATABASE_URL%" -c "SELECT loai_hinh, count(*) FROM tai_lieu GROUP BY 1 ORDER BY 1;" -c "SELECT count(*) FROM tai_lieu WHERE tsv @@ plainto_tsquery('simple', f_unaccent('luu tru'));"`
  Đạt khi: tổng ≈ 3.400–3.470, có đủ 8 loai_hinh, truy vấn "luu tru" (không dấu) > 0.

M2 — Dữ liệu mô phỏng
- `scripts/seed_demo.py` theo AGENTS.md mục 6 (seed 42, cờ du_lieu_mau = true, mật khẩu bcrypt).
- Ghi `reports/seed/seed_tom_tat.md`: số dòng mỗi bảng, top 10 từ khóa, tỉ lệ 0 kết quả, biểu đồ rank–tần suất log-log (`reports/seed/zipf.png`) chứng minh phân phối Zipf.
- LỆNH KIỂM CHỨNG: chạy seed 2 lần liên tiếp sau `db/schema.sql` + ETL, số dòng các bảng giống hệt nhau; `SELECT count(*) FROM log_tim_kiem WHERE so_ket_qua = 0` > 0.

M3 — Backend API (`server/`)
Route (JSON, tiền tố /api):
- Công khai: `GET /goi-y?q=` (≤8 gợi ý, trigram + unaccent), `GET /tim-kiem?q=&loai=&tu_nam=&den_nam=&trang=` (ghi log, trả `log_id`), `POST /tim-kiem/:logId/chon` {tai_lieu_id}, `GET /tai-lieu/:id`, `GET /ban-mem/:id` (cong_khai ai cũng xem; noi_bo phải đăng nhập).
- Tài khoản: `POST /dang-nhap`, `POST /dang-xuat`, `GET /toi`.
- nguoi_dung: `POST /muon` {tai_lieu_id} → cho_duyet; `GET /muon/cua-toi`.
- thu_thu: `GET /quan-ly/muon?trang_thai=`, `POST /quan-ly/muon/:id/duyet|tu-choi|tra`, `POST /quan-ly/tai-lieu/:id/ban-mem` (multer, chỉ PDF ≤ 20MB, lưu `uploads/`, set co_ban_mem, muc_truy_cap), `GET /thong-ke/tong-quan|tu-khoa|theo-ngay?so_ngay=|khong-ket-qua|nen-so-hoa`.
- Thống kê chỉ trả số tổng hợp, không trả nguoi_dung_id hay ma_phien.
- LỆNH KIỂM CHỨNG: `npm test` pass, gồm tối thiểu: tìm "luu tru" có kết quả và tạo 1 dòng log; khách gọi POST /muon → 401; nguoi_dung gọi /thong-ke → 403; duyệt mượn khi hết bản sao → 409; luồng đăng ký → duyệt → trả cập nhật đúng trạng thái bản sao.

M4 — Frontend từ tt_gk, màu đỏ (`public/`)
- Copy `D:\Courses\Web\tt_gk\css\style.css` và khung trang, đổi màu theo AGENTS.md mục 3. Thay số liệu giả trên trang chủ bằng số thật từ `/api/thong-ke/tong-quan` (hoặc ẩn đi).
- Trang: `index.html` (ô tìm + autocomplete), `tra-cuu.html` (kết quả, bộ lọc, phân trang, tình trạng "còn x/y", nhãn bản mềm), `chi-tiet.html`, `tai-khoan.html` (đăng nhập, lượt mượn của tôi), `quan-ly.html` (thủ thư: duyệt/trả, tải bản mềm), `dashboard.html`.
- Banner "DỮ LIỆU MẪU" trên mọi trang. Menu ẩn/hiện theo vai trò từ `/api/toi`.
- LỆNH KIỂM CHỨNG: `grep -rniE "0b3c6d|072648|165b9f|11, ?60, ?109" public` rỗng; test Playwright `tests/ui.spec.js` mở từng trang với 3 vai trò, không có lỗi console, gõ "luu tru" thấy gợi ý.

M5 — Dashboard trực quan hóa (`public/dashboard.html`)
- KPI 4 thẻ; word cloud (wordcloud2.js, kích thước theo căn bậc hai tần suất, màu bảng đỏ–vàng); bar ngang top 15; line lượt tìm theo ngày với nút 7/30/90; bảng 0 kết quả; bảng nên số hóa có nút "Số hóa" dẫn tới form tải bản mềm.
- Mỗi biểu đồ có tiêu đề dạng câu hỏi (ví dụ "Người dùng đang tìm gì nhiều nhất?") và một dòng ghi chú cách đọc.
- LỆNH KIỂM CHỨNG: sau khi thủ thư tải bản mềm cho tư liệu đứng đầu bảng "nên số hóa", tải lại dashboard thì tư liệu đó biến mất khỏi bảng (test Playwright); số liệu KPI khớp truy vấn SQL trực tiếp.

M6 — Công cụ demo và báo cáo (`tools/`, `package.json`)
- `npm run demo:reset`: drop + schema + views + ETL + seed, in tóm tắt.
- `npm run screenshots` (`tools/screenshots.js`, Playwright): đăng nhập từng vai trò, chụp mọi trang ở 1440px và 390px vào `reports/screenshots/<vai_tro>/<trang>.png`, kèm ảnh từng biểu đồ dashboard riêng.
- `npm run report` (`tools/export_report.py`): xuất `reports/so_lieu/*.csv` (top từ khóa, 0 kết quả, nên số hóa, theo ngày, theo loại hình), ảnh biểu đồ matplotlib tương ứng `reports/bieu_do/*.png`, `reports/tai_lieu/tu_dien_du_lieu.md` (đọc information_schema: bảng, cột, kiểu, ý nghĩa), `reports/tai_lieu/erd.png` (render `docs/erd.mmd` bằng `npx @mermaid-js/mermaid-cli`), `reports/tai_lieu/api.md` (danh sách route + vai trò được phép).
- `README.md`: cài đặt, chạy, tài khoản demo, KỊCH BẢN DEMO 5 phút (khách tìm "luu tru" không dấu → sv01 đăng ký mượn → thuthu duyệt → dashboard: word cloud, 0 kết quả, nên số hóa → tải bản mềm → tư liệu rời bảng, sv01 thấy nút Đọc).
- LỆNH KIỂM CHỨNG: `npm run demo:reset && npm test && npm run screenshots && npm run report` chạy hết không lỗi; `reports/` có đủ các file trên.

KẾT THÚC
Khi M1–M6 xong, tạo `reports/TONG_KET.md`: bảng milestone (trạng thái, số vòng sửa), danh sách lệch so với AGENTS.md (nếu có) và lý do, lỗi/giới hạn còn tồn tại. Không tự tuyên bố hoàn thành nếu bất kỳ lệnh kiểm chứng nào chưa pass.
