"""Note reader on REAL published clinical text (CodiEsp, CC BY 4.0), one ephemeral `modal run` in the EU.

Same model, prompt, settings and LectorEndpoint as notas/modal_eu.py. The sampled case texts are sent from the
laptop as an argument (published case reports, not patient records: docs/NOTES_REAL_PROTOCOL.md). The job returns
the recording only; verification happens locally and in CI by replaying it (eval/notas_reales/revisar.py).

    python3 eval/notas_reales/fetch.py && python3 eval/notas_reales/muestra.py
    modal run notas/modal_reales.py          # needs Ahmed's OK for each run: the account has a card on file
Never `modal deploy`.
"""
from __future__ import annotations

import json
from pathlib import Path

import modal

RAIZ = Path(__file__).resolve().parents[1]
MODELO = "Qwen/Qwen3-4B-Instruct-2507"
ETIQUETA = MODELO.split("/")[-1].lower()
SALIDA = RAIZ / "eval" / "notas_reales" / f"salidas_{ETIQUETA}.jsonl"

imagen = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("curl")
    .pip_install("vllm==0.11.0", "transformers==4.57.1")
    .add_local_dir(RAIZ / "notas", "/repo/notas", ignore=["**/__pycache__"])
)
app = modal.App("lector-notas-reales-eu", image=imagen)


@app.function(gpu=["L4", "L40S"], region="eu", routing_region="eu-west", timeout=3600)
def leer(textos: list[str]) -> dict:
    import subprocess
    import sys
    import time
    import urllib.request

    sys.path.insert(0, "/repo")
    log = open("/tmp/vllm.log", "w")
    servidor = subprocess.Popen(
        ["python3", "-m", "vllm.entrypoints.openai.api_server", "--model", MODELO, "--host", "127.0.0.1",
         "--port", "8000", "--max-model-len", "4096", "--seed", "35", "--dtype", "auto"],
        stdout=log, stderr=subprocess.STDOUT)
    try:
        for _ in range(180):
            if servidor.poll() is not None:
                raise RuntimeError("vLLM stopped:\n" + Path("/tmp/vllm.log").read_text()[-3000:])
            try:
                urllib.request.urlopen("http://127.0.0.1:8000/v1/models", timeout=5)
                break
            except OSError:
                time.sleep(5)
        else:
            raise RuntimeError("vLLM did not start in 15 min")
        from notas.leer import LectorEndpoint
        lector = LectorEndpoint("http://127.0.0.1:8000", MODELO)
        t0 = time.time()
        for t in textos:
            lector(t)
        return {"grabacion": lector.grabacion, "segundos_lectura": round(time.time() - t0, 1)}
    finally:
        servidor.terminate()


@app.local_entrypoint()
def main(muestra: str = "eval/notas_reales/muestra.json", salida: str = "") -> None:
    destino = (RAIZ / salida) if salida else SALIDA
    muestra = json.loads((RAIZ / muestra).read_text(encoding="utf-8"))
    textos = [(RAIZ / "eval/notas_reales/raw" / f"{c['id']}.txt").read_text(encoding="utf-8") for c in muestra["cases"]]
    r = leer.remote(textos)
    destino.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in r["grabacion"]), encoding="utf-8")
    print(f"{len(r['grabacion'])} outputs -> {destino.relative_to(RAIZ)} ({r['segundos_lectura']} s of reading)")
