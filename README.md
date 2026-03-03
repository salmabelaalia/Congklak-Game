# 🎮 Congklak — Minimax AI

> Implémentation de l'algorithme **Minimax avec élagage Alpha-Bêta** comme joueur informatique dans le jeu traditionnel indonésien **Congklak**.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange)
![Algorithm](https://img.shields.io/badge/Algorithm-Minimax%20%2B%20Alpha--Beta-green)
![License](https://img.shields.io/badge/License-MIT-purple)

---

## 📖 Description

Ce projet digitalise le jeu de plateau traditionnel **Congklak**, populaire en Indonésie et en Asie du Sud-Est. Il intègre une intelligence artificielle basée sur l'algorithme **Minimax optimisé par l'élagage Alpha-Bêta**, permettant à l'ordinateur de jouer de manière stratégique avec plusieurs niveaux de difficulté.

Ce travail est basé sur l'article de recherche :
> *"Implementation of Minimax with Alpha-Beta Pruning as Computer Player in Congklak"*
> — Brian Sumali, Ivan Michael Siregar, Rosalina — President University, Indonésie (2016)

---

## 🎯 Objectifs

- ✅ Créer une application jouable de Congklak
- ✅ Intégrer une IA intelligente comme adversaire
- ✅ Proposer plusieurs niveaux de difficulté
- ✅ Obtenir des décisions en moins de **2 secondes** par coup
- ✅ Préserver et valoriser un jeu traditionnel via la digitalisation

---

## 🕹️ Le Jeu Congklak

Le **Congklak** est un jeu de type **mancala** à deux joueurs, à information parfaite. Il sollicite la réflexion, la planification et les capacités mathématiques.

### Plateau de jeu

```
[MAISON IA = 0]  [1][2][3][4][5][6][7]              ← rangée de l'IA
                 [8][9][10][11][12][13][14]  [MAISON VOUS = 15]  ← votre rangée
```

- **16 cases** au total : 14 trous + 2 maisons
- **Au départ** : 7 graines dans chaque trou, maisons vides
- **But** : accumuler le plus de graines dans sa maison

### Règles spéciales

| # | Situation | Résultat |
|---|-----------|----------|
| 4 | Dernière graine → **votre maison** | Vous **rejouez** |
| 5 | Dernière graine → **trou vide** (votre côté) | **Capture** des graines du trou opposé |
| 6 | Dernière graine → **trou occupé** (votre côté) | **Relais** : ramasser et continuer |

---

## 🧠 Intelligence Artificielle

### Algorithme Minimax

Minimax est une technique de recherche en profondeur (**DFS**) pour les jeux séquentiels à deux joueurs :
- **MAX** = l'IA → cherche à **maximiser** son score
- **MIN** = le joueur humain → cherche à **minimiser** le score de l'IA

```
Complexité Minimax : O(b^p)
→ explore TOUS les nœuds jusqu'à la profondeur p
```

### Élagage Alpha-Bêta

Optimisation de Minimax qui **réduit drastiquement** le nombre de nœuds explorés sans modifier le résultat :

```
α (alpha) : meilleure valeur garantie pour MAX (IA)
β (bêta)  : meilleure valeur garantie pour MIN (Joueur)

Condition de coupe : si α ≥ β → on ignore la branche
```

```
Complexité Alpha-Bêta : O(b^(p/2))
→ Minimax explore 36 nœuds, Alpha-Bêta seulement 3 !
```

### Fonction d'évaluation

```python
def evaluate(state):
    return state.board[P2_HOME] - state.board[P1_HOME]
    # Positif = l'IA avantage, Négatif = le joueur avantage
```

### Les 3 fonctions principales

| Fonction | Rôle |
|----------|------|
| `GetMove(S)` | Point d'entrée — choisit le **meilleur trou** à jouer |
| `GetMax(S, α, β, D)` | Recherche la **valeur maximale** (tour IA) |
| `GetMin(S, α, β, D)` | Recherche la **valeur minimale** (tour joueur) |

---

## 🎚️ Niveaux de difficulté

| Niveau | Stratégie | Profondeur | Temps moyen |
|--------|-----------|-----------|-------------|
| 🟢 Facile | Coup **aléatoire** | — | < 0.01s |
| 🟡 Normal | Minimax | 2 | ~0.30s |
| 🟠 Expert | Minimax | 4 | ~0.70s |
| 🔴 Impossible | Minimax | 6 | ~1.30s |

> ⚠️ Au niveau **Impossible**, l'IA gagne systématiquement si elle joue en premier.

---

## 🏗️ Architecture du code

```
congklak.py
│
├── CongklakState          # Partie 1 : Plateau de jeu
│   ├── __init__()         # Initialise le plateau (16 cases, 7 graines)
│   ├── clone()            # Copie du plateau (pour simulations IA)
│   ├── get_holes()        # Retourne les trous d'un joueur
│   ├── get_home()         # Retourne la maison d'un joueur
│   ├── get_opponent()     # Retourne l'adversaire
│   ├── get_opposite()     # Retourne le trou en face
│   ├── legal_moves()      # Coups légaux disponibles
│   └── is_terminal()      # Vérifie si la partie est finie
│
├── do_move_full()         # Partie 2 : Exécution d'un coup complet
│   ├── Règle 4            # Dernière graine → maison → rejouer
│   ├── Règle 5            # Dernière graine → trou vide → capture
│   └── Règle 6            # Dernière graine → trou occupé → relais
│
├── MinimaxAI              # Partie 3 : Intelligence Artificielle
│   ├── evaluate()         # Fonction d'évaluation heuristique
│   ├── GetMove()          # Choisit le meilleur coup (point d'entrée)
│   ├── GetMax()           # Maximise le score (tour IA)
│   └── GetMin()           # Minimise le score (tour joueur)
│
└── CongklakGUI            # Partie 4 : Interface graphique (Tkinter)
    ├── _build_main_menu() # Affiche le menu principal
    ├── _open_settings()   # Paramètres (niveau, premier joueur)
    ├── _build_game_screen()# Plateau de jeu visuel
    ├── _human_move()      # Gestion du coup humain
    ├── _ai_move()         # Déclenchement du coup IA
    └── _end_game()        # Affichage du résultat final
```

---

## 🚀 Installation et lancement

### Prérequis

- **Python 3.8+**
- **Tkinter** (inclus par défaut avec Python)

### Cloner le projet

```bash
git clone https://github.com/salmabelaalia/Congklak-Game.git
cd Congklak-Game
```

### Lancer le jeu

```bash
python main.py
```

> 💡 **Conseil** : Lancez depuis le terminal ou un éditeur (VS Code, PyCharm) pour éviter l'icône du navigateur dans la barre des tâches.

---

## 🖥️ Interface

```
┌─────────────────────────────────────────┐
│  🎮 Congklak — Minimax AI               │
├─────────────────────────────────────────┤
│                                         │
│   ⚬  CONGKLAK  ⚬                       │
│   Jeu traditionnel indonésien           │
│                                         │
│   ▶  Jouer contre l'IA                 │
│   ℹ  Règles du jeu                     │
│   ✕  Quitter                           │
│                                         │
└─────────────────────────────────────────┘
```

### Écran de jeu

```
[Maison IA]  [1][2][3][4][5][6][7]              [        ]
[          ] [8][9][10][11][12][13][14] [Maison VOUS]

Vous: 0  •  IA: 0  •  En jeu: 98
IA: trou 3  |  temps: 0.32s  |  noeuds explorés: 247
```

---

## 📊 Performances

Temps de calcul enregistrés pour les 5 premiers coups :

| Coup | Normal (~0.3s) | Expert (~0.7s) | Impossible (~1.3s) |
|------|---------------|----------------|-------------------|
| 1er  | 0.32s | 0.93s | 1.10s |
| 2ème | 0.29s | 0.70s | 0.70s |
| 3ème | 0.28s | 0.64s | 1.29s |
| 4ème | 0.34s | 0.32s | 1.50s |
| 5ème | 0.27s | 0.35s | 0.30s |

✅ Temps toujours **< 2 secondes** — IA fluide en temps réel.

---

## 🔍 Analyse critique

### Points forts
- ✅ Algorithme Minimax adapté aux jeux à information parfaite
- ✅ Utilisation efficace de l'Alpha-Beta Pruning
- ✅ Réduction significative du nombre de nœuds explorés
- ✅ Implémentation complète et fonctionnelle
- ✅ Bonne prise en compte des règles spécifiques (relais, capture, tour bonus)
- ✅ Temps de réponse acceptable pour une application interactive

### Points faibles
- ⚠️ Fonction d'évaluation trop simplifiée (différence brute de graines)
- ⚠️ Profondeur de recherche limitée à 6
- ⚠️ Absence de mécanisme d'apprentissage automatique
- ⚠️ IA basée uniquement sur des règles fixes
- ⚠️ Manque de comparaison avec d'autres approches (Monte-Carlo, Deep Learning)

---

## 📚 Références

- Sumali, B., Siregar, I.M., Rosalina (2016). *Implementation of Minimax with Alpha-Beta Pruning as Computer Player in Congklak*. Jurnal Teknik Informatika dan Sistem Informasi, Vol. 2, No. 2.
- Russell, S. & Norvig, P. (2009). *Artificial Intelligence: A Modern Approach* (3rd Edition).
- Fuller, S.H., Gaschnig, J.G., Gillogly (1973). *Analysis of the Alpha-Beta Pruning*. Carnegie Mellon University.

## 📄 Licence

Ce projet est sous licence **MIT** — libre d'utilisation, modification et distribution.