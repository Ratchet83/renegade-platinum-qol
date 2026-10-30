"""Affiche la définition de macros de scrcmd.inc (référence décompilation)."""
import re
import sys

text = open(sys.argv[1], encoding="utf-8").read()
for name in sys.argv[2:]:
    m = re.search(r"^\s*\.macro\s+" + re.escape(name) + r"\b.*?^\s*\.endm", text, re.M | re.S)
    print(f"----- {name}")
    print(m.group(0) if m else "  (introuvable)")
