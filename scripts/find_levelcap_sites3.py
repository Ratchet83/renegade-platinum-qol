"""Étape 4 : candidats SaveData_Ptr (petites fonctions renvoyant un pointeur global) + site ov16."""
import os
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C

c = C.Code(sys.argv[1])
base, data = c.region()

callers = Counter(t for _, t in c.bls())
for ov in c.ovs:
    callers.update(t for _, t in c.bls(ov))

cands = []
for off in range(0, len(data) - 16, 2):
    h = struct.unpack_from("<8H", data, off)
    addr = base + off
    # forme A : ldr r0,[pc,#x] ; ldr r0,[r0] ; bx lr
    # forme B : push {r3,lr} ; ldr r0,[pc,#x] ; ldr r0,[r0] ; cmp r0,#0 ; ...
    if (h[0] & 0xFF00) == 0x4800 and h[1] == 0x6800 and h[2] == 0x4770:
        cands.append(addr)
    elif h[0] == 0xB508 and (h[1] & 0xFF00) == 0x4800 and h[2] == 0x6800 and h[3] == 0x2800:
        cands.append(addr)
cands.sort(key=lambda a: -callers[a])
print("Candidats (getter de global) les plus appelés :")
for a in cands[:8]:
    print(f"\n{a:08X} : {callers[a]} appels")
    c.print_disasm(a, 12)

print("\n--- overlay 16, autour du site 02249004")
c.print_disasm(0x02248FF0, 24, ov=16, stop_at_return=False)
