"""Download the public NHANES files this evaluation uses and pin them by SHA-256.

    python3 eval/nhanes/fetch.py            # download into eval/nhanes/raw/ and check against MANIFEST.json
    python3 eval/nhanes/fetch.py --update   # (re)write MANIFEST.json from what was downloaded

Public CDC/NCHS data, no account or key. Raw files are git-ignored; MANIFEST.json is committed, so a different
file (CDC revises files now and then) is reported, never silently used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
MANIFEST = HERE / "MANIFEST.json"
BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{name}.xpt"
CYCLES = {
    "2021": ["DEMO_L", "BIOPRO_L", "ALB_CR_L", "DIQ_L", "BPQ_L", "KIQ_U_L"],   # primary (+ "ever told weak/failing kidneys")
    "2009": ["DEMO_F", "BIOPRO_F", "ALB_CR_F", "DIQ_F", "BPQ_F"],              # secondary: the only cycle with a 2nd urine ACR
    "2017": ["P_DEMO", "P_BIOPRO", "P_ALB_CR", "P_DIQ", "P_BPQ", "P_KIQ_U", "P_RXQ_RX"],  # people.py: last cycle with drug names
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "nhanes-eval/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310 (fixed https CDC URL)
        data = r.read()
    if not data.startswith(b"HEADER RECORD"):
        raise RuntimeError(f"{url}: not a SAS transport (XPT) file")
    dest.write_bytes(data)


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--update", action="store_true", help="rewrite MANIFEST.json from the downloaded files")
    args = ap.parse_args(argv)
    RAW.mkdir(exist_ok=True)
    pinned = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    seen, mismatches = {}, []
    for year, names in CYCLES.items():
        for name in names:
            url = BASE.format(year=year, name=name)
            dest = RAW / f"{name}.xpt"
            if not dest.exists():
                print(f"downloading {url}")
                download(url, dest)
            digest = sha256(dest)
            seen[name] = {"url": url, "sha256": digest, "bytes": dest.stat().st_size}
            if name in pinned and pinned[name]["sha256"] != digest:
                mismatches.append(name)
    if args.update or not pinned:
        for v in seen.values():
            v["pinned_on"] = str(date.today())
        MANIFEST.write_text(json.dumps(seen, indent=2) + "\n")
        print(f"wrote {MANIFEST.relative_to(HERE.parent.parent)}")
    if mismatches and not args.update:
        print("WARNING: these files differ from MANIFEST.json (CDC may have revised them): " + ", ".join(mismatches))
        return 2
    print("all files match MANIFEST.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
