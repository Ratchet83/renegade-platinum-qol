"""Affiche le prix et la taille de quelques fiches d'objets (vérifie l'indexation)."""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt

names = [l.strip() for l in open(os.path.join(pt.REF, "generated__items.txt"), encoding="utf-8") if l.strip()]
rom = pt.Rom(sys.argv[1])
narc = rom.narc("itemtool/itemdata/pl_item_data.narc")
print("fiches :", len(narc.files), "| objets connus :", len(names))
for n in sys.argv[2:]:
    n = "ITEM_" + n
    if n in names:
        i = names.index(n)
        price = struct.unpack_from("<H", narc.files[i], 0)[0]
        print(f"{n:24s} {i:4d} prix={price} taille={len(narc.files[i])}")
    else:
        print(n, "inconnu")
