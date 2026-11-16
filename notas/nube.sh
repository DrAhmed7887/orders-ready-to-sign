#!/usr/bin/env bash
# Ejecuta el lector de notas con un modelo en la NUBE (nunca en el portátil) y graba las salidas.
#
# En Modal con GPU y tráfico en la UE: `modal run notas/modal_eu.py` (mismo flujo, un solo comando).
# Pensado para una máquina Linux con GPU (Google Colab T4/L4/A100, o cualquier VM con CUDA):
#   1. Sube el repo (zip de `git archive HEAD`) y descomprímelo; entra en la carpeta.
#   2. bash notas/nube.sh                      # set de desarrollo
#      bash notas/nube.sh ciego                # set ciego (cuando exista data/synthetic/notas_ciego/)
#   3. Descarga data/synthetic/notas_<set>/salidas_<modelo>.jsonl y haz commit: la CI y la demo lo repiten.
#
# Modelo: Qwen/Qwen3-4B-Instruct-2507 (Apache-2.0, comprobado en Hugging Face el 14 nov 2026), servido con vLLM
# en 127.0.0.1 dentro de la propia máquina en la nube: no se abre ningún puerto a internet. Solo notas sintéticas.
set -euo pipefail

SET="${1:-dev}"
MODELO="${MODELO:-Qwen/Qwen3-4B-Instruct-2507}"
PUERTO="${PUERTO:-8000}"
CARPETA="data/synthetic/notas_${SET}"
ETIQUETA_MODELO="$(basename "$MODELO" | tr '[:upper:]' '[:lower:]')"
SALIDA="${CARPETA}/salidas_${ETIQUETA_MODELO}.jsonl"

[ -f "${CARPETA}/extracto.sql" ] || { echo "No existe ${CARPETA}/extracto.sql" >&2; exit 2; }
command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || echo "Aviso: sin GPU visible"

python3 -m pip install -q "vllm>=0.6" pytest
python3 -m vllm.entrypoints.openai.api_server --model "$MODELO" --host 127.0.0.1 --port "$PUERTO" \
  --max-model-len 4096 --seed 35 --dtype auto > vllm.log 2>&1 &
VLLM_PID=$!
trap 'kill $VLLM_PID 2>/dev/null || true' EXIT

echo "Esperando a vLLM…"
for _ in $(seq 1 120); do
  curl -sf "http://127.0.0.1:${PUERTO}/v1/models" >/dev/null && break
  kill -0 $VLLM_PID 2>/dev/null || { tail -40 vllm.log; exit 1; }
  sleep 5
done

ETIQ="${CARPETA}/etiquetas.csv"
python3 eval/evaluar.py "${CARPETA}/extracto.sql" "$ETIQ" \
  --lector-url "http://127.0.0.1:${PUERTO}" --lector-modelo "$MODELO" --grabar "$SALIDA" \
  -o "eval/results/notas_${SET}_${ETIQUETA_MODELO}.md" || true
python3 eval/notas.py "${CARPETA}" "$SALIDA" -o "eval/results/notas_${SET}_${ETIQUETA_MODELO}_por_nota.md" || true

echo "Listo. Descarga y haz commit de:"
echo "  $SALIDA"
echo "  eval/results/notas_${SET}_${ETIQUETA_MODELO}.md  eval/results/notas_${SET}_${ETIQUETA_MODELO}_por_nota.md"
