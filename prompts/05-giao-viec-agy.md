# Giao việc cho đội agy (Claude Opus → Argon), 2026-10-27

Bạn là Argon (điều phối). Claude Opus là tổng chỉ huy và sẽ audit cuối. Đọc `AGENTS.md`, `docs/erd.mmd`, `prompts/01-teamwork.md` trước. Bên dưới là TRẠNG THÁI HIỆN TẠI và LƯU Ý KỸ THUẬT. Phần này ưu tiên hơn `01-teamwork.md` khi hai bên khác nhau.

> **CẬP NHẬT 2026-10-28:** backend chuyển sang **Python Flask** (AGENTS.md mục 2, chặng M3b). Các lưu ý 1–3, 5–7 bên dưới vẫn đúng về nghiệp vụ; thay Express/`yeuCauVaiTro`/supertest/multer bằng Flask/`yeu_cau_vai_tro`/pytest/upload của Flask.

## Phân vai
- Bạn (Argon): chia việc, tích hợp, quyết định. Không tự viết phần lớn code.
- Subagent: dùng `invoke_subagent` với `Model: "flash"` (dòng Gemini Flash). Có 3 vai riêng là implement, test và audit. Subagent đã implement phần nào thì không được tự audit phần đó.
- Vòng kiểm chứng của mỗi milestone: implement → test chạy LỆNH KIỂM CHỨNG → sửa → chạy lại → audit → ghi `reports/milestones/Mx.md` kèm output nguyên văn. Nếu quá 3 vòng vẫn chưa pass thì dùng cách /boost: tìm nguyên nhân gốc, đưa ra 2 cách sửa, chọn 1 cách.

## Trạng thái
- **M1: PASS, do Opus làm. KHÔNG làm lại.** Các file `db/schema.sql` (có `\ir views.sql` ở cuối), `db/views.sql`, `scripts/etl_import.py` và `reports/milestones/M1.md` đã có. Database `thu_vien_ck` đã có, `.env` đã có `DATABASE_URL`.
  - Hàm SQL dùng chung `tim_tai_lieu(q text) → (tai_lieu_id, diem)` gồm full-text không dấu và trigram `word_similarity`. **API và seed BẮT BUỘC dùng hàm này** để `so_ket_qua` trong log khớp với kết quả thật.
  - `f_chuan_hoa(text)` là hàm chuẩn hóa từ khóa, dùng cho `tu_khoa_chuan`.
  - Có thể sửa schema nếu cần, nhưng sau khi sửa phải chạy lại lệnh kiểm chứng M1.
- **M2: đã có bản nháp `scripts/seed_demo.py`, CHƯA chạy xong.** Có một lỗi hiệu năng đã biết:
  `cum_that = [c for c in trich_cum_tu(...) if ket_qua(c)[0] > 0][:SO_TU_KHOA_THAT]` gọi CSDL cho MỌI cụm từ (hàng nghìn cụm) trước khi cắt. Cần sửa thành duyệt lười và dừng khi đủ 220 cụm. Sau đó chạy lệnh kiểm chứng M2: schema → ETL → seed, chạy 2 lần, số dòng phải giống hệt nhau, có log 0 kết quả, có `reports/seed/seed_tom_tat.md` và `reports/seed/zipf.png`. Mục tiêu tỉ lệ 0 kết quả là 10–20%. Nếu lệch thì chỉnh rồi ghi lại trong M2.md.
- **M3: mới có `package.json`, đã chạy `npm install`** (express 4, pg, express-session, bcrypt 6 chạy được trên Node 24, multer 2, dotenv, supertest, @playwright/test). Các thư mục `server/routes`, `server/middleware`, `tests/api` đang trống. Script `npm test` là `python -m pytest tests/api -q`.
- M4, M5, M6: chưa làm.

## Lưu ý kỹ thuật (Opus đã chốt)
1. `server/app.js` export `app` và chỉ `listen` khi chạy trực tiếp, để supertest dùng được. Phục vụ file tĩnh từ `public/`.
2. `yeuCauVaiTro(...)`: `'*'` = ai cũng vào được (route công khai cũng phải khai báo rõ). `'nguoi_dung'` = sinh_vien|giang_vien. `'thu_thu'` = thu_thu|admin. Chưa đăng nhập trả 401, sai vai trò trả 403.
3. `GET /api/tim-kiem` chỉ ghi log khi `q` không rỗng VÀ đang ở trang 1, để phân trang không tạo log trùng. `ma_phien` = `req.sessionID`; phải gán một giá trị vào session để cookie được phát cho khách. `POST /tim-kiem/:logId/chon` chỉ cập nhật khi log thuộc đúng `ma_phien` hiện tại.
4. `/api/thong-ke/*` chỉ dành cho thu_thu (test yêu cầu nguoi_dung nhận 403). Số liệu trên trang chủ lấy từ một route công khai riêng, ví dụ `GET /api/gioi-thieu`, chỉ trả số đếm danh mục (tổng tư liệu, số theo loại hình, số đã số hóa), không có số liệu log.
5. Duyệt mượn chạy trong transaction: `SELECT ... FOR UPDATE` bản sao `con`; không còn bản sao thì trả 409. Trả tư liệu thì đưa bản sao về `con`.
6. Upload bản mềm: chỉ nhận PDF (kiểm tra cả mimetype lẫn 4 byte đầu `%PDF`), tối đa 20MB, lưu vào `uploads/`, set `co_ban_mem = true` và `muc_truy_cap`. Seed đã tạo sẵn `uploads/mau/ban_mem_mau.pdf` cho 40 tư liệu "đã số hóa mẫu".
7. Test API phải tự dọn dữ liệu đã tạo (lượt mượn, log) trong `after()` để chạy lại nhiều lần vẫn pass.
8. Frontend: bỏ ảnh Unsplash và số liệu giả của tt_gk. Mọi số liệu lấy từ API, ngược lại thì ẩn. CDN: Chart.js `https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js`, wordcloud2 `https://cdnjs.cloudflare.com/ajax/libs/wordcloud2.js/1.2.2/wordcloud2.min.js`. Kiểm tra URL tải được; nếu không được thì chọn bản đúng trên cdnjs và ghi rõ phiên bản. Font Awesome 6.4.0 giữ như tt_gk.
9. Playwright: chạy `npx playwright install chromium` một lần. `playwright.config.js` có `webServer: npm start` (cổng 3000). Đặt test UI ở `tests/ui/ui.spec.js`.
10. Mermaid: nếu `npx @mermaid-js/mermaid-cli` lỗi trên máy này thì copy `docs/erd.png` sang `reports/tai_lieu/erd.png` và ghi lại trong M6.md.

## Giới hạn an toàn
- Chỉ ghi file trong `D:\Courses\datavisualize\btth\CK`. KHÔNG sửa `D:\Courses\Web\tt_gk` (chỉ đọc và copy). KHÔNG sửa hay xóa `data/`.
- Chỉ làm việc với database `thu_vien_ck`. Không đụng database khác, không đổi mật khẩu, không cài dịch vụ hệ thống.
- Không commit hay push git, không xuất bản gì ra ngoài.
- Không in mật khẩu DB ra báo cáo (dùng `$DATABASE_URL`).

## Kết thúc
Làm M2 → M6 theo `prompts/01-teamwork.md`. Cuối cùng tạo `reports/TONG_KET.md`: bảng milestone (trạng thái, số vòng sửa), các điểm lệch so với AGENTS.md kèm lý do, lỗi còn tồn tại. KHÔNG báo hoàn thành nếu còn lệnh kiểm chứng chưa pass. Opus sẽ chạy lại toàn bộ lệnh kiểm chứng khi audit.
