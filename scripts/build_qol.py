"""Construit la ROM « Renegade QoL » à partir de la ROM Renegade de base.

Usage : python build_qol.py [--fr] [--test-vol]
  (lit roms/renegade_base.nds, écrit roms/renegade_qol[_fr][_test_vol].nds)
  --fr        : applique la traduction française (dossier translation/fr)
  --test-vol  : ROM de test où le Vol du Trainer Kit ne demande pas de badge

La ROM de base n'est jamais modifiée : chaque construction repart d'elle.
Chaque modification est une fonction mod_xxx(rom) ; on les active dans MODS.
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt

BASE = os.path.join(pt.ROOT, "roms", "renegade_base.nds")
TEST_FLY = "--test-vol" in sys.argv
FRENCH = "--fr" in sys.argv
OUT = os.path.join(pt.ROOT, "roms", "renegade_qol" + ("_fr" if FRENCH else "")
                   + ("_test_vol" if TEST_FLY else "") + ".nds")
FR_DIR = os.path.join(pt.ROOT, "translation", "fr")


def tr(en, fr):
    """Texte ajouté par nos modifications : version anglaise ou française selon --fr."""
    return fr if FRENCH else en

ITEM_RARE_CANDY = 50
VAR_0x8004, VAR_0x8005, VAR_RESULT = 0x8004, 0x8005, 0x800C
SE_CONFIRM = 0x5DC          # bip quand on parle à un PNJ (repris des PNJ d'origine)
COMMON_ADD_ITEM = 0x7FC     # « Vous obtenez X ! » + fanfare
COMMON_BAG_FULL = 0x7E1     # « Le Sac est plein. »
COND_EQ, COND_NE = 1, 5
GFX_SCIENTIST_M = 29
MOVEMENT_LOOK_AROUND = 2
ITEM_TRAINER_KIT = 465      # ancien Vs. Recorder


def mod_rare_candy_npc(rom, arm9, table):
    """PNJ au Centre Pokémon de Littorella : 99 Super Bonbons à chaque fois (+ Trainer Kit)."""
    h = pt.map_header(arm9, table, pt.header_id("SANDGEM_TOWN_POKECENTER_1F"))

    # 1) Textes : on ajoute les répliques à la fin de l'archive de la carte
    texts = rom.narc(pt.TEXTS)
    seed, strings = pt.read_msg_archive(texts.files[h["texts"]])
    msg_intro = len(strings)
    strings.append(pt.encode_text(tr(
        "I'm researching Rare Candies, and I\n"
        "have more than I could ever need!\r"
        "Here, take some. Come back whenever\n"
        "you want more!",
        "J'étudie les Super Bonbons, et j'en ai\n"
        "bien plus qu'il ne m'en faut !\r"
        "Tiens, prends-en. Reviens quand tu\n"
        "veux pour en avoir d'autres !"
    )))
    msg_kit = len(strings)
    strings.append(pt.encode_text(tr(
        "Oh, and take this Trainer Kit too!\r"
        "Use it anywhere to heal your team,\n"
        "access the PC or Fly!",
        "Oh, et prends aussi ce Kit Dresseur !\r"
        "Il permet de soigner ton équipe,\n"
        "d'utiliser le PC ou Vol, partout !"
    )))
    texts.files[h["texts"]] = pt.write_msg_archive(seed, strings)

    # 2) Script
    s = pt.ScriptBuilder()
    s.play_se(SE_CONFIRM)
    s.lock_all()
    s.face_player()
    s.message(msg_intro)
    s.wait_button()
    # Trainer Kit, seulement si le joueur ne l'a pas encore
    s.check_item(ITEM_TRAINER_KIT, 1, VAR_RESULT)
    s.compare_var_value(VAR_RESULT, 0)
    s.goto_if(COND_NE, "candies")
    s.message(msg_kit)
    s.wait_button()
    s.set_var(VAR_0x8004, ITEM_TRAINER_KIT)
    s.set_var(VAR_0x8005, 1)
    s.call_common(COMMON_ADD_ITEM)
    s.label("candies")
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


COMMON_SCRIPTS_FILE = 211   # scripts communs (numéros 2000 et plus)
COMMON_STRINGS_BANK = 213   # textes des scripts communs
ITEM_TEXT_BANKS = {         # textes du Trainer Kit (ancien Vs. Recorder)
    391: tr("A handy kit for Trainers. Use it\nanywhere to heal your team, access\nthe PC or Fly.",
           "Un kit pratique pour les Dresseurs.\nSoigne l'équipe, accède au PC ou\nutilise Vol, partout."),
    392: tr("Trainer Kit", "Kit Dresseur"),
    393: tr("a {CMD FF00 FF}Trainer Kit{CMD FF00 0}", "{CMD FF00 FF}Kit Dresseur{CMD FF00 0}"),
    394: tr("Trainer Kits", "Kits Dresseur"),
}
VAR_0x8008 = 0x8008
FANFARE_HEAL = 0x48E        # jingle de soin (repris des scripts du jeu)
BOX_MODE_MOVE_POKEMON = 2   # écran des boîtes « Déplacer des Pokémon »
SCRCMD_QOL_OPEN_FLY_MAP = 0x004      # commandes ajoutées (asm/trainer_kit.s)
SCRCMD_QOL_FLY_IF_SELECTED = 0x005
SCRCMD_QOL_CHECK_CAN_FLY = 0x006
FLY_ERROR_BADGE = 2


def mod_trainer_kit(rom, arm9, table):
    """Trainer Kit (ancien Vs. Recorder) : menu Soigner / PC / Vol utilisable partout."""
    texts = rom.narc(pt.TEXTS)

    # 1) Nom et description de l'objet
    for bank, text in ITEM_TEXT_BANKS.items():
        seed, strings = pt.read_msg_archive(texts.files[bank])
        if "Recorder" not in pt.decode_text(strings[ITEM_TRAINER_KIT]) and "record" not in \
                pt.decode_text(strings[ITEM_TRAINER_KIT]):
            raise SystemExit(f"Texte d'objet inattendu dans l'archive {bank}")
        strings[ITEM_TRAINER_KIT] = pt.encode_text(text)
        texts.files[bank] = pt.write_msg_archive(seed, strings)

    # 2) Textes du menu, ajoutés aux textes communs
    seed, strings = pt.read_msg_archive(texts.files[COMMON_STRINGS_BANK])

    def add(text):
        strings.append(pt.encode_text(text))
        assert len(strings) - 1 < 256, "numéro de texte trop grand pour un menu"
        return len(strings) - 1

    t_prompt = add(tr("What would you like to do?", "Que veux-tu faire ?"))
    t_heal = add(tr("Heal team", "Soigner"))
    t_pc = add("PC")
    t_fly = add(tr("Fly", "Vol"))
    t_cancel = add(tr("Cancel", "Annuler"))
    t_healed = add(tr("Your Pokémon were fully healed!", "Tes Pokémon sont en pleine forme !"))
    t_badge = add(tr("You need the Cobble Badge\nto Fly.", "Il faut le Badge Pavé\npour utiliser Vol."))
    t_no_fly = add(tr("You can't Fly here.", "Impossible d'utiliser Vol ici."))
    texts.files[COMMON_STRINGS_BANK] = pt.write_msg_archive(seed, strings)

    # 3) Script du menu
    s = pt.ScriptBuilder()
    s.lock_all()
    s.message(t_prompt)
    s.init_local_text_menu(1, 1, 0, VAR_0x8008)
    s.add_menu_entry(t_heal, 0)
    s.add_menu_entry(t_pc, 1)
    s.add_menu_entry(t_fly, 2)
    s.add_menu_entry(t_cancel, 3)
    s.show_menu()
    for value, label in [(0, "heal"), (1, "pc"), (2, "fly")]:
        s.compare_var_value(VAR_0x8008, value)
        s.goto_if(COND_EQ, label)
    s.label("close")
    s.close_message()
    s.release_all()
    s.end()

    s.label("heal")
    s.play_fanfare(FANFARE_HEAL)
    s.wait_fanfare()
    s.heal_party()
    s.message(t_healed)
    s.wait_button()
    s.goto("close")

    s.label("pc")
    s.close_message()
    s.fade_screen(fade_in=False)
    s.wait_fade_screen()
    s.open_pokemon_storage(BOX_MODE_MOVE_POKEMON)
    s.return_to_field()
    s.fade_screen(fade_in=True)
    s.wait_fade_screen()
    s.release_all()
    s.end()

    s.label("fly")
    s.raw_op(SCRCMD_QOL_CHECK_CAN_FLY)
    s.u16(VAR_0x8008)
    s.compare_var_value(VAR_0x8008, 0)
    s.goto_if(COND_EQ, "fly_ok")
    s.compare_var_value(VAR_0x8008, FLY_ERROR_BADGE)
    s.goto_if(COND_EQ, "fly_badge")
    s.message(t_no_fly)
    s.wait_button()
    s.goto("close")
    s.label("fly_badge")
    s.message(t_badge)
    s.wait_button()
    s.goto("close")
    s.label("fly_ok")
    s.close_message()
    s.fade_screen(fade_in=False)
    s.wait_fade_screen()
    s.raw_op(SCRCMD_QOL_OPEN_FLY_MAP)
    s.return_to_field()
    s.raw_op(SCRCMD_QOL_FLY_IF_SELECTED)
    s.u16(VAR_0x8008)
    s.compare_var_value(VAR_0x8008, 1)
    s.goto_if(COND_EQ, "flying")
    s.fade_screen(fade_in=True)
    s.wait_fade_screen()
    s.label("flying")
    s.release_all()
    s.end()

    scripts = rom.narc(pt.SCRIPTS)
    scripts.files[COMMON_SCRIPTS_FILE], script_no = pt.append_script(scripts.files[COMMON_SCRIPTS_FILE], s.build())
    rom.qol_script_id = 2000 + script_no - 1
    print(f"  Script du menu : n° {rom.qol_script_id}, textes {t_prompt}-{t_no_fly}")


ARMIPS = os.path.join(pt.ROOT, "tools", "armips", "armips.exe")
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
    (16, 0x0224A94A): bytes.fromhex("00d1"),                                # capture 100 %
    (None, 0x020EAC68): bytes.fromhex("4df70302 65f70302 81f70302"),        # Trainer Kit
    (None, 0x020EF8B0): bytes.fromhex("89910602 bd910602 00000000"),        # Trainer Kit
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

    res = subprocess.run([ARMIPS, "main.s", "-equ", "QOL_OVERLAY", str(new_id),
                          "-equ", "QOL_SCRIPT_ID", str(rom.qol_script_id),
                          "-equ", "QOL_TEST_FLY_NO_BADGE", "1" if TEST_FLY else "0"],
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
    strings[BAG_TEXT_REPEL_LINGER] = pt.encode_text(tr("{CMD 0103 0 0} turned off\nthe Repel.",
                                                       "{CMD 0103 0 0} a désactivé\nle Repousse."))
    texts.files[TEXT_BANK_BAG] = pt.write_msg_archive(seed, strings)


ITEM_DATA = "itemtool/itemdata/pl_item_data.narc"
# Objets « à revendre » : ils gardent leur prix pour pouvoir gagner de l'argent.
# (numéros bas : la fiche de données a le même numéro que l'objet)
VALUABLE_ITEMS = {
    86: "Petit Champignon", 87: "Gros Champignon", 88: "Perle", 89: "Grosse Perle",
    90: "Poussière Étoile", 91: "Morceau d'Étoile", 92: "Pépite", 93: "Écaille Cœur",
    106: "Os Rare",
}


def mod_prices(rom, arm9, table):
    """Tous les objets coûtent 1 $ en boutique (sauf les objets à revendre)."""
    import struct
    narc = rom.narc(ITEM_DATA)
    changed = 0
    for i, f in enumerate(narc.files):
        if len(f) < 2 or i in VALUABLE_ITEMS:
            continue
        (price,) = struct.unpack_from("<H", f, 0)
        if price > 1:
            narc.files[i] = struct.pack("<H", 1) + f[2:]
            changed += 1
    print(f"  {changed} fiches d'objets passées à 1 $")


ITEM_NAMES_BANK, ITEM_ARTICLE_BANK, ITEM_PLURAL_BANK = 392, 393, 394


def mod_translate_fr(rom, arm9, table):
    """Traduction française (translation/fr/*.json), uniquement avec --fr."""
    import re
    if not FRENCH:
        return
    texts = rom.narc(pt.TEXTS)
    total, skipped = 0, 0
    translated_items = {}
    for path in sorted(glob.glob(os.path.join(FR_DIR, "*.json"))):
        data = json.load(open(path, encoding="utf-8"))
        if "archive" not in data:
            continue  # corrections.json et autres fichiers d'aide
        bank = data["archive"]
        seed, strings = pt.read_msg_archive(texts.files[bank])
        for idx, entry in data["textes"].items():
            i = int(idx)
            current = pt.decode_text(strings[i])
            if current != entry["en"]:
                skipped += 1  # texte déjà modifié par nos améliorations (ex. Trainer Kit)
                continue
            strings[i] = pt.encode_text(entry["fr"])
            total += 1
            if bank == ITEM_NAMES_BANK:
                translated_items[i] = entry
        texts.files[bank] = pt.write_msg_archive(seed, strings)

    # Noms d'objets « avec article » et au pluriel, déduits des noms
    for bank in (ITEM_ARTICLE_BANK, ITEM_PLURAL_BANK):
        seed, strings = pt.read_msg_archive(texts.files[bank])
        for i, entry in translated_items.items():
            current = pt.decode_text(strings[i])
            if bank == ITEM_ARTICLE_BANK:
                new = re.sub(r"^(an|a|some) ", "", current).replace(entry["en"], entry["fr"])
            else:
                new = entry["fr"]
            strings[i] = pt.encode_text(new)
        texts.files[bank] = pt.write_msg_archive(seed, strings)
    print(f"  {total} textes traduits ({skipped} laissés car déjà modifiés), "
          f"{len(translated_items)} noms d'objets déclinés")


MODS = [mod_rare_candy_npc, mod_trainer_kit, mod_asm, mod_repel_text, mod_prices, mod_translate_fr]


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
