"""Trouve NitroMain (via le point d'entrée ARM9) et SetGBACartridgeVersion."""
import os
import struct
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C

c = C.Code(sys.argv[1])
entry = c.rom.arm9EntryAddress
print(f"Point d'entrée ARM9 : {entry:08X}")
arm = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
base, data = c.region()
# crt0 est en ARM ; on cherche le saut final vers NitroMain (ldr rX,=NitroMain ; bx rX)
off = entry - base
cands = []
for ins in arm.disasm(data[off:off + 0x400], entry):
    if ins.mnemonic == "ldr" and "[pc" in ins.op_str:
        imm = int(ins.op_str.split("#")[-1].rstrip("]"), 16) if "#" in ins.op_str else 0
        val = struct.unpack_from("<I", data, ins.address + 8 + imm - base)[0]
        if val & 1 and base <= val < base + len(data):
            cands.append((ins.address, val & ~1))
print("Pointeurs Thumb chargés par crt0 :", [(hex(a), hex(v)) for a, v in cands])
for _, v in cands[-2:]:
    print(f"\n--- {v:08X}")
    c.print_disasm(v, 40, stop_at_return=False)
