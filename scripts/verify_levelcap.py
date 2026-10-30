"""Vérifie le level cap dans la ROM construite : table des overlays, module, appels."""
import os
import struct
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C

c = C.Code(sys.argv[1])
ov = c.ovs[max(c.ovs)]
print(f"Overlay {max(c.ovs)} : ram=0x{ov.ramAddress:08X} taille={len(ov.data)} bss={ov.bssSize} "
      f"flags={ov.flags} fichier={ov.fileID}")
print(f"Overlay 16 : flags={c.ovs[16].flags} taille={len(c.ovs[16].data)}")

cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
cs.skipdata = True
print("\n=== Module level cap ===")
for ins in cs.disasm(bytes(ov.data), ov.ramAddress):
    print(f"  {ins.address:08X}: {ins.bytes.hex():10s} {ins.mnemonic} {ins.op_str}")

print("\n=== Sites modifiés ===")
for where, addr, n in [(None, 0x02000C90, 10), (None, 0x02096564, 6), (None, 0x02096AA0, 6),
                       (16, 0x02248FFE, 6), (16, 0x022490E4, 5)]:
    print(f"-- {'ARM9' if where is None else 'ov%d' % where} {addr:08X}")
    c.print_disasm(addr, n, ov=where, stop_at_return=False)
