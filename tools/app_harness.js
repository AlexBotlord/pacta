// Behavioral harness for docs/app.js: runs the real script against a minimal synthetic DOM built from the real
// generated HTML (parsed by verify_site_v2.py with html.parser and passed as JSON on stdin). Pure node: no network,
// no HTTP server or listener, no files written; the pre-flight checker gets a mock fetch and the first-party beacon (docs/b.js)
// a recording navigator.sendBeacon mock. Prints one JSON object with every assertion result.
//
//   stdin: {"app": "<app.js source>", "request": <dom tree>, "index": <dom tree>, "rowId": "<a real record id>",
//           "beacon": "<b.js source>", "protocol": <dom tree of /protocols/<protocolSlug>/>, "protocolSlug": "<slug>",
//           "notfound": <dom tree of 404.html>}
//   tree node: ["tag", {attrs}, [children...]] or a text string
"use strict";
const vm = require("vm");

// ---------- strict mini selector engine (throws like a browser on malformed selectors) ----------
function parseCompound(src) {
  const c = { tag: null, id: null, classes: [], attrs: [], checked: false, not: [] };
  let i = 0;
  const ident = /^[A-Za-z_][\w-]*/;
  while (i < src.length) {
    const rest = src.slice(i);
    let m;
    if (i === 0 && (m = rest.match(/^[a-z][a-z0-9]*/))) { c.tag = m[0]; i += m[0].length; }
    else if (rest[0] === "#" && (m = rest.slice(1).match(ident))) { c.id = m[0]; i += 1 + m[0].length; }
    else if (rest[0] === "." && (m = rest.slice(1).match(ident))) { c.classes.push(m[0]); i += 1 + m[0].length; }
    else if ((m = rest.match(/^\[([\w-]+)(?:="([^"\\\]]*)")?\]/))) { c.attrs.push([m[1], m[2]]); i += m[0].length; }
    else if ((m = rest.match(/^:checked/))) { c.checked = true; i += m[0].length; }
    else if ((m = rest.match(/^:not\(([^()]+)\)/))) { c.not.push(parseCompound(m[1])); i += m[0].length; }
    else throw new SyntaxError("Failed to execute 'querySelector': '" + src + "' is not a valid selector.");
  }
  return c;
}
function parseSelector(sel) {
  if (/\\/.test(sel) || (sel.match(/\[/g) || []).length !== (sel.match(/\]/g) || []).length) {
    throw new SyntaxError("Failed to execute 'querySelector': '" + sel + "' is not a valid selector.");
  }
  return sel.split(",").map(s => s.trim().split(/\s+/).map(parseCompound));
}
function matchCompound(el, c) {
  if (!el || el.nodeType !== 1) return false;
  if (c.tag && el.tagName.toLowerCase() !== c.tag) return false;
  if (c.id && el.getAttribute("id") !== c.id) return false;
  for (const k of c.classes) if (!el.classList.contains(k)) return false;
  for (const [a, v] of c.attrs) { if (!el.hasAttribute(a)) return false; if (v !== undefined && el.getAttribute(a) !== v) return false; }
  if (c.checked && !el.checked) return false;
  for (const n of c.not) if (matchCompound(el, n)) return false;
  return true;
}
function matchChain(el, chain) {
  if (!matchCompound(el, chain[chain.length - 1])) return false;
  let i = chain.length - 2, p = el.parentNode;
  while (i >= 0 && p) { if (matchCompound(p, chain[i])) i--; p = p.parentNode; }
  return i < 0;
}
const matches = (el, list) => list.some(ch => matchChain(el, ch));

// ---------- minimal DOM ----------
class Node_ { constructor() { this.parentNode = null; this.childNodes = []; } }
class Text extends Node_ { constructor(t) { super(); this.nodeType = 3; this.data = t; } get textContent() { return this.data; } }
class ClassList {
  constructor(el) { this.el = el; }
  _get() { return (this.el.getAttribute("class") || "").split(/\s+/).filter(Boolean); }
  contains(k) { return this._get().includes(k); }
  add(k) { const s = this._get(); if (!s.includes(k)) s.push(k); this.el.setAttribute("class", s.join(" ")); }
  remove(k) { this.el.setAttribute("class", this._get().filter(x => x !== k).join(" ")); }
  toggle(k, force) { const on = force === undefined ? !this.contains(k) : !!force; on ? this.add(k) : this.remove(k); return on; }
}
class Element extends Node_ {
  constructor(tag, attrs) {
    super(); this.nodeType = 1; this.tagName = tag.toUpperCase(); this.attributes = Object.assign({}, attrs || {});
    this.style = {}; this.listeners = {}; this.classList = new ClassList(this);
    this._value = this.attributes.value !== undefined ? this.attributes.value : null;
    this._checked = "checked" in this.attributes; this._tabIndex = 0;
  }
  get checked() { return this._checked; }
  set checked(v) {   // radio-group semantics, as in a browser: checking one radio unchecks the others with its name
    this._checked = !!v;
    if (v && this.getAttribute("type") === "radio" && this.getAttribute("name")) {
      let root = this; while (root.parentNode) root = root.parentNode;
      for (const e of root._desc ? root._desc() : []) {
        if (e !== this && e.getAttribute("type") === "radio" && e.getAttribute("name") === this.getAttribute("name")) e._checked = false;
      }
    }
  }
  getAttribute(k) { return Object.prototype.hasOwnProperty.call(this.attributes, k) ? String(this.attributes[k]) : null; }
  setAttribute(k, v) { this.attributes[k] = String(v); }
  removeAttribute(k) { delete this.attributes[k]; }
  hasAttribute(k) { return Object.prototype.hasOwnProperty.call(this.attributes, k); }
  toggleAttribute(k, force) { const on = force === undefined ? !this.hasAttribute(k) : !!force; on ? this.setAttribute(k, "") : this.removeAttribute(k); return on; }
  get id() { return this.getAttribute("id") || ""; }
  get href() { return this.getAttribute("href") || ""; } set href(v) { this.setAttribute("href", v); }
  get hidden() { return this.hasAttribute("hidden"); } set hidden(v) { v ? this.setAttribute("hidden", "") : this.removeAttribute("hidden"); }
  get tabIndex() { return this._tabIndex; } set tabIndex(v) { this._tabIndex = v; }
  get value() { if (this._value !== null) return this._value; return this.tagName === "TEXTAREA" ? this.textContent : ""; }
  set value(v) { this._value = String(v); }
  get textContent() { return this.childNodes.map(c => c.textContent).join(""); }
  set textContent(v) { this.childNodes = []; if (v !== "" && v !== null && v !== undefined) this.appendChild(new Text(String(v))); }
  get innerHTML() { return this.textContent; } set innerHTML(v) { this.textContent = v; }
  get parentElement() { return this.parentNode && this.parentNode.nodeType === 1 ? this.parentNode : null; }
  appendChild(c) { if (typeof c === "string") c = new Text(c); c.parentNode = this; this.childNodes.push(c); return c; }
  remove() { if (this.parentNode) { this.parentNode.childNodes = this.parentNode.childNodes.filter(x => x !== this); this.parentNode = null; } }
  get children() { return this.childNodes.filter(c => c.nodeType === 1); }
  *_desc() { for (const c of this.children) { yield c; yield* c._desc(); } }
  querySelectorAll(sel) { const l = parseSelector(sel); return [...this._desc()].filter(e => matches(e, l)); }
  querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
  closest(sel) { const l = parseSelector(sel); let e = this; while (e && e.nodeType === 1) { if (matches(e, l)) return e; e = e.parentNode; } return null; }
  addEventListener(t, fn) { (this.listeners[t] = this.listeners[t] || []).push(fn); }
  dispatchEvent(ev) {
    ev.target = ev.target || this;
    let n = this;
    while (n && !ev._stop) { for (const fn of (n.listeners[ev.type] || []).slice()) fn.call(n, ev); n = n.parentNode; }
    return !ev.defaultPrevented;
  }
  scrollIntoView() {} focus() {} select() {}
  get elements() {
    const out = {};
    for (const e of this._desc()) { const nm = e.getAttribute("name"); if (nm && /^(INPUT|TEXTAREA|SELECT)$/.test(e.tagName) && !(nm in out)) out[nm] = e; }
    return out;
  }
}
class Event_ {
  constructor(type) { this.type = type; this.defaultPrevented = false; this._stop = false; this.target = null; }
  preventDefault() { this.defaultPrevented = true; } stopPropagation() { this._stop = true; }
}
function build(tree) {
  if (typeof tree === "string") return new Text(tree);
  const [tag, attrs, kids] = tree;
  const el = new Element(tag, attrs);
  for (const k of kids) el.appendChild(build(k));
  return el;
}

// ---------- run app.js on a page ----------
function run(tree, app, loc) {
  const html = build(tree);
  const body = html.querySelector("body") || html;
  const document = new Element("#document", {});
  document.nodeType = 9; document.appendChild(html);
  document.documentElement = html; document.body = body;
  document.createElement = tag => new Element(tag, {});
  document.createElementNS = (ns, tag) => new Element(tag, {});   // SVG rosettes (namespace irrelevant in the synthetic DOM)
  document.createTextNode = t => new Text(String(t));
  document.getElementById = id => document.querySelectorAll("[id]").find(e => e.getAttribute("id") === id) || null;
  document.execCommand = () => true;
  document.referrer = loc.referrer || "";
  html.scrollHeight = 4000;
  const winListeners = {};
  const location = { href: "https://pacta.wtf" + loc.path + (loc.search || "") + (loc.hash || ""), search: loc.search || "", hash: loc.hash || "",
    pathname: loc.path, protocol: loc.protocol || "https:", hostname: "pacta.wtf" };
  const window = {
    addEventListener: (t, fn) => { (winListeners[t] = winListeners[t] || []).push(fn); }, isSecureContext: false, location,
    scrollY: 0, innerHeight: 800
  };
  // navigator.sendBeacon is a recording mock (no network); loc.nav overrides it (e.g. doNotTrack, or no sendBeacon at all)
  const beacons = [];
  const navigator = Object.assign({ sendBeacon: (url, body) => { beacons.push({ url, body }); return true; } }, loc.nav || {});
  const ctx = {
    window, document, location, navigator, URLSearchParams, URL, AbortController: loc.noAbort ? undefined : AbortController,
    console, Promise, JSON, Date, Math, Event: Event_,
    localStorage: { getItem: () => null, setItem: () => {} },
    setTimeout: () => 0, clearTimeout: () => {}, setInterval: () => 0,
    fetch: loc.fetch || (() => Promise.reject(new Error("network disabled in harness")))
  };
  vm.createContext(ctx);
  // deferred scripts run in document order (app.js, then b.js), both before DOMContentLoaded
  if (app) vm.runInContext(app, ctx, { filename: "app.js" });
  if (loc.beacon) vm.runInContext(loc.beacon, ctx, { filename: "b.js" });
  document.dispatchEvent(new Event_("DOMContentLoaded"));
  const events = () => beacons.map(b => JSON.parse(b.body));
  return { document, window, winListeners, location, Event_, beacons, events };
}

// ---------- scenarios ----------
const input = JSON.parse(require("fs").readFileSync(0, "utf8"));
const res = {};
const SCOPE = "HARNESS-SCOPE-7c1e https://example.invalid/docs 0x1111111111111111111111111111111111111111";
const TX = "0x" + "ab".repeat(32);
const FORUM = "https://forum.example.invalid/t/harness-listing/1";
const OPT = {
  clearance: "Full Protocol Control-Plane Dossier ($2,500–$5,000 USDC, 24h SLA)",
  continuous: "Continuous Aligned Maintenance ($1,500 USDC per month)",
  api_sla: "Enterprise / High-Throughput API SLA (priced on scope)",
  community: "Community queue (free; unscheduled, typically 6–8 weeks)"
};
const SET = { invoice: "Option A: formal commercial invoice (PDF) and counterparty settlement", direct: "Option B: direct on-chain USDC settlement" };
function ghParams(doc) {
  const h = doc.getElementById("req-gh").getAttribute("href") || "";
  if (!/^https:\/\/github\.com\/Fractal-Neurons\/pacta\/issues\/new\?/.test(h)) return null;
  return new URLSearchParams(h.split("?")[1]);
}
function setField(doc, id, v) {
  const el = doc.getElementById(id); el.value = v;
  const ev = new Event_("input"); ev.target = el; el.dispatchEvent(ev);
}
function pick(doc, val) {
  const r = doc.querySelectorAll('input[name="tier"]').find(x => x.getAttribute("value") === val);
  r.checked = true;
  const ev = new Event_("change"); ev.target = r; r.dispatchEvent(ev);
}
const checked = doc => (doc.querySelector('input[name="tier"]:checked') || { getAttribute: () => null }).getAttribute("value");
const settled = doc => (doc.querySelector('input[name="settlement"]:checked') || { getAttribute: () => null }).getAttribute("value");
function settle(doc, val) {
  const r = doc.querySelectorAll('input[name="settlement"]').find(x => x.getAttribute("value") === val);
  r.checked = true;
  const ev = new Event_("change"); ev.target = r; r.dispatchEvent(ev);
}
const brief = doc => doc.getElementById("req-brief").textContent;
try {
  // (a) /request/ defaults to the 24h clearance settled by Option A (commercial invoice): settlement panel visible,
  //     tx field and direct-settlement address hidden, GitHub intake prefilled with the exact dropdown options
  let p = run(input.request, input.app, { path: "/request/" });
  const d = p.document, treasury = d.getElementById("req-form").getAttribute("data-treasury");
  res.default_is_clearance = checked(d) === "clearance";
  const sub = new Event_("submit");
  res.req_form_submit_prevented = d.getElementById("req-form").dispatchEvent(sub) === false && sub.defaultPrevented === true
    && !d.getElementById("req-form").hasAttribute("onsubmit");
  res.default_settlement_is_invoice = settled(d) === "invoice";
  res.clearance_pay_panel_shown = d.getElementById("req-pay").hidden === false;
  res.invoice_hides_tx_and_direct = d.getElementById("req-tx-field").hidden === true && d.getElementById("req-direct").hidden === true;
  let q = ghParams(d);
  res.clearance_github_href = q !== null;
  res.clearance_github_tier_exact = !!q && q.get("package_tier") === OPT.clearance && q.get("settlement_preference") === SET.invoice;
  res.clearance_brief_has_price_and_invoice = /\$5,000 USDC/.test(brief(d)) && brief(d).includes("Settlement: Option A") && !brief(d).includes("Payment:")
    && /^0x[0-9a-fA-F]{40}$/.test(treasury || "") && !brief(d).includes(treasury);
  res.pay_summary_tracks_tier = d.getElementById("req-pay-sum").textContent === "Full Protocol Control-Plane Dossier · $2,500–$5,000 USDC, 24h SLA";
  // (b) Option B (direct on-chain USDC): tx field + treasury shown; a valid tx hash + forum URL flow into the brief and the GitHub prefill
  settle(d, "direct");
  res.direct_shows_tx_and_treasury = d.getElementById("req-tx-field").hidden === false && d.getElementById("req-direct").hidden === false
    && brief(d).includes("Settlement: Option B") && brief(d).includes(treasury) && brief(d).includes("Pacta treasury (direct settlement EOA)")
    && !/\bSafe\b|multisig/i.test(brief(d));
  setField(d, "req-scope", SCOPE); setField(d, "req-forum", FORUM); setField(d, "req-tx", TX);
  q = ghParams(d);
  res.tx_valid_in_brief = brief(d).includes("Payment: " + TX) && !/\(check:/.test(brief(d));
  res.tx_valid_in_github = !!q && q.get("payment_tx_hash") === TX && q.get("settlement_preference") === SET.direct;
  res.forum_in_brief_and_github = brief(d).includes("Forum proposal: " + FORUM) && !!q && q.get("forum_proposal_url") === FORUM;
  res.tx_valid_not_flagged = d.getElementById("req-tx").hasAttribute("aria-invalid") === false;
  // (c) a malformed tx hash is flagged and never forwarded to GitHub
  setField(d, "req-tx", "0x1234");
  q = ghParams(d);
  res.tx_invalid_flagged = d.getElementById("req-tx").getAttribute("aria-invalid") === "true" && /\(check:/.test(brief(d));
  res.tx_invalid_not_in_github = !!q && !q.has("payment_tx_hash");
  setField(d, "req-tx", TX);
  // (c2) back to Option A drops the tx hash from the brief and the intake (it stays in the field)
  settle(d, "invoice");
  q = ghParams(d);
  res.invoice_drops_tx = !brief(d).includes(TX) && !!q && !q.has("payment_tx_hash") && d.getElementById("req-tx").value === TX;
  settle(d, "direct");
  // (d) switching to the community queue hides payment, drops the tx hash, keeps the intake link working
  pick(d, "community");
  q = ghParams(d);
  res.community_pay_panel_hidden = d.getElementById("req-pay").hidden === true;
  res.community_tx_field_hidden = d.getElementById("req-tx-field").hidden === true;
  res.community_github_tier_exact = !!q && q.get("package_tier") === OPT.community && !q.has("settlement_preference");
  res.community_no_tx_anywhere = !!q && !q.has("payment_tx_hash") && !brief(d).includes(TX) && !/Payment:|Settlement:/.test(brief(d));
  const ev = new Event_("click"); d.getElementById("req-gh").dispatchEvent(ev);
  res.community_click_not_prevented = ev.defaultPrevented === false;
  // (e) back to clearance restores the payment panel (Option B still chosen, so the tx hash returns)
  pick(d, "clearance");
  res.clearance_restores_pay_panel = d.getElementById("req-pay").hidden === false && ghParams(d).get("payment_tx_hash") === TX;
  // (e2) continuous and API SLA tracks: own dropdown option, own amount in the summary and the Option B payment line
  pick(d, "continuous");
  q = ghParams(d);
  res.continuous_track = q.get("package_tier") === OPT.continuous && brief(d).includes("$1,500 USDC per month in USDC to the Pacta treasury")
    && d.getElementById("req-pay-sum").textContent === "Continuous Aligned Maintenance · $1,500 USDC per month";
  pick(d, "api_sla");
  q = ghParams(d);
  res.api_sla_track = q.get("package_tier") === OPT.api_sla && d.getElementById("req-pay").hidden === false
    && d.getElementById("req-pay-sum").textContent === "Enterprise / High-Throughput API SLA · priced on scope";
  // (f) ?tier=community prefill; unknown tiers fall back to the default
  p = run(input.request, input.app, { path: "/request/", search: "?tier=community" });
  res.prefill_selects_community = checked(p.document) === "community" && p.document.getElementById("req-pay").hidden === true;
  p = run(input.request, input.app, { path: "/request/", search: "?tier=disclosure" });
  res.prefill_unknown_tier_keeps_clearance = checked(p.document) === "clearance";
  p = run(input.request, input.app, { path: "/request/", search: "?tier=rapid-500" });
  res.prefill_rapid_500 = checked(p.document) === "rapid-500" && p.document.getElementById("req-pay").hidden === false
    && ghParams(p.document) !== null && ghParams(p.document).get("package_tier") === "Rapid Single-Gap Re-Verification ($500 USDC, 24h SLA)";
  // (f2) /request/?tier=…&protocol=…&forum=…&settlement=… prefill (the conversion-card links)
  {
    const PF = "https://forum.example.invalid/t/listing-proposal/42";
    const fieldVal = (doc, id) => doc.getElementById(id).value;
    const box = (doc, slug) => doc.querySelectorAll('input[name="protocol"]').find(x => x.getAttribute("data-slug") === slug);
    const slug = input.prefillSlug, name = box(d, slug) && box(d, slug).getAttribute("value");
    let x = run(input.request, input.app, { path: "/request/", search: "?tier=clearance&protocol=" + slug + "&forum=" + encodeURIComponent(PF) });
    let xd = x.document, xq = ghParams(xd);
    res.prefill_clearance_protocol_forum = checked(xd) === "clearance" && settled(xd) === "invoice" && !!name && box(xd, slug).checked === true
      && fieldVal(xd, "req-org") === name && fieldVal(xd, "req-forum") === PF && brief(xd).includes("Protocols in scope: " + name)
      && brief(xd).includes("Forum proposal: " + PF) && xq.get("forum_proposal_url") === PF && xq.get("settlement_preference") === SET.invoice;
    x = run(input.request, input.app, { path: "/request/", search: "?tier=clearance&protocol=" + slug + "&forum=" + encodeURIComponent(PF) + "&settlement=direct" });
    xd = x.document;
    res.prefill_settlement_direct = settled(xd) === "direct" && xd.getElementById("req-tx-field").hidden === false
      && xd.getElementById("req-direct").hidden === false && brief(xd).includes("Settlement: Option B");
    x = run(input.request, input.app, { path: "/request/", search: "?tier=continuous&protocol=" + slug + "&settlement=invoice" });
    xd = x.document; xq = ghParams(xd);
    res.prefill_continuous_invoice = checked(xd) === "continuous" && settled(xd) === "invoice" && xq.get("package_tier") === OPT.continuous
      && xq.get("settlement_preference") === SET.invoice && fieldVal(xd, "req-forum") === "";
    x = run(input.request, input.app, { path: "/request/", search: "?tier=api_sla" });
    res.prefill_api_sla = checked(x.document) === "api_sla" && x.document.getElementById("req-pay").hidden === false;
    // an issuer slug that is not an indexed protocol (e.g. an onboarding brief) only fills the organisation field
    x = run(input.request, input.app, { path: "/request/", search: "?tier=clearance&protocol=kerne-kusd-base" });
    res.prefill_unknown_slug_text_only = fieldVal(x.document, "req-org") === "kerne-kusd-base"
      && x.document.querySelectorAll('input[name="protocol"]').every(b => b.checked === false);
    // hostile input: unknown / prototype enum values ignored; markup stays text; control and bidi characters stripped; length capped
    const evil = "<img src=x onerror=alert(1)>" + String.fromCharCode(0, 7, 0x202e, 0x2066, 0x200b) + "x".repeat(200);
    x = run(input.request, input.app, { path: "/request/", search: "?tier=constructor&settlement=__proto__&protocol=" + encodeURIComponent(evil) + "&forum=" + encodeURIComponent("javascript:alert(1)") });
    xd = x.document;
    const org = fieldVal(xd, "req-org");
    res.prefill_hostile_inert = checked(xd) === "clearance" && settled(xd) === "invoice" && org.length === 80 && org.startsWith("<img src=x onerror=alert(1)>xxx")
      && !/[\u0000-\u001f\u202e\u2066\u200b]/.test(org) && fieldVal(xd, "req-forum") === ""
      && xd.querySelectorAll("img").length === d.querySelectorAll("img").length && !xd.querySelectorAll("img").some(i => i.getAttribute("onerror") !== null)
      && brief(xd).includes("Organization: <img src=x onerror=alert(1)>");
    for (const tier of ["__proto__", "toString", "hasOwnProperty", "TIER", "clearance%00", ""]) {
      x = run(input.request, input.app, { path: "/request/", search: "?tier=" + tier + "&settlement=" + tier });
      if (checked(x.document) !== "clearance" || settled(x.document) !== "invoice") res.prefill_enum_closed = false;
    }
    if (res.prefill_enum_closed !== false) res.prefill_enum_closed = true;
    const badForums = ["http://forum.example.invalid/t/1", "https://user:pw@forum.example.invalid/t/1", "https://:pw@forum.example.invalid/",
      "https://forum.example.invalid/" + "a".repeat(300), "https://forum.example.invalid/t 1", "data:text/html,hi", "//forum.example.invalid/t/1", "https:"];
    res.prefill_forum_https_only = badForums.every(f => fieldVal(run(input.request, input.app, { path: "/request/", search: "?forum=" + encodeURIComponent(f) }).document, "req-forum") === "");
  }
  p = run(input.index, input.app, { path: "/" });
  // (h) malformed hashes never throw during initialization; a real id still opens its drawer
  for (const h of ["#r-[unclosed", "#r-x\\", "#r-\"]", "#r-%E0%A4%A"]) {
    try { run(input.index, input.app, { path: "/", hash: h }); res["hash_ok " + h] = true; }
    catch (e) { res["hash_ok " + h] = false; res["hash_err " + h] = String(e); }
  }
  // (i0) the hero livebar names the next ETA that has not elapsed yet (tick() runs on DOMContentLoaded)
  {
    const lb = p.document.querySelector(".livebar");
    const pairs = (lb && lb.getAttribute("data-etas") || "").split(";").map((x) => x.split("|"));
    const nowS = Math.floor(Date.now() / 1000), want = pairs.find((x) => parseInt(x[0], 10) > nowS);
    const lp = lb && lb.querySelector(".lb-p"), cd = lb && lb.querySelector(".countdown"), nx = lb && lb.querySelector(".lb-next");
    res.livebar_skips_elapsed_etas = !!lb && pairs.length >= 2 && (want
      ? lp.textContent === want[1] && cd.getAttribute("data-eta") === want[0]
      : /past its ETA/.test(nx.textContent));
  }
} catch (e) {
  res.harness_error = String(e && e.stack || e);
}

// (i) live pre-flight checker: nothing is fetched on load; a preset fetches the free API exactly once; the response is
// rendered as text only (an HTML-looking summary stays text); cast commands carry the pinned block; bad input and
// HTTP errors never throw and never fetch. Mock fetch only: no network.
const PF_EXAMPLE = { schema: "pacta.preflight_check.v1", chain: "base", chainId: 8453, address: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  pinnedBlock: 23800000, pinnedBlockHash: "0x" + "ab".repeat(32), verdict: "MULTISIG_NO_TIMELOCK", riskScore: 60, isContract: true, isProxy: true,
  implementation: "0x2222222222222222222222222222222222222222", hasAdminSlot: true, canUpgradeZeroDelay: true,
  capabilities: { pause: true, blacklist: false, upgrade: true }, paused: false,
  controller: { address: "0x3333333333333333333333333333333333333333", kind: "multisig_safe", safeThreshold: 3, timelockDelaySec: null, safeOwnerCount: 5 },
  summary: "<img src=x onerror=alert(1)> 3-of-5 Safe" };
const flush = () => new Promise(r => setImmediate(r));
async function preflightScenario() {
  const calls = [];
  let reply = { status: 200, body: PF_EXAMPLE };
  const fetchMock = (url) => {   // the inspector loads this site's own /api/v1 JSON; only API calls are counted
    if (!/\/v1\/check\/preflight/.test(String(url))) return Promise.reject(new Error("site data not needed here"));
    calls.push(String(url)); const r = reply; return Promise.resolve({ status: r.status, json: () => Promise.resolve(r.body) });
  };
  const p = run(input.index, input.app, { path: "/", fetch: fetchMock });
  const d = p.document, out = d.getElementById("pf-out"), box = d.querySelector(".pf");
  res.pf_present = !!out && !!box && /^https:\/\//.test(box.getAttribute("data-api") || "");
  res.pf_no_fetch_on_load = calls.length === 0;
  const preset = d.querySelectorAll("[data-pf-address]")[0];
  preset.dispatchEvent(new Event_("click"));
  await flush(); await flush(); await flush();
  const want = box.getAttribute("data-api") + "/v1/check/preflight?chain=" + preset.getAttribute("data-pf-chain") + "&address=" + preset.getAttribute("data-pf-address")
    + "&caller_agent=pacta-wtf-checker&requester_role=individual_user&caller_purpose=general_research";
  res.pf_preset_fetches_once = calls.length === 1 && calls[0] === want;
  const txt = out.textContent;
  res.pf_renders_verdict = txt.includes("MULTISIG_NO_TIMELOCK") && txt.includes("Risk 60/100") && txt.includes("multisig_safe (3-of-5)") && txt.includes("pause, upgrade");
  // V05 + F05: plain-English verdict with the raw enum / JSON one click away; live contract check vs pinned comparison; 1-click RPC verify
  res.pp2_verdict_plain = txt.includes("A multisig can change it with no delay") && txt.includes("Heuristic score") && !!out.querySelector("[data-pf-raw]")
    && out.querySelector("[data-pf-raw]").textContent.includes("MULTISIG_NO_TIMELOCK") && txt.includes("Live contract check")
    && !!out.querySelector("[data-live-verify-btn]") && txt.includes('"getOwners()(address[])"') && txt.includes("--field hash");
  res.pf_text_only = out.querySelectorAll("img").length === 0 && txt.includes("<img src=x onerror=alert(1)>");
  res.pf_cast_commands = txt.includes("cast storage " + PF_EXAMPLE.address + " 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc --block 23800000")
    && txt.includes('"getThreshold()(uint256)" --block 23800000') && txt.includes("--rpc-url $BASE_RPC_URL");
  const form = d.getElementById("pf-form"), addr = form.querySelector('input[name="address"]');
  addr.value = "0x123"; const sev = new Event_("submit"); form.dispatchEvent(sev);
  await flush();
  res.pf_invalid_address_no_fetch = calls.length === 1 && sev.defaultPrevented === true && /40-hex/.test(out.textContent);
  reply = { status: 429, body: { error: "rate_limited", detail: "60 requests / minute" } };
  addr.value = PF_EXAMPLE.address; form.dispatchEvent(new Event_("submit"));
  await flush(); await flush(); await flush();
  res.pf_http_error_reported = calls.length === 2 && /HTTP 429 \(rate_limited\)/.test(out.textContent)
    && !!out.querySelector('[data-pf-state="ratelimit"]') && !!out.querySelector("[data-pf-retry]");
}
// (j) Codex F1 regression: a valid check is in flight, then an invalid address is submitted; the stale HTTP 200 resolves
// afterwards and must not overwrite the input error. The superseded request is aborted (AbortController).
async function staleResponseScenario() {
  const calls = [], signals = [];
  let release = null;
  const fetchMock = (url, opts) => {
    if (!/\/v1\/check\/preflight/.test(String(url))) return Promise.reject(new Error("site data not needed here"));
    calls.push(String(url)); signals.push(opts && opts.signal);
    return new Promise(r => { release = () => r({ status: 200, json: () => Promise.resolve(PF_EXAMPLE) }); });
  };
  const p = run(input.index, input.app, { path: "/", fetch: fetchMock });
  const d = p.document, out = d.getElementById("pf-out"), form = d.getElementById("pf-form"), addr = form.querySelector('input[name="address"]');
  addr.value = PF_EXAMPLE.address; form.dispatchEvent(new Event_("submit"));
  await flush();
  const pending = calls.length === 1 && /Checking/.test(out.textContent);
  addr.value = "0xnot-an-address"; form.dispatchEvent(new Event_("submit"));
  await flush();
  release(); await flush(); await flush(); await flush();
  res.pf_f1_stale_200_keeps_input_error = pending && calls.length === 1 && /40-hex/.test(out.textContent) && !out.textContent.includes("MULTISIG_NO_TIMELOCK");
  res.pf_f1_previous_request_aborted = !!signals[0] && signals[0].aborted === true;
  // same guarantee where AbortController does not exist (the sequence number alone protects the output)
  const p2 = run(input.index, input.app, { path: "/", fetch: fetchMock, noAbort: true });
  const f2 = p2.document.getElementById("pf-form"), a2 = f2.querySelector('input[name="address"]'), o2 = p2.document.getElementById("pf-out");
  a2.value = PF_EXAMPLE.address; f2.dispatchEvent(new Event_("submit")); await flush();
  a2.value = ""; f2.dispatchEvent(new Event_("submit")); await flush();
  release(); await flush(); await flush(); await flush();
  res.pf_f1_no_abortcontroller_still_safe = calls.length === 2 && signals[1] === undefined && /40-hex/.test(o2.textContent) && !o2.textContent.includes("MULTISIG_NO_TIMELOCK");
}

// (k) first-party beacon (docs/b.js) with a recording navigator.sendBeacon mock: payloads, copy hooks, scroll once, DNT,
// fetch fallback, 404, live-checker hook. Nothing leaves the process.
const BEACON = "https://pacta-x402.pacta.workers.dev/v1/telemetry/beacon";
const canon = x => Array.isArray(x) ? x.map(canon) : x && typeof x === "object" ? Object.keys(x).sort().reduce((o, k) => (o[k] = canon(x[k]), o), {}) : x;
const same = (a, b) => JSON.stringify(canon(a)) === JSON.stringify(canon(b));   // key order does not matter
function click(el) { const ev = new Event_("click"); el.dispatchEvent(ev); return ev; }
async function beaconScenario() {
  if (!input.beacon) { res.beacon_error = "no beacon source"; return; }
  const B = input.beacon;
  // page_load: referrer host + utm_source, string body to the first-party endpoint, nothing else on load
  let p = run(input.index, input.app, { path: "/", search: "?utm_source=Twitter&x=1", referrer: "https://news.ycombinator.com/item?id=1", beacon: B });
  res.b_page_load_payload = p.beacons.length === 1 && p.beacons[0].url === BEACON && typeof p.beacons[0].body === "string"
    && same(p.events()[0], { v: 1, e: "page_load", p: "/", r: "news.ycombinator.com", u: "twitter" });
  res.b_hook_exposed = typeof p.window.pactaBeacon === "function";
  // copy hooks, by what the button copies / the link points to
  const d = p.document, n0 = p.beacons.length;
  const copyMcp = d.querySelectorAll("button[data-copy]").find(b => /\/mcp$/.test(b.getAttribute("data-copy")));
  const copyCurl = d.querySelectorAll("button[data-copy]").find(b => /^curl /.test(b.getAttribute("data-copy")));
  const skill = d.querySelectorAll("a[href]").find(a => a.getAttribute("href") === "SKILL.md");
  const cta = d.querySelectorAll("a.primary")[0];
  click(copyMcp); click(copyCurl); click(skill); click(cta);
  res.b_copy_and_cta_events = same(p.events().slice(n0).map(e => e.e), ["copy_mcp_url", "copy_curl", "copy_skill_md", "cta_click"])
    && p.events().slice(n0).every(e => e.p === "/" && !("r" in e) && !("u" in e));
  // scroll_50 / scroll_90 fire once each
  const scroll = y => { p.window.scrollY = y; (p.winListeners.scroll || []).forEach(fn => fn({})); };
  const n1 = p.beacons.length;
  scroll(100); scroll(1300); scroll(1400); scroll(2900); scroll(3200); scroll(1300);
  res.b_scroll_once_each = same(p.events().slice(n1).map(e => e.e), ["scroll_50", "scroll_90"]);
  // the live checker reports chain:address (lowercased) through the hook
  const calls = [];
  const fetchMock = (url) => {
    if (!/\/v1\/check\/preflight/.test(String(url))) return Promise.reject(new Error("site data not needed here"));
    calls.push(String(url)); return Promise.resolve({ status: 200, json: () => Promise.resolve(PF_EXAMPLE) });
  };
  p = run(input.index, input.app, { path: "/", beacon: B, fetch: fetchMock });
  const f = p.document.getElementById("pf-form");
  f.querySelector('select[name="chain"]').value = "base";
  f.querySelector('input[name="address"]').value = PF_EXAMPLE.address;
  f.dispatchEvent(new Event_("submit")); await flush(); await flush(); await flush();
  const lc = p.events().filter(e => e.e === "live_checker_submit");
  res.b_live_checker_submit = lc.length === 1 && lc[0].t === "base:" + PF_EXAMPLE.address.toLowerCase() && calls.length === 1
    && p.document.getElementById("pf-out").textContent.includes("MULTISIG_NO_TIMELOCK");
  f.querySelector('input[name="address"]').value = "0x12"; f.dispatchEvent(new Event_("submit")); await flush();
  res.b_invalid_submit_not_reported = p.events().filter(e => e.e === "live_checker_submit").length === 1;
  // same-site referrer = "self"; protocol pages add t=slug and protocol_view; the term copy button = copy_curl
  if (input.protocol) {
    const path = "/protocols/" + input.protocolSlug + "/";
    p = run(input.protocol, input.app, { path, referrer: "https://pacta.wtf/protocols/", beacon: B });
    res.b_protocol_view = same(p.events(), [{ v: 1, e: "page_load", p: path, r: "self", t: input.protocolSlug }, { v: 1, e: "protocol_view", p: path, t: input.protocolSlug }]);
    const termBtn = p.document.querySelectorAll("button[data-copy-term]").find(b => /^curl /.test(b.closest(".term").querySelector("pre").textContent));
    const n2 = p.beacons.length; click(termBtn);
    const foot = p.document.querySelector(".memo-foot a"); click(foot);
    res.b_protocol_copy_curl_and_cta = same(p.events().slice(n2).map(e => e.e), ["copy_curl", "cta_click"]);
    // conversion callouts: every data-cta link (aligned page: maintenance + invoice; delta / RPC-observed page and briefs:
    // clearance + commercial invoice) fires cta_click
    const ctaClicks = (tree, path) => {
      const q = run(tree, input.app, { path, beacon: B }), links = q.document.querySelectorAll("a[data-cta]"), n = q.beacons.length;
      links.forEach(click);
      return { kinds: links.map(a => a.getAttribute("data-cta")), events: q.events().slice(n).map(e => e.e) };
    };
    const al = ctaClicks(input.protocol, path);
    res.b_cta_aligned_maintenance = same(al.kinds, ["continuous", "continuous_invoice"]) && same(al.events, ["cta_click", "cta_click"]);
    if (input.clearanceProtocol) {
      const cl = ctaClicks(input.clearanceProtocol, "/protocols/" + input.clearanceSlug + "/");
      res.b_cta_clearance_protocol = same(cl.kinds, ["free_notify", "clearance", "clearance_invoice"]) && same(cl.events, ["cta_click", "cta_click", "cta_click"]);
    }
    if (input.brief) {
      const br = ctaClicks(input.brief, "/briefs/" + input.briefSlug + "/");
      res.b_cta_clearance_brief = same(br.kinds, ["free_notify", "clearance", "clearance_invoice"]) && same(br.events, ["cta_click", "cta_click", "cta_click"]);
    }
    const hp = ctaClicks(input.index, "/");
    res.b_cta_pricing = same(hp.kinds, ["pricing_free", "pricing_rapid_500", "pricing_dossier"]) && same(hp.events, ["cta_click", "cta_click", "cta_click"]);
  }
  // 404: not_found_404 instead of page_load; paths are redacted to a closed canonical set BEFORE transmission
  // (Phase C.1): only /protocols/<safe-slug>/ keeps its slug (and t); anything else is "/404"; IP / local referrers are dropped
  if (input.notfound) {
    p = run(input.notfound, input.app, { path: "/protocols/pendle-finance-v2", search: "?utm_source=newsletter", referrer: "https://github.com/x/y?z=1", beacon: B });
    res.b_not_found_404 = same(p.events(), [{ v: 1, e: "not_found_404", p: "/404", r: "github.com", u: "newsletter" }]);   // Phase C.2: every 404 is "/404", never a slug
    const spec = run(input.notfound, input.app, { path: "/reset/alice%40example.org/private-token", referrer: "https://192.0.2.44/secret", beacon: B });
    const spec2 = run(input.notfound, input.app, { path: "/protocols/pendle-finance-v2", referrer: "https://github.com/some/repo", beacon: B });
    res.b_c1_spec_payloads = same(spec.events(), [{ v: 1, e: "not_found_404", p: "/404" }])
      && same(spec2.events(), [{ v: 1, e: "not_found_404", p: "/404", r: "github.com" }])
      && same(run(input.notfound, input.app, { path: "/protocols/alice-jones", beacon: B }).events(), [{ v: 1, e: "not_found_404", p: "/404" }]);   // Codex F1 probe
    const redact = [["/protocols/no-such-protocol/extra", "/404"], ["/protocols/alice%40example.org", "/404"], ["/protocols/reset-token", "/404"],
      ["/users/john/secret", "/404"], ["/briefs/etherfi-op-0x244e/", "/404"], ["/a@b/" + "x".repeat(200), "/404"], ["/protocols/Aave", "/404"]];
    res.b_not_found_path_sanitised = redact.every(([path, want]) => { const e = run(input.notfound, input.app, { path, beacon: B }).events(); return same(e, [{ v: 1, e: "not_found_404", p: want }]); });
    const ref = (r) => run(input.index, input.app, { path: "/", referrer: r, beacon: B }).events()[0];
    res.b_c1_referrers_redacted = ["https://192.0.2.44/", "https://10.0.0.1:8080/x", "https://[::1]/", "https://localhost/", "https://box.local/",
      "https://printer.lan/", "https://192-0-2-44.nip.io/", "https://c0a8002c.sslip.io/", "https://2130706433/", "https://0x7f000001/", "http://intranet/",
      "https://box.corp/x", "https://box.intranet/x"]
      .every((r) => !("r" in ref(r))) && ref("https://news.ycombinator.com/item?id=1").r === "news.ycombinator.com";
    const utm = (q) => run(input.index, input.app, { path: "/", search: q, beacon: B }).events()[0];
    res.b_c1_utm_redacted = ["?utm_source=192.0.2.44", "?utm_source=alice.bob", "?utm_source=user-123456", "?utm_source=reset-token", "?utm_source=1abc",
      "?utm_source=" + "x".repeat(25), "?utm_source=alice%40example.org"].every((q) => !("u" in utm(q))) && utm("?utm_source=Twitter").u === "twitter";
    // a slug is taken only from a real page: the path must equal the page's <link rel="canonical"> (Phase C.2)
    const canon = "https://pacta.wtf/protocols/" + input.protocolSlug + "/";
    const pageFor = (url) => JSON.parse(JSON.stringify(input.protocol).split(canon).join(url));
    const pages = (input.protocolSlugs || []).map((sl) => run(pageFor("https://pacta.wtf/protocols/" + sl + "/"), input.app, { path: "/protocols/" + sl + "/", beacon: B }).events()[0]);
    res.b_c1_all_protocol_slugs_kept = pages.length === input.expectProtocols && pages.length === input.protocolSlugs.length && pages.every((e, i) => e.p === "/protocols/" + input.protocolSlugs[i] + "/" && e.t === input.protocolSlugs[i]);
    const mismatch = run(input.protocol, input.app, { path: "/protocols/alice-jones/", beacon: B }).events()[0];
    const brief = run(pageFor("https://pacta.wtf/briefs/etherfi-op-0x244e/"), input.app, { path: "/briefs/etherfi-op-0x244e/", beacon: B }).events()[0];
    res.b_c2_slug_only_from_canonical = same(mismatch, { v: 1, e: "page_load", p: "/other" }) && same(brief, { v: 1, e: "page_load", p: "/briefs/etherfi-op-0x244e/" })
      && same(run(input.protocol, input.app, { path: "/protocols/" + input.protocolSlug + "/index.html", beacon: B }).events()[0].p, "/protocols/" + input.protocolSlug + "/");
    const views = [["/request", "/request/"], ["/protocols", "/protocols/"], ["/llms", "/llms/"], ["/llms/index.html", "/llms/"], ["/llms/x", "/other"], ["/briefs/etherfi-op-0x244e/", "/other"],
      ["/protocols/aave-v3-gho/", "/other"], ["/demos/swapio-x402/", "/other"], ["/reset/alice%40example.org/x", "/other"]];   // index page: canonical is "/"
    res.b_c1_page_paths = views.every(([path, want]) => run(input.index, input.app, { path, beacon: B }).events()[0].p === want);
    const mcp = p.document.querySelectorAll("button[data-copy]").find(b => /\/mcp$/.test(b.getAttribute("data-copy")));
    if (mcp) click(mcp);
    res.b_not_found_copy_mcp = !!mcp && p.events().length === 2 && p.events()[1].e === "copy_mcp_url";
  }
  // Do Not Track: nothing at all (no beacon, no fetch), the hook stays callable; plain http (local previews): nothing
  const sent = [];
  const rec = (url, opts) => {   // records beacon traffic only; app.js's own site-data fetch (api/v1/index.json) is refused
    if (String(url) !== BEACON) return Promise.reject(new Error("site data not needed here"));
    sent.push([url, opts]); return Promise.resolve({ status: 0, type: "opaque" });
  };
  p = run(input.index, input.app, { path: "/", beacon: B, nav: { doNotTrack: "1" }, fetch: rec });
  click(p.document.querySelectorAll("button[data-copy]").find(b => /\/mcp$/.test(b.getAttribute("data-copy"))));
  p.window.scrollY = 3500; (p.winListeners.scroll || []).forEach(fn => fn({}));
  p.window.pactaBeacon("live_checker_submit", "ethereum:0x" + "1".repeat(40));
  res.b_dnt_sends_nothing = p.beacons.length === 0 && sent.length === 0 && typeof p.window.pactaBeacon === "function";
  p = run(input.index, input.app, { path: "/", beacon: B, protocol: "http:", fetch: rec });
  res.b_non_https_sends_nothing = p.beacons.length === 0 && sent.length === 0;
  // no sendBeacon: fetch keepalive no-cors with the same string body
  p = run(input.index, input.app, { path: "/", beacon: B, nav: { sendBeacon: undefined }, fetch: rec });
  await flush();
  res.b_fetch_fallback = sent.length === 1 && sent[0][0] === BEACON && sent[0][1].method === "POST" && sent[0][1].keepalive === true
    && sent[0][1].mode === "no-cors" && same(JSON.parse(sent[0][1].body), { v: 1, e: "page_load", p: "/" });
  // no cookies, no storage: the beacon run never touches document.cookie or localStorage
  let touched = false;
  const trap = { get: () => { touched = true; return ""; }, set: () => { touched = true; } };
  const t0 = run(input.index, null, { path: "/", beacon: B });   // b.js alone
  Object.defineProperty(t0.document, "cookie", trap);
  click(t0.document.querySelectorAll("button[data-copy]")[0]);
  res.b_no_cookie_access = !touched && t0.events().length >= 1;
}
// (j) live timelock re-check: brief pages and #radar fetch the free /v1/briefs/live-timelocks once on load and update the
// state badges with textContent + class only; failures and malformed payloads keep the static block-pinned state.
async function liveTimelockScenario() {
  if (!input.timelockBrief) { res.live_error = "no timelock brief page"; return; }
  const LIVE = "https://pacta-x402.pacta.workers.dev/v1/briefs/live-timelocks?caller_agent=pacta-wtf-radar&requester_role=individual_user&caller_purpose=governance_monitoring";
  const opsOf = (doc) => (doc.querySelector("#post-eta-status [data-ops]").getAttribute("data-ops") || "").split(/\s+/).filter(Boolean);
  const op = (opId, live, block = 26420000) => ({ protocol: "Ethena", opId, live, block: { number: block, hash: "0x" + "ab".repeat(32), timestamp: 1794700000 } });
  const runWith = async (tree, path, reply) => {
    const calls = [];
    const fetchMock = (url, init) => {
      calls.push({ url: String(url), init });
      if (reply instanceof Error) return Promise.reject(reply);
      return Promise.resolve({ status: reply.status, json: () => (reply.bad ? Promise.reject(new Error("bad json")) : Promise.resolve(reply.body)) });
    };
    const p = run(tree, input.app, { path, fetch: fetchMock });
    for (let i = 0; i < 6; i++) await flush();
    return { d: p.document, calls };
  };
  const badge = (d) => d.querySelector("#post-eta-status [data-ops]");
  // static state before any network: READY, never EXECUTED
  let x = await runWith(input.timelockBrief, "/briefs/ethena-ops-0x0ca0-0x1fe5/", new Error("offline"));
  const ids = opsOf(x.d);
  res.live_static_ready = ids.length === 2 && badge(x.d).textContent === "READY · EXECUTABLE NOW" && badge(x.d).classList.contains("ready")
    && x.calls.length === 1 && x.calls[0].url === LIVE && x.d.querySelector("[data-live-line]").textContent === "";
  // live: both executed -> EXECUTED, banner flips, clause says superseded, latest block named
  x = await runWith(input.timelockBrief, "/briefs/ethena-ops-0x0ca0-0x1fe5/", { status: 200, body: { operations: ids.map((i) => op(i, { status: "done", isOperationDone: true, isOperationPending: false })) } });
  const ban = x.d.getElementById("post-eta-status");
  res.live_flips_executed = badge(x.d).textContent === "EXECUTED" && badge(x.d).classList.contains("executed") && !badge(x.d).classList.contains("ready")
    && ban.classList.contains("executed") && /live re-check at block #26,420,000: EXECUTED/.test(ban.querySelector(".ps-clause").textContent)
    && /#26,420,000/.test(x.d.querySelector("[data-live-line]").textContent);
  // live: one ready, one done -> MIXED; still ready -> READY (no change of meaning)
  x = await runWith(input.timelockBrief, "/briefs/ethena-ops-0x0ca0-0x1fe5/", { status: 200, body: { operations: [op(ids[0], { status: "ready", isOperationPending: true, isOperationDone: false }), op(ids[1], { status: "done", isOperationDone: true })] } });
  res.live_mixed = badge(x.d).textContent === "MIXED" && badge(x.d).classList.contains("mixed");
  x = await runWith(input.timelockBrief, "/briefs/ethena-ops-0x0ca0-0x1fe5/", { status: 200, body: { operations: ids.map((i) => op(i, { status: "ready", isOperationPending: true, isOperationDone: false })) } });
  res.live_ready_kept = badge(x.d).textContent === "READY · EXECUTABLE NOW" && badge(x.d).getAttribute("data-live") === "1";
  // failures keep the static state: HTTP 502, malformed JSON, missing / partial operations, markup in the payload stays text
  let keep = true;
  for (const reply of [{ status: 502, body: {} }, { status: 200, bad: true }, { status: 200, body: { operations: "nope" } },
    { status: 200, body: { operations: [op(ids[0], { status: "done", isOperationDone: true })] } },
    { status: 200, body: { operations: ids.map((i) => op(i, { status: "<img src=x onerror=alert(1)>" })) } }]) {
    x = await runWith(input.timelockBrief, "/briefs/ethena-ops-0x0ca0-0x1fe5/", reply);
    keep = keep && badge(x.d).textContent === "READY · EXECUTABLE NOW" && !x.d.querySelectorAll("img").some((i) => i.getAttribute("onerror") !== null);
  }
  res.live_failures_keep_static = keep;
  // homepage #radar: the Ethena row badge updates; pages without data-live-timelocks never fetch
  x = await runWith(input.index, "/", { status: 200, body: { operations: ids.map((i) => op(i, { status: "done", isOperationDone: true })) } });
  const row = x.d.querySelectorAll("#radar [data-ops]").find((b) => b.getAttribute("data-ops") === ids.join(" "));
  res.live_radar_row = !!row && row.textContent === "EXECUTED" && x.calls.filter((c) => /live-timelocks/.test(c.url)).length === 1
    && x.calls.filter((c) => /live-timelocks/.test(c.url))[0].url === LIVE;
  x = await runWith(input.request, "/request/", { status: 200, body: { operations: [] } });
  res.live_no_fetch_elsewhere = x.calls.length === 0;
}
// /protocols/ (visitor review P1): Status x Chain x search combine (intersection); "Clear all" resets all three; 0 matches renders a
// one-click recovery prompt (textContent + data-precover buttons, no inline handlers); rows only toggle the hidden attribute.
function protocolFilterScenario() {
  if (!input.protocolsIndex) return;
  const x = run(input.protocolsIndex, input.app, { path: "/protocols/" }), d = x.document;
  const rows = d.querySelectorAll("#proto-table tbody tr"), shown = () => rows.filter((r) => !r.hidden);
  const count = () => d.getElementById("proto-count").textContent, q = d.getElementById("proto-q");
  const btn = (kind, k) => d.querySelectorAll(`[data-pfilter-${kind}]`).find((b) => b.getAttribute(`data-pfilter-${kind}`) === k);
  const press = (b) => { const ev = new Event_("click"); ev.target = b; b.dispatchEvent(ev); };
  const click = (kind, k) => press(btn(kind, k));
  const type = (v) => { q.value = v; const ev = new Event_("input"); ev.target = q; q.dispatchEvent(ev); };
  const pressed = (kind) => d.querySelectorAll(`[data-pfilter-${kind}][aria-pressed="true"]`).map((b) => b.getAttribute(`data-pfilter-${kind}`));
  const tierIs = (t) => (r) => r.getAttribute("data-ptier") === t, chainHas = (c) => (r) => r.getAttribute("data-pchains").split(" ").includes(c);
  const n = rows.length, want = (pred) => rows.filter(pred).length, empty = d.getElementById("proto-empty"), clear = d.getElementById("proto-clear");
  res.pfilter_initial_all = n === input.expectProtocols && shown().length === n && count() === n + " of " + n + " protocols shown" && empty.hidden && clear.hidden;
  let ok = true;
  for (const [kind, k, pred] of [["status", "aligned", tierIs("aligned")], ["status", "parameter_delta", tierIs("parameter_delta")], ["status", "rpc_observed", tierIs("rpc_observed")],
    ["chain", "ethereum", chainHas("ethereum")], ["chain", "base", chainHas("base")]]) {
    click("status", "all"); click("chain", "all"); click(kind, k);
    const label = (btn(kind, k).querySelector(".num") || { textContent: "" }).textContent;
    ok = ok && shown().length === want(pred) && shown().every(pred) && String(want(pred)) === label && pressed(kind).join() === k
      && count() === want(pred) + " of " + n + " protocols shown";
  }
  res.pfilter_pills_exact = ok;
  // independent groups intersect: Status Parameter Delta x Chain Base = rows that are both
  click("status", "parameter_delta"); click("chain", "base");
  const both = (r) => tierIs("parameter_delta")(r) && chainHas("base")(r);
  res.pfilter_status_x_chain = pressed("status").join() === "parameter_delta" && pressed("chain").join() === "base" && shown().length === want(both)
    && shown().every(both) && want(both) < want(tierIs("parameter_delta"))
    && d.getElementById("proto-active").textContent.includes("Status: Parameter Delta") && d.getElementById("proto-active").textContent.includes("Chain: Base") && !clear.hidden;
  click("status", "all"); click("chain", "all"); type("ethena");
  res.pfilter_text_search = shown().length >= 1 && shown().every((r) => (r.getAttribute("data-psearch") || "").includes("ethena")) && shown().length < n;
  // 0 matches: recovery prompt names the active filters and offers one-click fixes
  click("chain", "base"); type("stader");
  const recover = (k) => empty.querySelectorAll("[data-precover]").find((b) => b.getAttribute("data-precover") === k);
  res.pfilter_empty_prompt = shown().length === 0 && !empty.hidden && empty.textContent.includes("No Base protocols match “stader”")
    && !!recover("chain") && !!recover("search") && !recover("status") && count() === "0 of " + n + " protocols shown";
  press(recover("chain"));
  res.pfilter_recover_chain = shown().length >= 1 && shown().every((r) => (r.getAttribute("data-psearch") || "").includes("stader")) && pressed("chain").join() === "all"
    && empty.hidden && q.value === "stader";
  type("<img src=x onerror=alert(1)>");
  res.pfilter_inert = shown().length === 0 && d.querySelectorAll("img").every((i) => i.getAttribute("onerror") === null) && !empty.hidden
    && empty.querySelectorAll("img").length === 0;
  click("status", "aligned"); click("chain", "ethereum"); type("aave");
  press(clear);
  res.pfilter_clear_all = shown().length === n && q.value === "" && pressed("status").join() === "all" && pressed("chain").join() === "all" && clear.hidden
    && d.getElementById("proto-active").textContent === "";
  res.pfilter_reset = shown().length === n;
  // curator baskets: each basket shows exactly its tagged rows, combines with Chain, and Clear all resets it
  const inB = (k) => (r) => (r.getAttribute("data-pbaskets") || "").split(" ").includes(k);
  let bok = true;
  for (const k of ["stable_rwa", "eth_lst_lrt", "lending_vaults", "base"]) {
    click("basket", k);
    if (!(shown().length === want(inB(k)) && shown().length > 0 && pressed("basket").join() === k)) bok = false;
  }
  click("basket", "stable_rwa"); click("chain", "base");
  const comb = shown().length === want((r) => inB("stable_rwa")(r) && chainHas("base")(r)) && /Basket: Stablecoins & RWA/.test(d.getElementById("proto-active").textContent);
  press(clear);
  res.pp2_baskets_protocols = bok && comb && shown().length === n && pressed("basket").join() === "all";
}

// Visitor review P1 / P2 (homepage): live check first (hero button -> one preflight call), confidence framing + catalogMatch next to the
// score, the pinned-catalog fallback, pinned-snapshot ages, and the inspector "What differs" (JS) == tools/control_diff.py for every
// flagged record. Everything is rendered with textContent; a catalogMatch URL that is not a pacta.wtf record page is never linked.
async function visitorScenario() {
  const calls = [];
  let reply = { status: 200, body: PF_EXAMPLE };
  const fetchMock = (url) => {
    const u = String(url);
    if (/api\/v1\/scorecards\.json/.test(u) && input.scorecardsJson) return Promise.resolve({ status: 200, json: () => Promise.resolve(input.scorecardsJson) });
    if (/api\/v1\/index\.json/.test(u) && input.indexJson) return Promise.resolve({ status: 200, json: () => Promise.resolve(input.indexJson) });
    if (!/\/v1\/check\/preflight/.test(u)) return Promise.reject(new Error("not needed"));
    calls.push(u); const r = reply; return Promise.resolve({ status: r.status, json: () => Promise.resolve(r.body) });
  };
  const p = run(input.index, input.app, { path: "/", fetch: fetchMock });
  const d = p.document, out = d.getElementById("pf-out");
  await flush(); await flush(); await flush();
  // Edge v3 hero: three receipts; a click renders the pinned receipt instantly and runs the live check of the same contract
  const rec = d.querySelectorAll("[data-receipt]"), go = rec[0], ro = d.getElementById("receipt-out");
  reply = { status: 200, body: { ...PF_EXAMPLE, verdict: "UNCLASSIFIED_CONTRACT_CONTROLLER", riskScore: 60, source: "live_rpc",
    assessment: { coverage: "indexed_verified", confidence: "medium", method: "Live bytecode + storage heuristic", limits: ["riskScore is a heuristic."] },
    catalogMatch: { slug: "stader-labs-ethx", name: "Stader Labs (ETHx)", url: "https://pacta.wtf/protocols/stader-labs-ethx/", classification: "parameter_delta",
      pinnedBlock: 26403676, whatDiffers: { changed: [{ parameter: "Safe threshold", observed: "3-of-6", documented: "3-of-5" }],
        matched: [{ parameter: "Timelock delay", value: "7 d" }] } } } };
  go.dispatchEvent(new Event_("click"));
  const instant = !!ro && ro.hidden === false && ro.textContent.includes("Stader ETHx: Docs say 3-of-5 · Chain says 3-of-6 Safe")
    && ro.textContent.includes("Base EAS attested") && ro.querySelectorAll("a").some((a) => a.getAttribute("href") === "protocols/stader-labs-ethx/");
  await flush(); await flush(); await flush();
  const t = out.textContent, link = out.querySelectorAll("a").find((a) => a.textContent === "Full record →");
  res.v_hero_receipts = rec.length === 3 && instant && rec.every((b) => /^0x[0-9a-fA-F]{40}$/.test(b.getAttribute("data-pf-address") || ""))
    && rec.map((b) => b.getAttribute("data-r-name")).join("|") === "Stader ETHx|YO Protocol|Moonwell (Base)";
  res.v_hero_click_fetches = calls.length === 1 && calls[0].includes("address=" + go.getAttribute("data-pf-address"));
  res.v_assessment_next_to_score = t.includes("Risk 60/100") && t.includes("Confidence medium") && t.includes("Indexed & verified record")
    && t.includes("Limits: riskScore is a heuristic.");
  res.v_catalog_match = t.includes("Indexed by Pacta: Stader Labs (ETHx)") && t.includes("Changed: Safe threshold 3-of-6 observed vs 3-of-5 documented")
    && t.includes("Matched: Timelock delay: 7 d") && !!link && link.getAttribute("href") === "https://pacta.wtf/protocols/stader-labs-ethx/";
  reply = { status: 200, body: { ...reply.body, catalogMatch: { ...reply.body.catalogMatch, url: "javascript:alert(1)", name: "<img src=x onerror=alert(1)>" } } };
  go.dispatchEvent(new Event_("click"));
  await flush(); await flush(); await flush();
  res.v_catalog_url_guard = !out.querySelectorAll("a").some((a) => /javascript:/i.test(a.getAttribute("href") || "")) && out.querySelectorAll("img").length === 0;
  reply = { status: 200, body: { schema: "pacta.preflight_catalog_fallback.v1", source: "pinned_catalog_fallback", verdict: null, riskScore: null,
    summary: "Live RPC unavailable; Stader Labs (ETHx) is indexed by Pacta.", assessment: { coverage: "indexed_verified", confidence: "medium", method: "No live read", limits: [] },
    catalogMatch: { slug: "stader-labs-ethx", name: "Stader Labs (ETHx)", url: "https://pacta.wtf/protocols/stader-labs-ethx/", classification: "parameter_delta", pinnedBlock: 26403676 } } };
  go.dispatchEvent(new Event_("click"));
  await flush(); await flush(); await flush();
  res.v_fallback_rendered = out.textContent.includes("PINNED CATALOG RECORD") && out.textContent.includes("Live RPC unavailable")
    && out.textContent.includes("Indexed by Pacta: Stader Labs (ETHx)") && !/HTTP 200/.test(out.textContent);
  // the hero checker flags a malformed address on its own input (aria-invalid + aria-describedby) and clears it on a valid one
  const pf = d.getElementById("pf-form"), pin = pf.querySelector('input[name="address"]');
  pin.value = "0x123"; pf.dispatchEvent(new Event_("submit")); await flush();
  const bad = pin.getAttribute("aria-invalid") === "true" && pin.getAttribute("aria-describedby") === "pf-msg" && !!d.getElementById("pf-msg");
  pin.value = "0xA35b1B31Ce002FBF2058D22F30f95D405200A15b"; pf.dispatchEvent(new Event_("submit")); await flush(); await flush(); await flush();
  res.e3_checker_aria_invalid = bad && pin.getAttribute("aria-invalid") === null && pin.getAttribute("aria-describedby") === null;
  const ages = d.querySelectorAll("[data-age]");
  res.v_ages = ages.length >= 2 && ages.every((a) => / \(\d+d \d+h \d+m ago\)$| \(\d+h \d+m ago\)$/.test(a.textContent));
  // Edge v3 scorecards: 16 static flagship rows; search / filters / Show all hydrate every protocol from /api/v1/scorecards.json
  const cards = (input.scorecardsJson && input.scorecardsJson.protocols) || [];
  const rowsNow = () => d.querySelectorAll("#scorecards tr.sc-row"), visible = () => rowsNow().filter((r) => !r.hidden);
  res.e3_static_sixteen = rowsNow().length === 16 && d.querySelectorAll("#scorecards tr.sc-drawer").length === 16
    && rowsNow().every((r) => r.querySelector("svg.rosette") && r.querySelector(".grade"));
  // a drawer opens / closes from its row toggle and carries the 5-factor breakdown
  const tog0 = rowsNow()[0].querySelector(".sc-toggle"), dr0 = d.getElementById(tog0.getAttribute("aria-controls"));
  let ev = new Event_("click"); ev.target = tog0; d.querySelector("[data-sc-body]").dispatchEvent(ev);
  const opened = dr0.hidden === false && tog0.getAttribute("aria-expanded") === "true" && dr0.querySelectorAll("[data-factor]").length === 5;
  ev = new Event_("click"); ev.target = tog0; d.querySelector("[data-sc-body]").dispatchEvent(ev);
  res.e3_drawer_toggle = opened && dr0.hidden === true && tog0.getAttribute("aria-expanded") === "false";
  d.querySelector("[data-sc-all]").dispatchEvent(new Event_("click"));
  for (let i = 0; i < 4; i++) await flush();
  const all = rowsNow();
  res.e3_hydrated_all = cards.length === all.length && all.length > 16 && d.querySelector("[data-sc-all]").hidden === true
    && all.every((r) => r.querySelector("svg.rosette") && r.querySelector("svg.rosette").querySelectorAll("path").length === 5
      && /Upgradeability .*Timelock floor .*Signer quorum .*Emergency \/ freeze scope .*Docs-vs-chain parity/.test(r.querySelector("svg.rosette").getAttribute("aria-label") || ""))
    && d.querySelectorAll("#scorecards tr.sc-drawer").length === cards.length;
  const obs = cards.filter((c) => !c.easAttested).map((c) => c.slug);
  res.e3_observed_parity_hollow = obs.length > 0 && obs.every((s) => {
    const r = all.find((x) => x.getAttribute("data-slug") === s); const ps = r ? r.querySelector("svg.rosette").querySelectorAll("path") : [];
    return ps.length === 5 && ps[4].getAttribute("class") === "r-u";
  });
  const pill = (k) => d.querySelectorAll("[data-sc-f]").find((b) => b.getAttribute("data-sc-f") === k);
  pill("delta").dispatchEvent(new Event_("click")); await flush(); await flush();
  const nDelta = cards.filter((c) => c.grade === "delta").length;
  res.e3_filter_deltas = visible().length === nDelta && visible().every((r) => r.getAttribute("data-grade") === "delta") && pill("delta").getAttribute("aria-pressed") === "true";
  pill("base").dispatchEvent(new Event_("click")); await flush(); await flush();
  res.e3_filter_basket = visible().length === cards.filter((c) => (c.baskets || []).includes("base")).length && visible().length > 0;
  const q = d.getElementById("sc-q");
  pill("all").dispatchEvent(new Event_("click")); await flush();
  const tg = visible()[0].querySelector(".sc-toggle"); ev = new Event_("click"); ev.target = tg; d.querySelector("[data-sc-body]").dispatchEvent(ev);
  q.value = "zzz-no-such-protocol"; q.dispatchEvent(new Event_("input")); await flush(); await flush();
  const emp = d.querySelector("[data-sc-empty]");
  res.e3_zero_match = visible().length === 0 && emp.hidden === false && d.querySelectorAll("#scorecards tr.sc-drawer").every((x) => x.hidden);
  emp.querySelector("[data-sc-clear]").dispatchEvent(new Event_("click")); await flush();
  res.e3_clear_filters = q.value === "" && visible().length === cards.length && emp.hidden === true && pill("all").getAttribute("aria-pressed") === "true";
  q.value = "usdc"; q.dispatchEvent(new Event_("input")); await flush(); await flush();
  res.e3_search = visible().some((r) => r.getAttribute("data-slug") === "circle-usdc") && visible().length < cards.length;
  const rc = d.querySelector("[data-radar-counts]");
  res.pp2_radar_counts = !!rc && /^\d+ pending operations? across \d+ protocols? · \d+ recently executed$/.test(rc.textContent);
}

// F05 "Verify live on RPC" (behavioural): a mocked JSON-RPC responder for the four public RPCs records every call, so the test asserts
// eth_blockNumber comes first and the read is pinned to that exact hex block; the rendered text carries the decimal live block
// number, the full hex word, the decoded value, the RPC host and the latency in ms. Also D1 (IMMUTABLE_NO_ADMIN headline).
const LIVE_N = 26430123, LIVE_HEX = "0x" + LIVE_N.toString(16);
const RPC_HOST_RE = /^https:\/\/(ethereum-rpc\.publicnode\.com|eth\.drpc\.org|base-rpc\.publicnode\.com|mainnet\.base\.org)$/;
const W_ADDR = "0x000000000000000000000000" + "3333333333333333333333333333333333333333";
const W_UINT = "0x" + "0".repeat(63) + "3";
const ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103";
async function liveRpcScenario() {
  const log = []; let reply = PF_EXAMPLE, rpcFail = false;
  const fetchMock = (url, init) => {
    const u = String(url);
    if (RPC_HOST_RE.test(u)) {
      const q = JSON.parse(init.body); log.push({ url: u, method: q.method, params: q.params });
      if (rpcFail) return Promise.resolve({ status: 200, json: () => Promise.resolve({ jsonrpc: "2.0", id: 1, error: { code: -32000, message: "upstream down" } }) });
      let result = null;
      if (q.method === "eth_blockNumber") result = LIVE_HEX;
      else if (q.method === "eth_getBlockByNumber") result = { number: q.params[0], hash: "0x" + "ab".repeat(32) };
      else if (q.method === "eth_getCode") result = "0x6080604052";
      else if (q.method === "eth_getStorageAt") result = W_ADDR;
      else if (q.method === "eth_call") result = q.params[0].data === "0x8da5cb5b" ? W_ADDR : W_UINT;
      return Promise.resolve({ status: 200, json: () => Promise.resolve({ jsonrpc: "2.0", id: 1, result }) });
    }
    if (/\/v1\/check\/preflight/.test(u)) return Promise.resolve({ status: 200, json: () => Promise.resolve(reply) });
    if (/api\/v1\/index\.json/.test(u) && input.indexJson) return Promise.resolve({ status: 200, json: () => Promise.resolve(input.indexJson) });
    return Promise.reject(new Error("not needed"));
  };
  const p = run(input.index, input.app, { path: "/", fetch: fetchMock });
  const d = p.document, out = d.getElementById("pf-out"), tog = d.querySelector("#scorecards .sc-toggle");
  const panel = d.getElementById(tog.getAttribute("aria-controls"));
  for (let i = 0; i < 4; i++) await flush();
  const clickLive = async (root) => {
    const b = root.querySelector("[data-live-verify-btn]"); if (!b) return null;
    b.dispatchEvent(new Event_("click")); for (let i = 0; i < 10; i++) await flush();
    return root.querySelector("[data-live-verify-out]").textContent;
  };
  const tail = (q) => q.params[q.params.length - 1];
  // (1) scorecard drawer: opening it attaches Verify live on RPC for the protocol's lead record, read at a fresh block
  { const ev = new Event_("click"); ev.target = tog; d.querySelector("[data-sc-body]").dispatchEvent(ev); await flush(); }
  log.length = 0;
  const it = await clickLive(panel);
  res.pp3_inspector_live_rpc = !!it && log.length === 2 && log[0].method === "eth_blockNumber" && ["eth_call", "eth_getStorageAt"].includes(log[1].method)
    && tail(log[1]) === LIVE_HEX && it.includes("Live at block #" + LIVE_N + " (" + LIVE_HEX + ")")
    && ((it.includes("Raw: " + W_UINT) && it.includes("Decoded: uint256 3")) || (it.includes("Raw: " + W_ADDR) && it.includes("= address 0x3333333333333333333333333333333333333333")))
    && /(ethereum-rpc|base-rpc)\.publicnode\.com · \d+ ms$/.test(it) && panel.querySelectorAll(".lv-line").length === 4;
  // (2) pre-flight on a proxy: pinned block hash match + live block, eth_getCode and the EIP-1967 admin slot at that block
  const form = d.getElementById("pf-form");
  const submit = async (body) => {
    reply = body; form.querySelector('select[name="chain"]').value = "base"; form.querySelector('input[name="address"]').value = PF_EXAMPLE.address;
    form.dispatchEvent(new Event_("submit")); for (let i = 0; i < 4; i++) await flush();
  };
  await submit(PF_EXAMPLE);
  log.length = 0;
  const pt = await clickLive(out);
  const m = (k) => log.filter((q) => q.method === k);
  res.pp3_preflight_live_rpc_proxy = !!pt && m("eth_getBlockByNumber").length === 1 && m("eth_getBlockByNumber")[0].params[0] === "0x" + (23800000).toString(16)
    && m("eth_blockNumber").length === 1 && m("eth_getCode").length === 1 && tail(m("eth_getCode")[0]) === LIVE_HEX
    && m("eth_getStorageAt").length === 1 && m("eth_getStorageAt")[0].params[1] === ADMIN_SLOT && tail(m("eth_getStorageAt")[0]) === LIVE_HEX
    && log.indexOf(m("eth_blockNumber")[0]) < log.indexOf(m("eth_getCode")[0]) && log.every((q) => /base/.test(q.url))
    && pt.includes("Pinned block #23800000 hash 0x" + "ab".repeat(32) + " = pinned hash ✓")
    && pt.includes("Live at block #" + LIVE_N + " (" + LIVE_HEX + "): eth_getCode 5 bytes") && pt.includes("EIP-1967 admin slot: " + W_ADDR)
    && pt.includes("Decoded: uint256 ") && pt.includes("= address 0x3333333333333333333333333333333333333333")
    && (pt.match(/base-rpc\.publicnode\.com · \d+ ms/g) || []).length === 2;
  // (3) D1 + non-proxy: IMMUTABLE_NO_ADMIN renders the exact headline (heuristic caveat kept); the live read is owner() at the fresh block
  await submit({ ...PF_EXAMPLE, verdict: "IMMUTABLE_NO_ADMIN", riskScore: 0, isProxy: false, implementation: null, hasAdminSlot: false,
    controller: { address: null, kind: "none" }, capabilities: {}, summary: "No admin surface found." });
  const vt = out.querySelector(".pf-verdict"), vb = vt && vt.querySelector(".badge");
  res.pp3_immutable_headline = !!vt && (vb ? vb.textContent === "No standard upgrade or admin authority detected" : vt.textContent.startsWith("No standard upgrade or admin authority detected"))
    && vt.textContent.includes("Heuristic score") && !out.textContent.includes("cannot be changed");
  log.length = 0;
  const ot = await clickLive(out);
  res.pp3_preflight_live_rpc_owner = !!ot && m("eth_call").length === 1 && m("eth_call")[0].params[0].data === "0x8da5cb5b"
    && m("eth_call")[0].params[0].to === PF_EXAMPLE.address && tail(m("eth_call")[0]) === LIVE_HEX && m("eth_getStorageAt").length === 0
    && ot.includes("owner(): " + W_ADDR) && ot.includes("= address 0x3333333333333333333333333333333333333333") && ot.includes("#" + LIVE_N) && /\d+ ms$/.test(ot);
  // (4) both public RPCs fail: each endpoint is tried once and the failure is reported (no throw, no stale value)
  rpcFail = true; log.length = 0;
  const ft = await clickLive(panel);
  res.pp3_live_rpc_failure = !!ft && ft.startsWith("Live RPC check failed (upstream down)") && log.length === 2 && log[0].url !== log[1].url
    && log.every((q) => q.method === "eth_blockNumber");
}

(async () => {
  try { protocolFilterScenario(); } catch (e) { res.harness_error = (res.harness_error || "") + String(e && e.stack || e); }
  try { await preflightScenario(); } catch (e) { res.harness_error = (res.harness_error || "") + String(e && e.stack || e); }
  try { await staleResponseScenario(); } catch (e) { res.harness_error = (res.harness_error || "") + String(e && e.stack || e); }
  try { await beaconScenario(); } catch (e) { res.harness_error = (res.harness_error || "") + String(e && e.stack || e); }
  try { await liveTimelockScenario(); } catch (e) { res.harness_error = (res.harness_error || "") + String(e && e.stack || e); }
  try { await visitorScenario(); } catch (e) { res.harness_error = (res.harness_error || "") + String(e && e.stack || e); }
  try { await liveRpcScenario(); } catch (e) { res.harness_error = (res.harness_error || "") + String(e && e.stack || e); }
  process.stdout.write(JSON.stringify(res));
})();
