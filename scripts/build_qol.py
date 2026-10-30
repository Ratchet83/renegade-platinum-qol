"""Construit la ROM « Renegade QoL » à partir de la ROM Renegade de base.

Usage : python build_qol.py   (lit travail/renegade_base.nds, écrit travail/renegade_qol.nds)

La ROM de base n'est jamais modifiée : chaque construction repart d'elle.
Chaque modification est une fonction mod_xxx(rom) ; on les active dans MODS.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt

BASE = os.path.join(pt.ROOT, "travail", "renegade_base.nds")
OUT = os.path.join(pt.ROOT, "travail", "renegade_qol.nds")

ITEM_RARE_CANDY = 50
VAR_0x8004, VAR_0x8005, VAR_RESULT = 0x8004, 0x8005, 0x800C
SE_CONFIRM = 0x5DC          # bip quand on parle à un PNJ (repris des PNJ d'origine)
COMMON_ADD_ITEM = 0x7FC     # « Vous obtenez X ! » + fanfare
COMMON_BAG_FULL = 0x7E1     # « Le Sac est plein. »
COND_EQ = 1
GFX_SCIENTIST_M = 29
MOVEMENT_LOOK_AROUND = 2


def mod_rare_candy_npc(rom, arm9, table):
    """PNJ au Centre Pokémon de Littorella qui donne 99 Super Bonbons à chaque fois."""
    h = pt.map_header(arm9, table, pt.header_id("SANDGEM_TOWN_POKECENTER_1F"))

    # 1) Texte : on ajoute une réplique à la fin de l'archive de la carte
    texts = rom.narc(pt.TEXTS)
    seed, strings = pt.read_msg_archive(texts.files[h["texts"]])
    msg_intro = len(strings)
    strings.append(pt.encode_text(
        "I'm researching Rare Candies, and I\n"
        "have more than I could ever need!\r"
        "Here, take some. Come back whenever\n"
        "you want more!"
    ))
    texts.files[h["texts"]] = pt.write_msg_archive(seed, strings)

    # 2) Script
    s = pt.ScriptBuilder()
    s.play_se(SE_CONFIRM)
    s.lock_all()
    s.face_player()
    s.message(msg_intro)
    s.wait_button()
    s.can_fit_item(ITEM_RARE_CANDY, 99, VAR_RESULT)
    s.compare_var_value(VAR_RESULT, 0)
    s.goto_if(COND_EQ, "bag_full")
    s.set_var(VAR_0x8004, ITEM_RARE_CANDY)
    s.set_var(VAR_0x8005, 99)
    s.call_common(COMMON_ADD_ITEM)
    s.close_message()
    s.release_all()
    s.end()
    s.label("bag_full")
    s.call_common(COMMON_BAG_FULL)
    s.close_message()
    s.release_all()
    s.end()

    scripts = rom.narc(pt.SCRIPTS)
    scripts.files[h["scripts"]], script_no = pt.append_script(scripts.files[h["scripts"]], s.build())

    # 3) PNJ : copie d'un PNJ existant, déplacé sur une case libre
    events = rom.narc(pt.EVENTS)
    sections, trailer = pt.read_events(events.files[h["events"]])
    objs = [pt.unpack_obj(r) for r in sections[1]]
    npc = dict(objs[0])
    npc.update(id=max(o["id"] for o in objs) + 1, gfx=GFX_SCIENTIST_M,
               movement=MOVEMENT_LOOK_AROUND, flag=0, script=script_no, dir=1, x=3, z=6, y=0)
    sections[1].append(pt.pack_obj(npc))
    events.files[h["events"]] = pt.write_events(sections, trailer)
    print(f"  PNJ Super Bonbons : script {script_no}, texte {msg_intro}, position (3, 6)")


ARMIPS = os.path.join(pt.ROOT, "outils", "armips", "armips.exe")
ASM_DIR = os.path.join(pt.ROOT, "asm")
BUILD_DIR = os.path.join(ASM_DIR, "build")

# Octets d'origine attendus aux endroits modifiés par asm/main.s
# (sécurité : si la ROM de base n'est pas celle prévue, on s'arrête)
ASM_EXPECTED = {
    # (overlay ou None pour l'ARM9, adresse) : octets d'origine
    (None, 0x02000C96): bytes.fromhex("0020 16f06aff 5e48 0021 caf0fcea"),  # démarrage
    (None, 0x0209656A): bytes.fromhex("ddf781ff"),                          # level cap
    (None, 0x02096AA6): bytes.fromhex("ddf7e3fc"),                          # level cap
    (16, 0x02249004): bytes.fromhex("2bf634fa"),                            # level cap
    (16, 0x022490EA): bytes.fromhex("2bf621fd"),                            # level cap
    (6, 0x02246C06): bytes.fromhex("491e"),                                 # Repousse
    (84, 0x0223DCB0): bytes.fromhex("0021 2152"),                           # Repousse
    (84, 0x0223DCDA): bytes.fromhex("0121"),                                # Repousse
}
ASM_OVERLAYS = [6, 16, 84]  # overlays du jeu modifiés par asm/main.s
QOL_RAM = 0x023C8000

TEXT_BANK_BAG = 7
BAG_TEXT_REPEL_LINGER = 62


def mod_asm(rom, arm9, table):
    """Code ajouté : level caps (16/26/33/39/44/53/56/62/78) et Repousse infini."""
    import subprocess
    import ndspy.code

    r = rom.rom
    ovs = r.loadArm9Overlays()
    arm9_data = bytearray(arm9)
    for (ov, addr), expected in ASM_EXPECTED.items():
        base, data = (0x02000000, arm9_data) if ov is None else (ovs[ov].ramAddress, ovs[ov].data)
        got = bytes(data[addr - base: addr - base + len(expected)])
        if got != expected:
            raise SystemExit(f"Octets inattendus à {addr:08X} : {got.hex()} (attendu {expected.hex()})")

    new_id = max(ovs) + 1
    os.makedirs(BUILD_DIR, exist_ok=True)

    def write(name, data):
        with open(os.path.join(BUILD_DIR, name), "wb") as f:
            f.write(data)

    def read(name):
        with open(os.path.join(BUILD_DIR, name), "rb") as f:
            return f.read()

    write("arm9.bin", arm9_data)
    for ov in ASM_OVERLAYS:
        write(f"overlay_{ov:04d}.bin", ovs[ov].data)

    res = subprocess.run([ARMIPS, "main.s", "-equ", "QOL_OVERLAY", str(new_id)],
                         cwd=ASM_DIR, capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit("Erreur armips :\n" + res.stdout + res.stderr)

    new_arm9 = read("arm9.bin")
    assert len(new_arm9) == len(arm9_data)
    r.arm9 = new_arm9
    for ov in ASM_OVERLAYS:
        o = ovs[ov]
        new = read(f"overlay_{ov:04d}.bin")
        assert len(new) == len(o.data)
        o.data = bytearray(new)
        r.files[o.fileID] = o.save(compress=False)

    code = read("qol_overlay.bin")
    file_id = len(r.files)
    r.files.append(b"")
    new_ov = ndspy.code.Overlay(code, QOL_RAM, len(code), 0, 0, 0, file_id, len(code), 0)
    r.files[file_id] = new_ov.save(compress=False)
    ovs[new_id] = new_ov
    r.arm9OverlayTable = ndspy.code.saveOverlayTable(ovs)
    print(f"  Module de code {new_id} : {len(code)} octets à 0x{QOL_RAM:08X} (fichier {file_id})")


def mod_repel_text(rom, arm9, table):
    """Texte du Sac quand on désactive le Repousse."""
    texts = rom.narc(pt.TEXTS)
    seed, strings = pt.read_msg_archive(texts.files[TEXT_BANK_BAG])
    old = pt.decode_text(strings[BAG_TEXT_REPEL_LINGER])
    if "linger" not in old:
        raise SystemExit(f"Texte du Sac inattendu : {old!r}")
    # {CMD 0103 0 0} = nom du joueur (tampon 0, rempli par le Sac)
    strings[BAG_TEXT_REPEL_LINGER] = pt.encode_text("{CMD 0103 0 0} turned off\nthe Repel.")
    texts.files[TEXT_BANK_BAG] = pt.write_msg_archive(seed, strings)


MODS = [mod_rare_candy_npc, mod_asm, mod_repel_text]


def main():
    print("Lecture de", BASE)
    rom = pt.Rom(BASE)
    arm9 = rom.arm9()
    table = pt.find_map_headers(arm9)
    for mod in MODS:
        print("->", mod.__doc__.strip().splitlines()[0])
        mod(rom, arm9, table)
    rom.save(OUT)
    print("ROM écrite :", OUT)


if __name__ == "__main__":
    main()
