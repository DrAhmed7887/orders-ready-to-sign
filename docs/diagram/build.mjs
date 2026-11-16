// Builds the workflow diagram from one description of the pipeline.
//   node docs/diagram/build.mjs
// Writes docs/workflow.svg (1600×900), docs/workflow_4x5.svg (1080×1350) and their PNGs.
// Text is wrapped by measuring it in the browser, so the SVGs carry explicit lines and need no script.
// Every box names a real file or rule. Each step is traced twice: Amparo (synthetic, with notes) and a real
// NHANES participant run through the unchanged engine. Real-data numbers are read from eval/results/*.json,
// never typed; a step that real data cannot exercise says so, and the build fails if that stops being true.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const load = (p) => JSON.parse(readFileSync(join(ROOT, p), "utf8"));
const nh = load("eval/results/nhanes.json");
const tr = load("eval/results/nhanes_trace.json");
const pick = (obj, prefix) => {
  const key = Object.keys(obj).find((k) => k.startsWith(prefix));
  if (!key) throw new Error(`eval/results/nhanes.json: no key starting with "${prefix}"`);
  return obj[key];
};
const hidden = pick(nh.primary["per_1000_adults_with_diabetes_or_hypertension"], "albuminuria_behind");
const confirmed = pick(nh.secondary, "repeat_orders_confirmed");
const per1000 = Math.round(hidden.per_1000);
const pct = (confirmed.per_1000 / 10).toFixed(1);
const ci = `${Math.round(confirmed.ci95_lo / 10)}–${Math.round(confirmed.ci95_hi / 10)}`;

// What real data can and cannot exercise, checked against the engine's own output.
const st = tr.steps_on_real_data;
const firedReal = Object.entries(st["2_rules_fired"]).filter(([, n]) => n > 0).map(([k]) => k);
if (firedReal.join() !== "S1b") throw new Error(`diagram says only S1b runs on real data; fired: ${firedReal}`);
if (st["4_S1c"] !== 0 || st.orders_with_note_text !== 0 || st["4_rows_removed_from_list_any_reason"] !== 0 ||
    Object.values(st.extract_rows).some((n) => n !== 0))
  throw new Error("diagram says notes, S1c and suppression are untested on real data; the trace says otherwise");
const R = tr.trace.egfr_60_or_more;
if (R.egfr < 60 || R.engine_rule !== "S1b") throw new Error("traced participant no longer matches the diagram's case");
const who = `${R.sex === "female" ? "Woman" : "Man"}, ${R.age_band.split("-")[0]}s`;
const NB = " ";

const SPEC = {
  title: "From a nightly extract to an order the doctor signs",
  subtitle: "Every box is a real file or rule. Traced twice: Amparo (synthetic, with notes) and a real NHANES 2009–2010 participant (no notes).",
  subtitleShort: "Traced with Amparo (synthetic) and a real NHANES participant.",
  labels: { syn: "Amparo · synthetic", real: "Real · NHANES" },
  steps: [
    { title: "Extract", tool: "ejecutar.py",
      body: "Loads the list: insert-only, every date checked.", short: "Insert-only load; every date checked.",
      syn: "eGFR 72 → 68 · ACR 85 in January",
      real: `${who} · eGFR ${R.egfr} · ACR ${R.acr_first_mg_g} (median of ${R.group_size} like her)` },
    { title: "Signed rules", tool: "S1a · S1b · S3",
      body: "SQL; thresholds in one table, signed by a physician.", short: "SQL; thresholds signed by a physician.",
      syn: "Not repeated for 10 months → S1b",
      real: "ACR ≥ 30 on one visit → S1b, repeat ACR" },
    { title: "Note reader", tool: "Qwen3-4B → verificar.py",
      body: "The model points to a sentence; the code checks it and reads the value and date.", short: "Model points to a sentence; code checks it.",
      syn: `“sentence${NB}2” → ACR${NB}110, 12${NB}Sep${NB}✓`,
      real: null, untested: "Not tested: NHANES has no notes" },
    { title: "Final rules", tool: "S1c",
      body: "Two high ACRs ≥ 3 months apart → S1c. Already ordered → not listed.", short: "Two high ACRs ≥ 3 months apart; then suppression.",
      syn: "85 → 110, 8 months apart → S1c",
      real: null, untested: "Not tested: no notes or orders in NHANES" },
    { title: "Doctor signs", tool: "ui/index.html", human: true,
      body: "Reason, numbers, dates. Sign, or dismiss with a reason.", short: "Sign, or dismiss with a reason.",
      syn: "10:20 · consider a CKD code (N18)",
      real: `Prepared, not signed. 10 days later: ACR${NB}${R.acr_second_mg_g} (${R.second_sample_confirms ? "≥" : "<"}${NB}30)` },
  ],
  evalLead: "Across NHANES:",
  evalText: `${per1000} per 1,000 adults with diabetes or hypertension have urine albumin ≥ 30 mg/g behind an eGFR ≥ 60 (2021–2023). ${pct} % (95 % CI ${ci}) of repeat-ACR orders were ≥ 30 again on a second urine within 10 days (2009–2010).`,
  evalShort: `${per1000} per 1,000 adults with diabetes or hypertension have albumin behind an eGFR ≥ 60 (2021–2023).`,
};

const C = { bg: "#f5f6f8", panel: "#ffffff", ink: "#0e1726", ink2: "#344054", muted: "#5d6779", line: "#e4e7ec",
  accent: "#0b6b61", accentInk: "#ffffff", accentSoft: "#e6f2f0", accentDeep: "#095a52", hush: "#8a94a6" };
const SANS = "Inter, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
const MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";

// Runs in the page: measures, wraps, lays out, returns the SVG markup and any overflow problems.
function layout({ spec, C, SANS, MONO, mode }) {
  const NS = "http://www.w3.org/2000/svg";
  const W = mode === "wide" ? 1600 : 1080, H = mode === "wide" ? 900 : 1350;
  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("xmlns", NS);
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("width", W); svg.setAttribute("height", H);
  svg.setAttribute("role", "img");
  document.body.appendChild(svg);
  const problems = [];
  const el = (name, attrs, parent = svg) => {
    const e = document.createElementNS(NS, name);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    parent.appendChild(e); return e;
  };
  const SLACK = 0.92; // room for a viewer whose fallback font is wider
  const measure = (s, size, weight, family) => {
    const t = el("text", { "font-size": size, "font-weight": weight, "font-family": family });
    t.textContent = s; const w = t.getComputedTextLength(); t.remove(); return w;
  };
  const wrap = (s, width, size, weight = 400, family = SANS) => {
    const words = s.split(" "), lines = []; let cur = "";
    for (const w of words) {
      const next = cur ? cur + " " + w : w;
      if (measure(next, size, weight, family) <= width * SLACK || !cur) cur = next; else { lines.push(cur); cur = w; }
    }
    if (cur) lines.push(cur);
    for (const l of lines) if (measure(l, size, weight, family) > width) problems.push(`too wide: "${l}"`);
    return lines;
  };
  const lh = (size) => Math.round(size * 1.3);
  const text = (lines, x, y, size, opts = {}) => {
    const t = el("text", { x, y, "font-size": size, "font-weight": opts.weight ?? 400, "font-family": opts.family ?? SANS,
      fill: opts.fill ?? C.ink, ...(opts.italic ? { "font-style": "italic" } : {}), ...(opts.anchor ? { "text-anchor": opts.anchor } : {}) });
    lines.forEach((l, i) => { const s = el("tspan", { x, dy: i ? lh(size) : 0 }, t); s.textContent = l; });
    return y + lh(size) * (lines.length - 1);
  };
  const realText = (s) => s.real ?? s.untested;

  el("title", {}).textContent = spec.title;
  el("desc", {}).textContent = spec.steps.map((s, i) =>
    `${i + 1}. ${s.title} (${s.tool}): ${s.body} ${spec.labels.syn}: ${s.syn}. ${spec.labels.real}: ${realText(s)}.`).join(" ") +
    ` ${spec.evalLead} ${spec.evalText}`;
  el("rect", { x: 0, y: 0, width: W, height: H, fill: C.bg });

  const M = mode === "wide" ? 40 : 44;
  const S = mode === "wide" ? { h1: 42, sub: 24, title: 26, tool: 24, body: 24, trace: 24, label: 24, eval: 24, badge: 26 }
                            : { h1: 44, sub: 28, title: 32, tool: 28, body: 28, trace: 28, label: 28, eval: 28, badge: 30 };
  let y = M + S.h1;
  y = text(wrap(spec.title, W - 2 * M, S.h1, 700), M, y, S.h1, { weight: 700 });
  y += lh(S.sub) + 4;
  y = text(wrap(mode === "wide" ? spec.subtitle : spec.subtitleShort, W - 2 * M, S.sub), M, y, S.sub, { fill: C.muted });
  const top = y + 26;

  const evalLines = wrap(spec.evalLead + " " + (mode === "wide" ? spec.evalText : spec.evalShort), W - 2 * M - 48, S.eval);
  const evalH = 28 + lh(S.eval) * evalLines.length;
  const evalTop = H - M - evalH;

  const steps = spec.steps;
  if (mode === "wide") {
    const gap = 30, cw = (W - 2 * M - gap * (steps.length - 1)) / steps.length, pad = 18, iw = cw - 2 * pad;
    const cards = steps.map((s) => ({
      s, tool: wrap(s.tool, iw, S.tool, 500, MONO), body: wrap(s.body, iw, S.body),
      syn: wrap(s.syn, iw, S.trace, 600), real: wrap(realText(s), iw, S.trace, s.real ? 600 : 400),
    }));
    const headH = Math.max(...cards.map((c) => 48 + 12 + lh(S.tool) * c.tool.length + 6 + lh(S.body) * c.body.length));
    const synH = Math.max(...cards.map((c) => lh(S.trace) * c.syn.length));
    const realH = Math.max(...cards.map((c) => lh(S.trace) * c.real.length));
    const sec = (n) => 20 + lh(S.label) + n;
    const ch = headH + sec(synH) + sec(realH) + 18;
    const avail = evalTop - 22 - top;
    if (ch > avail) problems.push(`cards ${Math.round(ch)} px tall, room ${Math.round(avail)}`);
    const cy = top + Math.max(0, (avail - ch) / 2);
    cards.forEach((c, i) => {
      const x = M + i * (cw + gap), hu = !!c.s.human;
      const fg = hu ? C.accentInk : C.ink, fg2 = hu ? C.accentInk : C.ink2, lab = hu ? C.accentSoft : C.muted;
      el("rect", { x, y: cy, width: cw, height: ch, rx: 16, fill: hu ? C.accent : C.panel, stroke: hu ? C.accent : C.line, "stroke-width": 2 });
      el("circle", { cx: x + pad + 18, cy: cy + 34, r: 18, fill: hu ? C.accentInk : C.accent });
      text([String(i + 1)], x + pad + 18, cy + 34 + S.badge * 0.35, S.badge, { weight: 700, fill: hu ? C.accent : C.accentInk, anchor: "middle" });
      text([c.s.title], x + pad + 46, cy + 34 + S.title * 0.35, S.title, { weight: 700, fill: fg });
      if (measure(c.s.title, S.title, 700, SANS) > iw - 46) problems.push(`title too wide: ${c.s.title}`);
      let yy = text(c.tool, x + pad, cy + 48 + 12 + lh(S.tool) - 6, S.tool, { family: MONO, weight: 500, fill: hu ? C.accentInk : C.accent });
      text(c.body, x + pad, yy + 6 + lh(S.body), S.body, { fill: fg2 });
      let sy = cy + headH;
      const section = (label, lines, h, style) => {
        el("line", { x1: x + pad, x2: x + cw - pad, y1: sy + 8, y2: sy + 8, stroke: hu ? C.accentSoft : C.line, "stroke-width": 2 });
        text([label], x + pad, sy + 20 + lh(S.label) - 6, S.label, { weight: 700, fill: lab });
        text(lines, x + pad, sy + 20 + lh(S.label) + lh(S.trace) - 6, S.trace, style);
        sy += 20 + lh(S.label) + h;
      };
      section(spec.labels.syn, c.syn, synH, { weight: 600, fill: hu ? C.accentInk : C.accent });
      section(spec.labels.real, c.real, realH, c.s.real ? { weight: 600, fill: fg } : { italic: true, fill: C.hush });
      if (i < cards.length - 1) {
        const ax = x + cw + gap / 2, ay = cy + ch / 2;
        el("path", { d: `M${ax - 8} ${ay - 14} L${ax + 8} ${ay} L${ax - 8} ${ay + 14}`, fill: "none", stroke: C.accent, "stroke-width": 4,
          "stroke-linecap": "round", "stroke-linejoin": "round" });
      }
    });
  } else {
    const gap = 7, pad = 22, cw = W - 2 * M, iw = cw - 2 * pad, labW = 168;
    const rows = steps.map((s) => ({
      s, body: wrap(s.short, iw, S.body), syn: wrap(s.syn, iw - labW, S.trace, 600),
      real: wrap(realText(s), iw - labW, S.trace, s.real ? 600 : 400),
    }));
    const rowH = (r) => 14 + lh(S.title) + 2 + lh(S.body) * r.body.length + 4 + lh(S.trace) * (r.syn.length + r.real.length) + 12;
    const heights = rows.map(rowH);
    const total = heights.reduce((a, b) => a + b, 0) + gap * (rows.length - 1);
    const avail = evalTop - 18 - top;
    if (total > avail) problems.push(`rows ${Math.round(total)} px tall, room ${Math.round(avail)}`);
    let ry = top + Math.max(0, (avail - total) / 2);
    rows.forEach((r, i) => {
      const h = heights[i], hu = !!r.s.human, x = M;
      const fg = hu ? C.accentInk : C.ink, fg2 = hu ? C.accentInk : C.ink2, lab = hu ? C.accentSoft : C.muted;
      el("rect", { x, y: ry, width: cw, height: h, rx: 16, fill: hu ? C.accent : C.panel, stroke: hu ? C.accent : C.line, "stroke-width": 2 });
      const by = ry + 14 + lh(S.title) / 2;
      el("circle", { cx: x + pad + 19, cy: by, r: 19, fill: hu ? C.accentInk : C.accent });
      text([String(i + 1)], x + pad + 19, by + S.badge * 0.35, S.badge, { weight: 700, fill: hu ? C.accent : C.accentInk, anchor: "middle" });
      const tx = x + pad + 52, base = by + S.title * 0.35;
      text([r.s.title], tx, base, S.title, { weight: 700, fill: fg });
      const toolX = tx + measure(r.s.title, S.title, 700, SANS) + 20;
      if (toolX + measure(r.s.tool, S.tool, 500, MONO) > x + cw - pad) problems.push(`tool too wide: ${r.s.tool}`);
      text([r.s.tool], toolX, base, S.tool, { family: MONO, weight: 500, fill: hu ? C.accentSoft : C.accent });
      let yy = text(r.body, x + pad, ry + 14 + lh(S.title) + 2 + lh(S.body) - 6, S.body, { fill: fg2 });
      yy += 4 + lh(S.trace);
      text(["Amparo"], x + pad, yy, S.label, { weight: 700, fill: lab });
      yy = text(r.syn, x + pad + labW, yy, S.trace, { weight: 600, fill: hu ? C.accentInk : C.accent });
      yy += lh(S.trace);
      text(["NHANES"], x + pad, yy, S.label, { weight: 700, fill: lab });
      text(r.real, x + pad + labW, yy, S.trace, r.s.real ? { weight: 600, fill: fg } : { italic: true, fill: C.hush });
      ry += h + gap;
    });
  }

  el("rect", { x: M, y: evalTop, width: W - 2 * M, height: evalH, rx: 14, fill: C.panel, stroke: C.accent, "stroke-width": 2 });
  const t = el("text", { x: M + 24, y: evalTop + 14 + lh(S.eval) - 6, "font-size": S.eval, "font-family": SANS, fill: C.ink2 });
  evalLines.forEach((l, i) => {
    const s = el("tspan", { x: M + 24, dy: i ? lh(S.eval) : 0 }, t);
    if (i === 0 && l.startsWith(spec.evalLead)) {
      const b = el("tspan", { "font-weight": 700, fill: C.accent }, s); b.textContent = spec.evalLead;
      const rest = el("tspan", {}, s); rest.textContent = l.slice(spec.evalLead.length);
    } else s.textContent = l;
  });
  for (const node of svg.querySelectorAll("text")) {
    const b = node.getBBox();
    if (b.x < 0 || b.y < 0 || b.x + b.width > W || b.y + b.height > H) problems.push(`off canvas: "${node.textContent.slice(0, 40)}"`);
  }
  return { markup: new XMLSerializer().serializeToString(svg), problems };
}

const browser = await chromium.launch(process.env.CI ? {} : { channel: "chrome" });
try {
  for (const [mode, name, W, H] of [["wide", "workflow", 1600, 900], ["tall", "workflow_4x5", 1080, 1350]]) {
    const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
    await page.setContent("<!doctype html><html><body style='margin:0'></body></html>");
    const { markup, problems } = await page.evaluate(layout, { spec: SPEC, C, SANS, MONO, mode });
    if (problems.length) { console.error(`${name} not written:\n  ` + problems.join("\n  ")); process.exitCode = 1; await page.close(); continue; }
    const svgText = `<?xml version="1.0" encoding="UTF-8"?>\n<!-- Generated by docs/diagram/build.mjs: edit that file, not this one. -->\n${markup}\n`;
    writeFileSync(join(ROOT, "docs", `${name}.svg`), svgText);
    await page.setContent(`<!doctype html><html><body style="margin:0">${markup}</body></html>`);
    await page.locator("svg").screenshot({ path: join(ROOT, "docs", `${name}.png`) });
    console.log(`docs/${name}.svg + .png (${W}×${H})`);
    await page.close();
  }
} finally {
  await browser.close();
}
