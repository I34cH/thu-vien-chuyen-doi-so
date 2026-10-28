/**
 * main.js - Thư viện JavaScript dùng chung cho Web Thư viện Chuyển đổi số
 * Nối API backend qua fetch (credentials: 'same-origin')
 * Quản lý phiên, menu theo vai trò, Autocomplete và ghi nhận click kết quả
 */

(function () {
  'use strict';

  // Ánh xạ tên loại hình chuẩn tiếng Việt
  const LOAI_HINH_MAP = {
    luan_an: 'Luận án',
    luan_van: 'Luận văn',
    khoa_luan: 'Khóa luận',
    bao_cao_kh: 'Báo cáo KH',
    ky_yeu: 'Kỷ yếu',
    sach: 'Sách',
    sach_ha_noi: 'Sách Hà Nội',
    tu_sach_tang: 'Tủ sách tặng'
  };

  const VAI_TRO_MAP = {
    sinh_vien: 'Sinh viên',
    giang_vien: 'Giảng viên',
    thu_thu: 'Thủ thư',
    admin: 'Quản trị viên',
    khach: 'Khách vãng lai'
  };

  function formatLoaiHinh(loai) {
    return LOAI_HINH_MAP[loai] || loai || 'Tư liệu';
  }

  function formatVaiTro(vt) {
    return VAI_TRO_MAP[vt] || vt || 'Bạn đọc';
  }

  function formatDate(isoStr) {
    if (!isoStr) return '---';
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return String(isoStr).substring(0, 10);
      const day = String(d.getDate()).padStart(2, '0');
      const mon = String(d.getMonth() + 1).padStart(2, '0');
      const yr = d.getFullYear();
      return `${day}/${mon}/${yr}`;
    } catch {
      return String(isoStr).substring(0, 10);
    }
  }

  /**
   * 1. Xác thực và hiển thị Menu / Profile theo vai trò từ /api/toi
   */
  async function initAuth() {
    try {
      const res = await fetch('/api/toi', {
        method: 'GET',
        credentials: 'same-origin',
        headers: { 'Accept': 'application/json' }
      });
      const data = await res.json();
      renderUserHeader(data);
      renderNavMenu(data);
      return data;
    } catch (err) {
      console.warn('Không thể kiểm tra phiên đăng nhập:', err);
      const guestData = { dang_nhap: false, user: null, vai_tro: 'khach', nhom_vai_tro: 'khach' };
      renderUserHeader(guestData);
      renderNavMenu(guestData);
      return guestData;
    }
  }

  function renderUserHeader(authData) {
    const profileWrap = document.querySelector('.user-quick-profile');
    if (!profileWrap) return;

    if (authData.dang_nhap && authData.user) {
      const u = authData.user;
      const avatarUrl = `https://ui-avatars.com/api/?name=${encodeURIComponent(u.ho_ten || u.ten_dang_nhap)}&background=9b1c1c&color=fff`;
      profileWrap.innerHTML = `
        <img src="${avatarUrl}" alt="Ảnh đại diện" class="user-avatar">
        <div class="user-details">
          <span class="user-name">${escapeHtml(u.ho_ten || u.ten_dang_nhap)}</span>
          <span class="user-role">${formatVaiTro(u.vai_tro)}</span>
        </div>
        <button type="button" class="btn-auth-action" id="btnHeaderLogout" title="Đăng xuất">
          <i class="fa-solid fa-right-from-bracket"></i> Thoát
        </button>
      `;

      const btnLogout = document.getElementById('btnHeaderLogout');
      if (btnLogout) {
        btnLogout.addEventListener('click', handleLogout);
      }
    } else {
      profileWrap.innerHTML = `
        <img src="https://ui-avatars.com/api/?name=Khach&background=9b1c1c&color=fff" alt="Khách" class="user-avatar">
        <div class="user-details">
          <span class="user-name">Khách vãng lai</span>
          <span class="user-role">Chưa đăng nhập</span>
        </div>
        <a href="tai-khoan.html" class="btn-auth-action" title="Đăng nhập">
          <i class="fa-solid fa-arrow-right-to-bracket"></i> Đăng nhập
        </a>
      `;
    }
  }

  async function handleLogout() {
    try {
      await fetch('/api/dang-xuat', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Accept': 'application/json' }
      });
      window.location.href = 'index.html';
    } catch (err) {
      console.error('Lỗi khi đăng xuất:', err);
      window.location.reload();
    }
  }

  function renderNavMenu(authData) {
    const navMenu = document.querySelector('.nav-menu');
    if (!navMenu) return;

    // Xác định trang hiện tại từ pathname
    const path = window.location.pathname.toLowerCase();
    const isIndex = path.endsWith('index.html') || path === '/' || path.endsWith('/');
    const isTraCuu = path.includes('tra-cuu.html') || path.includes('chi-tiet.html');
    const isQuanLy = path.includes('quan-ly.html');
    const isDashboard = path.includes('dashboard.html');
    const isTaiKhoan = path.includes('tai-khoan.html');

    const nhom = authData.nhom_vai_tro || 'khach';

    let html = `
      <li class="nav-item ${isIndex ? 'active' : ''}">
        <a href="index.html" class="nav-link"><i class="fa-solid fa-house"></i> Trang chủ</a>
      </li>
      <li class="nav-item ${isTraCuu ? 'active' : ''}">
        <a href="tra-cuu.html" class="nav-link"><i class="fa-solid fa-magnifying-glass"></i> Tra cứu OPAC</a>
      </li>
    `;

    if (nhom === 'thu_thu') {
      html += `
        <li class="nav-item ${isQuanLy ? 'active' : ''}">
          <a href="quan-ly.html" class="nav-link"><i class="fa-solid fa-book-bookmark"></i> Quản lý Mượn - Trả</a>
        </li>
        <li class="nav-item ${isDashboard ? 'active' : ''}">
          <a href="dashboard.html" class="nav-link"><i class="fa-solid fa-chart-pie"></i> Dashboard Thống kê</a>
        </li>
        <li class="nav-item ${isTaiKhoan ? 'active' : ''}">
          <a href="tai-khoan.html" class="nav-link"><i class="fa-solid fa-id-card"></i> Tài khoản</a>
        </li>
      `;
    } else if (nhom === 'nguoi_dung') {
      html += `
        <li class="nav-item ${isTaiKhoan ? 'active' : ''}">
          <a href="tai-khoan.html" class="nav-link"><i class="fa-solid fa-clock-rotate-left"></i> Lượt mượn của tôi</a>
        </li>
      `;
    } else {
      // Khách
      html += `
        <li class="nav-item ${isTaiKhoan ? 'active' : ''}">
          <a href="tai-khoan.html" class="nav-link"><i class="fa-solid fa-arrow-right-to-bracket"></i> Đăng nhập</a>
        </li>
      `;
    }

    navMenu.innerHTML = html;
  }

  /**
   * 2. Autocomplete gợi ý tìm kiếm khi gõ (index.html và tra-cuu.html)
   */
  function initAutocomplete(inputEl, resultsContainerEl) {
    if (!inputEl || !resultsContainerEl) return;

    let debounceTimer = null;
    let currentFocus = -1;

    inputEl.setAttribute('autocomplete', 'off');

    inputEl.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      const query = inputEl.value.trim();
      currentFocus = -1;

      if (query.length < 2) {
        resultsContainerEl.innerHTML = '';
        resultsContainerEl.style.display = 'none';
        return;
      }

      debounceTimer = setTimeout(async () => {
        try {
          const res = await fetch(`/api/goi-y?q=${encodeURIComponent(query)}`, {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
          });
          if (!res.ok) throw new Error('Lỗi tải gợi ý');
          const items = await res.json();
          renderAutocompleteItems(items, resultsContainerEl, inputEl);
        } catch (err) {
          console.error('Lỗi lấy gợi ý tìm kiếm:', err);
          resultsContainerEl.style.display = 'none';
        }
      }, 200);
    });

    // Điều hướng phím mũi tên và Enter trong dropdown
    inputEl.addEventListener('keydown', (e) => {
      const items = resultsContainerEl.querySelectorAll('.autocomplete-item');
      if (!items || items.length === 0 || resultsContainerEl.style.display === 'none') return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        currentFocus++;
        if (currentFocus >= items.length) currentFocus = 0;
        setActive(items);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        currentFocus--;
        if (currentFocus < 0) currentFocus = items.length - 1;
        setActive(items);
      } else if (e.key === 'Enter') {
        if (currentFocus > -1 && items[currentFocus]) {
          e.preventDefault();
          items[currentFocus].click();
        }
      } else if (e.key === 'Escape') {
        resultsContainerEl.style.display = 'none';
      }
    });

    function setActive(items) {
      items.forEach(it => it.classList.remove('active'));
      if (currentFocus > -1 && items[currentFocus]) {
        items[currentFocus].classList.add('active');
        items[currentFocus].scrollIntoView({ block: 'nearest' });
      }
    }

    // Đóng dropdown khi bấm ra ngoài
    document.addEventListener('click', (e) => {
      if (!inputEl.contains(e.target) && !resultsContainerEl.contains(e.target)) {
        resultsContainerEl.style.display = 'none';
      }
    });
  }

  function renderAutocompleteItems(items, containerEl, inputEl) {
    if (!items || items.length === 0) {
      containerEl.innerHTML = `
        <div class="autocomplete-item" style="color: var(--color-text-muted); cursor: default;">
          <i class="fa-solid fa-circle-info"></i> Không tìm thấy tư liệu phù hợp
        </div>
      `;
      containerEl.style.display = 'block';
      return;
    }

    let html = '';
    items.forEach((item) => {
      const loai = formatLoaiHinh(item.loai_hinh);
      const tacGia = item.tac_gia ? escapeHtml(item.tac_gia) : 'Chưa rõ tác giả';
      const nam = item.nam ? ` (${item.nam})` : '';
      const tieuDe = escapeHtml(item.tieu_de || 'Không có nhan đề');

      html += `
        <div class="autocomplete-item" data-id="${item.id}" data-title="${tieuDe}">
          <div class="ac-title"><i class="fa-solid fa-book-bookmark" style="color: var(--color-primary); margin-right: 6px;"></i>${tieuDe}</div>
          <div class="ac-meta">
            <span><i class="fa-regular fa-user"></i> ${tacGia}${nam}</span>
            <span class="badge" style="background: #f1f5f9; color: var(--color-primary-dark); font-size: 0.72rem;">${loai}</span>
          </div>
        </div>
      `;
    });

    containerEl.innerHTML = html;
    containerEl.style.display = 'block';

    const itemEls = containerEl.querySelectorAll('.autocomplete-item[data-id]');
    itemEls.forEach((el) => {
      el.addEventListener('click', () => {
        const id = el.getAttribute('data-id');
        window.location.href = `chi-tiet.html?id=${id}`;
      });
    });
  }

  /**
   * 3. Ghi nhận lựa chọn kết quả tìm kiếm (POST /api/tim-kiem/:logId/chon)
   */
  async function recordSelection(logId, taiLieuId) {
    if (!logId || !taiLieuId) return;
    try {
      await fetch(`/api/tim-kiem/${logId}/chon`, {
        method: 'POST',
        credentials: 'same-origin',
        keepalive: true,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ tai_lieu_id: parseInt(taiLieuId, 10) })
      });
    } catch (err) {
      console.warn('Không thể ghi log lựa chọn tư liệu:', err);
    }
  }

  function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // Khởi tạo tự động khi trang tải xong
  document.addEventListener('DOMContentLoaded', () => {
    initAuth();
  });

  // Xuất các hàm tiện ích cho các trang con sử dụng
  window.LibraryApp = {
    initAuth,
    initAutocomplete,
    recordSelection,
    formatLoaiHinh,
    formatVaiTro,
    formatDate,
    escapeHtml
  };
})();
