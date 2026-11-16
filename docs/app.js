// Pacta site v3: theme, live countdowns, copy buttons, live pre-flight checker, control-plane inspector, index filter + drawers,
// request builder. No wallet, no third-party trackers (the optional first-party beacon, b.js, is separate). Data comes from this site's own /api/v1/*.json files; the one exception is the
// pre-flight checker, which calls Pacta's own free API (data-api on .pf) only after an explicit submit or preset click.
// Record text is inserted with textContent (never innerHTML). Every control works without a mail client.
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { if (k === "text") n.textContent = attrs[k]; else n.setAttribute(k, attrs[k]); });
    (kids || []).forEach(function (c) { if (c !== null && c !== undefined) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return n;
  }
  function short(h, a, b) { return h.slice(0, a) + "…" + h.slice(-b); }
  function num(n) { return Number(n).toLocaleString("en-US"); }

  // ---- theme: Paper (default) / Slate ---------------------------------------------------------------
  function applyTheme(t) {
    if (t === "slate") document.documentElement.setAttribute("data-theme", "slate");
    else document.documentElement.removeAttribute("data-theme");
    $$(".tt span").forEach(function (s) { s.classList.toggle("on", s.getAttribute("data-t") === (t === "slate" ? "slate" : "paper")); });
    var b = $(".tt"); if (b) b.setAttribute("aria-label", "Theme: " + (t === "slate" ? "Slate (switch to Paper)" : "Paper (switch to Slate)"));
  }
  function initTheme() {
    var t = null; try { t = localStorage.getItem("pacta-theme"); } catch (e) {}
    applyTheme(t);
    var b = $(".tt");
    if (b) b.addEventListener("click", function () {
      var next = document.documentElement.getAttribute("data-theme") === "slate" ? "paper" : "slate";
      try { localStorage.setItem("pacta-theme", next); } catch (e) {}
      applyTheme(next);
    });
  }

  // ---- countdowns (an ETA is when execution becomes possible, not a guarantee) -----------------------
  function fmt(sec) {
    var d = Math.floor(sec / 86400), h = Math.floor(sec % 86400 / 3600), m = Math.floor(sec % 3600 / 60);
    return (d ? d + "d " : "") + h + "h " + m + "m";
  }
  // the hero livebar names the next queued ETA that has not elapsed yet (the static build names the earliest one)
  function advanceLivebar(now) {
    var lb = $(".livebar[data-etas]"); if (!lb) return;
    var next = (lb.getAttribute("data-etas") || "").split(";").map(function (x) {
      var i = x.indexOf("|"); return { eta: parseInt(x.slice(0, i), 10), p: x.slice(i + 1) };
    }).filter(function (o) { return o.eta > now && o.p; })[0];
    var p = $(".lb-p", lb), cd = $(".countdown", lb), wrap = $(".lb-next", lb);
    if (!p || !cd || !wrap) return;
    if (next) { p.textContent = next.p; cd.setAttribute("data-eta", String(next.eta)); }
    else { wrap.textContent = "Next: every queued operation is past its ETA; check the Radar for execution state"; }
  }
  function tick() {
    var now = Math.floor(Date.now() / 1000);
    advanceLivebar(now);
    $$("[data-eta]").forEach(function (n) {
      var eta = parseInt(n.getAttribute("data-eta"), 10);
      if (!eta) return;
      n.textContent = eta > now ? "Execution window opens in " + fmt(eta - now) : "Window open — verify execution state";
    });
  }

  // ---- live timelock re-check (read-only): one GET to the free /v1/briefs/live-timelocks on timelock briefs and #radar.
  //      Badges (data-ops) change only through textContent + class; any failure keeps the static block-pinned state.
  //      No polling, no reload, no markup from the network. --------------------------------------------------------------
  var OP_LABEL = { executed: "EXECUTED", ready: "READY · EXECUTABLE NOW", pending: "PENDING", unknown: "CANCELLED OR UNKNOWN", mixed: "MIXED" };
  var OP_STATES = ["executed", "ready", "pending", "unknown", "mixed"];
  var LIVE_TL_RE = /^https:\/\/pacta-x402\.pacta\.workers\.dev\/v1\/briefs\/live-timelocks(\?[a-z_=&.-]*)?$/;
  function liveOpState(op) {
    var l = op && typeof op.live === "object" && op.live ? op.live : {};
    if (l.isOperationDone === true || l.status === "done") return "executed";
    if (l.status === "ready" && l.isOperationPending !== false) return "ready";
    if (l.status === "pending") return "pending";
    if (l.status === "unset") return "unknown";
    return null;
  }
  function setOpState(b, st) {
    b.textContent = OP_LABEL[st];
    OP_STATES.forEach(function (c) { b.classList.toggle(c, c === st); });
    b.setAttribute("data-opstate", st);
    b.setAttribute("data-live", "1");
  }
  function applyLiveTimelocks(j) {
    if (!j || typeof j !== "object" || !Array.isArray(j.operations)) return;
    var by = {}, blk = null;
    j.operations.forEach(function (op) {
      var id = op && typeof op.opId === "string" ? op.opId.toLowerCase() : "", st = liveOpState(op);
      if (/^0x[0-9a-f]{64}$/.test(id) && st) by[id] = st;
      var n = op && op.block ? op.block.number : null;
      if (typeof n === "number" && isFinite(n) && n > 0 && (blk === null || n > blk)) blk = Math.floor(n);
    });
    var updated = 0;
    $$("[data-ops]").forEach(function (b) {
      var ids = (b.getAttribute("data-ops") || "").toLowerCase().split(/\s+/).filter(Boolean);
      var sts = ids.map(function (i) { return by[i]; });
      if (!sts.length || sts.some(function (s) { return !s; })) return;     // every operation must have been re-read
      var before = b.getAttribute("data-opstate"), st = sts.every(function (s) { return s === sts[0]; }) ? sts[0] : "mixed";
      setOpState(b, st);
      updated++;
      var banner = b.closest(".poststatus"), clause = banner && $(".ps-clause", banner);
      if (banner && st !== before) {
        OP_STATES.forEach(function (c) { banner.classList.toggle(c, c === st); });
        if (clause) clause.textContent = "(live re-check" + (blk !== null ? " at block #" + blk.toLocaleString("en-US") : "") + ": " + OP_LABEL[st]
          + "; the finalized-block reading below is superseded)";
      }
    });
    if (updated && blk !== null) {
      $$("[data-live-line]").forEach(function (n) {
        n.textContent = "Live re-check at the latest block #" + blk.toLocaleString("en-US") + " via the free /v1/briefs/live-timelocks.";
      });
    }
  }
  function initLiveTimelocks() {
    var host = $("[data-live-timelocks]");
    if (!host || typeof fetch !== "function" || !$("[data-ops]")) return;
    var url = host.getAttribute("data-live-timelocks") || "";
    if (!LIVE_TL_RE.test(url)) return;
    var init = { cache: "no-store", headers: { Accept: "application/json" } };
    try { if (typeof AbortSignal !== "undefined" && typeof AbortSignal.timeout === "function") init.signal = AbortSignal.timeout(8000); } catch (e) { /* no timeout */ }
    fetch(url, init)
      .then(function (r) { return r && r.status === 200 ? r.json() : null; })
      .then(applyLiveTimelocks, function () { /* offline / blocked / timeout: keep the static state */ })
      .catch(function () { /* malformed payload: keep the static state */ });
  }

  // ---- first-party beacon hooks: b.js defines window.pactaBeacon (and applies DNT / https / redaction); without it
  //      nothing is sent. copy_mcp_url / copy_curl by what a copy button copies, copy_skill_md, primary CTAs. --------
  function initBeaconHooks() {
    document.addEventListener("click", function (ev) {
      var B = window.pactaBeacon, x = ev.target, c, a, q, t;
      if (typeof B !== "function" || !x || !x.closest) return;
      if ((c = x.closest(".copy"))) {
        q = c.getAttribute("data-copy");
        if (q === null) { t = c.closest(".term"); t = t && t.querySelector("pre"); q = t ? t.textContent : ""; }
        if (/\/mcp\b/.test(q)) B("copy_mcp_url"); else if (/^curl /.test(q)) B("copy_curl");
      } else if ((a = x.closest("a"))) {
        if (/SKILL\.md$/.test(a.getAttribute("href") || "")) B("copy_skill_md");
        else if (a.closest("a.primary,.memo-foot a,a[data-cta]")) B("cta_click");
      }
    }, true);
  }

  // ---- copy to clipboard (works on http(s) and file://) ---------------------------------------------
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (resolve, reject) {
      var ta = el("textarea", { readonly: "", style: "position:fixed;top:-1000px;opacity:0" });
      ta.value = text; document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy") ? resolve() : reject(); } catch (e) { reject(e); } finally { ta.remove(); }
    });
  }
  function flash(btn, ok) {
    if (!btn.hasAttribute("data-label")) btn.setAttribute("data-label", btn.innerHTML);   // our own static markup
    clearTimeout(btn._t);
    btn.classList.toggle("done", ok);
    btn.textContent = ok ? "Copied!" : "Select and press Ctrl+C";
    btn._t = setTimeout(function () { btn.innerHTML = btn.getAttribute("data-label"); btn.classList.remove("done"); }, 1600);
  }
  function initCopy() {
    document.addEventListener("click", function (ev) {
      var b = ev.target.closest("[data-copy],[data-copy-from],[data-copy-term]");
      if (!b) return;
      ev.preventDefault(); ev.stopPropagation();
      var src = b.hasAttribute("data-copy-term") ? $("pre", b.closest(".term")) : $("#" + b.getAttribute("data-copy-from"));
      var text = b.hasAttribute("data-copy") ? b.getAttribute("data-copy") : (src ? src.textContent : "");
      copyText(text).then(function () {
        flash(b, true);
        var st = $("#req-status"); if (st && b.closest("#req-form")) st.textContent = "Copied! Paste it into an email to " + REQ_TO + " from any mail app.";
      }, function () { flash(b, false); });
    });
  }

  // ---- data -------------------------------------------------------------------------------------------
  var DATA = null, BYID = {};
  function loadData() {
    return fetch(document.documentElement.getAttribute("data-api") || "api/v1/index.json")
      .then(function (r) { return r.json(); })
      .then(function (d) { DATA = d; d.entries.forEach(function (e) { BYID[e.id] = e; }); return d; });
  }

  // ---- record rendering (mirrors sheet() in tools/build_site.py) -------------------------------------
  var CLS = { parameter_delta: ["delta", "Parameter delta"], protective_delta: ["protect", "Protective delta"], aligned_baseline: ["", "Aligned baseline"] };
  function badge(c, text, extra) { var k = CLS[c] || CLS.aligned_baseline; return el("span", { "class": ("badge " + (extra || k[0])).trim(), text: text || k[1] }); }
  // Exact compact duration: 0 -> 0s, 1 -> 1s, 86400 -> 1d, 129600 -> 1d 12h (mirrors secs() in tools/build_site.py)
  function secs(s) {
    if (s === null || s === undefined) return "—";
    var parts = []; s = Math.floor(s);
    [["d", 86400], ["h", 3600], ["m", 60], ["s", 1]].forEach(function (u) {
      if (s >= u[1]) { parts.push(Math.floor(s / u[1]) + u[0]); s = s % u[1]; }
    });
    return parts.join(" ") || "0s";
  }
  function copyBtn(v, label) { return el("button", { "class": "copy", type: "button", "data-copy": v, text: label || "Copy" }); }
  function hexref(v, a, b) { return [el("span", { "class": "addr", title: v, text: short(v, a || 6, b || 4) }), copyBtn(v)]; }
  function delayCmp(e) {
    var o = e.observed_delay_seconds, d = e.documented_delay_seconds;
    if ((o === null || o === undefined) && (d === null || d === undefined)) return el("span", { "class": "muted", text: "No timelock delay in this record" });
    var warn = o !== null && o !== undefined && d !== null && d !== undefined && o !== d;
    return el("span", { "class": "cmp" }, [
      el("span", { "class": "chip obs" + (warn ? " warn" : "") }, [el("i", { text: "Observed" }), el("b", { text: secs(o) })]),
      el("span", { "class": "vs", text: "vs" }),
      el("span", { "class": "chip" }, [el("i", { text: "Docs" }), el("b", { text: secs(d) })])]);
  }
  function multisig(text) {
    var seen = []; (text.match(/\b\d+-of-\d+\b/g) || []).forEach(function (x) { if (seen.indexOf(x) < 0) seen.push(x); });
    return seen.length ? seen.join(" · ") : null;
  }
  function proxyAdmin(text) {
    var m = text.match(/ProxyAdmin \((0x[0-9a-fA-F]{40})\)/) || text.match(/admin\(\) = [A-Za-z ]*\((0x[0-9a-fA-F]{40})\)/);
    return m ? m[1] : null;
  }
  // Runnable as-is: full signature + every argument (call_signature / call_args in /api/v1/index.json).
  // A record's chain (index.json records without one are Ethereum Mainnet); the RPC variable is never taken from the feed.
  function chainOf(e) { return e && e.chain === "base" ? "base" : "ethereum"; }
  function castCmd(e) {
    var rpc = '--rpc-url "' + (chainOf(e) === "base" ? "$BASE_RPC_URL" : "$ETH_RPC_URL") + '"';
    var first = e.check_type === "eth_getStorageAt"
      ? "cast storage " + e.target_contract + " \\\n  " + e.selector_or_slot + " \\\n  --block " + e.block_number + " " + rpc
      : "cast call " + e.target_contract + ' \\\n  "' + (e.call_signature || e.selector_or_slot) + '"' +
        (e.call_args && e.call_args.length ? " " + e.call_args.join(" ") : "") + " \\\n  --block " + e.block_number + " " + rpc;
    return first + "\ncast block " + e.block_number + " --field hash " + rpc + "\n# expect " + e.block_hash;
  }
  function term(cmd, title) {
    return el("div", { "class": "term" }, [
      el("div", { "class": "term-h" }, [el("span", { text: title || "Reproduce on any archive node" }),
        el("button", { "class": "copy", type: "button", "data-copy-term": "", text: "Copy command" })]),
      el("pre", { text: cmd })]);
  }
  function proof(e) {
    if (e.base_eas_uid) return el("a", { href: "https://base.easscan.org/attestation/view/" + e.base_eas_uid, target: "_blank", rel: "noopener", text: "Base EAS attestation " + short(e.base_eas_uid, 6, 4) + " ↗" });
    return el("span", { text: "Pending Base EAS batch attestation · pinned by block hash and summary SHA-256" });
  }
  // 32-byte hashes in prose are shortened with the full value in a tooltip (mirrors prose() in build_site.py)
  function prose(text) {
    var out = [], last = 0, re = /0x[0-9a-fA-F]{64}(?![0-9a-fA-F])/g, m;
    while ((m = re.exec(text))) {
      out.push(text.slice(last, m.index));
      out.push(el("span", { "class": "hx", title: m[0], text: short(m[0], 8, 6) }));
      last = m.index + m[0].length;
    }
    out.push(text.slice(last));
    return out;
  }
  function renderSheet(e) {
    var panel = $("#insp-panel"); if (!panel || !e) return;
    var obs = e.onchain_observed || "", ms = multisig(obs), pa = proxyAdmin(obs);
    var repo = "https://github.com/Fractal-Neurons/pacta/blob/main/";
    var rows = [
      ["Category", [e.category]],
      ["Target contract", [e.target_label + " · "].concat(hexref(e.target_contract))],
      ["Timelock delay", [delayCmp(e)]]];
    if (ms) rows.push(["Safe quorum", [el("span", { "class": "mono", text: ms })]]);
    if (pa) rows.push(["EIP-1967 ProxyAdmin", hexref(pa)]);
    rows.push(["Pinned block", [chainOf(e) === "base" ? "Base " : "", el("span", { "class": "num", text: "#" + num(e.block_number) }), " · Sprint " + e.sprint + " ",
      badge(null, "Scanner-pinned (L1 finalized)", "final")]]);
    rows.push(["Canonical block hash", hexref(e.block_hash, 8, 6)]);
    rows.push(["Proof", [proof(e)]]);
    rows.push(["Summary", [el("a", { href: repo + e.summary_doc, target: "_blank", rel: "noopener", text: e.summary_doc.split("/").pop() + " ↗" }), " · SHA-256 "].concat(hexref(e.summary_sha256, 8, 4))]);
    var dl = el("dl", { "class": "kv" });
    rows.forEach(function (r) { dl.appendChild(el("dt", { text: r[0] })); dl.appendChild(el("dd", {}, r[1])); });
    panel.textContent = "";
    panel.appendChild(el("div", { "class": "sheet-h" }, [el("h3", { text: e.protocol }), badge(e.classification)]));
    panel.appendChild(el("p", { "class": "sheet-sub", text: e.surface }));
    panel.appendChild(dl);
    panel.appendChild(el("p", { "class": "obs-text" }, prose(obs)));
    panel.appendChild(term(castCmd(e)));
  }

  // ---- inspector workbench ---------------------------------------------------------------------------
  function initInspector() {
    var list = $("#insp-list"); if (!list) return;
    var q = $("#insp-q"), count = $("#insp-count"), filt = "all";
    var links = $$("a[data-id]", list);
    function select(id, scroll) {
      var e = BYID[id]; if (!e) return false;
      links.forEach(function (a) { a.setAttribute("aria-current", String(a.getAttribute("data-id") === id)); });
      renderSheet(e);
      if (scroll) $("#inspector").scrollIntoView({ behavior: "smooth", block: "start" });
      return true;
    }
    function apply() {
      var t = (q && q.value || "").trim().toLowerCase(), shown = 0;
      links.forEach(function (a) {
        var e = BYID[a.getAttribute("data-id")];
        var hay = e ? JSON.stringify(e).toLowerCase() : a.textContent.toLowerCase();
        var ok = (filt === "all" || a.getAttribute("data-class") === filt) && (!t || hay.indexOf(t) >= 0);
        a.parentNode.hidden = !ok; if (ok) shown++;
      });
      if (count) count.textContent = shown + " of " + links.length + " records";
    }
    list.addEventListener("click", function (ev) {
      var a = ev.target.closest("a[data-id]"); if (!a || !DATA) return;   // without data, the link opens the index drawer
      ev.preventDefault(); select(a.getAttribute("data-id"), false);
    });
    list.addEventListener("keydown", function (ev) {
      if (ev.key !== "ArrowDown" && ev.key !== "ArrowUp") return;
      var vis = links.filter(function (a) { return !a.parentNode.hidden; }), i = vis.indexOf(document.activeElement);
      if (i < 0) return; ev.preventDefault();
      var n = vis[Math.max(0, Math.min(vis.length - 1, i + (ev.key === "ArrowDown" ? 1 : -1)))]; n.focus(); select(n.getAttribute("data-id"), false);
    });
    if (q) q.addEventListener("input", function () {
      apply();
      var first = links.filter(function (a) { return !a.parentNode.hidden; })[0];
      if (first && q.value.trim()) select(first.getAttribute("data-id"), false);
    });
    $$(".bench-filter button").forEach(function (b) {
      b.addEventListener("click", function () {
        filt = b.getAttribute("data-f");
        $$(".bench-filter button").forEach(function (o) { o.setAttribute("aria-pressed", String(o === b)); });
        apply();
      });
    });
    document.addEventListener("click", function (ev) {
      var b = ev.target.closest("[data-inspect]"); if (!b || !DATA) return;
      ev.preventDefault(); select(b.getAttribute("data-inspect"), true);
    });
  }

  // ---- public index: filter + inline drawers ---------------------------------------------------------
  function initIndex() {
    var rows = $$("#matrix tbody tr.rec"); if (!rows.length) return;
    var q = $("#matrix-q"), count = $("#matrix-count"), cls = "all";
    function drawer(r) { return document.getElementById("r-" + r.getAttribute("data-id")); }
    function toggle(r, open) {
      var d = drawer(r); if (!d) return;
      open = open === undefined ? !d.classList.contains("open") : open;
      d.classList.toggle("open", open); r.classList.toggle("open", open);
      var b = $(".inspect-btn", r); if (b) { b.setAttribute("aria-expanded", String(open)); b.textContent = open ? "Close" : "Details"; }
    }
    function apply() {
      var t = (q && q.value || "").trim().toLowerCase(), shown = 0;
      rows.forEach(function (r) {
        var ok = (cls === "all" || r.getAttribute("data-class") === cls) && (!t || r.getAttribute("data-search").indexOf(t) >= 0);
        r.hidden = !ok; if (!ok) toggle(r, false); else shown++;
      });
      if (count) count.textContent = shown + " of " + rows.length + " records shown";
    }
    rows.forEach(function (r) {
      r.addEventListener("click", function (ev) {
        if (ev.target.closest("a:not(.inspect-btn),button")) return;
        ev.preventDefault(); toggle(r);
      });
    });
    if (q) q.addEventListener("input", apply);
    $$("#index .seg button").forEach(function (b) {
      b.addEventListener("click", function () {
        cls = b.getAttribute("data-class");
        $$("#index .seg button").forEach(function (o) { o.setAttribute("aria-pressed", String(o === b)); });
        apply();
      });
    });
    function openFromHash() {
      var m = location.hash.match(/^#r-(.+)$/); if (!m) return;
      var id = m[1];
      try { id = decodeURIComponent(id); } catch (e) { /* keep the raw fragment */ }
      var r = rows.filter(function (x) { return x.getAttribute("data-id") === id; })[0]; if (!r) return;   // no selector parsing
      r.hidden = false; toggle(r, true); r.scrollIntoView({ block: "center" });
    }
    document.addEventListener("click", function (ev) {
      var a = ev.target.closest("a[data-open]"); if (!a) return;
      ev.preventDefault();
      var oid = a.getAttribute("data-open"), r = rows.filter(function (x) { return x.getAttribute("data-id") === oid; })[0]; if (!r) return;
      r.hidden = false; toggle(r, true); r.scrollIntoView({ behavior: "smooth", block: "center" });
    });
    window.addEventListener("hashchange", openFromHash);
    openFromHash();
    apply();
  }

  // ---- request builder: brief + GitHub intake + Gmail compose + copy ---------------------------------
  // Tracks: 24h clearance (default), continuous Aligned maintenance, high-throughput API SLA, free community queue. The
  // public data itself is free for everyone, so nothing here gates access. GitHub dropdown strings must match
  // .github/ISSUE_TEMPLATE/request-scan.yml. Paid tracks settle by Option A (commercial invoice, default) or Option B
  // (direct on-chain USDC to the Pacta treasury, an EOA).
  var REQ_TO = "pacta@dri.network";
  var TRACK = {
    clearance: ["24h Onboarding & Delta Clearance ($5,000 USDC flat)",
                "24h Onboarding & Delta Clearance ($5,000 USDC flat)",
                "Pacta 24h clearance request", "$5,000 USDC flat"],
    continuous: ["Continuous Aligned Maintenance ($1,500 USDC per month)",
                 "Continuous Aligned Maintenance ($1,500 USDC per month)",
                 "Pacta continuous Aligned maintenance request", "$1,500 USDC per month"],
    api_sla: ["Enterprise / High-Throughput API SLA (priced on scope)",
              "Enterprise / High-Throughput API SLA (priced on scope)",
              "Pacta enterprise API SLA request", "the scoped amount (quoted on the invoice)"],
    community: ["Community queue (free; unscheduled, typically 6–8 weeks)", "Community queue (free; unscheduled, typically 6–8 weeks)",
                "Pacta community queue request", ""]
  };
  var SETTLE = {
    invoice: ["Option A — formal commercial invoice (PDF) & counterparty settlement (no upfront transfer; invoice on scope confirmation)",
              "Option A: formal commercial invoice (PDF) and counterparty settlement"],
    direct: ["Option B — direct on-chain USDC settlement", "Option B: direct on-chain USDC settlement"]
  };
  var TX_RE = /^0x[0-9a-fA-F]{64}$/;
  function own(o, k) { return typeof k === "string" && Object.prototype.hasOwnProperty.call(o, k); }
  // ---- URL prefill (/request/?tier=…&protocol=…&forum=…&settlement=…, also /?…#request): closed enums and sanitised
  //      text only, written with .value / .checked, never as markup. PREFILL-BEGIN
  var BAD_CHARS = /[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u2028-\u202e\u2060-\u2069\ufeff]/g;
  function cleanText(v, max) { return String(v || "").replace(BAD_CHARS, "").replace(/\s+/g, " ").trim().slice(0, max); }
  function cleanForum(v) {
    var s = String(v || "").trim(), u;
    if (!s || s.length > 300 || /[\u0000-\u0020\u007f-\u009f\u200b-\u200f\u2028-\u202e\u2060-\u2069\ufeff]/.test(s)) return "";
    try { u = new URL(s); } catch (e) { return ""; }
    return u.protocol === "https:" && !u.username && !u.password && u.hostname ? s : "";
  }
  function readPrefill(search) {
    var q, out = {};
    try { q = new URLSearchParams(search || ""); } catch (e) { return out; }
    var t = q.get("tier"), st = q.get("settlement"), p = cleanText(q.get("protocol"), 80), f = cleanForum(q.get("forum"));
    if (own(TRACK, t)) out.tier = t;
    if (own(SETTLE, st)) out.settlement = st;
    if (p) out.protocol = p;
    if (f) out.forum = f;
    return out;
  }
  // PREFILL-END
  function initRequest() {
    var form = $("#req-form"); if (!form) return;
    form.addEventListener("submit", function (e) { e.preventDefault(); });   // the brief is built client-side; never navigate (no inline onsubmit: CSP-safe)
    var out = $("#req-brief"), gh = $("#req-gh"), gm = $("#req-gmail"), st = $("#req-status"), pay = $("#req-pay");
    var txField = $("#req-tx-field"), txHint = $("#req-tx-hint"), txIn = $("#req-tx"), sum = $("#req-pay-sum"), direct = $("#req-direct");
    var treasury = form.getAttribute("data-treasury") || "";
    function val(n) { var x = form.elements[n]; return x ? String(x.value || "").trim() : ""; }
    function tier() { var x = $('input[name="tier"]:checked', form); return x && own(TRACK, x.value) ? x.value : "clearance"; }
    function settlement() { var x = $('input[name="settlement"]:checked', form); return x && own(SETTLE, x.value) ? x.value : "invoice"; }
    function protocols() { return $$('input[name="protocol"]:checked', form).map(function (x) { return x.value; }); }
    function update() {
      var t = tier(), paid = t !== "community", s = settlement(), dir = paid && s === "direct";
      var ps = protocols(), org = val("org"), scope = val("scope"), contact = val("contact");
      var forum = val("forum"), tx = dir ? val("tx") : "", txOk = !tx || TX_RE.test(tx);
      var subj = TRACK[t][2] + (org ? " — " + org : "");
      var lines = ["To: " + REQ_TO, "Subject: " + subj, "",
        "Track: " + TRACK[t][0],
        "Organization: " + (org || "(not given)"),
        "Protocols in scope: " + (ps.length ? ps.join(", ") : "(none selected)")];
      if (scope) lines.push("Contracts / docs / portfolio:", scope);
      if (forum) lines.push("Forum proposal: " + forum);
      if (paid) {
        lines.push("Settlement: " + SETTLE[s][0]);
        if (dir) {
          lines.push("Payment: " + (tx ? tx + (txOk ? "" : "  (check: not a 0x-prefixed 32-byte transaction hash)")
                                       : "not yet sent; please confirm scope first") + " — " + TRACK[t][3] +
                     " in USDC to the Pacta treasury (direct settlement EOA) " + treasury + " on Base or Ethereum");
        }
      }
      lines.push("Contact: " + (contact || "(not given)"));
      lines.push("", "Sent from " + location.href.split("#")[0]);
      out.textContent = lines.join("\n");
      if (pay) pay.hidden = !paid;
      if (sum) sum.textContent = paid ? TRACK[t][0].replace(/ \((.*)\)$/, " · $1") : "";
      if (direct) direct.hidden = !dir;
      if (txField) txField.hidden = !dir;
      if (txIn) { if (txOk) txIn.removeAttribute("aria-invalid"); else txIn.setAttribute("aria-invalid", "true"); }
      if (txHint) txHint.textContent = txOk ? "A 66-character hash starting with 0x." : "That does not look like a transaction hash (0x + 64 hex characters).";
      var title = "[Pacta Scope] " + (org || (ps.length ? ps.slice(0, 3).join(", ") : TRACK[t][2].replace(/^Pacta | request$/g, "")));
      var p = new URLSearchParams({ template: "request-scan.yml", title: title });
      p.set("repo_or_portfolio_url", forum || scope.split(/\s+/).filter(function (w) { return /^https?:\/\//.test(w); })[0] || "");
      p.set("commitments_and_addresses", ["Protocols: " + (ps.join(", ") || "-"), scope].filter(Boolean).join("\n"));
      p.set("package_tier", TRACK[t][1]);
      if (paid) p.set("settlement_preference", SETTLE[s][1]);
      if (forum) p.set("forum_proposal_url", forum);
      if (dir && tx && txOk) p.set("payment_tx_hash", tx);
      p.set("contact_channel", contact);
      gh.href = "https://github.com/Fractal-Neurons/pacta/issues/new?" + p.toString();
      gm.href = "https://mail.google.com/mail/?view=cm&fs=1&to=" + encodeURIComponent(REQ_TO) + "&su=" + encodeURIComponent(subj) +
        "&body=" + encodeURIComponent(lines.slice(3).join("\n"));
      if (st) st.textContent = "";
    }
    function pick(name, v) {
      var r = $$('input[name="' + name + '"]', form).filter(function (x) { return x.value === v; })[0];
      if (r) r.checked = true;
      return !!r;
    }
    function preselect(t) { if (pick("tier", t)) update(); }
    function prefill(o) {
      if (o.tier) pick("tier", o.tier);
      if (o.settlement) pick("settlement", o.settlement);
      if (o.protocol) {
        var low = o.protocol.toLowerCase(), orgIn = form.elements.org;
        var box = $$('input[name="protocol"]', form).filter(function (x) {
          return x.getAttribute("data-slug") === o.protocol || String(x.value).toLowerCase() === low;
        })[0];
        if (box) box.checked = true;
        if (orgIn && !String(orgIn.value || "").trim()) orgIn.value = box ? box.value : o.protocol;
      }
      if (o.forum && form.elements.forum) form.elements.forum.value = o.forum;
    }
    form.addEventListener("input", update);
    form.addEventListener("change", update);
    gh.addEventListener("click", function () { if (st) st.textContent = "Opened in a new tab. If nothing appeared, use Copy brief."; });
    gm.addEventListener("click", function () { if (st) st.textContent = "Opened in a new tab. If nothing appeared, use Copy brief."; });
    document.addEventListener("click", function (ev) {
      var a = ev.target.closest("a[data-tier]"); if (!a) return;
      if ((a.getAttribute("href") || "").charAt(0) === "#") { preselect(a.getAttribute("data-tier")); }
    });
    prefill(readPrefill(location.search));
    update();
  }

  // ---- live pre-flight checker (free API; runs only on an explicit submit / preset click) ---------------
  var ADDR_RE = /^0x[0-9a-fA-F]{40}$/;
  var SLOT_IMPL = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc";
  var SLOT_BEACON = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50";
  var SLOT_PROXIABLE = "0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7";
  var VERDICT_CLASS = { IMMUTABLE_NO_ADMIN: "", TIMELOCK_PROTECTED: "protect", ZERO_DELAY_TIMELOCK_RISK: "delta", MULTISIG_NO_TIMELOCK: "delta",
    INSTANT_EOA_ADMIN_RISK: "delta", UNCLASSIFIED_CONTRACT_CONTROLLER: "delta", UNDEPLOYED_OR_EOA: "" };
  function pfCasts(r) {
    var rpc = r.chain === "base" ? "$BASE_RPC_URL" : "$ETH_RPC_URL", b = " --block " + r.pinnedBlock + " --rpc-url " + rpc, c = [];
    c.push("cast code " + r.address + b);
    c.push("cast storage " + r.address + " " + (r.proxyType === "eip1822" ? SLOT_PROXIABLE : r.proxyType === "eip1967_beacon" ? SLOT_BEACON : SLOT_IMPL) + b);
    if (r.proxyType === "eip1967_beacon" && ADDR_RE.test(String(r.beacon || ""))) {
      c.push("cast call " + r.beacon + ' "implementation()(address)"' + b);
      c.push("cast call " + r.beacon + ' "owner()(address)"' + b);
    }
    c.push("cast call " + r.address + ' "owner()(address)"' + b);
    var k = r.controller || {};
    if (k.address && k.kind === "multisig_safe") c.push("cast call " + k.address + ' "getThreshold()(uint256)"' + b);
    if (k.address && k.kind === "timelock") c.push("cast call " + k.address + ' "getMinDelay()(uint256)"' + b);
    return c;
  }
  function pfRow(k, v) { return el("div", {}, [el("dt", { text: k }), el("dd", {}, [v])]); }
  function pfAddr(v) { return ADDR_RE.test(String(v || "")) ? el("span", {}, hexref(v, 8, 6)) : "none"; }
  function pfRender(out, r) {
    out.textContent = "";
    var caps = r.capabilities || {}, k = r.controller || {};
    var capList = Object.keys(caps).filter(function (x) { return caps[x] === true; });
    var risk = typeof r.riskScore === "number" ? String(r.riskScore) + "/100" : "n/a";
    var ctl = String(k.kind || "none");
    if (typeof k.safeThreshold === "number") ctl += " (" + k.safeThreshold + "-of-" + (typeof k.safeOwnerCount === "number" ? k.safeOwnerCount : "?") + ")";
    if (typeof k.timelockDelaySec === "number") ctl += " (" + secs(k.timelockDelaySec) + " delay)";
    if (typeof k.roleAdminCount === "number") ctl += " (" + k.roleAdminCount + " DEFAULT_ADMIN_ROLE members)";
    out.appendChild(el("p", { "class": "pf-verdict" }, [badge(null, String(r.verdict), VERDICT_CLASS[r.verdict] || "delta"), " Risk " + risk]));
    out.appendChild(el("p", { text: String(r.summary || "") }));
    out.appendChild(el("dl", { "class": "pf-dl" }, [
      pfRow("Chain / block", String(r.chain) + " · block " + num(r.pinnedBlock)),
      pfRow("Contract", pfAddr(r.address)),
      pfRow("Proxy", r.isProxy ? "yes" : "no"),
      pfRow("Implementation", pfAddr(r.implementation)),
      pfRow("Controller", ADDR_RE.test(String(k.address || "")) ? el("span", {}, [ctl + " ", pfAddr(k.address)]) : ctl),
      pfRow("Zero-delay upgrade", r.canUpgradeZeroDelay === true ? "yes" : r.canUpgradeZeroDelay === false ? "no" : "unknown"),
      pfRow("Capabilities", capList.length ? capList.join(", ") : "none seen"),
      pfRow("Paused", r.paused === true ? "yes" : r.paused === false ? "no" : "n/a")]));
    if (r.isContract !== false && ADDR_RE.test(String(r.address)) && /^\d+$/.test(String(r.pinnedBlock)))
      out.appendChild(term(pfCasts(r).join("\n"), "Verify it yourself (Foundry cast, pinned block)"));
  }
  function initPreflight() {
    var box = $(".pf"), form = $("#pf-form"), out = $("#pf-out");
    if (!box || !form || !out) return;
    var api = box.getAttribute("data-api") || "", chainSel = $('select[name="chain"]', form), addr = $('input[name="address"]', form);
    if (!chainSel || !addr || !/^https:\/\//.test(api)) return;
    var seq = 0, ctl = null;
    function msg(t) { out.textContent = ""; out.appendChild(el("p", { "class": "note", text: t })); }
    function run() {
      // Every submit (valid or not) supersedes the previous one: bump seq and abort any in-flight request BEFORE the
      // input checks, so a stale response can never overwrite a later validation message.
      var my = ++seq;
      if (ctl) { try { ctl.abort(); } catch (e) { /* already settled */ } ctl = null; }
      var a = String(addr.value || "").trim(), ch = chainSel.value === "base" ? "base" : "ethereum";
      if (!ADDR_RE.test(a)) { msg("Enter a 0x-prefixed, 40-hex-character contract address."); return; }
      if (typeof fetch !== "function") { msg("This browser cannot call the API; use the curl command above."); return; }
      // First-party beacon hook (docs/b.js); optional: the checker works the same without it.
      if (typeof window.pactaBeacon === "function") { try { window.pactaBeacon("live_checker_submit", ch + ":" + a.toLowerCase()); } catch (e) { /* ignore */ } }
      var opts = { headers: { Accept: "application/json" } };
      if (typeof AbortController === "function") { ctl = new AbortController(); opts.signal = ctl.signal; }
      msg("Checking " + short(a, 6, 4) + " on " + ch + " at the latest block…");
      // optional free-tier attribution (non-personal): the browser demo names itself; no location, no personal data
      fetch(api + "/v1/check/preflight?chain=" + ch + "&address=" + a + "&caller_agent=pacta-wtf-checker&requester_role=individual_user&caller_purpose=general_research", opts)
        .then(function (res) { return res.json().then(function (b) { return { status: res.status, body: b }; }); })
        .then(function (x) {
          if (my !== seq) return;
          var b = x.body || {}, r = b.verdict ? b : (b.result && b.result.verdict ? b.result : null);
          if (x.status === 200 && r) pfRender(out, r);
          else msg("The API answered HTTP " + x.status + (b.error ? " (" + String(b.error) + ")" : "") + (b.detail ? ": " + String(b.detail) : "."));
        })
        .catch(function () { if (my === seq) msg("Could not reach the API. Try again, or use the curl command above."); });
    }
    form.addEventListener("submit", function (ev) { ev.preventDefault(); run(); });
    $$("[data-pf-address]").forEach(function (b) {
      b.addEventListener("click", function () {
        chainSel.value = b.getAttribute("data-pf-chain") === "base" ? "base" : "ethereum";
        addr.value = b.getAttribute("data-pf-address") || "";
        run();
      });
    });
  }

  // /protocols/: text search + one status / chain pill. Rows are only shown or hidden (hidden attribute); text via textContent.
  function initProtocolFilter() {
    var root = $("[data-pfilter-root]"), q = $("#proto-q"), count = $("#proto-count");
    if (!root || !q) return;
    var rows = $$("#proto-table tbody tr"), pills = $$("[data-pfilter]", root), active = "all";
    function match(tr) {
      var t = tr.getAttribute("data-ptier"), ch = (tr.getAttribute("data-pchains") || "").split(" ");
      if (active === "ethereum" || active === "base") return ch.indexOf(active) >= 0;
      return active === "all" || t === active;
    }
    function apply() {
      var words = q.value.toLowerCase().split(" ").filter(Boolean), shown = 0;
      rows.forEach(function (tr) {
        var hay = tr.getAttribute("data-psearch") || "";
        var ok = match(tr) && words.every(function (w) { return hay.indexOf(w) >= 0; });
        tr.hidden = !ok;
        if (ok) shown++;
      });
      if (count) count.textContent = shown + " of " + rows.length + " protocols shown";
    }
    pills.forEach(function (b) {
      b.addEventListener("click", function () {
        active = b.getAttribute("data-pfilter") || "all";
        pills.forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        apply();
      });
    });
    q.addEventListener("input", apply);
    apply();
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTheme(); initCopy(); initBeaconHooks(); tick(); setInterval(tick, 30000);
    initIndex(); initRequest(); initInspector(); initPreflight(); initLiveTimelocks(); initProtocolFilter();
    if ($("#insp-list")) loadData().catch(function () { /* static sheet and drawer links keep working */ });
  });
})();
