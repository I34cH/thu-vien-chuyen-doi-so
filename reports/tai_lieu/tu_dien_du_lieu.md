# Từ điển dữ liệu CSDL (`thu_vien_ck`)

> Tài liệu được trích xuất tự động từ `information_schema.tables` và `information_schema.columns` của PostgreSQL.

## 1. Tổng quan các bảng và khung nhìn (Views)

| Tên đối tượng | Loại | Số dòng hiện tại | Ý nghĩa nghiệp vụ |
|---|---|---:|---|
| `ban_sao` | Bảng cơ sở (TABLE) | 5,817 | Các bản sao vật lý tại kho tương ứng với từng tư liệu (1–3 bản/tư liệu có bản cứng). |
| `log_tim_kiem` | Bảng cơ sở (TABLE) | 8,000 | Nhật ký truy vấn tìm kiếm của người dùng và tư liệu được nhấp chọn từ danh sách kết quả. |
| `luot_muon` | Bảng cơ sở (TABLE) | 400 | Giao dịch đăng ký mượn, duyệt mượn, trả hoặc từ chối mượn bản sao vật lý. |
| `ma_van_de` | Bảng cơ sở (TABLE) | 29 | Danh mục mã phân loại vấn đề chuyên môn (QTVP, LTH, VB, LT, KS…). |
| `nguoi_dung` | Bảng cơ sở (TABLE) | 63 | Tài khoản người dùng hệ thống (sinh_vien, giang_vien, thu_thu, admin). |
| `tai_lieu` | Bảng cơ sở (TABLE) | 3,400 | Danh mục tư liệu gốc nạp từ 8 sheet Excel của Khoa (sách, luận án, luận văn, khóa luận, báo cáo KH, kỷ yếu). |
| `v_khong_ket_qua` | Khung nhìn (VIEW) | 90 | View liệt kê các từ khóa tìm nhiều nhưng trả về 0 kết quả để gợi ý mua sắm/bổ sung. |
| `v_nen_so_hoa` | Khung nhìn (VIEW) | 612 | View xếp hạng tư liệu ưu tiên số hóa theo công thức điểm = số lần chọn + 2 × số lượt mượn. |
| `v_tim_theo_ngay` | Khung nhìn (VIEW) | 90 | View tổng hợp số lượt tìm kiếm và số lượt 0 kết quả theo từng ngày. |
| `v_tinh_trang_tai_lieu` | Khung nhìn (VIEW) | 3,400 | View tổng hợp tổng số bản sao khả dụng (không mất) và số bản còn rảnh tại kho của mỗi tư liệu. |
| `v_tu_khoa_top` | Khung nhìn (VIEW) | 495 | View thống kê tần suất tìm kiếm theo cụm từ khóa chuẩn hóa và số lần trả về 0 kết quả. |

## 2. Chi tiết cấu trúc từng bảng và View

### Bảng: `ban_sao`

- **Mô tả:** Các bản sao vật lý tại kho tương ứng với từng tư liệu (1–3 bản/tư liệu có bản cứng).

| # | Tên cột | Kiểu dữ liệu | Cho phép NULL | Mặc định | Ý nghĩa |
|---:|---|---|:---:|---|---|
| 1 | `id` | `integer` | NO | `nextval('ban_sao_id_seq'::regclass)` | Mã định danh tự tăng của bản sao (khóa chính). |
| 2 | `tai_lieu_id` | `integer` | NO | — | Khóa ngoại tham chiếu tư liệu gốc tai_lieu(id). |
| 3 | `ma_ban_sao` | `character varying(60)` | NO | — | Mã vạch/ký hiệu từng cuốn bản sao cụ thể (VD: S.001-1). |
| 4 | `trang_thai` | `character varying(20)` | NO | `'con'::character varying` | Trạng thái vật lý: 'con' (sẵn sàng), 'dang_muon' (đang cho mượn), 'mat' (thất lạc). |
| 5 | `du_lieu_mau` | `boolean` | NO | `false` | Cờ phân biệt dữ liệu mô phỏng phục vụ demo (true) và dữ liệu phát sinh thật (false). |

### Bảng: `log_tim_kiem`

- **Mô tả:** Nhật ký truy vấn tìm kiếm của người dùng và tư liệu được nhấp chọn từ danh sách kết quả.

| # | Tên cột | Kiểu dữ liệu | Cho phép NULL | Mặc định | Ý nghĩa |
|---:|---|---|:---:|---|---|
| 1 | `id` | `bigint` | NO | `nextval('log_tim_kiem_id_seq'::regclass)` | Mã định danh tự tăng kiểu bigserial của dòng log tìm kiếm. |
| 2 | `tu_khoa` | `text` | NO | — | Chuỗi truy vấn nguyên bản người dùng nhập vào ô tìm kiếm. |
| 3 | `tu_khoa_chuan` | `text` | NO | — | Chuỗi từ khóa đã chuẩn hóa bằng f_chuan_hoa (chữ thường, bỏ dấu, gộp khoảng trắng). |
| 4 | `so_ket_qua` | `integer` | NO | — | Số lượng tư liệu khớp trả về tại thời điểm tìm kiếm. |
| 5 | `tai_lieu_chon_id` | `integer` | YES | — | Mã tư liệu người dùng nhấp chọn xem chi tiết từ danh sách kết quả (NULL nếu không chọn). |
| 6 | `thoi_diem` | `timestamp with time zone` | NO | `now()` | Thời điểm thực hiện truy vấn tìm kiếm. |
| 7 | `nguoi_dung_id` | `integer` | YES | — | Mã người dùng thực hiện tìm kiếm (NULL nếu là khách vãng lai). |
| 8 | `ma_phien` | `character varying(64)` | YES | — | Mã phiên làm việc ẩn danh (session ID) để liên kết sự kiện chọn kết quả. |
| 9 | `du_lieu_mau` | `boolean` | NO | `false` | Cờ đánh dấu log mô phỏng phục vụ demo. |

### Bảng: `luot_muon`

- **Mô tả:** Giao dịch đăng ký mượn, duyệt mượn, trả hoặc từ chối mượn bản sao vật lý.

| # | Tên cột | Kiểu dữ liệu | Cho phép NULL | Mặc định | Ý nghĩa |
|---:|---|---|:---:|---|---|
| 1 | `id` | `integer` | NO | `nextval('luot_muon_id_seq'::regclass)` | Mã định danh tự tăng của lượt mượn (khóa chính). |
| 2 | `nguoi_dung_id` | `integer` | NO | — | Khóa ngoại tham chiếu độc giả mượn nguoi_dung(id). |
| 3 | `tai_lieu_id` | `integer` | NO | — | Khóa ngoại tham chiếu tư liệu được yêu cầu tai_lieu(id). |
| 4 | `ban_sao_id` | `integer` | YES | — | Khóa ngoại tham chiếu bản sao được gán khi thủ thư duyệt (NULL khi đang chờ duyệt). |
| 5 | `trang_thai` | `character varying(20)` | NO | `'cho_duyet'::character varying` | Trạng thái phiếu mượn: 'cho_duyet', 'dang_muon', 'da_tra', 'tu_choi'. |
| 6 | `ngay_dang_ky` | `timestamp with time zone` | NO | `now()` | Thời điểm độc giả gửi yêu cầu đăng ký mượn. |
| 7 | `ngay_muon` | `date` | YES | — | Ngày thủ thư duyệt và giao bản sao. |
| 8 | `han_tra` | `date` | YES | — | Hạn trả dự kiến (ngay_muon + 14 ngày). |
| 9 | `ngay_tra` | `date` | YES | — | Ngày thực tế độc giả hoàn trả tài liệu. |
| 10 | `du_lieu_mau` | `boolean` | NO | `false` | Cờ đánh dấu lượt mượn mô phỏng phục vụ demo. |

### Bảng: `ma_van_de`

- **Mô tả:** Danh mục mã phân loại vấn đề chuyên môn (QTVP, LTH, VB, LT, KS…).

| # | Tên cột | Kiểu dữ liệu | Cho phép NULL | Mặc định | Ý nghĩa |
|---:|---|---|:---:|---|---|
| 1 | `ma` | `character varying(20)` | NO | — | Mã viết tắt phân loại vấn đề chuyên ngành (khóa chính). |
| 2 | `ten` | `character varying(200)` | YES | — | Tên giải nghĩa đầy đủ của mã vấn đề (để NULL khi chưa có bảng giải nghĩa). |

### Bảng: `nguoi_dung`

- **Mô tả:** Tài khoản người dùng hệ thống (sinh_vien, giang_vien, thu_thu, admin).

| # | Tên cột | Kiểu dữ liệu | Cho phép NULL | Mặc định | Ý nghĩa |
|---:|---|---|:---:|---|---|
| 1 | `id` | `integer` | NO | `nextval('nguoi_dung_id_seq'::regclass)` | Mã định danh tự tăng của người dùng (khóa chính). |
| 2 | `ten_dang_nhap` | `character varying(60)` | NO | — | Tên tài khoản đăng nhập duy nhất (VD: thuthu, sv01, gv01). |
| 3 | `mat_khau_hash` | `character varying(100)` | NO | — | Chuỗi băm mật khẩu bằng thuật toán bcrypt. |
| 4 | `ho_ten` | `character varying(200)` | NO | — | Họ và tên hiển thị của người dùng. |
| 5 | `vai_tro` | `character varying(20)` | NO | — | Vai trò trong hệ thống: sinh_vien, giang_vien, thu_thu, admin. |
| 6 | `du_lieu_mau` | `boolean` | NO | `false` | Cờ đánh dấu tài khoản sinh tự động phục vụ demo. |

### Bảng: `tai_lieu`

- **Mô tả:** Danh mục tư liệu gốc nạp từ 8 sheet Excel của Khoa (sách, luận án, luận văn, khóa luận, báo cáo KH, kỷ yếu).

| # | Tên cột | Kiểu dữ liệu | Cho phép NULL | Mặc định | Ý nghĩa |
|---:|---|---|:---:|---|---|
| 1 | `id` | `integer` | NO | `nextval('tai_lieu_id_seq'::regclass)` | Mã định danh tự tăng của tư liệu (khóa chính). |
| 2 | `ky_hieu` | `character varying(40)` | NO | — | Ký hiệu xếp giá duy nhất (VD: LA.01, VDQ.001). |
| 3 | `loai_hinh` | `character varying(30)` | NO | — | Loại hình tư liệu (luan_an, luan_van, khoa_luan, bao_cao_kh, ky_yeu, sach, sach_ha_noi, tu_sach_tang). |
| 4 | `tieu_de` | `text` | NO | — | Nhan đề đầy đủ của tư liệu hoặc tên đề tài nghiên cứu. |
| 5 | `tac_gia` | `character varying(500)` | YES | — | Họ tên tác giả hoặc người thực hiện đề tài. |
| 6 | `gvhd` | `character varying(500)` | YES | — | Giảng viên hướng dẫn (đối với luận án, luận văn, khóa luận, báo cáo KH). |
| 7 | `co_quan` | `character varying(500)` | YES | — | Cơ quan, đơn vị khảo sát hoặc thực tập. |
| 8 | `nxb` | `character varying(500)` | YES | — | Nhà xuất bản (đối với sách, kỷ yếu). |
| 9 | `nam` | `integer` | YES | — | Năm xuất bản hoặc bảo vệ đã chuẩn hóa về số nguyên 4 chữ số. |
| 10 | `nam_goc` | `character varying(60)` | YES | — | Chuỗi thời gian gốc trong Excel khi không phải số năm đơn thuần (VD: 1985-2005). |
| 11 | `ma_van_de` | `character varying(20)` | YES | — | Khóa ngoại tham chiếu bảng ma_van_de(ma). |
| 12 | `khoa_hoc` | `character varying(40)` | YES | — | Khóa đào tạo của sinh viên/học viên. |
| 13 | `he` | `character varying(40)` | YES | — | Hệ đào tạo (Chính quy, Tại chức…). |
| 14 | `ghi_chu` | `text` | YES | — | Ghi chú tình trạng hoặc thông tin phụ từ Excel gốc. |
| 15 | `khong_co_tl` | `boolean` | NO | `false` | Cờ đánh dấu tư liệu bị ghi chú 'Ko có TL' (không có bản cứng tại kho). |
| 16 | `co_ban_mem` | `boolean` | NO | `false` | Cờ đánh dấu tư liệu đã được số hóa (có tệp PDF bản mềm). |
| 17 | `muc_truy_cap` | `character varying(20)` | YES | — | Mức độ truy cập bản mềm: 'cong_khai' (ai cũng đọc được) hoặc 'noi_bo' (phải đăng nhập). |
| 18 | `duong_dan_ban_mem` | `character varying(300)` | YES | — | Đường dẫn tương đối của tệp PDF trong thư mục uploads/. |
| 19 | `tsv` | `tsvector` | YES | — | Vector toàn văn (tsvector) sinh tự động từ tiêu đề + tác giả đã bỏ dấu phục vụ tìm kiếm GIN. |
| 20 | `sheet_goc` | `character varying(60)` | NO | — | Tên sheet Excel gốc chứa bản ghi. |
| 21 | `dong_goc` | `integer` | NO | — | Số thứ tự dòng trong sheet Excel gốc. |

### View: `v_khong_ket_qua`

- **Mô tả:** View liệt kê các từ khóa tìm nhiều nhưng trả về 0 kết quả để gợi ý mua sắm/bổ sung.

| # | Tên cột | Kiểu dữ liệu | Cho phép NULL | Mặc định | Ý nghĩa |
|---:|---|---|:---:|---|---|
| 1 | `tu_khoa_chuan` | `text` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 2 | `hien_thi` | `text` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 3 | `so_lan` | `integer` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 4 | `lan_cuoi` | `timestamp with time zone` | YES | — | Trường tổng hợp / truy xuất từ view. |

### View: `v_nen_so_hoa`

- **Mô tả:** View xếp hạng tư liệu ưu tiên số hóa theo công thức điểm = số lần chọn + 2 × số lượt mượn.

| # | Tên cột | Kiểu dữ liệu | Cho phép NULL | Mặc định | Ý nghĩa |
|---:|---|---|:---:|---|---|
| 1 | `tai_lieu_id` | `integer` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 2 | `ky_hieu` | `character varying(40)` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 3 | `tieu_de` | `text` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 4 | `tac_gia` | `character varying(500)` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 5 | `loai_hinh` | `character varying(30)` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 6 | `nam` | `integer` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 7 | `so_lan_chon` | `integer` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 8 | `so_luot_muon` | `integer` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 9 | `diem` | `integer` | YES | — | Trường tổng hợp / truy xuất từ view. |

### View: `v_tim_theo_ngay`

- **Mô tả:** View tổng hợp số lượt tìm kiếm và số lượt 0 kết quả theo từng ngày.

| # | Tên cột | Kiểu dữ liệu | Cho phép NULL | Mặc định | Ý nghĩa |
|---:|---|---|:---:|---|---|
| 1 | `ngay` | `date` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 2 | `so_luot` | `integer` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 3 | `so_luot_0_kq` | `integer` | YES | — | Trường tổng hợp / truy xuất từ view. |

### View: `v_tinh_trang_tai_lieu`

- **Mô tả:** View tổng hợp tổng số bản sao khả dụng (không mất) và số bản còn rảnh tại kho của mỗi tư liệu.

| # | Tên cột | Kiểu dữ liệu | Cho phép NULL | Mặc định | Ý nghĩa |
|---:|---|---|:---:|---|---|
| 1 | `tai_lieu_id` | `integer` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 2 | `so_ban` | `integer` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 3 | `so_ban_con` | `integer` | YES | — | Trường tổng hợp / truy xuất từ view. |

### View: `v_tu_khoa_top`

- **Mô tả:** View thống kê tần suất tìm kiếm theo cụm từ khóa chuẩn hóa và số lần trả về 0 kết quả.

| # | Tên cột | Kiểu dữ liệu | Cho phép NULL | Mặc định | Ý nghĩa |
|---:|---|---|:---:|---|---|
| 1 | `tu_khoa_chuan` | `text` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 2 | `hien_thi` | `text` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 3 | `so_lan` | `integer` | YES | — | Trường tổng hợp / truy xuất từ view. |
| 4 | `so_lan_0_kq` | `integer` | YES | — | Trường tổng hợp / truy xuất từ view. |
