    document.addEventListener('DOMContentLoaded', async () => {
      await refreshPageState();

      // Xử lý gửi Form Đăng nhập
      document.getElementById('formLogin').addEventListener('submit', async (e) => {
        e.preventDefault();
        const ten_dang_nhap = document.getElementById('inputTenDangNhap').value.trim();
        const mat_khau = document.getElementById('inputMatKhau').value;
        const alertBox = document.getElementById('loginAlertBox');
        alertBox.style.display = 'none';

        try {
          const res = await fetch('/api/dang-nhap', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            },
            body: JSON.stringify({ ten_dang_nhap, mat_khau })
          });

          const data = await res.json();
          if (!res.ok || !data.thanh_cong) {
            alertBox.style.display = 'block';
            alertBox.style.backgroundColor = '#fee2e2';
            alertBox.style.color = '#b91c1c';
            alertBox.style.border = '1px solid #fecaca';
            alertBox.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> ${window.LibraryApp.escapeHtml(data.error || 'Đăng nhập không thành công.')}`;
            return;
          }

          // Đăng nhập thành công -> làm mới lại giao diện
          await refreshPageState();
        } catch (err) {
          alertBox.style.display = 'block';
          alertBox.style.backgroundColor = '#fee2e2';
          alertBox.style.color = '#b91c1c';
          alertBox.style.border = '1px solid #fecaca';
          alertBox.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> Lỗi kết nối máy chủ: ${window.LibraryApp.escapeHtml(err.message)}`;
        }
      });

      // Xử lý các nút điền nhanh tài khoản demo
      document.querySelectorAll('.btn-quick-login').forEach(btn => {
        btn.addEventListener('click', () => {
          document.getElementById('inputTenDangNhap').value = btn.getAttribute('data-user');
          document.getElementById('inputMatKhau').value = btn.getAttribute('data-pass');
          document.getElementById('loginAlertBox').style.display = 'none';
        });
      });

      // Xử lý nút Đăng xuất
      document.getElementById('btnLogoutAction').addEventListener('click', async () => {
        try {
          await fetch('/api/dang-xuat', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
          });
          await refreshPageState();
        } catch (err) {
          console.error('Lỗi khi đăng xuất:', err);
          window.location.reload();
        }
      });

      async function refreshPageState() {
        const authData = await window.LibraryApp.initAuth();
        const secLogin = document.getElementById('sectionLogin');
        const secProfile = document.getElementById('sectionProfile');

        if (authData.dang_nhap && authData.user) {
          secLogin.style.display = 'none';
          secProfile.style.display = 'block';

          const u = authData.user;
          document.getElementById('profileFullName').textContent = u.ho_ten || u.ten_dang_nhap;
          document.getElementById('profileUsername').textContent = u.ten_dang_nhap;
          document.getElementById('profileRoleBadge').textContent = window.LibraryApp.formatVaiTro(u.vai_tro);
          document.getElementById('profileAvatar').src = `https://ui-avatars.com/api/?name=${encodeURIComponent(u.ho_ten || u.ten_dang_nhap)}&background=9b1c1c&color=fff`;

          if (authData.nhom_vai_tro === 'thu_thu') {
            document.getElementById('borrowHistoryCard').style.display = 'none';
            document.getElementById('librarianQuickCard').style.display = 'block';
          } else {
            // Người dùng (sinh viên, giảng viên) -> Tải danh sách mượn
            document.getElementById('librarianQuickCard').style.display = 'none';
            document.getElementById('borrowHistoryCard').style.display = 'block';
            loadBorrowHistory();
          }
        } else {
          secLogin.style.display = 'block';
          secProfile.style.display = 'none';
        }
      }

      async function loadBorrowHistory() {
        const tbody = document.getElementById('myBorrowTableBody');
        tbody.innerHTML = `
          <tr>
            <td colspan="8" style="text-align: center; padding: 25px; color: var(--color-text-muted);">
              <i class="fa-solid fa-spinner fa-spin"></i> Đang tải danh sách mượn của bạn...
            </td>
          </tr>
        `;

        try {
          const res = await fetch('/api/muon/cua-toi', {
            method: 'GET',
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
          });

          if (!res.ok) throw new Error('Không thể tải lịch sử mượn.');
          const data = await res.json();
          const items = data.luot_muon || [];

          document.getElementById('borrowCountBadge').textContent = `${items.length} lượt mượn`;

          if (items.length === 0) {
            tbody.innerHTML = `
              <tr>
                <td colspan="8" style="text-align: center; padding: 30px; color: var(--color-text-muted);">
                  Bạn chưa đăng ký mượn tư liệu nào. <a href="tra-cuu.html" style="color: var(--color-primary); text-decoration: underline;">Tra cứu tư liệu ngay</a>.
                </td>
              </tr>
            `;
            return;
          }

          let html = '';
          items.forEach((m) => {
            let statusBadge = '';
            if (m.trang_thai === 'cho_duyet') {
              statusBadge = '<span class="badge badge-warning"><i class="fa-solid fa-clock"></i> Chờ duyệt</span>';
            } else if (m.trang_thai === 'dang_muon') {
              statusBadge = '<span class="badge badge-info"><i class="fa-solid fa-book-reader"></i> Đang mượn</span>';
            } else if (m.trang_thai === 'da_tra') {
              statusBadge = '<span class="badge badge-success"><i class="fa-solid fa-check"></i> Đã trả</span>';
            } else {
              statusBadge = '<span class="badge badge-danger"><i class="fa-solid fa-xmark"></i> Từ chối</span>';
            }

            const softBtn = m.co_ban_mem
              ? `<a href="/api/ban-mem/${m.tai_lieu_id}" target="_blank" class="badge badge-softcopy"><i class="fa-solid fa-file-pdf"></i> Đọc bản mềm</a>`
              : '<span style="color: #cbd5e1;">---</span>';

            html += `
              <tr>
                <td><strong>#${m.id}</strong></td>
                <td>
                  <a href="chi-tiet.html?id=${m.tai_lieu_id}" style="font-weight: 600; color: var(--color-primary-dark);">
                    ${window.LibraryApp.escapeHtml(m.tieu_de)}
                  </a>
                  <div style="font-size: 0.78rem; color: var(--color-text-muted); font-family: monospace;">${window.LibraryApp.escapeHtml(m.ky_hieu || '')}</div>
                </td>
                <td><span class="badge" style="background: #f1f5f9; color: var(--color-text-main);">${window.LibraryApp.formatLoaiHinh(m.loai_hinh)}</span></td>
                <td style="font-family: monospace;">${m.ma_ban_sao ? window.LibraryApp.escapeHtml(m.ma_ban_sao) : '<em>Chưa gán</em>'}</td>
                <td>${window.LibraryApp.formatDate(m.ngay_dang_ky)}</td>
                <td>${window.LibraryApp.formatDate(m.han_tra)}</td>
                <td>${statusBadge}</td>
                <td>${softBtn}</td>
              </tr>
            `;
          });
          tbody.innerHTML = html;
        } catch (err) {
          tbody.innerHTML = `
            <tr>
              <td colspan="8" style="text-align: center; padding: 25px; color: var(--status-danger);">
                Lỗi tải dữ liệu: ${window.LibraryApp.escapeHtml(err.message)}
              </td>
            </tr>
          `;
        }
      }
    });
  
