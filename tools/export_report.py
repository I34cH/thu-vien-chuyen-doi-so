"""
Công cụ xuất toàn bộ tài liệu và biểu đồ báo cáo học thuật (Milestone M6):
1. reports/so_lieu/*.csv:
   - tu_khoa_top.csv (Top từ khóa tìm kiếm)
   - khong_ket_qua.csv (Từ khóa tìm nhiều nhưng 0 kết quả)
   - nen_so_hoa.csv (Tư liệu đề xuất ưu tiên số hóa)
   - theo_ngay.csv (Xu hướng lượt tìm kiếm theo ngày)
   - theo_loai_hinh.csv (Phân bố tư liệu, bản sao, bản mềm và nhu cầu theo loại hình)
2. reports/bieu_do/*.png (Matplotlib đồng bộ bảng màu đỏ–vàng–xám #9b1c1c, #d4af37, #c53030, #64748b, #e57373):
   - tu_khoa_top.png
   - khong_ket_qua.png
   - nen_so_hoa.png
   - theo_ngay.png (đánh dấu ngày hôm nay là 'đang cập nhật')
   - theo_loai_hinh.png
3. reports/tai_lieu/tu_dien_du_lieu.md (Trích xuất trực tiếp từ information_schema của PostgreSQL)
4. reports/tai_lieu/erd.png (Render từ docs/erd.mmd qua mermaid-cli, dự phòng copy docs/erd.png)
5. reports/tai_lieu/api.md (Tự động trích xuất danh sách route + vai trò được phép từ code Python Flask)

Chạy: python tools/export_report.py   (hoặc npm run report)
"""
import ast
import csv
import os
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import psycopg2
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

GOC = Path(__file__).resolve().parent.parent
if str(GOC) not in sys.path:
    sys.path.insert(0, str(GOC))

load_dotenv(GOC / ".env")
os.environ["PGCLIENTENCODING"] = "UTF8"

THU_MUC_BAO_CAO = GOC / "reports"
THU_MUC_SO_LIEU = THU_MUC_BAO_CAO / "so_lieu"
THU_MUC_BIEU_DO = THU_MUC_BAO_CAO / "bieu_do"
THU_MUC_TAI_LIEU = THU_MUC_BAO_CAO / "tai_lieu"

# Bảng màu chủ đạo đỏ–vàng–xám theo AGENTS.md mục 3
MAU_DO_DAM = "#9b1c1c"
MAU_VANG_KIM = "#d4af37"
MAU_DO_TUOI = "#c53030"
MAU_XAM = "#64748b"
MAU_DO_NHAT = "#e57373"

TEN_LOAI_HINH = {
    "bao_cao_kh": "Báo cáo NCKH (KH)",
    "sach": "Sách thư viện (S-TV)",
    "khoa_luan": "Khóa luận tốt nghiệp (KL)",
    "luan_van": "Luận văn thạc sĩ (LV)",
    "tu_sach_tang": "Tủ sách PGS. Vương Đình Quyền",
    "ky_yeu": "Kỷ yếu khoa học (KY)",
    "sach_ha_noi": "Sách Hà Nội học (HN)",
    "luan_an": "Luận án tiến sĩ (LA)",
}

Y_NGHIA_BANG = {
    "ma_van_de": "Danh mục mã phân loại vấn đề chuyên môn (QTVP, LTH, VB, LT, KS…).",
    "tai_lieu": "Danh mục tư liệu gốc nạp từ 8 sheet Excel của Khoa (sách, luận án, luận văn, khóa luận, báo cáo KH, kỷ yếu).",
    "ban_sao": "Các bản sao vật lý tại kho tương ứng với từng tư liệu (1–3 bản/tư liệu có bản cứng).",
    "nguoi_dung": "Tài khoản người dùng hệ thống (sinh_vien, giang_vien, thu_thu, admin).",
    "luot_muon": "Giao dịch đăng ký mượn, duyệt mượn, trả hoặc từ chối mượn bản sao vật lý.",
    "log_tim_kiem": "Nhật ký truy vấn tìm kiếm của người dùng và tư liệu được nhấp chọn từ danh sách kết quả.",
    "v_tinh_trang_tai_lieu": "View tổng hợp tổng số bản sao khả dụng (không mất) và số bản còn rảnh tại kho của mỗi tư liệu.",
    "v_tu_khoa_top": "View thống kê tần suất tìm kiếm theo cụm từ khóa chuẩn hóa và số lần trả về 0 kết quả.",
    "v_tim_theo_ngay": "View tổng hợp số lượt tìm kiếm và số lượt 0 kết quả theo từng ngày.",
    "v_khong_ket_qua": "View liệt kê các từ khóa tìm nhiều nhưng trả về 0 kết quả để gợi ý mua sắm/bổ sung.",
    "v_nen_so_hoa": "View xếp hạng tư liệu ưu tiên số hóa theo công thức điểm = số lần chọn + 2 × số lượt mượn.",
}

Y_NGHIA_COT = {
    ("ma_van_de", "ma"): "Mã viết tắt phân loại vấn đề chuyên ngành (khóa chính).",
    ("ma_van_de", "ten"): "Tên giải nghĩa đầy đủ của mã vấn đề (để NULL khi chưa có bảng giải nghĩa).",
    ("tai_lieu", "id"): "Mã định danh tự tăng của tư liệu (khóa chính).",
    ("tai_lieu", "ky_hieu"): "Ký hiệu xếp giá duy nhất (VD: LA.01, VDQ.001).",
    ("tai_lieu", "loai_hinh"): "Loại hình tư liệu (luan_an, luan_van, khoa_luan, bao_cao_kh, ky_yeu, sach, sach_ha_noi, tu_sach_tang).",
    ("tai_lieu", "tieu_de"): "Nhan đề đầy đủ của tư liệu hoặc tên đề tài nghiên cứu.",
    ("tai_lieu", "tac_gia"): "Họ tên tác giả hoặc người thực hiện đề tài.",
    ("tai_lieu", "gvhd"): "Giảng viên hướng dẫn (đối với luận án, luận văn, khóa luận, báo cáo KH).",
    ("tai_lieu", "co_quan"): "Cơ quan, đơn vị khảo sát hoặc thực tập.",
    ("tai_lieu", "nxb"): "Nhà xuất bản (đối với sách, kỷ yếu).",
    ("tai_lieu", "nam"): "Năm xuất bản hoặc bảo vệ đã chuẩn hóa về số nguyên 4 chữ số.",
    ("tai_lieu", "nam_goc"): "Chuỗi thời gian gốc trong Excel khi không phải số năm đơn thuần (VD: 1985-2005).",
    ("tai_lieu", "ma_van_de"): "Khóa ngoại tham chiếu bảng ma_van_de(ma).",
    ("tai_lieu", "khoa_hoc"): "Khóa đào tạo của sinh viên/học viên.",
    ("tai_lieu", "he"): "Hệ đào tạo (Chính quy, Tại chức…).",
    ("tai_lieu", "ghi_chu"): "Ghi chú tình trạng hoặc thông tin phụ từ Excel gốc.",
    ("tai_lieu", "khong_co_tl"): "Cờ đánh dấu tư liệu bị ghi chú 'Ko có TL' (không có bản cứng tại kho).",
    ("tai_lieu", "co_ban_mem"): "Cờ đánh dấu tư liệu đã được số hóa (có tệp PDF bản mềm).",
    ("tai_lieu", "muc_truy_cap"): "Mức độ truy cập bản mềm: 'cong_khai' (ai cũng đọc được) hoặc 'noi_bo' (phải đăng nhập).",
    ("tai_lieu", "duong_dan_ban_mem"): "Đường dẫn tương đối của tệp PDF trong thư mục uploads/.",
    ("tai_lieu", "tsv"): "Vector toàn văn (tsvector) sinh tự động từ tiêu đề + tác giả đã bỏ dấu phục vụ tìm kiếm GIN.",
    ("tai_lieu", "sheet_goc"): "Tên sheet Excel gốc chứa bản ghi.",
    ("tai_lieu", "dong_goc"): "Số thứ tự dòng trong sheet Excel gốc.",
    ("ban_sao", "id"): "Mã định danh tự tăng của bản sao (khóa chính).",
    ("ban_sao", "tai_lieu_id"): "Khóa ngoại tham chiếu tư liệu gốc tai_lieu(id).",
    ("ban_sao", "ma_ban_sao"): "Mã vạch/ký hiệu từng cuốn bản sao cụ thể (VD: S.001-1).",
    ("ban_sao", "trang_thai"): "Trạng thái vật lý: 'con' (sẵn sàng), 'dang_muon' (đang cho mượn), 'mat' (thất lạc).",
    ("ban_sao", "du_lieu_mau"): "Cờ phân biệt dữ liệu mô phỏng phục vụ demo (true) và dữ liệu phát sinh thật (false).",
    ("nguoi_dung", "id"): "Mã định danh tự tăng của người dùng (khóa chính).",
    ("nguoi_dung", "ten_dang_nhap"): "Tên tài khoản đăng nhập duy nhất (VD: thuthu, sv01, gv01).",
    ("nguoi_dung", "mat_khau_hash"): "Chuỗi băm mật khẩu bằng thuật toán bcrypt.",
    ("nguoi_dung", "ho_ten"): "Họ và tên hiển thị của người dùng.",
    ("nguoi_dung", "vai_tro"): "Vai trò trong hệ thống: sinh_vien, giang_vien, thu_thu, admin.",
    ("nguoi_dung", "du_lieu_mau"): "Cờ đánh dấu tài khoản sinh tự động phục vụ demo.",
    ("luot_muon", "id"): "Mã định danh tự tăng của lượt mượn (khóa chính).",
    ("luot_muon", "nguoi_dung_id"): "Khóa ngoại tham chiếu độc giả mượn nguoi_dung(id).",
    ("luot_muon", "tai_lieu_id"): "Khóa ngoại tham chiếu tư liệu được yêu cầu tai_lieu(id).",
    ("luot_muon", "ban_sao_id"): "Khóa ngoại tham chiếu bản sao được gán khi thủ thư duyệt (NULL khi đang chờ duyệt).",
    ("luot_muon", "trang_thai"): "Trạng thái phiếu mượn: 'cho_duyet', 'dang_muon', 'da_tra', 'tu_choi'.",
    ("luot_muon", "ngay_dang_ky"): "Thời điểm độc giả gửi yêu cầu đăng ký mượn.",
    ("luot_muon", "ngay_muon"): "Ngày thủ thư duyệt và giao bản sao.",
    ("luot_muon", "han_tra"): "Hạn trả dự kiến (ngay_muon + 14 ngày).",
    ("luot_muon", "ngay_tra"): "Ngày thực tế độc giả hoàn trả tài liệu.",
    ("luot_muon", "du_lieu_mau"): "Cờ đánh dấu lượt mượn mô phỏng phục vụ demo.",
    ("log_tim_kiem", "id"): "Mã định danh tự tăng kiểu bigserial của dòng log tìm kiếm.",
    ("log_tim_kiem", "tu_khoa"): "Chuỗi truy vấn nguyên bản người dùng nhập vào ô tìm kiếm.",
    ("log_tim_kiem", "tu_khoa_chuan"): "Chuỗi từ khóa đã chuẩn hóa bằng f_chuan_hoa (chữ thường, bỏ dấu, gộp khoảng trắng).",
    ("log_tim_kiem", "so_ket_qua"): "Số lượng tư liệu khớp trả về tại thời điểm tìm kiếm.",
    ("log_tim_kiem", "tai_lieu_chon_id"): "Mã tư liệu người dùng nhấp chọn xem chi tiết từ danh sách kết quả (NULL nếu không chọn).",
    ("log_tim_kiem", "thoi_diem"): "Thời điểm thực hiện truy vấn tìm kiếm.",
    ("log_tim_kiem", "nguoi_dung_id"): "Mã người dùng thực hiện tìm kiếm (NULL nếu là khách vãng lai).",
    ("log_tim_kiem", "ma_phien"): "Mã phiên làm việc ẩn danh (session ID) để liên kết sự kiện chọn kết quả.",
    ("log_tim_kiem", "du_lieu_mau"): "Cờ đánh dấu log mô phỏng phục vụ demo.",
}


def ghi_csv(duong_dan: Path, cot: list[str], dong: list[tuple]):
    """Ghi danh sách dòng ra tệp CSV chuẩn UTF-8 with BOM."""
    duong_dan.parent.mkdir(parents=True, exist_ok=True)
    with open(duong_dan, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(cot)
        w.writerows(dong)


def xuat_so_lieu_va_bieu_do(cur):
    """Truy vấn số liệu tổng hợp, xuất 5 file CSV và 5 ảnh biểu đồ matplotlib."""
    THU_MUC_SO_LIEU.mkdir(parents=True, exist_ok=True)
    THU_MUC_BIEU_DO.mkdir(parents=True, exist_ok=True)

    # 1. Top từ khóa (tu_khoa_top.csv & tu_khoa_top.png)
    cur.execute("""
        SELECT tu_khoa_chuan, hien_thi, so_lan, so_lan_0_kq
        FROM v_tu_khoa_top
        ORDER BY so_lan DESC, tu_khoa_chuan ASC
        LIMIT 100
    """)
    rows_tk = cur.fetchall()
    ghi_csv(
        THU_MUC_SO_LIEU / "tu_khoa_top.csv",
        ["tu_khoa_chuan", "hien_thi", "so_lan", "so_lan_0_kq"],
        rows_tk,
    )

    top15 = rows_tk[:15][::-1]
    fig, ax = plt.subplots(figsize=(9, 6))
    labels_tk = [r[1] or r[0] for r in top15]
    vals_tk = [int(r[2]) for r in top15]
    colors_tk = [
        MAU_DO_DAM if i == len(top15) - 1
        else MAU_DO_TUOI if i >= len(top15) - 3
        else MAU_VANG_KIM if i >= len(top15) - 7
        else MAU_XAM
        for i in range(len(top15))
    ]
    bars = ax.barh(labels_tk, vals_tk, color=colors_tk, height=0.68)
    ax.bar_label(bars, padding=4, fontsize=9)
    ax.set_xlabel("Số lượt tìm kiếm")
    ax.set_title("15 từ khóa nào có tần suất tra cứu cao nhất? (DỮ LIỆU MẪU)", fontweight="bold", color=MAU_DO_DAM)
    ax.grid(axis="x", alpha=0.3)
    ax.set_xlim(0, max(vals_tk) * 1.15 if vals_tk else 10)
    fig.tight_layout()
    fig.savefig(THU_MUC_BIEU_DO / "tu_khoa_top.png", dpi=150)
    plt.close(fig)

    # 2. Từ khóa 0 kết quả (khong_ket_qua.csv & khong_ket_qua.png)
    cur.execute("""
        SELECT tu_khoa_chuan, hien_thi, so_lan, lan_cuoi::date::text
        FROM v_khong_ket_qua
        ORDER BY so_lan DESC, tu_khoa_chuan ASC
    """)
    rows_0kq = cur.fetchall()
    ghi_csv(
        THU_MUC_SO_LIEU / "khong_ket_qua.csv",
        ["tu_khoa_chuan", "hien_thi", "so_lan", "lan_cuoi"],
        rows_0kq,
    )

    top15_0kq = rows_0kq[:15][::-1]
    fig, ax = plt.subplots(figsize=(9, 6))
    labels_0 = [r[1] or r[0] for r in top15_0kq]
    vals_0 = [int(r[2]) for r in top15_0kq]
    bars0 = ax.barh(labels_0, vals_0, color=MAU_DO_TUOI, edgecolor=MAU_DO_DAM, height=0.68)
    ax.bar_label(bars0, padding=4, fontsize=9)
    ax.set_xlabel("Số lần tìm kiếm trả về 0 kết quả")
    ax.set_title("Những từ khóa nào được tìm nhiều nhưng chưa có tư liệu?", fontweight="bold", color=MAU_DO_DAM)
    ax.grid(axis="x", alpha=0.3)
    ax.set_xlim(0, max(vals_0) * 1.15 if vals_0 else 10)
    fig.tight_layout()
    fig.savefig(THU_MUC_BIEU_DO / "khong_ket_qua.png", dpi=150)
    plt.close(fig)

    # 3. Đề xuất nên số hóa (nen_so_hoa.csv & nen_so_hoa.png)
    cur.execute("""
        SELECT tai_lieu_id, ky_hieu, tieu_de, tac_gia, loai_hinh, nam,
               so_lan_chon, so_luot_muon, diem
        FROM v_nen_so_hoa
        ORDER BY diem DESC, tai_lieu_id ASC
        LIMIT 100
    """)
    rows_sh = cur.fetchall()
    ghi_csv(
        THU_MUC_SO_LIEU / "nen_so_hoa.csv",
        ["tai_lieu_id", "ky_hieu", "tieu_de", "tac_gia", "loai_hinh", "nam", "so_lan_chon", "so_luot_muon", "diem"],
        rows_sh,
    )

    top15_sh = rows_sh[:15][::-1]
    fig, ax = plt.subplots(figsize=(10, 6.5))
    labels_sh = [
        f"[{r[1]}] {(r[2][:42] + '…') if len(r[2]) > 42 else r[2]}"
        for r in top15_sh
    ]
    chon_vals = np.array([int(r[6]) for r in top15_sh])
    muon_diem_vals = np.array([int(r[7]) * 2 for r in top15_sh])
    ax.barh(labels_sh, chon_vals, color=MAU_VANG_KIM, label="Điểm từ lượt chọn (1 × lượt chọn)", height=0.68)
    ax.barh(labels_sh, muon_diem_vals, left=chon_vals, color=MAU_DO_DAM, label="Điểm từ lượt mượn (2 × lượt mượn)", height=0.68)
    tong_diem = chon_vals + muon_diem_vals
    for idx, td in enumerate(tong_diem):
        ax.text(td + 0.4, idx, str(td), va="center", fontsize=8.5, fontweight="bold", color=MAU_DO_DAM)
    ax.set_xlabel("Điểm ưu tiên số hóa (Điểm = Lượt chọn + 2 × Lượt mượn)")
    ax.set_title("Top 15 tư liệu cần được ưu tiên số hóa trước?", fontweight="bold", color=MAU_DO_DAM)
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.3)
    ax.set_xlim(0, max(tong_diem) * 1.15 if len(tong_diem) else 10)
    fig.tight_layout()
    fig.savefig(THU_MUC_BIEU_DO / "nen_so_hoa.png", dpi=150)
    plt.close(fig)

    # 4. Lượt tìm theo ngày (theo_ngay.csv & theo_ngay.png)
    cur.execute("""
        SELECT ngay::text, so_luot, so_luot_0_kq
        FROM v_tim_theo_ngay
        ORDER BY ngay ASC
    """)
    rows_ngay = cur.fetchall()
    ghi_csv(
        THU_MUC_SO_LIEU / "theo_ngay.csv",
        ["ngay", "so_luot", "so_luot_0_kq"],
        rows_ngay,
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    x_idx = np.arange(len(rows_ngay))
    y_tong = [int(r[1]) for r in rows_ngay]
    y_0kq = [int(r[2]) for r in rows_ngay]
    ngay_labels = [
        f"{r[0][8:10]}/{r[0][5:7]}" + (" (đang cập nhật)" if i == len(rows_ngay) - 1 else "")
        for i, r in enumerate(rows_ngay)
    ]

    if len(x_idx) > 1:
        ax.plot(x_idx[:-1], y_tong[:-1], "-", color=MAU_DO_DAM, lw=2, label="Tổng lượt tìm kiếm")
        ax.plot(x_idx[-2:], y_tong[-2:], "--", color=MAU_DO_DAM, lw=2)
        ax.plot(x_idx[-1], y_tong[-1], "o", color="#ffffff", markeredgecolor=MAU_DO_DAM, markeredgewidth=2, ms=6,
                label="Hôm nay (đang cập nhật)")
    else:
        ax.plot(x_idx, y_tong, "-", color=MAU_DO_DAM, lw=2, label="Tổng lượt tìm kiếm")

    ax.plot(x_idx, y_0kq, "--", color=MAU_VANG_KIM, lw=1.8, label="Tìm 0 kết quả")
    ax.fill_between(x_idx, y_tong, color=MAU_DO_DAM, alpha=0.08)

    tick_pos = list(range(0, len(rows_ngay), max(1, len(rows_ngay) // 10)))
    if (len(rows_ngay) - 1) not in tick_pos and len(rows_ngay) > 0:
        tick_pos[-1] = len(rows_ngay) - 1
    ax.set_xticks(tick_pos)
    ax.set_xticklabels([ngay_labels[i] for i in tick_pos], rotation=25, ha="right", fontsize=8.5)
    ax.set_ylabel("Số lượt tìm kiếm")
    ax.set_title("Xu hướng tìm kiếm thay đổi như thế nào theo thời gian (90 ngày)?", fontweight="bold", color=MAU_DO_DAM)
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(THU_MUC_BIEU_DO / "theo_ngay.png", dpi=150)
    plt.close(fig)

    # 5. Phân bố theo loại hình (theo_loai_hinh.csv & theo_loai_hinh.png)
    cur.execute("""
        WITH chon AS (
            SELECT tai_lieu_chon_id AS tl_id, count(*)::int AS so_chon
            FROM log_tim_kiem
            WHERE tai_lieu_chon_id IS NOT NULL
            GROUP BY 1
        ),
        muon AS (
            SELECT tai_lieu_id AS tl_id, count(*)::int AS so_muon
            FROM luot_muon
            WHERE trang_thai <> 'tu_choi'
            GROUP BY 1
        )
        SELECT t.loai_hinh,
               count(*)::int AS so_tai_lieu,
               count(*) FILTER (WHERE t.co_ban_mem = true)::int AS so_da_so_hoa,
               count(*) FILTER (WHERE t.khong_co_tl = true)::int AS so_khong_co_tl,
               coalesce(sum(v.so_ban), 0)::int AS tong_ban_sao,
               coalesce(sum(c.so_chon), 0)::int AS tong_luot_chon,
               coalesce(sum(m.so_muon), 0)::int AS tong_luot_muon
        FROM tai_lieu t
        LEFT JOIN v_tinh_trang_tai_lieu v ON v.tai_lieu_id = t.id
        LEFT JOIN chon c ON c.tl_id = t.id
        LEFT JOIN muon m ON m.tl_id = t.id
        GROUP BY t.loai_hinh
        ORDER BY so_tai_lieu DESC, t.loai_hinh ASC
    """)
    rows_loai = cur.fetchall()
    ghi_csv(
        THU_MUC_SO_LIEU / "theo_loai_hinh.csv",
        ["loai_hinh", "so_tai_lieu", "so_da_so_hoa", "so_khong_co_tl", "tong_ban_sao", "tong_luot_chon", "tong_luot_muon"],
        rows_loai,
    )

    rows_loai_rev = rows_loai[::-1]
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    labels_loai = [TEN_LOAI_HINH.get(r[0], r[0]) for r in rows_loai_rev]
    so_tl = [int(r[1]) for r in rows_loai_rev]
    so_chon = [int(r[5]) for r in rows_loai_rev]
    y_pos = np.arange(len(labels_loai))
    h = 0.38
    b1 = ax.barh(y_pos + h / 2, so_tl, height=h, color=MAU_DO_DAM, label="Số đầu tư liệu")
    b2 = ax.barh(y_pos - h / 2, so_chon, height=h, color=MAU_VANG_KIM, label="Tổng lượt nhấp chọn kết quả")
    ax.bar_label(b1, padding=3, fontsize=8.5)
    ax.bar_label(b2, padding=3, fontsize=8.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels_loai)
    ax.set_xlabel("Số lượng")
    ax.set_title("Quy mô danh mục và nhu cầu tra cứu theo từng loại hình tư liệu?", fontweight="bold", color=MAU_DO_DAM)
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.3)
    ax.set_xlim(0, max(so_tl + so_chon) * 1.15 if so_tl else 10)
    fig.tight_layout()
    fig.savefig(THU_MUC_BIEU_DO / "theo_loai_hinh.png", dpi=150)
    plt.close(fig)


def xuat_tu_dien_du_lieu(cur):
    """Đọc information_schema của PostgreSQL và ghi reports/tai_lieu/tu_dien_du_lieu.md."""
    THU_MUC_TAI_LIEU.mkdir(parents=True, exist_ok=True)
    cur.execute("""
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY CASE WHEN table_type = 'BASE TABLE' THEN 0 ELSE 1 END, table_name
    """)
    ds_bang = cur.fetchall()

    dong = [
        "# Từ điển dữ liệu CSDL (`thu_vien_ck`)",
        "",
        "> Tài liệu được trích xuất tự động từ `information_schema.tables` và `information_schema.columns` của PostgreSQL.",
        "",
        "## 1. Tổng quan các bảng và khung nhìn (Views)",
        "",
        "| Tên đối tượng | Loại | Số dòng hiện tại | Ý nghĩa nghiệp vụ |",
        "|---|---|---:|---|",
    ]

    for ten_bang, loai_bang in ds_bang:
        cur.execute(f'SELECT count(*) FROM "{ten_bang}"')
        so_dong = cur.fetchone()[0]
        loai_ht = "Bảng cơ sở (TABLE)" if loai_bang == "BASE TABLE" else "Khung nhìn (VIEW)"
        y_nghia = Y_NGHIA_BANG.get(ten_bang, "Đối tượng dữ liệu hệ thống.")
        dong.append(f"| `{ten_bang}` | {loai_ht} | {so_dong:,} | {y_nghia} |")

    dong += ["", "## 2. Chi tiết cấu trúc từng bảng và View", ""]

    for ten_bang, loai_bang in ds_bang:
        loai_ht = "Bảng" if loai_bang == "BASE TABLE" else "View"
        dong += [
            f"### {loai_ht}: `{ten_bang}`",
            "",
            f"- **Mô tả:** {Y_NGHIA_BANG.get(ten_bang, '')}",
            "",
            "| # | Tên cột | Kiểu dữ liệu | Cho phép NULL | Mặc định | Ý nghĩa |",
            "|---:|---|---|:---:|---|---|",
        ]
        cur.execute("""
            SELECT ordinal_position, column_name, data_type, character_maximum_length,
                   is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (ten_bang,))
        for pos, col, dtype, char_len, nullable, default in cur.fetchall():
            kieu = f"{dtype}({char_len})" if char_len else dtype
            mac_dinh = f"`{default}`" if default else "—"
            mo_ta_cot = Y_NGHIA_COT.get((ten_bang, col), "Trường tổng hợp / truy xuất từ view.")
            dong.append(f"| {pos} | `{col}` | `{kieu}` | {nullable} | {mac_dinh} | {mo_ta_cot} |")
        dong.append("")

    (THU_MUC_TAI_LIEU / "tu_dien_du_lieu.md").write_text("\n".join(dong), encoding="utf-8")


def xuat_erd_png():
    """Render docs/erd.mmd ra reports/tai_lieu/erd.png; dự phòng copy từ docs/erd.png theo mục 10 của 05-giao-viec-agy.md."""
    THU_MUC_TAI_LIEU.mkdir(parents=True, exist_ok=True)
    erd_mmd = GOC / "docs" / "erd.mmd"
    erd_out = THU_MUC_TAI_LIEU / "erd.png"
    erd_fallback = GOC / "docs" / "erd.png"

    mmdc_bin = GOC / "node_modules" / ".bin" / ("mmdc.cmd" if os.name == "nt" else "mmdc")
    if mmdc_bin.exists():
        try:
            subprocess.run([str(mmdc_bin), "-i", str(erd_mmd), "-o", str(erd_out)],
                           check=True, timeout=30, capture_output=True)
            if erd_out.exists() and erd_out.stat().st_size > 0:
                return "rendered_mmdc"
        except Exception:
            pass

    if erd_fallback.exists():
        shutil.copy2(erd_fallback, erd_out)
        return "copied_from_docs_erd_png"

    raise RuntimeError("Không thể tạo reports/tai_lieu/erd.png")


def trich_vai_tro_va_mo_ta_tu_ast():
    """Đọc AST của server/routes/*.py để lấy vai trò @yeu_cau_vai_tro(...) và docstring của mỗi hàm xử lý."""
    thong_tin = {}
    routes_dir = GOC / "server" / "routes"
    for py_file in sorted(routes_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        bp_name = py_file.stem
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                vai_tro = "*"
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call):
                        func = dec.func
                        func_name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
                        if func_name == "yeu_cau_vai_tro" and dec.args:
                            args_vals = [
                                a.value for a in dec.args if isinstance(a, ast.Constant)
                            ]
                            if args_vals:
                                vai_tro = ", ".join(str(v) for v in args_vals)
                doc = (ast.get_docstring(node) or "").strip()
                dong_doc = [d.strip() for d in doc.splitlines() if d.strip()]
                mo_ta = dong_doc[1] if len(dong_doc) > 1 else (dong_doc[0] if dong_doc else "")
                thong_tin[f"{bp_name}.{node.name}"] = (vai_tro, mo_ta)
    return thong_tin


def xuat_api_md():
    """Introspect Flask app.url_map kết hợp AST để sinh reports/tai_lieu/api.md."""
    THU_MUC_TAI_LIEU.mkdir(parents=True, exist_ok=True)
    from server.app import app

    ast_info = trich_vai_tro_va_mo_ta_tu_ast()
    DIEN_GIAI_VAI_TRO = {
        "*": "Công khai (`*` — mọi vai trò, kể cả khách)",
        "nguoi_dung": "Bạn đọc đã đăng nhập (`sinh_vien`, `giang_vien`)",
        "thu_thu": "Thủ thư / Quản trị (`thu_thu`, `admin`)",
    }

    routes = []
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith("/api") or rule.rule in ("/api", "/api/"):
            continue
        methods = sorted(m for m in rule.methods if m not in ("HEAD", "OPTIONS"))
        vai_tro_raw, mo_ta = ast_info.get(rule.endpoint, ("*", ""))
        routes.append((rule.rule, ", ".join(methods), rule.endpoint, vai_tro_raw, mo_ta))

    # Gộp các route trùng endpoint như /api/muon và /api/muon/
    da_gop = []
    seen = set()
    for path_str, methods, endpoint, vai_tro_raw, mo_ta in sorted(routes, key=lambda x: (x[2], len(x[0]))):
        if endpoint in seen and path_str.endswith("/"):
            continue
        seen.add(endpoint)
        da_gop.append((methods, path_str, endpoint, vai_tro_raw, mo_ta))

    da_gop.sort(key=lambda x: x[1])

    dong = [
        "# Danh sách API Backend (`server/app.py` — Python Flask)",
        "",
        "> Tài liệu được trích xuất tự động từ `app.url_map` và decorator `@yeu_cau_vai_tro(...)` trong `server/routes/*.py`.",
        "",
        "## 1. Quy ước phân quyền (`server/auth.py`)",
        "",
        "- `@yeu_cau_vai_tro('*')`: Tuyến công khai, khách vãng lai chưa đăng nhập cũng gọi được (hệ thống tự cấp `session['ma_phien']`).",
        "- `@yeu_cau_vai_tro('nguoi_dung')`: Yêu cầu đã đăng nhập với vai trò `sinh_vien` hoặc `giang_vien` (chưa đăng nhập trả `401`, sai vai trò trả `403`).",
        "- `@yeu_cau_vai_tro('thu_thu')`: Yêu cầu đã đăng nhập với vai trò `thu_thu` hoặc `admin` (chưa đăng nhập trả `401`, sai vai trò trả `403`).",
        "",
        "## 2. Bảng tổng hợp các Endpoint API",
        "",
        "| # | Phương thức | Đường dẫn (Route) | Endpoint Flask | Vai trò được phép | Mô tả chức năng |",
        "|---:|:---:|---|---|---|---|",
    ]

    for i, (methods, path_str, endpoint, vai_tro_raw, mo_ta) in enumerate(da_gop, 1):
        vt_hien_thi = DIEN_GIAI_VAI_TRO.get(vai_tro_raw, f"`{vai_tro_raw}`")
        dong.append(f"| {i} | `{methods}` | `{path_str}` | `{endpoint}` | {vt_hien_thi} | {mo_ta} |")

    dong.append("")
    (THU_MUC_TAI_LIEU / "api.md").write_text("\n".join(dong), encoding="utf-8")


def main():
    THU_MUC_BAO_CAO.mkdir(parents=True, exist_ok=True)
    THU_MUC_TAI_LIEU.mkdir(parents=True, exist_ok=True)
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("Thiếu biến môi trường DATABASE_URL trong .env")

    with psycopg2.connect(db_url) as conn, conn.cursor() as cur:
        print("[1/4] Xuất 5 tệp số liệu CSV (reports/so_lieu/*.csv) và 5 biểu đồ Matplotlib (reports/bieu_do/*.png)...")
        xuat_so_lieu_va_bieu_do(cur)

        print("[2/4] Xuất từ điển dữ liệu từ information_schema (reports/tai_lieu/tu_dien_du_lieu.md)...")
        xuat_tu_dien_du_lieu(cur)

    print("[3/4] Xuất sơ đồ ERD (reports/tai_lieu/erd.png)...")
    erd_mode = xuat_erd_png()
    print(f"      Trạng thái ERD: {erd_mode}")

    print("[4/4] Xuất tài liệu đặc tả API từ code Flask (reports/tai_lieu/api.md)...")
    xuat_api_md()

    print("Hoàn tất xuất toàn bộ báo cáo tại thư mục reports/!")


if __name__ == "__main__":
    main()
