"""Compare deux ROM : liste les fichiers (et sous-fichiers NARC) qui ont changé."""
import sys

import ndspy.narc
import ndspy.rom

a = ndspy.rom.NintendoDSRom.fromFile(sys.argv[1])
b = ndspy.rom.NintendoDSRom.fromFile(sys.argv[2])
print("ARM9 identique :", a.arm9 == b.arm9, "| ARM7 identique :", a.arm7 == b.arm7,
      "| overlays identiques :", a.arm9OverlayTable == b.arm9OverlayTable)
print("Nombre de fichiers :", len(a.files), "->", len(b.files))
for i, (fa, fb) in enumerate(zip(a.files, b.files)):
    if fa == fb:
        continue
    name = a.filenames.filenameOf(i) or f"(fichier {i})"
    detail = ""
    if fa[:4] == b"NARC":
        na, nb = ndspy.narc.NARC(fa), ndspy.narc.NARC(fb)
        changed = [j for j, (x, y) in enumerate(zip(na.files, nb.files)) if x != y]
        detail = f" -> sous-fichiers modifiés : {changed}"
    print(f"  {name}{detail}")
