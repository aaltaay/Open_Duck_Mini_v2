// Headless load test for the viewer page. Run it before every publish; it must print 'STATE loaded' and 'ERRORS none'.
// Usage: node altaay_lab/viewer/test_viewer.js <page.html> <folder with duck.glb.txt and manifest.json> <local three@0.160.0 package folder> <out.png> [scene]
// scene: dock or docked loads the page at #dock or #docked (dock_manifest.json + dock.glb.txt, docked_manifest.json + docked.glb.txt).
// The three folder is the npm package (npm pack three@0.160.0, unpacked): it needs build/ and examples/jsm/. Playwright with Chromium must be installed.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const PAGE = process.argv[2], DATA = process.argv[3], THREE = process.argv[4], SHOT = process.argv[5], SCENE = process.argv[6] || '';
(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 });
  const errs = [];
  page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  await page.route('**/*', async (route) => {
    const u = new URL(route.request().url());
    if (u.hostname === 'viewer.local') {
      if (u.pathname === '/index.html') return route.fulfill({ contentType: 'text/html', body: '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + fs.readFileSync(PAGE, 'utf8') + '</body></html>' });
      const f = path.join(DATA, u.pathname.slice(1));
      if (fs.existsSync(f)) return route.fulfill({ body: fs.readFileSync(f), contentType: f.endsWith('.json') ? 'application/json' : 'text/plain' });
      { console.log('404', u.href); return route.fulfill({ status: 404, body: '' }); }
    }
    if (u.hostname === 'cdn.jsdelivr.net') {
      const rel = u.pathname.replace('/npm/three@0.160.0/', '');
      const f = path.join(THREE, rel);
      if (fs.existsSync(f)) return route.fulfill({ body: fs.readFileSync(f), contentType: 'application/javascript' });
      { console.log('404', u.href); return route.fulfill({ status: 404, body: '' }); }
    }
    return route.fulfill({ status: 204, body: '' });   // fonts: not needed for the test
  });
  await page.goto('http://viewer.local/index.html' + (SCENE ? '#' + SCENE : ''));
  const t0 = Date.now(); let state = 'timeout';
  while (Date.now() - t0 < 150000) {
    const r = await page.evaluate(() => ({ hidden: document.getElementById('loading').hidden, msg: document.getElementById('loadmsg').textContent }));
    if (r.hidden) { state = 'loaded'; break; }
    if (/could not load/.test(r.msg)) { state = 'failed: ' + r.msg; break; }
    await page.waitForTimeout(1000);
  }
  console.log('STATE', state, 'after', ((Date.now() - t0) / 1000).toFixed(0), 's');
  if (state === 'loaded') {
    await page.waitForTimeout(1500);
    const info = await page.evaluate(() => ({ chips: document.getElementById('chips').innerText, labels: document.querySelectorAll('.pl-label').length }));
    console.log('INFO', JSON.stringify(info));
    await page.click('#tg-xray', { force: true }).catch((e) => console.log('xray click', e.message));
    await page.waitForTimeout(1000);
  }
  await page.screenshot({ path: SHOT });
  console.log('ERRORS', errs.length ? errs.slice(0, 8).join(' | ') : 'none');
  await browser.close();
})().catch((e) => { console.log('TESTFAIL', e.message); process.exit(1); });
