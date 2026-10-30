# Renegade Platinum QoL

*[English version](README.md)*

Des améliorations de confort pour **Pokémon Renegade Platinum v1.3.0** de Drayano, pour se concentrer sur les combats et la gestion d'équipe plutôt que sur l'entraînement et les allers-retours.

Le projet se présente sous forme de patch, à appliquer **par-dessus Renegade Platinum**, comme les patchs additionnels de Drayano. Une version française optionnelle traduit tout ce qui compte pour la stratégie.

> **Aucune ROM n'est fournie ici.** Il vous faut votre propre copie de Pokémon Platine (US), obtenue légalement, et le patch Renegade Platinum de Drayano.

## Fonctionnalités

| Fonctionnalité | Détails |
|---|---|
| **Level caps** | Vos Pokémon ne peuvent pas dépasser le niveau du Pokémon le plus fort du prochain Champion d'Arène. Au cap, ils ne gagnent plus d'expérience et les Super Bonbons n'ont aucun effet. Le cap monte à chaque badge et disparaît une fois Maître de la Ligue. |
| **Super Bonbons infinis** | Un scientifique, au Centre Pokémon de Littorella, donne 99 Super Bonbons à chaque fois qu'on lui parle. |
| **Repousse infini** | Utiliser un Repousse l'active sans le consommer, et l'effet ne s'arrête jamais. Réutilisez-le pour le désactiver. |
| **Kit Dresseur** | Remplace le Magnéto VS. Utilisé depuis le Sac ou assigné au bouton **Y**, il ouvre un menu, partout : **Soigner**, **PC** (déplacer des Pokémon) et **Vol**. Le Vol suit les règles de la CS (Badge Pavé, à l'extérieur uniquement), sans qu'aucun Pokémon ait besoin de la capacité. Le scientifique de Littorella donne aussi le kit. |
| **Capture à 100 %** | Toutes les Poké Balls capturent comme une Master Ball. |
| **Objets à 1 $** | Tout coûte 1 $ en boutique. Les objets à revendre (Pépite, Perles, Poussière Étoile, Os Rare…) gardent leur prix de revente. |

Renegade Platinum propose déjà des CT en 99 exemplaires, un Maître des Capacités et des tuteurs gratuits, et des objets d'évolution en vente. Ce patch n'y touche pas.

### Level caps

| Badges | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | Maître |
|---|---|---|---|---|---|---|---|---|---|---|
| Niveau max | 16 | 26 | 33 | 39 | 44 | 53 | 56 | 62 | 78 | 100 |

Comme un Pokémon niveau 100 en 4G, un Pokémon au cap ne gagne plus d'EV en combat. Les vitamines et les baies qui baissent les EV fonctionnent toujours.

## Versions

| Patch | Langue |
|---|---|
| `RenegadeQoL_EN.xdelta` | Anglais, mêmes textes que Renegade Platinum. |
| `RenegadeQoL_FR.xdelta` | Noms en français (Pokémon, capacités, objets, talents, natures, types, lieux), descriptions des capacités, objets et talents en français, et messages de combat en français. Les dialogues de l'histoire restent en anglais. |

## Installation

Il vous faut :
- un dump de **Pokémon Platine (US)**, fait à partir de votre propre cartouche ;
- **Renegade Platinum v1.3.0**, sur la page officielle de Drayano ;
- **Delta Patcher** (ou tout autre outil pour patchs xdelta).

Étapes :
1. Appliquez le patch de base de Renegade Platinum sur votre ROM Platine, en suivant les instructions de Drayano. Utilisez le patch 4997 pour une ROM Rev 1.
2. Appliquez `RenegadeQoL_EN.xdelta` **ou** `RenegadeQoL_FR.xdelta` sur la ROM Renegade obtenue.
3. Jouez.

Remarques :
- **Les sauvegardes Renegade existantes fonctionnent.** Si vous avez déjà le Magnéto VS, il devient le Kit Dresseur. Si la sauvegarde a été faite dans le Centre Pokémon de Littorella, sortez puis revenez pour voir le scientifique.
- **N'appliquez pas le patch deux fois.** Appliquez-le sur une ROM Renegade propre, pas sur une ROM qui l'a déjà.
- **ROM de base attendue** (Renegade Platinum v1.3.0 construite à partir d'un dump Platine US Rev 1) : SHA-1 `d4ee068b7e0a19a848436369f145e3154afe13ca`. Si Delta Patcher signale une erreur de checksum, votre ROM de base est différente.
- Les patchs additionnels optionnels de Renegade (accélération, taux de shiny…) n'ont pas été testés avec celui-ci.

## Construire depuis les sources

Le patch est construit par des scripts, à partir de votre propre ROM Renegade : le dépôt ne contient aucune donnée du jeu.

1. Placez votre dump Platine (US, Rev 1) dans `original/` et votre ROM Renegade v1.3.0 en `travail/renegade_base.nds`.
2. Installez **Python 3.12**, puis dans le dossier du projet :
   ```bash
   python -m venv outils/venv
   ```
   ```bash
   outils\venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
3. Placez **armips 0.11** (https://github.com/Kingcom/armips/releases) en `outils/armips/armips.exe`.
4. Téléchargez les fichiers de référence de la décompilation pokeplatinum :
   ```bash
   outils\venv\Scripts\python.exe scripts/fetch_refs.py
   ```
5. Construisez la ROM (ajoutez `--fr` pour la version française) :
   ```bash
   outils\venv\Scripts\python.exe -I scripts/build_qol.py
   ```
6. Construisez les deux patchs (nécessite `outils/xdelta/xdelta3.exe`) :
   ```bash
   outils\venv\Scripts\python.exe -I scripts/make_patches.py
   ```

Le script de construction vérifie les octets d'origine à chaque endroit du code qu'il modifie, et s'arrête s'ils ne correspondent pas. Il ne peut donc pas abîmer en silence une autre ROM de base.

### Organisation

```
asm/
  main.s          module de code ajouté (chargé au démarrage en 0x023C8000) + liste de tous les endroits modifiés
  levelcap.s      level caps (table des caps en bas du fichier)
  repel.s         Repousse infini
  trainer_kit.s   Kit Dresseur : fonctions de l'objet + commandes de script pour le Vol
scripts/
  build_qol.py    construit travail/renegade_qol[_fr].nds à partir de travail/renegade_base.nds
  make_patches.py construit les patchs xdelta anglais et français
  pt.py           bibliothèque : textes, scripts, PNJ, en-têtes de cartes
  gen_fr_*.py     génèrent les fichiers de traduction française
traduction/fr/    traduction française (un fichier JSON par catégorie, anglais et français côte à côte)
```

### Notes techniques

- Le code ARM9 de Renegade est quasiment identique à celui de Platine d'origine. Les adresses viennent donc de la décompilation [pret/pokeplatinum](https://github.com/pret/pokeplatinum), et sont vérifiées dans le binaire.
- Le code ajouté vit dans un overlay supplémentaire, chargé au démarrage dans une zone de RAM que le jeu n'utilise jamais (au-dessus de ses tas mémoire). Il remplace un appel redondant de `NitroMain`.
- Le Kit Dresseur reprend l'emplacement d'utilisation du Magnéto VS et trois commandes de script inutilisées (0x004 à 0x006). Le Vol appelle la vérification d'origine du jeu, `FieldMoves_CheckFly`, donc les règles de la CS s'appliquent.
- `build_qol.py --test-vol` construit une ROM de test où le Vol du Kit Dresseur ignore le badge.

## Crédits

- **Drayano** : Renegade Platinum. Ce projet ne fait qu'y ajouter des choses.
- **pret/pokeplatinum** : la décompilation de Platine, sans laquelle il aurait été impossible de trouver chaque fonction.
- **PokeAPI** : noms et descriptions officiels en français.
- **Kingcom (armips)** et **RoadrunnerWMC (ndspy)** : assembleur et outils pour ROM.
- Pokémon © Nintendo / Game Freak / The Pokémon Company. Projet de fan non commercial.
