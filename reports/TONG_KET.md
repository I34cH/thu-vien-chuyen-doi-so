# BÁO CÁO TỔNG KẾT DỰ ÁN — WEB THƯ VIỆN CHUYỂN ĐỔI SỐ

> **Đề tài cuối kì môn Trực quan hóa dữ liệu**  
> **Mục tiêu:** Xây dựng hệ thống minh họa vòng lặp ra quyết định chuyển đổi số trong thư viện đại học: **Người dùng tìm kiếm & mượn tư liệu → Hệ thống ghi nhận log → Thủ thư phân tích Dashboard trực quan hóa → Ưu tiên số hóa tư liệu có nhu cầu cao nhất → Phục vụ bản mềm PDF trực tuyến.**

---

## 1. Bảng tổng hợp trạng thái các Milestone (M1 → M6)

| Milestone | Nội dung chính | Trạng thái | Số vòng sửa | Kết quả kiểm chứng | Báo cáo chi tiết |
|:---:|---|:---:|:---:|---|---|
| **M1** | CSDL PostgreSQL (`db/schema.sql`, `db/views.sql`) + ETL làm sạch 8 sheet Excel (`scripts/etl_import.py`) | **PASS** | 1 | Nạp `3.400` tư liệu, đủ 8 `loai_hinh`, `29` mã vấn đề, `110` tư liệu `khong_co_tl = true`; tìm không dấu `"luu tru"` trả về `973` tư liệu. | `reports/milestones/M1.md` |
| **M2** | Sinh dữ liệu mô phỏng với `seed = 42` (`scripts/seed_demo.py`), phân phối Zipf ($s \approx 1.1$) | **PASS** | 2 | Chạy 2 lần liên tiếp cho số dòng giống hệt nhau (`5.817` bản sao, `63` người dùng, `400` lượt mượn, `8.000` log tìm kiếm); tỉ lệ 0 kết quả `12.1%`, tỉ lệ chọn `41.3%`, độ dốc Zipf `-1.10`. | `reports/milestones/M2.md` |
| **M3** | Backend API ban đầu (Node/Express) | **PASS** | 1 | 25/25 ca kiểm thử API đạt 100%. | `reports/milestones/M3.md` |
| **M3b** | Chuyển toàn bộ Backend sang **Python 3 + Flask + `psycopg2`** (theo yêu cầu người dùng cập nhật ngày 2026-10-28, giữ nguyên hợp đồng API) | **PASS** | 1 | `python -m pytest tests/api -q`: **25/25 passed**; `npx playwright test`: **33/33 passed**; xóa sạch mã Node/Express trong `server/`. | `reports/milestones/M3b.md` |
| **M4** | Giao diện Frontend kế thừa từ `tt_gk`, chuyển toàn bộ sang tông màu **Đỏ chủ đạo** (`#9b1c1c`), kết nối API thật | **PASS** | 2 | Regex tìm mã màu navy cũ trong `public/` trả về rỗng; **27/27** ca kiểm thử UI (`tests/ui/ui.spec.js`) trên 3 vai trò đạt 100%, không có lỗi console. | `reports/milestones/M4.md` |
| **M5** | Dashboard trực quan hóa cho Thủ thư (`public/dashboard.html`): 4 thẻ KPI, Word Cloud, Top 15 Bar chart, Line chart 7/30/90 ngày, Bảng 0 kết quả, Bảng ưu tiên số hóa | **PASS** | 2 | **6/6** ca kiểm thử chuyên biệt M5 (`tests/ui/dashboard.spec.js`) và tổng **33/33** ca Playwright đạt 100%; tải bản mềm cho tư liệu đầu bảng làm tư liệu rời khỏi bảng ngay khi tải lại. | `reports/milestones/M5.md` |
| **M6** | Công cụ Demo & Xuất báo cáo (`tools/demo_reset.py`, `tools/screenshots.js`, `tools/export_report.py`, `README.md`), làm sạch cụm từ khóa Top 15 & đánh dấu ngày đang cập nhật trên Line Chart | **PASS** | 1 | Toàn bộ chuỗi lệnh kiểm chứng M6 chạy thành công không lỗi; xuất đủ 5 CSV, 5 ảnh Matplotlib, 66 ảnh chụp giao diện, `reports/tai_lieu/tu_dien_du_lieu.md`, `reports/tai_lieu/erd.png`, `reports/tai_lieu/api.md`. | `reports/milestones/M6.md` |
| **M7** | Dọn và tối ưu cấu trúc thư mục: tách JS nội tuyến sang `public/js/trang/`, gom kiểm thử về `tests/api` & `tests/ui`, phân nhóm `reports/`, tạo `.gitignore` | **PASS** | 1 | 6 file HTML không còn JS nội tuyến; 25 test API (`tests/api/test_api.py`) và 33 test UI (`tests/ui/*.spec.js`) đạt 100%; dọn sạch 24 ảnh trùng lặp trong `reports/screenshots/`; cập nhật toàn bộ đường dẫn tài liệu. | `reports/milestones/M7.md` |

---

## 2. Các điểm điều chỉnh / làm rõ so với đặc tả ban đầu và lý do

1. **Chuyển Backend từ Node/Express sang Python Flask (Chặng M3b):**
   - **Lý do:** Ngày 2026-10-28, người dùng yêu cầu thống nhất toàn bộ dự án viết bằng Python (đã cập nhật chính thức vào `AGENTS.md` mục 2). Node.js chỉ còn giữ lại `@playwright/test` để chạy kiểm thử giao diện trình duyệt và chụp màn hình tự động (`tools/screenshots.js`).
   - **Tác động:** Giữ nguyên 100% đường dẫn, phương thức HTTP và cấu trúc JSON của 21 endpoint API; thay `tools/demo-reset.js` bằng `tools/demo_reset.py`.
2. **Loại bỏ từ đơn và mảnh cắt lệch âm tiết trong `scripts/seed_demo.py` (Chặng M6):**
   - **Lý do:** Trong `AGENTS.md` mục 6 ghi trích "cụm 1–3 từ" từ tiêu đề thật. Tuy nhiên, tiếng Việt có nhiều từ ghép 2 âm tiết (`lưu trữ`, `tài liệu`, `công tác`, `việt nam`, `quản lý`), nên nếu lấy từ đơn 1 âm tiết hoặc cắt cửa sổ trượt lệch ranh giới âm tiết sẽ sinh ra các từ khóa vô nghĩa (`công`, `liệu`, `việt`, `quản`) trên Top 15 và Word Cloud.
   - **Giải pháp:** Chỉ giữ các cụm 2–3 âm tiết có nghĩa độc lập trong `trich_cum_tu`, giúp biểu đồ Word Cloud và Top 15 từ khóa phản ánh đúng các chủ đề chuyên môn (`lưu trữ`, `tài liệu`, `công tác`, `việt nam`, `tổ chức`, `văn phòng`, `quản lý`…), đồng thời vẫn giữ nguyên các chỉ số mục tiêu (`seed = 42`, `8.000` dòng log, tỉ lệ 0 kết quả `12.1%`, tỉ lệ chọn `41.3%`, độ dốc Zipf `-1.10`).
3. **Đánh dấu ngày hôm nay là `"Đang cập nhật"` trên biểu đồ xu hướng theo ngày (Chặng M6):**
   - **Lý do:** Ngày hiện tại chưa kết thúc 24 giờ nên số lượt tìm kiếm của điểm cuối cùng trên Line Chart thấp hơn các ngày trọn vẹn trước đó.
   - **Giải pháp:** Đánh dấu rõ nhãn ngày cuối là `(đang cập nhật)`, vẽ đoạn nối cuối bằng nét đứt kèm điểm tròn rỗng và nhãn `Đang cập nhật` trực tiếp trên cả biểu đồ `Chart.js` (`public/dashboard.html`) lẫn biểu đồ `Matplotlib` (`reports/bieu_do/theo_ngay.png`).
4. **Mở rộng nhận diện ghi chú không có tài liệu và năm định dạng ngày Excel trong ETL (Chặng M1):**
   - **Lý do:** Trong dữ liệu gốc Excel, ngoài chuỗi `"Ko có TL"`, còn có các ô ghi `"ko có"` hoặc `"chưa có tài liệu"` (tổng cộng 110 tư liệu), và một số ô năm bị Excel tự động đổi thành số seri ngày (`1905-06-24` tương ứng năm `2003`).
   - **Giải pháp:** Quy đổi chính xác về năm số nguyên ở cột `nam` và bảo toàn chuỗi gốc ở cột `nam_goc`.
5. **Xuất sơ đồ `reports/tai_lieu/erd.png` theo cơ chế dự phòng (Chặng M6):**
   - **Lý do:** Môi trường máy cục bộ không cài sẵn gói `@mermaid-js/mermaid-cli` (`mmdc`).
   - **Giải pháp:** Thực hiện đúng mục 10 của `prompts/05-giao-viec-agy.md`: `tools/export_report.py` tự động kiểm tra `mmdc` và sao chép `docs/erd.png` sang `reports/tai_lieu/erd.png`.

---

## 3. Kiểm tra tuân thủ quy ước an toàn & bảo mật (`AGENTS.md` mục 3, 4, 8)

- **Phạm vi chức năng:** Tuân thủ nghiêm ngặt mục 4 của `AGENTS.md`, không thêm bất kỳ tính năng ngoài phạm vi nào (không OCR, không QR/mã vạch, không gửi email, không embedding).
- **Truy vấn SQL an toàn:** 100% truy vấn trong `server/`, `scripts/`, `tools/` dùng tham số hóa `%s` của `psycopg2`, không nối chuỗi SQL.
- **Kiểm soát phân quyền:** 100% route trong `server/routes/*.py` gắn decorator `@yeu_cau_vai_tro('*' | 'nguoi_dung' | 'thu_thu')`.
- **Bảo vệ quyền riêng tư trên Dashboard:** Các API `/api/thong-ke/*` và các view `v_*` chỉ trả về số liệu tổng hợp, không lộ `nguoi_dung_id` hay `ma_phien`.
- **Cờ `du_lieu_mau`:** Toàn bộ dữ liệu mô phỏng có `du_lieu_mau = true`; mọi dữ liệu phát sinh khi chạy kiểm thử đều được tự động dọn sạch trong `teardown` / `afterAll` (số bản ghi `du_lieu_mau = false` sau khi chạy toàn bộ test bằng `0`).
- **Hệ màu chủ đạo:** Toàn bộ giao diện `public/` và biểu đồ báo cáo sử dụng bảng màu Đỏ – Vàng kim – Xám (`#9b1c1c`, `#6b1010`, `#c53030`, `#d4af37`, `#64748b`, `#e57373`), không còn mã màu xanh navy cũ.

---

## 4. Lỗi / Giới hạn còn tồn tại

- **Không có lỗi chức năng hay lỗi kiểm thử tồn đọng:** Toàn bộ lệnh kiểm chứng từ M1 đến M6 (`demo_reset.py`, `25` bài test `pytest`, `33` bài test `Playwright`, `screenshots.js`, `export_report.py`) đều chạy PASS 100%.
- **Giới hạn có chủ đích của bản Demo:**
  - Một số mã vấn đề (`QTVP`, `LTH`, `VB`, `LT`, `KS`…) trong tệp Excel gốc của Khoa chưa có bảng giải nghĩa tên đầy đủ nên cột `ma_van_de.ten` để `NULL` và giao diện hiển thị trực tiếp mã theo đúng quy định tại mục 5 của `AGENTS.md`.
  - Máy chủ chạy trực tiếp bằng WSGI tích hợp của Flask (`python server/app.py` ở cổng `3000`) phục vụ trình diễn cục bộ; nếu triển khai thực tế trong môi trường sản xuất cần đặt sau WSGI server chuyên dụng (như Gunicorn/Waitress) và cấu hình `SESSION_SECRET` riêng trong `.env`.

---

## Opus final audit (2026-10-28) — CHẤP NHẬN

Chạy lại độc lập toàn bộ chuỗi từ đầu trên máy:

| Lệnh | Kết quả |
|---|---|
| `python tools/demo_reset.py` | OK, 43 giây: 3.400 tư liệu, 5.817 bản sao, 63 người dùng, 400 lượt mượn, 8.000 log; 0 kết quả 12,1%; Zipf -1,10 |
| `python -m pytest tests/api -q` | 25 passed |
| `npx playwright test` | 33 passed (3 vai trò, dashboard, luồng số hóa → tư liệu rời bảng) |
| `npm run screenshots` | 42 ảnh (1440px + 390px + 6 ảnh thành phần dashboard) |
| `python tools/export_report.py` | đủ `so_lieu/*.csv`, `bieu_do/*.png`, `reports/tai_lieu/tu_dien_du_lieu.md`, `reports/tai_lieu/erd.png`, `reports/tai_lieu/api.md` |

Đã kiểm tra thêm: không SQL nối chuỗi; mọi route có `yeu_cau_vai_tro`; không còn mã màu navy; banner DỮ LIỆU MẪU ở mọi trang; top 15 từ khóa không còn từ đơn vô nghĩa; giao diện 390px không tràn ngang.

Tồn tại nhỏ (không chặn):
- Đã khắc phục ở M7: dọn dẹp các ảnh trùng `x.png` không hậu tố trong `reports/screenshots/<vai_tro>/`.
- Chạy test Playwright ghi thêm vài log tìm kiếm thật; chạy `python tools/demo_reset.py` trước buổi demo.
- `reports/tai_lieu/erd.png` là bản sao `docs/erd.png` (máy không có mermaid-cli).
- `SECRET_KEY` có giá trị dự phòng cứng khi thiếu `.env` (chấp nhận cho demo).
