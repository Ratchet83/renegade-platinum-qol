"""Vérifie le Trainer Kit dans la ROM construite."""
import os
import struct
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C
import pt

path = sys.argv[1]
c = C.Code(path)
rom = pt.Rom(path)
ops = {v: k for k, v in pt.opcodes().items()}

print("Table des commandes 0x004-0x006 :", [hex(c.u32(0x020EAC68 + 4 * i)) for i in range(3)])
print("Fonctions du Vs. Recorder       :", [hex(c.u32(0x020EF8B0 + 4 * i)) for i in range(3)])
print("Entrée 22 (Flûte Azur) intacte  :", [hex(c.u32(0x020EF8A4 + 4 * i)) for i in range(3)])

ov = c.ovs[max(c.ovs)]
cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
cs.skipdata = True
start = c.u32(0x020EF8B0) & ~1
print(f"\n=== Code du kit (à partir de {start:08X}) ===")
for ins in cs.disasm(bytes(ov.data[start - ov.ramAddress:]), start):
    if ins.mnemonic in ("bl", "blx", "bx", "ldr", "push", "pop") or ins.address == start:
        print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")

# Script du menu
f = rom.narc(pt.SCRIPTS).files[211]
offs, _ = pt.read_script_file(f)
print(f"\nScripts communs : {len(offs)} entrées ; script 2058 à 0x{offs[58]:X}")
data = f[offs[58]:]
print("  octets :", data[:96].hex(" "))
_, s = pt.read_msg_archive(rom.narc(pt.TEXTS).files[213])
print("  textes :", [pt.decode_text(x) for x in s[132:140]])
for bank in (391, 392, 393, 394):
    _, t = pt.read_msg_archive(rom.narc(pt.TEXTS).files[bank])
    print(f"  objet [{bank}] {pt.decode_text(t[465])!r}")
