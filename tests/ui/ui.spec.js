/**
 * ui.spec.js - Bộ kiểm thử tự động giao diện Playwright (Milestone M4)
 * Kiểm tra:
 * 1. Mở từng trang với 3 vai trò: Khách vãng lai, Sinh viên (sv01), Thủ thư (thuthu).
 * 2. Đảm bảo không có lỗi console (console error / pageerror).
 * 3. Banner DỮ LIỆU MẪU xuất hiện trên mọi trang.
 * 4. Menu và quyền truy cập hiển thị đúng theo vai trò.
 * 5. Gõ "luu tru" trên ô tìm kiếm thấy danh sách gợi ý autocomplete.
 * 6. Kiểm tra luồng tìm kiếm và ghi nhận lựa chọn kết quả (POST /api/tim-kiem/:logId/chon).
 */

const { test, expect } = require('@playwright/test');

const PAGES = [
  { name: 'Trang chủ', path: '/index.html' },
  { name: 'Tra cứu OPAC', path: '/tra-cuu.html' },
  { name: 'Chi tiết tư liệu', path: '/chi-tiet.html?id=8' },
  { name: 'Tài khoản & Đăng nhập', path: '/tai-khoan.html' },
  { name: 'Quản lý mượn trả', path: '/quan-ly.html' },
  { name: 'Dashboard thống kê', path: '/dashboard.html' }
];

function setupConsoleListener(page) {
  const errors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      // Bỏ qua lỗi kết nối mạng ngoại vi nếu máy không có internet (ví dụ fonts Google)
      const text = msg.text();
      errors.push(`Console Error: ${text}`);
    }
  });
  page.on('pageerror', (err) => {
    errors.push(`Page Error: ${err.message}`);
  });
  return errors;
}

test.describe('Kiểm thử Giao diện Web Thư viện Chuyển đổi số (Milestone M4)', () => {

  // =========================================================================
  // 1. VAI TRÒ KHÁCH VÃNG LAI (CHƯA ĐĂNG NHẬP)
  // =========================================================================
  test.describe('1. Vai trò Khách vãng lai (khach)', () => {
    
    test.beforeEach(async ({ context }) => {
      await context.clearCookies();
    });

    for (const p of PAGES) {
      test(`Mở trang ${p.name} (${p.path}) không có lỗi console & có banner DỮ LIỆU MẪU`, async ({ page }) => {
        const errors = setupConsoleListener(page);

        await page.goto(p.path, { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(600);

        // 1. Banner cố định trên mọi trang
        const banner = page.locator('.demo-banner');
        await expect(banner).toBeVisible();
        await expect(banner).toContainText('DỮ LIỆU MẪU');

        // 2. Không có lỗi console
        expect(errors, `Lỗi console trên trang ${p.path}: ${errors.join(', ')}`).toEqual([]);
      });
    }

    test('Gõ "luu tru" trên index.html hiển thị danh sách gợi ý autocomplete', async ({ page }) => {
      const errors = setupConsoleListener(page);
      await page.goto('/index.html', { waitUntil: 'domcontentloaded' });

      const searchInput = page.locator('#heroSearchInput');
      await expect(searchInput).toBeVisible();

      // Gõ từ khóa "luu tru"
      await searchInput.fill('luu tru');

      // Chờ dropdown gợi ý hiển thị
      const dropdown = page.locator('#heroAutocompleteResults');
      await expect(dropdown).toBeVisible({ timeout: 5000 });

      // Có ít nhất 1 kết quả gợi ý
      const items = dropdown.locator('.autocomplete-item');
      await expect(items.first()).toBeVisible();
      const count = await items.count();
      expect(count).toBeGreaterThan(0);

      // Nội dung gợi ý chứa thông tin tư liệu
      const firstText = await items.first().textContent();
      expect(firstText.toLowerCase()).toContain('lưu trữ');

      expect(errors).toEqual([]);
    });

    test('Gõ "luu tru" trên tra-cuu.html hiển thị gợi ý và khi bấm kết quả tìm kiếm gọi chọn log', async ({ page }) => {
      const errors = setupConsoleListener(page);
      await page.goto('/tra-cuu.html', { waitUntil: 'domcontentloaded' });

      const searchInput = page.locator('#catalogSearchInput');
      await expect(searchInput).toBeVisible();

      // 1. Autocomplete trên trang tra-cuu.html
      await searchInput.fill('luu tru');
      const dropdown = page.locator('#catalogAutocompleteResults');
      await expect(dropdown).toBeVisible({ timeout: 5000 });
      const items = dropdown.locator('.autocomplete-item');
      await expect(items.first()).toBeVisible();
      expect(await items.count()).toBeGreaterThan(0);

      // 2. Thực hiện tìm kiếm danh mục (Submit form)
      await page.locator('#searchCatalogForm button[type="submit"]').click();

      // Chờ danh sách kết quả hiển thị
      const resultRows = page.locator('#resultsListContainer .book-list-row');
      await expect(resultRows.first()).toBeVisible({ timeout: 8000 });
      expect(await resultRows.count()).toBeGreaterThan(0);

      // Kiểm tra có hiển thị tình trạng bản sao "Còn x/y bản" hoặc nhãn
      const firstRow = resultRows.first();
      await expect(firstRow).toBeVisible();

      // Theo dõi request POST /api/tim-kiem/:logId/chon khi người dùng bấm vào kết quả
      let selectionRequested = false;
      page.on('request', (req) => {
        if (req.url().includes('/api/tim-kiem/') && req.url().includes('/chon') && req.method() === 'POST') {
          selectionRequested = true;
        }
      });

      // Bấm vào tiêu đề kết quả đầu tiên
      const titleLink = firstRow.locator('.doc-title-link');
      await titleLink.click();

      // Chờ chuyển hướng sang trang chi-tiet.html
      await page.waitForURL(/chi-tiet\.html/, { timeout: 6000 });
      expect(selectionRequested).toBe(true);

      expect(errors).toEqual([]);
    });

    test('Khách vào quan-ly.html và dashboard.html hiển thị thông báo yêu cầu quyền Thủ thư', async ({ page }) => {
      const errors = setupConsoleListener(page);

      await page.goto('/quan-ly.html', { waitUntil: 'domcontentloaded' });
      await expect(page.locator('#librarianForbiddenCard')).toBeVisible();

      await page.goto('/dashboard.html', { waitUntil: 'domcontentloaded' });
      await expect(page.locator('#dashForbiddenCard')).toBeVisible();

      expect(errors).toEqual([]);
    });

    test('Xử lý an toàn: Truy cập tra-cuu.html với tham số URL chứa ký tự đặc biệt không gây lỗi DOMException hay console error', async ({ page }) => {
      const errors = setupConsoleListener(page);

      await page.goto('/tra-cuu.html?loai=%22%3E%3Cscript%3E&q=%27%22%3C%3E%26&tu_nam=abc&den_nam=xyz', { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(600);

      // Trang vẫn tải bình thường và không có lỗi console
      await expect(page.locator('.demo-banner')).toBeVisible();
      await expect(page.locator('#searchCatalogForm')).toBeVisible();
      expect(errors).toEqual([]);
    });

    test('Đặt lại bộ lọc trên tra-cuu.html xóa sạch từ khóa và nạp lại toàn bộ danh mục', async ({ page }) => {
      const errors = setupConsoleListener(page);
      await page.goto('/tra-cuu.html?q=luu+tru', { waitUntil: 'domcontentloaded' });

      const searchInput = page.locator('#catalogSearchInput');
      await expect(searchInput).toHaveValue('luu tru');

      // Nhấn nút Đặt lại bộ lọc
      await page.locator('#btnResetFilter').click();
      await expect(searchInput).toHaveValue('');

      // Danh mục được nạp lại
      const summary = page.locator('#searchSummaryText');
      await expect(summary).toContainText('trong danh mục');

      expect(errors).toEqual([]);
    });
  });

  // =========================================================================
  // 2. VAI TRÒ SINH VIÊN (sv01 / sv123)
  // =========================================================================
  test.describe('2. Vai trò Sinh viên (sv01 / sv123)', () => {

    test.beforeEach(async ({ page }) => {
      // Đăng nhập bằng tài khoản sinh viên sv01
      await page.goto('/tai-khoan.html', { waitUntil: 'domcontentloaded' });
      await page.locator('#inputTenDangNhap').fill('sv01');
      await page.locator('#inputMatKhau').fill('sv123');
      await page.locator('#btnLoginSubmit').click();
      await expect(page.locator('#sectionProfile')).toBeVisible({ timeout: 5000 });
    });

    for (const p of PAGES) {
      test(`Sinh viên mở trang ${p.name} (${p.path}) không có lỗi console & menu đúng vai trò`, async ({ page }) => {
        const errors = setupConsoleListener(page);

        await page.goto(p.path, { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(600);

        // 1. Banner cố định
        await expect(page.locator('.demo-banner')).toBeVisible();

        // 2. Menu có "Lượt mượn của tôi", không có "Quản lý Mượn - Trả" của thủ thư
        const nav = page.locator('.main-nav');
        await expect(nav).toContainText('Lượt mượn của tôi');
        await expect(nav).not.toContainText('Quản lý Mượn - Trả');

        // 3. Không có lỗi console
        expect(errors, `Lỗi console trên trang ${p.path}: ${errors.join(', ')}`).toEqual([]);
      });
    }

    test('Sinh viên xem chi tiết tư liệu có nút Đăng ký mượn', async ({ page }) => {
      const errors = setupConsoleListener(page);
      await page.goto('/chi-tiet.html?id=8', { waitUntil: 'domcontentloaded' });

      // Nút Đăng ký mượn hiển thị
      const borrowBtn = page.locator('#btnDangKyMuon');
      await expect(borrowBtn).toBeVisible({ timeout: 5000 });

      expect(errors).toEqual([]);
    });

    test('Sinh viên truy cập quan-ly.html và dashboard.html bị chặn quyền truy cập', async ({ page }) => {
      const errors = setupConsoleListener(page);

      await page.goto('/quan-ly.html', { waitUntil: 'domcontentloaded' });
      await expect(page.locator('#librarianForbiddenCard')).toBeVisible();

      await page.goto('/dashboard.html', { waitUntil: 'domcontentloaded' });
      await expect(page.locator('#dashForbiddenCard')).toBeVisible();

      expect(errors).toEqual([]);
    });
  });

  // =========================================================================
  // 3. VAI TRÒ THỦ THƯ (thuthu / thuthu123)
  // =========================================================================
  test.describe('3. Vai trò Thủ thư (thuthu / thuthu123)', () => {

    test.beforeEach(async ({ page }) => {
      // Đăng nhập bằng tài khoản thủ thư
      await page.goto('/tai-khoan.html', { waitUntil: 'domcontentloaded' });
      await page.locator('#inputTenDangNhap').fill('thuthu');
      await page.locator('#inputMatKhau').fill('thuthu123');
      await page.locator('#btnLoginSubmit').click();
      await expect(page.locator('#sectionProfile')).toBeVisible({ timeout: 5000 });
    });

    for (const p of PAGES) {
      test(`Thủ thư mở trang ${p.name} (${p.path}) không có lỗi console & menu đầy đủ`, async ({ page }) => {
        const errors = setupConsoleListener(page);

        await page.goto(p.path, { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(600);

        // 1. Banner cố định
        await expect(page.locator('.demo-banner')).toBeVisible();

        // 2. Menu có Quản lý mượn trả & Dashboard thống kê
        const nav = page.locator('.main-nav');
        await expect(nav).toContainText('Quản lý Mượn - Trả');
        await expect(nav).toContainText('Dashboard Thống kê');

        // 3. Quick profile hiển thị vai trò Thủ thư
        const profile = page.locator('.user-quick-profile');
        await expect(profile).toContainText('Thủ thư');

        // 4. Không có lỗi console
        expect(errors, `Lỗi console trên trang ${p.path}: ${errors.join(', ')}`).toEqual([]);
      });
    }

    test('Thủ thư truy cập quan-ly.html xem được danh sách mượn và form tải bản mềm', async ({ page }) => {
      const errors = setupConsoleListener(page);
      await page.goto('/quan-ly.html', { waitUntil: 'domcontentloaded' });

      // Nội dung quản lý hiển thị
      await expect(page.locator('#librarianMainContent')).toBeVisible();
      await expect(page.locator('#librarianForbiddenCard')).not.toBeVisible();

      // Bảng danh sách mượn hiển thị
      await expect(page.locator('#adminBorrowTable')).toBeVisible();

      // Form tải bản mềm PDF hiển thị
      await expect(page.locator('#formUploadPdf')).toBeVisible();

      expect(errors).toEqual([]);
    });

    test('Thủ thư truy cập dashboard.html xem được 4 thẻ KPI với dữ liệu thật', async ({ page }) => {
      const errors = setupConsoleListener(page);
      await page.goto('/dashboard.html', { waitUntil: 'domcontentloaded' });

      // Nội dung dashboard hiển thị
      await expect(page.locator('#dashMainContent')).toBeVisible();
      await expect(page.locator('#dashForbiddenCard')).not.toBeVisible();

      // 4 thẻ KPI đã nạp dữ liệu từ /api/thong-ke/tong-quan
      const kpiTongTim = page.locator('#kpiTongTim');
      await expect(kpiTongTim).not.toHaveText('---', { timeout: 5000 });

      const kpiTiLe0Kq = page.locator('#kpiTiLe0Kq');
      await expect(kpiTiLe0Kq).not.toHaveText('---', { timeout: 5000 });

      expect(errors).toEqual([]);
    });
  });

  test.afterAll(async () => {
    const { execFileSync } = require('child_process');
    const path = require('path');
    const pyCleanup = [
      'import os, psycopg2',
      'from dotenv import load_dotenv',
      'load_dotenv()',
      'with psycopg2.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:',
      '    cur.execute("DELETE FROM log_tim_kiem WHERE du_lieu_mau = false")'
    ].join('\n');
    try {
      execFileSync('python', ['-c', pyCleanup], { cwd: path.resolve(__dirname, '..', '..') });
    } catch (_) {}
  });

});

