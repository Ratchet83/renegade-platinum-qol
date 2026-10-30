"""Génère traduction/fr/*.json (niveau 1 : noms) à partir des noms officiels (PokeAPI).

Pour chaque archive de noms de la ROM anglaise :
- on cherche le nom anglais dans PokeAPI (comparaison sans espaces, tirets, accents ni casse),
- on prend le nom français correspondant,
- les noms introuvables ou trop longs sont signalés et repris de traduction/fr/corrections.json.

Usage : python gen_fr_names.py <rom anglaise>
"""
import csv
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt

API = os.path.join(pt.REF, "pokeapi")
OUT = os.path.join(pt.ROOT, "traduction", "fr")
EN, FR = "9", "5"

# Archives de noms : (fichier, catégorie, CSV PokeAPI, colonne id, longueur max)
BANKS = [
    ("pokemon.json", 412, "Pokémon", "pokemon_species_names", "pokemon_species_id", 10),
    ("attaques.json", 647, "Attaques", "move_names", "move_id", 15),
    ("objets.json", 392, "Objets", "item_names", "item_id", 15),
    ("talents.json", 610, "Talents", "ability_names", "ability_id", 15),
    ("natures.json", 202, "Natures", "nature_names", "nature_id", 12),
    ("lieux.json", 433, "Lieux", "location_names", "location_id", 16),
]


# Archives traduites à la main (pas dans PokeAPI sous cette forme)
MANUAL = [
    ("types.json", 624, "Types", 10, {
        "NORMAL": "NORMAL", "FIGHTING": "COMBAT", "FLYING": "VOL", "POISON": "POISON",
        "GROUND": "SOL", "ROCK": "ROCHE", "BUG": "INSECTE", "GHOST": "SPECTRE", "STEEL": "ACIER",
        "FAIRY": "FÉE", "FIRE": "FEU", "WATER": "EAU", "GRASS": "PLANTE", "ELECTRIC": "ÉLECTRIK",
        "PSYCHIC": "PSY", "ICE": "GLACE", "DRAGON": "DRAGON", "DARK": "TÉNÈBRES",
    }),
    ("statistiques.json", 551, "Statistiques", 12, {
        "HP": "PV", "Attack": "Attaque", "Defense": "Défense", "Speed": "Vitesse",
        "Sp. Atk": "Atq. Spé.", "Sp. Def": "Déf. Spé.", "accuracy": "précision",
        "evasiveness": "esquive", "Max. HP": "PV max.",
    }),
]


def norm(s):
    s = unicodedata.normalize("NFKD", s.replace("’", "'"))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]", "", s.lower())


def load_map(csv_name, id_col):
    en, fr = {}, {}
    with open(os.path.join(API, csv_name + ".csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lang = row.get("local_language_id")
            if lang == EN:
                en[row[id_col]] = row["name"]
            elif lang == FR:
                fr[row[id_col]] = row["name"]
    by_name = {}
    for i, name in en.items():
        if i in fr:
            by_name.setdefault(norm(name), fr[i])
    return by_name


def main():
    rom = pt.Rom(sys.argv[1])
    texts = rom.narc(pt.TEXTS)
    os.makedirs(OUT, exist_ok=True)
    corr_path = os.path.join(OUT, "corrections.json")
    corrections = json.load(open(corr_path, encoding="utf-8")) if os.path.exists(corr_path) else {}

    report = []
    jobs = [(f, b, l, load_map(c, i), m) for f, b, l, c, i, m in BANKS]
    jobs += [(f, b, l, {norm(k): v for k, v in table.items()}, m) for f, b, l, m, table in MANUAL]
    for filename, bank, label, by_name, maxlen in jobs:
        _, strings = pt.read_msg_archive(texts.files[bank])
        entries, missing, too_long = {}, [], []
        for i, codes in enumerate(strings):
            en = pt.decode_text(codes)
            if not en or en.strip("-? ") == "":
                continue
            fr = corrections.get(label, {}).get(en) or by_name.get(norm(en))
            if fr is None:
                missing.append(en)
                continue
            if len(fr) > maxlen:
                too_long.append((en, fr))
            entries[str(i)] = {"en": en, "fr": fr}
        data = {"archive": bank, "categorie": label, "longueur_max": maxlen, "textes": entries}
        with open(os.path.join(OUT, filename), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        report.append((label, len(entries), missing, too_long))

    for label, n, missing, too_long in report:
        print(f"{label:10s} : {n} traduits, {len(missing)} introuvables, {len(too_long)} trop longs")
        if missing:
            print("   introuvables :", missing[:60])
        if too_long:
            print("   trop longs   :", too_long[:60])


if __name__ == "__main__":
    main()
