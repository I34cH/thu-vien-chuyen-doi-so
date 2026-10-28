"""
Blueprint quản lý việc đăng ký mượn và xem lịch sử mượn của người dùng (sinh viên, giảng viên)
"""
from flask import Blueprint, request, session, jsonify
import server.db as db
from server.auth import yeu_cau_vai_tro

muon_bp = Blueprint('muon', __name__)

@muon_bp.route('', methods=['POST'])
@muon_bp.route('/', methods=['POST'])
@yeu_cau_vai_tro('nguoi_dung')
def dang_ky_muon():
    """
    POST /api/muon
    Đăng ký mượn tư liệu (tạo lượt mượn ở trạng thái cho_duyet)
    """
    data = request.get_json(silent=True) or {}
    raw_id = data.get('tai_lieu_id')

    if raw_id is None or isinstance(raw_id, bool):
        return jsonify({
            'thanh_cong': False,
            'error': 'Vui lòng cung cấp mã tư liệu hợp lệ cần mượn.'
        }), 400

    try:
        doc_id = int(raw_id)
        if doc_id <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({
            'thanh_cong': False,
            'error': 'Vui lòng cung cấp mã tư liệu hợp lệ cần mượn.'
        }), 400

    # Kiểm tra tính hợp lệ của tư liệu và tình trạng tồn tại bản cứng
    tl_res = db.query(
        'SELECT id, tieu_de, khong_co_tl FROM tai_lieu WHERE id = %s',
        [doc_id]
    )

    if not tl_res:
        return jsonify({
            'thanh_cong': False,
            'error': 'Không tìm thấy tư liệu.'
        }), 404

    tl = tl_res[0]
    if tl.get('khong_co_tl'):
        return jsonify({
            'thanh_cong': False,
            'error': 'Tư liệu này hiện không có bản cứng tại thư viện để mượn.'
        }), 400

    nguoi_dung_id = session['user']['id']

    # Kiểm tra xem người dùng đã có yêu cầu mượn chưa hoàn tất cho tư liệu này chưa
    active_check = db.query(
        """SELECT id, trang_thai FROM luot_muon
           WHERE nguoi_dung_id = %s AND tai_lieu_id = %s AND trang_thai IN ('cho_duyet', 'dang_muon')""",
        [nguoi_dung_id, doc_id]
    )

    if active_check:
        tt = 'đang chờ duyệt' if active_check[0]['trang_thai'] == 'cho_duyet' else 'đang mượn'
        return jsonify({
            'thanh_cong': False,
            'error': f'Bạn đã có lượt mượn {tt} cho tư liệu này.'
        }), 400

    # Tạo lượt mượn mới ở trạng thái 'cho_duyet'
    insert_res = db.query(
        """INSERT INTO luot_muon (nguoi_dung_id, tai_lieu_id, ban_sao_id, trang_thai, ngay_dang_ky, du_lieu_mau)
           VALUES (%s, %s, NULL, 'cho_duyet', now(), false)
           RETURNING id, nguoi_dung_id, tai_lieu_id, ban_sao_id, trang_thai, ngay_dang_ky;""",
        [nguoi_dung_id, doc_id]
    )

    return jsonify({
        'thanh_cong': True,
        'message': 'Đăng ký mượn tư liệu thành công. Vui lòng chờ thủ thư xét duyệt.',
        'luot_muon': insert_res[0] if insert_res else None
    }), 201

@muon_bp.route('/cua-toi', methods=['GET'])
@yeu_cau_vai_tro('nguoi_dung')
def muon_cua_toi():
    """
    GET /api/muon/cua-toi
    Lấy danh sách các lượt mượn của tài khoản hiện tại
    """
    nguoi_dung_id = session['user']['id']

    rows = db.query(
        """SELECT m.id, m.tai_lieu_id, t.tieu_de, t.ky_hieu, t.loai_hinh,
                  t.co_ban_mem, t.muc_truy_cap,
                  m.ban_sao_id, b.ma_ban_sao,
                  m.trang_thai, m.ngay_dang_ky, m.ngay_muon, m.han_tra, m.ngay_tra
           FROM luot_muon m
           JOIN tai_lieu t ON t.id = m.tai_lieu_id
           LEFT JOIN ban_sao b ON b.id = m.ban_sao_id
           WHERE m.nguoi_dung_id = %s
           ORDER BY m.ngay_dang_ky DESC, m.id DESC;""",
        [nguoi_dung_id]
    )

    return jsonify({
        'thanh_cong': True,
        'luot_muon': rows
    })
