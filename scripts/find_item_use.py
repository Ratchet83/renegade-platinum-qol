"""Localise les fonctions d'utilisation de la Flûte Azur (script 2039) et la table sItemUseFuncs."""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C

c = C.Code(sys.argv[1])
base, data = c.region()
bl_at = dict(c.bls())

hits = []
for off in range(0, len(data) - 8, 2):
    (h,) = struct.unpack_from("<H", data, off)
    if (h & 0xF800) == 0x4800:  # ldr rX,[pc,#imm]
        a = base + off
        lit = ((a + 4) & ~3) + (h & 0xFF) * 4
        if base <= lit < base + len(data) - 4 and struct.unpack_from("<I", data, lit - base)[0] == 0x7F7:
            reg = (h >> 8) & 7
            # BL dans les 3 instructions suivantes
            for k in (2, 4, 6):
                if a + k in bl_at:
                    hits.append((a, reg, bl_at[a + k]))
                    break
for a, reg, tgt in hits:
    print(f"ldr r{reg},=0x7F7 @ {a:08X} -> bl {tgt:08X}")
    c.print_disasm(a - 6, 8, stop_at_return=False)

# Table : 26 entrées de 3 pointeurs ; l'entrée 22 (Flûte Azur) pointe vers les fonctions ci-dessus
funcs = set()
for a, reg, tgt in hits:
    # début de fonction : remonter jusqu'au push
    p = a
    while (struct.unpack_from("<H", data, p - base)[0] & 0xFF00) != 0xB500:
        p -= 2
    funcs.add(p)
print("Fonctions Flûte Azur :", [hex(f) for f in sorted(funcs)])
for off in range(0, len(data) - 12, 4):
    v = struct.unpack_from("<3I", data, off)
    if (v[0] & ~1) in funcs and (v[1] & ~1) in funcs:
        tbl = base + off - 22 * 12
        print(f"Entrée Flûte Azur à {base + off:08X} -> table sItemUseFuncs à {tbl:08X}")
        for i in range(26):
            e = struct.unpack_from("<3I", data, tbl - base + i * 12)
            print(f"  [{i:2d}] " + " ".join(f"{x:08X}" for x in e))
