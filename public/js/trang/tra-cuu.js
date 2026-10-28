    document.addEventListener('DOMContentLoaded', () => {
      let currentLogId = null;
      let currentPage = 1;

      const input = document.getElementById('catalogSearchInput');
      const dropdown = document.getElementById('catalogAutocompleteResults');
      if (input && dropdown) {
        window.LibraryApp.initAutocomplete(input, dropdown);
      }

      // Đọc query parameters từ URL
      const urlParams = new URLSearchParams(window.location.search);
      const initialQ = urlParams.get('q') || '';
      const initialLoai = urlParams.get('loai') || '';
      const initialTuNam = urlParams.get('tu_nam') || '';
      const initialDenNam = urlParams.get('den_nam') || '';
      const initialTrang = parseInt(urlParams.get('trang'), 10) || 1;

      input.value = initialQ;
      document.getElementById('catalogLoaiSelect').value = initialLoai;
      
      const radio = Array.from(document.querySelectorAll('input[name="filterLoaiRadio"]')).find(r => r.value === initialLoai);
      if (radio) radio.checked = true;

      if (initialTuNam) document.getElementById('filterTuNam').value = initialTuNam;
      if (initialDenNam) document.getElementById('filterDenNam').value = initialDenNam;

      // Thực hiện tìm kiếm ban đầu
      loadCatalog(initialTrang);

      // Xử lý gửi form tìm kiếm
      document.getElementById('searchCatalogForm').addEventListener('submit', (e) => {
        e.preventDefault();
        currentPage = 1;
        syncFormToFilters();
        loadCatalog(1);
      });

      // Thay đổi select loại hình trên thanh tìm kiếm
      document.getElementById('catalogLoaiSelect').addEventListener('change', (e) => {
        const val = e.target.value;
        const rad = Array.from(document.querySelectorAll('input[name="filterLoaiRadio"]')).find(r => r.value === val);
        if (rad) rad.checked = true;
      });

      // Thay đổi radio loại hình bên sidebar
      const radios = document.querySelectorAll('input[name="filterLoaiRadio"]');
      radios.forEach(r => {
        r.addEventListener('change', (e) => {
          document.getElementById('catalogLoaiSelect').value = e.target.value;
        });
      });

      // Áp dụng bộ lọc
      document.getElementById('btnApplyFilter').addEventListener('click', () => {
        currentPage = 1;
        loadCatalog(1);
      });

      // Đặt lại bộ lọc
      document.getElementById('btnResetFilter').addEventListener('click', () => {
        input.value = '';
        document.getElementById('catalogLoaiSelect').value = '';
        const defaultRadio = Array.from(document.querySelectorAll('input[name="filterLoaiRadio"]')).find(r => r.value === '');
        if (defaultRadio) defaultRadio.checked = true;
        document.getElementById('filterTuNam').value = '';
        document.getElementById('filterDenNam').value = '';
        currentLogId = null;
        currentPage = 1;
        loadCatalog(1);
      });

      // Đổi số bản ghi mỗi trang
      document.getElementById('selectPageSize').addEventListener('change', () => {
        currentPage = 1;
        loadCatalog(1);
      });

      function syncFormToFilters() {
        const selectLoai = document.getElementById('catalogLoaiSelect').value;
        const rad = Array.from(document.querySelectorAll('input[name="filterLoaiRadio"]')).find(r => r.value === selectLoai);
        if (rad) rad.checked = true;
      }

      async function loadCatalog(trang = 1) {
        currentPage = trang;
        const q = input.value.trim();
        const loai = document.getElementById('catalogLoaiSelect').value;
        const tuNam = document.getElementById('filterTuNam').value.trim();
        const denNam = document.getElementById('filterDenNam').value.trim();
        const pageSize = document.getElementById('selectPageSize').value;

        // Cập nhật URL trình duyệt (không reload)
        const params = new URLSearchParams();
        if (q) params.set('q', q);
        if (loai) params.set('loai', loai);
        if (tuNam) params.set('tu_nam', tuNam);
        if (denNam) params.set('den_nam', denNam);
        if (trang > 1) params.set('trang', trang);
        const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`;
        window.history.replaceState({}, '', newUrl);

        const container = document.getElementById('resultsListContainer');
        container.innerHTML = `
          <div style="text-align: center; padding: 40px; color: var(--color-text-muted);">
            <i class="fa-solid fa-spinner fa-spin fa-2x"></i>
            <p style="margin-top: 12px;">Đang tìm kiếm dữ liệu...</p>
          </div>
        `;

        try {
          const fetchParams = new URLSearchParams({
            trang: trang,
            gioi_han: pageSize
          });
          if (q) fetchParams.set('q', q);
          if (loai) fetchParams.set('loai', loai);
          if (tuNam) fetchParams.set('tu_nam', tuNam);
          if (denNam) fetchParams.set('den_nam', denNam);

          const res = await fetch(`/api/tim-kiem?${fetchParams.toString()}`, {
            method: 'GET',
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
          });
          const data = await res.json();

          if (!data.thanh_cong) throw new Error(data.error || 'Lỗi tra cứu');

          // Cập nhật logId từ lượt tìm kiếm: nếu ở trang 1, gán data.log_id hoặc null nếu không có từ khóa
          if (trang === 1) {
            currentLogId = data.log_id || null;
          } else if (data.log_id) {
            currentLogId = data.log_id;
          }

          renderResults(data, q);
          renderPagination(data);
        } catch (err) {
          console.error('Lỗi khi tải kết quả tra cứu:', err);
          container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: var(--status-danger);">
              <i class="fa-solid fa-circle-exclamation fa-2x"></i>
              <p style="margin-top: 12px;">Đã xảy ra lỗi khi tìm kiếm: ${window.LibraryApp.escapeHtml(err.message)}</p>
            </div>
          `;
        }
      }

      function renderResults(data, q) {
        const container = document.getElementById('resultsListContainer');
        const summary = document.getElementById('searchSummaryText');
        const items = data.du_lieu || [];
        const tongSo = data.tong_so || 0;

        if (q) {
          summary.innerHTML = `Tìm thấy <strong>${tongSo.toLocaleString('vi-VN')}</strong> kết quả cho từ khóa "<em>${window.LibraryApp.escapeHtml(q)}</em>"`;
        } else {
          summary.innerHTML = `Hiển thị <strong>${items.length}</strong> / <strong>${tongSo.toLocaleString('vi-VN')}</strong> tư liệu trong danh mục`;
        }

        if (items.length === 0) {
          container.innerHTML = `
            <div style="background: #fff; border: 1px dashed var(--color-border); border-radius: var(--radius-md); text-align: center; padding: 50px 20px;">
              <i class="fa-solid fa-box-open" style="font-size: 3rem; color: #cbd5e1; margin-bottom: 16px;"></i>
              <h4 style="font-size: 1.1rem; color: var(--color-text-main); margin-bottom: 8px;">Không tìm thấy tư liệu nào phù hợp</h4>
              <p style="color: var(--color-text-muted); font-size: 0.9rem;">Vui lòng thử lại với từ khóa khác, tìm không dấu, hoặc nới rộng khoảng thời gian tìm kiếm.</p>
            </div>
          `;
          return;
        }

        let html = '';
        items.forEach((doc) => {
          const loai = window.LibraryApp.formatLoaiHinh(doc.loai_hinh);
          const tacGia = doc.tac_gia ? window.LibraryApp.escapeHtml(doc.tac_gia) : 'Chưa rõ tác giả';
          const tieuDe = window.LibraryApp.escapeHtml(doc.tieu_de || 'Không có tiêu đề');
          const nxb = doc.nxb ? ` &bull; NXB: ${window.LibraryApp.escapeHtml(doc.nxb)}` : '';
          const nam = doc.nam ? ` &bull; Năm: ${doc.nam}` : '';
          const kyHieu = doc.ky_hieu ? window.LibraryApp.escapeHtml(doc.ky_hieu) : 'TL';
          const conLai = doc.so_ban_con != null ? doc.so_ban_con : 0;
          const tongBan = doc.so_ban != null ? doc.so_ban : 0;

          let statusHtml = '';
          if (doc.khong_co_tl) {
            statusHtml = '<span class="badge" style="background: #f1f5f9; color: var(--color-text-muted);"><i class="fa-solid fa-circle-xmark"></i> Không có bản cứng</span>';
          } else if (conLai > 0) {
            statusHtml = `<span class="badge badge-success"><i class="fa-solid fa-check"></i> Còn ${conLai}/${tongBan} bản</span>`;
          } else {
            statusHtml = '<span class="badge badge-danger"><i class="fa-solid fa-hourglass-empty"></i> Hết bản cứng</span>';
          }

          const softCopyHtml = doc.co_ban_mem
            ? `<span class="badge badge-softcopy"><i class="fa-solid fa-file-pdf"></i> Có bản mềm (${doc.muc_truy_cap === 'cong_khai' ? 'Công khai' : 'Nội bộ'})</span>`
            : '';

          const detailUrl = `chi-tiet.html?id=${doc.id}${currentLogId ? '&log_id=' + currentLogId : ''}`;

          html += `
            <article class="book-list-row" data-id="${doc.id}">
              <div class="book-thumb">
                <div class="book-cover-placeholder">
                  <i class="fa-solid fa-book" style="font-size: 2rem;"></i>
                  <span class="cover-label" style="font-size: 0.75rem; margin-top: 4px;">${loai}</span>
                </div>
              </div>
              <div class="book-info">
                <h3>
                  <a href="${detailUrl}" class="doc-title-link" data-id="${doc.id}">${tieuDe}</a>
                </h3>
                <div class="book-meta">
                  <span><i class="fa-regular fa-user"></i> <strong>${tacGia}</strong></span>
                  <span><i class="fa-solid fa-barcode"></i> Ký hiệu: <strong>${kyHieu}</strong></span>
                  <span><i class="fa-regular fa-calendar"></i> ${nam}${nxb}</span>
                </div>
                <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap;">
                  <span class="badge" style="background: #fdf2f2; color: var(--color-primary); font-weight: 600;">${loai}</span>
                  ${statusHtml}
                  ${softCopyHtml}
                </div>
                <div class="book-actions">
                  <a href="${detailUrl}" class="btn-primary-block doc-action-btn" data-id="${doc.id}" style="width: auto; padding: 7px 16px; font-size: 0.85rem;">
                    <i class="fa-solid fa-circle-info"></i> Xem chi tiết &amp; Mượn
                  </a>
                </div>
              </div>
            </article>
          `;
        });

        container.innerHTML = html;

        // Bắt sự kiện click vào kết quả để gọi POST /api/tim-kiem/:logId/chon
        const clickLinks = container.querySelectorAll('.doc-title-link, .doc-action-btn');
        clickLinks.forEach(link => {
          link.addEventListener('click', (e) => {
            const tlId = link.getAttribute('data-id');
            if (currentLogId && tlId) {
              window.LibraryApp.recordSelection(currentLogId, tlId);
            }
          });
        });
      }

      function renderPagination(data) {
        const pagContainer = document.getElementById('paginationContainer');
        const tongTrang = data.tong_trang || 1;
        const trang = data.trang || 1;

        if (tongTrang <= 1) {
          pagContainer.style.display = 'none';
          return;
        }

        pagContainer.style.display = 'flex';
        let html = '';

        // Nút Trước
        html += `<button type="button" class="btn-pag-nav" ${trang <= 1 ? 'disabled' : ''} data-page="${trang - 1}"><i class="fa-solid fa-chevron-left"></i></button>`;

        // Các số trang
        const maxPagesToShow = 5;
        let startPage = Math.max(1, trang - Math.floor(maxPagesToShow / 2));
        let endPage = Math.min(tongTrang, startPage + maxPagesToShow - 1);
        if (endPage - startPage + 1 < maxPagesToShow) {
          startPage = Math.max(1, endPage - maxPagesToShow + 1);
        }

        if (startPage > 1) {
          html += `<button type="button" data-page="1">1</button>`;
          if (startPage > 2) html += `<span>...</span>`;
        }

        for (let p = startPage; p <= endPage; p++) {
          html += `<button type="button" class="${p === trang ? 'active' : ''}" data-page="${p}">${p}</button>`;
        }

        if (endPage < tongTrang) {
          if (endPage < tongTrang - 1) html += `<span>...</span>`;
          html += `<button type="button" data-page="${tongTrang}">${tongTrang}</button>`;
        }

        // Nút Sau
        html += `<button type="button" class="btn-pag-nav" ${trang >= tongTrang ? 'disabled' : ''} data-page="${trang + 1}"><i class="fa-solid fa-chevron-right"></i></button>`;

        pagContainer.innerHTML = html;

        pagContainer.querySelectorAll('button[data-page]').forEach(btn => {
          btn.addEventListener('click', () => {
            if (btn.disabled) return;
            const targetPage = parseInt(btn.getAttribute('data-page'), 10);
            if (targetPage && targetPage !== trang && targetPage >= 1 && targetPage <= tongTrang) {
              window.scrollTo({ top: 150, behavior: 'smooth' });
              loadCatalog(targetPage);
            }
          });
        });
      }
    });
  
