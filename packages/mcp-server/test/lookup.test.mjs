// pacta_lookup_protocol (stdio): embedded catalog, caller fields, gateway-first with a clean fallback, and (where the site
// feeds are present, i.e. in pacta-github-repo) exact parity of the catalog with docs/api/v1/*.json.
import "./no-network.mjs";
import test from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { PactaMcpServer, TOOL_DEFINITIONS, LOOKUP_TOOL, MCP_INSTRUCTIONS, LOOKUP_CATALOG, LOOKUP_TOTALS, lookupProtocols, toChecksumAddress } from "../src/server.mjs";
import { LOOKUP_LIMITS } from "../src/lookup.mjs";
import { CALLER } from "./helpers.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const DOCS = join(HERE, "..", "..", "..", "docs", "api", "v1");
const GW = "https://gateway.example.test";
// PUBLISHED-COUNTS (the one line a Sprint stamp rewrites; equals pacta-github-repo verify_site_v2.EXPECT)
const PUBLISHED = Object.freeze({ protocols: 54, briefs: 8, easAttestedProtocols: 34, rpcObservedProtocols: 20 });
const rec = (reply) => {
  const calls = [];
  const f = async (url) => { calls.push(String(url)); return reply(String(url)); };
  f.calls = calls;
  return f;
};
const call = (srv, args, id = 1) => srv.handleMessage({ jsonrpc: "2.0", id, method: "tools/call", params: { name: "pacta_lookup_protocol", arguments: args } });
const body = (r) => JSON.parse(r.result.content[0].text);

test("pacta_lookup_protocol is listed first in both modes, query optional, caller fields required; initialize names it", async () => {
  assert.equal(TOOL_DEFINITIONS[0], LOOKUP_TOOL);
  assert.deepEqual(LOOKUP_TOOL.inputSchema.required, ["caller_agent", "requester_role", "caller_purpose"]);
  assert.deepEqual(LOOKUP_TOOL.annotations, { title: "Lookup Protocol or Token by Name", readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false });
  const local = new PactaMcpServer({ fetchImpl: rec(() => { throw new Error("no network"); }) });
  const gw = new PactaMcpServer({ x402Url: GW, fetchImpl: rec(() => { throw new Error("no network"); }) });
  for (const srv of [local, gw]) {
    const list = await srv.handleMessage({ jsonrpc: "2.0", id: 1, method: "tools/list" });
    assert.equal(list.result.tools[0].name, "pacta_lookup_protocol");
  }
  const init = await local.handleMessage({ jsonrpc: "2.0", id: 2, method: "initialize" });
  assert.equal(init.result.instructions, MCP_INSTRUCTIONS);
  assert.match(MCP_INSTRUCTIONS, /call pacta_lookup_protocol first/);
});

test("pacta_lookup_protocol: -32602 without valid caller fields (JWT, e-mail); invalid input is a tool error; nothing is sent", async () => {
  const f = rec(() => { throw new Error("must not be called"); });
  const srv = new PactaMcpServer({ x402Url: GW, fetchImpl: f });
  const none = await call(srv, { query: "ethena" });
  assert.equal(none.error.code, -32602);
  assert.match(none.error.message, /caller_agent \(missing\)/);
  const jwt = "ey" + "JhbGciOiJIUzI1NiJ9.e30.sig";
  for (const a of [jwt, jwt.toLowerCase(), "alice@example.com"]) {
    const r = await call(srv, { ...CALLER, caller_agent: a, query: "ethena" });
    assert.equal(r.error?.code, -32602, a);
  }
  for (const args of [{ query: "x".repeat(81) }, { chain: "polygon" }, { kind: "token" }, { limit: 0 }, { limit: LOOKUP_CATALOG.length + 1 }, { address: "0x1" }, { query: 7 }]) {
    const r = await call(srv, { ...CALLER, ...args });
    assert.equal(r.result.isError, true, JSON.stringify(args));
    assert.equal(body(r).code, "invalid_input", JSON.stringify(args));
  }
  assert.equal(f.calls.length, 0);
});

test("pacta_lookup_protocol without PACTA_X402_URL: answered from the embedded catalog, no network", async () => {
  const f = rec(() => { throw new Error("no network"); });
  const srv = new PactaMcpServer({ fetchImpl: f });
  const r = body(await call(srv, { ...CALLER, query: "USDe" }));
  assert.deepEqual([r.source, r.schema, r.results[0].slug, r.results[0].match, r.results[0].preflightArgs.chain], ["embedded_catalog", "pacta.protocol_lookup.v1", "ethena-usde-susde", "exact", "ethereum"]);
  assert.equal(r.gatewayFallback, undefined);
  const all = body(await call(srv, { ...CALLER }));
  assert.deepEqual([all.count, all.totalCatalog], [20, { ...PUBLISHED }]);
  const mw = body(await call(srv, { ...CALLER, query: "moonwell" })).results[0];
  assert.deepEqual([mw.evidenceBasis, mw.easAttested, mw.documentationComparison, mw.classification], ["rpc_observed", false, "not_assessed", "rpc_observed"]);
  assert.equal(f.calls.length, 0);
});

test("pacta_lookup_protocol with PACTA_X402_URL: asks GET /v1/protocols/lookup (caller fields forwarded) and falls back to the embedded catalog", async () => {
  const gwAnswer = { ...lookupProtocols({ query: "aave" }) };
  let f = rec(() => new Response(JSON.stringify(gwAnswer), { status: 200, headers: { "Content-Type": "application/json" } }));
  let srv = new PactaMcpServer({ x402Url: GW, fetchImpl: f });
  let r = body(await call(srv, { ...CALLER, query: " Aave ", chain: "eip155:1" }));
  assert.equal(r.source, "gateway");
  assert.equal(f.calls.length, 1);
  const u = new URL(f.calls[0]);
  assert.equal(u.origin + u.pathname, GW + "/v1/protocols/lookup");
  assert.deepEqual(Object.fromEntries(u.searchParams), { q: "Aave", chain: "ethereum", limit: "10", ...CALLER });
  for (const [name, reply] of [["http 502", () => new Response("bad gateway", { status: 502 })], ["not lookup json", () => new Response("{}", { status: 200 })],
    ["transport", () => { throw new Error("reset"); }]]) {
    f = rec(reply);
    srv = new PactaMcpServer({ x402Url: GW, fetchImpl: f });
    r = body(await call(srv, { ...CALLER, query: "kusd" }));
    assert.deepEqual([r.source, r.results[0].slug, typeof r.gatewayFallback], ["embedded_catalog", "kerne-kusd-base", "string"], name);
  }
});

test("catalog invariants: PUBLISHED protocols + briefs, maxLimit = catalog size, checksummed addresses, preflightArgs, scoped evidence basis", () => {
  assert.deepEqual(LOOKUP_TOTALS, { ...PUBLISHED, items: PUBLISHED.protocols + PUBLISHED.briefs });
  assert.equal(LOOKUP_LIMITS.maxLimit, LOOKUP_CATALOG.length);
  for (const x of LOOKUP_CATALOG) {
    assert.equal(toChecksumAddress(x.primaryContract), x.primaryContract, x.slug);
    assert.deepEqual(x.preflightArgs, { chain: x.chain, address: x.primaryContract }, x.slug);
    if (x.evidenceBasis === "rpc_observed") assert.deepEqual([x.classification, x.easAttested, x.documentationComparison], ["rpc_observed", false, "not_assessed"], x.slug);
    assert.ok(!(x.easAttested === false && ["aligned_baseline", "parameter_delta", "protective_delta", "mixed"].includes(x.classification)), x.slug);
  }
});

test("catalog parity with docs/api/v1 (index.json, rpc-pinned.json, onboarding.json, radar.json, lookup.json)", { skip: !existsSync(join(DOCS, "index.json")) && "site feeds live in pacta-github-repo" }, () => {
  const rd = (n) => JSON.parse(readFileSync(join(DOCS, n), "utf8"));
  const idx = rd("index.json"), pin = rd("rpc-pinned.json"), onb = rd("onboarding.json"), radar = rd("radar.json"), lk = rd("lookup.json");
  assert.deepEqual(lk.items, JSON.parse(JSON.stringify(LOOKUP_CATALOG)), "docs/api/v1/lookup.json == src/lookup.mjs");
  const bySlug = Object.fromEntries(LOOKUP_CATALOG.map((x) => [x.slug, x]));
  // every RPC-pinned record: slug, target, controller, chain, rpc_observed / not EAS-attested
  for (const e of pin.entries) {
    const x = bySlug[e.slug];
    assert.ok(x, e.slug);
    assert.deepEqual([x.primaryContract, x.controllerAddress, x.chain, x.classification, x.easAttested], [e.target_contract, e.controller_address, e.chain, "rpc_observed", false], e.slug);
  }
  // every index.json record belongs to exactly one EAS-attested protocol item with its UID and classification
  const surf = new Map();
  for (const x of LOOKUP_CATALOG.filter((i) => i.easAttested)) for (const s of x.surfaces) surf.set(s.id, { x, s });
  assert.equal(surf.size, idx.entries.length);
  for (const e of idx.entries) {
    const { x, s } = surf.get(e.id);
    assert.deepEqual([s.classification, s.targetContract, x.baseEasUids.includes(e.base_eas_uid)], [e.classification, e.target_contract, true], e.id);
  }
  assert.equal(new Set([...surf.values()].map((v) => v.x.slug)).size, PUBLISHED.easAttestedProtocols);
  const briefs = LOOKUP_CATALOG.filter((x) => x.kind === "brief").map((x) => x.slug).sort();
  assert.deepEqual(briefs, [...onb.briefs.map((b) => b.slug), ...radar.items.map((i) => i.brief.replace(/\/$/, "").split("/").pop())].sort());
});
