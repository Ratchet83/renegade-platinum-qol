"""Overlay_LoadByID : appelée avec (movs r0,#id ; movs r1,#2) — on liste et on désassemble."""
import os
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C

c = C.Code(sys.argv[1])
cnt = Counter()
for ov in [None] + list(c.ovs):
    b, blob = c.region(ov)
    for s, t in c.bls(ov):
        prev = blob[s - b - 4:s - b]
        if len(prev) == 4:
            h1, h2 = struct.unpack("<HH", prev)
            # (ldr r0,=ID | adds r0,rX,#0) ; movs r1,#2   ou   movs r1,#2 ; (ldr r0 | adds r0)
            def is_r0(h):
                return (h & 0xFF00) == 0x4800 or (h & 0xFFC7) == 0x1C00
            if (h2 == 0x2102 and is_r0(h1)) or (h1 == 0x2102 and is_r0(h2)):
                cnt[t] += 1
for t, n in cnt.most_common(4):
    print(f"{t:08X} : {n} appels")
t = cnt.most_common(1)[0][0]
print(f"\n--- {t:08X}")
c.print_disasm(t, 80, stop_at_return=False)
