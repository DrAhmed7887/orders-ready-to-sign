"""Download CodiEsp v1.4 (CC BY 4.0) and keep only the Spanish case texts.

    python3 eval/notas_reales/fetch.py   ->  eval/notas_reales/raw/<split>/<case>.txt  (git-ignored)

Source: Miranda-Escalada A., Gonzalez-Agirre A., Armengol-Estapé J., Krallinger M. CodiEsp corpus: Spanish clinical
cases coded in ICD10 (CIE10), eHealth CLEF 2020, Zenodo, doi:10.5281/zenodo.3837305, licence CC BY 4.0.
Published clinical case reports from open-access SciELO journals, not patient records.
"""
from __future__ import annotations

import hashlib
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "eval" / "notas_reales" / "raw"
URL = "https://zenodo.org/records/3837305/files/codiesp.zip?download=1"
SHA256 = "52b290233906a2eb589ac7b1d9429adeac88f6a9cae8b0d3c180504afbe61688"
SPLITS = ("train", "dev", "test", "background")


def main() -> int:
    with urllib.request.urlopen(URL, timeout=300) as r:
        data = r.read()
    got = hashlib.sha256(data).hexdigest()
    if got != SHA256:
        print(f"SHA-256 mismatch: got {got}, pinned {SHA256}", file=sys.stderr)
        return 1
    n = 0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            parts = Path(info.filename).parts
            # .../<split>/text_files/<case>.txt  (the Spanish originals; text_files_en are machine translations)
            if len(parts) >= 3 and parts[-2] == "text_files" and parts[-3] in SPLITS and parts[-1].endswith(".txt"):
                name = Path(parts[-1]).name
                if "/" in name or name.startswith("."):
                    continue
                out = RAW / parts[-3] / name
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(z.read(info))
                n += 1
    print(f"{n} Spanish case texts in {RAW.relative_to(ROOT)} (SHA-256 matches)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
