"""
Module middleware / decorator phân quyền và xác thực người dùng.
- '*' : Ai cũng truy cập được (kể cả khách vãng lai chưa đăng nhập)
- 'nguoi_dung' : Dành cho sinh_vien và giang_vien
- 'thu_thu' : Dành cho thu_thu và admin
Trả về 401 nếu chưa đăng nhập, 403 nếu sai vai trò.
"""
from functools import wraps
import uuid
from flask import session, jsonify

def yeu_cau_vai_tro(*vai_tros_cho_phep):
    """
    Decorator kiểm tra vai trò người dùng trong phiên làm việc.
    Luôn đảm bảo session được khởi tạo ma_phien và modified = True để Flask phát cookie.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Khởi tạo ma_phien nếu chưa có, để mỗi khách truy cập đều có phiên làm việc riêng
            if 'ma_phien' not in session:
                session['ma_phien'] = str(uuid.uuid4())
                session['khoi_tao'] = True
            session.modified = True

            # Nếu route cho phép '*', mọi đối tượng đều được phép truy cập
            if '*' in vai_tros_cho_phep:
                return fn(*args, **kwargs)

            # Kiểm tra trạng thái đăng nhập
            user = session.get('user')
            if not user:
                return jsonify({
                    'thanh_cong': False,
                    'error': 'Chưa đăng nhập. Vui lòng đăng nhập để tiếp tục.'
                }), 401

            vai_tro = user.get('vai_tro')

            # Kiểm tra tính hợp lệ của vai trò
            hop_le = False
            for vt in vai_tros_cho_phep:
                if vt == vai_tro:
                    hop_le = True
                    break
                if vt == 'nguoi_dung' and vai_tro in ('sinh_vien', 'giang_vien'):
                    hop_le = True
                    break
                if vt == 'thu_thu' and vai_tro in ('thu_thu', 'admin'):
                    hop_le = True
                    break

            if not hop_le:
                return jsonify({
                    'thanh_cong': False,
                    'error': 'Không có quyền truy cập.'
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator
