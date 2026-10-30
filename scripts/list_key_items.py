"""Liste les objets rares : numéro, fiche, prix, fonction d'utilisation, poche, nom en jeu."""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code as C
import pt

ITEM_TABLE = 0x020F0CC4
path = sys.argv[1]
c = C.Code(path)
rom = pt.Rom(path)
names = [l.strip() for l in open(os.path.join(pt.REF, "generated__items.txt"), encoding="utf-8") if l.strip()]
narc = rom.narc("itemtool/itemdata/pl_item_data.narc")

# Archive de texte des noms d'objets : celle qui contient « Master Ball » à l'index 1
texts = rom.narc(pt.TEXTS)
name_bank = None
for i, f in enumerate(texts.files):
    try:
        _, s = pt.read_msg_archive(f)
    except Exception:
        continue
    if len(s) > 460 and pt.decode_text(s[1]) == "Master Ball" and pt.decode_text(s[4]) == "Poké Ball":
        name_bank = (i, s)
        break
print("Archive des noms d'objets :", name_bank[0])

for item in range(int(sys.argv[2]), int(sys.argv[3]) + 1):
    data_id, icon, pal, gen3 = struct.unpack_from("<4H", c.arm9, ITEM_TABLE - 0x02000000 + item * 8)
    d = narc.files[data_id]
    price = struct.unpack_from("<H", d, 0)[0]
    bits = struct.unpack_from("<H", d, 8)[0]
    field_use = d[10]
    print(f"{item:3d} {names[item]:22s} fiche={data_id:3d} icône={icon:3d} prix={price:5d} "
          f"bits=0x{bits:04X} fieldUse={field_use:2d} nom={pt.decode_text(name_bank[1][item])!r}")
