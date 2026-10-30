"""Écrit une archive de textes dans un fichier (un texte par bloc), pour relecture / traduction.

Usage : python dump_bank.py <rom> <archive> <fichier de sortie>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt

rom = pt.Rom(sys.argv[1])
_, s = pt.read_msg_archive(rom.narc(pt.TEXTS).files[int(sys.argv[2])])
with open(sys.argv[3], "w", encoding="utf-8") as f:
    for i, codes in enumerate(s):
        f.write(f"[{i}] {pt.decode_text(codes)!r}\n")
print(len(s), "textes écrits")
