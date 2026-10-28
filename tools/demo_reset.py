"""
Công cụ đặt lại toàn bộ môi trường Demo (Milestone M6):
1. Khởi tạo lại schema + views CSDL (db/schema.sql + db/views.sql)
2. Dọn các tệp bản mềm tải lên ngoài thư mục mẫu (uploads/mau/)
3. Nạp lại dữ liệu thật từ Excel (scripts/etl_import.py)
4. Sinh lại dữ liệu mô phỏng với seed cố định 42 (scripts/seed_demo.py)
5. In bảng tóm tắt trạng thái hệ thống sau khi đặt lại

Chạy: python tools/demo_reset.py   (hoặc npm run demo:reset)
"""
import os
import sys
import time
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

GOC = Path(__file__).resolve().parent.parent
if str(GOC) not in sys.path:
    sys.path.insert(0, str(GOC))

load_dotenv(GOC / ".env")
os.environ["PGCLIENTENCODING"] = "UTF8"


def chay_schema_va_views(db_url: str):
    """Thực thi db/schema.sql và db/views.sql qua psycopg2."""
    schema_path = GOC / "db" / "schema.sql"
    views_path = GOC / "db" / "views.sql"

    schema_lines = [
        line for line in schema_path.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith(r"\ir ")
    ]
    schema_sql = "\n".join(schema_lines)
    views_sql = views_path.read_text(encoding="utf-8")

    with psycopg2.connect(db_url) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            cur.execute(views_sql)


def don_tep_upload():
    """Xóa các tệp PDF tải lên trong quá trình thử nghiệm, giữ nguyên uploads/mau/."""
    upload_dir = GOC / "uploads"
    if not upload_dir.exists():
        return 0
    da_xoa = 0
    for f in upload_dir.iterdir():
        if f.is_file() and f.suffix.lower() == ".pdf":
            try:
                f.unlink()
                da_xoa += 1
            except OSError:
                pass
    return da_xoa


def in_tom_tat(db_url: str, thoi_gian_chay: float):
    """Truy vấn và in bảng tóm tắt số liệu sau khi reset."""
    with psycopg2.connect(db_url) as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT
              (SELECT count(*) FROM tai_lieu WHERE co_ban_mem = true) AS so_da_so_hoa,
              (SELECT count(*) FROM tai_lieu WHERE khong_co_tl = true) AS so_khong_co_tl,
              (SELECT count(*) FROM luot_muon WHERE trang_thai IN ('cho_duyet', 'dang_muon')) AS muon_dang_mo,
              (SELECT count(*) FROM log_tim_kiem WHERE so_ket_qua = 0) AS log_0_kq
        """)
        so_da_so_hoa, so_khong_co_tl, muon_dang_mo, log_0_kq = cur.fetchone()

    print("\n" + "=" * 64)
    print("HOÀN TẤT ĐẶT LẠI MÔI TRƯỜNG DEMO (DEMO RESET)")
    print("=" * 64)
    print(f"- Tư liệu đã số hóa sẵn (bản mềm mẫu) : {so_da_so_hoa}")
    print(f"- Tư liệu không có bản cứng (Ko có TL): {so_khong_co_tl}")
    print(f"- Lượt mượn đang mở (chờ/đang mượn)   : {muon_dang_mo}")
    print(f"- Lượt tìm kiếm 0 kết quả             : {log_0_kq}")
    print(f"- Tài khoản demo: thuthu/thuthu123 | sv01/sv123 | gv01/gv123")
    print(f"- Tổng thời gian thực thi             : {thoi_gian_chay:.2f}s")
    print("=" * 64)


def main():
    t0 = time.time()
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("Thiếu biến môi trường DATABASE_URL trong .env")

    print("[1/4] Khởi tạo lại schema và views (db/schema.sql + db/views.sql)...")
    chay_schema_va_views(db_url)
    da_xoa = don_tep_upload()
    if da_xoa:
        print(f"      Đã dọn {da_xoa} tệp PDF tải lên cũ trong uploads/.")

    print("[2/4] Nạp dữ liệu thật từ Excel (scripts/etl_import.py)...")
    from scripts import etl_import
    etl_import.main()

    print("[3/4] Sinh dữ liệu mô phỏng với seed 42 (scripts/seed_demo.py)...")
    from scripts import seed_demo
    seed_demo.main()

    print("[4/4] Kiểm tra và tổng hợp kết quả...")
    in_tom_tat(db_url, time.time() - t0)


if __name__ == "__main__":
    main()
