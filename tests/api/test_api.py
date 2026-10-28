"""
Bộ kiểm thử tự động toàn diện cho Backend API (Milestone M3b - Python Flask)
Sử dụng pytest và Flask test client.
Kiểm tra đầy đủ 25 tình huống kiểm thử:
1. Tuyến công khai GET /api/gioi-thieu
2. Tìm "luu tru" có kết quả và tạo đúng 1 dòng log_tim_kiem
3. Khách vãng lai gọi POST /api/muon -> 401
4. nguoi_dung (sinh_vien) gọi /api/thong-ke/* -> 403
5. Duyệt mượn khi hết bản sao khả dụng -> 409
6. Luồng mượn hoàn chỉnh: Đăng ký -> Duyệt -> Trả cập nhật đúng trạng thái bản sao
7. Autocomplete GET /api/goi-y xử lý từ khóa ngắn và trả về tối đa 8 bản ghi
8. Phân trang GET /api/tim-kiem ở trang 2 không tạo log_tim_kiem trùng
9. Xác thực tài khoản: Đăng nhập sai trả về 401, thiếu dữ liệu trả về 400
10. Chi tiết tư liệu GET /api/tai-lieu/:id trả về chi tiết kèm bản sao; không chứa cột nội bộ tsv; ID không tồn tại trả về 404
11. Thủ thư có thể truy cập đầy đủ các báo cáo thống kê Dashboard
12. Upload bản mềm số hóa (kiểm tra header %PDF) và đọc file
13. POST /api/tim-kiem/:logId/chon kiểm tra tính hợp lệ và sự tồn tại của tai_lieu_id
14. Xác thực tài khoản: Đăng nhập với dữ liệu không phải chuỗi trả về 400
15. Bảo mật: Chống Path Traversal trên GET /api/ban-mem/:id
16. Bảo mật upload: Chặn file có đuôi không phải PDF dù giả mạo Content-Type application/pdf
17. Upload bản mềm: Dọn dẹp tệp cũ trên đĩa khi tải đè tệp mới
18. Đăng ký mượn: Chặn đăng ký trùng khi đã có lượt mượn đang chờ duyệt hoặc đang mượn
19. Phân trang tìm kiếm: Trang vượt ngưỡng (trang 999) trả về mảng rỗng nhưng vẫn giữ tong_so chính xác
20. Xử lý tìm kiếm an toàn: Ký tự đặc biệt và ký tự null không làm sập máy chủ
21. Xử lý endpoint API không tồn tại trả về JSON 404
22. POST /api/dang-xuat hủy phiên đăng nhập thành công
23. GET /api/muon/cua-toi trả về danh sách mượn của tài khoản; khách chưa đăng nhập trả về 401
24. GET /api/quan-ly/muon quản lý lượt mượn: hỗ trợ lọc theo trạng thái, cấm người dùng thường
25. POST /api/quan-ly/muon/:id/tu-choi từ chối yêu cầu mượn, cấm người dùng thường
"""

import os
import io
import time
import datetime
import urllib.parse
import pytest
from server.app import app
import server.db as db

@pytest.fixture(scope="module")
def test_context():
    """
    Fixture khởi tạo môi trường test, tạo các test client và bản ghi kiểm thử mẫu,
    sau đó tự động dọn sạch mọi dữ liệu kiểm thử trong teardown.
    """
    tao_log_ids = []
    tao_tl_ids = []
    tao_bs_ids = []
    tao_lm_ids = []
    tao_file_paths = []

    khach_client = app.test_client()
    sv_client = app.test_client()
    thuthu_client = app.test_client()

    # 1. Đăng nhập sinh viên sv01 / sv123
    sv_login = sv_client.post('/api/dang-nhap', json={'ten_dang_nhap': 'sv01', 'mat_khau': 'sv123'})
    assert sv_login.status_code == 200, "Đăng nhập sv01 phải thành công"
    assert sv_login.get_json()['user']['vai_tro'] == 'sinh_vien'

    # 2. Đăng nhập thủ thư thuthu / thuthu123
    tt_login = thuthu_client.post('/api/dang-nhap', json={'ten_dang_nhap': 'thuthu', 'mat_khau': 'thuthu123'})
    assert tt_login.status_code == 200, "Đăng nhập thuthu phải thành công"
    assert tt_login.get_json()['user']['vai_tro'] == 'thu_thu'

    # 3. Tạo tư liệu mẫu không có bản sao (kiểm thử 409)
    res_tl1 = db.query("""
        INSERT INTO tai_lieu (ky_hieu, loai_hinh, tieu_de, tac_gia, nam, khong_co_tl, co_ban_mem, sheet_goc, dong_goc)
        VALUES ('TEST_NO_COPY', 'sach', 'Tư liệu kiểm thử không có bản sao', 'Nhóm Test', 2026, false, false, 'TEST', 1)
        RETURNING id;
    """)
    doc_het_ban_sao_id = res_tl1[0]['id']
    tao_tl_ids.append(doc_het_ban_sao_id)

    # 4. Tạo tư liệu mẫu có 1 bản sao rảnh (kiểm thử luồng mượn -> duyệt -> trả)
    res_tl2 = db.query("""
        INSERT INTO tai_lieu (ky_hieu, loai_hinh, tieu_de, tac_gia, nam, khong_co_tl, co_ban_mem, sheet_goc, dong_goc)
        VALUES ('TEST_CYCLE_DOC', 'sach', 'Tư liệu kiểm thử vòng đời mượn trả', 'Nhóm Test', 2026, false, false, 'TEST', 2)
        RETURNING id;
    """)
    doc_co_ban_sao_id = res_tl2[0]['id']
    tao_tl_ids.append(doc_co_ban_sao_id)

    res_bs = db.query("""
        INSERT INTO ban_sao (tai_lieu_id, ma_ban_sao, trang_thai, du_lieu_mau)
        VALUES (%s, 'TEST_BS_CYCLE_01', 'con', false)
        RETURNING id;
    """, [doc_co_ban_sao_id])
    ban_sao_test_id = res_bs[0]['id']
    tao_bs_ids.append(ban_sao_test_id)

    ctx = {
        'khach_client': khach_client,
        'sv_client': sv_client,
        'thuthu_client': thuthu_client,
        'doc_het_ban_sao_id': doc_het_ban_sao_id,
        'doc_co_ban_sao_id': doc_co_ban_sao_id,
        'ban_sao_test_id': ban_sao_test_id,
        'tao_log_ids': tao_log_ids,
        'tao_tl_ids': tao_tl_ids,
        'tao_bs_ids': tao_bs_ids,
        'tao_lm_ids': tao_lm_ids,
        'tao_file_paths': tao_file_paths,
    }

    yield ctx

    # TEARDOWN: Dọn dẹp dữ liệu kiểm thử theo thứ tự khóa ngoại
    try:
        if tao_lm_ids:
            db.query('DELETE FROM luot_muon WHERE id = ANY(%s::int[])', [tao_lm_ids])
        db.query('DELETE FROM luot_muon WHERE du_lieu_mau = false')

        if tao_log_ids:
            db.query('DELETE FROM log_tim_kiem WHERE id = ANY(%s::bigint[])', [tao_log_ids])
        db.query('DELETE FROM log_tim_kiem WHERE du_lieu_mau = false')

        if tao_bs_ids:
            db.query('DELETE FROM ban_sao WHERE id = ANY(%s::int[])', [tao_bs_ids])
        db.query('DELETE FROM ban_sao WHERE du_lieu_mau = false')

        if tao_tl_ids:
            db.query('DELETE FROM tai_lieu WHERE id = ANY(%s::int[])', [tao_tl_ids])
        db.query("DELETE FROM tai_lieu WHERE ky_hieu LIKE 'TEST_%'")

        for f_path in tao_file_paths:
            if os.path.isfile(f_path):
                try:
                    os.unlink(f_path)
                except OSError:
                    pass
    except Exception as clean_err:
        print(f"Lỗi khi dọn dẹp dữ liệu test: {clean_err}")
    finally:
        db.close_pool()


# --------------------------------------------------------------------------
# Tình huống 0: Tuyến công khai giới thiệu danh mục
# --------------------------------------------------------------------------
def test_0_gioi_thieu(test_context):
    client = app.test_client()
    res = client.get('/api/gioi-thieu')
    assert res.status_code == 200
    data = res.get_json()
    assert data['thanh_cong'] is True
    assert isinstance(data['tong_tai_lieu'], int) and data['tong_tai_lieu'] > 0
    assert isinstance(data['so_da_so_hoa'], int) and data['so_da_so_hoa'] >= 0
    assert isinstance(data['theo_loai_hinh'], list) and len(data['theo_loai_hinh']) > 0


# --------------------------------------------------------------------------
# Tình huống 1: Tìm "luu tru" có kết quả và tạo đúng 1 dòng log_tim_kiem
# --------------------------------------------------------------------------
def test_1_tim_kiem_log(test_context):
    khach = test_context['khach_client']
    res = khach.get('/api/tim-kiem?q=luu tru&trang=1')
    assert res.status_code == 200
    data = res.get_json()
    assert data['thanh_cong'] is True
    assert len(data['du_lieu']) > 0, 'Phải có ít nhất 1 kết quả cho "luu tru"'
    assert data.get('log_id') is not None, 'Phải trả về log_id khi tìm ở trang 1'

    log_id = data['log_id']
    test_context['tao_log_ids'].append(log_id)

    # Kiểm tra trực tiếp trong CSDL
    db_log = db.query('SELECT * FROM log_tim_kiem WHERE id = %s', [log_id])
    assert len(db_log) == 1
    assert db_log[0]['tu_khoa'] == 'luu tru'
    assert db_log[0]['tu_khoa_chuan'] == 'luu tru'
    assert db_log[0]['so_ket_qua'] > 0, 'so_ket_qua trong log phải > 0'
    assert db_log[0]['du_lieu_mau'] is False, 'Log do người dùng tìm phải có du_lieu_mau = false'

    # Kiểm tra cập nhật tài liệu đã chọn từ đúng phiên làm việc
    tai_lieu_chon = data['du_lieu'][0]['id']
    chon_res = khach.post(f'/api/tim-kiem/{log_id}/chon', json={'tai_lieu_id': tai_lieu_chon})
    assert chon_res.status_code == 200
    assert chon_res.get_json()['thanh_cong'] is True

    db_log_updated = db.query('SELECT tai_lieu_chon_id FROM log_tim_kiem WHERE id = %s', [log_id])
    assert db_log_updated[0]['tai_lieu_chon_id'] == tai_lieu_chon

    # Phiên khác cố tình cập nhật log của phiên này phải bị từ chối 403
    stranger = app.test_client()
    stranger.get('/api/toi')  # cấp phiên mới
    stranger_res = stranger.post(f'/api/tim-kiem/{log_id}/chon', json={'tai_lieu_id': tai_lieu_chon})
    assert stranger_res.status_code == 403, 'Phiên khác cập nhật log phải nhận 403'


# --------------------------------------------------------------------------
# Tình huống 2: Khách vãng lai gọi POST /api/muon -> 401
# --------------------------------------------------------------------------
def test_2_khach_muon_401(test_context):
    unauth = app.test_client()
    res = unauth.post('/api/muon', json={'tai_lieu_id': test_context['doc_co_ban_sao_id']})
    assert res.status_code == 401
    data = res.get_json()
    assert data['thanh_cong'] is False
    assert 'error' in data, 'Phải có thông báo lỗi chưa đăng nhập'


# --------------------------------------------------------------------------
# Tình huống 3: nguoi_dung gọi /api/thong-ke/* -> 403
# --------------------------------------------------------------------------
def test_3_nguoi_dung_thong_ke_403(test_context):
    sv = test_context['sv_client']
    endpoints = [
        '/api/thong-ke/tong-quan',
        '/api/thong-ke/tu-khoa',
        '/api/thong-ke/theo-ngay?so_ngay=30',
        '/api/thong-ke/khong-ket-qua',
        '/api/thong-ke/nen-so-hoa'
    ]
    for ep in endpoints:
        res = sv.get(ep)
        assert res.status_code == 403, f'Endpoint {ep} phải cấm người dùng thông thường truy cập (403)'
        assert res.get_json()['thanh_cong'] is False


# --------------------------------------------------------------------------
# Tình huống 4: Duyệt mượn khi hết bản sao khả dụng -> 409 Conflict
# --------------------------------------------------------------------------
def test_4_duyet_het_ban_sao_409(test_context):
    sv = test_context['sv_client']
    thuthu = test_context['thuthu_client']

    # Sinh viên đăng ký mượn tài liệu không có bản sao nào
    muon_res = sv.post('/api/muon', json={'tai_lieu_id': test_context['doc_het_ban_sao_id']})
    assert muon_res.status_code == 201
    assert muon_res.get_json()['thanh_cong'] is True
    luot_muon_id = muon_res.get_json()['luot_muon']['id']
    test_context['tao_lm_ids'].append(luot_muon_id)

    # Thủ thư tiến hành duyệt mượn
    duyet_res = thuthu.post(f'/api/quan-ly/muon/{luot_muon_id}/duyet')
    assert duyet_res.status_code == 409, 'Không còn bản sao khả dụng phải trả về 409'
    assert duyet_res.get_json()['thanh_cong'] is False


# --------------------------------------------------------------------------
# Tình huống 5: Luồng đăng ký -> duyệt -> trả cập nhật đúng trạng thái bản sao
# --------------------------------------------------------------------------
def test_5_luong_muon_hoan_chinh(test_context):
    sv = test_context['sv_client']
    thuthu = test_context['thuthu_client']
    ban_sao_id = test_context['ban_sao_test_id']
    doc_id = test_context['doc_co_ban_sao_id']

    # Bước 1: Trạng thái ban đầu của bản sao là 'con'
    bs_before = db.query('SELECT trang_thai FROM ban_sao WHERE id = %s', [ban_sao_id])
    assert bs_before[0]['trang_thai'] == 'con'

    # Bước 2: Sinh viên đăng ký mượn
    reg_res = sv.post('/api/muon', json={'tai_lieu_id': doc_id})
    assert reg_res.status_code == 201
    assert reg_res.get_json()['thanh_cong'] is True
    lm_id = reg_res.get_json()['luot_muon']['id']
    test_context['tao_lm_ids'].append(lm_id)

    # Lượt mượn là 'cho_duyet', chưa gán bản sao
    lm_check1 = db.query('SELECT trang_thai, ban_sao_id FROM luot_muon WHERE id = %s', [lm_id])
    assert lm_check1[0]['trang_thai'] == 'cho_duyet'
    assert lm_check1[0]['ban_sao_id'] is None

    # Bản sao vẫn là 'con'
    bs_check1 = db.query('SELECT trang_thai FROM ban_sao WHERE id = %s', [ban_sao_id])
    assert bs_check1[0]['trang_thai'] == 'con'

    # Bước 3: Thủ thư duyệt mượn
    approve_res = thuthu.post(f'/api/quan-ly/muon/{lm_id}/duyet')
    assert approve_res.status_code == 200
    assert approve_res.get_json()['thanh_cong'] is True

    # Lượt mượn cập nhật thành 'dang_muon', gán bản sao, có han_tra
    lm_check2 = db.query('SELECT trang_thai, ban_sao_id, han_tra, ngay_muon FROM luot_muon WHERE id = %s', [lm_id])
    assert lm_check2[0]['trang_thai'] == 'dang_muon'
    assert lm_check2[0]['ban_sao_id'] == ban_sao_id
    assert lm_check2[0]['han_tra'] is not None

    han_tra = lm_check2[0]['han_tra']
    if isinstance(han_tra, str):
        han_tra_date = datetime.date.fromisoformat(han_tra)
    else:
        han_tra_date = han_tra
    today = datetime.date.today()
    diff_days = (han_tra_date - today).days
    assert 13 <= diff_days <= 15, f'Hạn trả phải cách ngày hiện tại ~14 ngày (thực tế: {diff_days})'

    # Bản sao chuyển sang 'dang_muon'
    bs_check2 = db.query('SELECT trang_thai FROM ban_sao WHERE id = %s', [ban_sao_id])
    assert bs_check2[0]['trang_thai'] == 'dang_muon'

    # Bước 4: Thủ thư ghi nhận trả tư liệu
    return_res = thuthu.post(f'/api/quan-ly/muon/{lm_id}/tra')
    assert return_res.status_code == 200
    assert return_res.get_json()['thanh_cong'] is True

    # Lượt mượn thành 'da_tra'
    lm_check3 = db.query('SELECT trang_thai, ngay_tra FROM luot_muon WHERE id = %s', [lm_id])
    assert lm_check3[0]['trang_thai'] == 'da_tra'
    assert lm_check3[0]['ngay_tra'] is not None

    # Bản sao trở về 'con'
    bs_check3 = db.query('SELECT trang_thai FROM ban_sao WHERE id = %s', [ban_sao_id])
    assert bs_check3[0]['trang_thai'] == 'con'


# --------------------------------------------------------------------------
# Tình huống 7: Autocomplete GET /api/goi-y
# --------------------------------------------------------------------------
def test_7_autocomplete(test_context):
    client = app.test_client()
    res_short = client.get('/api/goi-y?q=a')
    assert res_short.status_code == 200
    assert res_short.get_json() == []

    res_good = client.get('/api/goi-y?q=luu tru')
    assert res_good.status_code == 200
    data = res_good.get_json()
    assert isinstance(data, list)
    assert len(data) <= 8


# --------------------------------------------------------------------------
# Tình huống 8: Phân trang GET /api/tim-kiem ở trang 2 không sinh log trùng
# --------------------------------------------------------------------------
def test_8_phan_trang_khong_sinh_log(test_context):
    khach = test_context['khach_client']
    res = khach.get('/api/tim-kiem?q=luu tru&trang=2&gioi_han=5')
    assert res.status_code == 200
    data = res.get_json()
    assert data.get('log_id') is None, 'Trang 2 không được ghi thêm log'


# --------------------------------------------------------------------------
# Tình huống 9: Xác thực tài khoản sai mật khẩu / thiếu dữ liệu
# --------------------------------------------------------------------------
def test_9_dang_nhap_sai(test_context):
    client = app.test_client()
    res_empty = client.post('/api/dang-nhap', json={})
    assert res_empty.status_code == 400

    res_wrong = client.post('/api/dang-nhap', json={'ten_dang_nhap': 'sv01', 'mat_khau': 'sai_mat_khau'})
    assert res_wrong.status_code == 401


# --------------------------------------------------------------------------
# Tình huống 10: Chi tiết tư liệu GET /api/tai-lieu/:id
# --------------------------------------------------------------------------
def test_10_chi_tiet_tai_lieu(test_context):
    client = app.test_client()
    doc_id = test_context['doc_co_ban_sao_id']
    res_found = client.get(f'/api/tai-lieu/{doc_id}')
    assert res_found.status_code == 200
    data = res_found.get_json()
    assert data['thanh_cong'] is True
    assert isinstance(data['tai_lieu']['ban_sao'], list)
    assert 'tsv' not in data['tai_lieu'], 'Không được trả về cột nội bộ tsv'

    res_not_found = client.get('/api/tai-lieu/9999999')
    assert res_not_found.status_code == 404


# --------------------------------------------------------------------------
# Tình huống 11: Thủ thư truy cập đầy đủ các báo cáo thống kê Dashboard
# --------------------------------------------------------------------------
def test_11_thong_ke_dashboard(test_context):
    thuthu = test_context['thuthu_client']

    kpi_res = thuthu.get('/api/thong-ke/tong-quan')
    assert kpi_res.status_code == 200
    kpi_data = kpi_res.get_json()
    assert kpi_data['thanh_cong'] is True
    assert 'tong_luot_tim' in kpi_data
    assert 'ti_le_khong_ket_qua' in kpi_data
    assert 'luot_muon_dang_mo' in kpi_data
    assert 'so_da_so_hoa' in kpi_data

    tk_res = thuthu.get('/api/thong-ke/tu-khoa?limit=10')
    assert tk_res.status_code == 200
    assert isinstance(tk_res.get_json()['du_lieu'], list)

    ngay_res = thuthu.get('/api/thong-ke/theo-ngay?so_ngay=30')
    assert ngay_res.status_code == 200
    assert isinstance(ngay_res.get_json()['du_lieu'], list)

    kkq_res = thuthu.get('/api/thong-ke/khong-ket-qua?limit=10')
    assert kkq_res.status_code == 200
    assert isinstance(kkq_res.get_json()['du_lieu'], list)

    sh_res = thuthu.get('/api/thong-ke/nen-so-hoa?limit=10')
    assert sh_res.status_code == 200
    assert isinstance(sh_res.get_json()['du_lieu'], list)


# --------------------------------------------------------------------------
# Tình huống 12: Upload bản mềm PDF và đọc file
# --------------------------------------------------------------------------
def test_12_upload_va_doc_ban_mem(test_context):
    thuthu = test_context['thuthu_client']
    khach = test_context['khach_client']
    sv = test_context['sv_client']
    doc_id = test_context['doc_co_ban_sao_id']

    # 1. Tải lên tệp không hợp lệ (không phải header %PDF) -> 400
    bad_upload = thuthu.post(
        f'/api/quan-ly/tai-lieu/{doc_id}/ban-mem',
        data={
            'file': (io.BytesIO(b'NOT_A_PDF_HEADER_CONTENT'), 'fake.pdf', 'application/pdf'),
            'muc_truy_cap': 'cong_khai'
        },
        content_type='multipart/form-data'
    )
    assert bad_upload.status_code == 400
    assert bad_upload.get_json()['thanh_cong'] is False

    # 2. Tải lên tệp PDF hợp lệ
    valid_pdf_bytes = b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF'
    good_upload = thuthu.post(
        f'/api/quan-ly/tai-lieu/{doc_id}/ban-mem',
        data={
            'file': (io.BytesIO(valid_pdf_bytes), 'tailieu_test.pdf', 'application/pdf'),
            'muc_truy_cap': 'cong_khai'
        },
        content_type='multipart/form-data'
    )
    assert good_upload.status_code == 200
    good_data = good_upload.get_json()
    assert good_data['thanh_cong'] is True
    assert good_data['tai_lieu']['co_ban_mem'] is True

    uploaded_filename = good_data['tai_lieu']['duong_dan_ban_mem']
    test_context['tao_file_paths'].append(
        os.path.abspath(os.path.join(os.getcwd(), 'uploads', uploaded_filename))
    )

    # 3. Khách truy cập bản mềm công khai -> 200 (Content-Type: application/pdf)
    read_pub_res = khach.get(f'/api/ban-mem/{doc_id}')
    assert read_pub_res.status_code == 200
    assert 'application/pdf' in read_pub_res.headers.get('Content-Type', '')

    # 4. Chuyển sang nội bộ: Khách truy cập -> 401; Đăng nhập -> 200
    db.query("UPDATE tai_lieu SET muc_truy_cap = 'noi_bo' WHERE id = %s", [doc_id])

    read_no_auth = khach.get(f'/api/ban-mem/{doc_id}')
    assert read_no_auth.status_code == 401

    read_with_auth = sv.get(f'/api/ban-mem/{doc_id}')
    assert read_with_auth.status_code == 200
    assert 'application/pdf' in read_with_auth.headers.get('Content-Type', '')


# --------------------------------------------------------------------------
# Tình huống 13: POST /api/tim-kiem/:logId/chon kiểm tra tính hợp lệ
# --------------------------------------------------------------------------
def test_13_chon_tai_lieu_validation(test_context):
    khach = test_context['khach_client']
    search_res = khach.get('/api/tim-kiem?q=luu tru')
    log_id = search_res.get_json()['log_id']
    test_context['tao_log_ids'].append(log_id)

    # Mã tư liệu không phải số nguyên -> 400
    res_nan = khach.post(f'/api/tim-kiem/{log_id}/chon', json={'tai_lieu_id': 'khong_hop_le'})
    assert res_nan.status_code == 400

    # Mã tư liệu boolean True -> 400
    res_bool = khach.post(f'/api/tim-kiem/{log_id}/chon', json={'tai_lieu_id': True})
    assert res_bool.status_code == 400

    # Mã tư liệu không tồn tại trong CSDL -> 404
    res_not_found = khach.post(f'/api/tim-kiem/{log_id}/chon', json={'tai_lieu_id': 99999999})
    assert res_not_found.status_code == 404


# --------------------------------------------------------------------------
# Tình huống 14: Xác thực: Đăng nhập với dữ liệu không phải chuỗi -> 400
# --------------------------------------------------------------------------
def test_14_dang_nhap_kieu_sai(test_context):
    client = app.test_client()
    res_num = client.post('/api/dang-nhap', json={'ten_dang_nhap': 12345, 'mat_khau': 'test'})
    assert res_num.status_code == 400
    assert res_num.get_json()['thanh_cong'] is False


# --------------------------------------------------------------------------
# Tình huống 15: Bảo mật chống Path Traversal trên GET /api/ban-mem/:id
# --------------------------------------------------------------------------
def test_15_chong_path_traversal(test_context):
    client = app.test_client()
    doc_id = test_context['doc_co_ban_sao_id']

    # Gán đường dẫn cố tình thoát khỏi thư mục uploads/
    db.query(
        "UPDATE tai_lieu SET co_ban_mem = true, muc_truy_cap = 'cong_khai', duong_dan_ban_mem = '../package.json' WHERE id = %s",
        [doc_id]
    )

    res_attack = client.get(f'/api/ban-mem/{doc_id}')
    assert res_attack.status_code == 403, 'Đường dẫn tệp nằm ngoài uploads/ phải bị chặn 403'
    assert res_attack.get_json()['thanh_cong'] is False

    # Khôi phục
    db.query("UPDATE tai_lieu SET co_ban_mem = false, duong_dan_ban_mem = NULL WHERE id = %s", [doc_id])


# --------------------------------------------------------------------------
# Tình huống 16: Bảo mật upload: Chặn file có đuôi không phải PDF
# --------------------------------------------------------------------------
def test_16_upload_chan_duoi_khong_phai_pdf(test_context):
    thuthu = test_context['thuthu_client']
    doc_id = test_context['doc_co_ban_sao_id']

    fake_bytes = b'%PDF-1.4\nMalicious code'
    res = thuthu.post(
        f'/api/quan-ly/tai-lieu/{doc_id}/ban-mem',
        data={
            'file': (io.BytesIO(fake_bytes), 'exploit.exe', 'application/pdf'),
            'muc_truy_cap': 'cong_khai'
        },
        content_type='multipart/form-data'
    )
    assert res.status_code == 400, 'Tệp có phần mở rộng không phải .pdf phải bị từ chối'
    assert res.get_json()['thanh_cong'] is False


# --------------------------------------------------------------------------
# Tình huống 17: Upload bản mềm dọn dẹp tệp cũ trên đĩa khi tải đè
# --------------------------------------------------------------------------
def test_17_upload_don_tep_cu(test_context):
    thuthu = test_context['thuthu_client']
    doc_id = test_context['doc_co_ban_sao_id']

    pdf_buf1 = b'%PDF-1.4\nFile 1'
    pdf_buf2 = b'%PDF-1.4\nFile 2'

    # Tải tệp lần 1
    upload1 = thuthu.post(
        f'/api/quan-ly/tai-lieu/{doc_id}/ban-mem',
        data={'file': (io.BytesIO(pdf_buf1), 'tailieu_v1.pdf', 'application/pdf')},
        content_type='multipart/form-data'
    )
    assert upload1.status_code == 200
    file1_name = upload1.get_json()['tai_lieu']['duong_dan_ban_mem']
    file1_path = os.path.abspath(os.path.join(os.getcwd(), 'uploads', file1_name))
    test_context['tao_file_paths'].append(file1_path)
    assert os.path.isfile(file1_path), 'File 1 phải tồn tại trên đĩa'

    # Chờ 15ms để timestamp sinh tên mới
    time.sleep(0.02)

    # Tải đè tệp lần 2
    upload2 = thuthu.post(
        f'/api/quan-ly/tai-lieu/{doc_id}/ban-mem',
        data={'file': (io.BytesIO(pdf_buf2), 'tailieu_v2.pdf', 'application/pdf')},
        content_type='multipart/form-data'
    )
    assert upload2.status_code == 200
    file2_name = upload2.get_json()['tai_lieu']['duong_dan_ban_mem']
    file2_path = os.path.abspath(os.path.join(os.getcwd(), 'uploads', file2_name))
    test_context['tao_file_paths'].append(file2_path)

    # File 1 cũ phải được dọn dẹp, file 2 phải tồn tại
    assert not os.path.isfile(file1_path), 'File 1 cũ phải được xóa sau khi tải tệp mới'
    assert os.path.isfile(file2_path), 'File 2 mới phải tồn tại'


# --------------------------------------------------------------------------
# Tình huống 18: Đăng ký mượn chặn trùng khi đã có lượt mượn đang mở
# --------------------------------------------------------------------------
def test_18_chan_dang_ky_muon_trung(test_context):
    sv = test_context['sv_client']

    # Tạo 1 tư liệu mới có bản sao
    res_tl = db.query("""
        INSERT INTO tai_lieu (ky_hieu, loai_hinh, tieu_de, tac_gia, nam, khong_co_tl, co_ban_mem, sheet_goc, dong_goc)
        VALUES ('TEST_DUP_BORROW', 'sach', 'Tư liệu kiểm thử mượn trùng', 'Nhóm Test', 2026, false, false, 'TEST', 3)
        RETURNING id;
    """)
    tl_id = res_tl[0]['id']
    test_context['tao_tl_ids'].append(tl_id)

    # Sinh viên đăng ký mượn lần 1 -> 201
    res1 = sv.post('/api/muon', json={'tai_lieu_id': tl_id})
    assert res1.status_code == 201
    test_context['tao_lm_ids'].append(res1.get_json()['luot_muon']['id'])

    # Sinh viên tiếp tục đăng ký mượn lần 2 cho cùng tư liệu đó -> 400
    res2 = sv.post('/api/muon', json={'tai_lieu_id': tl_id})
    assert res2.status_code == 400
    assert res2.get_json()['thanh_cong'] is False


# --------------------------------------------------------------------------
# Tình huống 19: Phân trang trang vượt ngưỡng (trang 999)
# --------------------------------------------------------------------------
def test_19_phan_trang_vuot_nguong(test_context):
    khach = test_context['khach_client']
    res = khach.get('/api/tim-kiem?q=luu tru&trang=999&gioi_han=20')
    assert res.status_code == 200
    data = res.get_json()
    assert data['thanh_cong'] is True
    assert len(data['du_lieu']) == 0
    assert data['tong_so'] > 0, 'tong_so vẫn phải thể hiện đúng số lượng kết quả phù hợp'
    assert data.get('log_id') is None, 'Trang vượt ngưỡng không được sinh log'


# --------------------------------------------------------------------------
# Tình huống 20: Ký tự đặc biệt và ký tự null không làm sập máy chủ
# --------------------------------------------------------------------------
def test_20_tim_kiem_ky_tu_dac_biet(test_context):
    khach = test_context['khach_client']
    safe_queries = ["' OR 1=1 --", '::', '% _ \\', '() * & | !', 'luu\0tru']
    for q in safe_queries:
        encoded = urllib.parse.quote(q)
        res = khach.get(f'/api/tim-kiem?q={encoded}')
        assert res.status_code == 200, f'Truy vấn "{q}" không được trả về lỗi 500'
        assert res.get_json()['thanh_cong'] is True


# --------------------------------------------------------------------------
# Tình huống 21: Endpoint API không tồn tại trả về JSON 404
# --------------------------------------------------------------------------
def test_21_endpoint_khong_ton_tai(test_context):
    client = app.test_client()
    res_root = client.get('/api')
    assert res_root.status_code == 404
    assert res_root.get_json()['thanh_cong'] is False

    res_sub = client.get('/api/khong-ton-tai-endpoint')
    assert res_sub.status_code == 404
    assert res_sub.get_json()['thanh_cong'] is False


# --------------------------------------------------------------------------
# Tình huống 22: POST /api/dang-xuat hủy phiên đăng nhập thành công
# --------------------------------------------------------------------------
def test_22_dang_xuat(test_context):
    user_client = app.test_client()
    login_res = user_client.post('/api/dang-nhap', json={'ten_dang_nhap': 'sv01', 'mat_khau': 'sv123'})
    assert login_res.status_code == 200

    toi_before = user_client.get('/api/toi')
    assert toi_before.get_json()['dang_nhap'] is True

    logout_res = user_client.post('/api/dang-xuat')
    assert logout_res.status_code == 200
    assert logout_res.get_json()['thanh_cong'] is True

    toi_after = user_client.get('/api/toi')
    assert toi_after.get_json()['dang_nhap'] is False
    assert toi_after.get_json()['vai_tro'] == 'khach'


# --------------------------------------------------------------------------
# Tình huống 23: GET /api/muon/cua-toi
# --------------------------------------------------------------------------
def test_23_muon_cua_toi(test_context):
    khach = test_context['khach_client']
    sv = test_context['sv_client']

    # Khách chưa đăng nhập -> 401
    res_khach = khach.get('/api/muon/cua-toi')
    assert res_khach.status_code == 401
    assert res_khach.get_json()['thanh_cong'] is False

    # Sinh viên đã đăng nhập -> 200 và danh sách lượt mượn
    res_sv = sv.get('/api/muon/cua-toi')
    assert res_sv.status_code == 200
    assert res_sv.get_json()['thanh_cong'] is True
    assert isinstance(res_sv.get_json()['luot_muon'], list)


# --------------------------------------------------------------------------
# Tình huống 24: GET /api/quan-ly/muon
# --------------------------------------------------------------------------
def test_24_quan_ly_muon_danh_sach(test_context):
    sv = test_context['sv_client']
    thuthu = test_context['thuthu_client']

    # Người dùng thường (sv01) bị cấm 403
    res_forbidden = sv.get('/api/quan-ly/muon')
    assert res_forbidden.status_code == 403
    assert res_forbidden.get_json()['thanh_cong'] is False

    # Thủ thư lấy toàn bộ danh sách -> 200
    res_all = thuthu.get('/api/quan-ly/muon')
    assert res_all.status_code == 200
    assert res_all.get_json()['thanh_cong'] is True
    assert isinstance(res_all.get_json()['luot_muon'], list)

    # Lọc theo trạng thái cho_duyet
    res_filter = thuthu.get('/api/quan-ly/muon?trang_thai=cho_duyet')
    assert res_filter.status_code == 200
    assert res_filter.get_json()['thanh_cong'] is True
    assert isinstance(res_filter.get_json()['luot_muon'], list)
    for lm in res_filter.get_json()['luot_muon']:
        assert lm['trang_thai'] == 'cho_duyet'


# --------------------------------------------------------------------------
# Tình huống 25: POST /api/quan-ly/muon/:id/tu-choi
# --------------------------------------------------------------------------
def test_25_tu_choi_muon(test_context):
    sv = test_context['sv_client']
    thuthu = test_context['thuthu_client']

    # Tạo 1 tư liệu và 1 yêu cầu mượn ở trạng thái cho_duyet
    res_tl = db.query("""
        INSERT INTO tai_lieu (ky_hieu, loai_hinh, tieu_de, tac_gia, nam, khong_co_tl, co_ban_mem, sheet_goc, dong_goc)
        VALUES ('TEST_REJECT_DOC', 'sach', 'Tư liệu kiểm thử từ chối mượn', 'Nhóm Test', 2026, false, false, 'TEST', 4)
        RETURNING id;
    """)
    tl_id = res_tl[0]['id']
    test_context['tao_tl_ids'].append(tl_id)

    borrow_res = sv.post('/api/muon', json={'tai_lieu_id': tl_id})
    assert borrow_res.status_code == 201
    lm_id = borrow_res.get_json()['luot_muon']['id']
    test_context['tao_lm_ids'].append(lm_id)

    # Người dùng thường không được phép từ chối -> 403
    res_forbidden = sv.post(f'/api/quan-ly/muon/{lm_id}/tu-choi')
    assert res_forbidden.status_code == 403

    # Thủ thư từ chối yêu cầu mượn -> 200
    reject_res = thuthu.post(f'/api/quan-ly/muon/{lm_id}/tu-choi')
    assert reject_res.status_code == 200
    assert reject_res.get_json()['thanh_cong'] is True
    assert reject_res.get_json()['luot_muon']['trang_thai'] == 'tu_choi'

    # Kiểm tra trực tiếp trong CSDL
    db_check = db.query('SELECT trang_thai FROM luot_muon WHERE id = %s', [lm_id])
    assert db_check[0]['trang_thai'] == 'tu_choi'

    # Từ chối lại lượt mượn đã bị từ chối -> 400
    reject_again = thuthu.post(f'/api/quan-ly/muon/{lm_id}/tu-choi')
    assert reject_again.status_code == 400
