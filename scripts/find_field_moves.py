"""Localise FieldMove_GetTaskOrError, la table fieldMoveTaskOrError et FieldMoves_CheckFly."""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C

c = C.Code(sys.argv[1])
for ov in [None] + sorted(c.ovs):
    base, data = c.region(ov)
    for off in range(0, len(data) - 24, 2):
        h = struct.unpack_from("<12H", data, off)
        # cmp r0,#0 ; bne
        if h[0] != 0x2800 or (h[1] & 0xFF00) != 0xD100:
            continue
        window = h[2:10]
        if 0x00C9 in window and 0x4770 in window:
            a = base + off
            print(f"candidat {'ARM9' if ov is None else 'ov%d' % ov} {a:08X}")
            c.print_disasm(a, 12, ov=ov, stop_at_return=False)
