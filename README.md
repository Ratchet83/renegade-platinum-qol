# Renegade Platinum QoL

*[Version française](README.fr.md)*

A quality-of-life add-on for **Pokémon Renegade Platinum v1.3.0** by Drayano, so you can focus on battles and team building instead of grinding and backtracking.

It is distributed as a patch applied **on top of Renegade Platinum**, just like Drayano's own additional patches. An optional French version translates everything that matters for strategy.

> **No ROMs are provided here.** You need your own legally dumped copy of Pokémon Platinum (US) and Drayano's Renegade Platinum patch.

## Features

| Feature | Details |
|---|---|
| **Level caps** | Your Pokémon can't level past the next Gym Leader's ace. At the cap they stop gaining Exp. and Rare Candies have no effect. The cap rises with each badge and is removed once you become Champion. |
| **Infinite Rare Candies** | A scientist in the Sandgem Town Pokémon Center gives you 99 Rare Candies every time you talk to him. |
| **Infinite Repel** | Using any Repel turns it on without consuming it, and it never wears off. Use one again to turn it off. |
| **Trainer Kit** | Replaces the Vs. Recorder. Use it from the Bag or register it to **Y** to open a menu, anywhere: **Heal team**, **PC** (Move Pokémon) and **Fly**. Fly follows the HM's rules (Cobble Badge, outdoors only) but no Pokémon needs to know it. The Sandgem scientist also gives you the kit. |
| **100% catch rate** | Every Poké Ball catches like a Master Ball. |
| **$1 items** | Everything costs $1 in shops. Items meant to be sold (Nugget, Pearls, Stardust, Rare Bone…) keep their sell value. |

Renegade Platinum already provides 99-copy TMs, free move tutors and relearner, and buyable evolution items. This patch doesn't change any of that.

### Level caps

| Badges | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | Champion |
|---|---|---|---|---|---|---|---|---|---|---|
| Max level | 16 | 26 | 33 | 39 | 44 | 53 | 56 | 62 | 78 | 100 |

Like a level 100 Pokémon in Gen 4, a Pokémon at the cap doesn't gain EVs from battles. Vitamins and EV-reducing Berries still work.

## Versions

| Patch | Language |
|---|---|
| `RenegadeQoL_EN.xdelta` | English, same text as Renegade Platinum. |
| `RenegadeQoL_FR.xdelta` | French names (Pokémon, moves, items, abilities, natures, types, locations), French move, item and ability descriptions, and French battle messages. Story dialogue stays in English. |

## Installation

You need:
- a dump of **Pokémon Platinum (US)**, made from your own cartridge;
- **Renegade Platinum v1.3.0**, from Drayano's official page;
- **Delta Patcher** (or any xdelta patcher).

Steps:
1. Patch your Platinum ROM with Renegade Platinum's base patch, following Drayano's instructions. Use the 4997 patch for Rev 1 dumps.
2. Apply `RenegadeQoL_EN.xdelta` **or** `RenegadeQoL_FR.xdelta` to the resulting Renegade ROM.
3. Play.

Notes:
- **Existing Renegade saves work.** If you already own the Vs. Recorder, it becomes the Trainer Kit. If a save is inside the Sandgem Pokémon Center, step outside and back in to see the scientist.
- **Don't stack patches by mistake.** Apply this patch to a clean Renegade ROM, not to a ROM that already has it.
- **Expected base ROM** (Renegade Platinum v1.3.0 built from a Platinum US Rev 1 dump): SHA-1 `d4ee068b7e0a19a848436369f145e3154afe13ca`. If Delta Patcher reports a checksum error, your base ROM is different.
- Renegade's optional additional patches (speed-up, shiny rate…) are untested together with this one.

## Building from source

The patch is built by scripts from your own Renegade ROM, so the repository contains no game data.

1. Put your Platinum (US, Rev 1) dump in `original/` and your Renegade v1.3.0 ROM at `travail/renegade_base.nds`.
2. Install **Python 3.12**, then from the project folder:
   ```bash
   python -m venv outils/venv
   ```
   ```bash
   outils\venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
3. Put **armips 0.11** (https://github.com/Kingcom/armips/releases) at `outils/armips/armips.exe`.
4. Download the reference files from the pokeplatinum decompilation:
   ```bash
   outils\venv\Scripts\python.exe scripts/fetch_refs.py
   ```
5. Build the ROM (add `--fr` for the French version):
   ```bash
   outils\venv\Scripts\python.exe -I scripts/build_qol.py
   ```
6. Build both patches (needs `outils/xdelta/xdelta3.exe`):
   ```bash
   outils\venv\Scripts\python.exe -I scripts/make_patches.py
   ```

The build script checks the original bytes at every code location it changes and stops if they don't match, so it can't silently corrupt a different base ROM.

### Project layout

```
asm/
  main.s          added code module (loaded at boot at 0x023C8000) + list of every patched location
  levelcap.s      level caps (cap table at the bottom)
  repel.s         infinite Repel
  trainer_kit.s   Trainer Kit: item functions + script commands for Fly
scripts/
  build_qol.py    builds travail/renegade_qol[_fr].nds from travail/renegade_base.nds
  make_patches.py builds the English and French xdelta patches
  pt.py           library: texts, scripts, NPCs, map headers
  gen_fr_*.py     generate the French translation files
traduction/fr/    French translation (one JSON file per category, English and French side by side)
```

### Technical notes

- Renegade's ARM9 code is almost identical to vanilla Platinum, so addresses come from the [pret/pokeplatinum](https://github.com/pret/pokeplatinum) decompilation and are checked against the binary.
- New code lives in an extra overlay that is loaded at boot into RAM the game never uses (above its heaps). It replaces a redundant call in `NitroMain`.
- The Trainer Kit reuses the Vs. Recorder's item-use slot and three unused script commands (0x004–0x006). Fly calls the game's own `FieldMoves_CheckFly`, so the HM's rules apply.
- `build_qol.py --test-vol` builds a test ROM where the Trainer Kit's Fly ignores the badge requirement.

## Credits

- **Drayano**: Renegade Platinum. This project only adds to it.
- **pret/pokeplatinum**: the Platinum decompilation, which made finding every function possible.
- **PokeAPI**: official French names and descriptions.
- **Kingcom (armips)** and **RoadrunnerWMC (ndspy)**: assembler and ROM tools.
- Pokémon © Nintendo / Game Freak / The Pokémon Company. This is a non-commercial fan project.
