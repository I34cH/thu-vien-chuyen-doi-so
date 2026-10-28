# Web Thư Viện Chuyển Đổi Số — Hỗ Trợ Ra Quyết Định Số Hóa Tư Liệu

> **Đề tài cuối kì môn Trực quan hóa dữ liệu**  
> **Lưu ý:** Dữ liệu nhật ký tìm kiếm (`log_tim_kiem`), giao dịch mượn trả (`luot_muon`), bản sao (`ban_sao`) và người dùng (`nguoi_dung`) trong hệ thống là **DỮ LIỆU MẪU** (`du_lieu_mau = true`, sinh với `seed = 42`) trên nền **3.400 tư liệu thật** của Khoa để phục vụ trình diễn vòng lặp chuyển đổi số.

---

## 1. Mục tiêu bài toán & Vòng lặp chuyển đổi số

Hệ thống minh họa cách **dữ liệu hành vi tra cứu và mượn trả** giúp thủ thư quyết định **ưu tiên số hóa tư liệu nào trước** trong điều kiện nguồn lực có hạn:

1. **Người dùng tra cứu & mượn tư liệu** → Hệ thống tự động ghi nhận mọi lượt tìm kiếm (`log_tim_kiem`), sự kiện nhấp chọn kết quả (`tai_lieu_chon_id`) và yêu cầu mượn bản cứng (`luot_muon`).
2. **Thủ thư quan sát Dashboard trực quan hóa** → Nắm bắt chủ đề đang được quan tâm (Word Cloud, Top 15 từ khóa), xu hướng theo ngày (Line chart 7/30/90 ngày), các khoảng trống học liệu cần bổ sung (Bảng từ khóa 0 kết quả) và danh sách xếp hạng ưu tiên số hóa theo công thức:
   $$\text{Điểm ưu tiên} = \text{Số lần chọn} + 2 \times \text{Số lượt mượn}$$
3. **Thủ thư thực hiện số hóa (Tải bản mềm PDF)** → Tư liệu có bản mềm lập tức được phục vụ đọc trực tuyến (`cong_khai` hoặc `noi_bo`) và tự động rời khỏi danh sách chờ số hóa, nhường vị trí ưu tiên cho các tư liệu tiếp theo.

---

## 2. Công nghệ sử dụng

- **Cơ sở dữ liệu:** PostgreSQL (sử dụng extension `unaccent` và `pg_trgm` cho tìm kiếm toàn văn không dấu kết hợp độ tương đồng trigram).
- **Backend:** Python 3 + Flask + `psycopg2` (SQL thuần tham số hóa `%s`, không dùng ORM) + Flask signed session cookie + `bcrypt`.
- **Frontend:** HTML5 / CSS3 / JavaScript thuần (`fetch` API), kế thừa khung giao diện học thuật với tông **Đỏ chủ đạo** (`#9b1c1c`, `#6b1010`, `#c53030`) và màu nhấn **Vàng kim** (`#d4af37`).
- **Trực quan hóa dữ liệu:** `Chart.js` (4.4.1), `wordcloud2.js` (1.2.2) trên web và `matplotlib` cho xuất báo cáo tĩnh.
- **Kiểm thử & Công cụ tự động:** `pytest` (25 ca kiểm thử API backend), `Playwright` (33 ca kiểm thử giao diện và chụp màn hình tự động).

---

## 3. Hướng dẫn cài đặt & Khởi chạy

### Bước 1: Chuẩn bị biến môi trường và CSDL PostgreSQL
Đảm bảo PostgreSQL đang chạy và đã tạo cơ sở dữ liệu `thu_vien_ck`. Sao chép tệp `.env.example` thành `.env`:

```powershell
Copy-Item .env.example .env
```

Nội dung `.env` mẫu:
```ini
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/thu_vien_ck
SESSION_SECRET=thu-vien-chuyen-doi-so-secret-key-2026
PORT=3000
```

### Bước 2: Cài đặt thư viện
```powershell
# 1. Cài đặt toàn bộ thư viện Python cho ETL, Seed, Backend Flask, Pytest và xuất báo cáo
pip install -r scripts/requirements.txt

# 2. Cài đặt gói Node.js (chỉ dùng để chạy Playwright kiểm thử giao diện và chụp ảnh màn hình)
npm install
npx playwright install chromium
```

### Bước 3: Khởi tạo CSDL, nạp dữ liệu thật (ETL) và sinh dữ liệu mẫu (Seed 42)
```powershell
python tools/demo_reset.py
# Hoặc: npm run demo:reset
```
Lệnh trên sẽ tự động chạy `db/schema.sql`, `db/views.sql`, nạp 8 sheet từ tệp Excel gốc (`3.400` tư liệu) và sinh dữ liệu mô phỏng với `seed = 42` (`5.817` bản sao, `63` người dùng, `8.000` log tìm kiếm, `400` lượt mượn, `40` tư liệu có bản mềm mẫu).

### Bước 4: Khởi chạy máy chủ Web
```powershell
python server/app.py
# Hoặc: npm start
```
Mở trình duyệt tại địa chỉ: **`http://localhost:3000`**

---

## 4. Tài khoản Demo

| Vai trò | Tên đăng nhập | Mật khẩu | Quyền hạn trong bản Demo |
|---|---|---|---|
| **Khách vãng lai** | *(Không đăng nhập)* | — | Tìm kiếm OPAC (có gợi ý autocomplete), lọc danh mục, xem chi tiết tư liệu, đọc bản mềm `cong_khai`. |
| **Sinh viên** (`nguoi_dung`) | `sv01` | `sv123` | Toàn bộ quyền của khách + đọc bản mềm `noi_bo`, gửi yêu cầu **Đăng ký mượn**, theo dõi **Lượt mượn của tôi**. |
| **Giảng viên** (`nguoi_dung`) | `gv01` | `gv123` | Tương tự sinh viên (`nguoi_dung`). |
| **Thủ thư** (`thu_thu`) | `thuthu` | `thuthu123` | Duyệt / từ chối / ghi nhận trả mượn bản sao, tải bản mềm PDF số hóa, xem **Dashboard Thống kê**. |
| **60 tài khoản mẫu khác** | `sv02`..`sv49`, `gv02`..`gv13` | `demo123` | Sinh tự động bằng `Faker('vi_VN')` phục vụ dữ liệu mẫu. |

---

## 5. KỊCH BẢN DEMO 5 PHÚT

Trước buổi trình diễn, chạy `python tools/demo_reset.py` và khởi động `python server/app.py`.

### Phút 1 — Khách vãng lai tìm kiếm không dấu & Hệ thống ghi nhận hành vi
1. Mở trang chủ `http://localhost:3000` (trạng thái chưa đăng nhập — vai trò **Khách**). Chỉ vào **Banner cố định** trên đầu trang khẳng định dữ liệu log/mượn là dữ liệu mẫu phục vụ demo, và 4 ô số liệu danh mục thật từ CSDL (`3.400` tư liệu, `40` đã số hóa).
2. Tại ô tìm kiếm trung tâm, gõ không dấu **`luu tru`** → Danh sách **Autocomplete** lập tức gợi ý các tư liệu khớp nhờ kết hợp `unaccent` và `pg_trgm`.
3. Nhấn **Tìm kiếm** để sang trang `tra-cuu.html`: hệ thống hiển thị các tư liệu khớp kèm trạng thái **`Còn x/y bản`** và nhãn **`Có bản mềm`**, đồng thời tạo 1 bản ghi trong bảng `log_tim_kiem`.
4. Nhấp vào một tư liệu đứng đầu chưa có bản mềm → Hệ thống tự động cập nhật cột `tai_lieu_chon_id` cho dòng log vừa tạo và mở trang `chi-tiet.html`. Khách chưa đăng nhập sẽ thấy thông báo cần đăng nhập để đăng ký mượn.

### Phút 2 — Bạn đọc (`sv01`) đăng ký mượn tư liệu
1. Chuyển sang trang **Đăng nhập** (`tai-khoan.html`), bấm nút điền nhanh **` Sinh viên (sv01)`** (hoặc nhập `sv01` / `sv123`) rồi đăng nhập.
2. Xem bảng **Lượt mượn của tôi**: thấy sẵn các trạng thái `Chờ duyệt`, `Đang mượn`, `Đã trả`.
3. Mở một tư liệu còn bản sao rảnh (ví dụ từ trang tra cứu hoặc `/chi-tiet.html?id=8`), nhấn nút **`Đăng ký mượn`** → Hệ thống tạo lượt mượn mới ở trạng thái **`cho_duyet`**.

### Phút 3 — Thủ thư (`thuthu`) duyệt phiếu mượn trong Transaction
1. Đăng xuất `sv01`, đăng nhập tài khoản Thủ thư **`thuthu` / `thuthu123`** và mở trang **Quản lý Mượn - Trả** (`quan-ly.html`).
2. Lọc danh sách theo trạng thái **`Chờ duyệt`**, nhấn nút **`Duyệt mượn`** trên yêu cầu của `sv01`.
3. Hệ thống thực hiện transaction `SELECT ... FOR UPDATE`, tự động gán 1 bản sao có trạng thái `'con'`, đổi trạng thái bản sao sang `'dang_muon'` và đặt hạn trả **+14 ngày**. (Nếu bấm **`Ghi nhận trả`** ở một dòng đang mượn, bản sao lập tức trở về trạng thái `'con'`).

### Phút 4 — Thủ thư phân tích Dashboard trực quan hóa (`dashboard.html`)
1. Mở trang **Dashboard Thống kê** (`dashboard.html`), trình bày 4 thẻ KPI tổng hợp (Tổng lượt tìm, % 0 kết quả, Lượt mượn đang mở, Số tư liệu đã số hóa).
2. **Word Cloud & Biểu đồ cột ngang Top 15 từ khóa:** Chỉ ra các chủ đề bạn đọc tra cứu nhiều nhất (`lưu trữ`, `tài liệu`, `công tác`, `việt nam`, `quản lý`…).
3. **Biểu đồ đường (Line Chart) xu hướng tìm kiếm:** Bấm chuyển đổi giữa **7 ngày / 30 ngày / 90 ngày**; chỉ vào điểm cuối của ngày hôm nay được đánh dấu **`(đang cập nhật)`** bằng đoạn nối nét đứt.
4. **Hai bảng ra quyết định:**
   - **Bảng từ khóa tìm nhiều nhưng 0 kết quả** (`python`, `blockchain`, `điện toán đám mây`…) → Căn cứ đề xuất **mua bổ sung** học liệu mới.
   - **Bảng tư liệu ưu tiên số hóa** (`diem = so_lan_chon + 2 * so_luot_muon`) → Chỉ ra tư liệu đang đứng vị trí **#1** có nhu cầu đọc/mượn cao nhất nhưng chưa có bản mềm.

### Phút 5 — Số hóa tư liệu & Khép kín vòng lặp
1. Tại dòng đầu tiên của bảng **Tư liệu cần được ưu tiên số hóa trước**, nhấn nút **`Số hóa`** → Trình duyệt chuyển thẳng sang form **Tải bản mềm số hóa (PDF)** trên trang `quan-ly.html` và điền sẵn mã tư liệu.
2. Chọn tệp PDF mẫu (`uploads/mau/ban_mem_mau.pdf`), chọn mức truy cập **`Công khai (Ai cũng đọc được)`** (hoặc `Nội bộ`) và nhấn **`Tải bản mềm lên`**.
3. Quay lại trang **Dashboard** (`dashboard.html`):
   - Thẻ KPI **Tư liệu đã được số hóa** tăng thêm **1** (`41 / 3.400`).
   - Tư liệu vừa tải bản mềm **biến mất khỏi bảng đề xuất số hóa**, nhường vị trí đầu bảng cho tư liệu tiếp theo.
4. Đăng nhập lại tài khoản **`sv01`** (hoặc xem với tư cách khách), mở lại trang chi tiết của tư liệu vừa số hóa → Nút **`Đọc / Tải bản mềm PDF`** đã xuất hiện và mở trực tiếp tệp PDF trên trình duyệt.

---

## 6. Kiểm thử tự động & Xuất báo cáo

Chạy toàn bộ chuỗi lệnh kiểm chứng của dự án:

```powershell
# 1. Đặt lại CSDL + ETL + Seed mẫu
python tools/demo_reset.py

# 2. Chạy 25 bài kiểm thử API Backend (pytest)
python -m pytest tests/api -q

# 3. Chạy 33 bài kiểm thử giao diện tự động (Playwright)
npx playwright test

# 4. Chụp ảnh màn hình toàn bộ trang (3 vai trò x 6 trang x 1440px/390px + biểu đồ)
npm run screenshots

# 5. Xuất bộ báo cáo CSV, biểu đồ Matplotlib, Từ điển dữ liệu, ERD và API
python tools/export_report.py
```

Các đầu ra phục vụ báo cáo được lưu tại thư mục `reports/`:
- `reports/etl/`: Báo cáo kết quả làm sạch và nạp dữ liệu thật (`etl_tom_tat.csv`, `etl_bi_bo.csv`).
- `reports/seed/`: Thống kê phân bố mô phỏng Zipf và biểu đồ log-log (`seed_tom_tat.md`, `zipf.png`).
- `reports/so_lieu/*.csv`: 5 tệp số liệu tổng hợp (`tu_khoa_top.csv`, `khong_ket_qua.csv`, `nen_so_hoa.csv`, `theo_ngay.csv`, `theo_loai_hinh.csv`).
- `reports/bieu_do/*.png`: 5 biểu đồ Matplotlib độ phân giải cao.
- `reports/screenshots/`: Ảnh chụp màn hình thực tế theo 3 vai trò (`khach`, `nguoi_dung`, `thu_thu`) ở `1440px` và `390px` cùng ảnh từng biểu đồ trên `dashboard/`.
- `reports/tai_lieu/tu_dien_du_lieu.md`: Từ điển dữ liệu trích xuất từ `information_schema`.
- `reports/tai_lieu/erd.png`: Sơ đồ quan hệ thực thể (ERD).
- `reports/tai_lieu/api.md`: Tài liệu đặc tả toàn bộ API và phân quyền trích xuất từ Flask.
- `reports/milestones/M1.md` .. `M6.md` & `reports/TONG_KET.md`: Báo cáo nghiệm thu từng chặng và tổng kết dự án.

---

## 7. Cấu trúc thư mục dự án

```text
CK/
├── AGENTS.md                  # Hướng dẫn quy tắc & ràng buộc dành cho các agent
├── README.md                  # Hướng dẫn cài đặt, vận hành & kịch bản demo 5 phút
├── .gitignore                 # Bỏ qua các tệp tạm, cache, logs, uploads cá nhân
├── package.json               # Cấu hình kịch bản npm & công cụ Playwright
├── playwright.config.js       # Cấu hình Playwright kiểm thử UI (testDir: tests/ui)
├── pytest.ini                 # Cấu hình Pytest kiểm thử API (testpaths: tests/api)
├── data/                      # Tệp Excel danh mục 3.470 tư liệu gốc của Khoa (chỉ đọc)
├── prompts/                   # Kế hoạch & prompt cho luồng agent (Opus → Argon → Gemini Flash)
├── db/                        # Kịch bản DDL tạo bảng (schema.sql) và khung nhìn (views.sql)
├── docs/                      # Tài liệu đề bài, sơ đồ ERD gốc (erd.mmd, erd.png, file PDF mô tả)
├── public/                    # Giao diện web tĩnh (HTML, CSS và JavaScript render client)
│   ├── css/style.css          # Phong cách giao diện với bảng màu chủ đạo Đỏ - Vàng kim
│   ├── js/main.js             # Logic dùng chung (auth bar, toast, tiện ích fetch)
│   └── js/trang/              # Module JavaScript chuyên biệt cho từng trang (index, tra-cuu, chi-tiet...)
├── reports/                   # Toàn bộ đầu ra phục vụ báo cáo học thuật
│   ├── etl/                   # Báo cáo kết quả ETL và dữ liệu bị loại trừ
│   ├── seed/                  # Báo cáo sinh dữ liệu mẫu và phân bố Zipf
│   ├── tai_lieu/              # Từ điển dữ liệu CSDL, sơ đồ ERD, đặc tả API Flask
│   ├── so_lieu/               # 5 tệp số liệu CSV phục vụ phân tích
│   ├── bieu_do/               # 5 biểu đồ Matplotlib tương ứng số liệu
│   ├── screenshots/           # Ảnh chụp giao diện theo 3 vai trò (1440px, 390px) & dashboard
│   ├── milestones/            # Nhật ký kiểm chứng từng chặng (M1 – M7)
│   └── TONG_KET.md            # Báo cáo tổng kết toàn diện dự án
├── scripts/                   # Kịch bản ETL nạp dữ liệu thật & sinh dữ liệu mô phỏng Zipf
├── server/                    # Máy chủ backend Python Flask & các module Blueprint API
├── tests/                     # Toàn bộ kiểm thử tự động của hệ thống
│   ├── api/                   # 25 ca kiểm thử Backend API bằng pytest (test_api.py)
│   └── ui/                    # 33 ca kiểm thử giao diện & dashboard bằng Playwright (*.spec.js)
├── tools/                     # Công cụ tiện ích (demo_reset.py, screenshots.js, export_report.py)
│   └── agy/                   # Prompt giao việc cho agy (Argon) + nhật ký chạy (logs/)
└── uploads/                   # Thư mục lưu trữ bản mềm PDF số hóa (kèm file mẫu uploads/mau/)
```
