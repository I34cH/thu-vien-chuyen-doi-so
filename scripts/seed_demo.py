"""
Sinh DỮ LIỆU MẪU cho demo (cờ du_lieu_mau = true) theo AGENTS.md mục 6:
bản sao, người dùng, ~8.000 log tìm kiếm (Zipf s≈1.1, 90 ngày), ~400 lượt mượn, một số tư liệu đã số hóa.
Seed cố định 42 -> chạy lại cho cùng số dòng.
Chạy: python scripts/seed_demo.py   (sau db/schema.sql + scripts/etl_import.py)
"""
import os
import random
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timedelta, time
from pathlib import Path

import bcrypt
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from faker import Faker

sys.stdout.reconfigure(encoding="utf-8")
GOC = Path(__file__).resolve().parent.parent
load_dotenv(GOC / ".env")

SEED = 42
SO_LOG = 8000
SO_NGAY = 90
SO_LUOT_MUON = 400
ZIPF_S = 1.1
SO_TU_KHOA_THAT = 220

# Từ khóa không có tư liệu tương ứng (lọc lại bằng CSDL, giữ 30 cái thực sự ra 0 kết quả)
UNG_VIEN_KHONG_CO = [
    "học máy", "python", "trí tuệ nhân tạo", "blockchain", "dữ liệu lớn", "điện toán đám mây",
    "an ninh mạng", "machine learning", "deep learning", "chatgpt", "java", "lập trình web",
    "marketing số", "thương mại điện tử", "kinh tế lượng", "iot", "big data", "khoa học dữ liệu",
    "xử lý ảnh", "mạng nơ ron", "reactjs", "sql server", "excel nâng cao", "ielts", "toeic",
    "kế toán doanh nghiệp", "logistics", "chứng khoán", "metaverse", "thị giác máy tính",
    "điện toán lượng tử", "kotlin", "power bi", "tableau", "data mining", "robot",
    "năng lượng tái tạo", "biến đổi khí hậu", "fintech", "học sâu", "ngôn ngữ lập trình",
]

TU_DUNG = set("""và của các những cho với tại trong về một số là ở từ đến theo đối nhằm qua trên
việc này đó khi được có bị do để nên thì mà như sau trước giữa hiện nay năm giai đoạn tìm hiểu bước đầu
góp phần vấn đề thực trạng giải pháp nâng cao hoàn thiện nghiên cứu khảo sát một số""".split())


def bo_dau(s: str) -> str:
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def go_sai(s: str, rd: random.Random) -> str:
    """Tạo lỗi gõ nhẹ: xóa / đổi chỗ / lặp một ký tự."""
    vi_tri = [i for i, c in enumerate(s) if c.isalpha()]
    if len(vi_tri) < 4:
        return s
    i = rd.choice(vi_tri[1:-1])
    kieu = rd.choice(["xoa", "doi", "lap"])
    if kieu == "xoa":
        return s[:i] + s[i + 1:]
    if kieu == "doi" and i + 1 < len(s):
        return s[:i] + s[i + 1] + s[i] + s[i + 2:]
    return s[:i] + s[i] + s[i:]


KHONG_DAU_CUM = {
    "liệu", "trữ", "tác", "tâm", "phòng", "bản", "chính", "dụng", "nước",
    "viên", "sơ", "thống", "động", "lý", "tập", "gia", "nội", "nam", "học",
    "thư", "thác", "hội", "bộ", "nghệ", "hóa", "trị", "phố", "chức", "kiện",
    "nin", "phần", "minh", "chí", "cổ", "viện", "ty", "ương", "ninh", "mạng",
    "tộc", "huy",
}
KHONG_CUOI_CUM = {
    "lưu", "tài", "công", "trung", "văn", "quản", "tổ", "hoạt", "xây",
    "hành", "cơ", "quốc", "sinh", "hệ", "hồ", "nghiên", "khảo", "việt", "hà",
    "toàn", "cổ", "đại", "xã", "lê", "chí", "thị", "nhân", "cách", "chiến",
    "kháng", "khai", "giá", "khoa", "lịch", "nhà", "thông",
}


def trich_cum_tu(tieu_de_list):
    """Lấy cụm 2–3 từ phổ biến trong tiêu đề thật (bỏ từ đơn và mảnh cắt lệch âm tiết)."""
    df = Counter()
    for td in tieu_de_list:
        tu = re.findall(r"[^\W\d_]+", td.lower())
        cum = set()
        for n in (2, 3):
            for i in range(len(tu) - n + 1):
                c = tu[i:i + n]
                if c[0] in TU_DUNG or c[-1] in TU_DUNG:
                    continue
                if c[0] in KHONG_DAU_CUM or c[-1] in KHONG_CUOI_CUM:
                    continue
                if n == 3 and c[2] == "sử" and c[1] != "lịch":
                    continue
                if any(len(w) < 2 for w in c) or len(set(c)) < n:
                    continue
                cum.add(" ".join(c))
        df.update(cum)
    # ưu tiên cụm 2–3 từ: nhân điểm theo độ dài
    diem = {c: f * (1.6 if c.count(" ") == 1 else 1.9)
            for c, f in df.items() if f >= 4}
    return [c for c, _ in sorted(diem.items(), key=lambda x: (-x[1], x[0]))]



def tao_pdf_mau(duong_dan: Path):
    """Ghi một file PDF 1 trang tối giản làm bản mềm mẫu."""
    noi_dung = b"BT /F1 18 Tf 60 760 Td (Ban mem mau - DU LIEU MAU phuc vu demo) Tj ET"
    obj = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(noi_dung)).encode() + b" >>\nstream\n" + noi_dung + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    vt = []
    for i, o in enumerate(obj, 1):
        vt.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(obj) + 1}\n0000000000 65535 f \n".encode()
    for v in vt:
        out += f"{v:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(obj) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    duong_dan.parent.mkdir(parents=True, exist_ok=True)
    duong_dan.write_bytes(bytes(out))


def main():
    random.seed(SEED)
    rd = random.Random(SEED)
    rng = np.random.default_rng(SEED)
    Faker.seed(SEED)
    fk = Faker("vi_VN")

    kn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = kn.cursor()
    cur.execute("TRUNCATE log_tim_kiem, luot_muon, ban_sao, nguoi_dung RESTART IDENTITY CASCADE")
    cur.execute("UPDATE tai_lieu SET co_ban_mem = false, muc_truy_cap = NULL, duong_dan_ban_mem = NULL")

    cur.execute("SELECT id, ky_hieu, loai_hinh, tieu_de, khong_co_tl FROM tai_lieu ORDER BY id")
    tai_lieu = cur.fetchall()

    # ---------------- 1. Bản sao ----------------
    ban_sao = []
    for tl_id, ky_hieu, loai, _, khong_co in tai_lieu:
        if khong_co:
            continue
        if loai in ("sach", "sach_ha_noi", "tu_sach_tang", "ky_yeu"):
            n = rd.choices([1, 2, 3], weights=[2, 4, 4])[0]
        else:
            n = rd.choices([1, 2, 3], weights=[6, 3, 1])[0]
        for k in range(1, n + 1):
            ban_sao.append((tl_id, f"{ky_hieu}-{k}", "con", True))
    execute_values(cur, "INSERT INTO ban_sao (tai_lieu_id, ma_ban_sao, trang_thai, du_lieu_mau) VALUES %s",
                   ban_sao, page_size=1000)
    # Một số ít bản sao bị mất
    cur.execute("SELECT id FROM ban_sao ORDER BY id")
    id_ban_sao = [r[0] for r in cur.fetchall()]
    for bid in rd.sample(id_ban_sao, 25):
        cur.execute("UPDATE ban_sao SET trang_thai = 'mat' WHERE id = %s", (bid,))

    # ---------------- 2. Người dùng ----------------
    bam = lambda mk: bcrypt.hashpw(mk.encode(), bcrypt.gensalt(rounds=10)).decode()
    nguoi_dung = [
        ("thuthu", bam("thuthu123"), "Thủ thư Demo", "thu_thu", True),
        ("sv01", bam("sv123"), "Sinh viên Demo", "sinh_vien", True),
        ("gv01", bam("gv123"), "Giảng viên Demo", "giang_vien", True),
    ]
    mk_chung = bam("demo123")
    for i in range(60):
        la_gv = i >= 48
        ten = f"gv{i - 46:02d}" if la_gv else f"sv{i + 2:02d}"
        nguoi_dung.append((ten, mk_chung, fk.name(), "giang_vien" if la_gv else "sinh_vien", True))
    execute_values(cur, "INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau_hash, ho_ten, vai_tro, du_lieu_mau) "
                        "VALUES %s", nguoi_dung)
    cur.execute("SELECT id, ten_dang_nhap FROM nguoi_dung WHERE vai_tro IN ('sinh_vien','giang_vien') ORDER BY id")
    ban_doc = cur.fetchall()
    id_ban_doc = [r[0] for r in ban_doc]
    id_sv01 = next(i for i, t in ban_doc if t == "sv01")

    # ---------------- 3. Tập từ khóa ----------------
    def ket_qua(q, _bo_nho={}):
        if q not in _bo_nho:
            cur.execute("SELECT tai_lieu_id FROM tim_tai_lieu(%s) ORDER BY diem DESC, tai_lieu_id", (q,))
            ids = [r[0] for r in cur.fetchall()]
            _bo_nho[q] = (len(ids), ids[:10])
        return _bo_nho[q]

    cum_that = []
    for c in trich_cum_tu([t[3] for t in tai_lieu]):
        if ket_qua(c)[0] > 0:
            cum_that.append(c)
            if len(cum_that) >= SO_TU_KHOA_THAT:
                break

    khong_co = []
    for k in UNG_VIEN_KHONG_CO:
        if ket_qua(k)[0] == 0:
            khong_co.append(k)
            if len(khong_co) >= 30:
                break
    tap = list(cum_that)
    # chèn từ khóa không có tư liệu rải rác trên thang hạng để vài cái nổi bật trên dashboard
    vi_tri = sorted([3, 7] + rd.sample(range(10, len(tap)), len(khong_co) - 2))
    for vt, k in zip(vi_tri, khong_co):
        tap.insert(vt, k)
    hang = np.arange(1, len(tap) + 1)
    trong_so = 1.0 / hang ** ZIPF_S
    trong_so /= trong_so.sum()

    # ---------------- 4. Phân bổ lượt tìm theo ngày ----------------
    bay_gio = datetime.now().replace(microsecond=0)
    hom_nay = bay_gio.date()
    ngay_list = [hom_nay - timedelta(days=d) for d in range(SO_NGAY - 1, -1, -1)]

    def he_so_ngay(d):
        w = {0: 1.0, 1: 1.05, 2: 1.0, 3: 0.95, 4: 0.85, 5: 0.5, 6: 0.35}[d.weekday()]
        cach = (hom_nay - d).days
        if 48 <= cach <= 62 or cach <= 12:   # hai đợt trước kỳ thi
            w *= 1.7
        if cach == 0:
            w *= bay_gio.hour / 24 + 0.05
        return w

    wn = np.array([he_so_ngay(d) for d in ngay_list])
    so_moi_ngay = rng.multinomial(SO_LOG, wn / wn.sum())
    gio_ts = np.array([0.1, 0.05, 0.02, 0.02, 0.02, 0.1, 0.4, 1.0, 1.6, 2.0, 2.0, 1.4, 0.8, 1.2, 1.8, 2.0,
                       1.7, 1.2, 0.9, 1.1, 1.5, 1.4, 0.9, 0.4])
    gio_ts /= gio_ts.sum()

    logs = []
    dem_chon = Counter()
    for ngay, so in zip(ngay_list, so_moi_ngay):
        for _ in range(int(so)):
            gio = int(rng.choice(24, p=gio_ts))
            phut, giay = rd.randrange(60), rd.randrange(60)
            td = datetime.combine(ngay, time(gio, phut, giay))
            if td > bay_gio:
                td = bay_gio - timedelta(seconds=rd.randrange(1, 3600))
            goc = tap[int(rng.choice(len(tap), p=trong_so))]
            r = rd.random()
            if r < 0.15:
                tu_khoa = bo_dau(goc)
            elif r < 0.20:
                tu_khoa = go_sai(goc if rd.random() < 0.5 else bo_dau(goc), rd)
            else:
                tu_khoa = goc
            if rd.random() < 0.08:
                tu_khoa = tu_khoa.capitalize()
            so_kq, top = ket_qua(tu_khoa)
            chon = None
            if so_kq > 0 and rd.random() < 0.47:
                k = min(int(rng.geometric(0.45)) - 1, len(top) - 1)
                chon = top[k]
                dem_chon[chon] += 1
            nd = rd.choice(id_ban_doc) if rd.random() < 0.55 else None
            ma_phien = "%016x" % rd.getrandbits(64)
            logs.append((tu_khoa, so_kq, chon, td, nd, ma_phien, True))
    execute_values(cur, "INSERT INTO log_tim_kiem (tu_khoa, tu_khoa_chuan, so_ket_qua, tai_lieu_chon_id, thoi_diem, "
                        "nguoi_dung_id, ma_phien, du_lieu_mau) VALUES %s",
                   [(l[0], l[0]) + l[1:] for l in logs],
                   template="(%s, f_chuan_hoa(%s), %s, %s, %s, %s, %s, %s)", page_size=1000)

    # ---------------- 5. Lượt mượn ----------------
    cur.execute("SELECT id, tai_lieu_id FROM ban_sao WHERE trang_thai = 'con' ORDER BY id")
    ban_ranh = {}
    for bid, tl in cur.fetchall():
        ban_ranh.setdefault(tl, []).append(bid)
    co_ban = sorted(ban_ranh)
    tw = np.array([dem_chon.get(t, 0) * 3 + 1 for t in co_ban], dtype=float)
    tw /= tw.sum()
    luot = []
    for i in range(SO_LUOT_MUON):
        tl = co_ban[int(rng.choice(len(co_ban), p=tw))]
        nd = id_sv01 if i < 3 else rd.choice(id_ban_doc)
        cach = int(rng.integers(0, SO_NGAY))
        dk = datetime.combine(hom_nay - timedelta(days=cach), time(rd.randrange(8, 20), rd.randrange(60)))
        if dk > bay_gio:
            dk = bay_gio - timedelta(hours=1)
        r = rd.random()
        if i == 0 or (cach <= 3 and r < 0.6):
            tt = "cho_duyet"
        elif cach > 21:
            tt = "da_tra" if r < 0.85 else "tu_choi" if r < 0.93 else "dang_muon"
        else:
            tt = "dang_muon" if r < 0.6 else "da_tra" if r < 0.92 else "tu_choi"
        if i == 1:
            tt = "dang_muon"
        if i == 2:
            tt = "da_tra"
        ban, ngay_muon, han, ngay_tra = None, None, None, None
        if tt in ("dang_muon", "da_tra"):
            if tt == "dang_muon" and not ban_ranh.get(tl):
                tt = "da_tra"
            ngay_muon = (dk + timedelta(days=rd.randrange(0, 2))).date()
            ngay_muon = min(ngay_muon, hom_nay)
            han = ngay_muon + timedelta(days=14)
            if tt == "dang_muon":
                ban = ban_ranh[tl].pop()
            else:
                ban = rd.choice(ban_ranh[tl]) if ban_ranh.get(tl) else None
                ngay_tra = min(ngay_muon + timedelta(days=rd.randrange(3, 20)), hom_nay)
        luot.append((nd, tl, ban, tt, dk, ngay_muon, han, ngay_tra, True))
    execute_values(cur, "INSERT INTO luot_muon (nguoi_dung_id, tai_lieu_id, ban_sao_id, trang_thai, ngay_dang_ky, "
                        "ngay_muon, han_tra, ngay_tra, du_lieu_mau) VALUES %s", luot)
    cur.execute("UPDATE ban_sao b SET trang_thai = 'dang_muon' FROM luot_muon m "
                "WHERE m.ban_sao_id = b.id AND m.trang_thai = 'dang_muon'")

    # ---------------- 6. Một số tư liệu đã số hóa sẵn (bản mềm mẫu) ----------------
    tao_pdf_mau(GOC / "uploads" / "mau" / "ban_mem_mau.pdf")
    it_chon = [t[0] for t in tai_lieu if not t[4] and dem_chon.get(t[0], 0) <= 2]
    for tl in rd.sample(it_chon, 40):
        cur.execute("UPDATE tai_lieu SET co_ban_mem = true, muc_truy_cap = %s, duong_dan_ban_mem = %s WHERE id = %s",
                    (rd.choice(["cong_khai", "cong_khai", "noi_bo"]), "mau/ban_mem_mau.pdf", tl))
    kn.commit()

    # ---------------- 7. Báo cáo ----------------
    bao_cao(cur)
    kn.close()


def bao_cao(cur):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    so_dong = {}
    for b in ["tai_lieu", "ma_van_de", "ban_sao", "nguoi_dung", "luot_muon", "log_tim_kiem"]:
        cur.execute(f"SELECT count(*) FROM {b}")
        so_dong[b] = cur.fetchone()[0]
    cur.execute("SELECT hien_thi, so_lan FROM v_tu_khoa_top LIMIT 10")
    top = cur.fetchall()
    cur.execute("SELECT round(100.0 * avg((so_ket_qua = 0)::int), 1), "
                "round(100.0 * avg((tai_lieu_chon_id IS NOT NULL)::int), 1) FROM log_tim_kiem")
    ti_le_0, ti_le_chon = cur.fetchone()
    cur.execute("SELECT trang_thai, count(*) FROM luot_muon GROUP BY 1 ORDER BY 1")
    muon = cur.fetchall()
    cur.execute("SELECT so_lan FROM v_tu_khoa_top")
    tan_suat = np.array([r[0] for r in cur.fetchall()])

    hang = np.arange(1, len(tan_suat) + 1)
    k = min(100, len(tan_suat))
    he_so = np.polyfit(np.log(hang[:k]), np.log(tan_suat[:k]), 1)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.loglog(hang, tan_suat, "o", ms=3, color="#9b1c1c", label="Từ khóa (đã chuẩn hóa)")
    ax.loglog(hang[:k], np.exp(he_so[1]) * hang[:k] ** he_so[0], "-", color="#d4af37", lw=2,
              label=f"Đường khớp 100 hạng đầu: độ dốc = {he_so[0]:.2f}")
    ax.set_xlabel("Hạng (log)")
    ax.set_ylabel("Số lượt tìm (log)")
    ax.set_title("Phân bố rank–tần suất từ khóa tìm kiếm (DỮ LIỆU MẪU)")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    thu_muc_seed = GOC / "reports" / "seed"
    thu_muc_seed.mkdir(parents=True, exist_ok=True)
    fig.savefig(thu_muc_seed / "zipf.png", dpi=130)

    dong = ["# Tóm tắt dữ liệu mô phỏng (seed 42)", "", "Mọi dòng có `du_lieu_mau = true`.", "",
            "| Bảng | Số dòng |", "|---|---:|"]
    dong += [f"| {b} | {n} |" for b, n in so_dong.items()]
    dong += ["", f"- Tỉ lệ lượt tìm 0 kết quả: **{ti_le_0}%**",
             f"- Tỉ lệ log có `tai_lieu_chon_id`: **{ti_le_chon}%**",
             f"- Độ dốc log-log 100 hạng đầu: **{he_so[0]:.2f}** (Zipf s≈1.1 → độ dốc ≈ -1.1; "
             "lệch do gộp biến thể không dấu và lỗi gõ)", "",
             "## Lượt mượn theo trạng thái", "", "| Trạng thái | Số |", "|---|---:|"]
    dong += [f"| {t} | {n} |" for t, n in muon]
    dong += ["", "## Top 10 từ khóa", "", "| # | Từ khóa | Lượt |", "|---:|---|---:|"]
    dong += [f"| {i} | {t} | {n} |" for i, (t, n) in enumerate(top, 1)]
    dong += ["", "![Zipf](zipf.png)", ""]
    (thu_muc_seed / "seed_tom_tat.md").write_text("\n".join(dong), encoding="utf-8")
    print("\n".join(dong[4:12]))
    print(f"0 kết quả: {ti_le_0}% | có chọn: {ti_le_chon}% | độ dốc: {he_so[0]:.2f}")


if __name__ == "__main__":
    main()
