"""Harmonise le style de combat_source_1.json : articles devant talents, stats et capacités."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt

path = os.path.join(pt.ROOT, "translation", "fr", "combat_source_1.json")
data = json.load(open(path, encoding="utf-8"))
out = {}
for en, fr in data.items():
    if not en.startswith("_"):
        fr = re.sub(r"^\{CMD 0105 1 0\} de ", "Le talent {CMD 0105 1 0} de ", fr)
        fr = re.sub(r"^\{CMD 010D 1 0\} de ", "La stat {CMD 010D 1 0} de ", fr)
        fr = re.sub(r"^\{CMD 0106 1 0\} de \{S0\} est bloqué !", "La capacité {CMD 0106 1 0} de {S0} est bloquée !", fr)
        fr = re.sub(r"^\{CMD 0106 1 0\} de \{S0\} est renvoyé", "La capacité {CMD 0106 1 0} de {S0} est renvoyée", fr)
        fr = re.sub(r"^\{CMD 0106 1 0\} de \{S0\} perd", "La capacité {CMD 0106 1 0} de {S0} perd", fr)
        fr = fr.replace("grâce à {CMD 0105 1 0}", "grâce au talent {CMD 0105 1 0}")
        fr = fr.replace("rend l’attaque inefficace", "rend l’attaque inefficace")
    out[en] = fr
json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
