# M3b — Chuyển Backend từ Node/Express sang Python Flask (Giữ nguyên API)

- **Trạng thái:** xong (PASS)
- **Số vòng sửa:** 1 (Vòng 1 đạt 100% toàn bộ 25/25 ca kiểm thử `pytest` và 33/33 ca kiểm thử giao diện `Playwright`, dọn sạch mã Node/Express trong `server/`)
- **File tạo mới:**
  - `server/__init__.py`: đánh dấu gói Python `server`.
  - `server/app.py`: khởi tạo ứng dụng Flask, cấu hình `SECRET_KEY` từ `SESSION_SECRET` trong `.env`, `MAX_CONTENT_LENGTH = 20MB` (bắt lỗi 413 trả 400 JSON), `CustomJSONProvider` chuẩn hóa `date`/`datetime` sang ISO 8601 và `Decimal` sang `float`, đăng ký các Blueprint `/api`, `/api/muon`, `/api/quan-ly`, `/api/thong-ke`, xử lý lỗi 404/500 cho `/api` trả về JSON, phục vụ tĩnh thư mục `public/` ở `"/"`, chạy cổng `PORT` (mặc định 3000) khi gọi `python server/app.py`.
  - `server/db.py`: kết nối PostgreSQL qua `psycopg2.pool.ThreadedConnectionPool` và `RealDictCursor`, đọc `DATABASE_URL` từ `.env` qua `python-dotenv`, đặt `client_encoding='UTF8'`, cung cấp `query(sql, params)` và context manager `transaction()`.
  - `server/auth.py`: decorator `yeu_cau_vai_tro(*vai_tros_cho_phep)` hỗ trợ `'*'`, `'nguoi_dung'`, `'thu_thu'`, tự động cấp `session['ma_phien']` (UUID) và `session.modified = True` để phát cookie phiên cả cho khách vãng lai; trả `401` khi chưa đăng nhập, `403` khi sai vai trò.
  - `server/routes/__init__.py`: đánh dấu gói `server.routes`.
  - `server/routes/auth.py`: Blueprint xác thực (`POST /api/dang-nhap`, `POST /api/dang-xuat`, `GET /api/toi`) sử dụng `bcrypt.checkpw`.
  - `server/routes/tai_lieu.py`: Blueprint tra cứu công khai (`GET /api/gioi-thieu`, `GET /api/goi-y`, `GET /api/tim-kiem`, `POST /api/tim-kiem/<log_id>/chon`, `GET /api/tai-lieu/<id>`, `GET /api/ban-mem/<id>`).
  - `server/routes/muon.py`: Blueprint đăng ký mượn và xem lượt mượn cá nhân (`POST /api/muon`, `GET /api/muon/cua-toi`).
  - `server/routes/quan_ly.py`: Blueprint quản lý mượn trả trong transaction `SELECT ... FOR UPDATE` (`GET /api/quan-ly/muon`, `POST /api/quan-ly/muon/<id>/duyet`, `POST /api/quan-ly/muon/<id>/tu-choi`, `POST /api/quan-ly/muon/<id>/tra`) và tải bản mềm PDF (`POST /api/quan-ly/tai-lieu/<id>/ban-mem`).
  - `server/routes/thong_ke.py`: Blueprint thống kê tổng hợp cho Dashboard thủ thư (`GET /api/thong-ke/tong-quan`, `/tu-khoa`, `/theo-ngay`, `/khong-ket-qua`, `/nen-so-hoa`).
  - `server/tests/test_api.py`: bộ kiểm thử tự động 25 ca bằng `pytest` + Flask `test_client()`, tự động dọn sạch dữ liệu kiểm thử trong fixture teardown.
  - `reports/milestones/M3b.md`: báo cáo kiểm chứng milestone M3b.
- **File chỉnh sửa:**
  - `scripts/requirements.txt`: bổ sung `Flask>=3.0` và `pytest>=8.0`.
  - `playwright.config.js`: đổi `webServer.command` sang `'python server/app.py'` (cổng 3000).
  - `package.json` & `package-lock.json`: đổi `"main": "server/app.py"`, `"start": "python server/app.py"`, `"test": "python -m pytest server/tests -q"`, gỡ bỏ các dependency Node của backend cũ (`express`, `express-session`, `pg`, `bcrypt`, `multer`, `dotenv`, `supertest`), chỉ giữ `@playwright/test`.
  - `tests/dashboard.spec.js`: thay kết nối `server/db.js` (Node `pg`) bằng hàm tiện ích gọi Python (`psycopg2` + `dotenv`) để đối chiếu KPI trực tiếp với CSDL.
  - `reports/milestones/M3.md`: thêm dòng ghi chú chuyển sang backend Flask ở cuối file.
- **File đã xóa:**
  - `server/app.js`
  - `server/db.js`
  - `server/middleware/auth.js` (và thư mục `server/middleware/`)
  - `server/routes/auth.js`
  - `server/routes/taiLieu.js`
  - `server/routes/muon.js`
  - `server/routes/quanLy.js`
  - `server/routes/thongKe.js`
  - `server/tests/api.test.js`

---

## Lệnh kiểm chứng
```powershell
python -m pytest server/tests -q
npx playwright test
rg -n "require\(|express" server
```

## Output lệnh kiểm chứng (nguyên văn)

### 1. `python -m pytest server/tests -q` (kèm `-v` chi tiết)
```text
.........................                                                [100%]
25 passed in 1.24s
```

```text
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.0.3, pluggy-1.6.0 -- C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe
cachedir: .pytest_cache
rootdir: D:\Courses\datavisualize\btth\CK
plugins: anyio-4.12.0, Faker-40.43.0
collecting ... collected 25 items

server/tests/test_api.py::test_0_gioi_thieu PASSED                       [  4%]
server/tests/test_api.py::test_1_tim_kiem_log PASSED                     [  8%]
server/tests/test_api.py::test_2_khach_muon_401 PASSED                   [ 12%]
server/tests/test_api.py::test_3_nguoi_dung_thong_ke_403 PASSED          [ 16%]
server/tests/test_api.py::test_4_duyet_het_ban_sao_409 PASSED            [ 20%]
server/tests/test_api.py::test_5_luong_muon_hoan_chinh PASSED            [ 24%]
server/tests/test_api.py::test_7_autocomplete PASSED                     [ 28%]
server/tests/test_api.py::test_8_phan_trang_khong_sinh_log PASSED        [ 32%]
server/tests/test_api.py::test_9_dang_nhap_sai PASSED                    [ 36%]
server/tests/test_api.py::test_10_chi_tiet_tai_lieu PASSED               [ 40%]
server/tests/test_api.py::test_11_thong_ke_dashboard PASSED              [ 44%]
server/tests/test_api.py::test_12_upload_va_doc_ban_mem PASSED           [ 48%]
server/tests/test_api.py::test_13_chon_tai_lieu_validation PASSED        [ 52%]
server/tests/test_api.py::test_14_dang_nhap_kieu_sai PASSED              [ 56%]
server/tests/test_api.py::test_15_chong_path_traversal PASSED            [ 60%]
server/tests/test_api.py::test_16_upload_chan_duoi_khong_phai_pdf PASSED [ 64%]
server/tests/test_api.py::test_17_upload_don_tep_cu PASSED               [ 68%]
server/tests/test_api.py::test_18_chan_dang_ky_muon_trung PASSED         [ 72%]
server/tests/test_api.py::test_19_phan_trang_vuot_nguong PASSED          [ 76%]
server/tests/test_api.py::test_20_tim_kiem_ky_tu_dac_biet PASSED         [ 80%]
server/tests/test_api.py::test_21_endpoint_khong_ton_tai PASSED          [ 84%]
server/tests/test_api.py::test_22_dang_xuat PASSED                       [ 88%]
server/tests/test_api.py::test_23_muon_cua_toi PASSED                    [ 92%]
server/tests/test_api.py::test_24_quan_ly_muon_danh_sach PASSED          [ 96%]
server/tests/test_api.py::test_25_tu_choi_muon PASSED                    [100%]

============================= 25 passed in 1.23s ==============================
```

### 2. `npx playwright test`
```text
Running 33 tests using 1 worker

  ok  1 [chromium] › tests\dashboard.spec.js:75:3 › 1. Hiển thị đầy đủ các thành phần trực quan hóa M5: 4 KPI, 3 biểu đồ, 2 bảng phân tích; có tiêu đề câu hỏi & hướng dẫn cách đọc (1.8s)
  ok  2 [chromium] › tests\dashboard.spec.js:150:3 › 2. Số liệu 4 thẻ KPI trên trang khớp 100% với truy vấn SQL trực tiếp (2.4s)
  ok  3 [chromium] › tests\dashboard.spec.js:213:3 › 3. Chuyển đổi bộ lọc thời gian 7/30/90 ngày trên biểu đồ xu hướng (2.7s)
  ok  4 [chromium] › tests\dashboard.spec.js:243:3 › 4. LỆNH KIỂM CHỨNG M5: Thủ thư tải bản mềm (PDF mẫu) cho tư liệu đứng đầu bảng nên số hóa, tải lại dashboard thì tư liệu đó biến mất khỏi bảng; KPI trên trang khớp SQL trực tiếp; sau test hoàn trả trạng thái (5.1s)
  ok  5 [chromium] › tests\dashboard.spec.js:364:3 › 5. Kiểm thử bố cục Dashboard thích ứng trên màn hình di động (390px): không tràn viền ngang và xếp chồng 1 cột mượt mà (1.7s)
  ok  6 [chromium] › tests\dashboard.spec.js:392:3 › 6. Kiểm thử tương tác Word Cloud: canvas đã vẽ các từ khóa và gắn tooltip khi di chuột (2.7s)
  ok  7 [chromium] › tests\ui.spec.js:50:7 › 1. Vai trò Khách vãng lai (khach) › Mở trang Trang chủ (/index.html) không có lỗi console & có banner DỮ LIỆU MẪU (982ms)
  ok  8 [chromium] › tests\ui.spec.js:50:7 › 1. Vai trò Khách vãng lai (khach) › Mở trang Tra cứu OPAC (/tra-cuu.html) không có lỗi console & có banner DỮ LIỆU MẪU (936ms)
  ok  9 [chromium] › tests\ui.spec.js:50:7 › 1. Vai trò Khách vãng lai (khach) › Mở trang Chi tiết tư liệu (/chi-tiet.html?id=8) không có lỗi console & có banner DỮ LIỆU MẪU (952ms)
  ok 10 [chromium] › tests\ui.spec.js:50:7 › 1. Vai trò Khách vãng lai (khach) › Mở trang Tài khoản & Đăng nhập (/tai-khoan.html) không có lỗi console & có banner DỮ LIỆU MẪU (921ms)
  ok 11 [chromium] › tests\ui.spec.js:50:7 › 1. Vai trò Khách vãng lai (khach) › Mở trang Quản lý mượn trả (/quan-ly.html) không có lỗi console & có banner DỮ LIỆU MẪU (918ms)
  ok 12 [chromium] › tests\ui.spec.js:50:7 › 1. Vai trò Khách vãng lai (khach) › Mở trang Dashboard thống kê (/dashboard.html) không có lỗi console & có banner DỮ LIỆU MẪU (964ms)
  ok 13 [chromium] › tests\ui.spec.js:66:5 › 1. Vai trò Khách vãng lai (khach) › Gõ "luu tru" trên index.html hiển thị danh sách gợi ý autocomplete (829ms)
  ok 14 [chromium] › tests\ui.spec.js:93:5 › 1. Vai trò Khách vãng lai (khach) › Gõ "luu tru" trên tra-cuu.html hiển thị gợi ý và khi bấm kết quả tìm kiếm gọi chọn log (866ms)
  ok 15 [chromium] › tests\ui.spec.js:139:5 › 1. Vai trò Khách vãng lai (khach) › Khách vào quan-ly.html và dashboard.html hiển thị thông báo yêu cầu quyền Thủ thư (458ms)
  ok 16 [chromium] › tests\ui.spec.js:151:5 › 1. Vai trò Khách vãng lai (khach) › Xử lý an toàn: Truy cập tra-cuu.html với tham số URL chứa ký tự đặc biệt không gây lỗi DOMException hay console error (932ms)
  ok 17 [chromium] › tests\ui.spec.js:163:5 › 1. Vai trò Khách vãng lai (khach) › Đặt lại bộ lọc trên tra-cuu.html xóa sạch từ khóa và nạp lại toàn bộ danh mục (463ms)
  ok 18 [chromium] › tests\ui.spec.js:197:7 › 2. Vai trò Sinh viên (sv01 / sv123) › Sinh viên mở trang Trang chủ (/index.html) không có lỗi console & menu đúng vai trò (1.2s)
  ok 19 [chromium] › tests\ui.spec.js:197:7 › 2. Vai trò Sinh viên (sv01 / sv123) › Sinh viên mở trang Tra cứu OPAC (/tra-cuu.html) không có lỗi console & menu đúng vai trò (1.2s)
  ok 20 [chromium] › tests\ui.spec.js:197:7 › 2. Vai trò Sinh viên (sv01 / sv123) › Sinh viên mở trang Chi tiết tư liệu (/chi-tiet.html?id=8) không có lỗi console & menu đúng vai trò (1.2s)
  ok 21 [chromium] › tests\ui.spec.js:197:7 › 2. Vai trò Sinh viên (sv01 / sv123) › Sinh viên mở trang Tài khoản & Đăng nhập (/tai-khoan.html) không có lỗi console & menu đúng vai trò (1.1s)
  ok 22 [chromium] › tests\ui.spec.js:197:7 › 2. Vai trò Sinh viên (sv01 / sv123) › Sinh viên mở trang Quản lý mượn trả (/quan-ly.html) không có lỗi console & menu đúng vai trò (1.1s)
  ok 23 [chromium] › tests\ui.spec.js:197:7 › 2. Vai trò Sinh viên (sv01 / sv123) › Sinh viên mở trang Dashboard thống kê (/dashboard.html) không có lỗi console & menu đúng vai trò (1.2s)
  ok 24 [chromium] › tests\ui.spec.js:216:5 › 2. Vai trò Sinh viên (sv01 / sv123) › Sinh viên xem chi tiết tư liệu có nút Đăng ký mượn (536ms)
  ok 25 [chromium] › tests\ui.spec.js:227:5 › 2. Vai trò Sinh viên (sv01 / sv123) › Sinh viên truy cập quan-ly.html và dashboard.html bị chặn quyền truy cập (660ms)
  ok 26 [chromium] › tests\ui.spec.js:255:7 › 3. Vai trò Thủ thư (thuthu / thuthu123) › Thủ thư mở trang Trang chủ (/index.html) không có lỗi console & menu đầy đủ (1.2s)
  ok 27 [chromium] › tests\ui.spec.js:255:7 › 3. Vai trò Thủ thư (thuthu / thuthu123) › Thủ thư mở trang Tra cứu OPAC (/tra-cuu.html) không có lỗi console & menu đầy đủ (1.2s)
  ok 28 [chromium] › tests\ui.spec.js:255:7 › 3. Vai trò Thủ thư (thuthu / thuthu123) › Thủ thư mở trang Chi tiết tư liệu (/chi-tiet.html?id=8) không có lỗi console & menu đầy đủ (1.1s)
  ok 29 [chromium] › tests\ui.spec.js:255:7 › 3. Vai trò Thủ thư (thuthu / thuthu123) › Thủ thư mở trang Tài khoản & Đăng nhập (/tai-khoan.html) không có lỗi console & menu đầy đủ (1.1s)
  ok 30 [chromium] › tests\ui.spec.js:255:7 › 3. Vai trò Thủ thư (thuthu / thuthu123) › Thủ thư mở trang Quản lý mượn trả (/quan-ly.html) không có lỗi console & menu đầy đủ (1.1s)
  ok 31 [chromium] › tests\ui.spec.js:255:7 › 3. Vai trò Thủ thư (thuthu / thuthu123) › Thủ thư mở trang Dashboard thống kê (/dashboard.html) không có lỗi console & menu đầy đủ (1.3s)
  ok 32 [chromium] › tests\ui.spec.js:278:5 › 3. Vai trò Thủ thư (thuthu / thuthu123) › Thủ thư truy cập quan-ly.html xem được danh sách mượn và form tải bản mềm (657ms)
  ok 33 [chromium] › tests\ui.spec.js:295:5 › 3. Vai trò Thủ thư (thuthu / thuthu123) › Thủ thư truy cập dashboard.html xem được 4 thẻ KPI với dữ liệu thật (1.0s)

  33 passed (44.6s)
```

### 3. `rg -n "require\(|express" server`
```text
(rỗng - exit code 1, không có kết quả khớp)
```

---

## Kết quả Audit (Subagent AUDIT độc lập)
- [x] **Khớp 100% hợp đồng API với bản Express cũ:** Tất cả 20 endpoint trên 5 Blueprint (`auth`, `tai_lieu`, `muon`, `quan_ly`, `thong_ke`) cùng `/api` 404 handler giữ nguyên đường dẫn, phương thức HTTP, mã trạng thái (`200`, `201`, `400`, `401`, `403`, `404`, `409`), cấu trúc JSON phản hồi và cơ chế cookie phiên. Giao diện `public/` không phải chỉnh sửa bất kỳ dòng nào và vượt qua toàn bộ 33/33 test Playwright.
- [x] **SQL tham số hóa 100%:** Mọi truy vấn qua `psycopg2` đều sử dụng tham số `%s`, tuyệt đối không nối chuỗi hay dùng f-string trong SQL.
- [x] **Phân quyền trên mọi route:** 100% các hàm xử lý route trong `server/routes/*.py` đều gắn tường minh `@yeu_cau_vai_tro('*' | 'nguoi_dung' | 'thu_thu')`.
- [x] **Hàm tìm kiếm và chuẩn hóa dùng chung:** `/api/goi-y` và `/api/tim-kiem` dùng hàm CSDL `tim_tai_lieu(%s)` và `f_chuan_hoa(%s)`. Chỉ ghi log khi `q` không rỗng và `trang == 1`; cập nhật `tai_lieu_chon_id` kiểm tra đúng `ma_phien`.
- [x] **Transaction & Khóa dòng:** Duyệt mượn và ghi nhận trả sử dụng `with db.transaction() as cur:` cùng `SELECT ... FOR UPDATE`, trả `409` khi hết bản sao khả dụng.
- [x] **Bảo mật Upload & Đọc bản mềm:** Kiểm tra đuôi `.pdf`, `mimetype == 'application/pdf'`, 4 byte đầu `b'%PDF'`, giới hạn 20MB, xóa file cũ ngoài `mau/` khi tải đè, và chặn Path Traversal trên `GET /api/ban-mem/<id>` bằng `os.path.commonpath` (`403`).
- [x] **Cờ `du_lieu_mau` & Bảo vệ danh tính:** Log tìm kiếm và lượt mượn phát sinh từ API có `du_lieu_mau = false`; các API `/api/thong-ke/*` chỉ trả số liệu tổng hợp, không trả `nguoi_dung_id` hay `ma_phien`.
- [x] **Dọn dẹp sau kiểm thử:** Sau khi chạy `pytest` và `playwright`, số bản ghi có `du_lieu_mau = false` trong `log_tim_kiem`, `luot_muon`, `ban_sao` và `ky_hieu LIKE 'TEST_%'` trong `tai_lieu` đều bằng `0`.

## Vấn đề còn lại
- Không còn vấn đề tồn đọng.

## Opus audit (độc lập)
Chấp nhận. Chạy lại: `python -m pytest server/tests -q` 25 passed; `npx playwright test` 33 passed trên backend Flask; `rg "require\(|express" server` rỗng; không có SQL f-string/nối chuỗi; mọi route Blueprint có `yeu_cau_vai_tro`. Ghi chú: test Playwright để lại 3 log tìm kiếm không phải dữ liệu mẫu (được xóa khi `demo_reset`); SECRET_KEY có giá trị dự phòng cứng khi thiếu .env (chấp nhận cho demo).
