"""Callers de SetGBACartridgeVersion + localisation de Overlay_LoadByID / FS_LoadOverlay."""
import os
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C

SET_GBA = 0x02017B70
c = C.Code(sys.argv[1])
base, data = c.region()

all_bls = [(None, s, t) for s, t in c.bls()]
for ov in c.ovs:
    all_bls += [(ov, s, t) for s, t in c.bls(ov)]
print("Appels à SetGBACartridgeVersion :", [(ov, hex(s)) for ov, s, t in all_bls if t == SET_GBA])
refs = [off for off in range(0, len(data) - 3, 2) if struct.unpack_from("<I", data, off)[0] in (SET_GBA, SET_GBA | 1)]
print("Pointeurs vers elle :", [hex(base + r) for r in refs])

# Overlay_LoadByID(id, type) : appelée très souvent avec « movs r0,#id ; movs r1,#2 » (chargement asynchrone)
cnt = Counter()
for ov, s, t in all_bls:
    blob = c.region(ov)[1]
    b = c.region(ov)[0]
    prev = blob[s - b - 4:s - b]
    if len(prev) == 4:
        h1, h2 = struct.unpack("<HH", prev)
        if (h1 & 0xFF00) == 0x2000 and (h2 & 0xFF00) == 0x2100 and (h2 & 0xFF) <= 2:
            cnt[t] += 1
print("\nCibles appelées avec (movs r0,#imm ; movs r1,#0..2) :")
for t, n in cnt.most_common(5):
    print(f"  {t:08X} : {n}")
loader = cnt.most_common(1)[0][0]
print(f"\n--- Overlay_LoadByID probable : {loader:08X}")
c.print_disasm(loader, 70, stop_at_return=False)
