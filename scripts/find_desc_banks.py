"""Trouve les archives de descriptions (attaques, objets, talents) en comparant avec PokeAPI (Platine, anglais)."""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt

API = os.path.join(pt.REF, "pokeapi")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower().replace("­", ""))


def platinum_en(csv_name, id_col, ver_col):
    out = {}
    with open(os.path.join(API, csv_name + ".csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row[ver_col] == "9" and row["language_id"] == "9":
                out[int(row[id_col])] = norm(row["flavor_text"])
    return out


rom = pt.Rom(sys.argv[1])
narc = rom.narc(pt.TEXTS)
targets = {
    "attaques": platinum_en("move_flavor_text", "move_id", "version_group_id"),
    "talents": platinum_en("ability_flavor_text", "ability_id", "version_group_id"),
}
for i, f in enumerate(narc.files):
    try:
        _, s = pt.read_msg_archive(f)
    except Exception:
        continue
    d = [norm(pt.decode_text(x)) for x in s]
    for label, ref in targets.items():
        hits = sum(1 for k, v in ref.items() if k < len(d) and d[k] == v)
        if hits > 50:
            print(f"{label} : archive {i} ({len(d)} textes), {hits}/{len(ref)} identiques à Platine")
