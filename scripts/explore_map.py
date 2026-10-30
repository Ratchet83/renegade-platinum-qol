"""Affiche tout ce qui concerne une carte : en-tête, textes, scripts, PNJ.

Usage : python explore_map.py <rom.nds> <NOM_CARTE>   (ex : SANDGEM_TOWN_POKECENTER_1F)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt

rom = pt.Rom(sys.argv[1])
arm9 = rom.arm9()
table = pt.find_map_headers(arm9)
print("Table des en-têtes trouvée à ARM9+0x%X" % table)
hid = pt.header_id(sys.argv[2])
h = pt.map_header(arm9, table, hid)
print("En-tête", hid, h)

# Textes
seed, strings = pt.read_msg_archive(rom.narc(pt.TEXTS).files[h["texts"]])
print(f"\n=== Textes (archive {h['texts']}, seed {seed}) ===")
for i, s in enumerate(strings):
    print(f"[{i}] {pt.decode_text(s)!r}")

# Scripts
data = rom.narc(pt.SCRIPTS).files[h["scripts"]]
offsets, hdr = pt.read_script_file(data)
print(f"\n=== Scripts (fichier {h['scripts']}, {len(data)} octets) ===")
for i, o in enumerate(offsets):
    nxt = sorted(x for x in offsets + [len(data)] if x > o)[0]
    print(f"script {i + 1} @0x{o:X}: {data[o:min(nxt, o + 48)].hex(' ')}")

# Événements
sections, trailer = pt.read_events(rom.narc(pt.EVENTS).files[h["events"]])
print(f"\n=== Événements (fichier {h['events']}) : {[len(s) for s in sections]} trailer={len(trailer)} ===")
for raw in sections[1]:
    print(pt.unpack_obj(raw))
