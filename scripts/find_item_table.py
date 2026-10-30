"""Retrouve sItemArchiveIDs (objet -> fiche de données) dans l'ARM9 et affiche quelques entrées."""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C
import pt

c = C.Code(sys.argv[1])
base, data = c.region()
names = [l.strip() for l in open(os.path.join(pt.REF, "generated__items.txt"), encoding="utf-8") if l.strip()]
N = len(names)
for off in range(0, len(data) - N * 8, 2):
    if all(struct.unpack_from("<H", data, off + 8 * i)[0] == i for i in range(1, 100)):
        print(f"sItemArchiveIDs à {base + off:08X}")
        for n in ["MASTER_BALL", "NUGGET", "TM01", "HM01", "POKE_RADAR", "FASHION_CASE", "VS_SEEKER", "TOWN_MAP"]:
            if "ITEM_" + n in names:
                i = names.index("ITEM_" + n)
                print(f"  {n:14s} objet {i:3d} -> fiche {struct.unpack_from('<H', data, off + 8 * i)[0]}")
        break
