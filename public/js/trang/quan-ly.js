    document.addEventListener('DOMContentLoaded', async () => {
      let currentFilterStatus = '';

      // Kiểm tra vai trò người dùng
      const authData = await window.LibraryApp.initAuth();
      if (authData.nhom_vai_tro !== 'thu_thu') {
        document.getElementById('librarianForbiddenCard').style.display = 'block';
        document.getElementById('librarianMainContent').style.display = 'none';
        return;
      }

      document.getElementById('librarianForbiddenCard').style.display = 'none';
      document.getElementById('librarianMainContent').style.display = 'block';

      // Kiểm tra URL query param ?so_hoa_id= để điền sẵn vào form tải bản mềm
      const urlParams = new URLSearchParams(window.location.search);
      const prefillId = urlParams.get('so_hoa_id');
      if (prefillId) {
        document.getElementById('inputUploadDocId').value = prefillId;
        checkDocPreview(prefillId);
        setTimeout(() => {
          const form = document.getElementById('formUploadPdf');
          if (form) {
            form.scrollIntoView({ behavior: 'smooth' });
          }
        }, 200);
      }

      // Tải danh sách mượn ban đầu
      loadAdminBorrows('');

      // Bộ lọc trạng thái (Pills)
      document.querySelectorAll('#filterStatusPills .filter-pill').forEach(pill => {
        pill.addEventListener('click', () => {
          document.querySelectorAll('#filterStatusPills .filter-pill').forEach(p => p.classList.remove('active'));
          pill.classList.add('active');
          currentFilterStatus = pill.getAttribute('data-status') || '';
          loadAdminBorrows(currentFilterStatus);
        });
      });

      // Nút làm mới
      document.getElementById('btnReloadBorrows').addEventListener('click', () => {
        loadAdminBorrows(currentFilterStatus);
      });

      // Tự động kiểm tra thông tin tư liệu khi nhập ID
      document.getElementById('inputUploadDocId').addEventListener('change', (e) => {
        const id = e.target.value.trim();
        if (id) checkDocPreview(id);
      });

      async function checkDocPreview(id) {
        const previewWrap = document.getElementById('uploadDocPreview');
        try {
          const res = await fetch(`/api/tai-lieu/${id}`, { credentials: 'same-origin' });
          if (!res.ok) throw new Error('Không tìm thấy');
          const data = await res.json();
          if (data.thanh_cong && data.tai_lieu) {
            const tl = data.tai_lieu;
            previewWrap.style.display = 'block';
            document.getElementById('previewDocTitle').textContent = `[#${tl.id}] ${tl.tieu_de}`;
            document.getElementById('previewDocStatus').innerHTML = `
              Loại hình: <strong>${window.LibraryApp.formatLoaiHinh(tl.loai_hinh)}</strong> | 
              Ký hiệu: <code>${tl.ky_hieu || 'TL'}</code> | 
              Bản mềm: ${tl.co_ban_mem ? '<span style="color: #16a34a; font-weight: 600;">Đã có bản mềm (' + tl.muc_truy_cap + ')</span>' : '<span style="color: #dc2626;">Chưa có bản mềm</span>'}
            `;
          }
        } catch {
          previewWrap.style.display = 'none';
        }
      }

      // Xử lý gửi Form tải bản mềm PDF
      document.getElementById('formUploadPdf').addEventListener('submit', async (e) => {
        e.preventDefault();
        const docId = document.getElementById('inputUploadDocId').value.trim();
        const mucTruyCap = document.getElementById('selectMucTruyCap').value;
        const fileInput = document.getElementById('inputFilePdf');
        const file = fileInput.files[0];

        if (!docId || !file) {
          showAlert('Vui lòng nhập mã tư liệu và chọn file PDF.', 'error');
          return;
        }

        const formData = new FormData();
        formData.append('muc_truy_cap', mucTruyCap);
        formData.append('file', file);

        const btn = document.getElementById('btnSubmitUpload');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang tải file lên...';

        try {
          const res = await fetch(`/api/quan-ly/tai-lieu/${docId}/ban-mem`, {
            method: 'POST',
            credentials: 'same-origin',
            body: formData
          });

          const data = await res.json();
          if (!res.ok || !data.thanh_cong) {
            throw new Error(data.error || 'Lỗi khi tải tệp.');
          }

          showAlert(`Tải bản mềm thành công cho tư liệu #${docId}! Mức truy cập: ${mucTruyCap}.`, 'success');
          fileInput.value = '';
          checkDocPreview(docId);
        } catch (err) {
          showAlert(`Lỗi tải bản mềm: ${err.message}`, 'error');
        } finally {
          btn.disabled = false;
          btn.innerHTML = '<i class="fa-solid fa-file-arrow-up"></i> Tải bản mềm lên &amp; Cập nhật số hóa';
        }
      });

      async function loadAdminBorrows(status = '') {
        const tbody = document.getElementById('adminBorrowTableBody');
        tbody.innerHTML = `
          <tr>
            <td colspan="7" style="text-align: center; padding: 25px; color: var(--color-text-muted);">
              <i class="fa-solid fa-spinner fa-spin"></i> Đang tải danh sách mượn...
            </td>
          </tr>
        `;

        try {
          const url = status ? `/api/quan-ly/muon?trang_thai=${encodeURIComponent(status)}` : '/api/quan-ly/muon';
          const res = await fetch(url, {
            method: 'GET',
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
          });

          if (!res.ok) throw new Error('Không thể tải danh sách mượn.');
          const data = await res.json();
          const items = data.luot_muon || [];

          document.getElementById('borrowCountInfo').textContent = `Tổng cộng: ${items.length} lượt mượn`;

          if (items.length === 0) {
            tbody.innerHTML = `
              <tr>
                <td colspan="7" style="text-align: center; padding: 30px; color: var(--color-text-muted);">
                  Không có lượt mượn nào ở trạng thái này.
                </td>
              </tr>
            `;
            return;
          }

          let html = '';
          items.forEach((m) => {
            let statusBadge = '';
            let actionBtns = '';

            if (m.trang_thai === 'cho_duyet') {
              statusBadge = '<span class="badge badge-warning"><i class="fa-solid fa-clock"></i> Chờ duyệt</span>';
              actionBtns = `
                <button type="button" class="action-btn action-btn-approve btn-approve-borrow" data-id="${m.id}" title="Duyệt yêu cầu (gán bản sao còn rảnh, hạn trả +14 ngày)">
                  <i class="fa-solid fa-check"></i> Duyệt
                </button>
                <button type="button" class="action-btn action-btn-reject btn-reject-borrow" data-id="${m.id}" title="Từ chối yêu cầu">
                  <i class="fa-solid fa-xmark"></i> Từ chối
                </button>
              `;
            } else if (m.trang_thai === 'dang_muon') {
              statusBadge = '<span class="badge badge-info"><i class="fa-solid fa-book-reader"></i> Đang mượn</span>';
              actionBtns = `
                <button type="button" class="action-btn action-btn-return btn-return-borrow" data-id="${m.id}" title="Ghi nhận độc giả đã trả tư liệu">
                  <i class="fa-solid fa-rotate-left"></i> Nhận trả
                </button>
              `;
            } else if (m.trang_thai === 'da_tra') {
              statusBadge = '<span class="badge badge-success"><i class="fa-solid fa-circle-check"></i> Đã trả</span>';
              actionBtns = `<small style="color: var(--color-text-muted);">${window.LibraryApp.formatDate(m.ngay_tra)}</small>`;
            } else {
              statusBadge = '<span class="badge badge-danger"><i class="fa-solid fa-circle-xmark"></i> Từ chối</span>';
              actionBtns = '<small style="color: var(--color-text-muted);">---</small>';
            }

            const nguoiDocStr = `${window.LibraryApp.escapeHtml(m.ho_ten || m.ten_dang_nhap)} <br><small style="color: var(--color-text-muted);">${window.LibraryApp.formatVaiTro(m.vai_tro)} (${window.LibraryApp.escapeHtml(m.ten_dang_nhap)})</small>`;
            const tieuDeStr = `
              <a href="chi-tiet.html?id=${m.tai_lieu_id}" target="_blank" style="font-weight: 600; color: var(--color-primary-dark);">
                ${window.LibraryApp.escapeHtml(m.tieu_de)}
              </a>
              <div style="font-size: 0.78rem; color: var(--color-text-muted);">
                <span class="badge" style="background: #f1f5f9; padding: 1px 6px;">${window.LibraryApp.formatLoaiHinh(m.loai_hinh)}</span>
                <code>${window.LibraryApp.escapeHtml(m.ky_hieu || '')}</code>
              </div>
            `;

            html += `
              <tr data-borrow-id="${m.id}">
                <td><strong>#${m.id}</strong></td>
                <td>${nguoiDocStr}</td>
                <td>${tieuDeStr}</td>
                <td style="font-family: monospace;">${m.ma_ban_sao ? window.LibraryApp.escapeHtml(m.ma_ban_sao) : '<em style="color:#94a3b8;">Chưa gán</em>'}</td>
                <td>
                  <div>ĐK: ${window.LibraryApp.formatDate(m.ngay_dang_ky)}</div>
                  ${m.han_tra ? `<div style="font-size: 0.8rem; color: var(--color-primary);">Hạn: <strong>${window.LibraryApp.formatDate(m.han_tra)}</strong></div>` : ''}
                </td>
                <td>${statusBadge}</td>
                <td style="text-align: center;">${actionBtns}</td>
              </tr>
            `;
          });

          tbody.innerHTML = html;

          // Bắt sự kiện các nút Duyệt, Từ chối, Trả
          tbody.querySelectorAll('.btn-approve-borrow').forEach(btn => {
            btn.addEventListener('click', () => handleApprove(btn.getAttribute('data-id')));
          });
          tbody.querySelectorAll('.btn-reject-borrow').forEach(btn => {
            btn.addEventListener('click', () => handleReject(btn.getAttribute('data-id')));
          });
          tbody.querySelectorAll('.btn-return-borrow').forEach(btn => {
            btn.addEventListener('click', () => handleReturn(btn.getAttribute('data-id')));
          });
        } catch (err) {
          tbody.innerHTML = `
            <tr>
              <td colspan="7" style="text-align: center; padding: 25px; color: var(--status-danger);">
                Lỗi tải dữ liệu: ${window.LibraryApp.escapeHtml(err.message)}
              </td>
            </tr>
          `;
        }
      }

      async function handleApprove(id) {
        if (!confirm(`Xác nhận DUYỆT lượt mượn #${id}?\nHệ thống sẽ tự động gán bản sao còn rảnh và đặt hạn trả 14 ngày.`)) return;

        try {
          const res = await fetch(`/api/quan-ly/muon/${id}/duyet`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
          });

          const data = await res.json();
          if (!res.ok || !data.thanh_cong) {
            throw new Error(data.error || 'Duyệt mượn không thành công.');
          }

          showAlert(`Đã duyệt thành công lượt mượn #${id}! Đã gán bản sao: ${data.luot_muon?.ban_sao_id || 'thành công'}.`, 'success');
          loadAdminBorrows(currentFilterStatus);
        } catch (err) {
          showAlert(`Lỗi khi duyệt mượn: ${err.message}`, 'error');
        }
      }

      async function handleReject(id) {
        if (!confirm(`Xác nhận TỪ CHỐI yêu cầu mượn #${id}?`)) return;

        try {
          const res = await fetch(`/api/quan-ly/muon/${id}/tu-choi`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
          });

          const data = await res.json();
          if (!res.ok || !data.thanh_cong) {
            throw new Error(data.error || 'Từ chối mượn không thành công.');
          }

          showAlert(`Đã từ chối lượt mượn #${id}.`, 'info');
          loadAdminBorrows(currentFilterStatus);
        } catch (err) {
          showAlert(`Lỗi khi từ chối: ${err.message}`, 'error');
        }
      }

      async function handleReturn(id) {
        if (!confirm(`Xác nhận GHI NHẬN TRẢ cho lượt mượn #${id}?\nBản sao sẽ được hoàn lại trạng thái sẵn sàng cho mượn.`)) return;

        try {
          const res = await fetch(`/api/quan-ly/muon/${id}/tra`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
          });

          const data = await res.json();
          if (!res.ok || !data.thanh_cong) {
            throw new Error(data.error || 'Ghi nhận trả không thành công.');
          }

          showAlert(`Đã ghi nhận trả tư liệu cho lượt mượn #${id}. Bản sao đã về trạng thái sẵn sàng.`, 'success');
          loadAdminBorrows(currentFilterStatus);
        } catch (err) {
          showAlert(`Lỗi khi ghi nhận trả: ${err.message}`, 'error');
        }
      }

      function showAlert(msg, type = 'info') {
        const box = document.getElementById('actionAlertBox');
        box.style.display = 'block';
        if (type === 'success') {
          box.style.backgroundColor = '#dcfce7';
          box.style.color = '#15803d';
          box.style.border = '1px solid #bbf7d0';
          box.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${window.LibraryApp.escapeHtml(msg)}`;
        } else if (type === 'error') {
          box.style.backgroundColor = '#fee2e2';
          box.style.color = '#b91c1c';
          box.style.border = '1px solid #fecaca';
          box.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> ${window.LibraryApp.escapeHtml(msg)}`;
        } else {
          box.style.backgroundColor = '#e0f2fe';
          box.style.color = '#0369a1';
          box.style.border = '1px solid #bae6fd';
          box.innerHTML = `<i class="fa-solid fa-circle-info"></i> ${window.LibraryApp.escapeHtml(msg)}`;
        }
        window.scrollTo({ top: 100, behavior: 'smooth' });
      }
    });
  
