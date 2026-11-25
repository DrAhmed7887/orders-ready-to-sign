// Automated tests for the interactive .sb-* sandbox on index.html (no backend, deterministic mirror).
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { chromium } from "playwright-core";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const LANDING = pathToFileURL(path.join(RAIZ, "index.html")).href + "#sandbox";

let navegador, contexto, pagina;
const errores = [];

before(async () => {
  navegador = await chromium.launch(process.env.CI ? {} : { channel: "chrome" });
  contexto = await navegador.newContext();
  pagina = await contexto.newPage();
  pagina.on("pageerror", e => errores.push(e.message));
  pagina.on("console", m => { if (m.type() === "error") errores.push(m.text()); });
  await pagina.goto(LANDING);
});

after(async () => {
  await navegador?.close();
  assert.deepEqual(errores, [], "landing sandbox should produce zero page or console errors");
});

test("sandbox loads Amparo preset with live CKD-EPI 2021 eGFR, S1c rule, and verified note", async () => {
  assert.equal(await pagina.locator("#sb-egfr-val").textContent(), "74.1");
  assert.match(await pagina.locator("#sb-egfr-badge").textContent(), /G2 · Mildly decreased/);
  assert.match(await pagina.locator("#sb-rule-badge").textContent(), /S1c · Persistent albuminuria/);
  assert.match(await pagina.locator("#sb-guard-badge").textContent(), /VERIFIED/);
  assert.match(await pagina.locator("#sb-guard-extracted").textContent(), /ACR 110 mg\/g · date 2026-09-12/);
});

test("editing eGFR (SCr) and uACR updates KDIGO stage, S1b/S1a rules, and dialysis exclusion live", async () => {
  await pagina.locator("#sb-scr").fill("1.45");
  await pagina.locator("#sb-acr").fill("45");
  await pagina.getByRole("button", { name: "Clear note" }).click();

  assert.equal(await pagina.locator("#sb-egfr-val").textContent(), "39.0");
  assert.match(await pagina.locator("#sb-egfr-badge").textContent(), /G3b · Moderate to severe \(30–44\)/);
  assert.match(await pagina.locator("#sb-rule-badge").textContent(), /S1b · Repeat ACR due/);
  assert.match(await pagina.locator("#sb-order-card").textContent(), /45 mg\/g, A2 \(30–299 mg\/g\)/);

  await pagina.locator("#sb-clear-acr").click();
  assert.match(await pagina.locator("#sb-rule-badge").textContent(), /S1a · Screening overdue/);

  await pagina.locator("#sb-dial").check();
  assert.match(await pagina.locator("#sb-rule-badge").textContent(), /Excluded · Left off list/);
  await pagina.locator("#sb-dial").uncheck();
});

test("note guard enforces negation, ungrounded value/bound, dipstick, injection, and normal repeat rules", async () => {
  await pagina.locator('.sb-chip[data-preset="s1b"]').click();
  assert.match(await pagina.locator("#sb-rule-badge").textContent(), /S1b · Repeat ACR due/);

  // Negation rule (N1d)
  await pagina.locator("#sb-note").fill("No se ha realizado CAC 110 mg/g el 12/09/2026.");
  assert.equal(await pagina.locator("#sb-guard-badge").textContent(), "BLOCKED");
  assert.match(await pagina.locator("#sb-guard-reason").textContent(), /N1d.*negation/i);
  assert.match(await pagina.locator("#sb-guard-extracted").textContent(), /Extracted: none/);
  assert.match(await pagina.locator("#sb-rule-badge").textContent(), /S1b · Repeat ACR due/);

  // Ungrounded value/bound rule (Round 15 V4/V6)
  await pagina.getByRole("button", { name: "Test ungrounded bound" }).click();
  assert.equal(await pagina.locator("#sb-guard-badge").textContent(), "BLOCKED");
  assert.match(await pagina.locator("#sb-guard-reason").textContent(), /Round 15 V4\/V6/);

  // Dipstick exclusion (Round 15 V3)
  await pagina.getByRole("button", { name: "Test dipstick ++++" }).click();
  assert.equal(await pagina.locator("#sb-guard-badge").textContent(), "BLOCKED");
  assert.match(await pagina.locator("#sb-guard-reason").textContent(), /Round 15 V3/);

  // Normal repeat note suppresses S1b (N1a)
  await pagina.getByRole("button", { name: "Test normal repeat note" }).click();
  assert.equal(await pagina.locator("#sb-guard-badge").textContent(), "VERIFIED");
  assert.match(await pagina.locator("#sb-guard-extracted").textContent(), /ACR 14 mg\/g · date 2026-10-01/);
  assert.match(await pagina.locator("#sb-rule-badge").textContent(), /Suppressed \(N1a\)/);

  // Prompt-injection preset
  await pagina.locator('.sb-chip[data-preset="injection"]').click();
  assert.equal(await pagina.locator("#sb-guard-badge").textContent(), "BLOCKED");
  assert.match(await pagina.locator("#sb-guard-reason").textContent(), /prompt-injection guard/);
});
