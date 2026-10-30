"""Cherche dans tous les scripts de la ROM des séquences de commandes, pour en récupérer les arguments.

- FadeScreen (+8 octets) ; WaitFadeScreen ; OpenRegionMap
- PlayFanfare (+2) ; WaitFanfare ; HealParty
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt

o = pt.opcodes()
op = lambda n: struct.pack("<H", o["SCRCMD_" + n])
rom = pt.Rom(sys.argv[1])
scripts = rom.narc(pt.SCRIPTS)

found = {}
for i, f in enumerate(scripts.files):
    # fondu + carte
    k = f.find(op("WAITFADESCREEN") + op("OPENREGIONMAP"))
    if k >= 10 and f[k - 10:k - 8] == op("FADESCREEN") and "fade" not in found:
        found["fade"] = (i, f[k - 10:k].hex(" "), f[k + 4:k + 20].hex(" "))
    k = f.find(op("WAITFANFARE") + op("HEALPARTY"))
    if k >= 4 and f[k - 4:k - 2] == op("PLAYFANFARE") and "heal" not in found:
        found["heal"] = (i, f[k - 4:k].hex(" "))
for k, v in found.items():
    print(k, v)
print({n: hex(o["SCRCMD_" + n]) for n in ["FADESCREEN", "WAITFADESCREEN", "OPENREGIONMAP", "RETURNTOFIELD",
                                            "PLAYFANFARE", "WAITFANFARE", "HEALPARTY", "OPENPOKEMONSTORAGE",
                                            "INITLOCALTEXTMENU", "ADDMENUENTRYIMM", "SHOWMENU", "CHECKBADGEACQUIRED",
                                            "UNUSED_004", "UNUSED_005", "UNUSED_006"]})
