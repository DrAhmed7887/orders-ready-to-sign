"""Download LivingNER v6.3.1 (CC BY 4.0) and keep only the Spanish case texts (round 13 E2, held-out 2).

    python3 eval/notas_reales/fetch_livingner.py  ->  eval/notas_reales/raw/livingner_<split>/<case>.txt (git-ignored)

Source: Miranda-Escalada A., Farré-Maduell E., Lima-López S., González Gacio G., Krallinger M. LivingNER corpus,
Zenodo, doi:10.5281/zenodo.7684093, licence CC BY 4.0. Published clinical case reports, not patient records. Many
texts are the same SciELO cases as CodiEsp: eval/notas_reales/muestra.py --corpus livingner drops those.
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
URL = "https://zenodo.org/records/7684093/files/livingner-bundle_training_valid_test_background_multilingual.zip?download=1"
SHA256 = "07661ea90ea4c407c60b2dfce8f01b2e773a0cec590680d205cd5cced1d75bd4"
SPLITS = ("training", "valid", "test_background")   # Spanish originals in <split>/text-files/ (test is inside test_background)


def main() -> int:
    with urllib.request.urlopen(URL, timeout=600) as r:
        data = r.read()
    got = hashlib.sha256(data).hexdigest()
    if got != SHA256:
        print(f"SHA-256 mismatch: got {got}, pinned {SHA256}", file=sys.stderr)
        return 1
    n = 0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            parts = Path(info.filename).parts
            if len(parts) >= 3 and parts[-2] == "text-files" and parts[-3] in SPLITS and parts[-1].endswith(".txt"):
                name = Path(parts[-1]).name
                if "/" in name or name.startswith("."):
                    continue
                dest = RAW / f"livingner_{parts[-3]}" / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(info))
                n += 1
    print(f"{n} Spanish case texts -> {RAW.relative_to(ROOT)}/livingner_*")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
