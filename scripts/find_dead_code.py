"""Cherche des fonctions mortes dans l'ARM9 (jamais appelées, jamais référencées).

Une zone est retenue si :
- elle commence par un « push {..., lr} » ;
- aucune instruction BL/BLX (ARM9 + tous les overlays) ne vise le début de la zone ;
- aucun mot de 32 bits (ARM9 + overlays) ne contient une adresse de la zone.
Usage : python find_dead_code.py <rom> [adresse_hex_a_desassembler]
"""
import bisect
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C

c = C.Code(sys.argv[1])
base, data = c.region()
end = base + len(data)

if len(sys.argv) > 2:
    c.print_disasm(int(sys.argv[2], 16), int(sys.argv[3]) if len(sys.argv) > 3 else 200, stop_at_return=False)
    sys.exit()

targets = set(t for _, t in c.bls())
for ov in c.ovs:
    targets.update(t for _, t in c.bls(ov))

refs = set()
for blob in [data] + [bytes(o.data) for o in c.ovs.values()]:
    for off in range(0, len(blob) - 3, 2):
        (v,) = struct.unpack_from("<I", blob, off)
        if base <= v < end:
            refs.add(v & ~1)
print("cibles BL :", len(targets), "| références :", len(refs))

starts = sorted(t for t in targets | refs if base <= t < end)
results = []
for off in range(0, len(data) - 2, 2):
    a = base + off
    (h,) = struct.unpack_from("<H", data, off)
    if (h & 0xFF00) != 0xB500 or a in targets or a in refs:
        continue
    i = bisect.bisect_right(starts, a)
    nxt = starts[i] if i < len(starts) else end
    size = nxt - a
    if 64 <= size <= 4000:
        results.append((size, a, nxt))

results.sort(reverse=True)
print(f"{len(results)} zones candidates. Les 15 plus grandes :")
for size, a, nxt in results[:15]:
    print(f"  {a:08X}-{nxt:08X} ({size} octets)")
