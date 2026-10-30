"""Outils d'analyse du code ARM9 / overlays (désassemblage Thumb avec capstone)."""
import os
import struct
import sys

import capstone
import ndspy.codeCompression
import ndspy.rom

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARM9_BASE = 0x02000000

_cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
_cs.detail = False
_cs.skipdata = True  # ne pas s'arrêter sur des octets non décodables


class Code:
    def __init__(self, rom_path):
        self.rom = ndspy.rom.NintendoDSRom.fromFile(rom_path)
        self.arm9 = bytes(ndspy.codeCompression.decompress(self.rom.arm9))
        self.ovs = self.rom.loadArm9Overlays()

    def region(self, ov=None):
        """(base, data) de l'ARM9 ou d'un overlay."""
        if ov is None:
            return ARM9_BASE, self.arm9
        o = self.ovs[ov]
        return o.ramAddress, bytes(o.data)

    def u32(self, addr, ov=None):
        base, data = self.region(ov)
        return struct.unpack_from("<I", data, addr - base)[0]

    def bls(self, ov=None):
        """Toutes les instructions BL Thumb : liste de (adresse, cible)."""
        base, data = self.region(ov)
        out = []
        for off in range(0, len(data) - 4, 2):
            hi, lo = struct.unpack_from("<HH", data, off)
            if (hi & 0xF800) == 0xF000 and (lo & 0xF800) in (0xF800, 0xE800):
                imm = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
                if imm & 0x400000:
                    imm -= 0x800000
                tgt = base + off + 4 + imm
                if (lo & 0xF800) == 0xE800:  # BLX vers du code ARM : aligné sur 4
                    tgt &= ~3
                out.append((base + off, tgt))
        return out

    def disasm(self, addr, count=60, ov=None):
        base, data = self.region(ov)
        off = addr - base
        lines = []
        for ins in _cs.disasm(data[off:off + count * 4], addr):
            lines.append(ins)
            if len(lines) >= count:
                break
        return lines

    def print_disasm(self, addr, count=60, ov=None, stop_at_return=True):
        for ins in self.disasm(addr, count, ov):
            print(f"  {ins.address:08X}: {ins.bytes.hex():10s} {ins.mnemonic} {ins.op_str}")
            if stop_at_return and (ins.mnemonic == "bx" and ins.op_str == "lr" or
                                   ins.mnemonic == "pop" and "pc" in ins.op_str):
                break


def find_pointer_table(code, length, ov=None, min_len=None):
    """Cherche un tableau de `length` pointeurs Thumb (impairs) consécutifs."""
    base, data = code.region(ov)
    min_len = min_len or length
    run, start = 0, 0
    for off in range(0, len(data) - 4, 4):
        (v,) = struct.unpack_from("<I", data, off)
        if v & 1 and 0x02000000 <= v < 0x02400000:
            if run == 0:
                start = off
            run += 1
        else:
            if run >= min_len:
                yield base + start, run
            run = 0
