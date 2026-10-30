"""Infos sur les scripts communs : archive de textes, fichier de scripts, macros utiles."""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt

rom = pt.Rom(sys.argv[1])
texts = rom.narc(pt.TEXTS)
for i, f in enumerate(texts.files):
    try:
        _, s = pt.read_msg_archive(f)
    except Exception:
        continue
    for j, codes in enumerate(s):
        t = pt.decode_text(codes)
        if "booted up the PC" in t or "Accessed Pokémon Storage" in t.replace("\n", " "):
            print(f"archive {i} ({len(s)} textes) [{j}] {t!r}")

# Fichier des scripts communs : celui dont l'entrée n°18 (0x7E2, PC) commence par LockAll ; PlaySE
scripts = rom.narc(pt.SCRIPTS)
for i, f in enumerate(scripts.files):
    try:
        offs, _ = pt.read_script_file(f)
    except Exception:
        continue
    if len(offs) > 40 and f[offs[18]:offs[18] + 4] == bytes.fromhex("6000 4900"):
        print(f"scripts communs : fichier {i}, {len(offs)} entrées, {len(f)} octets")
