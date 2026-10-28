# AGENTS.md — Web thư viện chuyển đổi số (đề tài cuối kì Trực quan hóa dữ liệu)

Mọi agent (Argon, Gemini 3.8 Flash subagent) đọc file này trước khi làm. Kế hoạch và các chặng nằm ở `prompts/`.

## 1. Mục tiêu bản demo
Dữ liệu tìm kiếm và mượn tư liệu giúp thủ thư quyết định số hóa tư liệu nào trước.
Vòng lặp: người dùng tìm → hệ thống ghi log → thủ thư xem dashboard → số hóa (tải bản mềm) → tư liệu có bản mềm sinh dữ liệu cho vòng sau.
Đây là bản demo, KHÔNG làm web thư viện hoàn chỉnh. Không thêm tính năng ngoài danh sách ở mục 4.

## 2. Công nghệ (đã chốt, không đổi)
- CSDL: PostgreSQL (đã cài trên máy). Extension: `unaccent`, `pg_trgm`.
- Backend: **Python 3 + Flask** + `psycopg2` (SQL thuần, không ORM) + session cookie ký của Flask + `bcrypt`. Chạy: `python server/app.py` (cổng 3000). (Đổi từ Node/Express ngày 2026-10-28 theo yêu cầu người dùng: toàn dự án dùng Python; API giữ nguyên.)
- Frontend: HTML/CSS/JS thuần, render phía trình duyệt bằng `fetch`. Tái dùng giao diện `D:\Courses\Web\tt_gk` (copy `css/style.css`, cấu trúc top-bar/header/nav/footer của `index.html`, `tra-cuu.html`, `quan-ly.html`).
- Biểu đồ: Chart.js, wordcloud2.js (nạp từ cdnjs, ghi rõ phiên bản).
- Script dữ liệu: Python 3 (`pandas`, `openpyxl`, `psycopg2-binary`, `Faker` locale `vi_VN`, `numpy`).
- Kiểm thử: `pytest` + Flask test client cho API; Playwright (Node, chỉ dùng cho kiểm thử giao diện và chụp màn hình).

## 3. Giao diện: đổi màu chủ đạo từ xanh navy sang ĐỎ
Trong `style.css` của tt_gk, thay toàn bộ (12 chỗ mã cứng + biến):
```
--color-primary:       #0b3c6d  →  #9b1c1c
--color-primary-dark:  #072648  →  #6b1010
--color-primary-light: #165b9f  →  #c53030
rgba(11, 60, 109, x)            →  rgba(155, 28, 28, x)
ui-avatars background=0b3c6d    →  background=9b1c1c
```
Giữ màu nhấn vàng kim `--color-accent: #d4af37`. Giữ màu trạng thái (`--status-*`), nhưng `--status-borrowed` đổi sang `#6366f1` để không lẫn với nền đỏ. Không còn mã màu navy nào: `grep -i "0b3c6d\|072648\|165b9f\|11, 60, 109"` phải ra rỗng.
Biểu đồ dùng bảng màu đỏ–vàng–xám đồng bộ: `#9b1c1c, #d4af37, #c53030, #64748b, #e57373`.

## 4. Phạm vi chức năng
Vai trò trong demo: `khach` (không đăng nhập), `nguoi_dung` (gộp sinh_vien + giang_vien, cột vai_tro vẫn lưu riêng), `thu_thu` (gộp admin).
1. Tìm kiếm tư liệu: gợi ý khi gõ (autocomplete), chấp nhận gõ không dấu và sai chính tả nhẹ (`unaccent` + `pg_trgm`), lọc theo loại hình và năm.
2. Danh sách kết quả: tiêu đề, tác giả, loại hình, năm, "còn x/y bản", nhãn "Có bản mềm".
3. Ghi log MỖI lần tìm (`log_tim_kiem`) và cập nhật `tai_lieu_chon_id` khi người dùng bấm vào kết quả.
4. Chi tiết tư liệu; nút "Đăng ký mượn" (chỉ nguoi_dung) → lượt mượn trạng thái `cho_duyet`.
5. Thủ thư: duyệt mượn (gán bản sao còn rảnh, hạn trả = +14 ngày), ghi nhận trả, tải bản mềm lên (PDF) + chọn mức truy cập (`cong_khai` / `noi_bo`).
6. Dashboard thủ thư (chỉ số liệu tổng hợp, KHÔNG hiện ai tìm gì):
   - Word cloud từ khóa (đếm theo cả cụm truy vấn đã chuẩn hóa, không tách từ).
   - Top 15 từ khóa (bar ngang, Chart.js).
   - Lượt tìm theo ngày (line chart) — bộ lọc 7/30/90 ngày.
   - Bảng từ khóa tìm nhiều nhưng 0 kết quả → gợi ý mua/bổ sung.
   - Bảng "nên số hóa": `diem = so_lan_chon + 2 * so_luot_muon`, chỉ tư liệu `co_ban_mem = false` và `khong_co_tl = false`, xếp giảm dần.
   - Thẻ KPI: tổng lượt tìm, % tìm không có kết quả, số lượt mượn đang mở, số tư liệu đã số hóa.
7. Banner cố định trên mọi trang: "Dữ liệu log, lượt mượn, người dùng là DỮ LIỆU MẪU phục vụ demo".

Ngoài phạm vi (KHÔNG làm): gợi ý tư liệu tương tự, embedding, OCR, QR/mã vạch, email, stream graph, đồ thị mượn chung.

## 5. Dữ liệu thật
File `data/[Bản chuẩn] DANH MỤC TƯ LIỆU KHOA.xlsx`, 8 sheet ≈ 3.470 dòng, header ở dòng 1, sheet LA và S-TV có thêm 1 dòng số thứ tự cột ở dòng 2 (bỏ đi):
| Sheet | loai_hinh | Cột chính |
|---|---|---|
| LA | luan_an | Ký hiệu mới, Thời gian, Vấn đề, Họ và tên đệm, Tên, Tên đề tài, Thời gian địa điểm khảo sát, GVHD, Hệ, Ghi chú |
| LV | luan_van | Ký hiệu, Thời gian, Vấn đề, Họ tên, Tên đề tài, Cơ quan đơn vị, GVHD, Hệ, Khoá, Ghi chú |
| KL | khoa_luan | như LV |
| KH | bao_cao_kh | như LV |
| KY | ky_yeu | Ký hiệu, Thời gian, Tên sách tư liệu, Nhà xuất bản, Tác giả, Ghi chú |
| S-TV | sach | Ký hiệu mới, Thời gian, Tên đề sách, NXB, Tác giả, Ghi chú |
| HN | sach_ha_noi | Ký hiệu, Thời gian, Tên đề sách, NXB, Tác giả, Loại hình, ĐC tài liệu, Ghi chú |
| PGS. Vương Đình Quyền | tu_sach_tang | Tên sách, Nhà xuất bản, Năm xuất bản, Tác giả (không có ký hiệu → sinh `VDQ.001`…) |

Làm sạch bắt buộc: ô chỉ có `.`, `#`, `nan` → NULL; trim khoảng trắng (`"LTH "` → `LTH`); năm không phải số (`"1985-2005"`) → lấy năm đầu, lưu chuỗi gốc ở `nam_goc`; ghép "Họ và tên đệm" + "Tên" thành `tac_gia`; Ghi chú chứa `Ko có TL` → `khong_co_tl = true`; dòng không có tiêu đề → bỏ, ghi vào `reports/etl/etl_bi_bo.csv`. Không sửa lỗi chính tả trong tiêu đề (giữ nguyên dữ liệu gốc).
Mã "Vấn đề" (QTVP, LTH, VB, LT, KS…) chưa có bảng giải nghĩa: lưu vào bảng `ma_van_de(ma, ten)` với `ten = NULL`, giao diện hiện mã.

## 6. Dữ liệu mô phỏng (cờ `du_lieu_mau = true`)
- Bản sao: mỗi tư liệu 1–3 bản (sách nhiều hơn luận văn), tư liệu `khong_co_tl` = 0 bản.
- Người dùng: 1 thủ thư `thuthu/thuthu123`, 1 sinh viên `sv01/sv123`, 1 giảng viên `gv01/gv123` + 60 người dùng Faker.
- Log tìm kiếm ~8.000 dòng trải 90 ngày, theo Zipf (s≈1.1) trên tập từ khóa lấy từ tiêu đề thật (cụm 1–3 từ) + 30 từ khóa không có tư liệu tương ứng (ví dụ "học máy", "python", "trí tuệ nhân tạo") + 15% biến thể không dấu + 5% lỗi gõ; nhiều lượt hơn vào ngày thường và trước kỳ thi; ~40% log có `tai_lieu_chon_id`.
- Lượt mượn ~400 dòng, ưu tiên tư liệu được chọn nhiều. Seed cố định `random.seed(42)` để demo lặp lại được.

## 7. Cấu trúc thư mục
```
CK/
  AGENTS.md  prompts/  .gitignore
  docs/      (erd.mmd, erd.png, Mô tả bài toán...)
  data/      (Excel gốc, chỉ đọc)
  db/        (schema.sql, views.sql)
  scripts/   (etl_import.py, seed_demo.py, requirements.txt)
  server/    (app.py, routes/*.py (Blueprint), auth.py, db.py)
  public/    (index.html, tra-cuu.html, chi-tiet.html, tai-khoan.html, quan-ly.html, dashboard.html,
              css/style.css, js/main.js, js/trang/*.js)
  tests/     (api/test_*.py, ui/*.spec.js)
  tools/     (demo_reset.py, screenshots.js, export_report.py, agy/ = prompt giao việc + logs/)
  reports/   (đầu ra phục vụ báo cáo: etl/, seed/, tai_lieu/, so_lieu/, bieu_do/, screenshots/, milestones/, TONG_KET.md)
  uploads/   (mau/ban_mem_mau.pdf, tệp số hóa tải lên)
  .env.example  package.json  playwright.config.js  pytest.ini  README.md
```

## 8. Quy ước
- Tên bảng/cột tiếng Việt không dấu, snake_case. Comment code tiếng Việt.
- Mọi truy vấn dùng tham số (`%s` của psycopg2), không nối chuỗi SQL.
- Mọi route kiểm tra vai trò bằng decorator `yeu_cau_vai_tro(...)`.
- Không commit `.env`. Chuỗi kết nối lấy từ `DATABASE_URL`.
- Một milestone chỉ được báo "xong" khi lệnh kiểm chứng trong prompt của milestone đó chạy pass; dán output vào `reports/milestones/Mx.md`.
