"""Génère traduction/fr/combat.json et combat_attaques.json (niveau 3 : messages de combat).

- Archive 368 : chaque message est réduit à sa forme de base (voir battle_families.py),
  traduite dans traduction/fr/combat_source*.json (clé = forme anglaise, valeur = français
  avec {S0}, {S1} pour les Pokémon). Les variantes « sauvage » / « ennemi » sont générées.
- Archive 0 : « X utilise <attaque> ! », généré à partir des noms d'attaques français.

Usage : python gen_fr_battle.py <rom anglaise>
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import battle_families as bf
import pt

OUT = os.path.join(pt.ROOT, "traduction", "fr")
MOVES_USED_BANK = 0
SIDE_SUFFIX = {"own": "", "wild": " sauvage", "foe": " ennemi"}

# Largeur estimée des variables (en caractères) pour le découpage des lignes
TOKEN_WIDTH = {"0101": 10, "0100": 10, "0103": 7, "010E": 12, "0105": 13, "0106": 13, "0108": 13,
               "010D": 9, "010F": 8, "0110": 10, "0111": 9, "010B": 8}
TOKEN = re.compile(r"\{CMD ([0-9A-F]{4})[^}]*\}")


def width(text):
    text = text.replace(" ", " ")
    return len(TOKEN.sub(lambda m: "x" * TOKEN_WIDTH.get(m.group(1), 4), text))


def wrap_battle(text, max_width):
    """Découpe en lignes ; 2 lignes par cadre : « \\n » entre lignes, « \\f » entre cadres."""
    text = re.sub(r" ([!?:;])", " \\1", text)  # pas de « ! » seul en début de ligne
    # les variables {CMD xxxx a b} ne doivent jamais être coupées
    text = re.sub(r"\{CMD [^}]*\}", lambda m: m.group(0).replace(" ", " "), text)
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        cand = w if not cur else cur + " " + w
        if cur and width(cand.replace(" ", " ")) > max_width:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    out = ""
    for k, line in enumerate(lines):
        if k:
            out += "\n" if k % 2 == 1 else "\f"
        out += line
    return out.replace(" ", " ")


def placeholders(s):
    return sorted(TOKEN.findall(s) + re.findall(r"\{CMD [^}]*\}", s))


def main():
    rom = pt.Rom(sys.argv[1])
    texts = rom.narc(pt.TEXTS)

    # --- Archive 368 -----------------------------------------------------------
    source = {}
    for path in sorted(glob.glob(os.path.join(OUT, "combat_source*.json"))):
        source.update({k: v for k, v in json.load(open(path, encoding="utf-8")).items() if not k.startswith("_")})
    _, s = pt.read_msg_archive(texts.files[bf.BANK])
    strings = [pt.decode_text(x) for x in s]
    max_w = max(width(l) for t in strings for l in re.split(r"[\n\x0c\r]", t))
    entries, missing, errors = {}, [], []
    for sk, members in bf.families(strings).items():
        fr_sk = source.get(sk)
        if fr_sk is None:
            missing.append(sk)
            continue
        en_ph = sorted(re.findall(r"\{CMD [^}]*\}|\{S\d\}", sk))
        fr_ph = sorted(re.findall(r"\{CMD [^}]*\}|\{S\d\}", fr_sk))
        if en_ph != fr_ph:
            errors.append((sk, fr_sk))
            continue
        for i, subjects, end in members:
            fr = fr_sk
            for n, (buf, side) in enumerate(subjects):
                fr = fr.replace("{S%d}" % n, "{CMD 0101 %s 0}%s" % (buf, SIDE_SUFFIX[side]))
            if "{S" in fr:
                errors.append((sk, fr_sk))
                break
            entries[str(i)] = {"en": strings[i], "fr": wrap_battle(fr, max_w) + end}
    with open(os.path.join(OUT, "combat.json"), "w", encoding="utf-8") as f:
        json.dump({"archive": bf.BANK, "categorie": "Messages de combat", "largeur": max_w,
                   "textes": entries}, f, ensure_ascii=False, indent=1)
    print(f"Messages de combat : {len(entries)}/{len([t for t in strings if t.strip()])} traduits "
          f"(largeur {max_w}), {len(missing)} formes sans traduction, {len(errors)} erreurs de variables")
    for sk in missing:
        print("   ? " + json.dumps(sk, ensure_ascii=False))
    for sk, fr in errors:
        print("   ! " + json.dumps(sk, ensure_ascii=False) + " -> " + json.dumps(fr, ensure_ascii=False))

    # --- Archive 0 : « X utilise <attaque> ! » --------------------------------
    moves = json.load(open(os.path.join(OUT, "attaques.json"), encoding="utf-8"))["textes"]
    _, s0 = pt.read_msg_archive(texts.files[MOVES_USED_BANK])
    entries0 = {}
    for i, codes in enumerate(s0):
        en = pt.decode_text(codes)
        move = moves.get(str(i // 3))
        if not move or "used" not in en:
            continue
        side = ["own", "wild", "foe"][i % 3]
        fr = "{CMD 0101 0 0}%s utilise\n%s !" % (SIDE_SUFFIX[side], move["fr"])
        entries0[str(i)] = {"en": en, "fr": fr}
    with open(os.path.join(OUT, "combat_attaques.json"), "w", encoding="utf-8") as f:
        json.dump({"archive": MOVES_USED_BANK, "categorie": "Attaques utilisées en combat",
                   "textes": entries0}, f, ensure_ascii=False, indent=1)
    print(f"« X utilise Y ! » : {len(entries0)} générés")


if __name__ == "__main__":
    main()
