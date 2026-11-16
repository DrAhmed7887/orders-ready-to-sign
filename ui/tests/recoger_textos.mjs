// Collects every text the doctor screen can show (all cohorts, views, patients, tabs, the discard dialog).
// Used to build and to check the English mode: node ui/tests/recoger_textos.mjs [lang] > textos.json
import { chromium } from "playwright-core";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const lang = process.argv[2] || "es";
const base = pathToFileURL(path.join(RAIZ, "ui", "index.html")).href;
const b = await chromium.launch(process.env.CI ? {} : { channel: "chrome" });
const p = await b.newPage({ viewport: { width: 1366, height: 900 } });
p.setDefaultTimeout(15000);
const errores = [];
p.on("pageerror", e => errores.push(e.message));
const textos = new Map();
let paginas = 0;
async function recoger(donde) {
  if (++paginas % 50 === 0) console.error(`${paginas} views…`);
  const lista = await p.evaluate(lang => {
    const out = [];
    const saltar = lang === "en" ? "script,style,[lang=es]" : "script,style";
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      if (n.parentElement && n.parentElement.closest(saltar)) continue;
      const t = n.nodeValue.replace(/\s+/g, " ").trim();
      if (t) out.push(t);
    }
    document.querySelectorAll("[aria-label],[title],[placeholder]").forEach(el => {
      if (el.closest(saltar)) return;
      for (const a of ["aria-label", "title", "placeholder"]) { const v = el.getAttribute(a); if (v) out.push(v.trim()); }
    });
    out.push(document.title);
    return out;
  }, lang);
  for (const t of lista) if (!textos.has(t)) textos.set(t, donde);
}
for (const cohort of ["base", "aguja", "cupo"]) {
  const url = `${base}?cohort=${cohort}&lang=${lang}`;
  for (const v of ["pedidos", "agenda", "fuera", "registro", "consulta"]) {
    await p.goto(`${url}#${v}`); await recoger(`${cohort}#${v}`);
  }
    const pedidos = await p.evaluate(c => ({base: window.PEDIDOS, aguja: window.PEDIDOS_AGUJA, cupo: window.PEDIDOS_CUPO})[c].pedidos.map(x => x.id), cohort);
  for (const id of pedidos) {
    await p.goto(`${url}#ficha/${encodeURIComponent(id)}`); await recoger(`${cohort}#ficha/${id}`);
    await p.goto(`${url}#consulta/${encodeURIComponent(id)}`); await recoger(`${cohort}#consulta/${id}`);
    for (const tab of await p.locator("[data-pestana]").evaluateAll(els => els.map(e => e.dataset.pestana))) {
      await p.click(`[data-pestana="${tab}"]`); await recoger(`${cohort}#consulta/${id}/${tab}`);
    }
  }
  await p.goto(`${url}#pedidos`);
  const d = p.locator("button[data-descartar]").first();
  if (await d.count()) { await d.click(); await recoger(`${cohort}#dialogo`); await p.keyboard.press("Escape"); }
  const f = p.locator("button[data-firmar]").first();
  if (await f.count()) { await f.click(); await p.goto(`${url}#registro`); await recoger(`${cohort}#registro-firmado`); }
}
await b.close();
console.log(JSON.stringify({ errores, textos: Object.fromEntries(textos) }, null, 1));
