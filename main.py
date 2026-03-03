import tkinter as tk
from tkinter import font as tkfont, messagebox
import random
import time
import copy
import math


# ─────────────────────────────────────────────
#  LOGIQUE DE JEU
# ─────────────────────────────────────────────

# Partie 1: Plateau de jeu
class CongklakState:
    PLAYER1 = 1
    PLAYER2 = 2

    P1_HOLES = list(range(8, 15))   # indices 8-14
    P2_HOLES = list(range(1, 8))    # indices 1-7
    P1_HOME = 15
    P2_HOME = 0
    TOTAL = 16

    # Créer un nouveau plateau
    def __init__(self):
        # 16 cases à 0
        self.board = [0] * 16
        # Trou du joueur
        for i in self.P1_HOLES:
            self.board[i] = 7
        # Trou du IA
        for i in self.P2_HOLES:
            self.board[i] = 7
        self.current_player = self.PLAYER1

    # Copie du plateau : IA doit simuler des coups sans modifier le vrai plateau
    def clone(self):
        s = CongklakState.__new__(CongklakState)
        s.board = self.board[:]  # copie le plateau
        s.current_player = self.current_player
        return s

    # Donne-moi les trous de ce joueur
    def get_holes(self, player):
        return self.P1_HOLES if player == self.PLAYER1 else self.P2_HOLES

    # Donne-moi la maison de ce joueur
    def get_home(self, player):
        return self.P1_HOME if player == self.PLAYER1 else self.P2_HOME

    # Qui est l'adversaire ?
    def get_opponent(self, player):
        return self.PLAYER2 if player == self.PLAYER1 else self.PLAYER1

    # Trouver le trou en face
    def get_opposite(self, hole):
        """
          IA  :  [1] [2] [3] [4] [5] [6] [7]
                  |   |   |   |   |   |   |
          VOUS:  [8] [9] [10][11][12][13][14]
        """
        if hole in self.P1_HOLES:
            return hole - 7   # 8->1, 9->2, 10->3, 11->4, 12->5, 13->6, 14->7
        elif hole in self.P2_HOLES:
            return hole + 7   # 1->8, 2->9, 3->10, 4->11, 5->12, 6->13, 7->14
        return -1

    # Quels trous peut-on choisir ?
    def legal_moves(self, player):
        ''' Retourne la liste des trous du joueur qui ont au moins 1 graine
            si un trou est vide (=0), donc exclu
        '''
        return [h for h in self.get_holes(player) if self.board[h] > 0]

    # La partie est-elle finie ?
    def is_terminal(self):
        return (all(self.board[h] == 0 for h in self.P1_HOLES) and
                all(self.board[h] == 0 for h in self.P2_HOLES))  # deux côtés vides

    def do_move(self, hole):
        """
        Exécute un mouvement depuis le trou donné.
        Retourne le prochain joueur à jouer.
        Distribution dans le sens anti-horaire :
          Joueur 1 : 8->9->10->...->14->15(maison)->7->6->5->...->1->0(sauté)->8->...
          Joueur 2 : 7->6->5->...->1->0(maison)->8->9->...->14->15(sauté)->7->...
        """
        seeds = self.board[hole]
        self.board[hole] = 0
        pos = hole
        opponent_home = self.get_home(self.get_opponent(self.current_player))

        while seeds > 0:
            pos = self._next(pos, self.current_player)
            if pos == opponent_home:
                continue  # sauter la maison adverse (déjà avancé)
            # En réalité on doit sauter, donc on refait :
            # _next gère déjà le saut dans la logique ci-dessous
            self.board[pos] += 1
            seeds -= 1

        # Évaluer l'atterrissage de la dernière graine
        if pos == self.get_home(self.current_player):
            # Tour supplémentaire pour le joueur actuel
            return self.current_player

        player_holes = self.get_holes(self.current_player)
        if pos in player_holes and self.board[pos] == 1:
            # Atterri dans un trou vide de son côté -> capture
            opposite = self.get_opposite(pos)
            captured = self.board[opposite]
            self.board[opposite] = 0
            self.board[pos] = 0
            self.board[self.get_home(self.current_player)] += captured + 1
            return self.get_opponent(self.current_player)

        if pos not in (self.P1_HOME, self.P2_HOME) and self.board[pos] > 1:
            # Atterri dans un trou occupé -> continuer la distribution (déjà géré ci-dessus)
            # Géré par la boucle while ci-dessus — quand seeds > 0 on continue
            # En réalité la règle dit : si la dernière pièce tombe dans un trou occupé,
            # ramasser tout et redistribuer depuis ce trou
            # Il faut réimplémenter avec la distribution en relais
            pass

        return self.get_opponent(self.current_player)

    def _next(self, pos, player):
        """Obtenir la position suivante dans le sens anti-horaire, en sautant la maison adverse."""
        opponent_home = self.get_home(self.get_opponent(player))
        # Ordre anti-horaire : 8,9,10,11,12,13,14,15,7,6,5,4,3,2,1,0 puis recommence
        order = self.P1_HOLES + [self.P1_HOME] + list(reversed(self.P2_HOLES)) + [self.P2_HOME]
        # Circulaire pour le joueur 1. Pour le joueur 2, même chemin circulaire mais orientation différente.
        # En réalité, les deux joueurs utilisent LE MÊME chemin circulaire (anti-horaire).
        idx = order.index(pos)
        while True:
            idx = (idx + 1) % len(order)
            nxt = order[idx]
            if nxt != opponent_home:
                return nxt


# Partie 2: Exécuter un coup complet : 3 règles spéciales
def do_move_full(state, hole):
    """
    Distribution complète avec relais. Retourne (nouvel_état, prochain_joueur).

    Ordre de distribution (anti-horaire, identique pour les deux joueurs) :
      [8..14] -> [15=MAISON_J1] -> [7..1] -> [0=MAISON_J2] -> recommence

    Règles :
      Règle 4 : dernière dans sa propre maison       -> tour supplémentaire
      Règle 5 : dernière dans un trou VIDE (son côté) -> capture l'opposé -> fin de tour
      Règle 6 : dernière dans un trou OCCUPÉ (son côté) -> relais (ramasser et redistribuer)
      Sinon (trou adverse)                            -> fin de tour immédiate
    """
    s = state.clone()
    current = s.current_player
    own_home = s.get_home(current)
    own_holes = s.get_holes(current)
    opponent_home = s.get_home(s.get_opponent(current))
    order = s.P1_HOLES + [s.P1_HOME] + list(reversed(s.P2_HOLES)) + [s.P2_HOME]

    pos = hole
    for _ in range(500):
        seeds = s.board[pos]
        s.board[pos] = 0

        # L'ordre de distribution des graines
        i = order.index(pos)
        distributed = 0
        last = pos

        # Distribuer les graines une par une ; mémoriser l'état de chaque trou AVANT d'y placer une graine
        last_hole_before = 0  # mémorise le contenu du trou de destination AVANT la dernière graine

        # Distribution des graines
        while distributed < seeds:
            i = (i + 1) % len(order)
            nxt = order[i]
            if nxt == opponent_home:
                continue  # sauter la maison adverse
            if distributed == seeds - 1:
                # C'est la dernière graine — mémoriser l'état du trou AVANT de placer
                last_hole_before = s.board[nxt]
            s.board[nxt] += 1
            distributed += 1
            last = nxt

        # Règle 4 : dernière graine dans SA maison -> rejouer
        if last == own_home:
            s.current_player = current
            return s, current  # même joueur rejoue !

        # Règle 5 : dernière graine dans trou VIDE (son côté) -> capture
        # (last_hole_before == 0 signifie que le trou était vide quand la graine est arrivée)
        if last in own_holes and last_hole_before == 0:
            opp = s.get_opposite(last)
            captured = s.board[opp]
            s.board[opp] = 0
            s.board[last] = 0
            s.board[own_home] += captured + 1
            s.current_player = s.get_opponent(current)
            return s, s.get_opponent(current)

        # Règle 6 : dernière graine dans trou OCCUPÉ -> relais
        # (last_hole_before > 0 signifie que le trou avait déjà des graines)
        if last in own_holes and last_hole_before > 0:
            pos = last
            continue  # retour au début de la boucle for !

        # Cas par défaut : atterri sur un trou adverse (quel que soit son état) -> fin de tour
        s.current_player = s.get_opponent(current)
        return s, s.get_opponent(current)

    s.current_player = s.get_opponent(current)
    return s, s.get_opponent(current)


# ─────────────────────────────────────────────
#  MINIMAX WITH ALPHA-BETA PRUNING
# ─────────────────────────────────────────────

class MinimaxAI:
    def __init__(self, depth=3):
        self.depth = depth
        self.nodes_explored = 0

    # Donner un score à la position
    def evaluate(self, state):
        """Heuristique : différence de graines dans les maisons (IA = Joueur 2 = MAX)."""
        # graines IA  moins  graines VOUS
        return state.board[state.P2_HOME] - state.board[state.P1_HOME]

    # ── Article Figure 3.7 / 5.5 : GetMove(État S) : Coup ───────────────
    def GetMove(self, S):
        """
        Retourne le meilleur coup pour l'état actuel S.
        Correspond à GetMove(État S) : Coup dans l'article.
        """
        self.nodes_explored = 0
        Best_Move = None
        Alpha = -math.inf   # moins infini au départ
        Beta  =  math.inf   # plus infini au départ
        Best_Move_Value = -math.inf

        moves = S.legal_moves(S.current_player)  # coups disponibles
        if not moves:
            return None  # aucun coup possible

        for Mi in moves:
            NS, NP = do_move_full(S, Mi)  # simuler le coup -> NS=nouvel état, NP=prochain joueur
            self.nodes_explored += 1

            if NS.is_terminal():  # partie finie ?
                Current_Move_Value = self.evaluate(NS)
            elif NP == S.current_player:
                # NP est le joueur actuel (tour supplémentaire) → encore MAX
                Current_Move_Value = self.GetMax(NS, Alpha, Beta, 1)
            else:
                # NP est l'adversaire → MIN
                Current_Move_Value = self.GetMin(NS, Alpha, Beta, 1)

            if Current_Move_Value > Best_Move_Value:  # meilleur que ce qu'on a ?
                Alpha            = Current_Move_Value
                Best_Move_Value  = Current_Move_Value
                Best_Move        = Mi  # → on garde ce coup !

            # Coupure Alpha à la racine
            if Alpha >= Beta:
                break  # inutile de continuer

        # Si aucun meilleur coup trouvé (toutes pertes), choisir aléatoirement
        if Best_Move is None:
            Best_Move = random.choice(moves)

        return Best_Move

    # ── Article Figure 3.8 / 5.6 : GetMax(État S, Alpha, Beta, Profondeur D) ─
    def GetMax(self, S, Alpha, Beta, D):
        """
        Retourne la meilleure valeur (maximum) pour l'état S à la profondeur D.
        Correspond à GetMax(État S, BorneMin Alpha, BorneMax Beta, Profondeur D) : Valeur
        """
        # Cas de base : état terminal OU limite de profondeur atteinte
        if S.is_terminal() or D >= self.depth:
            return self.evaluate(S)  # → score final

        moves = S.legal_moves(S.current_player)
        if not moves:
            return self.evaluate(S)

        Best_Move_Value = -math.inf  # commence au pire score possible

        for Mi in moves:
            NS, NP = do_move_full(S, Mi)
            self.nodes_explored += 1

            if NS.is_terminal():
                Current_Move_Value = self.evaluate(NS)
            elif NP == S.current_player:
                # Tour supplémentaire → encore MAX
                Current_Move_Value = self.GetMax(NS, Alpha, Beta, D + 1)
            else:
                # Tour de l'adversaire → MIN
                Current_Move_Value = self.GetMin(NS, Alpha, Beta, D + 1)

            if Current_Move_Value > Best_Move_Value:
                Best_Move_Value = Current_Move_Value
                Alpha = max(Alpha, Best_Move_Value)  # améliore la garantie

            # Condition d'élagage Alpha-Beta (article : "Si Alpha >= Beta : couper")
            if Alpha >= Beta:
                break  # ✂️ Élaguer les branches restantes

        return Best_Move_Value

    # ── Article Figure 3.9 / 5.7 : GetMin(État S, Alpha, Beta, Profondeur D) ─
    def GetMin(self, S, Alpha, Beta, D):
        """
        Retourne la pire valeur (minimum) pour l'état S à la profondeur D.
        Correspond à GetMin(État S, BorneMin Alpha, BorneMax Beta, Profondeur D) : Valeur
        """
        # Cas de base : état terminal OU limite de profondeur atteinte
        if S.is_terminal() or D >= self.depth:
            return self.evaluate(S)

        moves = S.legal_moves(S.current_player)
        if not moves:
            return self.evaluate(S)

        Worst_Move_Value = math.inf  # commence au meilleur score possible

        for Mi in moves:
            NS, NP = do_move_full(S, Mi)
            self.nodes_explored += 1

            if NS.is_terminal():
                Current_Move_Value = self.evaluate(NS)
            elif NP == S.current_player:
                # Tour supplémentaire → encore MIN
                Current_Move_Value = self.GetMin(NS, Alpha, Beta, D + 1)
            else:
                # Tour de l'adversaire → MAX
                Current_Move_Value = self.GetMax(NS, Alpha, Beta, D + 1)

            if Current_Move_Value < Worst_Move_Value:
                Worst_Move_Value = Current_Move_Value
                Beta = min(Beta, Worst_Move_Value)  # réduit la borne haute

            # Condition d'élagage Alpha-Beta (article : "Si Alpha >= Beta : couper")
            if Alpha >= Beta:
                break  # ✂️ Élaguer les branches restantes

        return Worst_Move_Value

    # ── Alias en minuscules pour que le code GUI fonctionne toujours ───────────────
    def get_move(self, state): return self.GetMove(state)
    def get_max(self, s, a, b, d): return self.GetMax(s, a, b, d)
    def get_min(self, s, a, b, d): return self.GetMin(s, a, b, d)


# ─────────────────────────────────────────────
#  GUI
# ─────────────────────────────────────────────

# L'interface visuelle
class CongklakGUI:
    # Couleurs
    BG         = "#1a0a00"
    BOARD_BG   = "#5c2d0a"
    HOLE_EMPTY = "#3d1f07"
    HOLE_P1    = "#e8a020"
    HOLE_P2    = "#20a8e8"
    HOME_P1    = "#c87000"
    HOME_P2    = "#0070c8"
    SEED_COLOR = "#f5d060"
    TEXT_LIGHT = "#f5e6c8"
    TEXT_DARK  = "#1a0a00"
    HIGHLIGHT  = "#ffe066"
    DISABLED   = "#5c3a1a"
    GREEN_MSG  = "#50e878"
    RED_MSG    = "#e85050"

    def __init__(self, root):
        self.root = root
        self.root.title("Congklak — Minimax AI")
        self.root.configure(bg=self.BG)
        self.root.resizable(False, False)  # fenêtre non redimensionnable

        self.ai_level = tk.StringVar(value="Normal")
        self.first_player = tk.StringVar(value="Human")
        self.state = None
        self.ai = None
        self.human_player = CongklakState.PLAYER1
        self.game_active = False
        self.hole_buttons = {}

        self._build_fonts()
        self._build_main_menu() # Afficher le menu principal

    def _build_fonts(self):
        self.font_title  = tkfont.Font(family="Georgia", size=26, weight="bold")
        self.font_sub    = tkfont.Font(family="Georgia", size=13, slant="italic")
        self.font_btn    = tkfont.Font(family="Courier", size=12, weight="bold")
        self.font_hole   = tkfont.Font(family="Courier", size=11, weight="bold")
        self.font_home   = tkfont.Font(family="Courier", size=14, weight="bold")
        self.font_label  = tkfont.Font(family="Courier", size=10)
        self.font_status = tkfont.Font(family="Courier", size=11, weight="bold")
        self.font_info   = tkfont.Font(family="Courier", size=9)

    # ── MENU PRINCIPAL ──────────────────────────────────────────────────────────

    def _build_main_menu(self):
        self._clear()
        f = tk.Frame(self.root, bg=self.BG, padx=60, pady=40)
        f.pack()  # l'affiche dans la fenêtre

        tk.Label(f, text="⚬  CONGKLAK  ⚬", font=self.font_title,
                 bg=self.BG, fg=self.HIGHLIGHT).pack(pady=(0, 4))
        tk.Label(f, text="Jeu traditionnel indonésien avec IA Minimax",
                 font=self.font_sub, bg=self.BG, fg="#b89060").pack(pady=(0, 30))

        for txt, cmd in [
            ("▶  Jouer contre l'IA",    self._open_settings),
            ("ℹ  Règles du jeu",        self._show_rules),
            ("✕  Quitter",              self.root.quit),
        ]:
            tk.Button(f, text=txt, font=self.font_btn, bg=self.BOARD_BG,
                      fg=self.TEXT_LIGHT, activebackground=self.HIGHLIGHT,
                      activeforeground=self.TEXT_DARK, relief="flat",
                      width=32, pady=10, cursor="hand2",
                      command=cmd).pack(pady=6)

    # ── PARAMÈTRES ───────────────────────────────────────────────────────────

    def _open_settings(self):
        self._clear()
        f = tk.Frame(self.root, bg=self.BG, padx=60, pady=40)
        f.pack()

        tk.Label(f, text="Paramètres", font=self.font_title,
                 bg=self.BG, fg=self.HIGHLIGHT).pack(pady=(0, 24))

        # Niveau de l'IA
        tk.Label(f, text="Niveau de l'IA :", font=self.font_btn,
                 bg=self.BG, fg=self.TEXT_LIGHT).pack(anchor="w")
        lvl_f = tk.Frame(f, bg=self.BG)
        lvl_f.pack(anchor="w", pady=(4, 16))
        for lvl in ["Facile", "Normal", "Expert", "Impossible"]:
            tk.Radiobutton(lvl_f, text=lvl, variable=self.ai_level, value=lvl,
                           font=self.font_label, bg=self.BG, fg=self.TEXT_LIGHT,
                           selectcolor=self.BOARD_BG,
                           activebackground=self.BG).pack(side="left", padx=8)

        # Premier joueur
        tk.Label(f, text="Premier joueur :", font=self.font_btn,
                 bg=self.BG, fg=self.TEXT_LIGHT).pack(anchor="w")
        fp_f = tk.Frame(f, bg=self.BG)
        fp_f.pack(anchor="w", pady=(4, 24))
        for fp in ["Human", "Computer"]:
            tk.Radiobutton(fp_f, text=fp, variable=self.first_player, value=fp,
                           font=self.font_label, bg=self.BG, fg=self.TEXT_LIGHT,
                           selectcolor=self.BOARD_BG,
                           activebackground=self.BG).pack(side="left", padx=8)

        btn_f = tk.Frame(f, bg=self.BG)
        btn_f.pack()
        tk.Button(btn_f, text="✓  Démarrer", font=self.font_btn, bg=self.HOLE_P1,
                  fg=self.TEXT_DARK, relief="flat", width=16, pady=8,
                  cursor="hand2", command=self._start_game).pack(side="left", padx=8)
        tk.Button(btn_f, text="←  Retour", font=self.font_btn, bg=self.BOARD_BG,
                  fg=self.TEXT_LIGHT, relief="flat", width=16, pady=8,
                  cursor="hand2", command=self._build_main_menu).pack(side="left", padx=8)

    # ── RÈGLES ──────────────────────────────────────────────────────────────

    def _show_rules(self):
        win = tk.Toplevel(self.root)
        win.title("Règles du Congklak")
        win.configure(bg=self.BG)
        win.resizable(False, False)
        rules = (
            "RÈGLES DU CONGKLAK\n"
            "══════════════════════════════════════\n\n"
            "Plateau : 2 rangées de 7 trous + 2 maisons (16 trous).\n"
            "Départ  : 7 graines dans chaque trou (maisons vides).\n\n"
            "Tour de jeu :\n"
            "  1. Choisissez un trou de votre côté.\n"
            "  2. Distribuez les graines sens anti-horaire (une par trou).\n"
            "  3. On saute la maison adverse, pas la sienne.\n\n"
            "Règles spéciales :\n"
            "  • Dernière graine dans votre maison → rejouer.\n"
            "  • Dernière graine dans trou vide (votre côté) → capture\n"
            "    des graines du trou opposé → dans votre maison.\n"
            "  • Dernière graine dans trou occupé → ramasser et continuer.\n\n"
            "Fin de partie :\n"
            "  • Quand tous les trous des deux côtés sont vides.\n"
            "  • Le joueur avec le plus de graines dans sa maison gagne.\n\n"
            "IA : Minimax avec Alpha-Beta Pruning\n"
            "  Facile    : Aléatoire\n"
            "  Normal    : Profondeur 2\n"
            "  Expert    : Profondeur 4\n"
            "  Impossible: Profondeur 6\n"
        )
        tk.Label(win, text=rules, font=tkfont.Font(family="Courier", size=10),
                 bg=self.BG, fg=self.TEXT_LIGHT, justify="left",
                 padx=30, pady=20).pack()
        tk.Button(win, text="Fermer", font=self.font_btn, bg=self.BOARD_BG,
                  fg=self.TEXT_LIGHT, relief="flat", pady=6,
                  command=win.destroy).pack(pady=(0, 20))

    # ── DÉMARRAGE DU JEU ─────────────────────────────────────────────────────

    def _start_game(self):
        lvl = self.ai_level.get()
        depth_map = {"Facile": 0, "Normal": 2, "Expert": 4, "Impossible": 6}
        depth = depth_map[lvl]

        self.state = CongklakState()
        self.ai = MinimaxAI(depth=depth)
        self.game_active = True

        if self.first_player.get() == "Human":
            self.human_player = CongklakState.PLAYER1
            self.state.current_player = CongklakState.PLAYER1
        else:
            self.human_player = CongklakState.PLAYER1
            self.state.current_player = CongklakState.PLAYER2

        self._build_game_screen()

        if self.state.current_player != self.human_player:
            self.root.after(800, self._ai_move)  # l'IA joue en premier après un petit délai

    # ── ÉCRAN DE JEU ────────────────────────────────────────────────────────

    def _build_game_screen(self):
        self._clear()
        root = self.root

        # Barre supérieure
        top = tk.Frame(root, bg=self.BG, pady=8)
        top.pack(fill="x", padx=20)

        tk.Button(top, text="← Menu", font=self.font_label, bg=self.BOARD_BG,
                  fg=self.TEXT_LIGHT, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self._confirm_quit).pack(side="left")

        self.lbl_level = tk.Label(top,
            text=f"Niveau: {self.ai_level.get()}",
            font=self.font_label, bg=self.BG, fg="#b89060")
        self.lbl_level.pack(side="right")

        # Statut
        self.lbl_status = tk.Label(root, text="", font=self.font_status,
                                   bg=self.BG, fg=self.GREEN_MSG, pady=6)
        self.lbl_status.pack()

        # Cadre du plateau
        board_frame = tk.Frame(root, bg=self.BOARD_BG, bd=0,
                               padx=18, pady=18, relief="flat")
        board_frame.pack(padx=24, pady=4)

        self.hole_buttons = {}
        self._draw_board(board_frame)

        # Barre de score
        self.lbl_score = tk.Label(root, text="", font=self.font_status,
                                  bg=self.BG, fg=self.TEXT_LIGHT, pady=6)
        self.lbl_score.pack()

        # Informations
        self.lbl_info = tk.Label(root, text="", font=self.font_info,
                                 bg=self.BG, fg="#888060", pady=2)
        self.lbl_info.pack()

        self._refresh_board()
        self._update_status()

    # Dessiner le plateau
    def _draw_board(self, frame):
        """
        Visualisation correcte de la distribution anti-horaire :

          [MAISON_IA=gauche] [IA : 1  2  3  4  5  6  7] [          ]
          [                ] [VOUS: 8  9 10 11 12 13 14] [MAISON_VOUS=droite]

        Joueur 1 distribue gauche→droite (8→9→…→14→MAISON1→ haut-droite→gauche)   anti-horaire ✓
        Joueur 2 distribue droite→gauche (7→6→…→1→MAISON2→ bas-gauche→droite)    anti-horaire ✓

        Les deux rangées partagent le même alignement de colonnes gauche-droite :
          col 1=trous(1,8), col2=(2,9), …, col7=(7,14)
        les graines tournent visuellement autour de l'ovale dans un seul sens.
        """
        # Maison IA (GAUCHE)
        home2_frame = tk.Frame(frame, bg=self.BOARD_BG)
        home2_frame.grid(row=0, column=0, rowspan=4, padx=(0, 12), pady=4)
        self._make_home_widget(home2_frame, CongklakState.PLAYER2)

        # Trous IA (ligne 1) : ordre GAUCHE→DROITE [1,2,3,4,5,6,7]
        # Anti-horaire pour l'IA = distribuer de droite à gauche (7→6→5→4→3→2→1→MAISON2) ✓
        p2_display_order = CongklakState.P2_HOLES  # [1,2,3,4,5,6,7]

        # Étiquettes des numéros de trous IA (ligne 0, au-dessus des boutons)
        for col_idx, hole in enumerate(p2_display_order):
            tk.Label(frame, text=str(hole), font=self.font_info,
                     bg=self.BOARD_BG, fg="#80c8e8").grid(
                         row=0, column=col_idx + 1, pady=(4, 0))

        for col_idx, hole in enumerate(p2_display_order):
            btn = tk.Button(frame, text="7", font=self.font_hole,
                            width=4, height=2,
                            bg=self.HOLE_P2, fg=self.TEXT_DARK,
                            relief="flat", cursor="arrow",
                            state="disabled")  # désactivé : on ne peut pas cliquer dessus
            btn.grid(row=1, column=col_idx + 1, padx=3, pady=2)
            self.hole_buttons[hole] = btn

        # Trous JOUEUR 1 (ligne 2) : ordre GAUCHE→DROITE [8,9,10,11,12,13,14]
        # Anti-horaire pour J1 = distribuer de gauche à droite (8→9→…→14→MAISON1) ✓
        for col_idx, hole in enumerate(CongklakState.P1_HOLES):
            btn = tk.Button(frame, text="7", font=self.font_hole,
                            width=4, height=2,
                            bg=self.HOLE_P1, fg=self.TEXT_DARK,
                            relief="flat", cursor="hand2",
                            command=lambda h=hole: self._human_move(h))
            # command=... → quand on clique, appelle _human_move(h)
            # IMPORTANT : lambda h=hole → capture la valeur de hole
            # sans ça, tous les boutons appelleraient le dernier hole !
            btn.grid(row=2, column=col_idx + 1, padx=3, pady=2)
            self.hole_buttons[hole] = btn

        # Étiquettes des numéros de trous J1 (ligne 3, sous les boutons)
        for col_idx, hole in enumerate(CongklakState.P1_HOLES):
            tk.Label(frame, text=str(hole), font=self.font_info,
                     bg=self.BOARD_BG, fg="#e8c060").grid(
                         row=3, column=col_idx + 1, pady=(0, 4))

        # Maison JOUEUR 1 (DROITE)
        home1_frame = tk.Frame(frame, bg=self.BOARD_BG)
        home1_frame.grid(row=0, column=8, rowspan=4, padx=(12, 0), pady=4)
        self._make_home_widget(home1_frame, CongklakState.PLAYER1)

        # Étiquettes de direction
        tk.Label(frame, text="IA → sens de semis →", font=self.font_info,
                 bg=self.BOARD_BG, fg=self.HOLE_P2).grid(
                     row=4, column=1, columnspan=7, sticky="w", pady=(4, 0))
        tk.Label(frame, text="← sens de semis ← Vous", font=self.font_info,
                 bg=self.BOARD_BG, fg=self.HOLE_P1).grid(
                     row=5, column=1, columnspan=7, sticky="e")

    def _make_home_widget(self, frame, player):
        color = self.HOME_P1 if player == CongklakState.PLAYER1 else self.HOME_P2
        lbl_name = "Maison\nVous" if player == CongklakState.PLAYER1 else "Maison\nIA"
        tk.Label(frame, text=lbl_name, font=self.font_info,
                 bg=self.BOARD_BG, fg=color).pack()
        lbl = tk.Label(frame, text="0", font=self.font_home,
                       bg=color, fg=self.TEXT_DARK,
                       width=5, height=4, relief="flat")
        lbl.pack(pady=4)
        attr = "lbl_home1" if player == CongklakState.PLAYER1 else "lbl_home2"
        setattr(self, attr, lbl)

    # ── RAFRAÎCHISSEMENT ────────────────────────────────────────────────────────

    # Mettre à jour l'affichage
    def _refresh_board(self):
        b = self.state.board  # raccourci
        for hole, btn in self.hole_buttons.items():
            val = b[hole]              # nombre de graines
            btn.config(text=str(val))  # affiche le nombre
            if hole in CongklakState.P1_HOLES:
                # Trou vide → marron sombre, sinon orange
                base = self.HOLE_P1 if val > 0 else self.HOLE_EMPTY
                btn.config(bg=base)
            else:
                # Trou IA vide → marron sombre, sinon bleu
                base = self.HOLE_P2 if val > 0 else self.HOLE_EMPTY
                btn.config(bg=base)

        # Mettre à jour les maisons
        self.lbl_home1.config(text=str(b[CongklakState.P1_HOME]))
        self.lbl_home2.config(text=str(b[CongklakState.P2_HOME]))

        # Mettre à jour le score
        total = sum(b)
        self.lbl_score.config(
            text=f"Vous: {b[CongklakState.P1_HOME]}  •  "
                 f"IA: {b[CongklakState.P2_HOME]}  •  "
                 f"En jeu: {total - b[CongklakState.P1_HOME] - b[CongklakState.P2_HOME]}")

    def _update_status(self):
        if not self.game_active:
            return
        if self.state.current_player == self.human_player:
            self.lbl_status.config(text="Votre tour — Choisissez un trou",
                                   fg=self.GREEN_MSG)
            self._set_p1_buttons(True)
        else:
            self.lbl_status.config(text="L'IA réfléchit…", fg="#e8c060")
            self._set_p1_buttons(False)

    def _set_p1_buttons(self, enabled):
        legal = self.state.legal_moves(self.human_player)
        for hole in CongklakState.P1_HOLES:
            btn = self.hole_buttons[hole]
            if enabled and hole in legal:
                btn.config(state="normal", cursor="hand2",
                           relief="flat")
            else:
                btn.config(state="disabled", cursor="arrow")

    def _highlight_hole(self, hole, on):
        if hole not in self.hole_buttons:
            return
        if on:
            self.hole_buttons[hole].config(bg=self.HIGHLIGHT, fg=self.TEXT_DARK)
        else:
            self._refresh_board()

    # ── COUP DU JOUEUR ─────────────────────────────────────────────────────

    def _human_move(self, hole):
        if not self.game_active:
            return
        if self.state.current_player != self.human_player:
            return
        if hole not in self.state.legal_moves(self.human_player):
            return

        self._set_p1_buttons(False)              # désactive vos boutons
        self._highlight_hole(hole, True)         # surligne le trou choisi (jaune)
        self.root.after(300, lambda: self._apply_move(hole))
        # Attend 300ms puis applique le coup (effet visuel)

    def _apply_move(self, hole):
        new_state, next_player = do_move_full(self.state, hole)  # exécute le coup
        self.state = new_state        # met à jour l'état
        self._refresh_board()         # rafraîchit l'affichage

        if self.state.is_terminal():  # partie finie ?
            self._end_game()
            return

        self._check_soft_endgame()    # victoire évidente ?
        if not self.game_active:
            return

        self.state.current_player = next_player
        self._update_status()

        if next_player != self.human_player:     # c'est le tour de l'IA ?
            self.root.after(700, self._ai_move)  # → l'IA joue après 700ms

    # ── COUP DE L'IA ────────────────────────────────────────────────────────

    def _ai_move(self):
        if not self.game_active:
            return

        lvl = self.ai_level.get()
        t0 = time.time()  # chronomètre start

        if lvl == "Facile":
            moves = self.state.legal_moves(self.state.current_player)
            move = random.choice(moves) if moves else None  # coup aléatoire
        else:
            move = self.ai.get_move(self.state)  # Minimax !

        elapsed = time.time() - t0  # temps écoulé

        if move is None:
            self.state.current_player = self.human_player
            self._update_status()
            return

        # Affiche les infos en bas
        self.lbl_info.config(
            text=f"IA: trou {move}  |  temps: {elapsed:.2f}s  |  "
                 f"noeuds explorés: {self.ai.nodes_explored if lvl != 'Facile' else 'N/A'}")

        self._highlight_hole(move, True)               # surligne le trou de l'IA
        self.root.after(500, lambda: self._apply_ai_move(move))  # attend 500ms

    def _apply_ai_move(self, move):
        new_state, next_player = do_move_full(self.state, move)
        self.state = new_state
        self._refresh_board()

        if self.state.is_terminal():
            self._end_game()
            return

        self._check_soft_endgame()
        if not self.game_active:
            return

        self.state.current_player = next_player
        self._update_status()

        if next_player != self.human_player:
            self.root.after(800, self._ai_move)

    # ── DÉTECTION DE FIN DE PARTIE ÉVIDENTE ────────────────────────────────

    def _check_soft_endgame(self):
        total_seeds = 98  # 7 trous * 7 graines * 2 joueurs
        half = total_seeds // 2 + 1  # majorité absolue = 50 graines
        b = self.state.board
        if b[CongklakState.P1_HOME] >= half:
            # Vous avez déjà 50+ graines → vous avez gagné !
            if messagebox.askyesno("Victoire évidente",
                                   f"Vous avez {b[CongklakState.P1_HOME]} graines !\n"
                                   "La victoire est évidente. Terminer la partie ?"):
                self._end_game(forced=True)
        elif b[CongklakState.P2_HOME] >= half:
            # L'IA a 50+ graines → défaite évidente
            if messagebox.askyesno("Défaite évidente",
                                   f"L'IA a {b[CongklakState.P2_HOME]} graines !\n"
                                   "La défaite est évidente. Terminer la partie ?"):
                self._end_game(forced=True)

    # ── FIN DE PARTIE ───────────────────────────────────────────────────────

    def _end_game(self, forced=False):
        self.game_active = False      # bloque toute interaction
        self._set_p1_buttons(False)
        b = self.state.board
        p1 = b[CongklakState.P1_HOME]  # vos graines
        p2 = b[CongklakState.P2_HOME]  # graines de l'IA

        if p1 > p2:
            msg = f"🎉 Vous gagnez !\nVous: {p1}  •  IA: {p2}"
            color = self.GREEN_MSG
        elif p2 > p1:
            msg = f"💻 L'IA gagne !\nVous: {p1}  •  IA: {p2}"
            color = self.RED_MSG
        else:
            msg = f"🤝 Égalité !\nVous: {p1}  •  IA: {p2}"
            color = self.HIGHLIGHT

        self.lbl_status.config(text=msg, fg=color)

        # Afficher la fenêtre de résultat
        result_win = tk.Toplevel(self.root)
        result_win.title("Résultat")
        result_win.configure(bg=self.BG)
        result_win.resizable(False, False)
        tk.Label(result_win, text=msg, font=self.font_title,
                 bg=self.BG, fg=color, padx=40, pady=30).pack()
        btn_f = tk.Frame(result_win, bg=self.BG)
        btn_f.pack(pady=(0, 20))
        tk.Button(btn_f, text="Rejouer", font=self.font_btn, bg=self.HOLE_P1,
                  fg=self.TEXT_DARK, relief="flat", width=14, pady=8,
                  cursor="hand2",
                  command=lambda: [result_win.destroy(), self._start_game()]
                  ).pack(side="left", padx=8)
        tk.Button(btn_f, text="Menu", font=self.font_btn, bg=self.BOARD_BG,
                  fg=self.TEXT_LIGHT, relief="flat", width=14, pady=8,
                  cursor="hand2",
                  command=lambda: [result_win.destroy(), self._build_main_menu()]
                  ).pack(side="left", padx=8)

    def _confirm_quit(self):
        if self.game_active:
            if messagebox.askyesno("Quitter", "Abandonner la partie en cours ?"):
                self.game_active = False
                self._build_main_menu()
        else:
            self._build_main_menu()

    # ── UTILITAIRE ────────────────────────────────────────────────────────

    def _clear(self):
        # winfo_children() = tous les éléments affichés
        # destroy() = supprime chaque élément -> repart d'une fenêtre vide
        for w in self.root.winfo_children():
            w.destroy()


# ─────────────────────────────────────────────
#  POINT D'ENTRÉE
# ─────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("720x520")  # taille : 720 pixels × 520 pixels
    app = CongklakGUI(root)
    root.mainloop()  # attend les clics/événements en boucle