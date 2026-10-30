"""Localise Repel_UpdateSteps (ov6), TryUseRepel (ov84) et le texte « effects linger »."""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C
import pt

path = sys.argv[1]
c = C.Code(path)

# --- ov6 : Repel_UpdateSteps : ldrb ; cmp #0 ; beq ; subs #1 ; strb
base, data = c.region(6)
print(f"ov6 @ {base:08X}")
for off in range(0, len(data) - 10, 2):
    h = struct.unpack_from("<5H", data, off)
    # ldrb rX,[rY] ; cmp rX,#0 ; b.. ; subs rX,#1 (0x38 0x01 = subs r0,#1 ...)
    if (h[0] & 0xF800) == 0x7800 and (h[1] & 0xF8FF) == 0x2800 and (h[2] & 0xFF00) in (0xD000,) \
            and (h[3] & 0xF8FF) == 0x3801:
        print(f"  candidat {base + off:08X}")
        c.print_disasm(base + off - 16, 24, ov=6, stop_at_return=False)

# --- ov84 : comparaisons avec ITEM_REPEL (0x4F), SUPER (0x4C), MAX (0x4D)
base, data = c.region(84)
print(f"\nov84 @ {base:08X}")
for off in range(0, len(data) - 2, 2):
    (h,) = struct.unpack_from("<H", data, off)
    if (h & 0xF8FF) == 0x284D:  # cmp rX, #0x4D (Max Repel)
        print(f"  cmp #0x4D @ {base + off:08X}")
        c.print_disasm(base + off - 30, 60, ov=84, stop_at_return=False)

# --- texte
rom = pt.Rom(path)
narc = rom.narc(pt.TEXTS)
for i, f in enumerate(narc.files):
    try:
        _, strings = pt.read_msg_archive(f)
    except Exception:
        continue
    for j, s in enumerate(strings):
        t = pt.decode_text(s)
        if "Repel" in t and ("linger" in t or "used" in t.lower()):
            print(f"\ntexte archive {i} [{j}] : {t!r}")
