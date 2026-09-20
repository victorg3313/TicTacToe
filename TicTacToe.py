import tkinter as tk
from tkinter import font as tkfont, ttk
import random
import platform
import threading
import json
import os


COLOR_BG        = "#05060c"
COLOR_CARD_BG   = "#0d1020"
COLOR_CARD_EDGE = "#1c2140"
COLOR_GRID      = "#10142a"
COLOR_HOVER     = "#181e3c"
COLOR_X         = "#00f3ff"
COLOR_X_GLOW    = "#0a4a52"
COLOR_O         = "#ff2a75"
COLOR_O_GLOW    = "#4a0a24"
COLOR_WIN       = "#39ff88"
COLOR_TEXT      = "#eef2ff"
COLOR_MUTED     = "#6672a3"
COLOR_ACCENT    = "#9b5cff"

NOMBRES_NIVELES = {
    1: ("Novato",     "🟢"),
    2: ("Aficionado", "🟡"),
    3: ("Intermedio", "🟠"),
    4: ("Avanzado",   "🔴"),
    5: ("Casi perfecta", "🟣"),
}

CELL = 118
PAD  = 8

BRAIN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ttt_brain.json")


AI_EPSILON = {1: 0.60, 2: 0.40, 3: 0.20, 4: 0.08, 5: 0.0}

WINS = [(0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)]



V = {}  


def check_winner_str(state):
    for a, b, c in WINS:
        if state[a] != " " and state[a] == state[b] == state[c]:
            return state[a]
    return None


def canonical(board, player):
    """Convierte el tablero a la perspectiva de 'player', para que la
    misma tabla V sirva para X y para O (simetría)."""
    if player == "X":
        return "".join(board)
    return "".join("O" if ch == "X" else ("X" if ch == "O" else " ") for ch in board)


def get_value(state):
    v = V.get(state)
    if v is not None:
        return v
    winner = check_winner_str(state)
    if winner == "X":
        v = 1.0
    elif winner == "O":
        v = 0.0
    else:
        v = 0.5  
    V[state] = v
    return v


def train_brain(episodes=60000, alpha=0.4, eps_start=0.3, eps_end=0.02, progress_cb=None):
    """Entrena jugando `episodes` partidas de la IA contra sí misma
    (self-play) y actualizando V con la regla de diferencia temporal:
        V(s) <- V(s) + alpha * (V(s') - V(s))
    """
    for ep in range(episodes):
        epsilon = eps_start + (eps_end - eps_start) * (ep / episodes)
        board = [" "] * 9
        player = "X"
        last_state = {"X": None, "O": None}

        while True:
            avail = [i for i, v in enumerate(board) if v == " "]

            if random.random() < epsilon:
                action = random.choice(avail)
            else:
                best_val, best_actions = -1, []
                for a in avail:
                    board[a] = player
                    val = get_value(canonical(board, player))
                    board[a] = " "
                    if val > best_val:
                        best_val, best_actions = val, [a]
                    elif val == best_val:
                        best_actions.append(a)
                action = random.choice(best_actions)

            board[action] = player
            cs = canonical(board, player)
            v_new = get_value(cs)
            if last_state[player] is not None:
                v_old = get_value(last_state[player])
                V[last_state[player]] = v_old + alpha * (v_new - v_old)
            last_state[player] = cs

            winner = check_winner_str("".join(board))
            done = winner is not None or " " not in board
            if done:
                for p in ("X", "O"):
                    if last_state[p] is not None:
                        v_term = get_value(canonical(board, p))
                        v_old = get_value(last_state[p])
                        V[last_state[p]] = v_old + alpha * (v_term - v_old)
                break

            player = "O" if player == "X" else "X"

        if progress_cb and ep % 2000 == 0:
            progress_cb(ep / episodes)

    if progress_cb:
        progress_cb(1.0)


def save_brain(path=BRAIN_FILE):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(V, f)
    except OSError:
        pass  


def load_brain(path=BRAIN_FILE):
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            V.update(json.load(f))
        return True
    except (OSError, json.JSONDecodeError):
        return False


def ai_choose_move(flat_board, level):
    """La IA (siempre 'O') elige jugada usando lo que aprendió en V.
    `level` solo controla cuánto explora (se equivoca) a propósito;
    la evaluación de cada jugada siempre viene del modelo entrenado."""
    avail = [i for i, v in enumerate(flat_board) if v == " "]
    epsilon = AI_EPSILON.get(level, 0.0)

    if random.random() < epsilon:
        return random.choice(avail)

    best_val, best_actions = -1, []
    for a in avail:
        flat_board[a] = "O"
        val = get_value(canonical(flat_board, "O"))
        flat_board[a] = " "
        if val > best_val:
            best_val, best_actions = val, [a]
        elif val == best_val:
            best_actions.append(a)
    return random.choice(best_actions)


class TrainingSplash:
    def __init__(self, root, on_done):
        self.root = root
        self.on_done = on_done

        self.win = tk.Toplevel(root)
        self.win.title("Preparando IA...")
        self.win.configure(bg=COLOR_BG)
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", lambda: None)  

        frame = tk.Frame(self.win, bg=COLOR_CARD_BG, padx=30, pady=26,
                          highlightbackground=COLOR_CARD_EDGE, highlightthickness=1)
        frame.pack()

        tk.Label(frame, text="🧠 ENTRENANDO IA POR PRIMERA VEZ",
                 font=("Consolas", 12, "bold"), bg=COLOR_CARD_BG, fg=COLOR_ACCENT).pack(pady=(0, 6))
        tk.Label(frame, text="Está jugando miles de partidas contra sí misma\npara aprender a jugar (esto solo pasa una vez).",
                 font=("Consolas", 9), bg=COLOR_CARD_BG, fg=COLOR_MUTED, justify="center").pack(pady=(0, 16))

        style = ttk.Style()
        style.theme_use("default")
        style.configure("cyber.Horizontal.TProgressbar", troughcolor=COLOR_GRID,
                         background=COLOR_X, thickness=10, bordercolor=COLOR_GRID)

        self.progress = ttk.Progressbar(frame, style="cyber.Horizontal.TProgressbar",
                                         mode="determinate", length=260, maximum=100)
        self.progress.pack()

        self.win.update_idletasks()
        w, h = self.win.winfo_reqwidth(), self.win.winfo_reqheight()
        ws, hs = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
        self.win.geometry(f"{w}x{h}+{(ws - w) // 2}+{(hs - h) // 2}")

        self._progress_value = 0
        threading.Thread(target=self._run_training, daemon=True).start()
        self._poll()

    def _run_training(self):
        train_brain(progress_cb=lambda p: setattr(self, "_progress_value", p * 100))
        save_brain()
        self._progress_value = 100
        self._finished = True

    def _poll(self):
        self.progress["value"] = self._progress_value
        if getattr(self, "_finished", False):
            self.win.destroy()
            self.on_done()
        else:
            self.root.after(80, self._poll)



class TicTacToeTech:
    def __init__(self, root):
        self.root = root
        self.root.title("Tic Tac Toe // Cyber Edition ⚡ (IA con Machine Learning)")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        self.f_title  = tkfont.Font(family="Consolas", size=14, weight="bold")
        self.f_label  = tkfont.Font(family="Consolas", size=10, weight="bold")
        self.f_status = tkfont.Font(family="Consolas", size=15, weight="bold")
        self.f_symbol = tkfont.Font(family="Consolas", size=44, weight="bold")
        self.f_score  = tkfont.Font(family="Consolas", size=11, weight="bold")
        self.f_tiny   = tkfont.Font(family="Consolas", size=8)

        self.playerX = "X"
        self.playerO = "O"
        self.curr_player = self.playerX
        self.turns = 0
        self.game_over = False
        self.vs_ai = False
        self.ai_level = 1
        self.score = {"X": 0, "O": 0, "Empates": 0}

        self.board = [[None] * 3 for _ in range(3)]

        self._build_ui()
        self._center_window()

    def play_sound(self, tipo):
        if platform.system() != "Windows":
            return

        def _beep():
            try:
                import winsound
                if tipo == "click":
                    winsound.Beep(1200, 40)
                elif tipo == "ai":
                    winsound.Beep(800, 60)
                elif tipo == "win":
                    for freq in (1000, 1500, 2000):
                        winsound.Beep(freq, 80)
                elif tipo == "tie":
                    for freq in (600, 400):
                        winsound.Beep(freq, 100)
            except Exception:
                pass

        threading.Thread(target=_beep, daemon=True).start()

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=COLOR_BG)
        outer.pack(padx=18, pady=18)

        self.header = tk.Frame(outer, bg=COLOR_CARD_BG, highlightbackground=COLOR_CARD_EDGE,
                                highlightthickness=1)
        self.header.pack(fill="x", pady=(0, 12))

        tk.Label(self.header, text="⚡ TIC · TAC · TOE", font=self.f_title,
                 bg=COLOR_CARD_BG, fg=COLOR_ACCENT).pack(pady=(14, 2))
        tk.Label(self.header, text="IA entrenada por refuerzo (self-play)", font=self.f_tiny,
                 bg=COLOR_CARD_BG, fg=COLOR_MUTED).pack(pady=(0, 10))

        mode_row = tk.Frame(self.header, bg=COLOR_CARD_BG)
        mode_row.pack(pady=(0, 8))
        self.btn_pvp = self._pill_button(mode_row, "👥  2 JUGADORES", self.set_mode_pvp)
        self.btn_pvp.pack(side="left", padx=5)
        self.btn_ai = self._pill_button(mode_row, "🤖  VS IA", self.set_mode_ai)
        self.btn_ai.pack(side="left", padx=5)

        self.lbl_level = tk.Label(self.header, text="MODO MULTIJUGADOR LOCAL", font=self.f_label,
                                   bg=COLOR_CARD_BG, fg=COLOR_MUTED)
        self.lbl_level.pack(pady=(2, 6))

        self.lbl_status = tk.Label(self.header, text="Turno: X", font=self.f_status,
                                    bg=COLOR_CARD_BG, fg=COLOR_X)
        self.lbl_status.pack(pady=(0, 6))

        score_row = tk.Frame(self.header, bg=COLOR_CARD_BG)
        score_row.pack(pady=(0, 14))
        self.lbl_score = tk.Label(score_row, text=self._score_text(), font=self.f_score,
                                   bg=COLOR_CARD_BG, fg=COLOR_MUTED)
        self.lbl_score.pack()

        size = CELL * 3 + PAD * 4
        self.canvas = tk.Canvas(outer, width=size, height=size, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        self.canvas.bind("<Leave>", lambda e: self._set_hover(None))

        self._hover_cell = None
        self._draw_board()

        self.btn_reset = tk.Button(
            outer, text="🔄  REINICIAR PARTIDA", font=self.f_label,
            bg=COLOR_CARD_BG, fg=COLOR_TEXT, activebackground=COLOR_ACCENT,
            activeforeground="white", bd=0, cursor="hand2", command=self.reset_game,
            highlightbackground=COLOR_CARD_EDGE, highlightthickness=1,
        )
        self.btn_reset.pack(fill="x", pady=(14, 6), ipady=8)

        self.btn_retrain = tk.Button(
            outer, text="🧠  REENTRENAR IA DESDE CERO", font=self.f_tiny,
            bg=COLOR_BG, fg=COLOR_MUTED, activebackground=COLOR_BG, activeforeground=COLOR_X,
            bd=0, cursor="hand2", command=self._retrain,
        )
        self.btn_retrain.pack(pady=(0, 0))

    def _retrain(self):
        V.clear()
        self.ai_level = 1
        self.root.withdraw()
        TrainingSplash(self.root, on_done=lambda: (self.root.deiconify(), self._update_level_label()))

    def _pill_button(self, parent, text, command):
        return tk.Button(
            parent, text=text, font=self.f_label, bg=COLOR_GRID, fg=COLOR_TEXT,
            activebackground=COLOR_X, activeforeground=COLOR_BG, bd=0, padx=14, pady=8,
            cursor="hand2", command=command,
        )

    def _score_text(self):
        return f"X  {self.score['X']}    ·    O  {self.score['O']}    ·    Empates  {self.score['Empates']}"

 
    def _cell_bbox(self, r, c):
        x0 = PAD + c * (CELL + PAD)
        y0 = PAD + r * (CELL + PAD)
        return x0, y0, x0 + CELL, y0 + CELL

    def _draw_board(self):
        self.canvas.delete("all")
        for r in range(3):
            for c in range(3):
                self._draw_cell(r, c)

    def _draw_cell(self, r, c, win=False, hover=False):
        x0, y0, x1, y1 = self._cell_bbox(r, c)
        val = self.board[r][c]

        if win:
            fill = COLOR_WIN
        elif hover and val is None and not self.game_over:
            fill = COLOR_HOVER
        else:
            fill = COLOR_GRID

        self._round_rect(x0, y0, x1, y1, radius=16, fill=fill, outline=COLOR_CARD_EDGE, width=1)

        if val == "X":
            self._draw_glow_text(x0, y0, x1, y1, "X", COLOR_X, COLOR_X_GLOW if not win else COLOR_BG)
        elif val == "O":
            self._draw_glow_text(x0, y0, x1, y1, "O", COLOR_O, COLOR_O_GLOW if not win else COLOR_BG)

    def _draw_glow_text(self, x0, y0, x1, y1, text, color, glow_color):
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for dx, dy in ((0, 3), (0, -3), (3, 0), (-3, 0)):
            self.canvas.create_text(cx + dx, cy + dy, text=text, font=self.f_symbol, fill=glow_color)
        self.canvas.create_text(cx, cy, text=text, font=self.f_symbol, fill=color)

    def _round_rect(self, x0, y0, x1, y1, radius=14, **kwargs):
        points = [
            x0 + radius, y0, x1 - radius, y0, x1, y0, x1, y0 + radius,
            x1, y1 - radius, x1, y1, x1 - radius, y1, x0 + radius, y1,
            x0, y1, x0, y1 - radius, x0, y0 + radius, x0, y0,
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)


    def _cell_at(self, x, y):
        for r in range(3):
            for c in range(3):
                x0, y0, x1, y1 = self._cell_bbox(r, c)
                if x0 <= x <= x1 and y0 <= y <= y1:
                    return r, c
        return None

    def _on_canvas_motion(self, event):
        self._set_hover(self._cell_at(event.x, event.y))

    def _set_hover(self, cell):
        if cell == self._hover_cell:
            return
        prev, self._hover_cell = self._hover_cell, cell
        if prev:
            self._draw_cell(*prev)
        if cell:
            self._draw_cell(*cell, hover=True)

    def _on_canvas_click(self, event):
        cell = self._cell_at(event.x, event.y)
        if cell:
            self.set_tile(*cell)

  
    def set_mode_pvp(self):
        self.vs_ai = False
        self.btn_pvp.config(bg=COLOR_ACCENT, fg="white")
        self.btn_ai.config(bg=COLOR_GRID, fg=COLOR_TEXT)
        self.lbl_level.config(text="MODO MULTIJUGADOR LOCAL", fg=COLOR_MUTED)
        self.reset_game()

    def set_mode_ai(self):
        self.vs_ai = True
        self.btn_ai.config(bg=COLOR_ACCENT, fg="white")
        self.btn_pvp.config(bg=COLOR_GRID, fg=COLOR_TEXT)
        self._update_level_label()
        self.reset_game()

    def _update_level_label(self):
        if self.vs_ai:
            nombre, icono = NOMBRES_NIVELES[self.ai_level]
            self.lbl_level.config(text=f"{icono}  NIVEL {self.ai_level} · {nombre.upper()}", fg=COLOR_X)

 
    def set_tile(self, row, col):
        if self.game_over or self.board[row][col] is not None:
            return

        self.play_sound("click" if self.curr_player == self.playerX else "ai")

        self.board[row][col] = self.curr_player
        self._draw_cell(row, col)
        self.turns += 1

        if self.check_winner():
            return

        self.curr_player = self.playerO if self.curr_player == self.playerX else self.playerX
        self.lbl_status.config(
            text=f"Turno: {self.curr_player}",
            fg=COLOR_X if self.curr_player == self.playerX else COLOR_O,
        )

        if self.vs_ai and self.curr_player == self.playerO and not self.game_over:
            self.root.after(300, self.make_ai_move)

    def _flatten(self):
        return [self.board[r][c] if self.board[r][c] else " " for r in range(3) for c in range(3)]

    def make_ai_move(self):
        flat = self._flatten()
        if " " not in flat:
            return
        idx = ai_choose_move(flat, self.ai_level)
        self.set_tile(idx // 3, idx % 3)


    def evaluate_winner(self):
        b = self.board
        lines = [b[i] for i in range(3)] + [[b[r][i] for r in range(3)] for i in range(3)]
        lines += [[b[0][0], b[1][1], b[2][2]], [b[0][2], b[1][1], b[2][0]]]
        for line in lines:
            if line[0] is not None and line[0] == line[1] == line[2]:
                return line[0]
        return None

    def _winning_coords(self):
        b = self.board
        rows = [[(i, 0), (i, 1), (i, 2)] for i in range(3)]
        cols = [[(0, i), (1, i), (2, i)] for i in range(3)]
        diags = [[(0, 0), (1, 1), (2, 2)], [(0, 2), (1, 1), (2, 0)]]
        for coords in rows + cols + diags:
            vals = [b[r][c] for r, c in coords]
            if vals[0] is not None and vals[0] == vals[1] == vals[2]:
                return coords
        return []

    def check_winner(self):
        winner = self.evaluate_winner()

        if winner:
            for r, c in self._winning_coords():
                self._draw_cell(r, c, win=True)

            self.game_over = True
            self.play_sound("win")
            self.score[winner] += 1
            self.lbl_score.config(text=self._score_text())

            if self.vs_ai and winner == self.playerX:
                if self.ai_level < 5:
                    self.ai_level += 1
                    nombre, icono = NOMBRES_NIVELES[self.ai_level]
                    msg = f"¡GANASTE! Subes a {icono} {nombre}"
                else:
                    msg = "¡INCREÍBLE! Venciste a la IA casi perfecta 🎉"
                self.lbl_status.config(text=msg, fg=COLOR_WIN)
                self._update_level_label()
            else:
                quien = "Jugaste tú" if winner == self.playerX else ("La IA" if self.vs_ai else "Jugador O")
                self.lbl_status.config(text=f"¡Ganó {winner}! ({quien})", fg=COLOR_WIN)

            return True

        if self.turns == 9:
            self.game_over = True
            self.play_sound("tie")
            self.score["Empates"] += 1
            self.lbl_score.config(text=self._score_text())
            self.lbl_status.config(text="¡Empate Técnico!", fg=COLOR_TEXT)
            return True

        return False


    def reset_game(self):
        self.turns = 0
        self.game_over = False
        self.curr_player = self.playerX
        self.board = [[None] * 3 for _ in range(3)]
        self._hover_cell = None
        self.lbl_status.config(text=f"Turno: {self.curr_player}", fg=COLOR_X)
        self._draw_board()

    def _center_window(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        ws, hs = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(ws - w) // 2}+{(hs - h) // 2}")



def launch_game(root):
    root.deiconify()
    TicTacToeTech(root)


if __name__ == "__main__":
    root = tk.Tk()

    if load_brain():
    
        launch_game(root)
    else:
        root.withdraw()
        TrainingSplash(root, on_done=lambda: launch_game(root))

    root.mainloop()
