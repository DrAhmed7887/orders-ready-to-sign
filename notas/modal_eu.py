"""Lector de notas con un modelo real en Modal, con cómputo y tráfico en la UE (nunca en el portátil).

Hace lo mismo que notas/nube.sh, en un solo `modal run` efímero:
- La GPU se elige en la UE (`region="eu"`, Espacio Económico Europeo; precio ×1.15) y las entradas y salidas
  pasan por Dublín (`routing_region="eu-west"`). Fuente: modal.com/docs/guide/region-selection (14 nov 2026).
- Dentro del contenedor, vLLM sirve Qwen/Qwen3-4B-Instruct-2507 (Apache-2.0) en 127.0.0.1: no se abre ningún
  puerto a internet, no hace falta clave y no queda nada desplegado. Los pesos se bajan en la nube, no aquí.
- El mismo código del repo (eval/evaluar.py → LectorEndpoint) lee las notas sintéticas y graba las salidas;
  luego eval/notas.py las puntúa. Este script trae los archivos al portátil para revisarlos y hacer commit.
- Las grabaciones del oráculo (salidas_oraculo.jsonl) se quedan: prueban el código. Las del modelo van al lado.

Uso (necesita `modal token new` y el OK de Ahmed para cada ejecución: la cuenta tiene tarjeta):
    modal run notas/modal_eu.py                       # notas_dev, aguja y cupo_espanol_1000
    modal run notas/modal_eu.py --sets aguja
Nunca `modal deploy`. Solo notas sintéticas.
"""
from __future__ import annotations

from pathlib import Path

import modal

RAIZ = Path(__file__).resolve().parents[1]
MODELO = "Qwen/Qwen3-4B-Instruct-2507"
ETIQUETA = MODELO.split("/")[-1].lower()          # qwen3-4b-instruct-2507, igual que nube.sh
# set → (carpeta, lista esperada con notas). «ciego» no tiene notas: no hay nada que leer.
SETS_VALIDOS = {"notas_dev": ("data/synthetic/notas_dev", "etiquetas.csv"),
                "aguja": ("data/synthetic/aguja", "etiquetas.csv"),
                "cupo_espanol_1000": ("data/synthetic/cupo_espanol_1000", "etiquetas_cupo_1000.csv")}

imagen = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("curl")
    .pip_install("vllm==0.11.0", "transformers==4.57.1")   # transformers 5.x rompe el tokenizador en vLLM 0.11
    .add_local_dir(RAIZ, "/repo", ignore=["node_modules", ".git", "**/__pycache__", "ui", "docs", "*.db"])
)
app = modal.App("pedidos-lector-notas-eu", image=imagen)


@app.function(gpu=["L4", "L40S"], region="eu", routing_region="eu-west", timeout=1800)
def leer(sets: list[str]) -> dict[str, str]:
    import subprocess
    import time
    import urllib.request

    log = open("/tmp/vllm.log", "w")
    servidor = subprocess.Popen(
        ["python3", "-m", "vllm.entrypoints.openai.api_server", "--model", MODELO, "--host", "127.0.0.1",
         "--port", "8000", "--max-model-len", "4096", "--seed", "35", "--dtype", "auto"],
        stdout=log, stderr=subprocess.STDOUT)
    try:
        for _ in range(180):
            if servidor.poll() is not None:
                raise RuntimeError("vLLM se paró:\n" + Path("/tmp/vllm.log").read_text()[-3000:])
            try:
                urllib.request.urlopen("http://127.0.0.1:8000/v1/models", timeout=5)
                break
            except OSError:
                time.sleep(5)
        else:
            raise RuntimeError("vLLM no arrancó en 15 min")

        devuelto: dict[str, str] = {}
        for s in sets:
            carpeta, etiquetas = SETS_VALIDOS[s]
            grabadas = f"{carpeta}/salidas_{ETIQUETA}.jsonl"
            informe = f"eval/results/{s}_{ETIQUETA}"
            pasos = [
                ["python3", "eval/evaluar.py", f"{carpeta}/extracto.sql", f"{carpeta}/{etiquetas}",
                 "--lector-url", "http://127.0.0.1:8000", "--lector-modelo", MODELO, "--grabar", grabadas,
                 "-o", f"{informe}.md"],
                ["python3", "eval/notas.py", carpeta, grabadas, "--etiquetas", etiquetas, "-o", f"{informe}_por_nota.md"],
            ]
            for paso in pasos:   # sin check: una etiqueta que no coincide no debe perder la grabación
                r = subprocess.run(paso, cwd="/repo", capture_output=True, text=True)
                print(f"$ {' '.join(paso[:3])} … → código {r.returncode}\n{r.stdout[-1500:]}{r.stderr[-1500:]}")
            for ruta in [grabadas, f"{informe}.md", f"{informe}.json", f"{informe}_por_nota.md",
                         f"{informe}_por_nota.json"]:
                p = Path("/repo") / ruta
                if p.exists():
                    devuelto[ruta] = p.read_text(encoding="utf-8")
        return devuelto
    finally:
        servidor.terminate()


@app.local_entrypoint()
def main(sets: str = "notas_dev,aguja,cupo_espanol_1000") -> None:
    elegidos = [s.strip() for s in sets.split(",") if s.strip()]
    malos = [s for s in elegidos if s not in SETS_VALIDOS]
    if malos:
        raise SystemExit(f"Sets desconocidos: {malos}. Válidos: {sorted(SETS_VALIDOS)}")
    archivos = leer.remote(elegidos)
    for ruta, contenido in archivos.items():
        destino = (RAIZ / ruta).resolve()
        if RAIZ not in destino.parents:      # solo dentro del repo
            raise SystemExit(f"Ruta fuera del repo: {ruta}")
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(contenido, encoding="utf-8")
        print("escrito", ruta)
