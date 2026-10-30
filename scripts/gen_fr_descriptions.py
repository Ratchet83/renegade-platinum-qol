"""Génère traduction/fr/desc_*.json (niveau 2 : descriptions).

- Attaques et talents : associés par numéro ; objets : associés par nom anglais.
- Texte français : version officielle la plus proche de Platine disponible dans PokeAPI
  (Platine, puis Noir/Blanc, puis jeux suivants), recoupé à la largeur des cadres du jeu.
- Une description anglaise modifiée par Renegade (différente de toutes les versions
  officielles anglaises) n'est pas reprise : elle doit être traduite dans
  corrections_descriptions.json (clé = texte anglais de la ROM).

Usage : python gen_fr_descriptions.py <rom anglaise>
"""
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt

API = os.path.join(pt.REF, "pokeapi")
OUT = os.path.join(pt.ROOT, "traduction", "fr")
# Ordre de préférence des versions pour le texte français
VERSION_ORDER = ["9", "10", "8", "11", "14", "15", "16", "17", "18", "20", "25"]

BANKS = [
    ("desc_attaques.json", 646, "Descriptions des attaques", "move_flavor_text", "move_id", "id"),
    ("desc_objets.json", 391, "Descriptions des objets", "item_flavor_text", "item_id", "name"),
    ("desc_talents.json", 612, "Descriptions des talents", "ability_flavor_text", "ability_id", "id"),
]


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower().replace("­", ""))


def flat(s):
    s = s.replace("­\n", "").replace("­", "")
    return re.sub(r"\s+", " ", s).strip()


def wrap(text, width):
    lines, cur = [], ""
    for word in text.split(" "):
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= width:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def load_flavor(csv_name, id_col):
    """{id: {version: {lang: texte}}}"""
    out = {}
    with open(os.path.join(API, csv_name + ".csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["language_id"] in ("5", "9"):
                out.setdefault(row[id_col], {}).setdefault(row["version_group_id"], {})[row["language_id"]] = row["flavor_text"]
    return out


def item_ids_by_name():
    ids = {}
    with open(os.path.join(API, "item_names.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["local_language_id"] == "9":
                ids.setdefault(norm(row["name"]), row["item_id"])
    return ids


def main():
    rom = pt.Rom(sys.argv[1])
    texts = rom.narc(pt.TEXTS)
    _, item_names = pt.read_msg_archive(texts.files[392])
    item_names = [pt.decode_text(x) for x in item_names]
    item_ids = item_ids_by_name()
    corr_path = os.path.join(OUT, "corrections_descriptions.json")
    corrections = json.load(open(corr_path, encoding="utf-8")) if os.path.exists(corr_path) else {}

    for filename, bank, label, csv_name, id_col, key_mode in BANKS:
        flavor = load_flavor(csv_name, id_col)
        _, strings = pt.read_msg_archive(texts.files[bank])
        en_all = [pt.decode_text(x) for x in strings]
        en_lines = [l for t in en_all for l in t.split("\n") if l]
        width = max(len(l) for l in en_lines)
        max_lines = max(len([l for l in t.split("\n") if l]) for t in en_all)
        entries, renegade, too_long = {}, [], []
        for i, en in enumerate(en_all):
            if not flat(en) or flat(en) in ("-", "?", "???"):
                continue
            key = str(i) if key_mode == "id" else item_ids.get(norm(item_names[i]))
            manual = corrections.get(str(bank), {}).get(str(i))
            if manual:
                lines = wrap(flat(manual), width)
                if len(lines) > max_lines:
                    too_long.append((i, len(lines), manual))
                entries[str(i)] = {"en": en, "fr": "\n".join(lines), "source": "manuel"}
                continue
            versions = flavor.get(key, {}) if key else {}
            official_en = {norm(v["9"]) for v in versions.values() if "9" in v}
            if norm(en) not in official_en:
                renegade.append((i, en))
                continue
            fr = None
            for ver in VERSION_ORDER:
                if "5" in versions.get(ver, {}):
                    fr, src = flat(versions[ver]["5"]).replace("'", "’"), ver
                    break
            if fr is None:
                renegade.append((i, en))
                continue
            lines = wrap(fr, width)
            if len(lines) > max_lines:
                too_long.append((i, len(lines), fr))
            entries[str(i)] = {"en": en, "fr": "\n".join(lines), "source": f"version {src}"}
        with open(os.path.join(OUT, filename), "w", encoding="utf-8") as f:
            json.dump({"archive": bank, "categorie": label, "largeur": width, "lignes_max": max_lines,
                       "textes": entries}, f, ensure_ascii=False, indent=1)
        print(f"{label} : {len(entries)} traduites (largeur {width}, {max_lines} lignes max), "
              f"{len(renegade)} propres à Renegade, {len(too_long)} trop longues")
        for i, en in renegade:
            print(f"   R [{i}] {en!r}")
        for i, n, fr in too_long:
            print(f"   L [{i}] {n} lignes : {fr!r}")


if __name__ == "__main__":
    main()
