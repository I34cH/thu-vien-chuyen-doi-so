    document.addEventListener('DOMContentLoaded', async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const docId = urlParams.get('id');
      const logId = urlParams.get('log_id');

      if (!docId) {
        showError('Không có mã tư liệu để hiển thị.');
        return;
      }

      // Lấy thông tin phiên hiện tại
      let currentUser = null;
      let userRole = 'khach';
      let nhomVaiTro = 'khach';
      try {
        const authData = await window.LibraryApp.initAuth();
        currentUser = authData.user;
        userRole = authData.vai_tro;
        nhomVaiTro = authData.nhom_vai_tro;
      } catch (e) {
        console.warn('Lỗi lấy thông tin tài khoản:', e);
      }

      // Tải chi tiết tư liệu từ /api/tai-lieu/:id
      try {
        const res = await fetch(`/api/tai-lieu/${docId}`, {
          method: 'GET',
          credentials: 'same-origin',
          headers: { 'Accept': 'application/json' }
        });

        if (!res.ok) {
          if (res.status === 404) throw new Error('Không tìm thấy tư liệu yêu cầu.');
          throw new Error('Lỗi máy chủ khi lấy dữ liệu tư liệu.');
        }

        const data = await res.json();
        if (!data.thanh_cong || !data.tai_lieu) throw new Error(data.error || 'Dữ liệu không hợp lệ');

        renderDocDetail(data.tai_lieu, nhomVaiTro, userRole);

        // Nếu người dùng chuyển đến từ kết quả tìm kiếm có log_id, ghi nhận lựa chọn
        if (logId && docId) {
          window.LibraryApp.recordSelection(logId, docId);
        }
      } catch (err) {
        showError(err.message);
      }

      function showError(msg) {
        document.getElementById('detailLoadingBox').style.display = 'none';
        document.getElementById('detailContentCard').style.display = 'none';
        document.getElementById('detailErrorBox').style.display = 'block';
        document.getElementById('detailErrorMsg').textContent = msg;
      }

      function renderDocDetail(doc, nhom, role) {
        document.getElementById('detailLoadingBox').style.display = 'none';
        document.getElementById('detailContentCard').style.display = 'block';

        const loaiStr = window.LibraryApp.formatLoaiHinh(doc.loai_hinh);
        document.title = `${doc.tieu_de || 'Chi tiết'} | Thư Viện Đại Học`;

        document.getElementById('docLoaiBadge').textContent = loaiStr;
        document.getElementById('docLoaiPill').textContent = loaiStr;
        document.getElementById('docTitle').textContent = doc.tieu_de || 'Không có nhan đề';
        document.getElementById('docTacGia').textContent = doc.tac_gia || 'Chưa rõ tác giả';
        document.getElementById('docKyHieu').textContent = doc.ky_hieu || 'TL';
        document.getElementById('docNam').textContent = doc.nam_goc || doc.nam || '---';

        // NXB
        if (doc.nxb) {
          document.getElementById('docNxb').textContent = doc.nxb;
        } else {
          document.getElementById('rowNxb').style.display = 'none';
        }

        // Mã vấn đề
        if (doc.ma_van_de) {
          const vdTen = doc.ten_ma_van_de ? ` (${doc.ten_ma_van_de})` : '';
          document.getElementById('docMaVanDe').textContent = `${doc.ma_van_de}${vdTen}`;
        } else {
          document.getElementById('rowMaVanDe').style.display = 'none';
        }

        // GVHD
        if (doc.gvhd) {
          document.getElementById('docGvhd').textContent = doc.gvhd;
        } else {
          document.getElementById('rowGvhd').style.display = 'none';
        }

        // Cơ quan
        if (doc.co_quan_dia_diem) {
          document.getElementById('docCoQuan').textContent = doc.co_quan_dia_diem;
        } else {
          document.getElementById('rowCoQuan').style.display = 'none';
        }

        // Hệ / Khóa
        const heKhoaParts = [];
        if (doc.he) heKhoaParts.push(`Hệ: ${doc.he}`);
        if (doc.khoa) heKhoaParts.push(`Khóa: ${doc.khoa}`);
        if (heKhoaParts.length > 0) {
          document.getElementById('docHeKhoa').textContent = heKhoaParts.join(' &bull; ');
        } else {
          document.getElementById('rowHeKhoa').style.display = 'none';
        }

        // Ghi chú
        if (doc.ghi_chu) {
          document.getElementById('docGhiChu').textContent = doc.ghi_chu;
        } else {
          document.getElementById('rowGhiChu').style.display = 'none';
        }

        // Tình trạng bản cứng
        const statusBadge = document.getElementById('docStatusBadge');
        const conLai = doc.so_ban_con != null ? doc.so_ban_con : 0;
        const tongBan = doc.so_ban != null ? doc.so_ban : 0;

        if (doc.khong_co_tl) {
          statusBadge.innerHTML = '<span class="badge" style="background: #f1f5f9; color: var(--color-text-muted);"><i class="fa-solid fa-circle-xmark"></i> Không có bản cứng tại TV</span>';
        } else if (conLai > 0) {
          statusBadge.innerHTML = `<span class="badge badge-success"><i class="fa-solid fa-check"></i> Còn ${conLai}/${tongBan} bản khả dụng</span>`;
        } else {
          statusBadge.innerHTML = '<span class="badge badge-danger"><i class="fa-solid fa-hourglass-empty"></i> Đã mượn hết bản cứng</span>';
        }

        // Tình trạng bản mềm
        const softCopyPill = document.getElementById('docSoftCopyPill');
        const softActionArea = document.getElementById('docSoftCopyActionArea');

        if (doc.co_ban_mem) {
          const mucTc = doc.muc_truy_cap === 'cong_khai' ? 'Công khai' : 'Nội bộ';
          softCopyPill.innerHTML = `<span class="badge badge-softcopy"><i class="fa-solid fa-file-pdf"></i> Có bản mềm (${mucTc})</span>`;

          softActionArea.innerHTML = `
            <a href="/api/ban-mem/${doc.id}" target="_blank" class="btn-primary-block" style="background: linear-gradient(135deg, #6d28d9, #8b5cf6);">
              <i class="fa-solid fa-file-pdf"></i> Đọc / Tải bản mềm PDF
            </a>
            ${doc.muc_truy_cap === 'noi_bo' && nhom === 'khach' ? '<small style="color: var(--color-text-muted); display: block; text-align: center;">(Bản mềm nội bộ: cần đăng nhập để đọc)</small>' : ''}
          `;
        } else {
          softCopyPill.innerHTML = '<span class="badge" style="background: #f1f5f9; color: var(--color-text-muted);"><i class="fa-solid fa-file"></i> Chưa có bản mềm</span>';
          if (nhom === 'thu_thu') {
            softActionArea.innerHTML = `
              <a href="quan-ly.html?so_hoa_id=${doc.id}" class="btn-primary-block" style="background: linear-gradient(135deg, var(--color-accent), var(--color-accent-hover)); color: #fff;">
                <i class="fa-solid fa-upload"></i> Tải bản mềm số hóa lên
              </a>
            `;
          }
        }

        // Khu vực nút Đăng ký mượn
        const borrowArea = document.getElementById('docBorrowActionArea');
        if (doc.khong_co_tl) {
          borrowArea.innerHTML = `
            <button type="button" class="btn-primary-block" disabled style="opacity: 0.6; cursor: not-allowed; background: #94a3b8;">
              <i class="fa-solid fa-ban"></i> Không thể mượn (Ko có TL)
            </button>
          `;
        } else if (nhom === 'nguoi_dung') {
          borrowArea.innerHTML = `
            <button type="button" class="btn-primary-block" id="btnDangKyMuon">
              <i class="fa-solid fa-bookmark"></i> Đăng ký mượn tài liệu
            </button>
          `;
          document.getElementById('btnDangKyMuon').addEventListener('click', () => handleDangKyMuon(doc.id));
        } else if (nhom === 'khach') {
          borrowArea.innerHTML = `
            <a href="tai-khoan.html" class="btn-primary-block">
              <i class="fa-solid fa-arrow-right-to-bracket"></i> Đăng nhập để mượn sách
            </a>
          `;
        }

        // Bảng danh sách bản sao
        const copiesBody = document.getElementById('copiesTableBody');
        const banSaoList = doc.ban_sao || [];
        if (banSaoList.length === 0) {
          copiesBody.innerHTML = `
            <tr>
              <td colspan="3" style="text-align: center; color: var(--color-text-muted); padding: 20px;">
                Tư liệu này hiện chưa có bản sao vật lý được ghi nhận.
              </td>
            </tr>
          `;
        } else {
          let rowsHtml = '';
          banSaoList.forEach((bs, idx) => {
            let statusText = '';
            if (bs.trang_thai === 'con') {
              statusText = '<span class="badge badge-success"><i class="fa-solid fa-circle-check"></i> Sẵn sàng cho mượn</span>';
            } else if (bs.trang_thai === 'dang_muon') {
              statusText = '<span class="badge badge-info"><i class="fa-solid fa-book-reader"></i> Đang được mượn</span>';
            } else if (bs.trang_thai === 'bao_tri') {
              statusText = '<span class="badge badge-warning"><i class="fa-solid fa-wrench"></i> Đang bảo trì / phục chế</span>';
            } else {
              statusText = '<span class="badge badge-danger"><i class="fa-solid fa-circle-xmark"></i> Mất / Hỏng</span>';
            }

            rowsHtml += `
              <tr>
                <td>${idx + 1}</td>
                <td style="font-family: monospace; font-weight: 600;">${window.LibraryApp.escapeHtml(bs.ma_ban_sao)}</td>
                <td>${statusText}</td>
              </tr>
            `;
          });
          copiesBody.innerHTML = rowsHtml;
        }
      }

      async function handleDangKyMuon(taiLieuId) {
        const alertBox = document.getElementById('borrowAlertMsg');
        alertBox.style.display = 'none';

        try {
          const res = await fetch('/api/muon', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            },
            body: JSON.stringify({ tai_lieu_id: taiLieuId })
          });

          const data = await res.json();
          if (!res.ok || !data.thanh_cong) {
            alertBox.style.display = 'block';
            alertBox.style.backgroundColor = '#fee2e2';
            alertBox.style.color = '#b91c1c';
            alertBox.style.border = '1px solid #fecaca';
            alertBox.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> ${window.LibraryApp.escapeHtml(data.error || 'Không thể đăng ký mượn.')}`;
            return;
          }

          alertBox.style.display = 'block';
          alertBox.style.backgroundColor = '#dcfce7';
          alertBox.style.color = '#15803d';
          alertBox.style.border = '1px solid #bbf7d0';
          alertBox.innerHTML = `
            <i class="fa-solid fa-circle-check"></i> <strong>Đăng ký mượn thành công!</strong> Yêu cầu của bạn đang ở trạng thái <em>Chờ duyệt</em>. 
            Bạn có thể theo dõi trong <a href="tai-khoan.html" style="text-decoration: underline; font-weight: 600;">Lịch sử mượn</a>.
          `;

          // Vô hiệu hóa nút mượn sau khi đăng ký
          const btn = document.getElementById('btnDangKyMuon');
          if (btn) {
            btn.disabled = true;
            btn.style.opacity = '0.6';
            btn.style.cursor = 'not-allowed';
            btn.innerHTML = '<i class="fa-solid fa-clock"></i> Đang chờ thủ thư duyệt';
          }
        } catch (err) {
          alertBox.style.display = 'block';
          alertBox.style.backgroundColor = '#fee2e2';
          alertBox.style.color = '#b91c1c';
          alertBox.style.border = '1px solid #fecaca';
          alertBox.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> Lỗi kết nối máy chủ: ${window.LibraryApp.escapeHtml(err.message)}`;
        }
      }
    });
  
