"""Affiche les infos de base d'une ROM DS (en-tête, overlays, dossiers principaux)."""
import sys
import ndspy.rom

rom = ndspy.rom.NintendoDSRom.fromFile(sys.argv[1])
print("Nom :", rom.name, "| Code :", rom.idCode, "| Révision :", rom.version)
print("ARM9 :", len(rom.arm9), "octets | overlays ARM9 :", len(rom.arm9OverlayTable))
print("Fichiers :", len(rom.files))

# Fichiers clés pour nos modifications
for path in [
    "fielddata/script/scr_seq.narc",       # scripts du monde
    "fielddata/eventdata/zone_event.narc", # PNJ / événements par carte
    "itemtool/itemdata/pl_item_data.narc", # données des objets
    "msgdata/pl_msg.narc",                 # textes
]:
    try:
        fid = rom.filenames.idOf(path)
        print(f"OK  {path}  (id {fid}, {len(rom.files[fid])} octets)")
    except Exception as e:
        print(f"??  {path}  -> {e}")
