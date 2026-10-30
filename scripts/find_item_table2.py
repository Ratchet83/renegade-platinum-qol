"""Retrouve Item_Load et la table sItemArchiveIDs via le nom de fichier « pl_item_data.narc »."""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C

c = C.Code(sys.argv[1])
base, data = c.region()
s = data.find(b"itemtool/itemdata/pl_item_data.narc")
print(f"chaîne à {base + s:08X}")
# table de pointeurs vers les chemins des NARC
ptr = struct.pack("<I", base + s)
p = data.find(ptr)
# remonter au début de la table : pointeurs consécutifs vers des chaînes
start = p
while True:
    (v,) = struct.unpack_from("<I", data, start - 4)
    if base <= v < base + len(data) and data[v - base:v - base + 1].isalpha():
        start -= 4
    else:
        break
idx = (p - start) // 4
print(f"table des chemins à {base + start:08X}, index NARC de pl_item_data = {idx}")

# Fonctions qui chargent ce NARC : « movs r0,#idx » ou « ldr r0,=idx » juste avant un BL
for site, tgt in c.bls():
    prev = data[site - base - 8:site - base]
    hs = struct.unpack("<4H", prev)
    if any(h == (0x2000 | idx) for h in hs) and idx < 256:
        print(f"  appel {site:08X} -> {tgt:08X}")
