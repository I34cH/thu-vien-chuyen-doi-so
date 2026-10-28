# /boost — chỉ dùng khi kẹt (Argon, effort medium)

Phiên: `agy --model <ARGON> --effort medium`, gõ `/boost` + một khung dưới đây, điền phần <...>.

## Khung chung
Lỗi: <dán thông báo lỗi / test fail nguyên văn>
Đã thử: <các lần sửa trong /goal và vì sao chưa được>
Ràng buộc: tuân theo AGENTS.md, không đổi công nghệ, không thêm tính năng.
Yêu cầu: tìm nguyên nhân gốc, đề xuất 2 cách sửa, chọn 1, sửa, chạy lại lệnh kiểm chứng của milestone, giải thích ngắn trong reports/milestones/<Mx>.md mục "Boost".

## Các lỗi dễ gặp, đã dự đoán
1. **Tìm không dấu/sai chính tả cho kết quả kém**: `unaccent` không IMMUTABLE nên không dùng được trong index → cần hàm bọc `f_unaccent` IMMUTABLE; cân bằng giữa full-text (`simple` config) và trigram `similarity > 0.3`; xếp hạng kết hợp `ts_rank` + `similarity`.
2. **Đọc Excel lệch cột**: sheet LA và S-TV có dòng số thứ tự cột ở dòng 2; sheet LV/KH có cột thừa cuối; ô gộp/xuống dòng trong tên GVHD (`\n`).
3. **Log Zipf trông không thật**: kiểm tra đồ thị log-log có gần thẳng, tỉ lệ 0 kết quả trong khoảng 10–20%, phân bố theo ngày có chu kỳ tuần.
4. **Dashboard chậm khi log lớn**: dùng view tổng hợp hoặc materialized view, index `thoi_diem`, giới hạn khoảng ngày.
5. **Session/phân quyền lệch giữa test và trình duyệt**: cookie `sameSite`, `credentials: 'include'` trong fetch, thứ tự middleware.
6. **Playwright trên Windows**: cần `npx playwright install chromium` một lần; server phải khởi động trước test (`webServer` trong config).
