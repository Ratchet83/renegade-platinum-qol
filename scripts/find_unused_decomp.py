"""Liste les fonctions du code permanent (ARM9) jamais utilisées d'après la décompilation.

On ne garde que celles dont le nom contient leur adresse (sub_02XXXXXX…),
pour pouvoir les retrouver directement dans le binaire.
"""
import os
import re
import sys
from collections import Counter

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ref", "src_tree", "pokeplatinum-main")

# Objets de l'ARM9 (section « Static main » du fichier de liens)
static_objs = []
in_static = False
for line in open(os.path.join(ROOT, "platinum.us", "main.lsf.in"), encoding="utf-8"):
    s = line.strip()
    if s.startswith("Static"):
        in_static = True
    elif s.startswith("Overlay") or s.startswith("Autoload"):
        in_static = False
    elif in_static and s.startswith("Object"):
        static_objs.append(s.split()[1])

# Comptage de tous les identifiants dans tout le code
counts = Counter()
for d, _, files in os.walk(ROOT):
    for f in files:
        if f.endswith((".c", ".h", ".s", ".inc")):
            txt = open(os.path.join(d, f), encoding="utf-8", errors="ignore").read()
            counts.update(re.findall(r"\b[A-Za-z_]\w*\b", txt))

defn = re.compile(r"^(?:static\s+)?[\w\s\*]+?\b(\w+)\s*\([^;]*\)\s*\{", re.M)
results = []
for obj in static_objs:
    path = os.path.join(ROOT, obj.replace("$(", "").replace(")", ""))
    if not path.endswith(".c") or not os.path.exists(path):
        continue
    txt = open(path, encoding="utf-8", errors="ignore").read()
    for m in defn.finditer(txt):
        name = m.group(1)
        am = re.search(r"(02[0-9A-Fa-f]{6})", name)
        if am and counts[name] <= 2:  # définition (+ éventuel prototype)
            # taille approximative : nombre de lignes du corps
            body_end = txt.find("\n}\n", m.end())
            lines = txt[m.end():body_end].count("\n")
            results.append((lines, name, int(am.group(1), 16), obj, counts[name]))

results.sort(reverse=True)
print(len(static_objs), "objets ARM9,", len(results), "fonctions inutilisées à adresse connue")
for lines, name, addr, obj, n in results[:30]:
    print(f"  {addr:08X} {name:30s} ~{lines:3d} lignes  ({obj}, {n} occurrences)")
