"""Retrouve les adresses utiles au level cap dans la ROM (ARM9 + overlay 16)."""
import os
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C
import pt

c = C.Code(sys.argv[1])
ops = pt.opcodes()

# 1) Table des commandes de script (839 entrées)
tables = []
for ov in [None] + sorted(c.ovs):
    for addr, n in C.find_pointer_table(c, 839, ov=ov, min_len=800):
        tables.append((ov, addr, n))
print("Tables candidates :", [(ov, hex(a), n) for ov, a, n in tables])
ov_t, tbl, _ = tables[0]


def scrcmd(name):
    return c.u32(tbl + 4 * ops["SCRCMD_" + name], ov=ov_t) & ~1


for name in ["COUNTBADGESACQUIRED", "CHECKGAMECOMPLETED"]:
    a = scrcmd(name)
    print(f"\n== ScrCmd {name} @ {a:08X}")
    c.print_disasm(a, 40)

# 2) Pokemon_GetValue : la cible de BL la plus appelée avec r1 = constante et r2 = 0
base, data = c.region()
counter = Counter()
for site, tgt in c.bls():
    prev = data[site - base - 4: site - base]
    if len(prev) == 4:
        h1, h2 = struct.unpack("<HH", prev)
        # movs r1,#imm ; movs r2,#0   (dans un ordre ou l'autre)
        if ((h1 & 0xFF00) == 0x2100 and h2 == 0x2200) or (h1 == 0x2200 and (h2 & 0xFF00) == 0x2100):
            counter[tgt] += 1
print("\nCibles les plus appelées avec (r1=imm, r2=0) :")
for tgt, n in counter.most_common(5):
    print(f"  {tgt:08X} : {n} appels")
