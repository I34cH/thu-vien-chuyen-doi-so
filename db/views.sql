-- =====================================================================
-- View tổng hợp cho dashboard (chỉ số liệu tổng hợp, không lộ ai tìm gì)
-- =====================================================================

-- Số bản sao và số bản còn rảnh của từng tư liệu
CREATE OR REPLACE VIEW v_tinh_trang_tai_lieu AS
SELECT t.id AS tai_lieu_id,
       count(b.id) FILTER (WHERE b.trang_thai <> 'mat')::int AS so_ban,
       count(b.id) FILTER (WHERE b.trang_thai = 'con')::int  AS so_ban_con
FROM tai_lieu t
LEFT JOIN ban_sao b ON b.tai_lieu_id = t.id
GROUP BY t.id;

-- Từ khóa theo cả cụm đã chuẩn hóa; hien_thi = cách gõ phổ biến nhất (có dấu)
CREATE OR REPLACE VIEW v_tu_khoa_top AS
SELECT tu_khoa_chuan,
       mode() WITHIN GROUP (ORDER BY lower(regexp_replace(btrim(tu_khoa), '\s+', ' ', 'g'))) AS hien_thi,
       count(*)::int AS so_lan,
       count(*) FILTER (WHERE so_ket_qua = 0)::int AS so_lan_0_kq
FROM log_tim_kiem
GROUP BY tu_khoa_chuan
ORDER BY so_lan DESC;

-- Lượt tìm theo ngày
CREATE OR REPLACE VIEW v_tim_theo_ngay AS
SELECT thoi_diem::date AS ngay,
       count(*)::int AS so_luot,
       count(*) FILTER (WHERE so_ket_qua = 0)::int AS so_luot_0_kq
FROM log_tim_kiem
GROUP BY 1
ORDER BY 1;

-- Từ khóa được tìm nhưng không có kết quả -> gợi ý mua/bổ sung
CREATE OR REPLACE VIEW v_khong_ket_qua AS
SELECT tu_khoa_chuan,
       mode() WITHIN GROUP (ORDER BY lower(regexp_replace(btrim(tu_khoa), '\s+', ' ', 'g'))) AS hien_thi,
       count(*)::int AS so_lan,
       max(thoi_diem) AS lan_cuoi
FROM log_tim_kiem
WHERE so_ket_qua = 0
GROUP BY tu_khoa_chuan
ORDER BY so_lan DESC;

-- Tư liệu nên số hóa: diem = so_lan_chon + 2 * so_luot_muon
CREATE OR REPLACE VIEW v_nen_so_hoa AS
WITH chon AS (
  SELECT tai_lieu_chon_id AS tai_lieu_id, count(*)::int AS so_lan_chon
  FROM log_tim_kiem WHERE tai_lieu_chon_id IS NOT NULL GROUP BY 1
), muon AS (
  SELECT tai_lieu_id, count(*)::int AS so_luot_muon
  FROM luot_muon WHERE trang_thai <> 'tu_choi' GROUP BY 1
)
SELECT t.id AS tai_lieu_id, t.ky_hieu, t.tieu_de, t.tac_gia, t.loai_hinh, t.nam,
       coalesce(c.so_lan_chon, 0) AS so_lan_chon,
       coalesce(m.so_luot_muon, 0) AS so_luot_muon,
       coalesce(c.so_lan_chon, 0) + 2 * coalesce(m.so_luot_muon, 0) AS diem
FROM tai_lieu t
LEFT JOIN chon c ON c.tai_lieu_id = t.id
LEFT JOIN muon m ON m.tai_lieu_id = t.id
WHERE t.co_ban_mem = false
  AND t.khong_co_tl = false
  AND coalesce(c.so_lan_chon, 0) + coalesce(m.so_luot_muon, 0) > 0
ORDER BY diem DESC, t.id;
