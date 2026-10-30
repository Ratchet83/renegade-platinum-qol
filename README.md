# Renegade Platinum — QoL

Améliorations de confort pour **Pokémon Renegade Platinum v1.3.0** (Drayano), pour se concentrer sur les combats et la gestion d'équipe.

Ce dépôt ne contient **aucune ROM ni aucun patch Renegade** : seulement les scripts et le code qui construisent la ROM modifiée à partir de ta propre ROM.

## Fonctionnalités

| Fonctionnalité | Détail |
|---|---|
| Super Bonbons infinis | Un scientifique au Centre Pokémon de Littorella donne 99 Super Bonbons à chaque fois |
| Level caps | Niveau max selon les badges : 16 / 26 / 33 / 39 / 44 / 53 / 56 / 62 / 78, puis aucune limite après la Ligue. Au cap : plus d'XP en combat, Super Bonbon refusé |
| Repousse infini | Utiliser un Repousse l'active sans le consommer ; le réutiliser le désactive |
| Capture à 100 % | Toutes les Poké Balls capturent à coup sûr |
| Objets à 1 $ | Tout coûte 1 $ en boutique ; les objets à revendre (Pépite, Perles…) gardent leur prix |
| Trainer Kit | L'ancien Vs. Recorder (donné aussi par le scientifique de Littorella) ouvre un menu utilisable partout, assignable à Y : soigner l'équipe, PC (déplacer des Pokémon), Vol (mêmes règles que la CS : badge Pavé, extérieur) |

Déjà présents dans Renegade : CT à 99 exemplaires (+ PNJ de recharge à la Ligue), maître des capacités et tuteurs gratuits, Pierre Stase achetable.

## Organisation

```
asm/
  main.s        module de code ajouté (chargé au démarrage à 0x023C8000) + liste des endroits modifiés
  levelcap.s    level caps (table des caps en bas du fichier)
  repel.s       Repousse infini
  trainer_kit.s Trainer Kit : fonctions de l'objet + commandes de script pour le Vol
scripts/
  build_qol.py  construit travail/renegade_qol.nds à partir de travail/renegade_base.nds
  pt.py         bibliothèque : textes, scripts, PNJ, en-têtes de cartes
  code.py       désassemblage Thumb (capstone)
  fetch_refs.py télécharge les références de la décompilation pokeplatinum
  explore_map.py, diff_roms.py, find_*.py, verify_*.py : outils d'analyse
```

## Installation depuis zéro (Windows)

1. **ROM de base** : dumpe ta cartouche Pokémon Platine **US (Rev 1)** et place-la dans `original/`.
2. **Patch Renegade** : télécharge Renegade Platinum v1.3.0 depuis la page officielle de Drayano, applique le patch de base avec DeltaPatcher sur une **copie** de la ROM, et enregistre le résultat sous `travail/renegade_base.nds`.
3. **Python 3.12** (`winget install Python.Python.3.12`), puis dans `C:\RomHack` :
   ```bash
   python -m venv outils/venv
   ```
   ```bash
   outils\venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
4. **armips 0.11** : télécharge-le depuis https://github.com/Kingcom/armips/releases et place `armips.exe` dans `outils/armips/`.
5. **Références** :
   ```bash
   outils\venv\Scripts\python.exe scripts/fetch_refs.py
   ```

## Construire la ROM

```bash
outils\venv\Scripts\python.exe -I scripts/build_qol.py
```

Résultat : `travail/renegade_qol.nds`. La ROM de base n'est jamais modifiée ; le script vérifie les octets d'origine avant chaque modification du code.

## Notes techniques

- Le code ARM9 de Renegade est quasiment identique à Platine d'origine : les adresses viennent de la décompilation [pret/pokeplatinum](https://github.com/pret/pokeplatinum), vérifiées dans le binaire.
- Le code ajouté vit dans un nouvel overlay (122) chargé au démarrage dans une zone de RAM inutilisée (`0x023C8000`), à la place d'un appel redondant de `NitroMain`.
- Prévu pour la suite : traduction française complète.
