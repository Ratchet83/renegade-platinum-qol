"""Télécharge les fichiers de référence de la décompilation pokeplatinum dans ref/.

Usage : python scripts/fetch_refs.py [--sources]
  --sources : télécharge aussi l'archive complète des sources (≈ 60 Mo, pour l'analyse)
"""
import io
import os
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "ref")
BASE = "https://raw.githubusercontent.com/pret/pokeplatinum/main/"

# Fichiers nécessaires à build_qol.py (pt.py) et aux scripts d'analyse
FILES = [
    "tools/msgenc/charmap.txt",
    "include/data/scripts/scrcmd.h",
    "asm/macros/scrcmd.inc",
    "generated/map_headers.txt",
    "generated/items.txt",
    "generated/object_events_gfx.txt",
    "generated/pokemon_data_params.txt",
    "generated/vars_flags.txt",
    "res/field/scripts/scripts_common.s",
]


def main():
    os.makedirs(REF, exist_ok=True)
    for path in FILES:
        out = os.path.join(REF, path.replace("/", "__"))
        print("->", path)
        urllib.request.urlretrieve(BASE + path, out)

    if "--sources" in sys.argv:
        print("-> archive des sources (src, include, asm, platinum.us)")
        url = "https://codeload.github.com/pret/pokeplatinum/zip/refs/heads/main"
        data = urllib.request.urlopen(url).read()
        z = zipfile.ZipFile(io.BytesIO(data))
        dest = os.path.join(REF, "src_tree")
        for m in z.infolist():
            p = m.filename.split("/", 1)[1] if "/" in m.filename else ""
            if p.startswith(("src/", "include/", "asm/", "platinum.us/")) and not m.is_dir():
                z.extract(m, dest)
    print("Terminé.")


if __name__ == "__main__":
    main()
