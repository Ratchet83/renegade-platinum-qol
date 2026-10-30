"""Étape 3 : SaveData_Ptr (fonction « ldr r0,=global ; ldr r0,[r0] ») + détails des sites."""
import os
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C

GET_VALUE = 0x02074470
GET_TRAINER_INFO = 0x02025E38
GET_VARS_FLAGS = 0x020507E4

c = C.Code(sys.argv[1])
base, data = c.region()
bl_at = dict(c.bls())

cnt = Counter()
for site, tgt in bl_at.items():
    if tgt in (GET_TRAINER_INFO, GET_VARS_FLAGS):
        for back in (4, 6, 8):
            if (site - back) in bl_at:
                cnt[bl_at[site - back]] += 1
                break
print("Fonctions appelées juste avant GetTrainerInfo/GetVarsFlags :")
for a, n in cnt.most_common(6):
    ins = c.disasm(a, 6)
    print(f"  {a:08X} ({n}x) : " + " | ".join(f"{i.mnemonic} {i.op_str}" for i in ins))

print("\n--- overlay 16, site 02249004")
c.print_disasm(0x02248FF8, 16, ov=16, stop_at_return=False)

print("\n--- ARM9 : tous les GetValue(LEVEL) entre 0x02096580 et 0x02097400")
for site, tgt in sorted(bl_at.items()):
    if 0x02096580 <= site < 0x02097400 and tgt == GET_VALUE:
        if data[site - base - 4: site - base - 2] == b"\xa1\x21" or data[site - base - 2: site - base] == b"\xa1\x21":
            print(f"site {site:08X}")
            c.print_disasm(site - 6, 20, stop_at_return=False)
