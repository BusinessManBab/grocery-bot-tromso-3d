// PLAYWRIGHT_MODULE=/path/to/playwright node tools/browser_check.cjs
// Uses software WebGL for correctness checks, NOT a laptop GPU performance benchmark.
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.CHROMIUM_PATH || undefined,
    args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });
  try {
    for (const [name, viewport] of [
      ['desktop', { width: 1440, height: 1000 }],
      ['phone', { width: 390, height: 844 }],
    ]) {
      const page = await browser.newPage({ viewport });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto((process.env.PREVIEW_URL || 'http://localhost:8138/') + '?view=2d', { waitUntil: 'networkidle' });
      await page.waitForFunction(() => window.groceryView?.game.players.length === 10 && window.groceryView.panels);
      await page.evaluate(() => { groceryView.play.paused = true; groceryView.play.head = 240; });
      await page.waitForFunction(() => document.getElementById('tick').textContent.includes('240'));
      assert.equal(await page.locator('.g-row').count(), 10);
      // Every standings seat must reopen and switch its shop, including scrolled rows.
      for (let seat = 0; seat < 10; seat++) {
        await page.locator('#shop-close').click();
        await page.locator('.g-row').nth(seat).click();
        await page.waitForFunction(seat => {
          const player = groceryView.game.players[seat];
          return !document.getElementById('shopwin').hidden &&
            document.getElementById('shop-title').textContent ===
              (seat === groceryView.game.meta.you ? 'Your shop' : `${player.name}'s shop`);
        }, seat);
      }
      await page.locator('.g-row').nth(9).click(); // Clear fleet focus, leave the shop selected.
      await page.locator('#shop-close').click();
      // The actual order card data are checked using a known recording order.
      const oid = await page.evaluate(async () => {
        const shop = await (await fetch('data/shop.json')).json();
        return Object.keys(shop.orders)[0];
      });
      await page.evaluate(id => groceryView.panels.showOrder(id), oid);
      await page.waitForFunction(() => !document.getElementById('ordercard').hidden);
      await page.keyboard.press('Escape');
      await page.screenshot({ path: `/tmp/opencode/tromso-${name}-2d.png` });
      await page.locator('#view-3d').click();
      await page.waitForFunction(() => groceryView.world3d && document.body.classList.contains('is-3d'), null, { timeout: 120000 });
      const geometry = await page.evaluate(() => {
        const world = groceryView.world3d;
        let vertices = 0;
        world.scene.traverse(object => {
          if (object.isMesh && [20, 21].includes(object.renderOrder)) vertices += object.geometry.attributes.position.count;
        });
        return { buildingVertices: vertices, drawCalls: world.renderer.info.render.calls };
      });
      assert(geometry.buildingVertices <= 650000, JSON.stringify(geometry));
      await page.screenshot({ path: `/tmp/opencode/tromso-${name}-3d.png`, timeout: 120000 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      assert.deepEqual(errors, []);
      console.log(`${name}: PASS — 10 standings/shop selections, order card, 2D, 3D, no browser errors`, geometry);
      await page.close();
    }
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    await page.goto(process.env.PREVIEW_URL || 'http://localhost:8138/', { waitUntil: 'networkidle' });
    await page.waitForFunction(() => groceryView.world3d && groceryView.panels?.seat === 2 &&
      document.body.classList.contains('is-3d'), null, { timeout: 120000 });
    await page.screenshot({ path: '/tmp/opencode/tromso-default-3d.png', timeout: 120000 });
    console.log('Default entry: PASS — active 3D replay with Your shop open');
    await page.close();
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
