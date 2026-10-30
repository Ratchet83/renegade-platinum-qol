"""Regroupe les messages de combat (archive 368) par « famille » de variantes.

Un message est réduit à un squelette : chaque sujet Pokémon est remplacé par {S0}, {S1}
(« {X} », « The wild {X} », « The foe’s {X} », « the wild {X} », « the foe’s {X} »),
les retours à la ligne sont aplatis. Les variantes d'une même famille ont le même squelette.

Utilisé par gen_fr_battle.py ; lancé seul, il écrit la liste des squelettes à traduire.
Usage : python battle_families.py <rom> <fichier de sortie>
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt

BANK = 368
SUBJECT = re.compile(r"(?:(The|the) (wild|foe’s)[ \n\x0c]+)?\{CMD 0101 (\d) 0\}")
END = re.compile(r"((?:\{CMD 02\w\w[^}]*\}|\r|\x0c)*)$")


def skeleton(text):
    """-> (squelette, [(numéro de tampon, camp)], fin du texte)"""
    end = END.search(text).group(1)
    body = text[: len(text) - len(end)] if end else text
    subjects = []

    def repl(m):
        side = {"wild": "wild", "foe’s": "foe"}.get(m.group(2), "own")
        subjects.append((m.group(3), side))
        return "{S%d}" % (len(subjects) - 1)

    sk = SUBJECT.sub(repl, body)
    sk = re.sub(r"[\n\x0c]+", " ", sk)
    sk = re.sub(r"\s+", " ", sk).strip()
    return sk, subjects, end


def families(strings):
    fam = {}
    for i, t in enumerate(strings):
        if not t.strip():
            continue
        sk, subjects, end = skeleton(t)
        fam.setdefault(sk, []).append((i, subjects, end))
    return fam


if __name__ == "__main__":
    rom = pt.Rom(sys.argv[1])
    _, s = pt.read_msg_archive(rom.narc(pt.TEXTS).files[BANK])
    strings = [pt.decode_text(x) for x in s]
    fam = families(strings)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        for sk, members in fam.items():
            f.write(f"{members[0][0]}\t{len(members)}\t{sk}\n")
    print(f"{len(strings)} messages -> {len(fam)} squelettes à traduire "
          f"({sum(len(sk) for sk in fam)} caractères)")
