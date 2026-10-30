"""Liste les positions des PNJ dans tous les Centres Pokémon 1F (même plan de salle)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt

rom = pt.Rom(sys.argv[1])
arm9 = rom.arm9()
table = pt.find_map_headers(arm9)
names = [l.strip() for l in open(os.path.join(pt.REF, "generated__map_headers.txt"), encoding="utf-8") if l.strip()]
for hid, name in enumerate(names):
    if not name.endswith("POKECENTER_1F"):
        continue
    h = pt.map_header(arm9, table, hid)
    sections, _ = pt.read_events(rom.narc(pt.EVENTS).files[h["events"]])
    pos = sorted((o["x"], o["z"]) for o in map(pt.unpack_obj, sections[1]))
    print(f"{name:45s} matrix={h['matrix']:3d} area={h['area']:3d} {pos}")
