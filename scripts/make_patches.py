"""Construit les ROM anglaise et française, puis les patchs xdelta à partager (dossier patches/).

Les patchs s'appliquent sur la ROM Renegade Platinum v1.3.0 (roms/renegade_base.nds).
Chaque patch est vérifié : on le réapplique sur la ROM de base et on compare le résultat.

Usage : python make_patches.py
"""
import hashlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt

PY = sys.executable
XDELTA = os.path.join(pt.ROOT, "tools", "xdelta", "xdelta3.exe")
BASE = os.path.join(pt.ROOT, "roms", "renegade_base.nds")
DIST = os.path.join(pt.ROOT, "patches")
BUILD = os.path.join(pt.ROOT, "scripts", "build_qol.py")

VERSIONS = [
    ("EN", [], os.path.join(pt.ROOT, "roms", "renegade_qol.nds"),
     "Renegade Platinum QoL (English) - apply on Renegade Platinum v1.3.0"),
    ("FR", ["--fr"], os.path.join(pt.ROOT, "roms", "renegade_qol_fr.nds"),
     "Renegade Platinum QoL (French / francais) - apply on Renegade Platinum v1.3.0"),
]


def sha1(path):
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()


def run(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(f"Échec : {' '.join(cmd)}\n{res.stdout}{res.stderr}")
    return res.stdout


def main():
    os.makedirs(DIST, exist_ok=True)
    lines = [f"Base : Renegade Platinum v1.3.0, SHA-1 {sha1(BASE)}"]
    for lang, args, rom, description in VERSIONS:
        print(f"-> Construction {lang}")
        run([PY, "-I", BUILD] + args)
        patch = os.path.join(DIST, f"RenegadeQoL_{lang}.xdelta")
        if os.path.exists(patch):
            os.remove(patch)
        # -A : description fixe dans l'en-tête (au lieu des chemins des fichiers),
        # pour que le patch soit identique quel que soit le dossier de construction
        run([XDELTA, "-e", "-9", "-S", "djw", f"-A={description}", "-s", BASE, rom, patch])
        # vérification : base + patch = ROM construite
        check = os.path.join(DIST, f"_verif_{lang}.nds")
        run([XDELTA, "-d", "-f", "-s", BASE, patch, check])
        ok = sha1(check) == sha1(rom)
        os.remove(check)
        if not ok:
            raise SystemExit(f"Le patch {lang} ne redonne pas la ROM construite !")
        size = os.path.getsize(patch) / 1024
        print(f"   {os.path.basename(patch)} : {size:.0f} Ko, vérifié")
        lines.append(f"{os.path.basename(patch)} : résultat SHA-1 {sha1(rom)}")
    with open(os.path.join(DIST, "checksums.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
