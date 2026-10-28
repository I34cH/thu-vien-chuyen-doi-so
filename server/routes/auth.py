"""
Blueprint xác thực tài khoản: Đăng nhập, Đăng xuất, Thông tin tài khoản hiện tại
"""
from flask import Blueprint, request, session, jsonify
import bcrypt
import server.db as db
from server.auth import yeu_cau_vai_tro

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/dang-nhap', methods=['POST'])
@yeu_cau_vai_tro('*')
def dang_nhap():
    """
    POST /api/dang-nhap
    Đăng nhập hệ thống bằng tên đăng nhập và mật khẩu
    """
    data = request.get_json(silent=True) or {}
    ten_dang_nhap = data.get('ten_dang_nhap')
    mat_khau = data.get('mat_khau')

    if (
        not isinstance(ten_dang_nhap, str) or
        not isinstance(mat_khau, str) or
        not ten_dang_nhap.strip() or
        not mat_khau
    ):
        return jsonify({
            'thanh_cong': False,
            'error': 'Vui lòng cung cấp đầy đủ tên đăng nhập và mật khẩu.'
        }), 400

    rows = db.query(
        'SELECT id, ten_dang_nhap, mat_khau_hash, ho_ten, vai_tro FROM nguoi_dung WHERE ten_dang_nhap = %s',
        [ten_dang_nhap.strip()]
    )

    if not rows:
        return jsonify({
            'thanh_cong': False,
            'error': 'Tên đăng nhập hoặc mật khẩu không chính xác.'
        }), 401

    nguoi_dung = rows[0]
    mat_khau_hash = nguoi_dung['mat_khau_hash']
    if isinstance(mat_khau_hash, str):
        mat_khau_hash_bytes = mat_khau_hash.encode('utf-8')
    else:
        mat_khau_hash_bytes = bytes(mat_khau_hash)

    khop_mat_khau = bcrypt.checkpw(mat_khau.encode('utf-8'), mat_khau_hash_bytes)

    if not khop_mat_khau:
        return jsonify({
            'thanh_cong': False,
            'error': 'Tên đăng nhập hoặc mật khẩu không chính xác.'
        }), 401

    # Lưu thông tin người dùng vào session
    session['user'] = {
        'id': nguoi_dung['id'],
        'ten_dang_nhap': nguoi_dung['ten_dang_nhap'],
        'ho_ten': nguoi_dung['ho_ten'],
        'vai_tro': nguoi_dung['vai_tro']
    }
    session['khoi_tao'] = True
    session.modified = True

    return jsonify({
        'thanh_cong': True,
        'message': 'Đăng nhập thành công.',
        'user': session['user']
    })

@auth_bp.route('/dang-xuat', methods=['POST'])
@yeu_cau_vai_tro('*')
def dang_xuat():
    """
    POST /api/dang-xuat
    Đăng xuất tài khoản và hủy phiên làm việc
    """
    session.clear()
    resp = jsonify({
        'thanh_cong': True,
        'message': 'Đăng xuất thành công.'
    })
    resp.delete_cookie('session')
    return resp

@auth_bp.route('/toi', methods=['GET'])
@yeu_cau_vai_tro('*')
def toi():
    """
    GET /api/toi
    Lấy thông tin tài khoản đang đăng nhập trong phiên
    """
    user = session.get('user')
    if user:
        vai_tro = user.get('vai_tro')
        if vai_tro in ('sinh_vien', 'giang_vien'):
            nhom_vai_tro = 'nguoi_dung'
        elif vai_tro in ('thu_thu', 'admin'):
            nhom_vai_tro = 'thu_thu'
        else:
            nhom_vai_tro = 'khach'

        return jsonify({
            'dang_nhap': True,
            'user': user,
            'vai_tro': vai_tro,
            'nhom_vai_tro': nhom_vai_tro
        })

    return jsonify({
        'dang_nhap': False,
        'user': None,
        'vai_tro': 'khach',
        'nhom_vai_tro': 'khach'
    })
