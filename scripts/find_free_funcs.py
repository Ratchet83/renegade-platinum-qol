"""Croise les fonctions « inutilisées » de la décompilation avec le binaire.

Garde celles qu'aucun BL/BLX ni aucun mot de 32 bits ne référence (ARM9 + overlays),
et affiche leur taille réelle dans la ROM.
"""
import os
import re
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ref", "src_tree", "pokeplatinum-main")

# Fonctions de l'ARM9 à adresse dans le nom
static_objs, in_static = [], False
for line in open(os.path.join(ROOT, "platinum.us", "main.lsf.in"), encoding="utf-8"):
    s = line.strip()
    if s.startswith("Static"):
        in_static = True
    elif s.startswith(("Overlay", "Autoload")):
        in_static = False
    elif in_static and s.startswith("Object"):
        static_objs.append(s.split()[1])
names = set()
for obj in static_objs:
    p = os.path.join(ROOT, obj)
    if p.endswith(".c") and os.path.exists(p):
        names.update(re.findall(r"\bsub_(02[0-9A-F]{6})\b", open(p, encoding="utf-8", errors="ignore").read()))
cands = sorted(int(n, 16) for n in names)

c = C.Code(sys.argv[1])
base, data = c.region()
targets = Counter(t for _, t in c.bls())
blobs = [data]
for ov, o in c.ovs.items():
    targets.update(t for _, t in c.bls(ov))
    blobs.append(bytes(o.data))
refs = Counter()
for blob in blobs:
    for off in range(0, len(blob) - 3, 2):
        (v,) = struct.unpack_from("<I", blob, off)
        if base <= v < base + len(data):
            refs[v & ~1] += 1
starts = sorted(set(targets) | set(refs))

import bisect
free = []
for a in cands:
    if targets[a] or refs[a]:
        continue
    nxt = starts[bisect.bisect_right(starts, a)]
    inside = [hex(x) for x in range(a + 2, nxt, 2) if targets[x] or refs[x]]
    free.append((nxt - a, a, nxt, inside))
free.sort(reverse=True)
print(f"{len(cands)} fonctions sub_02xxxxxx dans l'ARM9, {len(free)} jamais référencées au début :")
for size, a, nxt, inside in free[:25]:
    print(f"  {a:08X}-{nxt:08X} : {size} octets  refs internes={inside[:4]}")
