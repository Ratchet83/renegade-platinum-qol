"""Compare le code (ARM9 + overlays) de Platine d'origine et de Renegade."""
import os
import sys

import ndspy.codeCompression
import ndspy.rom

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
orig = ndspy.rom.NintendoDSRom.fromFile(os.path.join(ROOT, "original", "Pokemon - Platinum Version (USA) (Rev 1).nds"))
ren = ndspy.rom.NintendoDSRom.fromFile(os.path.join(ROOT, "travail", "renegade_base.nds"))

a9o = ndspy.codeCompression.decompress(orig.arm9)
a9r = ndspy.codeCompression.decompress(ren.arm9)
print(f"ARM9 : orig {len(a9o)} / renegade {len(a9r)} octets, compressé orig={len(orig.arm9)} ren={len(ren.arm9)}")
diffs = [i for i in range(min(len(a9o), len(a9r))) if a9o[i] != a9r[i]]
print(f"  octets différents : {len(diffs)}")
# regroupe les zones modifiées
zones = []
for i in diffs:
    if zones and i - zones[-1][1] <= 16:
        zones[-1][1] = i
    else:
        zones.append([i, i])
for s, e in zones[:80]:
    print(f"  0x{0x02000000 + s:08X}-0x{0x02000000 + e:08X} ({e - s + 1} o)")
if len(zones) > 80:
    print(f"  ... {len(zones)} zones au total")

ovo = orig.loadArm9Overlays()
ovr = ren.loadArm9Overlays()
print("\nOverlays :", len(ovo), "/", len(ovr))
for i in sorted(ovr):
    o, r = ovo.get(i), ovr[i]
    if o is None:
        print(f"  ov{i:03d} NOUVEAU ram=0x{r.ramAddress:08X} taille={len(r.data)}")
        continue
    if o.data != r.data or o.ramAddress != r.ramAddress or len(o.data) != len(r.data):
        nd = sum(1 for x, y in zip(o.data, r.data) if x != y)
        print(f"  ov{i:03d} modifié ram=0x{r.ramAddress:08X} taille {len(o.data)}->{len(r.data)} "
              f"bss {o.bssSize}->{r.bssSize} octets diff={nd}")
