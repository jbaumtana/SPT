// Tests for overlay-engine.js (docs/overlay-fix-plan.md, Phase 1), in headless Chromium.
// Run: NODE_PATH=$(npm root -g) node tools/overlay/test_engine.js
// Uses Playwright; set CHROMIUM_PATH to override the browser binary.
'use strict';
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ENGINE = fs.readFileSync(path.join(__dirname, 'overlay-engine.js'), 'utf8');
const tick = (page) => page.evaluate(() => new Promise((r) => setTimeout(r, 30)));

async function setup(browser, html) {
  const page = await browser.newPage();
  await page.setContent(`<html><body>${html}</body></html>`);
  await page.addScriptTag({ content: ENGINE });
  return page;
}

const tests = {
  async 'E1: in-place text change is re-replaced'(browser) {
    const page = await setup(browser, '<h1 id="t">Healthcare Tech Industry</h1><p id="c" class="cap">old caption</p>');
    await page.evaluate(() => __demoTailor.apply({
      textRules: [{ find: 'Healthcare Tech Industry', replace: 'Health Insurance Policy' }],
      selectorRules: [{ selector: '.cap', action: 'text', value: 'NEW CAPTION' }],
    }));
    // React-style in-place rewrite of an existing text node
    await page.evaluate(() => { document.getElementById('t').firstChild.nodeValue = 'Healthcare Tech Industry'; });
    await page.evaluate(() => { document.getElementById('c').firstChild.nodeValue = 'old caption'; });
    await tick(page);
    const t = await page.textContent('#t');
    const c = await page.textContent('#c');
    if (t !== 'Health Insurance Policy') throw new Error(`title came back as "${t}"`);
    if (c !== 'NEW CAPTION') throw new Error(`caption came back as "${c}"`);
  },

  async 'E2: wholeWord works next to punctuation and node edges'(browser) {
    const page = await setup(browser, [
      '<p id="a">Compliance Approval [MF]-Step 1</p>',
      '<p id="b">Thanks @handle, see you</p>',
      '<p id="c">Follow #tag.</p>',
      '<p id="d">Tech</p>',
      '<p id="e">Technology stays</p>',
    ].join(''));
    await page.evaluate(() => __demoTailor.apply({ textRules: [
      { find: 'Compliance Approval [MF]', replace: 'Legal Review' },
      { find: '@handle', replace: '@bcbs' },
      { find: '#tag', replace: '#blue' },
      { find: 'Tech', replace: 'Policy' },
    ] }));
    const got = await page.evaluate(() => ['a', 'b', 'c', 'd', 'e'].map((id) => document.getElementById(id).textContent));
    const want = ['Legal Review-Step 1', 'Thanks @bcbs, see you', 'Follow #blue.', 'Policy', 'Technology stays'];
    got.forEach((g, i) => { if (g !== want[i]) throw new Error(`#${'abcde'[i]}: "${g}" != "${want[i]}"`); });
  },

  async 'E3: keyed captions survive a redraw in a different order'(browser) {
    const page = await setup(browser, '<ul id="l"></ul>');
    await page.evaluate(() => {
      const l = document.getElementById('l');
      ['p1', 'p2', 'p3', 'p2'].forEach((id) => {
        l.insertAdjacentHTML('beforeend', `<li data-qa-msg="${id}"><span class="cap">seed ${id}</span></li>`);
      });
      __demoTailor.apply({ selectorRules: [{ selector: '.cap', action: 'text', keyAttr: 'data-qa-msg', value: ['A', 'B', 'C', 'D', 'E'] }] });
    });
    const read = () => page.evaluate(() => [...document.querySelectorAll('[data-qa-msg]')].map((li) => [li.dataset.qaMsg, li.textContent]));
    const before = Object.fromEntries(await read());
    const dup = (await read()).filter(([k]) => k === 'p2').map(([, v]) => v);
    if (dup[0] !== dup[1]) throw new Error(`duplicate post got different captions: ${dup}`);
    await page.evaluate(() => {
      const l = document.getElementById('l');
      l.innerHTML = '';
      ['p3', 'p1', 'p2'].forEach((id) => l.insertAdjacentHTML('beforeend', `<li data-qa-msg="${id}"><span class="cap">seed ${id}</span></li>`));
    });
    await tick(page);
    for (const [k, v] of await read()) {
      if (before[k] !== v) throw new Error(`${k} changed from "${before[k]}" to "${v}" after redraw`);
    }
  },

  async 'E4: scoped rule wins over a general rule, element claimed once'(browser) {
    const page = await setup(browser,
      '<div data-qa-date="10/14/2026"><span class="cap">a</span></div>' +
      '<div data-qa-date="10/15/2026"><span class="cap" id="pin">b</span></div>');
    await page.evaluate(() => __demoTailor.apply({ selectorRules: [
      { selector: '.cap', action: 'text', value: ['GENERAL'] },
      { selector: '.cap', action: 'text', scope: "[data-qa-date='10/15/2026']", value: 'PINNED' },
    ] }));
    const got = await page.evaluate(() => [...document.querySelectorAll('.cap')].map((e) => e.textContent));
    if (got[0] !== 'GENERAL' || got[1] !== 'PINNED') throw new Error(`got ${JSON.stringify(got)}`);
  },

  async 'E5: apply twice then revert once restores the page exactly'(browser) {
    const page = await setup(browser, '<p class="cap">Secure Patient Technology</p><img src="a.png">');
    const original = await page.evaluate(() => document.documentElement.outerHTML);
    const payload = {
      textRules: [{ find: 'Secure Patient Technology', replace: 'BCBSA' }],
      selectorRules: [{ selector: 'img', action: 'attr', attr: 'src', value: 'b.png' }],
      cssVars: { '--brand-primary': '#005EB8' },
      injectCss: 'body{color:red}',
    };
    await page.evaluate((p) => { __demoTailor.apply(p); __demoTailor.apply(p); __demoTailor.revert(); }, payload);
    const after = await page.evaluate(() => document.documentElement.outerHTML);
    if (after !== original) throw new Error('page differs after apply, apply, revert');
  },

  async 'E6: audit reports visible leftovers with selectors'(browser) {
    const page = await setup(browser,
      '<p id="v">Partnering with NPAF at #ViVE2025 bit.ly/x</p>' +
      '<p style="display:none">NPAF hidden</p><p>clean text</p>');
    const res = await page.evaluate(() => __demoTailor.audit({ deny: ['NPAF'], patterns: ['#\\w+', 'bit\\.ly'] }));
    const matches = res.map((r) => r.match).sort();
    if (JSON.stringify(matches) !== JSON.stringify(['#ViVE2025', 'NPAF', 'bit.ly'].sort())) throw new Error(`got ${JSON.stringify(res)}`);
    if (!res.every((r) => r.selector === '#v')) throw new Error('missing or wrong selector');
  },

  async 'E7: revert disconnects observers; later changes are not re-applied'(browser) {
    const page = await setup(browser, '<h1 id="t">Secure Patient Technology</h1>');
    await page.evaluate(() => {
      __demoTailor.apply({ textRules: [{ find: 'Secure Patient Technology', replace: 'BCBSA' }] });
      __demoTailor.revert();
      document.getElementById('t').firstChild.nodeValue = 'Secure Patient Technology';
      document.body.insertAdjacentHTML('beforeend', '<p id="n">Secure Patient Technology</p>');
    });
    await tick(page);
    const s = await page.evaluate(() => [document.getElementById('t').textContent, document.getElementById('n').textContent, __demoTailor.status().observing]);
    if (s[0] !== 'Secure Patient Technology' || s[1] !== 'Secure Patient Technology' || s[2]) throw new Error(`got ${JSON.stringify(s)}`);
  },
};

(async () => {
  const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
  let failed = 0;
  for (const [name, fn] of Object.entries(tests)) {
    try { await fn(browser); console.log(`PASS  ${name}`); }
    catch (e) { failed++; console.log(`FAIL  ${name}\n      ${e.message.split('\n')[0]}`); }
  }
  await browser.close();
  console.log(failed ? `\n${failed} failed` : '\nall passed');
  process.exit(failed ? 1 : 0);
})();
