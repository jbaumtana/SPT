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

  async 'E4b: perScope limits a scoped rule to N elements per scope; the rest fall through'(browser) {
    const page = await setup(browser,
      '<div data-qa-date="10/21/2026"><span class="cap">a</span><span class="cap">b</span></div>' +
      '<div data-qa-date="10/22/2026"><span class="cap">c</span></div>');
    await page.evaluate(() => __demoTailor.apply({ selectorRules: [
      { selector: '.cap', action: 'text', value: ['G1', 'G2', 'G3'] },
      { selector: '.cap', action: 'text', scope: "[data-qa-date='10/21/2026']", perScope: 1, value: 'PINNED' },
    ] }));
    const got = await page.evaluate(() => [...document.querySelectorAll('.cap')].map((e) => e.textContent));
    if (got[0] !== 'PINNED' || got[1] === 'PINNED' || got[2] === 'PINNED') throw new Error(`got ${JSON.stringify(got)}`);
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

  async 'V1: image action swaps img src, clears srcset and picture sources, and reverts exactly'(browser) {
    const page = await setup(browser,
      '<img id="a" src="seed.png" srcset="seed2.png 2x" sizes="100vw">' +
      '<picture><source srcset="seed.webp"><img id="b" src="seed.png"></picture>' +
      '<div id="c" style="background:url(seed.png)"></div>');
    // The browser re-serialises attribute order and the background shorthand, so compare values, not markup.
    const snap = () => page.evaluate(() => ({
      a: ['src', 'srcset', 'sizes'].map((x) => document.getElementById('a').getAttribute(x)),
      b: [document.getElementById('b').getAttribute('src'), document.querySelector('source').getAttribute('srcset')],
      c: getComputedStyle(document.getElementById('c')).backgroundImage,
    }));
    const original = await snap();
    await page.evaluate(() => __demoTailor.apply({ selectorRules: [{ selector: 'img, #c', action: 'image', value: 'data:image/png;base64,AA' }] }));
    const got = await page.evaluate(() => ({
      a: [document.getElementById('a').getAttribute('src'), document.getElementById('a').hasAttribute('srcset'), document.getElementById('a').hasAttribute('sizes')],
      b: [document.getElementById('b').getAttribute('src'), document.querySelector('source').hasAttribute('srcset')],
      c: document.getElementById('c').style.backgroundImage,
    }));
    if (got.a[0] !== 'data:image/png;base64,AA' || got.a[1] || got.a[2]) throw new Error(`img: ${JSON.stringify(got.a)}`);
    if (got.b[0] !== 'data:image/png;base64,AA' || got.b[1]) throw new Error(`picture: ${JSON.stringify(got.b)}`);
    if (!got.c.includes('data:image/png;base64,AA')) throw new Error(`background: ${got.c}`);
    await page.evaluate(() => __demoTailor.revert());
    const after = await snap();
    if (JSON.stringify(after) !== JSON.stringify(original)) throw new Error(`after revert ${JSON.stringify(after)} != ${JSON.stringify(original)}`);
  },

  async 'V2: an image the app resets in place is swapped back'(browser) {
    const page = await setup(browser, '<img id="a" src="seed.png">');
    await page.evaluate(() => __demoTailor.apply({ selectorRules: [{ selector: '#a', action: 'image', value: 'data:image/png;base64,AA' }] }));
    await page.evaluate(() => {
      const i = document.getElementById('a');
      i.setAttribute('src', 'seed.png');
      i.setAttribute('srcset', 'seed2.png 2x');
    });
    await tick(page);
    const s = await page.evaluate(() => [document.getElementById('a').getAttribute('src'), document.getElementById('a').hasAttribute('srcset')]);
    if (s[0] !== 'data:image/png;base64,AA' || s[1]) throw new Error(`got ${JSON.stringify(s)}`);
  },

  async 'V3: replaceWith hides a canvas and svg and shows our markup; revert restores the page'(browser) {
    const page = await setup(browser,
      '<section><div id="c1" class="chart"><canvas width="300" height="120"></canvas></div></section>' +
      '<section><div id="c2" class="chart"><svg width="300" height="120"><rect width="40" height="90"/></svg></div></section>');
    const original = await page.evaluate(() => document.documentElement.outerHTML);
    await page.evaluate(() => __demoTailor.apply({ selectorRules: [
      { selector: '#c1', action: 'replaceWith', id: 'one', value: '<svg viewBox="0 0 10 10"><title>Sample one</title></svg>' },
      { selector: '#c2', action: 'replaceWith', id: 'two', value: '<svg viewBox="0 0 10 10"><title>Sample two</title></svg>' },
    ] }));
    const s = await page.evaluate(() => ({
      hidden: ['c1', 'c2'].map((id) => getComputedStyle(document.getElementById(id)).display),
      reps: [...document.querySelectorAll('[data-demo-tailor-replacement]')].map((r) => r.getAttribute('data-demo-tailor-replacement') + ':' + r.querySelector('title').textContent),
    }));
    if (s.hidden.some((d) => d !== 'none')) throw new Error(`originals not hidden: ${s.hidden}`);
    if (JSON.stringify(s.reps) !== JSON.stringify(['one:Sample one', 'two:Sample two'])) throw new Error(`reps ${JSON.stringify(s.reps)}`);
    await page.evaluate(() => __demoTailor.revert());
    const after = await page.evaluate(() => document.documentElement.outerHTML);
    if (after !== original) throw new Error('page differs after revert');
  },

  async 'V4: replacement survives the app dropping it and un-hiding the original; a re-rendered chart is replaced once'(browser) {
    const page = await setup(browser, '<div id="host"><div class="chart" id="orig"><svg width="200" height="80"></svg></div></div>');
    await page.evaluate(() => __demoTailor.apply({ selectorRules: [{ selector: '.chart', action: 'replaceWith', id: 'k', value: '<b>SAMPLE</b>' }] }));
    await page.evaluate(() => {
      document.querySelector('[data-demo-tailor-replacement]').remove();
      document.getElementById('orig').style.display = '';
    });
    await tick(page);
    let s = await page.evaluate(() => [document.querySelectorAll('[data-demo-tailor-replacement]').length, getComputedStyle(document.getElementById('orig')).display]);
    if (s[0] !== 1 || s[1] !== 'none') throw new Error(`after drop: ${JSON.stringify(s)}`);
    await page.evaluate(() => { document.getElementById('host').innerHTML = '<div class="chart" id="fresh"><svg width="200" height="80"></svg></div>'; });
    await tick(page);
    s = await page.evaluate(() => [document.querySelectorAll('[data-demo-tailor-replacement]').length, getComputedStyle(document.getElementById('fresh')).display]);
    if (s[0] !== 1 || s[1] !== 'none') throw new Error(`after re-render: ${JSON.stringify(s)}`);
  },

  async 'V5: replacement text is not rewritten by text rules'(browser) {
    const page = await setup(browser, '<div class="chart"><svg width="200" height="80"></svg></div>');
    await page.evaluate(() => __demoTailor.apply({
      textRules: [{ find: 'Sample', replace: 'CHANGED' }],
      selectorRules: [{ selector: '.chart', action: 'replaceWith', value: '<p id="r">Sample</p>' }],
    }));
    const t = await page.textContent('#r');
    if (t !== 'Sample') throw new Error(`got "${t}"`);
  },

  async 'V6: scan inventories canvas, svg charts (not icons) and background images'(browser) {
    const page = await setup(browser,
      '<canvas id="cv" width="300" height="120"></canvas>' +
      '<svg id="ch" width="300" height="120"><rect width="40" height="90"/><text x="0" y="10">Impressions</text></svg>' +
      '<svg id="ic" width="16" height="16"><path d="M0 0"/></svg>' +
      '<div id="bg" style="width:50px;height:50px;background-image:url(seed.png)"></div>');
    const v = (await page.evaluate(() => __demoTailor.scan())).visuals;
    if (v.canvas.length !== 1 || v.canvas[0].selector !== '#cv') throw new Error(`canvas ${JSON.stringify(v.canvas)}`);
    if (v.svg.length !== 1 || v.svg[0].selector !== '#ch' || v.svg[0].texts[0] !== 'Impressions') throw new Error(`svg ${JSON.stringify(v.svg)}`);
    if (v.backgroundImages.length !== 1 || v.backgroundImages[0].selector !== '#bg') throw new Error(`bg ${JSON.stringify(v.backgroundImages)}`);
  },

  async 'V7: audit flags denied image sources and charts still showing; clean after replace'(browser) {
    const page = await setup(browser,
      '<img id="i" src="https://cdn.example/spt-security.png">' +
      '<div id="bg" style="width:20px;height:20px;background-image:url(https://cdn.example/spt-hero.png)"></div>' +
      '<div class="chart" id="c"><canvas width="200" height="80"></canvas></div>');
    const opts = { denyImages: ['spt-security', 'spt-hero'], charts: ['.chart'] };
    const before = await page.evaluate((o) => __demoTailor.audit(o), opts);
    const kinds = before.map((r) => r.kind + ':' + r.selector).sort();
    if (JSON.stringify(kinds) !== JSON.stringify(['chart:#c', 'image:#bg', 'image:#i'].sort())) throw new Error(`before ${JSON.stringify(kinds)}`);
    await page.evaluate(() => __demoTailor.apply({ selectorRules: [
      { selector: '#i, #bg', action: 'image', value: 'data:image/png;base64,AA' },
      { selector: '.chart', action: 'replaceWith', value: '<i>x</i>' },
    ] }));
    const after = await page.evaluate((o) => __demoTailor.audit(o), opts);
    if (after.length) throw new Error(`after ${JSON.stringify(after)}`);
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
