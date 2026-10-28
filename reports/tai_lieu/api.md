# Danh sách API Backend (`server/app.py` — Python Flask)

> Tài liệu được trích xuất tự động từ `app.url_map` và decorator `@yeu_cau_vai_tro(...)` trong `server/routes/*.py`.

## 1. Quy ước phân quyền (`server/auth.py`)

- `@yeu_cau_vai_tro('*')`: Tuyến công khai, khách vãng lai chưa đăng nhập cũng gọi được (hệ thống tự cấp `session['ma_phien']`).
- `@yeu_cau_vai_tro('nguoi_dung')`: Yêu cầu đã đăng nhập với vai trò `sinh_vien` hoặc `giang_vien` (chưa đăng nhập trả `401`, sai vai trò trả `403`).
- `@yeu_cau_vai_tro('thu_thu')`: Yêu cầu đã đăng nhập với vai trò `thu_thu` hoặc `admin` (chưa đăng nhập trả `401`, sai vai trò trả `403`).

## 2. Bảng tổng hợp các Endpoint API

| # | Phương thức | Đường dẫn (Route) | Endpoint Flask | Vai trò được phép | Mô tả chức năng |
|---:|:---:|---|---|---|---|
| 1 | `GET` | `/api/ban-mem/<id>` | `tai_lieu.ban_mem` | Công khai (`*` — mọi vai trò, kể cả khách) | Xem hoặc tải tệp PDF bản mềm số hóa của tư liệu: |
| 2 | `POST` | `/api/dang-nhap` | `auth.dang_nhap` | Công khai (`*` — mọi vai trò, kể cả khách) | Đăng nhập hệ thống bằng tên đăng nhập và mật khẩu |
| 3 | `POST` | `/api/dang-xuat` | `auth.dang_xuat` | Công khai (`*` — mọi vai trò, kể cả khách) | Đăng xuất tài khoản và hủy phiên làm việc |
| 4 | `GET` | `/api/gioi-thieu` | `tai_lieu.gioi_thieu` | Công khai (`*` — mọi vai trò, kể cả khách) | Route công khai trả về các số đếm danh mục cho trang chủ |
| 5 | `GET` | `/api/goi-y` | `tai_lieu.goi_y` | Công khai (`*` — mọi vai trò, kể cả khách) | Gợi ý tìm kiếm nhanh (autocomplete, tối đa 8 kết quả) |
| 6 | `POST` | `/api/muon` | `muon.dang_ky_muon` | Bạn đọc đã đăng nhập (`sinh_vien`, `giang_vien`) | Đăng ký mượn tư liệu (tạo lượt mượn ở trạng thái cho_duyet) |
| 7 | `GET` | `/api/muon/cua-toi` | `muon.muon_cua_toi` | Bạn đọc đã đăng nhập (`sinh_vien`, `giang_vien`) | Lấy danh sách các lượt mượn của tài khoản hiện tại |
| 8 | `GET` | `/api/quan-ly/muon` | `quan_ly.danh_sach_muon` | Thủ thư / Quản trị (`thu_thu`, `admin`) | Xem danh sách tất cả các lượt mượn trong hệ thống, có thể lọc theo trạng thái |
| 9 | `POST` | `/api/quan-ly/muon/<id>/duyet` | `quan_ly.duyet_muon` | Thủ thư / Quản trị (`thu_thu`, `admin`) | Duyệt yêu cầu mượn trong Transaction: |
| 10 | `POST` | `/api/quan-ly/muon/<id>/tra` | `quan_ly.tra_muon` | Thủ thư / Quản trị (`thu_thu`, `admin`) | Ghi nhận trả tư liệu: |
| 11 | `POST` | `/api/quan-ly/muon/<id>/tu-choi` | `quan_ly.tu_choi_muon` | Thủ thư / Quản trị (`thu_thu`, `admin`) | Từ chối yêu cầu mượn tư liệu |
| 12 | `POST` | `/api/quan-ly/tai-lieu/<id>/ban-mem` | `quan_ly.upload_ban_mem` | Thủ thư / Quản trị (`thu_thu`, `admin`) | Upload tệp PDF số hóa cho tư liệu: |
| 13 | `GET` | `/api/tai-lieu/<id>` | `tai_lieu.chi_tiet_tai_lieu` | Công khai (`*` — mọi vai trò, kể cả khách) | Chi tiết thông tin tư liệu kèm danh sách bản sao và tình trạng sẵn sàng |
| 14 | `GET` | `/api/thong-ke/khong-ket-qua` | `thong_ke.khong_ket_qua` | Thủ thư / Quản trị (`thu_thu`, `admin`) | Danh sách từ khóa tìm kiếm nhiều nhưng 0 kết quả -> Gợi ý mua/bổ sung tư liệu |
| 15 | `GET` | `/api/thong-ke/nen-so-hoa` | `thong_ke.nen_so_hoa` | Thủ thư / Quản trị (`thu_thu`, `admin`) | Bảng tư liệu đề xuất nên số hóa theo điểm quan tâm (diem = so_lan_chon + 2 * so_luot_muon) |
| 16 | `GET` | `/api/thong-ke/theo-ngay` | `thong_ke.theo_ngay` | Thủ thư / Quản trị (`thu_thu`, `admin`) | Xu hướng lượt tìm kiếm theo ngày (bộ lọc 7, 30 hoặc 90 ngày) |
| 17 | `GET` | `/api/thong-ke/tong-quan` | `thong_ke.tong_quan` | Thủ thư / Quản trị (`thu_thu`, `admin`) | 4 Thẻ KPI chính: Tổng lượt tìm, % tìm không có kết quả, số lượt mượn đang mở, số tư liệu đã số hóa |
| 18 | `GET` | `/api/thong-ke/tu-khoa` | `thong_ke.tu_khoa` | Thủ thư / Quản trị (`thu_thu`, `admin`) | Danh sách từ khóa tìm kiếm nhiều nhất (phục vụ biểu đồ Word Cloud và Bar chart) |
| 19 | `GET` | `/api/tim-kiem` | `tai_lieu.tim_kiem` | Công khai (`*` — mọi vai trò, kể cả khách) | Tìm kiếm danh mục tư liệu có phân trang và bộ lọc. |
| 20 | `POST` | `/api/tim-kiem/<log_id>/chon` | `tai_lieu.chon_tai_lieu` | Công khai (`*` — mọi vai trò, kể cả khách) | Cập nhật tư liệu người dùng đã nhấp vào xem từ kết quả tìm kiếm. |
| 21 | `GET` | `/api/toi` | `auth.toi` | Công khai (`*` — mọi vai trò, kể cả khách) | Lấy thông tin tài khoản đang đăng nhập trong phiên |
