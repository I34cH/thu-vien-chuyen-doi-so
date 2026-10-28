# Opus final audit — gửi gì về cho Claude

Sau khi M6 xong (hoặc khi muốn kiểm giữa chừng), quay lại cuộc trò chuyện với Claude và nhắn:

> "Audit bản build web thư viện trong thư mục CK."

Claude sẽ tự đọc thư mục CK trên máy (đã được cấp quyền) và kiểm:
1. `reports/TONG_KET.md` và `reports/milestones/M1..M6.md`: output lệnh kiểm chứng có thật sự pass không.
2. Đối chiếu code với AGENTS.md: phạm vi, phân quyền từng route, SQL tham số, thống kê không lộ người tìm, banner dữ liệu mẫu, màu đỏ.
3. Số liệu: ETL có mất dòng bất thường không (`reports/etl/etl_tom_tat.csv`), log có đúng hình Zipf (`reports/seed/zipf.png`), KPI khớp SQL.
4. Giao diện: xem `reports/screenshots/` theo 3 vai trò, desktop và mobile.
5. Sẵn sàng demo: README có kịch bản 5 phút, `demo:reset` chạy lại được.

Kết quả audit sẽ là một trong ba: **Chấp nhận** · **Yêu cầu sửa** (kèm danh sách /goal cụ thể) · **Trả về lập kế hoạch** (nếu lệch đặc tả lớn).
Sau khi chấp nhận, Claude dựng khung báo cáo cuối kì từ thư mục `reports/`.
