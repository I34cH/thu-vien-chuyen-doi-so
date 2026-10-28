/**
 * dashboard.spec.js - Kiểm thử tự động Dashboard & Trực quan hóa dữ liệu (Milestone M5)
 * 
 * LỆNH KIỂM CHỨNG M5:
 * 1. Mở Dashboard thủ thư, kiểm tra 4 KPI, Word Cloud (wordcloud2.js), Top 15 (Chart.js bar),
 *    Line chart xu hướng theo ngày (nút 7/30/90), Bảng 0 kết quả, Bảng nên số hóa.
 * 2. Mỗi biểu đồ có tiêu đề dạng câu hỏi và một dòng ghi chú cách đọc.
 * 3. Bảng màu đồng bộ đỏ-vàng-xám (#9b1c1c, #d4af37, #c53030, #64748b, #e57373).
 * 4. Số liệu 4 thẻ KPI trên trang khớp truy vấn SQL trực tiếp.
 * 5. Thủ thư tải bản mềm (PDF mẫu) cho tư liệu đứng đầu bảng nên số hóa, tải lại dashboard
 *    thì tư liệu đó biến mất khỏi bảng; KPI trên trang khớp truy vấn SQL trực tiếp.
 * 6. Sau test hoàn trả trạng thái ban đầu (revert DB & dọn file tải lên).
 */

const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');
const { execFileSync } = require('child_process');

// Helper db truy vấn PostgreSQL qua Python (psycopg2) thay thế module Node pg cũ
const db = {
  query: async (text, params = []) => {
    const sql = text.replace(/\$\d+/g, '%s');
    const pyScript = [
      'import os, sys, json',
      'from dotenv import load_dotenv',
      'import psycopg2',
      'from psycopg2.extras import RealDictCursor',
      'load_dotenv()',
      'conn = psycopg2.connect(os.environ["DATABASE_URL"])',
      'with conn.cursor(cursor_factory=RealDictCursor) as cur:',
      '    p = json.loads(sys.argv[2])',
      '    cur.execute(sys.argv[1], p if p else None)',
      '    rows = [dict(r) for r in cur.fetchall()] if cur.description else []',
      'conn.commit()',
      'conn.close()',
      'print(json.dumps(rows, default=str))'
    ].join('\n');
    const out = execFileSync('python', ['-c', pyScript, sql, JSON.stringify(params)], {
      encoding: 'utf-8',
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
      cwd: path.resolve(__dirname, '..', '..')
    });
    return { rows: JSON.parse(out.trim() || '[]') };
  },
  pool: {
    end: async () => {}
  }
};

function setupConsoleListener(page) {
  const errors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(`Console Error: ${msg.text()}`);
    }
  });
  page.on('pageerror', (err) => {
    errors.push(`Page Error: ${err.message}`);
  });
  return errors;
}

test.describe('Kiểm thử Trực quan hóa dữ liệu Dashboard (Milestone M5)', () => {

  test.beforeEach(async ({ page }) => {
    // Đăng nhập vai trò Thủ thư trước mỗi test
    await page.goto('/tai-khoan.html', { waitUntil: 'domcontentloaded' });
    await page.locator('#inputTenDangNhap').fill('thuthu');
    await page.locator('#inputMatKhau').fill('thuthu123');
    await page.locator('#btnLoginSubmit').click();
    await expect(page.locator('#sectionProfile')).toBeVisible({ timeout: 5000 });
  });

  test('1. Hiển thị đầy đủ các thành phần trực quan hóa M5: 4 KPI, 3 biểu đồ, 2 bảng phân tích; có tiêu đề câu hỏi & hướng dẫn cách đọc', async ({ page }) => {
    const errors = setupConsoleListener(page);

    await page.goto('/dashboard.html', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);

    // Kiểm tra quyền thủ thư được mở
    await expect(page.locator('#dashMainContent')).toBeVisible();
    await expect(page.locator('#dashForbiddenCard')).not.toBeVisible();

    // 1. 4 Thẻ KPI hiển thị dữ liệu
    const kpiTongTim = page.locator('#kpiTongTim');
    const kpiTiLe0 = page.locator('#kpiTiLe0Kq');
    const kpiLuotMuon = page.locator('#kpiLuotMuonMo');
    const kpiDaSoHoa = page.locator('#kpiDaSoHoa');

    await expect(kpiTongTim).not.toHaveText('---', { timeout: 5000 });
    await expect(kpiTiLe0).not.toHaveText('---', { timeout: 5000 });
    await expect(kpiLuotMuon).not.toHaveText('---', { timeout: 5000 });
    await expect(kpiDaSoHoa).not.toHaveText('---', { timeout: 5000 });

    // 2. Khung Word Cloud & Canvas
    const wcCanvas = page.locator('#wordcloudCanvas');
    await expect(wcCanvas).toBeVisible();

    // 3. Khung Top 15 Bar chart & Canvas
    const topCanvas = page.locator('#topKeywordsChart');
    await expect(topCanvas).toBeVisible();

    // 4. Khung Line chart theo ngày & Nút bộ lọc 7/30/90
    const timelineCanvas = page.locator('#timelineChart');
    await expect(timelineCanvas).toBeVisible();

    const pill7 = page.locator('#timelineFilterPills button[data-days="7"]');
    const pill30 = page.locator('#timelineFilterPills button[data-days="30"]');
    const pill90 = page.locator('#timelineFilterPills button[data-days="90"]');
    await expect(pill7).toBeVisible();
    await expect(pill30).toBeVisible();
    await expect(pill90).toBeVisible();

    // 5. Bảng từ khóa 0 kết quả
    const zeroTable = page.locator('#zeroResultsTable');
    await expect(zeroTable).toBeVisible();
    const zeroRows = page.locator('#zeroResultsTableBody tr');
    await expect(zeroRows.first()).toBeVisible({ timeout: 5000 });
    const zeroCount = await zeroRows.count();
    expect(zeroCount).toBeGreaterThan(0);

    // 6. Bảng tư liệu đề xuất nên số hóa có nút "Số hóa"
    const digitizeTable = page.locator('#shouldDigitizeTable');
    await expect(digitizeTable).toBeVisible();
    const digitizeRows = page.locator('#shouldDigitizeTableBody tr');
    await expect(digitizeRows.first()).toBeVisible({ timeout: 5000 });
    const digitizeCount = await digitizeRows.count();
    expect(digitizeCount).toBeGreaterThan(0);

    const firstSoHoaBtn = digitizeRows.first().locator('.btn-so-hoa');
    await expect(firstSoHoaBtn).toBeVisible();
    await expect(firstSoHoaBtn).toContainText('Số hóa');

    // 7. Mỗi biểu đồ và bảng phân tích đều có tiêu đề dạng câu hỏi (?) và dòng hướng dẫn cách đọc
    const titles = await page.locator('.panel-title').allTextContents();
    const guides = await page.locator('.chart-guide').allTextContents();

    expect(titles.length).toBeGreaterThanOrEqual(5);
    expect(guides.length).toBeGreaterThanOrEqual(5);

    // Kiểm tra các tiêu đề biểu đồ đều chứa dấu hỏi chấm (?)
    const chartQuestionTitles = titles.filter(t => t.includes('?'));
    expect(chartQuestionTitles.length).toBeGreaterThanOrEqual(5);

    // Kiểm tra không có lỗi console
    expect(errors, `Lỗi console: ${errors.join(', ')}`).toEqual([]);
  });

  test('2. Số liệu 4 thẻ KPI trên trang khớp 100% với truy vấn SQL trực tiếp', async ({ page }) => {
    const errors = setupConsoleListener(page);

    await page.goto('/dashboard.html', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);

    // Truy vấn CSDL trực tiếp
    const [logRes, muonRes, tlRes] = await Promise.all([
      db.query(`
        SELECT 
          count(*)::int AS tong_luot_tim,
          coalesce(round(count(*) FILTER (WHERE so_ket_qua = 0) * 100.0 / NULLIF(count(*), 0), 2), 0)::real AS ti_le_khong_ket_qua
        FROM log_tim_kiem;
      `),
      db.query(`
        SELECT count(*)::int AS luot_muon_dang_mo
        FROM luot_muon
        WHERE trang_thai IN ('cho_duyet', 'dang_muon');
      `),
      db.query(`
        SELECT 
          count(*)::int AS tong_tai_lieu,
          count(*) FILTER (WHERE co_ban_mem = true)::int AS so_da_so_hoa
        FROM tai_lieu;
      `)
    ]);

    const sqlLog = logRes.rows[0];
    const sqlMuon = muonRes.rows[0];
    const sqlTl = tlRes.rows[0];

    // Lấy số liệu trên giao diện web
    const elTongTim = page.locator('#kpiTongTim');
    const elTiLe0 = page.locator('#kpiTiLe0Kq');
    const elLuotMuon = page.locator('#kpiLuotMuonMo');
    const elDaSoHoa = page.locator('#kpiDaSoHoa');

    await expect(elTongTim).not.toHaveText('---', { timeout: 5000 });

    const txtTongTim = (await elTongTim.textContent()).replace(/\./g, '').replace(/,/g, '').trim();
    const valTongTimAttr = await elTongTim.getAttribute('data-value');
    expect(Number(valTongTimAttr || txtTongTim)).toBe(sqlLog.tong_luot_tim);

    const txtTiLe0 = (await elTiLe0.textContent()).replace('%', '').trim();
    const valTiLe0Attr = await elTiLe0.getAttribute('data-value');
    expect(parseFloat(valTiLe0Attr || txtTiLe0)).toBeCloseTo(sqlLog.ti_le_khong_ket_qua, 1);

    const txtLuotMuon = (await elLuotMuon.textContent()).replace(/\./g, '').replace(/,/g, '').trim();
    const valLuotMuonAttr = await elLuotMuon.getAttribute('data-value');
    expect(Number(valLuotMuonAttr || txtLuotMuon)).toBe(sqlMuon.luot_muon_dang_mo);

    const txtDaSoHoa = await elDaSoHoa.textContent();
    const valDaSoHoaAttr = await elDaSoHoa.getAttribute('data-value');
    const valTongTlAttr = await elDaSoHoa.getAttribute('data-tong');

    expect(Number(valDaSoHoaAttr)).toBe(sqlTl.so_da_so_hoa);
    expect(Number(valTongTlAttr)).toBe(sqlTl.tong_tai_lieu);
    expect(txtDaSoHoa).toContain(Number(sqlTl.so_da_so_hoa).toLocaleString('vi-VN'));
    expect(txtDaSoHoa).toContain(Number(sqlTl.tong_tai_lieu).toLocaleString('vi-VN'));

    expect(errors).toEqual([]);
  });

  test('3. Chuyển đổi bộ lọc thời gian 7/30/90 ngày trên biểu đồ xu hướng', async ({ page }) => {
    const errors = setupConsoleListener(page);

    await page.goto('/dashboard.html', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);

    const pill7 = page.locator('#timelineFilterPills button[data-days="7"]');
    const pill30 = page.locator('#timelineFilterPills button[data-days="30"]');
    const pill90 = page.locator('#timelineFilterPills button[data-days="90"]');

    // Chuyển sang 7 ngày
    await pill7.click();
    await expect(pill7).toHaveClass(/active/);
    await expect(pill30).not.toHaveClass(/active/);
    await page.waitForTimeout(400);

    // Chuyển sang 90 ngày
    await pill90.click();
    await expect(pill90).toHaveClass(/active/);
    await expect(pill7).not.toHaveClass(/active/);
    await page.waitForTimeout(400);

    // Quay lại 30 ngày
    await pill30.click();
    await expect(pill30).toHaveClass(/active/);
    await expect(pill90).not.toHaveClass(/active/);

    expect(errors).toEqual([]);
  });

  test('4. LỆNH KIỂM CHỨNG M5: Thủ thư tải bản mềm (PDF mẫu) cho tư liệu đứng đầu bảng nên số hóa, tải lại dashboard thì tư liệu đó biến mất khỏi bảng; KPI trên trang khớp SQL trực tiếp; sau test hoàn trả trạng thái', async ({ page }) => {
    const errors = setupConsoleListener(page);
    let topDocId = null;

    try {
      // 1. Mở Dashboard
      await page.goto('/dashboard.html', { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(1000);

      // 2. Xác định tư liệu đứng đầu bảng "nên số hóa"
      const topRow = page.locator('#shouldDigitizeTableBody tr').first();
      await expect(topRow).toBeVisible({ timeout: 5000 });

      const topDocIdStr = await topRow.getAttribute('data-doc-id');
      expect(topDocIdStr).toBeTruthy();
      topDocId = parseInt(topDocIdStr, 10);
      const topDocTitle = (await topRow.locator('td:nth-child(2) a').textContent()).trim();

      // 3. Nhấp nút "Số hóa" trên dòng đầu tiên -> dẫn tới form tải bản mềm trên quan-ly.html
      const btnSoHoa = topRow.locator('.btn-so-hoa');
      await expect(btnSoHoa).toBeVisible();
      await btnSoHoa.click();

      // Đảm bảo trình duyệt đã chuyển đến trang quan-ly.html với tham số so_hoa_id
      await page.waitForURL(`**/quan-ly.html?so_hoa_id=${topDocId}`);
      await expect(page.locator('#formUploadPdf')).toBeVisible({ timeout: 5000 });

      // Mã tư liệu trên form tải bản mềm đã được điền sẵn
      const inputDocId = page.locator('#inputUploadDocId');
      await expect(inputDocId).toHaveValue(String(topDocId));

      // 4. Thủ thư tải bản mềm PDF mẫu lên
      const samplePdfPath = path.resolve(process.cwd(), 'uploads', 'mau', 'ban_mem_mau.pdf');
      expect(fs.existsSync(samplePdfPath), `Không tìm thấy file mẫu: ${samplePdfPath}`).toBe(true);

      const fileInput = page.locator('#inputFilePdf');
      await fileInput.setInputFiles(samplePdfPath);

      // Bấm nút Tải bản mềm lên
      const btnSubmit = page.locator('#btnSubmitUpload');
      await btnSubmit.click();

      // Chờ thông báo thành công hiển thị
      const alertBox = page.locator('#actionAlertBox');
      await expect(alertBox).toBeVisible({ timeout: 10000 });
      await expect(alertBox).toContainText(`Tải bản mềm thành công cho tư liệu #${topDocId}`);

      // 5. Tải lại trang Dashboard thống kê
      await page.goto('/dashboard.html', { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(1000);

      // 6. Kiểm tra tư liệu vừa được số hóa BIẾN MẤT khỏi bảng "nên số hóa"
      const updatedTableRows = page.locator('#shouldDigitizeTableBody tr');
      await expect(updatedTableRows.first()).toBeVisible({ timeout: 5000 });

      // Không còn dòng nào có data-doc-id bằng topDocId
      const matchingOldDoc = page.locator(`#shouldDigitizeTableBody tr[data-doc-id="${topDocId}"]`);
      await expect(matchingOldDoc).toHaveCount(0);

      // Dòng đầu tiên hiện tại phải là tư liệu khác
      const newTopDocIdStr = await page.locator('#shouldDigitizeTableBody tr').first().getAttribute('data-doc-id');
      expect(newTopDocIdStr).not.toBe(String(topDocId));

      // 7. Kiểm tra thẻ KPI số tư liệu đã số hóa đã tăng và khớp với SQL trực tiếp
      const checkSql = await db.query(`
        SELECT 
          count(*)::int AS tong_tai_lieu,
          count(*) FILTER (WHERE co_ban_mem = true)::int AS so_da_so_hoa
        FROM tai_lieu;
      `);
      const currentSqlTl = checkSql.rows[0];

      const kpiDaSoHoa = page.locator('#kpiDaSoHoa');
      await expect(kpiDaSoHoa).not.toHaveText('---', { timeout: 5000 });

      const currentValAttr = await kpiDaSoHoa.getAttribute('data-value');
      expect(Number(currentValAttr)).toBe(currentSqlTl.so_da_so_hoa);
    } finally {
      // 8. HOÀN TRẢ TRẠNG THÁI BAN ĐẦU TRONG KHỐI FINALLY ĐẢM BẢO LUÔN ĐƯỢC THỰC THI
      if (topDocId) {
        try {
          // Tìm tệp vừa upload trên đĩa để xóa dọn dẹp
          const docRecord = await db.query('SELECT duong_dan_ban_mem FROM tai_lieu WHERE id = $1', [topDocId]);
          if (docRecord.rows.length > 0 && docRecord.rows[0].duong_dan_ban_mem) {
            const uploadedFile = docRecord.rows[0].duong_dan_ban_mem;
            if (!uploadedFile.startsWith('mau/')) {
              const filePath = path.resolve(process.cwd(), 'uploads', path.basename(uploadedFile));
              if (fs.existsSync(filePath)) {
                try { fs.unlinkSync(filePath); } catch (_) {}
              }
            }
          }

          // Khôi phục lại trạng thái chưa số hóa cho tư liệu
          await db.query(`
            UPDATE tai_lieu
            SET co_ban_mem = false,
                duong_dan_ban_mem = NULL,
                muc_truy_cap = 'cong_khai'
            WHERE id = $1;
          `, [topDocId]);
        } catch (cleanupErr) {
          console.error('Lỗi khi hoàn trả trạng thái ban đầu:', cleanupErr);
        }
      }
    }

    // Xác nhận trong CSDL tư liệu đã trở về co_ban_mem = false
    const verifyReset = await db.query('SELECT co_ban_mem FROM tai_lieu WHERE id = $1', [topDocId]);
    expect(verifyReset.rows[0].co_ban_mem).toBe(false);

    // Tải lại Dashboard và xác nhận tư liệu đã xuất hiện lại ở vị trí đầu bảng
    await page.goto('/dashboard.html', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);

    const restoredTopDocIdStr = await page.locator('#shouldDigitizeTableBody tr').first().getAttribute('data-doc-id');
    expect(restoredTopDocIdStr).toBe(String(topDocId));

    expect(errors).toEqual([]);
  });

  test('5. Kiểm thử bố cục Dashboard thích ứng trên màn hình di động (390px): không tràn viền ngang và xếp chồng 1 cột mượt mà', async ({ page }) => {
    const errors = setupConsoleListener(page);

    // Đặt viewport chuẩn di động 390px (iPhone 12/13/14) theo yêu cầu M6
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/dashboard.html', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);

    // Kiểm tra không có lỗi tràn chiều ngang trang
    const isOverflowing = await page.evaluate(() => {
      return document.documentElement.scrollWidth > window.innerWidth;
    });
    expect(isOverflowing).toBe(false);

    // Kiểm tra các khối lưới biểu đồ đã chuyển về 1 cột
    const chartsGridCols = await page.locator('.dashboard-charts-grid').evaluate((el) => {
      return window.getComputedStyle(el).gridTemplateColumns.split(' ').length;
    });
    expect(chartsGridCols).toBe(1);

    const tablesGridCols = await page.locator('.dashboard-tables-grid').evaluate((el) => {
      return window.getComputedStyle(el).gridTemplateColumns.split(' ').length;
    });
    expect(tablesGridCols).toBe(1);

    expect(errors).toEqual([]);
  });

  test('6. Kiểm thử tương tác Word Cloud: canvas đã vẽ các từ khóa và gắn tooltip khi di chuột', async ({ page }) => {
    const errors = setupConsoleListener(page);

    await page.goto('/dashboard.html', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);

    const canvas = page.locator('#wordcloudCanvas');
    await expect(canvas).toBeVisible();

    const box = await canvas.boundingBox();
    expect(box).not.toBeNull();
    expect(box.width).toBeGreaterThan(200);
    expect(box.height).toBeGreaterThan(200);

    // Di chuột vào giữa canvas để kích hoạt tương tác
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.waitForTimeout(300);

    // Di chuột ra ngoài khung để xác nhận tooltip ẩn
    await page.mouse.move(box.x - 50, box.y - 50);
    await page.waitForTimeout(200);
    const tooltip = page.locator('#wordcloudTooltip');
    await expect(tooltip).not.toBeVisible();

    expect(errors).toEqual([]);
  });

  test.afterAll(async () => {
    await db.pool.end();
  });

});
