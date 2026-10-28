/**
 * tools/screenshots.js - Chụp ảnh màn hình tự động bằng Playwright (Milestone M6)
 *
 * Chụp:
 * 1. 3 vai trò (khach, nguoi_dung [sv01], thu_thu [thuthu])
 * 2. Toàn bộ 6 trang (index, tra-cuu, chi-tiet, tai-khoan, quan-ly, dashboard)
 * 3. Hai độ phân giải: Desktop (1440x900) và Mobile (390x844)
 *    -> Lưu tại reports/screenshots/<vai_tro>/<trang>_1440.png và <trang>_390.png
 * 4. Ảnh riêng từng khối biểu đồ và bảng phân tích trên Dashboard thủ thư
 *    -> Lưu tại reports/screenshots/dashboard/
 *
 * Chạy: npm run screenshots   (hoặc node tools/screenshots.js)
 */

const { chromium } = require('@playwright/test');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const http = require('http');

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const ROOT_DIR = path.resolve(__dirname, '..');
const OUT_DIR = path.join(ROOT_DIR, 'reports', 'screenshots');

const PAGES = [
  { slug: 'index', url: '/index.html' },
  { slug: 'tra-cuu', url: '/tra-cuu.html' },
  { slug: 'chi-tiet', url: '/chi-tiet.html?id=8' },
  { slug: 'tai-khoan', url: '/tai-khoan.html' },
  { slug: 'quan-ly', url: '/quan-ly.html' },
  { slug: 'dashboard', url: '/dashboard.html' }
];

const ROLES = [
  { name: 'khach', user: null, pass: null },
  { name: 'nguoi_dung', user: 'sv01', pass: 'sv123' },
  { name: 'thu_thu', user: 'thuthu', pass: 'thuthu123' }
];

const VIEWPORTS = [
  { suffix: '1440', width: 1440, height: 900 },
  { suffix: '390', width: 390, height: 844 }
];

function checkServerReady(url) {
  return new Promise((resolve) => {
    const req = http.get(`${url}/api/gioi-thieu`, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(1500, () => {
      req.destroy();
      resolve(false);
    });
  });
}

async function ensureServer() {
  if (await checkServerReady(BASE_URL)) {
    return null;
  }
  console.log('Khởi động máy chủ Python Flask (python server/app.py)...');
  const proc = spawn('python', ['server/app.py'], {
    cwd: ROOT_DIR,
    stdio: 'ignore',
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
  });

  for (let i = 0; i < 40; i++) {
    await new Promise((r) => setTimeout(r, 500));
    if (await checkServerReady(BASE_URL)) {
      return proc;
    }
  }
  proc.kill();
  throw new Error('Không thể khởi động máy chủ tại ' + BASE_URL);
}

async function main() {
  const serverProc = await ensureServer();
  let browser = null;
  let totalFiles = 0;

  try {
    fs.mkdirSync(OUT_DIR, { recursive: true });
    browser = await chromium.launch();

    for (const role of ROLES) {
      const roleDir = path.join(OUT_DIR, role.name);
      fs.mkdirSync(roleDir, { recursive: true });

      const context = await browser.newContext({
        viewport: { width: 1440, height: 900 }
      });
      const page = await context.newPage();

      // Đăng nhập nếu vai trò có tài khoản
      if (role.user && role.pass) {
        await page.goto(`${BASE_URL}/tai-khoan.html`, { waitUntil: 'networkidle' });
        await page.locator('#inputTenDangNhap').fill(role.user);
        await page.locator('#inputMatKhau').fill(role.pass);
        await page.locator('#btnLoginSubmit').click();
        await page.locator('#sectionProfile').waitFor({ state: 'visible', timeout: 8000 });
      }

      for (const vp of VIEWPORTS) {
        await page.setViewportSize({ width: vp.width, height: vp.height });

        for (const p of PAGES) {
          await page.goto(`${BASE_URL}${p.url}`, { waitUntil: 'networkidle' });
          await page.waitForTimeout(p.slug === 'dashboard' ? 1200 : 500);

          const fileWithVp = path.join(roleDir, `${p.slug}_${vp.suffix}.png`);
          await page.screenshot({ path: fileWithVp, fullPage: true });
          totalFiles++;

          // Khi ở vai trò thu_thu + 1440px + trang dashboard: chụp riêng từng biểu đồ/bảng vào dashboard/
          if (role.name === 'thu_thu' && vp.suffix === '1440' && p.slug === 'dashboard') {
            const dashDir = path.join(OUT_DIR, 'dashboard');
            fs.mkdirSync(dashDir, { recursive: true });

            const chartTargets = [
              { name: 'kpi_tong_quan.png', locator: page.locator('.stats-grid').first() },
              { name: 'bieu_do_wordcloud.png', locator: page.locator('#wordcloudWrapper').locator('..') },
              { name: 'bieu_do_top_tu_khoa.png', locator: page.locator('#topKeywordsChart').locator('..').locator('..') },
              { name: 'bieu_do_theo_ngay.png', locator: page.locator('#timelineChart').locator('..').locator('..') },
              { name: 'bang_khong_ket_qua.png', locator: page.locator('#zeroResultsTable').locator('..').locator('..') },
              { name: 'bang_nen_so_hoa.png', locator: page.locator('#shouldDigitizeTable').locator('..').locator('..') }
            ];

            for (const ct of chartTargets) {
              const destDash = path.join(dashDir, ct.name);
              await ct.locator.screenshot({ path: destDash });
              totalFiles++;
            }
          }
        }
      }

      await context.close();
      console.log(`Đã chụp xong vai trò: ${role.name}`);
    }

    console.log(`Hoàn tất chụp ${totalFiles} tập tin ảnh tại: ${OUT_DIR}`);
  } finally {
    if (browser) {
      await browser.close();
    }
    if (serverProc) {
      serverProc.kill();
    }
  }
}

main().catch((err) => {
  console.error('Lỗi khi chụp màn hình:', err);
  process.exit(1);
});
