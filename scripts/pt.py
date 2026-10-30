"""Petite bibliothèque pour modifier Pokémon Platine (US) / Renegade Platinum.

- Textes : décodage / encodage des archives msgdata (chiffrement Gen 4 + charmap)
- Scripts : lecture / écriture des fichiers de scripts (table d'entrées + bytecode)
- Événements : lecture / écriture des PNJ d'une carte (zone_event)
- En-têtes de cartes : retrouver quel script / texte / événement va avec une carte
"""
import os
import re
import struct

import ndspy.codeCompression
import ndspy.narc
import ndspy.rom

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "ref")

# --------------------------------------------------------------------------
# Jeu de caractères
# --------------------------------------------------------------------------
_charmap = None
_revmap = None


def charmap():
    global _charmap, _revmap
    if _charmap is None:
        _charmap, _revmap = {}, {}
        path = os.path.join(REF, "tools__msgenc__charmap.txt")
        for line in open(path, encoding="utf-8"):
            line = line.rstrip("\n").lstrip(" \t")
            if not line or line.startswith("//") or "=" not in line:
                continue
            code, ch = line.split("=", 1)
            try:
                code = int(code, 16)
            except ValueError:
                continue
            _charmap[code] = ch
            # On garde le premier code rencontré pour chaque caractère
            if ch not in _revmap and len(ch) == 1:
                _revmap[ch] = code
        # Caractères de contrôle utiles
        _revmap["\n"] = 0xE000
        _revmap["\r"] = 0x25BC  # attendre + défiler
        _revmap["\f"] = 0x25BD  # attendre + nouvelle bulle
    return _charmap, _revmap


def decode_text(codes):
    cmap, _ = charmap()
    out = []
    i = 0
    while i < len(codes):
        c = codes[i]
        if c == 0xFFFF:
            break
        if c == 0xFFFE:  # commande (variable, couleur…) : {CMD type arg...}
            typ = codes[i + 1]
            n = codes[i + 2]
            args = codes[i + 3:i + 3 + n]
            out.append("{CMD %04X %s}" % (typ, " ".join("%X" % a for a in args)))
            i += 3 + n
            continue
        if c == 0xE000:
            out.append("\n")
        elif c == 0x25BC:
            out.append("\r")
        elif c == 0x25BD:
            out.append("\f")
        else:
            out.append(cmap.get(c, "{%04X}" % c))
        i += 1
    return "".join(out)


def encode_text(s):
    _, rev = charmap()
    codes = []
    i = 0
    while i < len(s):
        m = re.match(r"\{CMD ([0-9A-Fa-f]+)((?: [0-9A-Fa-f]+)*)\}", s[i:])
        if m:
            args = [int(a, 16) for a in m.group(2).split()]
            codes += [0xFFFE, int(m.group(1), 16), len(args)] + args
            i += m.end()
            continue
        m = re.match(r"\{([0-9A-Fa-f]{4})\}", s[i:])
        if m:
            codes.append(int(m.group(1), 16))
            i += m.end()
            continue
        ch = s[i]
        if ch == "'":
            ch = "’"
        if ch not in rev:
            raise ValueError(f"Caractère non supporté : {ch!r}")
        codes.append(rev[ch])
        i += 1
    codes.append(0xFFFF)
    return codes


# Variables de texte courantes (STRVAR) : {CMD 0100 0 0} = nom du joueur dans le tampon 0, etc.
def strvar(index):
    return "{CMD 0100 %X 0}" % index


def read_msg_archive(data):
    """Renvoie (seed, [liste de listes de codes u16])."""
    count, seed = struct.unpack_from("<HH", data, 0)
    key = (seed * 0x2FD) & 0xFFFF
    entries = []
    for i in range(count):
        k = (key * (i + 1)) & 0xFFFF
        k = k | (k << 16)
        off, ln = struct.unpack_from("<II", data, 4 + i * 8)
        entries.append((off ^ k, ln ^ k))
    strings = []
    for i, (off, ln) in enumerate(entries):
        k = (0x91BD3 * (i + 1)) & 0xFFFF
        codes = []
        for j in range(ln):
            (c,) = struct.unpack_from("<H", data, off + j * 2)
            codes.append(c ^ k)
            k = (k + 0x493D) & 0xFFFF
        strings.append(codes)
    return seed, strings


def write_msg_archive(seed, strings):
    count = len(strings)
    key = (seed * 0x2FD) & 0xFFFF
    header = bytearray(struct.pack("<HH", count, seed))
    body = bytearray()
    off = 4 + count * 8
    for i, codes in enumerate(strings):
        k = (key * (i + 1)) & 0xFFFF
        k = k | (k << 16)
        header += struct.pack("<II", off ^ k, len(codes) ^ k)
        k2 = (0x91BD3 * (i + 1)) & 0xFFFF
        for c in codes:
            body += struct.pack("<H", c ^ k2)
            k2 = (k2 + 0x493D) & 0xFFFF
        off += len(codes) * 2
    return bytes(header + body)


# --------------------------------------------------------------------------
# Scripts
# --------------------------------------------------------------------------
_opcodes = None


def opcodes():
    """Nom SCRCMD_xxx -> numéro, d'après la table de la décompilation."""
    global _opcodes
    if _opcodes is None:
        _opcodes = {}
        path = os.path.join(REF, "include__data__scripts__scrcmd.h")
        n = 0
        for line in open(path, encoding="utf-8"):
            m = re.match(r"\s*ScriptCommand\((SCRCMD_\w+)", line)
            if m:
                _opcodes[m.group(1)] = n
                n += 1
    return _opcodes


def read_script_file(data):
    """Renvoie la liste des offsets absolus de chaque script d'entrée."""
    offsets = []
    pos = 0
    while True:
        (v,) = struct.unpack_from("<H", data, pos)
        if v == 0xFD13:
            break
        (rel,) = struct.unpack_from("<I", data, pos)
        offsets.append(pos + 4 + rel)
        pos += 4
    return offsets, pos + 2  # offsets, taille de l'en-tête


class ScriptBuilder:
    """Assembleur minimal : on écrit des commandes, avec des labels pour les sauts."""

    def __init__(self):
        self.buf = bytearray()
        self.labels = {}
        self.fixups = []  # (position du s32, label)

    def op(self, name):
        self.buf += struct.pack("<H", opcodes()["SCRCMD_" + name])

    def u8(self, v):
        self.buf += struct.pack("<B", v)

    def u16(self, v):
        self.buf += struct.pack("<H", v)

    def label(self, name):
        self.labels[name] = len(self.buf)

    def jump_target(self, name):
        self.fixups.append((len(self.buf), name))
        self.buf += b"\0\0\0\0"

    # Commandes de haut niveau -------------------------------------------
    def end(self):
        self.op("END")

    def play_se(self, se):
        self.op("PLAYSE"); self.u16(se)

    def lock_all(self):
        self.op("LOCKALL")

    def release_all(self):
        self.op("RELEASEALL")

    def face_player(self):
        self.op("FACEPLAYER")

    def message(self, msg_id):
        self.op("MESSAGE"); self.u8(msg_id)

    def wait_button(self):
        self.op("WAITBUTTON")

    def close_message(self):
        self.op("CLOSEMESSAGE")

    def set_var(self, var, value):
        self.op("SETVARFROMVALUE"); self.u16(var); self.u16(value)

    def compare_var_value(self, var, value):
        self.op("COMPAREVARTOVALUE"); self.u16(var); self.u16(value)

    def goto_if(self, cond, label):
        self.op("GOTOIF"); self.u8(cond); self.jump_target(label)

    def goto(self, label):
        self.op("GOTO"); self.jump_target(label)

    def call_common(self, script_id):
        self.op("CALLCOMMONSCRIPT"); self.u16(script_id)

    def can_fit_item(self, item, count, dest_var):
        self.op("CANFITITEM"); self.u16(item); self.u16(count); self.u16(dest_var)

    def check_item(self, item, count, dest_var):
        self.op("CHECKITEM"); self.u16(item); self.u16(count); self.u16(dest_var)

    def raw_op(self, number):
        """Commande par numéro (pour les commandes ajoutées par le module de code)."""
        self.u16(number)

    def init_local_text_menu(self, x, y, cursor, var, can_exit_with_b=True):
        self.op("INITLOCALTEXTMENU"); self.u8(x); self.u8(y); self.u8(cursor)
        self.u8(1 if can_exit_with_b else 0); self.u16(var)

    def add_menu_entry(self, text_id, index):
        self.op("ADDMENUENTRYIMM"); self.u8(text_id); self.u8(index)

    def show_menu(self):
        self.op("SHOWMENU")

    def fade_screen(self, fade_in):
        # valeurs reprises des scripts du jeu (FadeScreenOut / FadeScreenIn)
        self.op("FADESCREEN"); self.u16(6); self.u16(1); self.u16(1 if fade_in else 0); self.u16(0)

    def wait_fade_screen(self):
        self.op("WAITFADESCREEN")

    def return_to_field(self):
        self.op("RETURNTOFIELD")

    def open_pokemon_storage(self, mode):
        self.op("OPENPOKEMONSTORAGE"); self.u8(mode)

    def play_fanfare(self, seq):
        self.op("PLAYFANFARE"); self.u16(seq)

    def wait_fanfare(self):
        self.op("WAITFANFARE")

    def heal_party(self):
        self.op("HEALPARTY")

    def build(self):
        out = bytearray(self.buf)
        for pos, name in self.fixups:
            struct.pack_into("<i", out, pos, self.labels[name] - (pos + 4))
        return bytes(out)


def append_script(data, code):
    """Ajoute un nouveau script d'entrée à un fichier de scripts.

    Renvoie (nouvelles données, numéro du script, base 1 comme dans les PNJ).
    Les sauts internes des scripts existants sont relatifs, donc décaler tout
    le bytecode de 4 octets (nouvelle entrée dans la table) ne casse rien.
    """
    offsets, hdr_size = read_script_file(data)
    body = data[hdr_size:]
    # alignement du code ajouté sur 4 octets (comme le jeu d'origine)
    pad = (-len(body)) % 4
    body = body + b"\0" * pad
    new_hdr_size = hdr_size + 4
    shift = new_hdr_size - hdr_size
    new_offsets = [o + shift for o in offsets] + [new_hdr_size + len(body)]
    hdr = bytearray()
    for i, o in enumerate(new_offsets):
        hdr += struct.pack("<I", o - (i * 4 + 4))
    hdr += struct.pack("<H", 0xFD13)
    assert len(hdr) == new_hdr_size
    return bytes(hdr) + body + code, len(new_offsets)


# --------------------------------------------------------------------------
# Événements (PNJ)
# --------------------------------------------------------------------------
BG_SIZE, OBJ_SIZE, WARP_SIZE, COORD_SIZE = 20, 32, 12, 16
OBJ_FIELDS = ["id", "gfx", "movement", "trainer_type", "flag", "script", "dir",
              "sight", "unk1", "unk2", "range_x", "range_z", "x", "z", "y"]
OBJ_FMT = "<12H2Hi"  # 12 u16, x/z u16, y s32 = 32 octets


def read_events(data):
    pos = 0
    sections = []
    for size in (BG_SIZE, OBJ_SIZE, WARP_SIZE, COORD_SIZE):
        (n,) = struct.unpack_from("<I", data, pos)
        pos += 4
        sections.append([data[pos + i * size: pos + (i + 1) * size] for i in range(n)])
        pos += n * size
    return sections, data[pos:]


def write_events(sections, trailer=b""):
    out = bytearray()
    for sec in sections:
        out += struct.pack("<I", len(sec))
        for e in sec:
            out += e
    return bytes(out) + trailer


def unpack_obj(raw):
    return dict(zip(OBJ_FIELDS, struct.unpack(OBJ_FMT, raw)))


def pack_obj(d):
    return struct.pack(OBJ_FMT, *[d[f] for f in OBJ_FIELDS])


# --------------------------------------------------------------------------
# ROM
# --------------------------------------------------------------------------
class Rom:
    def __init__(self, path):
        self.rom = ndspy.rom.NintendoDSRom.fromFile(path)
        self._narcs = {}

    def narc(self, path):
        if path not in self._narcs:
            self._narcs[path] = ndspy.narc.NARC(self.rom.getFileByName(path))
        return self._narcs[path]

    def save(self, path):
        for p, narc in self._narcs.items():
            self.rom.setFileByName(p, narc.save())
        self.rom.saveToFile(path)

    def arm9(self):
        return ndspy.codeCompression.decompress(self.rom.arm9)


SCRIPTS = "fielddata/script/scr_seq.narc"
EVENTS = "fielddata/eventdata/zone_event.narc"
TEXTS = "msgdata/pl_msg.narc"

MAP_HEADER_SIZE = 24


def find_map_headers(arm9, n_headers=593):
    """Cherche la table des en-têtes de cartes dans l'ARM9.

    Repère : l'en-tête 0 (EVERYWHERE) puis des en-têtes plausibles à la suite.
    On teste la cohérence (ids de scripts/textes/événements dans les bornes).
    """
    def plausible(off):
        for i in range(n_headers):
            b = arm9[off + i * 24: off + i * 24 + 24]
            if len(b) < 24:
                return False
            area, _, matrix, scr, init, msg, day, night, wild, ev = struct.unpack_from("<BBHHHHHHHH", b)
            if not (scr < 1200 and init < 1200 and msg < 800 and ev < 700 and matrix < 300):
                return False
            if not (day == 0 or 1000 <= day <= 1300):
                return False
        return True

    for off in range(0, len(arm9) - n_headers * 24, 4):
        if plausible(off):
            return off
    return None


def map_header(arm9, table_off, header_id):
    b = arm9[table_off + header_id * 24: table_off + header_id * 24 + 24]
    area, unk, matrix, scr, init, msg, day, night, wild, ev, label = struct.unpack_from("<BBHHHHHHHHH", b)
    return dict(area=area, matrix=matrix, scripts=scr, init_scripts=init, texts=msg,
                music_day=day, music_night=night, wild=wild, events=ev, label=label)


def header_id(name):
    """Numéro d'en-tête d'après generated/map_headers.txt (MAP_HEADER_xxx)."""
    path = os.path.join(REF, "generated__map_headers.txt")
    names = [l.strip() for l in open(path, encoding="utf-8") if l.strip()]
    return names.index("MAP_HEADER_" + name)
