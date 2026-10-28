-- =====================================================================
-- Schema CSDL web thư viện chuyển đổi số (theo docs/erd.mmd)
-- Chạy lại được nhiều lần: xóa bảng cũ rồi tạo mới.
-- =====================================================================
SET client_min_messages = warning;

CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

DROP VIEW IF EXISTS v_tu_khoa_top, v_tim_theo_ngay, v_khong_ket_qua, v_nen_so_hoa, v_tinh_trang_tai_lieu CASCADE;
DROP TABLE IF EXISTS log_tim_kiem, luot_muon, ban_sao, nguoi_dung, tai_lieu, ma_van_de CASCADE;
DROP FUNCTION IF EXISTS tim_tai_lieu(text) CASCADE;

-- Bỏ dấu tiếng Việt, khai báo IMMUTABLE để dùng được trong index / cột sinh
CREATE OR REPLACE FUNCTION f_unaccent(text) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT AS
$$ SELECT public.unaccent('public.unaccent'::regdictionary, $1) $$;

-- Chuẩn hóa truy vấn: bỏ dấu, chữ thường, gộp khoảng trắng
CREATE OR REPLACE FUNCTION f_chuan_hoa(text) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT AS
$$ SELECT lower(f_unaccent(regexp_replace(btrim($1), '\s+', ' ', 'g'))) $$;

CREATE TABLE ma_van_de (
  ma  varchar(20) PRIMARY KEY,
  ten varchar(200)                 -- chưa có bảng giải nghĩa: để NULL
);

CREATE TABLE tai_lieu (
  id                serial PRIMARY KEY,
  ky_hieu           varchar(40) NOT NULL UNIQUE,
  loai_hinh         varchar(30) NOT NULL,
  tieu_de           text NOT NULL,
  tac_gia           varchar(500),
  gvhd              varchar(500),
  co_quan           varchar(500),
  nxb               varchar(500),
  nam               int,
  nam_goc           varchar(60),
  ma_van_de         varchar(20) REFERENCES ma_van_de(ma),
  khoa_hoc          varchar(40),
  he                varchar(40),
  ghi_chu           text,
  khong_co_tl       boolean NOT NULL DEFAULT false,
  co_ban_mem        boolean NOT NULL DEFAULT false,
  muc_truy_cap      varchar(20) CHECK (muc_truy_cap IN ('cong_khai', 'noi_bo')),
  duong_dan_ban_mem varchar(300),
  tsv               tsvector GENERATED ALWAYS AS (
                      to_tsvector('simple', f_chuan_hoa(coalesce(tieu_de, '') || ' ' || coalesce(tac_gia, '')))
                    ) STORED,
  sheet_goc         varchar(60) NOT NULL,
  dong_goc          int NOT NULL
);
CREATE INDEX idx_tai_lieu_tsv ON tai_lieu USING gin (tsv);
CREATE INDEX idx_tai_lieu_trgm ON tai_lieu USING gin (f_unaccent(lower(tieu_de)) gin_trgm_ops);
CREATE INDEX idx_tai_lieu_loai ON tai_lieu (loai_hinh);

CREATE TABLE ban_sao (
  id          serial PRIMARY KEY,
  tai_lieu_id int NOT NULL REFERENCES tai_lieu(id) ON DELETE CASCADE,
  ma_ban_sao  varchar(60) NOT NULL UNIQUE,
  trang_thai  varchar(20) NOT NULL DEFAULT 'con' CHECK (trang_thai IN ('con', 'dang_muon', 'mat')),
  du_lieu_mau boolean NOT NULL DEFAULT false
);
CREATE INDEX idx_ban_sao_tl ON ban_sao (tai_lieu_id);

CREATE TABLE nguoi_dung (
  id            serial PRIMARY KEY,
  ten_dang_nhap varchar(60) NOT NULL UNIQUE,
  mat_khau_hash varchar(100) NOT NULL,
  ho_ten        varchar(200) NOT NULL,
  vai_tro       varchar(20) NOT NULL CHECK (vai_tro IN ('sinh_vien', 'giang_vien', 'thu_thu', 'admin')),
  du_lieu_mau   boolean NOT NULL DEFAULT false
);

CREATE TABLE luot_muon (
  id            serial PRIMARY KEY,
  nguoi_dung_id int NOT NULL REFERENCES nguoi_dung(id),
  tai_lieu_id   int NOT NULL REFERENCES tai_lieu(id),
  ban_sao_id    int REFERENCES ban_sao(id),           -- NULL khi chờ duyệt
  trang_thai    varchar(20) NOT NULL DEFAULT 'cho_duyet'
                CHECK (trang_thai IN ('cho_duyet', 'dang_muon', 'da_tra', 'tu_choi')),
  ngay_dang_ky  timestamptz NOT NULL DEFAULT now(),
  ngay_muon     date,
  han_tra       date,
  ngay_tra      date,
  du_lieu_mau   boolean NOT NULL DEFAULT false
);
CREATE INDEX idx_luot_muon_tl ON luot_muon (tai_lieu_id);
CREATE INDEX idx_luot_muon_tt ON luot_muon (trang_thai);

CREATE TABLE log_tim_kiem (
  id               bigserial PRIMARY KEY,
  tu_khoa          text NOT NULL,
  tu_khoa_chuan    text NOT NULL,                      -- f_chuan_hoa(tu_khoa)
  so_ket_qua       int NOT NULL,
  tai_lieu_chon_id int REFERENCES tai_lieu(id),
  thoi_diem        timestamptz NOT NULL DEFAULT now(),
  nguoi_dung_id    int REFERENCES nguoi_dung(id),      -- NULL nếu khách
  ma_phien         varchar(64),
  du_lieu_mau      boolean NOT NULL DEFAULT false
);
CREATE INDEX idx_log_tu_khoa_chuan ON log_tim_kiem (tu_khoa_chuan);
CREATE INDEX idx_log_thoi_diem ON log_tim_kiem (thoi_diem);
CREATE INDEX idx_log_chon ON log_tim_kiem (tai_lieu_chon_id);

-- ---------------------------------------------------------------------
-- Hàm tìm kiếm dùng chung cho API và script sinh dữ liệu:
--  * full-text trên tiêu đề + tác giả đã bỏ dấu (gõ không dấu vẫn ra)
--  * word_similarity trigram trên tiêu đề (chấp nhận sai chính tả nhẹ)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION tim_tai_lieu(p_q text)
RETURNS TABLE (tai_lieu_id int, diem real)
LANGUAGE sql STABLE AS
$$
  WITH q AS (
    SELECT f_chuan_hoa(p_q) AS qn, plainto_tsquery('simple', f_chuan_hoa(p_q)) AS tq
  )
  SELECT t.id,
         (ts_rank(t.tsv, q.tq) * 2 + word_similarity(q.qn, f_unaccent(lower(t.tieu_de))))::real
  FROM tai_lieu t, q
  WHERE length(q.qn) >= 2
    AND (t.tsv @@ q.tq OR q.qn <% f_unaccent(lower(t.tieu_de)))
$$;

-- Tạo các view tổng hợp
\ir views.sql
