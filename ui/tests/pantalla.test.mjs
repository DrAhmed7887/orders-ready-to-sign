// Prueba automática de la pantalla del médico: lo que el CP3 tiene que enseñar, hecho con clics reales.
// Local: usa el Chrome instalado. CI: usa el Chromium que instala el workflow.
// Las pruebas comparten una página y se ejecutan EN ORDEN: cada una parte de las decisiones de la anterior.
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { chromium } from "playwright-core";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const PAGINA = pathToFileURL(path.join(RAIZ, "ui", "index.html")).href;
const PEDIDOS_JS = path.join(RAIZ, "ui", "pedidos.js");
const PYTHON = process.env.PYTHON || "python3";

let navegador, contexto, pagina, comprometido;
const erroresDePagina = [];

function regenerar() {
  execFileSync(PYTHON, ["ejecutar.py", "data/synthetic/demo_seed.sql", "-o", "ui/pedidos.json"], { cwd: RAIZ });
}

const fila = nombre => pagina.locator(".fila", { hasText: nombre });
const pendientes = () => pagina.locator("#n-pedidos").textContent();

before(async () => {
  comprometido = readFileSync(PEDIDOS_JS, "utf8");   // lo que hay en el repositorio
  regenerar();
  navegador = await chromium.launch(process.env.CI ? {} : { channel: "chrome" });
  contexto = await navegador.newContext({ acceptDownloads: true });
  pagina = await contexto.newPage();
  pagina.on("pageerror", e => erroresDePagina.push(e.message));
  await pagina.goto(PAGINA + "#pedidos");
});

after(async () => {
  await navegador?.close();
  assert.deepEqual(erroresDePagina, [], "la página no debe lanzar errores");
});

test("lista: 3 grupos en orden, aviso de Pilar y Antonio fuera de la lista", async () => {
  const nombres = await pagina.locator(".fila .nombre").allTextContents();
  assert.deepEqual(nombres, ["Manuel, 72", "Pilar, 67", "Rosa, 59"]);
  assert.match(await pagina.locator(".banner").textContent(), /Hoy en consulta · 10:40.*Pilar/s);
  assert.match(await pagina.locator(".discontinua").textContent(), /Antonio · Pedido ya pendiente/);
  assert.equal(await pendientes(), "3");
});

test("lo primero que se ve es el resultado: 3 pedidos que el filtro básico no ve, y los pasos", async () => {
  assert.match(await pagina.locator("h1").textContent(), /3 pedidos renales que un filtro básico no ve/);
  assert.match(await pagina.locator(".resultado").textContent(), /ve 0 de 3/);
  assert.match(await pagina.locator(".pasos").textContent(), /4 pacientes.*extracto completo.*1 fuera.*3 pedidos.*0 de 3 decididos/s);
});

test("Firmar desde la lista queda registrado", async () => {
  await fila("Manuel").getByRole("button", { name: "Firmar" }).click();
  assert.match(await fila("Manuel").textContent(), /Firmado \d\d:\d\d/);
  assert.equal(await pendientes(), "2");
});

test("Aplazar desde la ficha, con la procedencia fechada a la vista", async () => {
  await pagina.getByRole("link", { name: "Abrir ficha" }).click();
  assert.match(await pagina.locator("table").textContent(), /12 feb 2026.*CAC \(orina\).*85 mg\/g/s);
  // Las condiciones de la regla, con sus umbrales y su fuente de parametros. D1–D5 firmadas (14 nov): sin aviso amarillo.
  const cond = await pagina.locator(".condiciones").textContent();
  assert.match(cond, /CAC ≥30 mg\/g \(≥3 mg\/mmol\).*KDIGO 2024, tabla 1/s);
  assert.match(cond, /Sin repetir en más de 6 meses.*Sin código de ERC/s);
  assert.equal(await pagina.locator(".condiciones .prop").count(), 0, "con todo firmado no hay umbrales en propuesta");
  await pagina.getByRole("button", { name: "Aplazar" }).click();
  assert.match(await pagina.locator(".pedido-caja").textContent(), /Aplazado/);
  await pagina.getByRole("link", { name: "← Pedidos para firmar" }).click();
  assert.equal(await pendientes(), "1");
});

test("Descartar pide un motivo y Esc después no descarta otro pedido", async () => {
  await fila("Rosa").getByRole("button", { name: "Descartar…" }).click();
  await pagina.getByLabel("Seguimiento en nefrología u otro centro").check();
  await pagina.locator("dialog").getByRole("button", { name: "Descartar" }).click();
  await fila("Rosa").locator(".estado.desc").waitFor();   // el cierre del diálogo es asíncrono
  assert.match(await fila("Rosa").textContent(), /Descartado.*Seguimiento en nefrología/s);

  await fila("Rosa").getByRole("button", { name: "deshacer" }).click();
  await fila("Rosa").getByRole("button", { name: "Descartar…" }).click();
  await pagina.keyboard.press("Escape");
  await pagina.locator("dialog").waitFor({ state: "hidden" });
  await pagina.evaluate(() => new Promise(r => setTimeout(r, 0)));   // deja correr onclose
  assert.equal(await fila("Rosa").getByRole("button", { name: "Firmar" }).count(), 1, "Esc no debe descartar");
  assert.equal(await pendientes(), "1");
});

test("las decisiones sobreviven a recargar y a volver a ejecutar las reglas, sin duplicados", async () => {
  regenerar();
  assert.equal(readFileSync(PEDIDOS_JS, "utf8"), comprometido,
               "volver a ejecutar da el mismo pedidos.js que el del repositorio");
  await pagina.reload();
  assert.equal(await pagina.locator(".fila").count(), 3);
  assert.match(await fila("Manuel").textContent(), /Firmado/);
  assert.equal(await pendientes(), "1");
});

test("registro de decisiones y exportación en JSON", async () => {
  await pagina.goto(PAGINA + "#registro");
  const filas = await pagina.locator("tbody tr").allTextContents();
  assert.equal(filas.length, 2);
  const [descarga] = await Promise.all([pagina.waitForEvent("download"),
                                        pagina.getByRole("button", { name: "Exportar registro (JSON)" }).click()]);
  const json = JSON.parse(readFileSync(await descarga.path(), "utf8"));
  assert.deepEqual(Object.values(json.decisiones).map(d => d.accion).sort(), ["aplazado", "firmado"]);
});

test("un enlace manipulado no ejecuta código", async () => {
  await pagina.goto(PAGINA + "#constructor/" + encodeURIComponent('<img src=x onerror="window.__x=1">'));
  await pagina.locator("h1").first().waitFor();
  assert.equal(await pagina.evaluate(() => window.__x), undefined);
  assert.equal(await pagina.locator("main img").count(), 0);
});

for (const [caso, valor] of [["JSON roto", "{no es json"], ["lista", "[]"],
                             ["decisión mal formada", '{"x":{"accion":"hackeado","hora":1}}']]) {
  test(`un almacenamiento local corrupto (${caso}) no rompe la pantalla`, async () => {
    await pagina.evaluate(v => { for (const k of Object.keys(localStorage)) localStorage.setItem(k, v); }, valor);
    await pagina.goto(PAGINA + "#registro");
    await pagina.reload();
    assert.match(await pagina.locator("main").textContent(), /Aún no hay decisiones/);
    assert.equal(await pendientes(), "3");
  });
}

test("si el navegador no deja guardar, la pantalla lo dice; y deja de decirlo cuando vuelve a guardar", async () => {
  const otra = await navegador.newContext();
  await otra.addInitScript(() => {
    const real = Storage.prototype.setItem;
    window.__bloquear = true;
    Storage.prototype.setItem = function (...a) { if (window.__bloquear) throw new Error("bloqueado"); return real.apply(this, a); };
  });
  const p = await otra.newPage();
  await p.goto(PAGINA + "#pedidos");
  await p.locator(".fila", { hasText: "Rosa" }).getByRole("button", { name: "Firmar" }).click();
  assert.match(await p.locator(".alerta").textContent(), /no se ha podido guardar/);
  await p.evaluate(() => { window.__bloquear = false; });
  await p.locator(".fila", { hasText: "Manuel" }).getByRole("button", { name: "Firmar" }).click();
  assert.equal(await p.locator(".alerta").count(), 0);
  await otra.close();
});

test("con un extracto incompleto la pantalla lo avisa arriba", async () => {
  const otra = await navegador.newContext();
  await otra.addInitScript(() => {
    let valor;
    Object.defineProperty(window, "PEDIDOS", {
      get: () => valor,
      set: v => { valor = { ...v, extracto_completo: false, pedidos: [] }; },
    });
  });
  const p = await otra.newPage();
  await p.goto(PAGINA + "#pedidos");
  assert.match(await p.locator(".alerta").textContent(), /Extracto incompleto/);
  await otra.close();
});

test("un CAC con una unidad que la SQL no clasifica no muestra categoría A1–A3 en la ficha", async () => {
  const otra = await navegador.newContext();
  await otra.addInitScript(() => {
    let valor;
    Object.defineProperty(window, "PEDIDOS", {
      get: () => valor,
      set: v => { valor = { ...v, pedidos: v.pedidos.map(p => ({ ...p,
        procedencia: p.procedencia.map(x => x.prueba === "CAC" ? { ...x, unidad: "mg/dL" } : x) })) }; },
    });
  });
  const p = await otra.newPage();
  await p.goto(PAGINA + "#ficha/S1b-2-2026-02-12");
  assert.match(await p.locator("table").textContent(), /85 mg\/dL/);
  assert.equal(await p.locator("table .chip").count(), 0);
  await otra.close();
});

test("un umbral que vuelve a estado «propuesta» se marca en la ficha como pendiente de firma", async () => {
  const otra = await navegador.newContext();
  await otra.addInitScript(() => {
    let valor;
    Object.defineProperty(window, "PEDIDOS", {
      get: () => valor,
      set: v => { valor = { ...v, parametros: v.parametros.map(x =>
        x.clave === "cac_umbral_mg_mmol" ? { ...x, estado: "propuesta D2" } : x) }; },
    });
  });
  const p = await otra.newPage();
  await p.goto(PAGINA + "#ficha/S1b-2-2026-02-12");
  assert.match(await p.locator(".condiciones").textContent(),
               /CAC ≥30 mg\/g \(≥3 mg\/mmol\).*propuesta D2 · pendiente de firma clínica/s);
  assert.equal(await p.locator(".condiciones .prop").count(), 1);
  await otra.close();
});

test("las decisiones se guardan por extracto: otra fuente con la misma fecha no hereda las de la demo", async () => {
  const otra = await navegador.newContext();
  await otra.addInitScript(() => {
    let valor;
    Object.defineProperty(window, "PEDIDOS", { get: () => valor, set: v => { valor = { ...v, fuente: "sintetico_ciego" }; } });
  });
  const p = await otra.newPage();
  await p.goto(PAGINA + "#pedidos");
  await p.locator(".fila", { hasText: "Rosa" }).getByRole("button", { name: "Firmar" }).click();
  const claves = await p.evaluate(() => Object.keys(localStorage));
  assert.deepEqual(claves, ["g35-decisiones-sintetico_ciego-2026-11-14"]);
  await otra.close();
});

test("cupo AP español de 1.000: el selector cambia de cohorte, la tira resume el cupo y la consulta abre una aguja", async () => {
  const otra = await navegador.newContext();
  const p = await otra.newPage();
  const errores = [];
  p.on("pageerror", e => errores.push(e.message));
  p.on("console", m => { if (m.type() === "error") errores.push(m.text()); });
  await p.goto(PAGINA + "#pedidos");
  await p.getByRole("button", { name: "Cupo AP Español · 1.000 pac." }).click();
  const tira = p.locator(".cupo-tira");
  assert.match(await tira.textContent(), /Cupo AP Español · 1\.000 adultos sintéticos/);
  assert.match(await tira.textContent(), /Agujas en el pajar \(S1c\)/);
  assert.match(await p.locator("#quien").textContent(), /Cupo AP Español \(1\.000 pac\.\)/);
  await tira.locator(".agujas a").first().click();
  assert.match(await p.locator(".ws-banner").textContent(), /SIP-S\d{8}/);
  assert.match(await p.locator(".ws-banner").textContent(), /años · (Mujer|Hombre)/);
  assert.match(await p.locator(".pedido-caja").textContent(), /Petición clínica.*Valoración clínica \(KDIGO \/ N18\).*Prioridad.*Ordinaria/s);
  await p.getByRole("tab", { name: "Hoja de evolución" }).click();
  assert.equal(await p.locator(".ws-evol mark").count() >= 1, true, "la frase comprobada se resalta");
  await p.getByRole("button", { name: "Caso Carmen · 4 pac." }).click();
  await p.goto(PAGINA + "#pedidos");
  assert.deepEqual(await p.locator(".fila .nombre").allTextContents(), ["Manuel, 72", "Pilar, 67", "Rosa, 59"]);
  assert.deepEqual(errores, []);
  await otra.close();
});


test("revisión externa (F5): pastillas en #consulta/<id>, cambio de cohorte desde una ficha, cifras y reglas", async () => {
  const otra = await navegador.newContext();
  const p = await otra.newPage();
  const errores = [];
  p.on("pageerror", e => errores.push(e.message));
  await p.goto(PAGINA + "#pedidos");
  await p.getByRole("button", { name: "Cupo AP Español · 1.000 pac." }).click();
  assert.match(await p.locator(".pasos").textContent(), /S3c/, "la tira de pasos nombra S3c");
  // Las cifras de «fuera» de la tira cuadran con el contador del menú (incluye los que siguen por otro pedido).
  const tira = await p.locator(".cupo-tira").textContent();
  const fueraMenu = Number(await p.locator("#n-fuera").textContent());
  const sumas = [...tira.matchAll(/(\d+)\s*(?:fuera:|con un pedido retirado)/g)].map(m => Number(m[1]));
  assert.equal(sumas.reduce((a, b) => a + b, 0), fueraMenu, tira);
  // Desde #consulta/<id>, otra pastilla cambia de paciente (antes el parámetro del enlace lo bloqueaba).
  await p.locator(".cupo-tira .agujas a").first().click();
  const antes = await p.locator(".ws-banner").textContent();
  await p.locator(".btn-pac-sel:not(.activo)").first().click();
  assert.notEqual(await p.locator(".ws-banner").textContent(), antes);
  // Un paciente sin diagnósticos codificados no enseña «sin diagnósticos» como si fuera un código.
  assert.equal(await p.locator("li code", { hasText: /sin diagn/i }).count(), 0);
  // Desde la ficha de un pedido del cupo, cambiar de cohorte no deja «Pedido no encontrado».
  await p.goto(PAGINA + "#pedidos");
  await p.locator(".fila a[href^='#ficha/']").first().click();
  await p.getByRole("button", { name: "Caso Carmen · 4 pac." }).click();
  assert.doesNotMatch(await p.locator("#vista").textContent(), /Pedido no encontrado/);
  assert.deepEqual(errores, []);
  await otra.close();
});
