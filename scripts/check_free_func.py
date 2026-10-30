"""Vérifie qu'une fonction ARM9 est vraiment morte et mesure sa taille.

Usage : python check_free_func.py <rom> <adresse_hex>
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C

c = C.Code(sys.argv[1])
addr = int(sys.argv[2], 16)
base, data = c.region()

# Fin de fonction : début de la fonction suivante (prochaine cible de BL ou référence)
targets = set(t for _, t in c.bls())
blobs = {"arm9": data}
for ov, o in c.ovs.items():
    targets.update(t for _, t in c.bls(ov))
    blobs[f"ov{ov}"] = bytes(o.data)
nxt = min(t for t in targets if t > addr)
print(f"Fonction {addr:08X} -> prochaine fonction connue {nxt:08X} : {nxt - addr} octets")

bl_into = [(s, t) for s, t in c.bls() if addr <= t < nxt]
for ov in c.ovs:
    bl_into += [(s, t) for s, t in c.bls(ov) if addr <= t < nxt]
print("BL/BLX visant la zone :", [(hex(s), hex(t)) for s, t in bl_into])

hits = []
for name, blob in blobs.items():
    for off in range(0, len(blob) - 3, 2):
        (v,) = struct.unpack_from("<I", blob, off)
        if addr <= (v & ~1) < nxt:
            hits.append((name, off))
print("Mots de 32 bits pointant dans la zone :", hits[:20])
print()
c.print_disasm(addr, 12, stop_at_return=False)
print("...")
c.print_disasm(nxt - 24, 14, stop_at_return=False)
