    document.addEventListener('DOMContentLoaded', () => {
      // 1. Kích hoạt Autocomplete ở ô tìm kiếm trang chủ
      const input = document.getElementById('heroSearchInput');
      const dropdown = document.getElementById('heroAutocompleteResults');
      if (input && dropdown) {
        window.LibraryApp.initAutocomplete(input, dropdown);
      }

      // 2. Tab chuyển loại hình trên trang chủ
      const tabs = document.querySelectorAll('.opac-tab-btn');
      const selectLoai = document.getElementById('heroSelectLoai');
      tabs.forEach(tab => {
        tab.addEventListener('click', () => {
          tabs.forEach(t => t.classList.remove('active'));
          tab.classList.add('active');
          const loai = tab.getAttribute('data-loai') || '';
          if (selectLoai) selectLoai.value = loai;
        });
      });

      // 3. Tải số liệu thống kê thật từ /api/gioi-thieu (AGENTS.md mục 4 / prompts 05-giao-viec)
      fetch('/api/gioi-thieu', { credentials: 'same-origin' })
        .then(res => res.json())
        .then(data => {
          if (data.thanh_cong) {
            document.getElementById('statTongTaiLieu').textContent = Number(data.tong_tai_lieu).toLocaleString('vi-VN');
            document.getElementById('statDaSoHoa').textContent = Number(data.so_da_so_hoa).toLocaleString('vi-VN');
            document.getElementById('statCoBanCung').textContent = Number(data.co_ban_cung).toLocaleString('vi-VN');
            if (data.theo_loai_hinh && data.theo_loai_hinh.length > 0) {
              document.getElementById('statSoLoaiHinh').textContent = data.theo_loai_hinh.length;
            }
          }
        })
        .catch(err => console.warn('Lỗi lấy thống kê giới thiệu:', err));

      // 4. Tải một số tư liệu tiêu biểu thật từ /api/tim-kiem (Bỏ hoàn toàn Unsplash)
      fetch('/api/tim-kiem?gioi_han=6', { credentials: 'same-origin' })
        .then(res => res.json())
        .then(resData => {
          const grid = document.getElementById('homeBooksGrid');
          if (!grid) return;
          const items = resData.du_lieu || [];
          if (items.length === 0) {
            grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--color-text-muted);">Chưa có tư liệu nào trong danh mục.</p>';
            return;
          }

          let html = '';
          items.forEach(doc => {
            const loai = window.LibraryApp.formatLoaiHinh(doc.loai_hinh);
            const tacGia = doc.tac_gia ? window.LibraryApp.escapeHtml(doc.tac_gia) : 'Nhiều tác giả';
            const tieuDe = window.LibraryApp.escapeHtml(doc.tieu_de);
            const nam = doc.nam ? doc.nam : '---';
            const kyHieu = doc.ky_hieu ? window.LibraryApp.escapeHtml(doc.ky_hieu) : 'TL';
            const conLai = doc.so_ban_con != null ? doc.so_ban_con : 0;
            const tongBan = doc.so_ban != null ? doc.so_ban : 0;

            let statusHtml = '';
            if (doc.khong_co_tl) {
              statusHtml = '<span class="book-status" style="color: var(--color-text-muted);"><span class="status-dot red"></span> Không có TL</span>';
            } else if (conLai > 0) {
              statusHtml = `<span class="book-status"><span class="status-dot green"></span> Còn ${conLai}/${tongBan} bản</span>`;
            } else {
              statusHtml = '<span class="book-status" style="color: var(--status-danger);"><span class="status-dot red"></span> Hết bản cứng</span>';
            }

            const softCopyBadge = doc.co_ban_mem
              ? '<span class="badge badge-softcopy" style="margin-left: 4px;"><i class="fa-solid fa-file-pdf"></i> Có bản mềm</span>'
              : '';

            html += `
              <div class="book-card">
                <div class="book-card-figure">
                  <div class="book-cover-placeholder">
                    <i class="fa-solid fa-book-bookmark"></i>
                    <span class="cover-label">${loai}</span>
                  </div>
                  <span class="book-tag">${nam}</span>
                </div>
                <div class="book-card-body">
                  <span class="book-call-number">${kyHieu}</span>
                  <h3 class="book-title"><a href="chi-tiet.html?id=${doc.id}">${tieuDe}</a></h3>
                  <p class="book-author"><i class="fa-regular fa-user"></i> ${tacGia}</p>
                  <div style="margin-bottom: 8px;">${softCopyBadge}</div>
                  <div class="book-card-footer">
                    ${statusHtml}
                    <a href="chi-tiet.html?id=${doc.id}" style="font-weight: 600; color: var(--color-primary); font-size: 0.8rem;">
                      Chi tiết <i class="fa-solid fa-arrow-right"></i>
                    </a>
                  </div>
                </div>
              </div>
            `;
          });
          grid.innerHTML = html;
        })
        .catch(err => {
          console.warn('Lỗi tải danh mục nổi bật:', err);
          const grid = document.getElementById('homeBooksGrid');
          if (grid) grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--color-text-muted);">Không thể tải danh mục tư liệu.</p>';
        });
    });
  
