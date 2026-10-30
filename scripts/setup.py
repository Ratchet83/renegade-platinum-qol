"""One-time setup for building the patch from source (Windows).

Creates the local folders that are not in the repository and installs the tools:
  roms/                 your own ROMs go here (put Renegade at roms/renegade_base.nds)
  tools/venv/           Python environment with ndspy and capstone
  tools/armips/         armips 0.11 (assembler)
  tools/xdelta/         xdelta3 3.0.11 (patch tool)
  ref/                  reference files from the pokeplatinum decompilation

Usage (from the repository folder):  python scripts/setup.py
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
VENV_PY = os.path.join(TOOLS, "venv", "Scripts", "python.exe")
ARMIPS_URL = "https://github.com/Kingcom/armips/releases/download/v0.11.0/armips-v0.11.0-windows-x86.7z"
XDELTA_URL = "https://github.com/jmacd/xdelta-gpl/releases/download/v3.0.11/xdelta3-3.0.11-x86_64.exe.zip"


def step(msg):
    print(f"-> {msg}")


def download(url):
    with urllib.request.urlopen(url) as r:
        return r.read()


def main():
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10 or newer is required (3.12 recommended).")

    for folder in ("roms", "tools"):
        os.makedirs(os.path.join(ROOT, folder), exist_ok=True)

    if not os.path.exists(VENV_PY):
        step("Creating the Python environment (tools/venv)")
        subprocess.run([sys.executable, "-m", "venv", os.path.join(TOOLS, "venv")], check=True)
    step("Installing ndspy and capstone")
    subprocess.run([VENV_PY, "-m", "pip", "install", "-q", "-r", os.path.join(ROOT, "requirements.txt")], check=True)

    armips = os.path.join(TOOLS, "armips", "armips.exe")
    if not os.path.exists(armips):
        step("Downloading armips 0.11")
        os.makedirs(os.path.dirname(armips), exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            archive = os.path.join(tmp, "armips.7z")
            with open(archive, "wb") as f:
                f.write(download(ARMIPS_URL))
            # Windows 10+ ships bsdtar, which can extract .7z archives
            subprocess.run(["tar", "-xf", archive, "-C", os.path.dirname(armips)], check=True)

    xdelta = os.path.join(TOOLS, "xdelta", "xdelta3.exe")
    if not os.path.exists(xdelta):
        step("Downloading xdelta3 3.0.11")
        os.makedirs(os.path.dirname(xdelta), exist_ok=True)
        z = zipfile.ZipFile(io.BytesIO(download(XDELTA_URL)))
        exe = next(n for n in z.namelist() if n.lower().endswith(".exe"))
        with z.open(exe) as src, open(xdelta, "wb") as dst:
            shutil.copyfileobj(src, dst)

    step("Downloading reference files (ref/)")
    subprocess.run([VENV_PY, "-I", os.path.join(ROOT, "scripts", "fetch_refs.py")], check=True)

    base = os.path.join(ROOT, "roms", "renegade_base.nds")
    print()
    print("Setup complete.")
    if os.path.exists(base):
        print("Found roms/renegade_base.nds: you can build now.")
    else:
        print("Next: copy your Renegade Platinum v1.3.0 ROM to roms/renegade_base.nds")


if __name__ == "__main__":
    main()
