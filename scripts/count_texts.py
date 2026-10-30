"""Compte les textes du jeu : total, et archives « noms » (Pokémon, attaques, objets, talents, lieux…)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt

rom = pt.Rom(sys.argv[1])
narc = rom.narc(pt.TEXTS)
banks = []
for i, f in enumerate(narc.files):
    try:
        _, s = pt.read_msg_archive(f)
    except Exception:
        continue
    texts = [pt.decode_text(x) for x in s]
    banks.append((i, texts))


def find(pred):
    return [i for i, t in banks if pred(t)]


probes = {
    "Pokémon (noms)": lambda t: len(t) > 490 and t[1:4] == ["Bulbasaur", "Ivysaur", "Venusaur"],
    "Attaques (noms)": lambda t: len(t) > 460 and t[1:3] == ["Pound", "Karate Chop"],
    "Objets (noms)": lambda t: len(t) > 460 and t[1] == "Master Ball" and t[4] == "Poké Ball",
    "Talents (noms)": lambda t: len(t) > 120 and t[1:3] == ["Stench", "Drizzle"],
    "Natures": lambda t: 20 <= len(t) <= 30 and t[0] in ("Hardy", "HARDY"),
    "Lieux": lambda t: any(x == "Twinleaf Town" for x in t) and any(x == "Sandgem Town" for x in t),
}
total_str = sum(len(t) for _, t in banks)
total_chr = sum(sum(len(x) for x in t) for _, t in banks)
print(f"Total : {len(banks)} archives, {total_str} textes, {total_chr} caractères")
names = set()
for label, pred in probes.items():
    ids = find(pred)
    names.update(ids)
    for i in ids:
        t = dict(banks)[i]
        print(f"  {label:18s} archive {i:3d} : {len(t)} textes, {sum(len(x) for x in t)} car.")

# Archives voisines des noms (descriptions d'attaques / objets / talents)
for label, i in [("Desc. attaques ?", 646), ("Desc. talents ?", 610)]:
    pass
small = [(i, t) for i, t in banks if i not in names]
print(f"\nHors noms : {sum(len(t) for _, t in small)} textes, {sum(sum(len(x) for x in t) for _, t in small)} caractères")
