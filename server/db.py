"""
Module kết nối CSDL PostgreSQL sử dụng psycopg2 ThreadedConnectionPool.
Đọc cấu hình từ biến môi trường DATABASE_URL qua python-dotenv.
"""
import os
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor

# Đảm bảo mã hóa UTF-8 cho kết nối PostgreSQL
os.environ['PGCLIENTENCODING'] = 'UTF8'

# Nạp biến môi trường từ .env
load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("Chưa cấu hình biến môi trường DATABASE_URL trong .env")

# Khởi tạo connection pool luồng an toàn (minconn=1, maxconn=20)
pool = ThreadedConnectionPool(
    minconn=1,
    maxconn=20,
    dsn=DATABASE_URL,
    client_encoding='UTF8'
)

def get_conn():
    """Lấy một kết nối từ pool."""
    return pool.getconn()

def put_conn(conn):
    """Trả kết nối về pool."""
    if conn:
        pool.putconn(conn)

def close_pool():
    """Đóng toàn bộ kết nối trong pool khi tắt máy chủ."""
    if pool:
        pool.closeall()

def query(sql, params=None):
    """
    Thực thi truy vấn SQL với tham số %s (RealDictCursor).
    Tự động commit và trả kết quả dưới dạng danh sách dict.
    Tương đương với db.query() trong bản Node/pg.
    """
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if cur.description is not None:
                rows = [dict(row) for row in cur.fetchall()]
            else:
                rows = []
        conn.commit()
        return rows
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)

@contextmanager
def transaction():
    """
    Context manager hỗ trợ transaction an toàn:
    Tự động COMMIT nếu thành công, ROLLBACK nếu có ngoại lệ,
    và luôn trả kết nối về pool trong finally.
    
    Sử dụng:
        with transaction() as cur:
            cur.execute(...)
            rows = cur.fetchall()
    """
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)
