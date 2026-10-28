"""
ETL: nạp 8 sheet của file Excel danh mục tư liệu khoa vào bảng tai_lieu, ma_van_de.
Làm sạch theo AGENTS.md mục 5. Ghi báo cáo vào reports/etl/etl_tom_tat.csv và reports/etl/etl_bi_bo.csv.
Chạy: python scripts/etl_import.py
"""
import csv
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
GOC = Path(__file__).resolve().parent.parent
load_dotenv(GOC / ".env")
FILE_EXCEL = GOC / "data" / "[Bản chuẩn] DANH MỤC TƯ LIỆU KHOA.xlsx"
THU_MUC_BAO_CAO = GOC / "reports" / "etl"
THU_MUC_BAO_CAO.mkdir(parents=True, exist_ok=True)

# Cấu hình từng sheet: loai_hinh và ánh xạ cột Excel -> cột CSDL
# (một cột CSDL có thể ghép từ nhiều cột Excel)
CAU_HINH = {
    "LA": dict(loai="luan_an", bo_dong_2=True, ky_hieu="Ký hiệu mới", nam="Thời gian", van_de="Vấn đề",
               tac_gia=["Họ và tên đệm", "Tên"], tieu_de="Tên đề tài",
               co_quan=["Thời gian, địa điểm khảo sát trong LA"], gvhd="Giáo viên hướng dẫn",
               he="Hệ", ghi_chu=["Ghi chú"]),
    "LV": dict(loai="luan_van", ky_hieu="Ký hiệu", nam="Thời gian", van_de="Vấn đề",
               tac_gia=["Họ và tên đệm", "Tên riêng"], tieu_de="Tên đề tài", co_quan=["Cơ quan đơn vị"],
               gvhd="Giáo viên hướng dẫn", he="Hệ", khoa="Khoá", ghi_chu=["Ghi chú", "Unnamed: 13"]),
    "KL": dict(loai="khoa_luan", ky_hieu="Ký hiệu mới", nam="Thời gian", van_de="Vấn đề",
               tac_gia=["Họ và tên đệm", "Tên"], tieu_de="Tên đề tài", co_quan=["Cơ quan đơn vị"],
               gvhd="Giáo viên hướng dẫn", he="Hệ", khoa="Khoá", ghi_chu=["Ghi chú"]),
    "KH": dict(loai="bao_cao_kh", ky_hieu="Ký hiệu mới", nam="Thời gian", van_de="Vấn đề",
               tac_gia=["Họ và tên đệm", "Tên"], tieu_de="tên đề tài", co_quan=["Cơ quan đơn vị"],
               gvhd="Giáo viên hướng dẫn", he="Hệ", khoa="Khoá", ghi_chu=["Ghi chú", "Unnamed: 13"]),
    "KY": dict(loai="ky_yeu", ky_hieu="Ký hiệu", nam="Thời gian", van_de="Vấn Đề",
               tac_gia=["Tác giả"], tieu_de="Tên  sách, tư liệu", nxb=["Nhà xuất bản", "Unnamed: 7"],
               ghi_chu=["Ghi chú"]),
    "S-TV": dict(loai="sach", bo_dong_2=True, ky_hieu="Ký hiệu mới", nam="Thời gian",
                 tac_gia=["Tác giả"], tieu_de="Tên đề sách", nxb=["NXB"], ghi_chu=["Ghi chú"]),
    "HN": dict(loai="sach_ha_noi", ky_hieu="Ký hiệu", nam="Thời gian", tac_gia=["Tác giả"],
               tieu_de="Tên đề sách", nxb=["NXB"], ghi_chu=["Ghi chú", "Loại hình", "ĐC Tài liệu"]),
    "PGS. Vương Đình Quyền": dict(loai="tu_sach_tang", ky_hieu=None, tien_to="VDQ", nam="Năm xuất bản",
                                  tac_gia=["Tác giả"], tieu_de="Tên sách", nxb=["Nhà xuất bản"]),
}

GIA_TRI_RONG = {"", ".", "#", "nan", "none", "nat"}
MAU_KHONG_CO_TL = re.compile(r"ko\s*có\s*tl|^ko\s*có$|chưa\s*có\s*tài\s*liệu", re.IGNORECASE)


class BoDem:
    """Đếm số ô đã làm sạch cho từng sheet."""
    def __init__(self):
        self.so_o = 0


def lam_sach(gia_tri, dem: BoDem):
    """Trả về chuỗi đã trim, hoặc None nếu ô rỗng / chỉ có '.', '#', 'nan'."""
    if gia_tri is None or (isinstance(gia_tri, float) and pd.isna(gia_tri)):
        return None
    goc = str(gia_tri)
    s = goc.replace("\r", " ").replace("\n", "; ").strip()
    s = re.sub(r"[ \t]+", " ", s)
    if s.lower() in GIA_TRI_RONG:
        dem.so_o += 1
        return None
    if s != goc:
        dem.so_o += 1
    return s


def ghep(cac_gia_tri, dau_noi=" "):
    phan = [g for g in cac_gia_tri if g]
    return dau_noi.join(phan) if phan else None


def tach_nam(gia_tri):
    """Trả về (nam:int|None, nam_goc:str|None). nam_goc chỉ lưu khi giá trị gốc không phải số năm thuần."""
    if gia_tri is None:
        return None, None
    s = gia_tri.strip()
    if re.fullmatch(r"\d{4}", s):
        return int(s), None
    # Ô Excel bị định dạng ngày: số năm bị hiểu thành số seri ngày (1905-06-24 = 2003)
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})( 00:00:00)?", s)
    if m:
        seri = (date(int(m[1]), int(m[2]), int(m[3])) - date(1899, 12, 30)).days
        if 1900 <= seri <= 2030:
            return seri, s
    m = re.search(r"\d{4}", s)
    if m and 1800 <= int(m.group()) <= 2030:
        return int(m.group()), s
    return None, s


def doc_sheet(ten_sheet, df, cfg, dem):
    """Chuyển một sheet thành danh sách bản ghi và danh sách dòng bị bỏ."""
    ban_ghi, bi_bo = [], []
    so_dong_goc = len(df)
    for chi_so, dong in df.iterrows():
        dong_excel = chi_so + 2  # header ở dòng 1
        if cfg.get("bo_dong_2") and dong_excel == 2:
            continue  # dòng số thứ tự cột
        lay = lambda cot: lam_sach(dong.get(cot), dem) if cot else None
        tieu_de = lay(cfg["tieu_de"])
        if not tieu_de:
            bi_bo.append({"sheet": ten_sheet, "dong_goc": dong_excel, "ly_do": "khong_co_tieu_de",
                          "du_lieu_goc": " | ".join(str(v) for v in dong.values if not pd.isna(v))})
            continue
        if cfg.get("ky_hieu"):
            ky_hieu = lay(cfg["ky_hieu"])
        else:
            ky_hieu = None
        nam, nam_goc = tach_nam(lay(cfg.get("nam")))
        ghi_chu = ghep([lay(c) for c in cfg.get("ghi_chu", [])], "; ")
        ban_ghi.append({
            "ky_hieu": ky_hieu,
            "loai_hinh": cfg["loai"],
            "tieu_de": tieu_de,
            "tac_gia": ghep([lay(c) for c in cfg.get("tac_gia", [])]),
            "gvhd": lay(cfg.get("gvhd")),
            "co_quan": ghep([lay(c) for c in cfg.get("co_quan", [])], "; "),
            "nxb": ghep([lay(c) for c in cfg.get("nxb", [])], "; "),
            "nam": nam,
            "nam_goc": nam_goc,
            "ma_van_de": lay(cfg.get("van_de")),
            "khoa_hoc": lay(cfg.get("khoa")),
            "he": lay(cfg.get("he")),
            "ghi_chu": ghi_chu,
            "khong_co_tl": bool(ghi_chu and any(MAU_KHONG_CO_TL.search(p.strip()) for p in ghi_chu.split(";"))),
            "sheet_goc": ten_sheet,
            "dong_goc": dong_excel,
        })
    # Sinh ký hiệu cho sheet không có (VDQ.001…)
    if not cfg.get("ky_hieu"):
        for i, bg in enumerate(ban_ghi, 1):
            bg["ky_hieu"] = f"{cfg['tien_to']}.{i:03d}"
    so_goc = so_dong_goc - (1 if cfg.get("bo_dong_2") else 0)
    return ban_ghi, bi_bo, so_goc


def main():
    THU_MUC_BAO_CAO.mkdir(exist_ok=True)
    tat_ca = pd.read_excel(FILE_EXCEL, sheet_name=None, header=0, dtype=str)
    moi_ban_ghi, moi_bi_bo, tom_tat = [], [], []
    for ten_sheet, cfg in CAU_HINH.items():
        dem = BoDem()
        ban_ghi, bi_bo, so_goc = doc_sheet(ten_sheet, tat_ca[ten_sheet], cfg, dem)
        moi_ban_ghi += ban_ghi
        moi_bi_bo += bi_bo
        tom_tat.append({"sheet": ten_sheet, "loai_hinh": cfg["loai"], "so_dong_goc": so_goc,
                        "so_dong_nap": len(ban_ghi), "so_dong_bo": len(bi_bo), "so_o_lam_sach": dem.so_o})

    # Ký hiệu thiếu hoặc trùng: thêm hậu tố để giữ ràng buộc UNIQUE, ghi lại vào báo cáo
    da_thay = {}
    for bg in moi_ban_ghi:
        kh = bg["ky_hieu"] or f"{bg['sheet_goc']}.R{bg['dong_goc']}"
        goc = kh
        n = 1
        while kh in da_thay:
            n += 1
            kh = f"{goc}#{n}"
        if kh != bg["ky_hieu"]:
            moi_bi_bo.append({"sheet": bg["sheet_goc"], "dong_goc": bg["dong_goc"],
                              "ly_do": f"ky_hieu_doi_thanh:{kh} (khong bo dong)", "du_lieu_goc": bg["ky_hieu"] or ""})
        da_thay[kh] = True
        bg["ky_hieu"] = kh

    ma_van_de = sorted({bg["ma_van_de"] for bg in moi_ban_ghi if bg["ma_van_de"]})

    cot = ["ky_hieu", "loai_hinh", "tieu_de", "tac_gia", "gvhd", "co_quan", "nxb", "nam", "nam_goc",
           "ma_van_de", "khoa_hoc", "he", "ghi_chu", "khong_co_tl", "sheet_goc", "dong_goc"]
    with psycopg2.connect(os.environ["DATABASE_URL"]) as ket_noi, ket_noi.cursor() as cur:
        cur.execute("TRUNCATE log_tim_kiem, luot_muon, ban_sao, tai_lieu, ma_van_de RESTART IDENTITY CASCADE")
        execute_values(cur, "INSERT INTO ma_van_de (ma, ten) VALUES %s", [(m, None) for m in ma_van_de])
        execute_values(cur, f"INSERT INTO tai_lieu ({', '.join(cot)}) VALUES %s",
                       [tuple(bg[c] for c in cot) for bg in moi_ban_ghi], page_size=500)

    with open(THU_MUC_BAO_CAO / "etl_tom_tat.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(tom_tat[0].keys()))
        w.writeheader()
        w.writerows(tom_tat)
    with open(THU_MUC_BAO_CAO / "etl_bi_bo.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["sheet", "dong_goc", "ly_do", "du_lieu_goc"])
        w.writeheader()
        w.writerows(moi_bi_bo)

    print(f"{'sheet':<24}{'goc':>6}{'nap':>6}{'bo':>5}{'o_sach':>8}")
    for t in tom_tat:
        print(f"{t['sheet']:<24}{t['so_dong_goc']:>6}{t['so_dong_nap']:>6}{t['so_dong_bo']:>5}{t['so_o_lam_sach']:>8}")
    print(f"Tổng nạp: {len(moi_ban_ghi)} tư liệu, {len(ma_van_de)} mã vấn đề, "
          f"{sum(bg['khong_co_tl'] for bg in moi_ban_ghi)} tư liệu 'Ko có TL'")


if __name__ == "__main__":
    main()
