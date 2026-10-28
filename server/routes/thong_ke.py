"""
Blueprint thống kê dữ liệu phục vụ Dashboard dành cho thủ thư
Chỉ trả về số liệu tổng hợp, tuyệt đối không trả nguoi_dung_id hay ma_phien
"""
from flask import Blueprint, request, jsonify
import server.db as db
from server.auth import yeu_cau_vai_tro

thong_ke_bp = Blueprint('thong_ke', __name__)

@thong_ke_bp.route('/tong-quan', methods=['GET'])
@yeu_cau_vai_tro('thu_thu')
def tong_quan():
    """
    GET /api/thong-ke/tong-quan
    4 Thẻ KPI chính: Tổng lượt tìm, % tìm không có kết quả, số lượt mượn đang mở, số tư liệu đã số hóa
    """
    log_res = db.query("""
        SELECT 
          count(*)::int AS tong_luot_tim,
          coalesce(round(count(*) FILTER (WHERE so_ket_qua = 0) * 100.0 / NULLIF(count(*), 0), 2), 0)::real AS ti_le_khong_ket_qua
        FROM log_tim_kiem;
    """)

    muon_res = db.query("""
        SELECT count(*)::int AS luot_muon_dang_mo
        FROM luot_muon
        WHERE trang_thai IN ('cho_duyet', 'dang_muon');
    """)

    tl_res = db.query("""
        SELECT 
          count(*)::int AS tong_tai_lieu,
          count(*) FILTER (WHERE co_ban_mem = true)::int AS so_da_so_hoa
        FROM tai_lieu;
    """)

    log_data = log_res[0] if log_res else {'tong_luot_tim': 0, 'ti_le_khong_ket_qua': 0.0}
    muon_data = muon_res[0] if muon_res else {'luot_muon_dang_mo': 0}
    tl_data = tl_res[0] if tl_res else {'tong_tai_lieu': 0, 'so_da_so_hoa': 0}

    return jsonify({
        'thanh_cong': True,
        'tong_luot_tim': log_data['tong_luot_tim'],
        'ti_le_khong_ket_qua': log_data['ti_le_khong_ket_qua'],
        'luot_muon_dang_mo': muon_data['luot_muon_dang_mo'],
        'so_da_so_hoa': tl_data['so_da_so_hoa'],
        'tong_tai_lieu': tl_data['tong_tai_lieu']
    })

@thong_ke_bp.route('/tu-khoa', methods=['GET'])
@yeu_cau_vai_tro('thu_thu')
def tu_khoa():
    """
    GET /api/thong-ke/tu-khoa?limit=
    Danh sách từ khóa tìm kiếm nhiều nhất (phục vụ biểu đồ Word Cloud và Bar chart)
    """
    try:
        limit = int(request.args.get('limit', 50))
        if limit < 1:
            limit = 50
        if limit > 200:
            limit = 200
    except (ValueError, TypeError):
        limit = 50

    rows = db.query("""
        SELECT tu_khoa_chuan, hien_thi, so_lan, so_lan_0_kq
        FROM v_tu_khoa_top
        LIMIT %s
    """, [limit])

    return jsonify({
        'thanh_cong': True,
        'du_lieu': rows
    })

@thong_ke_bp.route('/theo-ngay', methods=['GET'])
@yeu_cau_vai_tro('thu_thu')
def theo_ngay():
    """
    GET /api/thong-ke/theo-ngay?so_ngay=
    Xu hướng lượt tìm kiếm theo ngày (bộ lọc 7, 30 hoặc 90 ngày)
    """
    try:
        so_ngay = int(request.args.get('so_ngay', 30))
        if so_ngay not in (7, 30, 90):
            so_ngay = 30
    except (ValueError, TypeError):
        so_ngay = 30

    rows = db.query("""
        SELECT ngay::text, so_luot, so_luot_0_kq
        FROM v_tim_theo_ngay
        WHERE ngay >= CURRENT_DATE - (%s * INTERVAL '1 day')
        ORDER BY ngay ASC
    """, [so_ngay])

    return jsonify({
        'thanh_cong': True,
        'so_ngay': so_ngay,
        'du_lieu': rows
    })

@thong_ke_bp.route('/khong-ket-qua', methods=['GET'])
@yeu_cau_vai_tro('thu_thu')
def khong_ket_qua():
    """
    GET /api/thong-ke/khong-ket-qua?limit=
    Danh sách từ khóa tìm kiếm nhiều nhưng 0 kết quả -> Gợi ý mua/bổ sung tư liệu
    """
    try:
        limit = int(request.args.get('limit', 20))
        if limit < 1:
            limit = 20
        if limit > 100:
            limit = 100
    except (ValueError, TypeError):
        limit = 20

    rows = db.query("""
        SELECT tu_khoa_chuan, hien_thi, so_lan, lan_cuoi
        FROM v_khong_ket_qua
        LIMIT %s
    """, [limit])

    return jsonify({
        'thanh_cong': True,
        'du_lieu': rows
    })

@thong_ke_bp.route('/nen-so-hoa', methods=['GET'])
@yeu_cau_vai_tro('thu_thu')
def nen_so_hoa():
    """
    GET /api/thong-ke/nen-so-hoa?limit=
    Bảng tư liệu đề xuất nên số hóa theo điểm quan tâm (diem = so_lan_chon + 2 * so_luot_muon)
    """
    try:
        limit = int(request.args.get('limit', 20))
        if limit < 1:
            limit = 20
        if limit > 100:
            limit = 100
    except (ValueError, TypeError):
        limit = 20

    rows = db.query("""
        SELECT tai_lieu_id, ky_hieu, tieu_de, tac_gia, loai_hinh, nam,
               so_lan_chon, so_luot_muon, diem
        FROM v_nen_so_hoa
        LIMIT %s
    """, [limit])

    return jsonify({
        'thanh_cong': True,
        'du_lieu': rows
    })
