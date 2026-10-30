"""Cherche SaveData_Ptr : push ; ldr r0,=g ; ldr r0,[r0] ; cmp r0,#0 ; bne ; bl Assert ; ldr r0,=g ; ldr r0,[r0] ; pop.

Puis vérifie que le global pointé est bien celui écrit par SaveData_Init
(le même global doit être lu par la fonction et pointer vers les mêmes données).
"""
import os
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C

ASSERT = 0x02022974
c = C.Code(sys.argv[1])
base, data = c.region()
callers = Counter(t for _, t in c.bls())
for ov in c.ovs:
    callers.update(t for _, t in c.bls(ov))


def pool(addr, h):
    """Adresse chargée par ldr rX,[pc,#imm] à l'adresse addr."""
    tgt = ((addr + 4) & ~3) + (h & 0xFF) * 4
    return struct.unpack_from("<I", data, tgt - base)[0]


for off in range(0, len(data) - 20, 2):
    h = struct.unpack_from("<10H", data, off)
    a = base + off
    if (h[0] == 0xB508 and (h[1] & 0xFF00) == 0x4800 and h[2] == 0x6800 and h[3] == 0x2800
            and (h[4] & 0xFF00) == 0xD100 and (h[5] & 0xF800) == 0xF000 and (h[7] & 0xFF00) == 0x4800
            and h[8] == 0x6800 and h[9] == 0xBD08):
        g1, g2 = pool(a + 2, h[1]), pool(a + 14, h[7])
        if g1 == g2:
            print(f"{a:08X} global={g1:08X} appels={callers[a]}")
