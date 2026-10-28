"""
Khởi tạo ứng dụng Python Flask cho Web thư viện chuyển đổi số
Cung cấp API backend và phục vụ giao diện tĩnh từ thư mục public/
"""
import sys
import os
import datetime
from decimal import Decimal

# Đảm bảo thư mục gốc dự án luôn nằm trong sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask.json.provider import DefaultJSONProvider
from werkzeug.exceptions import RequestEntityTooLarge

# Nạp cấu hình từ biến môi trường
load_dotenv()

# Tạo các thư mục lưu trữ nếu chưa có
public_dir = os.path.abspath(os.path.join(root_dir, 'public'))
os.makedirs(public_dir, exist_ok=True)

upload_dir = os.path.abspath(os.path.join(root_dir, 'uploads'))
os.makedirs(upload_dir, exist_ok=True)

class CustomJSONProvider(DefaultJSONProvider):
    """
    JSON Provider tùy chỉnh để serialize datetime sang chuẩn ISO 8601
    và Decimal sang float/int chuẩn JSON.
    """
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

app = Flask(__name__, static_folder=None)
app.json = CustomJSONProvider(app)

# Cấu hình Secret key & Giới hạn tệp tải lên
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'thu-vien-chuyen-doi-so-secret-key-2026')
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_NAME'] = 'session'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=1)

# Xử lý ngoại lệ vượt quá dung lượng tệp tải lên (20MB)
@app.errorhandler(RequestEntityTooLarge)
def handle_file_size_exceeded(e):
    return jsonify({
        'thanh_cong': False,
        'error': 'Dung lượng tệp vượt quá giới hạn cho phép (20MB).'
    }), 400

# Đăng ký các Blueprint API
from server.routes.auth import auth_bp
from server.routes.tai_lieu import tai_lieu_bp
from server.routes.muon import muon_bp
from server.routes.quan_ly import quan_ly_bp
from server.routes.thong_ke import thong_ke_bp

app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(tai_lieu_bp, url_prefix='/api')
app.register_blueprint(muon_bp, url_prefix='/api/muon')
app.register_blueprint(quan_ly_bp, url_prefix='/api/quan-ly')
app.register_blueprint(thong_ke_bp, url_prefix='/api/thong-ke')

# Bắt lỗi 404 cho các endpoint /api không tồn tại
@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith('/api'):
        return jsonify({
            'thanh_cong': False,
            'error': 'Endpoint API không tồn tại.'
        }), 404
    return jsonify({
        'thanh_cong': False,
        'error': 'Tài nguyên không tồn tại.'
    }), 404

# Bắt lỗi 500 trả về JSON
@app.errorhandler(500)
def handle_500(e):
    return jsonify({
        'thanh_cong': False,
        'error': 'Lỗi nội bộ máy chủ.'
    }), 500

# Tuyến gốc API /api hoặc /api/ trả về JSON 404
@app.route('/api', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/api/', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def api_root():
    return jsonify({
        'thanh_cong': False,
        'error': 'Endpoint API không tồn tại.'
    }), 404

# Phục vụ file tĩnh từ public/
@app.route('/', defaults={'path': 'index.html'}, methods=['GET'])
@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    if path.startswith('api'):
        return jsonify({
            'thanh_cong': False,
            'error': 'Endpoint API không tồn tại.'
        }), 404

    target_file = os.path.join(public_dir, path)
    if os.path.isfile(target_file):
        return send_from_directory(public_dir, path)

    if os.path.isdir(target_file):
        idx = os.path.join(target_file, 'index.html')
        if os.path.isfile(idx):
            return send_from_directory(public_dir, os.path.join(path, 'index.html'))

    return jsonify({
        'thanh_cong': False,
        'error': 'Tài nguyên không tồn tại.'
    }), 404

if __name__ == '__main__':
    if sys.platform.startswith('win'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass
    port = int(os.environ.get('PORT', 3000))
    print(f"Máy chủ Web Thư viện Python Flask đang chạy tại cổng http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
