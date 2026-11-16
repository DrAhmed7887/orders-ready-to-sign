// English mode (ui/index.html?lang=en): every view of every cohort, no Spanish left outside «note quotes» and
// lang="es" notes, no page errors, and a second translation pass changes nothing (a non-idempotent pass froze
// the page once through the MutationObserver).
import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { chromium } from "playwright-core";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const PYTHON = process.env.PYTHON || "python3";

test("English mode: no Spanish left, no page errors", { timeout: 300000 }, () => {
  const out = execFileSync("node", [path.join(RAIZ, "ui/tests/recoger_textos.mjs"), "en"], { cwd: RAIZ, maxBuffer: 64 << 20 });
  const datos = JSON.parse(out);
  assert.deepEqual(datos.errores, [], "page errors in English mode");
  const f = path.join(mkdtempSync(path.join(tmpdir(), "idioma-")), "textos_en.json");
  writeFileSync(f, out);
  execFileSync(PYTHON, [path.join(RAIZ, "ui/tests/espanol_restante.py"), f], { stdio: "inherit" });
  test.textos = Object.keys(datos.textos);
});

test("English mode: a second pass changes nothing", { timeout: 120000 }, async () => {
  const b = await chromium.launch(process.env.CI ? {} : { channel: "chrome" });
  const p = await b.newPage();
  await p.goto(pathToFileURL(path.join(RAIZ, "ui", "index.html")).href + "?lang=en&cohort=cupo#pedidos");
  const textos = execFileSync("node", [path.join(RAIZ, "ui/tests/recoger_textos.mjs"), "es"], { cwd: RAIZ, maxBuffer: 64 << 20 });
  const muestras = Object.keys(JSON.parse(textos).textos);
  const inestables = await p.evaluate(ts => ts.filter(t => !window.traducirEsEstable(t)), muestras);
  await b.close();
  assert.deepEqual(inestables.slice(0, 20), [], `${inestables.length} texts change on a second pass`);
});

test("English mode: the screen after signing and after dismissing has no Spanish", { timeout: 120000 }, async () => {
  const b = await chromium.launch(process.env.CI ? {} : { channel: "chrome" });
  const plano = async (l) => (await l.first().innerText()).replace(/\s+/g, " ").trim();
  let firmado, chip, descartado;
  try {
    const p = await b.newPage();
    await p.goto(pathToFileURL(path.join(RAIZ, "ui", "index.html")).href + "?lang=en&cohort=aguja#consulta/S1c-251-2026-09-12");
    await p.locator("button.firmar:visible").first().click();
    firmado = await plano(p.locator(".estado:visible"));
    chip = await plano(p.locator(".btn-pac-sel.activo"));
    await p.locator("button.deshacer:visible").first().click();
    await p.locator("button[data-descartar]:visible").first().click();
    await p.locator("#dlg-descartar button[value=ok]").click();
    descartado = await plano(p.locator(".estado:visible"));
  } finally {
    await b.close();   // an open browser keeps the test runner alive after a failed check
  }
  assert.match(firmado, /^Signed \d\d:\d\d$/);
  assert.match(chip, /· signed$/);
  assert.match(descartado, /^Dismissed \d\d:\d\d · Already assessed in another visit$/);
  for (const s of [firmado, chip, descartado]) assert.doesNotMatch(s, /firmad|descartad|deshacer|Ya valorado/i);
});
