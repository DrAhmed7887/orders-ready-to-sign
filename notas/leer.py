"""Lee las notas de los pacientes candidatos y guarda en nota_hallazgo lo que pasa las comprobaciones.

Un «lector» es cualquier función texto_de_nota → salida del modelo (dict) o None, con un atributo `modelo`.
- LectorEndpoint: un servidor compatible con OpenAI (/v1/chat/completions) en la nube que el equipo elija
  (llama-server, vLLM…). Nunca se descarga un modelo en el portátil.
- LectorGrabado: repite salidas ya grabadas (JSONL). La CI y la demo usan este: mismo resultado siempre.
"""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from notas.verificar import frases, verificar

PROMPT = (Path(__file__).resolve().parent / "prompt_es.md")
ESQUEMA_SALIDA = {
    "type": "object",
    "properties": {
        "etiqueta": {"type": "string", "enum": ["ya_realizada", "rechazo", "nefrologia", "ninguna"]},
        "prueba": {"type": ["string", "null"], "enum": ["CAC", "FGe", None]},
        "fecha_en_nota": {"type": ["string", "null"]},
        "frase": {"type": ["integer", "null"], "minimum": 1},
    },
    "required": ["etiqueta", "prueba", "fecha_en_nota", "frase"],
    "additionalProperties": False,
}

Lector = Callable[[str], Optional[Dict[str, Any]]]
MAX_CARACTERES = 6000   # una nota más larga se corta por frases enteras: lo que quede fuera no puede señalarse


def nota_numerada(texto: str, maximo: int = MAX_CARACTERES) -> str:
    """La nota como la ve el modelo: una frase por línea, «[n] frase». Los «<» y «>» se neutralizan."""
    lineas: List[str] = []
    total = 0
    for i, frase in enumerate(frases(texto), start=1):
        segura = frase.replace("<", "‹").replace(">", "›")
        total += len(segura)
        if total > maximo:
            break
        lineas.append(f"[{i}] {segura}")
    return "<nota>\n" + "\n".join(lineas) + "\n</nota>"


def huella(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


class LectorGrabado:
    """Salidas grabadas en JSONL: {"sha256": huella(nota), "salida": {...}, "modelo": "..."} por línea."""

    def __init__(self, ruta: Path) -> None:
        self.salidas: Dict[str, Any] = {}
        modelos = set()
        for n, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), start=1):
            if not linea.strip():
                continue
            try:
                fila = json.loads(linea)
                h, salida = fila["sha256"], fila.get("salida")
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                raise ValueError(f"{ruta}:{n}: línea grabada no válida ({type(exc).__name__})") from exc
            if not isinstance(h, str):
                raise ValueError(f"{ruta}:{n}: sha256 no válido")
            if h in self.salidas and self.salidas[h] != salida:
                raise ValueError(f"{ruta}:{n}: dos salidas distintas para la misma nota")
            self.salidas[h] = salida
            modelos.add(str(fila.get("modelo") or "?"))
        self.modelo = "grabado:" + "+".join(sorted(modelos))
        self.sin_grabar: List[str] = []

    def __call__(self, texto: str) -> Optional[Dict[str, Any]]:
        h = huella(texto)
        if h not in self.salidas:
            self.sin_grabar.append(h)   # sin salida grabada → sin efecto, y se informa
            return None
        return self.salidas[h]


class LectorEndpoint:
    """Servidor compatible con OpenAI. URL y modelo por argumento; la clave (si hace falta) por variable de entorno."""

    def __init__(self, url: str, modelo: str, clave_env: str = "LECTOR_API_KEY", timeout: int = 120) -> None:
        if not url.startswith(("http://", "https://")):
            raise ValueError("La URL del lector debe empezar por http:// o https://")
        self.url = url.rstrip("/") + "/v1/chat/completions"
        self.modelo = modelo
        self.clave = os.environ.get(clave_env, "")
        self.timeout = timeout
        self.sistema = PROMPT.read_text(encoding="utf-8")
        self.grabacion: List[Dict[str, Any]] = []
        self._vistas: Dict[str, Any] = {}     # una llamada por texto distinto: la misma nota da la misma salida

    def __call__(self, texto: str) -> Optional[Dict[str, Any]]:
        h = huella(texto)
        if h in self._vistas:
            return self._vistas[h]
        cuerpo = {
            "model": self.modelo,
            "messages": [{"role": "system", "content": self.sistema},
                         {"role": "user", "content": nota_numerada(texto)}],
            "temperature": 0, "seed": 35, "max_tokens": 1024,   # modelos que razonan antes de responder
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": "hallazgo", "strict": True, "schema": ESQUEMA_SALIDA}},
        }
        cabeceras = {"Content-Type": "application/json"}
        if self.clave:
            cabeceras["Authorization"] = "Bearer " + self.clave
        req = urllib.request.Request(self.url, data=json.dumps(cuerpo).encode("utf-8"), headers=cabeceras)
        salida: Optional[Dict[str, Any]] = None
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                contenido = json.load(r)["choices"][0]["message"]["content"]
            salida = json_de(contenido)
        except (OSError, http.client.HTTPException, KeyError, IndexError, TypeError, ValueError) as exc:
            # OSError cubre URLError y los timeouts de Python 3.9; ValueError cubre JSON y UTF-8 inválidos.
            salida = {"_error": f"{type(exc).__name__}"}   # → falla la comprobación de forma: sin efecto
        self.grabacion.append({"sha256": h, "salida": salida, "modelo": self.modelo})
        self._vistas[h] = salida
        return salida


def json_de(contenido: Any) -> Any:
    """El JSON de la respuesta; acepta que venga entre ```json … ```. Un contenido vacío es un error (sin efecto)."""
    if not isinstance(contenido, str):
        raise TypeError("respuesta sin contenido")
    t = contenido.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
        t = t.rsplit("```", 1)[0]
    return json.loads(t)


def leer_notas(con: sqlite3.Connection, lector: Lector) -> int:
    """Solo pacientes candidatos y notas de la ventana N1f (≤12 meses, ≤ fecha del extracto). Devuelve nº de notas leídas."""
    notas = con.execute(
        """SELECT n.note_id, n.person_id, n.note_date, n.note_text FROM note n CROSS JOIN ref
           WHERE n.person_id IN (SELECT person_id FROM candidato)
             AND n.note_date <= ref.hoy
             AND n.note_date >= date(ref.hoy, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro
                                                      WHERE clave = 'meses_nota_realizada') || ' months')
           ORDER BY n.note_id"""
    ).fetchall()
    hoy = con.execute("SELECT hoy FROM ref").fetchone()[0]
    modelo = getattr(lector, "modelo", "?")
    for n in notas:
        for h in verificar(n["note_text"], n["note_date"], lector(n["note_text"]), hoy):
            con.execute(
                "INSERT INTO nota_hallazgo (note_id, person_id, note_date, etiqueta, prueba, fecha_cita, cita, valor, "
                "unidad, verificada, motivo_rechazo, modelo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (n["note_id"], n["person_id"], n["note_date"], h["etiqueta"], h["prueba"], h["fecha_cita"],
                 h["cita"], h["valor"], h["unidad"], h["verificada"], h["motivo_rechazo"], modelo))
    return len(notas)
