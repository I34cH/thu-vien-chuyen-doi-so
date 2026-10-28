    document.addEventListener('DOMContentLoaded', async () => {
      // 1. Kiểm tra vai trò Thủ thư
      const authData = await window.LibraryApp.initAuth();
      if (authData.nhom_vai_tro !== 'thu_thu') {
        document.getElementById('dashForbiddenCard').style.display = 'block';
        document.getElementById('dashMainContent').style.display = 'none';
        return;
      }

      document.getElementById('dashForbiddenCard').style.display = 'none';
      document.getElementById('dashMainContent').style.display = 'block';

      // Các biến quản lý instance biểu đồ để hủy khi cập nhật lại
      let topBarChartInstance = null;
      let timelineChartInstance = null;
      let currentTimelineDays = 30;

      // Bảng màu đỏ–vàng–xám đồng bộ (AGENTS.md mục 3)
      const PALETTE = {
        primary: '#9b1c1c',      // Đỏ đậm chủ đạo
        primaryLight: '#c53030', // Đỏ tươi
        accent: '#d4af37',       // Vàng kim nhấn
        muted: '#64748b',        // Xám xanh
        lightRed: '#e57373'      // Hồng đỏ nhạt
      };

      // -----------------------------------------------------------------------
      // A. TẢI 4 THẺ KPI CHÍNH
      // -----------------------------------------------------------------------
      async function loadKpiSummary() {
        try {
          const res = await fetch('/api/thong-ke/tong-quan', {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
          });
          if (!res.ok) throw new Error('Không thể nạp dữ liệu KPI');
          const data = await res.json();
          if (data.thanh_cong) {
            const elTongTim = document.getElementById('kpiTongTim');
            const elTiLe0 = document.getElementById('kpiTiLe0Kq');
            const elLuotMuon = document.getElementById('kpiLuotMuonMo');
            const elDaSoHoa = document.getElementById('kpiDaSoHoa');

            elTongTim.textContent = Number(data.tong_luot_tim).toLocaleString('vi-VN');
            elTongTim.setAttribute('data-value', data.tong_luot_tim);

            elTiLe0.textContent = `${data.ti_le_khong_ket_qua}%`;
            elTiLe0.setAttribute('data-value', data.ti_le_khong_ket_qua);

            elLuotMuon.textContent = Number(data.luot_muon_dang_mo).toLocaleString('vi-VN');
            elLuotMuon.setAttribute('data-value', data.luot_muon_dang_mo);

            elDaSoHoa.textContent = `${Number(data.so_da_so_hoa).toLocaleString('vi-VN')} / ${Number(data.tong_tai_lieu).toLocaleString('vi-VN')}`;
            elDaSoHoa.setAttribute('data-value', data.so_da_so_hoa);
            elDaSoHoa.setAttribute('data-tong', data.tong_tai_lieu);
          }
        } catch (err) {
          console.warn('Lỗi nạp KPI tổng quan:', err);
        }
      }

      // -----------------------------------------------------------------------
      // B. WORD CLOUD TỪ KHÓA (wordcloud2.js - Kích thước theo căn bậc hai tần suất)
      // -----------------------------------------------------------------------
      async function loadWordCloud() {
        const wrapper = document.getElementById('wordcloudWrapper');
        const canvas = document.getElementById('wordcloudCanvas');
        const tooltip = document.getElementById('wordcloudTooltip');
        const emptyMsg = document.getElementById('wordcloudEmpty');
        if (!wrapper || !canvas) return;

        // Đảm bảo tooltip ẩn khi chuột rời khung Word Cloud
        if (!wrapper.dataset.hasLeaveListener) {
          wrapper.addEventListener('mouseleave', () => {
            if (tooltip) tooltip.style.display = 'none';
          });
          wrapper.dataset.hasLeaveListener = 'true';
        }

        try {
          const res = await fetch('/api/thong-ke/tu-khoa?limit=80', {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
          });
          if (!res.ok) throw new Error('Không thể tải từ khóa');
          const data = await res.json();
          const items = data.du_lieu || [];

          if (items.length === 0 || typeof WordCloud === 'undefined') {
            canvas.style.display = 'none';
            if (emptyMsg) {
              emptyMsg.style.display = 'block';
              emptyMsg.textContent = typeof WordCloud === 'undefined'
                ? 'Không thể tải thư viện Word Cloud.'
                : 'Không có đủ dữ liệu từ khóa để hiển thị Word Cloud.';
            }
            return;
          }

          canvas.style.display = 'block';
          if (emptyMsg) emptyMsg.style.display = 'none';

          // Chuẩn bị kích thước thực tế cho canvas
          const containerWidth = wrapper.clientWidth || 550;
          canvas.width = containerWidth;
          canvas.height = 320;

          // Tính toán căn bậc hai tần suất (AGENTS.md & Milestone M5)
          const isMobile = containerWidth < 500;
          const minFontSize = isMobile ? 11 : 13;
          const maxFontSize = isMobile ? 32 : 44;

          const frequencies = items.map(d => Number(d.so_lan) || 1);
          const sqrtValues = frequencies.map(f => Math.sqrt(f));
          const minSqrt = Math.min(...sqrtValues);
          const maxSqrt = Math.max(...sqrtValues);

          // Danh sách [từ khóa, tần suất] (trên mobile giới hạn 45 từ để vẽ sắc nét và không bị đè chữ)
          const displayItems = isMobile ? items.slice(0, 45) : items;
          const wordList = displayItems.map(d => [d.hien_thi || d.tu_khoa_chuan, Number(d.so_lan)]);

          // Vẽ Word Cloud bằng wordcloud2.js
          WordCloud(canvas, {
            list: wordList,
            gridSize: isMobile ? 6 : 8,
            fontFamily: 'Roboto, sans-serif',
            fontWeight: '600',
            weightFactor: function (size) {
              const sqrt = Math.sqrt(size);
              if (maxSqrt === minSqrt) return 20;
              const norm = (sqrt - minSqrt) / (maxSqrt - minSqrt);
              return Math.round(minFontSize + norm * (maxFontSize - minFontSize));
            },
            color: function (word, weight) {
              const sqrt = Math.sqrt(weight);
              const norm = maxSqrt === minSqrt ? 0.5 : (sqrt - minSqrt) / (maxSqrt - minSqrt);
              if (norm > 0.65) return PALETTE.primary;       // Nhóm tra cứu cao nhất: Đỏ đậm
              if (norm > 0.40) return PALETTE.primaryLight;  // Nhóm tra cứu cao: Đỏ tươi
              if (norm > 0.20) return PALETTE.accent;        // Nhóm khá: Vàng kim
              if (norm > 0.08) return PALETTE.lightRed;      // Nhóm vừa: Hồng đỏ nhạt
              return PALETTE.muted;                          // Nhóm ít: Xám xanh
            },
            backgroundColor: '#ffffff',
            rotateRatio: isMobile ? 0 : 0.25,
            rotationSteps: 2,
            drawOutOfBound: false,
            shrinkToFit: false,
            hover: function (item, dimension, evt) {
              canvas.style.cursor = item ? 'pointer' : 'default';
              if (item) {
                tooltip.style.display = 'block';
                tooltip.innerHTML = `<strong>${window.LibraryApp.escapeHtml(item[0])}</strong>: ${Number(item[1]).toLocaleString('vi-VN')} lượt tìm`;
                const rect = wrapper.getBoundingClientRect();
                const x = evt.clientX - rect.left + 10;
                const y = evt.clientY - rect.top - 30;
                tooltip.style.left = `${Math.max(10, Math.min(x, wrapper.clientWidth - 150))}px`;
                tooltip.style.top = `${Math.max(10, y)}px`;
              } else {
                tooltip.style.display = 'none';
              }
            },
            click: function (item) {
              if (item && item[0]) {
                window.location.href = `tra-cuu.html?q=${encodeURIComponent(item[0])}`;
              }
            }
          });
        } catch (err) {
          console.warn('Lỗi vẽ Word Cloud:', err);
          if (emptyMsg) {
            canvas.style.display = 'none';
            emptyMsg.style.display = 'block';
            emptyMsg.style.color = 'var(--status-danger)';
            emptyMsg.textContent = `Lỗi tải Word Cloud: ${err.message}`;
          }
        }
      }

      // -----------------------------------------------------------------------
      // C. TOP 15 TỪ KHÓA TÌM KIẾM NHIỀU NHẤT (Bar Chart ngang - Chart.js)
      // -----------------------------------------------------------------------
      async function loadTopKeywordsChart() {
        const canvas = document.getElementById('topKeywordsChart');
        if (!canvas) return;

        try {
          const res = await fetch('/api/thong-ke/tu-khoa?limit=15', {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
          });
          if (!res.ok) throw new Error('Không thể tải top 15 từ khóa');
          const data = await res.json();
          const items = data.du_lieu || [];

          const labels = items.map(d => d.hien_thi || d.tu_khoa_chuan);
          const values = items.map(d => Number(d.so_lan));

          // Bảng màu cột theo thứ hạng
          const backgroundColors = items.map((_, idx) => {
            if (idx === 0) return PALETTE.primary;
            if (idx < 3) return PALETTE.primaryLight;
            if (idx < 7) return PALETTE.accent;
            return PALETTE.muted;
          });

          if (topBarChartInstance) {
            topBarChartInstance.destroy();
          }

          const ctx = canvas.getContext('2d');
          topBarChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
              labels,
              datasets: [{
                label: 'Lượt tìm kiếm',
                data: values,
                backgroundColor: backgroundColors,
                borderWidth: 0,
                borderRadius: 4
              }]
            },
            options: {
              indexAxis: 'y',
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false },
                tooltip: {
                  callbacks: {
                    label: (context) => ` ${context.raw.toLocaleString('vi-VN')} lượt tra cứu`
                  }
                }
              },
              scales: {
                x: {
                  beginAtZero: true,
                  grid: { color: '#f1f5f9' },
                  ticks: {
                    precision: 0,
                    font: { size: 11 }
                  }
                },
                y: {
                  grid: { display: false },
                  ticks: {
                    font: { size: 12, weight: '500' },
                    color: '#2b354f'
                  }
                }
              }
            }
          });
        } catch (err) {
          console.warn('Lỗi vẽ biểu đồ Top 15:', err);
        }
      }

      // -----------------------------------------------------------------------
      // D. XU HƯỚNG TÌM KIẾM THEO THỜI GIAN (Line Chart - Chart.js có nút 7/30/90)
      // -----------------------------------------------------------------------
      async function loadTimelineChart(days = 30) {
        const canvas = document.getElementById('timelineChart');
        if (!canvas) return;

        try {
          const res = await fetch(`/api/thong-ke/theo-ngay?so_ngay=${days}`, {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
          });
          if (!res.ok) throw new Error('Không thể tải xu hướng theo ngày');
          const data = await res.json();
          const items = data.du_lieu || [];

          // Format ngày: YYYY-MM-DD -> DD/MM (đánh dấu ngày hôm nay là 'đang cập nhật')
          const labels = items.map((d, idx) => {
            const parts = d.ngay.split('-');
            const ddmm = `${parts[2]}/${parts[1]}`;
            if (idx === items.length - 1) {
              return `${ddmm} (đang cập nhật)`;
            }
            return ddmm;
          });
          const totalSearches = items.map(d => Number(d.so_luot));
          const zeroSearches = items.map(d => Number(d.so_luot_0_kq));

          if (timelineChartInstance) {
            timelineChartInstance.destroy();
          }

          const baseRadius = days === 90 ? 1.5 : (days === 30 ? 3 : 4);
          const ctx = canvas.getContext('2d');
          timelineChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
              labels,
              datasets: [
                {
                  label: 'Tổng lượt tìm kiếm',
                  data: totalSearches,
                  borderColor: PALETTE.primary,
                  backgroundColor: 'rgba(155, 28, 28, 0.08)',
                  fill: true,
                  tension: 0.25,
                  borderWidth: 2.2,
                  segment: {
                    borderDash: (sCtx) => sCtx.p1DataIndex === items.length - 1 ? [4, 4] : undefined
                  },
                  pointBackgroundColor: items.map((_, idx) => idx === items.length - 1 ? '#ffffff' : PALETTE.primary),
                  pointBorderColor: PALETTE.primary,
                  pointBorderWidth: items.map((_, idx) => idx === items.length - 1 ? 2.2 : 1.5),
                  pointRadius: items.map((_, idx) => idx === items.length - 1 ? baseRadius + 1.5 : baseRadius),
                  pointHoverRadius: 6
                },
                {
                  label: 'Tìm không có kết quả (0 KQ)',
                  data: zeroSearches,
                  borderColor: PALETTE.accent,
                  backgroundColor: 'rgba(212, 175, 55, 0.05)',
                  borderDash: [5, 4],
                  fill: false,
                  tension: 0.25,
                  borderWidth: 2,
                  pointBackgroundColor: items.map((_, idx) => idx === items.length - 1 ? '#ffffff' : PALETTE.accent),
                  pointBorderColor: PALETTE.accent,
                  pointBorderWidth: 1.5,
                  pointRadius: days === 90 ? 1.5 : (days === 30 ? 2.5 : 3.5),
                  pointHoverRadius: 5
                }
              ]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              interaction: {
                mode: 'index',
                intersect: false
              },
              plugins: {
                legend: {
                  position: 'top',
                  labels: {
                    usePointStyle: true,
                    boxWidth: 8,
                    font: { size: 12, weight: '500' }
                  }
                },
                tooltip: {
                  callbacks: {
                    label: (context) => {
                      const suffix = context.dataIndex === items.length - 1 ? ' (ngày hôm nay đang cập nhật)' : '';
                      return ` ${context.dataset.label}: ${context.raw.toLocaleString('vi-VN')} lượt${suffix}`;
                    }
                  }
                }
              },
              scales: {
                x: {
                  grid: { color: '#f8fafc' },
                  ticks: {
                    font: { size: 11 },
                    maxTicksLimit: days === 90 ? 15 : (days === 30 ? 10 : 7)
                  }
                },
                y: {
                  beginAtZero: true,
                  grid: { color: '#f1f5f9' },
                  ticks: {
                    precision: 0,
                    font: { size: 11 }
                  }
                }
              }
            },
            plugins: [{
              id: 'todayUpdatingLabel',
              afterDatasetsDraw(chart) {
                const meta = chart.getDatasetMeta(0);
                if (!meta || !meta.data || meta.data.length === 0) return;
                const lastPoint = meta.data[meta.data.length - 1];
                if (!lastPoint) return;
                const c = chart.ctx;
                c.save();
                c.font = '600 10.5px Roboto, sans-serif';
                c.fillStyle = PALETTE.primary;
                c.textAlign = 'right';
                c.fillText('Đang cập nhật', lastPoint.x - 8, Math.max(18, lastPoint.y - 8));
                c.restore();
              }
            }]
          });
        } catch (err) {
          console.warn('Lỗi vẽ biểu đồ xu hướng theo ngày:', err);
        }
      }

      // Lắng nghe sự kiện bấm nút lọc mốc ngày 7/30/90
      document.querySelectorAll('#timelineFilterPills .filter-pill').forEach(btn => {
        btn.addEventListener('click', () => {
          document.querySelectorAll('#timelineFilterPills .filter-pill').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          const days = parseInt(btn.getAttribute('data-days'), 10) || 30;
          currentTimelineDays = days;
          loadTimelineChart(days);
        });
      });

      // -----------------------------------------------------------------------
      // E. BẢNG TỪ KHÓA TÌM NHIỀU NHƯNG 0 KẾT QUẢ (Gợi ý mua/bổ sung)
      // -----------------------------------------------------------------------
      async function loadZeroResultsTable() {
        const tbody = document.getElementById('zeroResultsTableBody');
        try {
          const res = await fetch('/api/thong-ke/khong-ket-qua?limit=15', {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
          });
          if (!res.ok) throw new Error('Không thể tải từ khóa 0 kết quả');
          const data = await res.json();
          const items = data.du_lieu || [];

          if (items.length === 0) {
            tbody.innerHTML = `
              <tr>
                <td colspan="5" style="text-align: center; padding: 25px; color: var(--color-text-muted);">
                  Không có từ khóa nào trả về 0 kết quả.
                </td>
              </tr>
            `;
            return;
          }

          let html = '';
          items.forEach((item, index) => {
            html += `
              <tr>
                <td style="text-align: center; font-weight: 600; color: var(--color-text-muted);">${index + 1}</td>
                <td>
                  <strong style="color: var(--color-primary-dark); font-size: 0.92rem;">
                    ${window.LibraryApp.escapeHtml(item.hien_thi || item.tu_khoa_chuan)}
                  </strong>
                  ${item.hien_thi !== item.tu_khoa_chuan ? `<br><small style="color: var(--color-text-muted); font-family: monospace;">(${window.LibraryApp.escapeHtml(item.tu_khoa_chuan)})</small>` : ''}
                </td>
                <td style="text-align: center;">
                  <span class="badge" style="background: #fef3c7; color: #b45309; font-weight: 700;">
                    ${Number(item.so_lan).toLocaleString('vi-VN')}
                  </span>
                </td>
                <td style="text-align: center; font-size: 0.82rem; color: var(--color-text-muted);">
                  ${window.LibraryApp.formatDate(item.lan_cuoi)}
                </td>
                <td style="text-align: center;">
                  <span class="badge" style="background: #fee2e2; color: #9b1c1c; font-size: 0.78rem;">
                    <i class="fa-solid fa-cart-plus"></i> Cần bổ sung
                  </span>
                </td>
              </tr>
            `;
          });

          tbody.innerHTML = html;
        } catch (err) {
          tbody.innerHTML = `
            <tr>
              <td colspan="5" style="text-align: center; padding: 20px; color: var(--status-danger);">
                Lỗi tải bảng: ${window.LibraryApp.escapeHtml(err.message)}
              </td>
            </tr>
          `;
        }
      }

      // -----------------------------------------------------------------------
      // F. BẢNG TƯ LIỆU NÊN SỐ HÓA (diem = so_lan_chon + 2 * so_luot_muon)
      //    Có nút "Số hóa" dẫn tới form tải bản mềm trên quan-ly.html
      // -----------------------------------------------------------------------
      async function loadShouldDigitizeTable() {
        const tbody = document.getElementById('shouldDigitizeTableBody');
        try {
          const res = await fetch('/api/thong-ke/nen-so-hoa?limit=15', {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
          });
          if (!res.ok) throw new Error('Không thể tải danh sách đề xuất số hóa');
          const data = await res.json();
          const items = data.du_lieu || [];

          if (items.length === 0) {
            tbody.innerHTML = `
              <tr>
                <td colspan="7" style="text-align: center; padding: 30px; color: var(--color-text-muted);">
                  Tất cả tư liệu có nhu cầu cao đã được số hóa hoặc không còn tư liệu chờ số hóa.
                </td>
              </tr>
            `;
            return;
          }

          let html = '';
          items.forEach((item) => {
            html += `
              <tr data-doc-id="${item.tai_lieu_id}">
                <td>
                  <code style="font-size: 0.8rem; background: #f1f5f9; padding: 2px 6px; border-radius: 3px;">
                    ${window.LibraryApp.escapeHtml(item.ky_hieu || 'TL.' + item.tai_lieu_id)}
                  </code>
                </td>
                <td>
                  <a href="chi-tiet.html?id=${item.tai_lieu_id}" target="_blank" style="font-weight: 600; color: var(--color-primary-dark); font-size: 0.92rem;">
                    ${window.LibraryApp.escapeHtml(item.tieu_de)}
                  </a>
                  <div style="font-size: 0.78rem; margin-top: 2px;">
                    <span class="badge" style="background: #f1f5f9; padding: 1px 6px; color: var(--color-text-muted);">
                      ${window.LibraryApp.formatLoaiHinh(item.loai_hinh)}
                    </span>
                  </div>
                </td>
                <td style="font-size: 0.85rem;">
                  <div>${window.LibraryApp.escapeHtml(item.tac_gia || '---')}</div>
                  <small style="color: var(--color-text-muted);">${item.nam || ''}</small>
                </td>
                <td style="text-align: center; font-weight: 500;">
                  ${Number(item.so_lan_chon).toLocaleString('vi-VN')}
                </td>
                <td style="text-align: center; font-weight: 500;">
                  ${Number(item.so_luot_muon).toLocaleString('vi-VN')}
                </td>
                <td style="text-align: center;">
                  <span class="badge" style="background: #fee2e2; color: #9b1c1c; font-weight: 700; font-size: 0.9rem;">
                    ${item.diem}
                  </span>
                </td>
                <td style="text-align: center;">
                  <a href="quan-ly.html?so_hoa_id=${item.tai_lieu_id}" class="btn-so-hoa" data-doc-id="${item.tai_lieu_id}" title="Tải bản mềm số hóa cho tư liệu #${item.tai_lieu_id}">
                    <i class="fa-solid fa-cloud-arrow-up"></i> Số hóa
                  </a>
                </td>
              </tr>
            `;
          });

          tbody.innerHTML = html;
        } catch (err) {
          tbody.innerHTML = `
            <tr>
              <td colspan="7" style="text-align: center; padding: 25px; color: var(--status-danger);">
                Lỗi tải bảng: ${window.LibraryApp.escapeHtml(err.message)}
              </td>
            </tr>
          `;
        }
      }

      // Khởi chạy tất cả các khối dữ liệu
      await Promise.all([
        loadKpiSummary(),
        loadWordCloud(),
        loadTopKeywordsChart(),
        loadTimelineChart(30),
        loadZeroResultsTable(),
        loadShouldDigitizeTable()
      ]);

      // Xử lý vẽ lại Word Cloud khi thay đổi kích thước cửa sổ (debounce)
      let resizeTimer = null;
      window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
          loadWordCloud();
        }, 300);
      });
    });
  
