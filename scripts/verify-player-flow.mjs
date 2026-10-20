// UI fixture checks only. Run against Vite; the separate encounter scripts verify real gameplay.
import {chromium} from '@playwright/test'
import assert from 'node:assert/strict'
import {mkdir, writeFile} from 'node:fs/promises'
const out = process.env.OUT || 'test-results/player-flow'
await mkdir(out, {recursive: true})
const browser = await chromium.launch({executablePath: process.env.CHROMIUM || '/usr/bin/chromium', headless: true, args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']})
const context = await browser.newContext({viewport: {width: 1100, height: 700}}), page = await context.newPage()
const errors = [], failed = [], checks = [], origin = process.env.ONSITE_URL || 'http://127.0.0.1:5173'
page.on('pageerror', e => errors.push(e.message)); page.on('requestfailed', r => failed.push(r.url()))
page.on('response', r => {if (r.status() >= 400) failed.push(`${r.status()} ${r.url()}`)})
const ready = () => page.waitForFunction(() => window.__frontendFixture?.ready)
const setRange = async (id, value) => page.locator(id).evaluate((el, val) => {el.value = String(val); el.dispatchEvent(new Event('input', {bubbles: true}))}, value)
try {
  await page.goto(`${origin}/tests/frontend-harness.html`); await ready()
  assert.equal(await page.locator('#mission-title').textContent(), 'Heron Reach.'); assert.equal(await page.locator('#mission-bots').textContent(), '06'); assert.equal(await page.locator('#mission-levels').textContent(), '05')
  assert.equal(await page.locator('[data-map="heron-reach"]').getAttribute('aria-current'), 'page'); checks.push('Reach menu accurately describes six bots and five levels')
  await page.locator('#tab-play').focus(); await page.keyboard.press('ArrowRight'); assert.equal(await page.locator('#tab-kit').getAttribute('aria-selected'), 'true')
  await page.locator('input[name="hood"][value="down"]').check(); await page.locator('input[name="trainers"][value="high"]').check()
  await page.waitForFunction(() => document.querySelector('#kit-preview-status')?.textContent === '', null, {timeout: 90000})
  assert.equal(await page.locator('#operator-preview canvas').count(), 1); checks.push('Keyboard tabs and actual 3D kit preview; hood and trainers selected')
  await page.screenshot({path: `${out}/kit-fixture.png`})
  await page.click('#tab-settings'); await setRange('#menu-sensitivity', 1.6); await setRange('#menu-volume', .35)
  await page.uncheck('#menu-sound'); await page.check('#menu-reduced-motion')
  await page.locator('#menu-quality').focus(); await page.keyboard.press('ArrowDown'); assert.equal(await page.inputValue('#menu-quality'), 'balanced'); checks.push('Native select arrows work with the actual gameplay Input listener installed')
  await page.reload(); await ready(); await page.click('#tab-settings')
  assert.equal(await page.inputValue('#menu-sensitivity'), '1.6'); assert.equal(await page.inputValue('#menu-volume'), '0.35'); assert.equal(await page.isChecked('#menu-sound'), false); assert.equal(await page.isChecked('#menu-reduced-motion'), true); assert.equal(await page.inputValue('#menu-quality'), 'balanced')
  assert.deepEqual((await page.evaluate(() => __frontendFixture.inspect())).kit, {hood: 'down', trainers: 'high'}); checks.push('Settings and kit survive reload')
  await page.locator('#start').focus(); await page.keyboard.press('Space'); assert.equal(await page.isVisible('#menu'), false); checks.push('Native Space activates Enter the Estate with gameplay Input installed')
  await page.evaluate(() => __frontendFixture.pause()); await page.waitForFunction(() => document.activeElement?.id === 'resume')
  await page.keyboard.press('Tab'); assert.equal(await page.evaluate(() => document.activeElement?.id), 'restart-pause'); await page.keyboard.press('Shift+Tab'); assert.equal(await page.evaluate(() => document.activeElement?.id), 'resume')
  await page.keyboard.press('Shift+Tab'); assert.equal(await page.evaluate(() => document.activeElement?.id), 'leave-pause'); await page.keyboard.press('Tab'); assert.equal(await page.evaluate(() => document.activeElement?.id), 'resume')
  assert.equal(await page.inputValue('#sensitivity'), '1.6'); await setRange('#sensitivity', .8); await page.click('#leave-pause'); assert.equal(await page.isVisible('#menu'), true); assert.equal(await page.isVisible('#hud'), false)
  assert.equal((await page.evaluate(() => __frontendFixture.inspect())).titleReturns, 1); checks.push('Native intermediate Tab, pause focus wrap, synchronised controls and return to title')
  await page.click('#start'); await page.evaluate(() => __frontendFixture.result({outcome: 'won', seconds: 83.2, shots: 50, hits: 30, kills: 6}))
  assert.equal(await page.locator('#result-time').textContent(), '01:23'); assert.equal(await page.locator('#result-accuracy').textContent(), '60%')
  await page.evaluate(() => __frontendFixture.result({outcome: 'won', seconds: 83.2, shots: 50, hits: 30, kills: 6}))
  let records = await page.evaluate(() => JSON.parse(localStorage.getItem('onsite.player.v1')).records); assert.equal(records['heron-reach'].played, 1)
  await page.click('#restart'); assert.equal(await page.isVisible('#result'), false); await page.evaluate(() => __frontendFixture.result({outcome: 'lost', seconds: 17, shots: 12, hits: 3, kills: 1})); await page.click('#leave-result')
  await page.reload(); await ready(); records = await page.evaluate(() => JSON.parse(localStorage.getItem('onsite.player.v1')).records)
  assert.equal(records['heron-reach'].played, 2); assert.equal(records['heron-reach'].secured, 1); assert.equal(records['heron-reach'].best.seconds, 83.2); assert.equal(records['heron-court'].played, 0); checks.push('Results record once, retry resets UI, loss preserves best, separate map records')
  await page.goto(`${origin}/tests/frontend-harness.html?map=heron-court`); await ready(); assert.equal(await page.locator('#mission-bots').textContent(), '03'); assert.equal(await page.locator('#mission-levels').textContent(), '02'); assert.equal(await page.locator('#mission-time').textContent(), '03:00'); checks.push('Court menu accurately describes three bots, two levels and three minutes')
  await page.screenshot({path: `${out}/title-fixture.png`})
  await page.setViewportSize({width: 390, height: 844}); await page.click('#tab-settings')
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)); await page.click('#start'); await page.evaluate(() => __frontendFixture.pause()); await page.click('#leave-pause'); await page.screenshot({path: `${out}/narrow-fixture.png`}); checks.push('390 px menu/settings remain reachable without horizontal overflow')
  assert.deepEqual(errors, []); assert.deepEqual(failed, [])
  await writeFile(`${out}/report.json`, JSON.stringify({context: 'Isolated frontend fixture; synthetic results, not gameplay evidence', renderer: 'Chromium / ANGLE SwiftShader', checks, errors, failed}, null, 2)); console.log(checks.join('\n'))
} catch (error) {await page.screenshot({path: `${out}/failure.png`}); await writeFile(`${out}/failure.json`, JSON.stringify({checks, errors, failed, error: String(error)}, null, 2)); throw error}
finally {await context.close(); await browser.close()}
