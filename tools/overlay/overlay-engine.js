/* demo-tailor overlay engine v1.2.0-spt
 * Copied from the demo-tailor plugin (v1.0.0) and fixed per
 * docs/overlay-fix-plan.md, Phase 1: in-place text changes (E1), wholeWord
 * next to punctuation (E2), keyed values (E3), scoped rules claimed once (E4),
 * idempotent apply (E5), audit() (E6), revert() stops all observers (E7),
 * perScope on scoped rules (one pinned caption per day).
 * v1.2.0: visuals. `image` action (img src+srcset+picture, svg <image>, CSS
 * background), `replaceWith` action (hide a chart/canvas/svg and inject
 * replacement markup in its place), attribute watching so the app can't undo
 * either, scan() inventories canvas/svg/background images, audit() checks
 * image sources and charts left showing.
 * Tests: tools/overlay/test_engine.js
 *
 * Injects prospect-specific branding and content over a running demo app,
 * without touching the app's backend. Idempotent, revertible, survives SPA
 * re-renders via MutationObserver.
 *
 * Usage from Claude in Chrome (javascript_tool):
 *   1. Paste this whole file to define window.__demoTailor
 *   2. __demoTailor.scan()            -> inventory of replaceable strings
 *   3. __demoTailor.apply(payload)    -> apply the overlay
 *   4. __demoTailor.revert()          -> restore the original demo
 */
(function () {
  'use strict';

  var VERSION = '1.2.0-spt';
  /* Revert any engine already on the page, whatever its version, so two
     observers never run at once. */
  if (window.__demoTailor && typeof window.__demoTailor.revert === 'function') {
    try { window.__demoTailor.revert(); } catch (e) {}
  }

  var DEFAULT_AVOID = ['script', 'style', 'noscript', 'code', 'pre', 'textarea', 'input', 'select'];
  var undoLog = [];
  var claims = new WeakMap();     /* element -> {claimKey: true}: the first matching selector rule wins (E4) */
  var appliedText = new WeakMap();/* element -> {action, value} set by a text/html rule, re-applied if the app rewrites it (E1) */
  var ruleCursor = [];            /* per-rule counter so unkeyed value arrays keep cycling as nodes stream in */
  var scopeCounts = [];           /* per-rule WeakMap: scope element -> elements claimed in it (perScope) */
  var appliedImage = new WeakMap();/* element -> value set by an image rule, re-applied if the app resets it */
  var hiddenEls = new WeakSet();  /* elements hidden by a hide/replaceWith rule, re-hidden if the app resets display */
  var replacements = [];          /* {orig, rep, value}: injected replacement markup next to a hidden original */
  var observer = null;
  var current = null;
  var applying = false;

  function isEditable(node) {
    var el = node.nodeType === 1 ? node : node.parentElement;
    while (el) {
      if (el.isContentEditable) return true;
      el = el.parentElement;
    }
    return false;
  }

  function skip(node, avoid) {
    var el = node.nodeType === 1 ? node : node.parentElement;
    if (!el) return true;
    if (el.closest('[data-demo-tailor-skip]')) return true;
    for (var i = 0; i < avoid.length; i++) {
      try { if (el.closest(avoid[i])) return true; } catch (e) {}
    }
    return isEditable(node);
  }

  function record(target, prop, original) {
    undoLog.push({ target: target, prop: prop, original: original });
  }

  function escapeRe(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  /* Preserve the casing shape of the matched text: ACME -> NORTHWIND,
     Acme -> Northwind, acme -> northwind. */
  function matchCase(matched, replacement) {
    if (matched === matched.toUpperCase() && matched !== matched.toLowerCase()) {
      return replacement.toUpperCase();
    }
    if (matched === matched.toLowerCase()) return replacement.toLowerCase();
    if (matched[0] === matched[0].toUpperCase()) {
      return replacement.charAt(0).toUpperCase() + replacement.slice(1);
    }
    return replacement;
  }

  function buildRegex(rule) {
    if (rule.mode === 'regex') return new RegExp(rule.find, rule.flags || 'g');
    var body = escapeRe(rule.find);
    /* Lookarounds instead of \b, so a find string that starts or ends with
       punctuation ("[MF]", "@handle", "#tag") still matches (E2). */
    if (rule.wholeWord !== false) body = '(?<![\\p{L}\\p{N}_])' + body + '(?![\\p{L}\\p{N}_])';
    return new RegExp(body, rule.caseSensitive ? 'gu' : 'giu');
  }

  function applyTextRules(root, rules, avoid) {
    if (!rules.length) return 0;
    var compiled = rules.map(function (r) {
      return { re: buildRegex(r), replace: r.replace, caseAware: r.caseAware !== false };
    });
    var hits = 0;
    var node;
    var batch = [];
    if (root.nodeType === 3) {
      batch.push(root);
    } else {
      var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
      while ((node = walker.nextNode())) batch.push(node);
    }

    batch.forEach(function (textNode) {
      var value = textNode.nodeValue;
      if (!value || !value.trim()) return;
      if (skip(textNode, avoid)) return;
      var next = value;
      compiled.forEach(function (c) {
        next = next.replace(c.re, function (m) {
          return c.caseAware ? matchCase(m, c.replace) : c.replace;
        });
      });
      if (next !== value) {
        record(textNode, 'nodeValue', value);
        textNode.nodeValue = next;
        hits++;
      }
    });
    return hits;
  }

  var TEXT_ATTRS = ['placeholder', 'alt', 'title', 'aria-label'];

  function applyAttrRules(root, rules, avoid) {
    if (!rules.length) return 0;
    var compiled = rules.map(function (r) {
      return { re: buildRegex(r), replace: r.replace, caseAware: r.caseAware !== false };
    });
    var hits = 0;
    var els = root.querySelectorAll('*');
    Array.prototype.forEach.call(els, function (el) {
      if (skip(el, avoid.filter(function (a) { return a !== 'input' && a !== 'textarea'; }))) return;
      TEXT_ATTRS.forEach(function (attr) {
        var v = el.getAttribute && el.getAttribute(attr);
        if (!v) return;
        var next = v;
        compiled.forEach(function (c) {
          next = next.replace(c.re, function (m) {
            return c.caseAware ? matchCase(m, c.replace) : c.replace;
          });
        });
        if (next !== v) {
          record({ el: el, attr: attr }, 'attribute', v);
          el.setAttribute(attr, next);
          hits++;
        }
      });
    });
    return hits;
  }

  /* An element is changed by at most one selector rule per action/target. */
  function claim(el, key) {
    var set = claims.get(el);
    if (!set) { set = {}; claims.set(el, set); }
    if (set[key]) return false;
    set[key] = true;
    return true;
  }

  /* FNV-1a: the same key always picks the same value, across redraws and reloads (E3). */
  function hashKey(s) {
    var h = 2166136261;
    for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }

  function pickValue(rule, ri, el, values) {
    if (rule.keyAttr) {
      var holder = el.closest(rule.keyClosest || ('[' + rule.keyAttr + ']'));
      var key = holder && holder.getAttribute(rule.keyAttr);
      if (key) return values[hashKey(key) % values.length];
    }
    var v = values[ruleCursor[ri] % values.length];
    ruleCursor[ri]++;
    return v;
  }

  /* Snapshot an element's children so text/html edits can be reverted exactly,
     even after later text rules replace the nodes we created. */
  function recordChildren(el) {
    var frag = document.createDocumentFragment();
    Array.prototype.slice.call(el.childNodes).forEach(function (n) {
      frag.appendChild(n.cloneNode(true));
    });
    record(el, 'children', frag);
  }

  function setAttrRecorded(el, attr, value) {
    record({ el: el, attr: attr }, 'attribute', el.getAttribute(attr));
    if (value === null) el.removeAttribute(attr); else el.setAttribute(attr, value);
  }

  function cssUrl(value) {
    return 'url("' + String(value).replace(/"/g, '%22') + '")';
  }

  /* Swap an image wherever the app keeps it, so nothing from the original survives:
     <img> (and srcset/sizes, and <picture> sources), SVG <image>, or a CSS background. */
  function applyImage(el, value) {
    var tag = el.tagName.toLowerCase();
    if (tag === 'img') {
      setAttrRecorded(el, 'src', value);
      ['srcset', 'sizes'].forEach(function (a) { if (el.hasAttribute(a)) setAttrRecorded(el, a, null); });
      var pic = el.parentElement;
      if (pic && pic.tagName === 'PICTURE') {
        Array.prototype.forEach.call(pic.querySelectorAll('source'), function (src) {
          if (src.hasAttribute('srcset')) setAttrRecorded(src, 'srcset', null);
        });
      }
    } else if (tag === 'image') {
      if (el.hasAttribute('xlink:href')) setAttrRecorded(el, 'xlink:href', null);
      setAttrRecorded(el, 'href', value);
    } else {
      record({ el: el, styleProp: 'background-image' }, 'style', el.style.getPropertyValue('background-image'));
      el.style.setProperty('background-image', cssUrl(value), 'important');
    }
    appliedImage.set(el, value);
  }

  function imageHolds(el, value) {
    var tag = el.tagName.toLowerCase();
    if (tag === 'img') return el.getAttribute('src') === value && !el.hasAttribute('srcset');
    if (tag === 'image') return el.getAttribute('href') === value;
    return (el.style.getPropertyValue('background-image') || '').indexOf(String(value).replace(/"/g, '%22')) !== -1;
  }

  function hideEl(el) {
    record({ el: el, styleProp: 'display' }, 'style', el.style.getPropertyValue('display'));
    el.style.setProperty('display', 'none', 'important');
    hiddenEls.add(el);
  }

  /* Hide a chart, canvas or image and put our own markup where it was. Works for canvas
     and SVG alike because the original is never edited, only hidden and left in place. */
  function applyReplace(el, rule, value) {
    if (!el.parentNode) return;
    var height = el.getBoundingClientRect().height;
    var rep = document.createElement('div');
    rep.setAttribute('data-demo-tailor-skip', '');
    rep.setAttribute('data-demo-tailor-replacement', rule.id || '');
    rep.innerHTML = value;
    if (rule.matchSize !== false && height) rep.style.minHeight = Math.round(height) + 'px';
    el.parentNode.insertBefore(rep, el.nextSibling);
    record({ el: rep }, 'remove', null);
    hideEl(el);
    replacements.push({ orig: el, rep: rep });
  }

  /* The app redrew something we changed: put our version back (images, hidden originals,
     replacement markup the app's own re-render dropped). */
  function reassertVisual(el) {
    var v = appliedImage.get(el);
    if (v !== undefined && !imageHolds(el, v)) applyImage(el, v);
    if (hiddenEls.has(el) && el.style.getPropertyValue('display') !== 'none') el.style.setProperty('display', 'none', 'important');
  }

  function maintainReplacements() {
    replacements = replacements.filter(function (r) {
      if (!r.orig.isConnected) { if (r.rep.parentNode) r.rep.parentNode.removeChild(r.rep); return false; }
      if (!r.rep.isConnected) r.orig.parentNode.insertBefore(r.rep, r.orig.nextSibling);
      return true;
    });
  }

  function needsAttrWatch(rules) {
    return (rules || []).some(function (r) { return r.action === 'image' || r.action === 'hide' || r.action === 'replaceWith'; });
  }

  function applySelectorRules(rules) {
    var hits = 0;
    /* Scoped rules run first so they claim their elements before general ones (E4). */
    var ordered = (rules || []).map(function (rule, ri) { return { rule: rule, ri: ri }; })
      .sort(function (a, b) { return (b.rule.scope ? 1 : 0) - (a.rule.scope ? 1 : 0) || a.ri - b.ri; });
    ordered.forEach(function (o) {
      var rule = o.rule, ri = o.ri;
      var els;
      try { els = document.querySelectorAll(rule.selector); } catch (e) { return; }
      if (ruleCursor[ri] === undefined) ruleCursor[ri] = 0;
      var claimKey = rule.action + ':' + (rule.attr || rule.styleProp || '');
      Array.prototype.forEach.call(els, function (el, i) {
        if (typeof rule.index === 'number' && rule.index !== i) return;
        var holder = null;
        if (rule.scope) {
          try { holder = el.closest(rule.scope); } catch (e) { return; }
          if (!holder) return;
          /* perScope: claim at most N elements per scope element; the rest fall through to later rules. */
          if (rule.perScope) {
            if (!scopeCounts[ri]) scopeCounts[ri] = new WeakMap();
            var used = scopeCounts[ri].get(holder) || 0;
            if (used >= rule.perScope) return;
            if (!claim(el, claimKey)) return;
            scopeCounts[ri].set(holder, used + 1);
          } else if (!claim(el, claimKey)) return;
        } else if (!claim(el, claimKey)) return;
        var values = Array.isArray(rule.value) ? rule.value : [rule.value];
        var value = pickValue(rule, ri, el, values);
        switch (rule.action) {
          case 'text':
            recordChildren(el);
            el.textContent = value;
            appliedText.set(el, { action: 'text', value: value });
            break;
          case 'html':
            recordChildren(el);
            el.innerHTML = value;
            appliedText.set(el, { action: 'html', value: el.innerHTML });
            break;
          case 'attr':
            record({ el: el, attr: rule.attr }, 'attribute', el.getAttribute(rule.attr));
            el.setAttribute(rule.attr, value);
            break;
          case 'style':
            record({ el: el, styleProp: rule.styleProp }, 'style', el.style.getPropertyValue(rule.styleProp));
            el.style.setProperty(rule.styleProp, value, 'important');
            break;
          case 'hide':
            hideEl(el);
            break;
          case 'image':
            applyImage(el, value);
            break;
          case 'replaceWith':
            applyReplace(el, rule, value);
            break;
          default:
            return;
        }
        hits++;
      });
    });
    return hits;
  }

  function applyCssVars(vars) {
    if (!vars) return 0;
    var root = document.documentElement;
    var n = 0;
    Object.keys(vars).forEach(function (k) {
      record({ el: root, styleProp: k }, 'style', root.style.getPropertyValue(k));
      root.style.setProperty(k, vars[k], 'important');
      n++;
    });
    return n;
  }

  function injectCss(css) {
    if (!css) return;
    var tag = document.createElement('style');
    tag.id = 'demo-tailor-css';
    tag.setAttribute('data-demo-tailor-skip', '');
    tag.textContent = css;
    document.head.appendChild(tag);
    record({ el: tag }, 'remove', null);
  }

  function runPass(root) {
    if (!current) return { text: 0, attrs: 0 };
    var avoid = (current.avoidSelectors || DEFAULT_AVOID);
    return {
      text: applyTextRules(root, current.textRules || [], avoid),
      attrs: applyAttrRules(root, current.attrRules || current.textRules || [], avoid)
    };
  }

  /* If the app rewrote text inside an element a text/html rule set, put our value back (E1). */
  function reassertApplied(node) {
    var el = node.nodeType === 1 ? node : node.parentElement;
    while (el) {
      var a = appliedText.get(el);
      if (a) {
        if (a.action === 'text' && el.textContent !== a.value) el.textContent = a.value;
        if (a.action === 'html' && el.innerHTML !== a.value) el.innerHTML = a.value;
        return;
      }
      el = el.parentElement;
    }
  }

  function startObserver() {
    if (observer) observer.disconnect();
    observer = new MutationObserver(function (mutations) {
      if (applying) return;
      applying = true;
      try {
        var added = [];
        var changedText = [];
        var removedReplacement = false;
        mutations.forEach(function (m) {
          if (m.type === 'attributes') { if (m.target.isConnected) reassertVisual(m.target); return; }
          Array.prototype.forEach.call(m.removedNodes || [], function (n) {
            if (n.nodeType === 1 && n.hasAttribute('data-demo-tailor-replacement')) removedReplacement = true;
          });
          if (m.type === 'characterData') {
            if (m.target.isConnected) changedText.push(m.target);
            return;
          }
          Array.prototype.forEach.call(m.addedNodes, function (n) {
            if (n.nodeType === 1) added.push(n);
            else if (n.nodeType === 3 && n.parentElement) added.push(n.parentElement);
          });
          if (m.target && m.target.nodeType === 1) changedText.push(m.target);
        });
        if (added.length && current && current.selectorRules) applySelectorRules(current.selectorRules);
        if (added.length || removedReplacement) maintainReplacements();
        changedText.forEach(function (n) { if (n.isConnected) reassertApplied(n); });
        added.forEach(function (n) { if (n.isConnected) runPass(n); });
        changedText.forEach(function (n) { if (n.isConnected && n.nodeType === 3) runPass(n); });
      } finally {
        /* Drop the mutations our own writes just caused, so the engine never triggers itself. */
        if (observer) observer.takeRecords();
        applying = false;
      }
    });
    var opts = { childList: true, subtree: true, characterData: true };
    if (current && needsAttrWatch(current.selectorRules)) {
      opts.attributes = true;
      opts.attributeFilter = ['src', 'srcset', 'href', 'xlink:href', 'style'];
    }
    observer.observe(document.documentElement, opts);
  }

  function apply(payload) {
    /* Applying twice equals applying once (E5). */
    if (current || undoLog.length) revert();
    current = payload || {};
    applying = true;
    var stats;
    try {
      stats = { selectors: applySelectorRules(current.selectorRules) };
      var textStats = runPass(document.body);
      stats.text = textStats.text;
      stats.attrs = textStats.attrs;
      stats.cssVars = applyCssVars(current.cssVars);
      injectCss(current.injectCss);
    } finally {
      applying = false;
    }
    startObserver();
    return { ok: true, version: VERSION, applied: stats, undoEntries: undoLog.length };
  }

  function revert() {
    if (observer) { observer.disconnect(); observer = null; }
    for (var i = undoLog.length - 1; i >= 0; i--) {
      var e = undoLog[i];
      try {
        if (e.prop === 'attribute') {
          if (e.original === null) e.target.el.removeAttribute(e.target.attr);
          else e.target.el.setAttribute(e.target.attr, e.original);
        } else if (e.prop === 'style') {
          if (!e.original) e.target.el.style.removeProperty(e.target.styleProp);
          else e.target.el.style.setProperty(e.target.styleProp, e.original);
          if (e.target.el.getAttribute('style') === '') e.target.el.removeAttribute('style');
        } else if (e.prop === 'children') {
          while (e.target.firstChild) e.target.removeChild(e.target.firstChild);
          e.target.appendChild(e.original.cloneNode(true));
        } else if (e.prop === 'remove') {
          if (e.target.el && e.target.el.parentNode) e.target.el.parentNode.removeChild(e.target.el);
        } else {
          e.target[e.prop] = e.original;
        }
      } catch (err) {}
    }
    undoLog = [];
    claims = new WeakMap();
    appliedText = new WeakMap();
    appliedImage = new WeakMap();
    hiddenEls = new WeakSet();
    replacements = [];
    ruleCursor = [];
    scopeCounts = [];
    current = null;
    return { ok: true, reverted: true };
  }

  /* Inventory the page so the caller can decide what to replace.
     Returns the most common visible strings plus candidate branded tokens. */
  function scan(opts) {
    opts = opts || {};
    var limit = opts.limit || 120;
    var counts = {};
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
    var node;
    while ((node = walker.nextNode())) {
      if (skip(node, DEFAULT_AVOID)) continue;
      var t = (node.nodeValue || '').trim();
      if (!t || t.length > 120) continue;
      var el = node.parentElement;
      if (!el || !el.offsetParent) continue;
      counts[t] = (counts[t] || 0) + 1;
    }
    var strings = Object.keys(counts)
      .map(function (k) { return { text: k, count: counts[k] }; })
      .sort(function (a, b) { return b.count - a.count; })
      .slice(0, limit);

    var images = Array.prototype.slice.call(document.images)
      .filter(function (im) { return im.offsetParent; })
      .slice(0, 40)
      .map(function (im) {
        var pic = im.parentElement && im.parentElement.tagName === 'PICTURE';
        return { src: im.currentSrc || im.src, alt: im.alt, w: im.naturalWidth, h: im.naturalHeight, selector: cssPath(im), srcset: im.hasAttribute('srcset'), picture: !!pic };
      });

    return { url: location.href, title: document.title, strings: strings, images: images, visuals: scanVisuals() };
  }

  function isShown(el) {
    if (!el.getClientRects().length) return false;
    var cs = getComputedStyle(el);
    return cs.visibility !== 'hidden' && cs.display !== 'none';
  }

  /* What a chart is made of, so the browser pass can pick a replacement route:
     <canvas> (nothing to edit; replaceWith only), <svg> (text is reachable, shapes are
     not), and CSS background images (invisible to document.images). */
  function scanVisuals() {
    var out = { canvas: [], svg: [], backgroundImages: [] };
    Array.prototype.forEach.call(document.querySelectorAll('canvas'), function (c) {
      if (out.canvas.length < 40 && isShown(c)) out.canvas.push({ selector: cssPath(c), w: c.clientWidth, h: c.clientHeight, label: c.getAttribute('aria-label') || '' });
    });
    Array.prototype.forEach.call(document.querySelectorAll('svg'), function (v) {
      if (out.svg.length >= 40 || (v.parentElement && v.parentElement.closest('svg')) || !isShown(v)) return;
      var r = v.getBoundingClientRect();
      if (r.width < 48 || r.height < 32) return;  /* icons */
      var texts = Array.prototype.slice.call(v.querySelectorAll('text')).slice(0, 6).map(function (t) { return t.textContent.trim(); });
      out.svg.push({ selector: cssPath(v), w: Math.round(r.width), h: Math.round(r.height),
        shapes: v.querySelectorAll('path,rect,circle,line,polygon').length, texts: texts, label: v.getAttribute('aria-label') || '' });
    });
    Array.prototype.forEach.call(document.body.querySelectorAll('*'), function (el) {
      if (out.backgroundImages.length >= 40) return;
      var bg = getComputedStyle(el).backgroundImage;
      if (bg && bg.indexOf('url(') !== -1 && isShown(el)) out.backgroundImages.push({ selector: cssPath(el), url: bg.slice(0, 160) });
    });
    return out;
  }

  /* Visible leftovers after apply(): literal deny strings (case-insensitive)
     and regex patterns. Same visibility rules as scan() (E6). */
  function audit(opts) {
    opts = opts || {};
    var res = [];
    var deny = (opts.deny || []).map(function (d) { return new RegExp(escapeRe(d), 'gi'); });
    var pats = (opts.patterns || []).map(function (p) { return new RegExp(p, 'g'); });
    var walker = document.createTreeWalker(opts.root || document.body, NodeFilter.SHOW_TEXT, null);
    var node;
    while ((node = walker.nextNode())) {
      if (skip(node, DEFAULT_AVOID)) continue;
      var el = node.parentElement;
      if (!el || !el.offsetParent) continue;
      var t = node.nodeValue || '';
      deny.concat(pats).forEach(function (re) {
        re.lastIndex = 0;
        var m;
        while ((m = re.exec(t))) {
          res.push({ kind: 'text', match: m[0], text: t.trim().slice(0, 120), selector: cssPath(el) });
          if (!m[0]) re.lastIndex++;
        }
      });
    }
    /* Imagery: sources (img, svg <image>, CSS background) that match a deny substring. */
    var denyImg = (opts.denyImages || []).map(function (d) { return String(d).toLowerCase(); });
    if (denyImg.length) {
      Array.prototype.forEach.call((opts.root || document.body).querySelectorAll('*'), function (el) {
        var src = (el.tagName === 'IMG' ? (el.currentSrc || el.src) : el.tagName.toLowerCase() === 'image' ? (el.getAttribute('href') || '') : '') ||
          (function () { var bg = getComputedStyle(el).backgroundImage; return bg && bg.indexOf('url(') !== -1 ? bg : ''; })();
        if (!src || !isShown(el)) return;
        denyImg.forEach(function (d) {
          if (src.toLowerCase().indexOf(d) !== -1) res.push({ kind: 'image', match: d, text: src.slice(0, 120), selector: cssPath(el) });
        });
      });
    }
    /* Charts that should have been replaced but are still showing. */
    (opts.charts || []).forEach(function (sel) {
      var els;
      try { els = document.querySelectorAll(sel); } catch (e) { return; }
      Array.prototype.forEach.call(els, function (el) {
        if (isShown(el)) res.push({ kind: 'chart', match: sel, text: '', selector: cssPath(el) });
      });
    });
    return res;
  }

  function cssPath(el) {
    if (!el) return '';
    if (el.id) return '#' + CSS.escape(el.id);
    var parts = [];
    while (el && el.nodeType === 1 && parts.length < 5) {
      var part = el.tagName.toLowerCase();
      if (el.classList.length) {
        part += '.' + Array.prototype.slice.call(el.classList).slice(0, 2).map(function (c) { return CSS.escape(c); }).join('.');
      }
      parts.unshift(part);
      el = el.parentElement;
    }
    return parts.join(' > ');
  }

  window.__demoTailor = {
    version: VERSION,
    apply: apply,
    revert: revert,
    scan: scan,
    audit: audit,
    cssPath: cssPath,
    status: function () {
      return { version: VERSION, active: !!current, undoEntries: undoLog.length, observing: !!observer };
    }
  };

  return window.__demoTailor.status();
})();
