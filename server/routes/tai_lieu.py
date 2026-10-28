"""
Blueprint tra cứu tư liệu: Giới thiệu, Gợi ý tìm kiếm, Tra cứu, Chọn kết quả, Chi tiết và Đọc bản mềm
"""
import os
import math
from flask import Blueprint, request, session, jsonify, send_file
import server.db as db
from server.auth import yeu_cau_vai_tro

tai_lieu_bp = Blueprint('tai_lieu', __name__)

@tai_lieu_bp.route('/gioi-thieu', methods=['GET'])
@yeu_cau_vai_tro('*')
def gioi_thieu():
    """
    GET /api/gioi-thieu
    Route công khai trả về các số đếm danh mục cho trang chủ
    """
    tong_res = db.query("""
        SELECT 
          count(*)::int AS tong_tai_lieu,
          count(*) FILTER (WHERE co_ban_mem = true)::int AS so_da_so_hoa,
          count(*) FILTER (WHERE khong_co_tl = false)::int AS co_ban_cung
        FROM tai_lieu;
    """)

    loai_res = db.query("""
        SELECT loai_hinh, count(*)::int AS so_luong
        FROM tai_lieu
        GROUP BY loai_hinh
        ORDER BY so_luong DESC;
    """)

    stats = tong_res[0] if tong_res else {'tong_tai_lieu': 0, 'so_da_so_hoa': 0, 'co_ban_cung': 0}

    return jsonify({
        'thanh_cong': True,
        'tong_tai_lieu': stats['tong_tai_lieu'],
        'so_da_so_hoa': stats['so_da_so_hoa'],
        'co_ban_cung': stats['co_ban_cung'],
        'theo_loai_hinh': loai_res
    })

@tai_lieu_bp.route('/goi-y', methods=['GET'])
@yeu_cau_vai_tro('*')
def goi_y():
    """
    GET /api/goi-y?q=
    Gợi ý tìm kiếm nhanh (autocomplete, tối đa 8 kết quả)
    Bắt buộc sử dụng hàm SQL tim_tai_lieu(q)
    """
    raw_q = request.args.get('q', '')
    q = str(raw_q).replace('\0', '').strip()[:200]
    if not q or len(q) < 2:
        return jsonify([])

    rows = db.query("""
        SELECT t.id, t.ky_hieu, t.tieu_de, t.tac_gia, t.loai_hinh, t.nam, s.diem
        FROM tim_tai_lieu(%s) s
        JOIN tai_lieu t ON t.id = s.tai_lieu_id
        ORDER BY s.diem DESC, t.id ASC
        LIMIT 8
    """, [q])

    return jsonify(rows)

@tai_lieu_bp.route('/tim-kiem', methods=['GET'])
@yeu_cau_vai_tro('*')
def tim_kiem():
    """
    GET /api/tim-kiem?q=&loai=&tu_nam=&den_nam=&trang=&gioi_han=
    Tìm kiếm danh mục tư liệu có phân trang và bộ lọc.
    Bắt buộc dùng hàm SQL tim_tai_lieu(q).
    Chỉ ghi log_tim_kiem khi q không rỗng VÀ đang ở trang 1.
    """
    raw_q = request.args.get('q', '')
    q = str(raw_q).replace('\0', '').strip()[:200]

    raw_loai = request.args.get('loai')
    loai = str(raw_loai).strip() if raw_loai and str(raw_loai).strip() else None

    try:
        raw_tu_nam = request.args.get('tu_nam')
        tu_nam = int(raw_tu_nam) if raw_tu_nam is not None and raw_tu_nam != '' else None
    except (ValueError, TypeError):
        tu_nam = None

    try:
        raw_den_nam = request.args.get('den_nam')
        den_nam = int(raw_den_nam) if raw_den_nam is not None and raw_den_nam != '' else None
    except (ValueError, TypeError):
        den_nam = None

    try:
        trang = int(request.args.get('trang', 1))
        if trang < 1:
            trang = 1
    except (ValueError, TypeError):
        trang = 1

    try:
        gioi_han = int(request.args.get('gioi_han', 20))
        if gioi_han < 1:
            gioi_han = 20
        if gioi_han > 100:
            gioi_han = 100
    except (ValueError, TypeError):
        gioi_han = 20

    vi_tri_offset = (trang - 1) * gioi_han

    rows = []
    tong_so = 0

    if q:
        sql_tim_kiem = """
            WITH tim AS (
              SELECT tai_lieu_id, diem FROM tim_tai_lieu(%s)
            )
            SELECT t.id, t.ky_hieu, t.loai_hinh, t.tieu_de, t.tac_gia, t.nxb, t.nam,
                   t.co_ban_mem, t.khong_co_tl, t.muc_truy_cap,
                   v.so_ban, v.so_ban_con,
                   tim.diem,
                   count(*) OVER()::int AS tong_so
            FROM tim
            JOIN tai_lieu t ON t.id = tim.tai_lieu_id
            LEFT JOIN v_tinh_trang_tai_lieu v ON v.tai_lieu_id = t.id
            WHERE (%s::varchar IS NULL OR t.loai_hinh = %s)
              AND (%s::int IS NULL OR t.nam >= %s)
              AND (%s::int IS NULL OR t.nam <= %s)
            ORDER BY tim.diem DESC, t.id ASC
            OFFSET %s LIMIT %s;
        """
        rows = db.query(sql_tim_kiem, [q, loai, loai, tu_nam, tu_nam, den_nam, den_nam, vi_tri_offset, gioi_han])
        if rows:
            tong_so = rows[0]['tong_so']
        elif trang > 1:
            count_res = db.query("""
                WITH tim AS (
                  SELECT tai_lieu_id FROM tim_tai_lieu(%s)
                )
                SELECT count(*)::int AS tong_so
                FROM tim
                JOIN tai_lieu t ON t.id = tim.tai_lieu_id
                WHERE (%s::varchar IS NULL OR t.loai_hinh = %s)
                  AND (%s::int IS NULL OR t.nam >= %s)
                  AND (%s::int IS NULL OR t.nam <= %s);
            """, [q, loai, loai, tu_nam, tu_nam, den_nam, den_nam])
            tong_so = count_res[0]['tong_so'] if count_res else 0
        else:
            tong_so = 0
    else:
        sql_duyet = """
            SELECT t.id, t.ky_hieu, t.loai_hinh, t.tieu_de, t.tac_gia, t.nxb, t.nam,
                   t.co_ban_mem, t.khong_co_tl, t.muc_truy_cap,
                   v.so_ban, v.so_ban_con,
                   NULL::real AS diem,
                   count(*) OVER()::int AS tong_so
            FROM tai_lieu t
            LEFT JOIN v_tinh_trang_tai_lieu v ON v.tai_lieu_id = t.id
            WHERE (%s::varchar IS NULL OR t.loai_hinh = %s)
              AND (%s::int IS NULL OR t.nam >= %s)
              AND (%s::int IS NULL OR t.nam <= %s)
            ORDER BY t.id ASC
            OFFSET %s LIMIT %s;
        """
        rows = db.query(sql_duyet, [loai, loai, tu_nam, tu_nam, den_nam, den_nam, vi_tri_offset, gioi_han])
        if rows:
            tong_so = rows[0]['tong_so']
        elif trang > 1:
            count_res = db.query("""
                SELECT count(*)::int AS tong_so
                FROM tai_lieu t
                WHERE (%s::varchar IS NULL OR t.loai_hinh = %s)
                  AND (%s::int IS NULL OR t.nam >= %s)
                  AND (%s::int IS NULL OR t.nam <= %s);
            """, [loai, loai, tu_nam, tu_nam, den_nam, den_nam])
            tong_so = count_res[0]['tong_so'] if count_res else 0
        else:
            tong_so = 0

    # Ghi log tìm kiếm khi có từ khóa và đang ở trang 1
    log_id = None
    if q and trang == 1:
        ma_phien = session.get('ma_phien')
        user = session.get('user')
        nguoi_dung_id = user.get('id') if user else None

        log_res = db.query("""
            INSERT INTO log_tim_kiem (tu_khoa, tu_khoa_chuan, so_ket_qua, nguoi_dung_id, ma_phien, du_lieu_mau)
            VALUES (%s, f_chuan_hoa(%s), %s, %s, %s, false)
            RETURNING id;
        """, [q, q, tong_so, nguoi_dung_id, ma_phien])
        if log_res:
            log_id = log_res[0]['id']

    # Loại bỏ trường tong_so khỏi từng dòng kết quả
    danh_sach = [{k: v for k, v in row.items() if k != 'tong_so'} for row in rows]

    return jsonify({
        'thanh_cong': True,
        'du_lieu': danh_sach,
        'tong_so': tong_so,
        'trang': trang,
        'gioi_han': gioi_han,
        'tong_trang': math.ceil(tong_so / gioi_han) if tong_so > 0 else 1,
        'log_id': log_id
    })

@tai_lieu_bp.route('/tim-kiem/<log_id>/chon', methods=['POST'])
@yeu_cau_vai_tro('*')
def chon_tai_lieu(log_id):
    """
    POST /api/tim-kiem/:logId/chon
    Cập nhật tư liệu người dùng đã nhấp vào xem từ kết quả tìm kiếm.
    Chỉ cho phép cập nhật khi log thuộc đúng ma_phien hiện tại.
    """
    # Kiểm tra log_id và tai_lieu_id hợp lệ
    try:
        parsed_log_id = int(log_id)
        data = request.get_json(silent=True) or {}
        raw_tl_id = data.get('tai_lieu_id')
        if raw_tl_id is None or isinstance(raw_tl_id, bool):
            raise ValueError()
        parsed_tl_id = int(raw_tl_id)
        if parsed_log_id <= 0 or parsed_tl_id <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({
            'thanh_cong': False,
            'error': 'Vui lòng cung cấp mã log hợp lệ và mã tư liệu được chọn.'
        }), 400

    ma_phien = session.get('ma_phien')

    # Kiểm tra log có tồn tại và thuộc phiên hiện tại không
    check_log = db.query(
        'SELECT id, ma_phien FROM log_tim_kiem WHERE id = %s',
        [parsed_log_id]
    )

    if not check_log:
        return jsonify({
            'thanh_cong': False,
            'error': 'Không tìm thấy log tìm kiếm tương ứng.'
        }), 404

    if check_log[0]['ma_phien'] != ma_phien:
        return jsonify({
            'thanh_cong': False,
            'error': 'Không thể cập nhật log của phiên làm việc khác.'
        }), 403

    # Kiểm tra tư liệu được chọn có tồn tại trong CSDL không
    check_tl = db.query('SELECT id FROM tai_lieu WHERE id = %s', [parsed_tl_id])
    if not check_tl:
        return jsonify({
            'thanh_cong': False,
            'error': 'Không tìm thấy tư liệu được chọn.'
        }), 404

    update_res = db.query(
        'UPDATE log_tim_kiem SET tai_lieu_chon_id = %s WHERE id = %s RETURNING id, tai_lieu_chon_id',
        [parsed_tl_id, parsed_log_id]
    )

    return jsonify({
        'thanh_cong': True,
        'message': 'Cập nhật tư liệu đã chọn thành công.',
        'log': update_res[0] if update_res else None
    })

@tai_lieu_bp.route('/tai-lieu/<id>', methods=['GET'])
@yeu_cau_vai_tro('*')
def chi_tiet_tai_lieu(id):
    """
    GET /api/tai-lieu/:id
    Chi tiết thông tin tư liệu kèm danh sách bản sao và tình trạng sẵn sàng
    """
    try:
        doc_id = int(id)
        if doc_id <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({
            'thanh_cong': False,
            'error': 'Mã tư liệu không hợp lệ.'
        }), 400

    tl_res = db.query("""
        SELECT t.*, v.so_ban, v.so_ban_con, mvd.ten AS ten_ma_van_de
        FROM tai_lieu t
        LEFT JOIN v_tinh_trang_tai_lieu v ON v.tai_lieu_id = t.id
        LEFT JOIN ma_van_de mvd ON mvd.ma = t.ma_van_de
        WHERE t.id = %s
    """, [doc_id])

    if not tl_res:
        return jsonify({
            'thanh_cong': False,
            'error': 'Không tìm thấy tư liệu yêu cầu.'
        }), 404

    bs_res = db.query("""
        SELECT id, ma_ban_sao, trang_thai
        FROM ban_sao
        WHERE tai_lieu_id = %s
        ORDER BY id ASC
    """, [doc_id])

    tai_lieu = tl_res[0]
    tai_lieu.pop('tsv', None)
    tai_lieu['ban_sao'] = bs_res

    return jsonify({
        'thanh_cong': True,
        'tai_lieu': tai_lieu
    })

@tai_lieu_bp.route('/ban-mem/<id>', methods=['GET'])
@yeu_cau_vai_tro('*')
def ban_mem(id):
    """
    GET /api/ban-mem/:id
    Xem hoặc tải tệp PDF bản mềm số hóa của tư liệu:
    - cong_khai: Ai cũng có thể xem
    - noi_bo: Phải đăng nhập tài khoản hợp lệ
    """
    try:
        doc_id = int(id)
        if doc_id <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({
            'thanh_cong': False,
            'error': 'Mã tư liệu không hợp lệ.'
        }), 400

    tl_res = db.query(
        'SELECT id, tieu_de, co_ban_mem, muc_truy_cap, duong_dan_ban_mem FROM tai_lieu WHERE id = %s',
        [doc_id]
    )

    if not tl_res:
        return jsonify({
            'thanh_cong': False,
            'error': 'Không tìm thấy tư liệu.'
        }), 404

    tl = tl_res[0]

    if not tl.get('co_ban_mem') or not tl.get('duong_dan_ban_mem'):
        return jsonify({
            'thanh_cong': False,
            'error': 'Tư liệu này hiện chưa có bản mềm số hóa.'
        }), 404

    # Nếu là tài liệu lưu hành nội bộ, bắt buộc phải đăng nhập
    if tl.get('muc_truy_cap') == 'noi_bo' and not session.get('user'):
        return jsonify({
            'thanh_cong': False,
            'error': 'Tư liệu lưu hành nội bộ. Vui lòng đăng nhập để truy cập tài liệu này.'
        }), 401

    # Chuẩn hóa và kiểm tra đường dẫn an toàn chống Path Traversal
    upload_base_dir = os.path.abspath(os.path.join(os.getcwd(), 'uploads'))
    rel_path = tl['duong_dan_ban_mem'].replace('\\', '/')
    if rel_path.startswith('uploads/'):
        rel_path = rel_path[len('uploads/'):]

    full_path = os.path.abspath(os.path.join(upload_base_dir, rel_path))

    # Tuyệt đối không cho phép truy xuất tệp nằm ngoài thư mục uploads/
    try:
        common = os.path.commonpath([upload_base_dir, full_path])
    except ValueError:
        return jsonify({'thanh_cong': False, 'error': 'Đường dẫn tệp không hợp lệ.'}), 403

    if common != upload_base_dir or full_path == upload_base_dir:
        return jsonify({
            'thanh_cong': False,
            'error': 'Đường dẫn tệp không hợp lệ.'
        }), 403

    if not os.path.isfile(full_path):
        return jsonify({
            'thanh_cong': False,
            'error': 'Tệp bản mềm không tìm thấy trên hệ thống lưu trữ.'
        }), 404

    return send_file(
        full_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"tai_lieu_{tl['id']}.pdf"
    )
