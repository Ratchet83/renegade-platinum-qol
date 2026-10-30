"""Étape 2 : SaveData_Ptr + les appels « niveau » comparés à 100 (ARM9 et overlay 16)."""
import os
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C

GET_VALUE = 0x02074470
GET_TRAINER_INFO = 0x02025E38
GET_VARS_FLAGS = 0x020507E4
HAS_BADGE = 0x02025F34

c = C.Code(sys.argv[1])

# SaveData_Ptr : fonction sans argument appelée juste avant GetTrainerInfo / GetVarsFlags
base, data = c.region()
bl_at = dict(c.bls())
cnt = Counter()
for site, tgt in bl_at.items():
    if tgt in (GET_TRAINER_INFO, GET_VARS_FLAGS) and (site - 4) in bl_at:
        cnt[bl_at[site - 4]] += 1
print("Candidats SaveData_Ptr :", [(hex(a), n) for a, n in cnt.most_common(4)])
for a, _ in cnt.most_common(1):
    c.print_disasm(a, 12)
print("\nTrainerInfo_HasBadge :")
c.print_disasm(HAS_BADGE, 16)


def level_sites(ov=None):
    base, data = c.region(ov)
    out = []
    for site, tgt in c.bls(ov):
        if tgt != GET_VALUE:
            continue
        before = data[site - base - 6: site - base]
        after = data[site - base + 4: site - base + 10]
        if b"\xa1\x21" in before:  # movs r1, #0xA1 (MON_DATA_LEVEL)
            # cherche cmp rX, #0x64 juste après
            for k in range(0, len(after) - 1, 2):
                h = struct.unpack_from("<H", after, k)[0]
                if (h & 0xF8FF) == 0x2864:
                    out.append(site)
                    break
    return out


for ov in [None, 16]:
    sites = level_sites(ov)
    print(f"\n=== {'ARM9' if ov is None else 'overlay %d' % ov} : {len(sites)} appels GetValue(LEVEL) suivis de cmp #100")
    for s in sites:
        print(f"--- site {s:08X}")
        c.print_disasm(s - 12, 14, ov=ov, stop_at_return=False)
