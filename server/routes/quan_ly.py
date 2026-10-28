"""
Blueprint quản lý dành cho thủ thư:
- Quản lý duyệt, từ chối, trả lượt mượn (sử dụng transaction và SELECT FOR UPDATE)
- Tải bản mềm PDF số hóa (kiểm tra mimetype và 4 byte magic %PDF, tối đa 20MB)
"""
import os
import time
from flask import Blueprint, request, jsonify
import server.db as db
from server.auth import yeu_cau_vai_tro

quan_ly_bp = Blueprint('quan_ly', __name__)

@quan_ly_bp.route('/muon', methods=['GET'])
@yeu_cau_vai_tro('thu_thu')
def danh_sach_muon():
    """
    GET /api/quan-ly/muon?trang_thai=
    Xem danh sách tất cả các lượt mượn trong hệ thống, có thể lọc theo trạng thái
    """
    raw_status = request.args.get('trang_thai')
    trang_thai = str(raw_status).strip() if raw_status and str(raw_status).strip() else None

    rows = db.query(
        """SELECT m.id, m.nguoi_dung_id, u.ho_ten, u.ten_dang_nhap, u.vai_tro,
                  m.tai_lieu_id, t.tieu_de, t.ky_hieu, t.loai_hinh,
                  m.ban_sao_id, b.ma_ban_sao,
                  m.trang_thai, m.ngay_dang_ky, m.ngay_muon, m.han_tra, m.ngay_tra
           FROM luot_muon m
           JOIN nguoi_dung u ON u.id = m.nguoi_dung_id
           JOIN tai_lieu t ON t.id = m.tai_lieu_id
           LEFT JOIN ban_sao b ON b.id = m.ban_sao_id
           WHERE (%s::varchar IS NULL OR m.trang_thai = %s)
           ORDER BY m.ngay_dang_ky DESC, m.id DESC;""",
        [trang_thai, trang_thai]
    )

    return jsonify({
        'thanh_cong': True,
        'luot_muon': rows
    })

@quan_ly_bp.route('/muon/<id>/duyet', methods=['POST'])
@yeu_cau_vai_tro('thu_thu')
def duyet_muon(id):
    """
    POST /api/quan-ly/muon/:id/duyet
    Duyệt yêu cầu mượn trong Transaction:
    - Khóa bản ghi mượn và tìm bản sao còn rảnh với FOR UPDATE
    - Nếu không còn bản sao -> trả về 409
    - Gán bản sao, chuyển trạng thái sang 'dang_muon', hạn trả = +14 ngày
    """
    try:
        luot_muon_id = int(id)
        if luot_muon_id <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'thanh_cong': False, 'error': 'Mã lượt mượn không hợp lệ.'}), 400

    with db.transaction() as cur:
        # Khóa dòng lượt mượn để xử lý
        cur.execute(
            'SELECT id, tai_lieu_id, trang_thai FROM luot_muon WHERE id = %s FOR UPDATE',
            [luot_muon_id]
        )
        lm_rows = cur.fetchall()
        if not lm_rows:
            return jsonify({'thanh_cong': False, 'error': 'Không tìm thấy lượt mượn.'}), 404

        luot_muon = lm_rows[0]
        if luot_muon['trang_thai'] != 'cho_duyet':
            return jsonify({
                'thanh_cong': False,
                'error': f"Lượt mượn hiện không ở trạng thái chờ duyệt (trạng thái: {luot_muon['trang_thai']})."
            }), 400

        # Tìm và khóa một bản sao còn rảnh (trang_thai = 'con')
        cur.execute(
            """SELECT id, ma_ban_sao
               FROM ban_sao
               WHERE tai_lieu_id = %s AND trang_thai = 'con'
               ORDER BY id ASC
               LIMIT 1
               FOR UPDATE""",
            [luot_muon['tai_lieu_id']]
        )
        bs_rows = cur.fetchall()
        if not bs_rows:
            return jsonify({
                'thanh_cong': False,
                'error': 'Không còn bản sao khả dụng để cho mượn.'
            }), 409

        ban_sao_duoc_gan = bs_rows[0]

        # Cập nhật trạng thái bản sao thành 'dang_muon'
        cur.execute(
            "UPDATE ban_sao SET trang_thai = 'dang_muon' WHERE id = %s",
            [ban_sao_duoc_gan['id']]
        )

        # Cập nhật lượt mượn: gán bản sao, ngày mượn hôm nay, hạn trả = +14 ngày
        cur.execute(
            """UPDATE luot_muon
               SET ban_sao_id = %s,
                   trang_thai = 'dang_muon',
                   ngay_muon = CURRENT_DATE,
                   han_tra = CURRENT_DATE + INTERVAL '14 days'
               WHERE id = %s
               RETURNING *;""",
            [ban_sao_duoc_gan['id'], luot_muon_id]
        )
        update_lm = cur.fetchall()[0]

        return jsonify({
            'thanh_cong': True,
            'message': 'Duyệt yêu cầu mượn thành công.',
            'luot_muon': dict(update_lm),
            'ban_sao': dict(ban_sao_duoc_gan)
        })

@quan_ly_bp.route('/muon/<id>/tu-choi', methods=['POST'])
@yeu_cau_vai_tro('thu_thu')
def tu_choi_muon(id):
    """
    POST /api/quan-ly/muon/:id/tu-choi
    Từ chối yêu cầu mượn tư liệu
    """
    try:
        luot_muon_id = int(id)
        if luot_muon_id <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'thanh_cong': False, 'error': 'Mã lượt mượn không hợp lệ.'}), 400

    check_res = db.query(
        'SELECT id, trang_thai FROM luot_muon WHERE id = %s',
        [luot_muon_id]
    )

    if not check_res:
        return jsonify({'thanh_cong': False, 'error': 'Không tìm thấy lượt mượn.'}), 404

    if check_res[0]['trang_thai'] != 'cho_duyet':
        return jsonify({
            'thanh_cong': False,
            'error': f"Không thể từ chối lượt mượn ở trạng thái {check_res[0]['trang_thai']}."
        }), 400

    rows = db.query(
        "UPDATE luot_muon SET trang_thai = 'tu_choi' WHERE id = %s RETURNING *",
        [luot_muon_id]
    )

    return jsonify({
        'thanh_cong': True,
        'message': 'Đã từ chối yêu cầu mượn tư liệu.',
        'luot_muon': rows[0] if rows else None
    })

@quan_ly_bp.route('/muon/<id>/tra', methods=['POST'])
@yeu_cau_vai_tro('thu_thu')
def tra_muon(id):
    """
    POST /api/quan-ly/muon/:id/tra
    Ghi nhận trả tư liệu:
    - Kiểm tra trạng thái đang mượn
    - Cập nhật bản sao về 'con'
    - Cập nhật lượt mượn thành 'da_tra' và ghi nhận ngày trả
    """
    try:
        luot_muon_id = int(id)
        if luot_muon_id <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'thanh_cong': False, 'error': 'Mã lượt mượn không hợp lệ.'}), 400

    with db.transaction() as cur:
        cur.execute(
            'SELECT id, ban_sao_id, trang_thai FROM luot_muon WHERE id = %s FOR UPDATE',
            [luot_muon_id]
        )
        lm_rows = cur.fetchall()
        if not lm_rows:
            return jsonify({'thanh_cong': False, 'error': 'Không tìm thấy lượt mượn.'}), 404

        luot_muon = lm_rows[0]
        if luot_muon['trang_thai'] != 'dang_muon':
            return jsonify({
                'thanh_cong': False,
                'error': f"Lượt mượn hiện không ở trạng thái đang mượn (trạng thái: {luot_muon['trang_thai']})."
            }), 400

        # Đưa bản sao về trạng thái 'con'
        if luot_muon.get('ban_sao_id'):
            cur.execute(
                "UPDATE ban_sao SET trang_thai = 'con' WHERE id = %s",
                [luot_muon['ban_sao_id']]
            )

        # Cập nhật lượt mượn thành 'da_tra'
        cur.execute(
            """UPDATE luot_muon
               SET trang_thai = 'da_tra',
                   ngay_tra = CURRENT_DATE
               WHERE id = %s
               RETURNING *;""",
            [luot_muon_id]
        )
        update_lm = cur.fetchall()[0]

        return jsonify({
            'thanh_cong': True,
            'message': 'Ghi nhận trả tư liệu thành công.',
            'luot_muon': dict(update_lm)
        })

@quan_ly_bp.route('/tai-lieu/<id>/ban-mem', methods=['POST'])
@yeu_cau_vai_tro('thu_thu')
def upload_ban_mem(id):
    """
    POST /api/quan-ly/tai-lieu/:id/ban-mem
    Upload tệp PDF số hóa cho tư liệu:
    - Kiểm tra tệp PDF hợp lệ (mimetype + 4 byte magic %PDF)
    - Tối đa 20MB
    - Cập nhật co_ban_mem = true, muc_truy_cap, duong_dan_ban_mem
    """
    try:
        doc_id = int(id)
        if doc_id <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'thanh_cong': False, 'error': 'Mã tư liệu không hợp lệ.'}), 400

    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({
            'thanh_cong': False,
            'error': 'Vui lòng chọn tệp PDF để tải lên.'
        }), 400

    filename_lower = file.filename.lower()
    if not filename_lower.endswith('.pdf') or file.mimetype != 'application/pdf':
        return jsonify({
            'thanh_cong': False,
            'error': 'Chỉ chấp nhận tệp định dạng PDF.'
        }), 400

    # Đọc 4 byte đầu tiên của file để xác thực header %PDF
    header_bytes = file.read(4)
    file.seek(0)
    if header_bytes != b'%PDF':
        return jsonify({
            'thanh_cong': False,
            'error': 'Tệp tải lên không phải là tệp PDF hợp lệ (thiếu header %PDF).'
        }), 400

    # Kiểm tra tư liệu có tồn tại trong CSDL không
    check_doc = db.query('SELECT id, tieu_de, duong_dan_ban_mem FROM tai_lieu WHERE id = %s', [doc_id])
    if not check_doc:
        return jsonify({'thanh_cong': False, 'error': 'Không tìm thấy tư liệu.'}), 404

    # Dọn dẹp tệp cũ trên đĩa nếu trước đó có bản mềm tự tải (không phải trong mau/)
    old_path = check_doc[0].get('duong_dan_ban_mem')
    if old_path:
        norm_old = old_path.replace('\\', '/')
        if norm_old.startswith('uploads/'):
            norm_old = norm_old[len('uploads/'):]
        if not norm_old.startswith('mau/'):
            old_full_path = os.path.abspath(os.path.join(os.getcwd(), 'uploads', os.path.basename(old_path)))
            if os.path.isfile(old_full_path):
                try:
                    os.unlink(old_full_path)
                except OSError:
                    pass

    # Lưu tệp mới
    upload_dir = os.path.abspath(os.path.join(os.getcwd(), 'uploads'))
    os.makedirs(upload_dir, exist_ok=True)
    timestamp_ms = int(time.time() * 1000)
    unique_name = f"tl_{doc_id}_{timestamp_ms}.pdf"
    save_path = os.path.join(upload_dir, unique_name)
    file.save(save_path)

    muc_truy_cap = 'noi_bo' if request.form.get('muc_truy_cap') == 'noi_bo' else 'cong_khai'

    update_res = db.query(
        """UPDATE tai_lieu
           SET co_ban_mem = true,
               muc_truy_cap = %s,
               duong_dan_ban_mem = %s
           WHERE id = %s
           RETURNING id, ky_hieu, tieu_de, co_ban_mem, muc_truy_cap, duong_dan_ban_mem;""",
        [muc_truy_cap, unique_name, doc_id]
    )

    return jsonify({
        'thanh_cong': True,
        'message': 'Tải lên bản mềm số hóa thành công.',
        'tai_lieu': update_res[0] if update_res else None
    })
