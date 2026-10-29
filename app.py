import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import db

# =====================================================================
#  THEME
# =====================================================================
BG = "#171B20"          # deep charcoal page background
NAV = "#222A30"         # top bar / sidebar
CARD = "#283238"        # cards
INPUT = "#3B484F"       # inputs / ghost buttons
TEXT = "#F7F7F2"
MUTED = "#B7C1C5"
ACCENT = "#FFF6A1"
ACCENT_HOVER = "#F3E77E"
FONT = "Segoe UI"

POSTER_COLORS = ["#758A93", "#91A0A4", "#A6A18B", "#687C86",
                 "#B3A88A", "#82979C", "#667B84", "#A1B0B2"]


def apply_style(root):
    root.configure(bg=BG)
    root.option_add("*Font", (FONT, 10))
    root.option_add("*Frame.Background", BG)
    root.option_add("*Label.Background", BG)
    root.option_add("*TCombobox*Listbox.background", INPUT)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", "white")

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Treeview", background=CARD, fieldbackground=CARD,
                    foreground=TEXT, rowheight=34, borderwidth=0, font=(FONT, 10))
    style.configure("Treeview.Heading", background=INPUT, foreground=TEXT,
                    font=(FONT, 10, "bold"), relief="flat", padding=8)
    style.map("Treeview", background=[("selected", ACCENT)],
              foreground=[("selected", "#283238")])
    style.map("Treeview.Heading", background=[("active", "#3a4060")])
    style.configure("TCombobox", fieldbackground=INPUT, background=INPUT,
                    foreground=TEXT, arrowcolor=TEXT, bordercolor=INPUT,
                    lightcolor=INPUT, darkcolor=INPUT, padding=6)
    style.map("TCombobox", fieldbackground=[("readonly", INPUT)],
              foreground=[("readonly", TEXT)],
              selectbackground=[("readonly", INPUT)],
              selectforeground=[("readonly", TEXT)])
    style.configure("Vertical.TScrollbar", background=INPUT, troughcolor=BG,
                    bordercolor=BG, arrowcolor=TEXT, lightcolor=INPUT, darkcolor=INPUT)


# =====================================================================
#  SMALL REUSABLE WIDGETS
# =====================================================================
class Btn(tk.Label):
    """Flat modern button (a Label, so colors work on Windows, Mac and Linux)."""
    KINDS = {
        "primary": (ACCENT, ACCENT_HOVER, "#283238"),
        "ghost": (INPUT, "#3a4060", TEXT),
        "danger": ("#9D4B50", "#B85C61", "white"),
    }

    def __init__(self, parent, text, command, kind="primary", **kw):
        bg, hover, fg = self.KINDS[kind]
        kw.setdefault("padx", 18)
        kw.setdefault("pady", 9)
        super().__init__(parent, text=text, bg=bg, fg=fg,
                         font=(FONT, 10, "bold"), cursor="hand2", **kw)
        self.command = command
        self.normal = bg
        self.hover = hover
        self.bind("<Enter>", lambda e: self.config(bg=self.hover))
        self.bind("<Leave>", lambda e: self.config(bg=self.normal))
        self.bind("<Button-1>", lambda e: self.command())


class ScrollFrame(tk.Frame):
    """Reusable vertical scroll area with reliable mouse-wheel support.

    Mouse-wheel events are handled only by the scroll area underneath the
    pointer, so multiple pages/scroll areas do not fight over scrolling.
    Add content to ``.inner``.
    """

    def __init__(self, parent, bg=BG):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(
            self, bg=bg, highlightthickness=0, borderwidth=0,
            yscrollincrement=24
        )
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.window = self.canvas.create_window(
            (0, 0), window=self.inner, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_inner)

        # Bind globally because the pointer is often over a label/card inside
        # the canvas. _on_mousewheel checks widget ancestry so only the correct
        # ScrollFrame reacts.
        self.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.bind_all("<Button-4>", self._on_mousewheel, add="+")
        self.bind_all("<Button-5>", self._on_mousewheel, add="+")

    def _update_scroll_region(self, _event=None):
        try:
            if self.canvas.winfo_exists():
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except tk.TclError:
            pass

    def _resize_inner(self, event):
        try:
            if self.canvas.winfo_exists():
                self.canvas.itemconfigure(self.window, width=event.width)
                self._update_scroll_region()
        except tk.TclError:
            pass

    def _belongs_to_this_scrollframe(self, widget):
        """True when the event came from this canvas or one of its children."""
        try:
            while widget is not None:
                if widget == self.inner or widget == self.canvas:
                    return True
                widget = getattr(widget, "master", None)
        except tk.TclError:
            return False
        return False

    def _on_mousewheel(self, event):
        try:
            if not self.canvas.winfo_exists():
                return
            if not self._belongs_to_this_scrollframe(event.widget):
                return
            bbox = self.canvas.bbox("all")
            if not bbox or (bbox[3] - bbox[1]) <= self.canvas.winfo_height():
                return

            if getattr(event, "num", None) == 4:
                units = -3
            elif getattr(event, "num", None) == 5:
                units = 3
            else:
                delta = getattr(event, "delta", 0)
                # Windows usually reports multiples of 120; small non-zero
                # deltas still get a useful scroll step on touchpads.
                units = -1 * (max(1, abs(delta) // 120)) if delta > 0 else max(1, abs(delta) // 120)
            self.canvas.yview_scroll(units, "units")
        except tk.TclError:
            pass


def lbl(parent, text, size=10, bold=False, fg=TEXT, bg=BG, **kw):
    return tk.Label(parent, text=text, bg=bg, fg=fg,
                    font=(FONT, size, "bold" if bold else "normal"), **kw)


def pill(parent, text, bg=INPUT, fg=TEXT):
    return tk.Label(parent, text=text, bg=bg, fg=fg,
                    font=(FONT, 9, "bold"), padx=12, pady=4)


def make_entry(parent, show=None, width=28):
    return tk.Entry(parent, show=show, width=width, bg=INPUT, fg=TEXT,
                    insertbackground=TEXT, relief="flat", font=(FONT, 11),
                    highlightthickness=1, highlightbackground=INPUT,
                    highlightcolor=ACCENT)


def field(parent, text, show=None, bg=CARD):
    """Label + entry stacked vertically. Returns the entry."""
    lbl(parent, text, 9, fg=MUTED, bg=bg, anchor="w").pack(fill="x")
    entry = make_entry(parent, show)
    entry.pack(fill="x", ipady=8, pady=(4, 14))
    return entry


def page_title(parent, title, subtitle=""):
    lbl(parent, title, 24, True).pack(anchor="w")
    if subtitle:
        lbl(parent, subtitle, 10, fg=MUTED).pack(anchor="w", pady=(0, 12))


def make_table(parent, columns):
    """columns = list of (key, title, width). Returns (frame, tree)."""
    frame = tk.Frame(parent, bg=CARD)
    tree = ttk.Treeview(frame, columns=[c[0] for c in columns],
                        show="headings", selectmode="browse")
    for key, title, width in columns:
        tree.heading(key, text=title)
        tree.column(key, width=width, anchor="center")
    bar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=bar.set)
    tree.pack(side="left", fill="both", expand=True)
    bar.pack(side="right", fill="y")
    return frame, tree


def fill_tree(tree, rows, keys, iid_key):
    tree.delete(*tree.get_children())
    for r in rows:
        values = ["" if r[k] is None else r[k] for k in keys]
        tree.insert("", "end", iid=str(r[iid_key]), values=values)


def get_field(row, key, default=None):
    try:
        value = row[key]
        return default if value is None else value
    except (KeyError, IndexError, TypeError):
        return default


def fmt_time(value):
    parts = str(value).split(":")
    try:
        return f"{int(parts[0]):02d}:{parts[1]}"
    except (ValueError, IndexError):
        return str(value)


def make_poster(parent, movie, width, height, letter_size):
    """Colored 'poster' with the first letter of the movie title."""
    color = POSTER_COLORS[int(movie["movie_id"]) % len(POSTER_COLORS)]
    box = tk.Frame(parent, bg=color, width=width, height=height)
    letter = (str(movie["title"]).strip() or "?")[0].upper()
    tk.Label(box, text=letter, bg=color, fg="white",
             font=(FONT, letter_size, "bold")).place(relx=0.5, rely=0.5, anchor="center")
    return box


def make_clickable(widget, command):
    widget.config(cursor="hand2")
    widget.bind("<Button-1>", lambda e: command())
    for child in widget.winfo_children():
        make_clickable(child, command)



# =====================================================================
#  MODERN CUSTOM MODALS (instead of native message boxes)
# =====================================================================
def show_modal(parent, title, message, icon="✓", accent=ACCENT,
               confirm_text="Got it", cancel_text=None, on_confirm=None,
               details=None):
    """A themed modal dialog with custom actions and optional booking details."""
    win = tk.Toplevel(parent)
    win.title(title)
    win.configure(bg=BG)
    win.transient(parent)
    win.resizable(False, False)
    win.grab_set()

    width, height = (470, 390 if details else 290)
    win.geometry(f"{width}x{height}")
    win.update_idletasks()
    x = parent.winfo_rootx() + max(0, (parent.winfo_width() - width) // 2)
    y = parent.winfo_rooty() + max(0, (parent.winfo_height() - height) // 2)
    win.geometry(f"+{x}+{y}")

    shell = tk.Frame(win, bg=CARD, padx=28, pady=24,
                     highlightthickness=1, highlightbackground="#758A93")
    shell.pack(fill="both", expand=True, padx=8, pady=8)

    icon_canvas = tk.Canvas(shell, width=58, height=58, bg=CARD,
                            highlightthickness=0)
    icon_canvas.pack(pady=(0, 12))
    icon_canvas.create_oval(3, 3, 55, 55, fill=accent, outline="")
    icon_canvas.create_text(29, 29, text=icon, fill="#283238",
                            font=(FONT, 22, "bold"))

    lbl(shell, title, 18, True, bg=CARD, fg=TEXT).pack()
    lbl(shell, message, 10, fg=MUTED, bg=CARD, justify="center",
        wraplength=390).pack(pady=(8, 10))

    if details:
        detail_box = tk.Frame(shell, bg="#20292E", padx=14, pady=10)
        detail_box.pack(fill="x", pady=(0, 12))
        for key, value in details:
            line = tk.Frame(detail_box, bg="#20292E")
            line.pack(fill="x", pady=2)
            lbl(line, key, 9, fg=MUTED, bg="#20292E").pack(side="left")
            lbl(line, str(value), 9, True, fg=TEXT, bg="#20292E").pack(side="right")

    actions = tk.Frame(shell, bg=CARD)
    actions.pack(fill="x", pady=(4, 0))

    def close():
        try:
            win.grab_release()
        except tk.TclError:
            pass
        win.destroy()

    if cancel_text:
        Btn(actions, cancel_text, close, kind="ghost").pack(
            side="left", expand=True, fill="x", padx=(0, 8))

    def confirm():
        close()
        if on_confirm:
            on_confirm()

    Btn(actions, confirm_text, confirm,
        kind="danger" if accent in ("#B85C61", "#9D4B50") else "primary").pack(
            side="left" if cancel_text else "right",
            expand=True, fill="x", padx=(8, 0) if cancel_text else 0)
    win.bind("<Escape>", lambda e: close())
    win.bind("<Return>", lambda e: confirm())
    win.wait_window()


# =====================================================================
#  MAIN APP
# =====================================================================
class CinemaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        apply_style(self)
        self.title("Cinema Ticket Booking System")
        self.geometry("1150x740")
        self.minsize(1000, 650)
        self.current_user = None
        self.page = None
        self.navigate(LoginPage)

    def report_callback_exception(self, exc, val, tb):
        messagebox.showerror("Error", f"Something went wrong:\n{val}")

    def navigate(self, page_class, *args):
        """Destroy the current page and show a new one."""
        if self.page is not None:
            self.page.destroy()
        self.page = page_class(self, *args)
        self.page.pack(fill="both", expand=True)

    def go_home(self):
        if self.current_user["role"] == "admin":
            self.navigate(AdminPage)
        else:
            self.navigate(HomePage)

    def logout(self):
        self.current_user = None
        self.navigate(LoginPage)


# =====================================================================
#  LOGIN & REGISTER PAGES
# =====================================================================
def build_auth_shell(page):
    """Left brand panel + right form card. Returns the card."""
    left = tk.Frame(page, bg="#758A93", width=460)
    left.pack(side="left", fill="y")
    left.pack_propagate(False)
    box = tk.Frame(left, bg="#758A93")
    box.place(relx=0.5, rely=0.5, anchor="center")
    lbl(box, "CINEMA", 40, True, fg="#222A30", bg="#758A93").pack(anchor="w")
    lbl(box, "Book your seats in seconds", 14, fg="#222A30", bg="#758A93").pack(
        anchor="w", pady=(4, 30))
    for line in ("Browse the latest movies", "Pick your favorite seats",
                 "Manage all your bookings"):
        lbl(box, "•  " + line, 11, fg="#222A30", bg="#758A93").pack(anchor="w", pady=3)

    right = tk.Frame(page, bg=BG)
    right.pack(side="right", fill="both", expand=True)
    card = tk.Frame(right, bg=CARD, padx=44, pady=38)
    card.place(relx=0.5, rely=0.5, anchor="center")
    return card


class LoginPage(tk.Frame):
    def __init__(self, app):
        super().__init__(app, bg=BG)
        self.app = app
        card = build_auth_shell(self)

        lbl(card, "Welcome back", 22, True, bg=CARD).pack(anchor="w")
        lbl(card, "Login to your account", 10, fg=MUTED, bg=CARD).pack(
            anchor="w", pady=(2, 22))
        self.email = field(card, "Email")
        self.password = field(card, "Password", show="*")
        Btn(card, "Login", self.do_login).pack(fill="x", pady=(6, 14))

        link = lbl(card, "Don't have an account? Create one", 10, fg=ACCENT, bg=CARD,
                   cursor="hand2")
        link.pack()
        link.bind("<Button-1>", lambda e: app.navigate(RegisterPage))

        self.password.bind("<Return>", lambda e: self.do_login())
        self.email.focus_set()

    def do_login(self):
        email = self.email.get().strip()
        password = self.password.get()
        if not email or not password:
            messagebox.showwarning("Missing data", "Please enter email and password.")
            return
        user = db.login_user(email, password)
        if user is None:
            messagebox.showerror("Login failed", "Wrong email or password.")
            return
        self.app.current_user = user
        self.app.go_home()


class RegisterPage(tk.Frame):
    def __init__(self, app):
        super().__init__(app, bg=BG)
        self.app = app
        card = build_auth_shell(self)

        lbl(card, "Create account", 22, True, bg=CARD).pack(anchor="w")
        lbl(card, "It only takes a few seconds", 10, fg=MUTED, bg=CARD).pack(
            anchor="w", pady=(2, 22))
        self.name = field(card, "Full Name")
        self.email = field(card, "Email")
        self.password = field(card, "Password", show="*")
        Btn(card, "Register", self.do_register).pack(fill="x", pady=(6, 14))

        link = lbl(card, "Already have an account? Login", 10, fg=ACCENT, bg=CARD,
                   cursor="hand2")
        link.pack()
        link.bind("<Button-1>", lambda e: app.navigate(LoginPage))
        self.name.focus_set()

    def do_register(self):
        ok, msg = db.register_user(self.name.get().strip(),
                                   self.email.get().strip(),
                                   self.password.get())
        if ok:
            messagebox.showinfo("Success", msg)
            self.app.navigate(LoginPage)
        else:
            messagebox.showerror("Error", msg)


# =====================================================================
#  CUSTOMER PAGES
# =====================================================================
class CustomerPage(tk.Frame):
    """Base page: top navigation bar + a .body area."""

    def __init__(self, app, active="movies"):
        super().__init__(app, bg=BG)
        self.app = app

        bar = tk.Frame(self, bg=NAV)
        bar.pack(fill="x")
        brand = tk.Frame(bar, bg=NAV)
        brand.pack(side="left", padx=(30, 40), pady=14)
        lbl(brand, "CINE", 16, True, fg=ACCENT, bg=NAV).pack(side="left")
        lbl(brand, "MA", 16, True, bg=NAV).pack(side="left")

        links = (("movies", "Movies", HomePage), ("bookings", "My Bookings", MyBookingsPage))
        for key, text, target in links:
            link = lbl(bar, text, 11, True, bg=NAV, cursor="hand2",
                       fg=ACCENT if key == active else MUTED)
            link.pack(side="left", padx=14)
            link.bind("<Button-1>", lambda e, t=target: app.navigate(t))

        Btn(bar, "Logout", app.logout, kind="ghost").pack(side="right", padx=30)
        lbl(bar, f"Hi, {app.current_user['full_name']}", 10, fg=MUTED, bg=NAV).pack(
            side="right")

        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True, padx=40, pady=24)


class MovieCard(tk.Frame):
    WIDTH = 230

    def __init__(self, parent, movie, on_open):
        # Canvas paints a rounded outer silhouette; content is inset so its
        # square Tk widgets do not cover the rounded corners.
        super().__init__(parent, bg=BG, padx=0, pady=0)
        self.canvas = tk.Canvas(self, width=self.WIDTH + 12, height=306,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()
        self._rounded_rect(self.canvas, 2, 2, self.WIDTH + 10, 302, 18, CARD)
        content = tk.Frame(self.canvas, bg=CARD)
        self.canvas.create_window(6, 6, anchor="nw", window=content,
                                  width=self.WIDTH, height=292)
        poster = make_poster(content, movie, self.WIDTH - 12, 160, 60)
        poster.pack(padx=6, pady=(6, 0))
        make_clickable(poster, lambda: on_open(movie))

        info = tk.Frame(content, bg=CARD)
        info.pack(fill="both", expand=True, padx=14, pady=10)
        title = lbl(info, movie["title"], 12, True, bg=CARD, anchor="w", justify="left",
                    wraplength=self.WIDTH - 28, height=2)
        title.pack(fill="x")
        make_clickable(title, lambda: on_open(movie))
        genre = get_field(movie, "genre", "Movie")
        lbl(info, f'{genre}  •  {movie["duration_min"]} min', 9, fg=MUTED, bg=CARD,
            anchor="w").pack(fill="x", pady=(4, 10))
        Btn(info, "Book Now", lambda: on_open(movie)).pack(fill="x")

    @staticmethod
    def _rounded_rect(canvas, x1, y1, x2, y2, radius, fill):
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1,
            x2, y1 + radius, x2, y2 - radius, x2, y2,
            x2 - radius, y2, x1 + radius, y2, x1, y2,
            x1, y2 - radius, x1, y1 + radius, x1, y1
        ]
        canvas.create_polygon(points, smooth=True, splinesteps=24,
                              fill=fill, outline=fill)


class HomePage(CustomerPage):
    COLS = 4

    def __init__(self, app):
        super().__init__(app, "movies")
        self.movies = db.get_movies()

        head = tk.Frame(self.body, bg=BG)
        head.pack(fill="x", pady=(0, 16))
        titles = tk.Frame(head, bg=BG)
        titles.pack(side="left")
        lbl(titles, "Now Showing", 24, True).pack(anchor="w")
        lbl(titles, "Pick a movie and book your seats", 10, fg=MUTED).pack(anchor="w")

        self.search = tk.StringVar()
        entry = make_entry(head, width=28)
        entry.config(textvariable=self.search)
        entry.pack(side="right", ipady=8)
        lbl(head, "Search:", 10, fg=MUTED).pack(side="right", padx=8)
        self.search.trace_add("write", lambda *a: self.render())

        self.scroll = ScrollFrame(self.body)
        self.scroll.pack(fill="both", expand=True)
        self.render()

    def render(self):
        inner = self.scroll.inner
        for widget in inner.winfo_children():
            widget.destroy()
        text = self.search.get().strip().lower()
        movies = [m for m in self.movies
                  if text in str(m["title"]).lower()
                  or text in str(get_field(m, "genre", "")).lower()]
        if not movies:
            lbl(inner, "No movies found.", 12, fg=MUTED).grid(row=0, column=0, pady=40)
            return
        for col in range(self.COLS):
            inner.grid_columnconfigure(col, weight=1)
        for i, movie in enumerate(movies):
            MovieCard(inner, movie, self.open_movie).grid(
                row=i // self.COLS, column=i % self.COLS, padx=10, pady=10, sticky="n")
        # Refresh the scroll region after rebuilding the movie grid.
        self.scroll.after_idle(self.scroll._update_scroll_region)

    def open_movie(self, movie):
        self.app.navigate(MovieDetailsPage, movie)


class MovieDetailsPage(CustomerPage):
    def __init__(self, app, movie):
        super().__init__(app, "movies")
        Btn(self.body, "←  Back to movies", lambda: app.navigate(HomePage),
            kind="ghost").pack(anchor="w", pady=(0, 16))

        row = tk.Frame(self.body, bg=BG)
        row.pack(fill="both", expand=True)
        make_poster(row, movie, 280, 400, 110).pack(side="left", anchor="n")

        info = tk.Frame(row, bg=BG)
        info.pack(side="left", fill="both", expand=True, padx=(36, 0))
        lbl(info, movie["title"], 28, True, anchor="w", justify="left",
            wraplength=620).pack(anchor="w")

        pills = tk.Frame(info, bg=BG)
        pills.pack(anchor="w", pady=12)
        pill(pills, get_field(movie, "genre", "Movie"), ACCENT).pack(side="left", padx=(0, 8))
        pill(pills, f'{movie["duration_min"]} min').pack(side="left")

        desc = get_field(movie, "description",
                         "Choose a showtime below, pick your favorite seats and enjoy the show.")
        lbl(info, desc, 11, fg=MUTED, anchor="w", justify="left",
            wraplength=620).pack(anchor="w", pady=(0, 20))

        lbl(info, "Showtimes", 16, True, anchor="w").pack(anchor="w", pady=(0, 8))
        scroll = ScrollFrame(info)
        scroll.pack(fill="both", expand=True)
        showtimes = db.get_showtimes(movie["movie_id"])
        if not showtimes:
            lbl(scroll.inner, "No showtimes available yet.", 11, fg=MUTED).pack(anchor="w")
        for st in showtimes:
            self.add_showtime_row(scroll.inner, movie, st)

    def add_showtime_row(self, parent, movie, st):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", pady=5, padx=(0, 8))
        left = tk.Frame(row, bg=CARD)
        left.pack(side="left", padx=18, pady=12)
        lbl(left, fmt_time(st["show_time"]), 18, True, bg=CARD).pack(anchor="w")
        lbl(left, str(st["show_date"]), 10, fg=MUTED, bg=CARD).pack(anchor="w")

        mid = tk.Frame(row, bg=CARD)
        mid.pack(side="left", padx=40)
        lbl(mid, str(st["hall_name"]), 12, True, bg=CARD).pack(anchor="w")
        lbl(mid, f'{float(st["price"]):.2f} EGP per seat', 10, fg=MUTED, bg=CARD).pack(
            anchor="w")

        Btn(row, "Book", lambda: self.app.navigate(BookingPage, movie, st)).pack(
            side="right", padx=18)


class BookingPage(CustomerPage):
    FREE = "#758A93"
    HOVER = "#91A4AB"
    SELECTED = "#FFF6A1"
    BOOKED = "#171B20"

    def __init__(self, app, movie, showtime):
        super().__init__(app, "movies")
        self.movie = movie
        self.showtime = showtime
        self.price = float(showtime["price"])
        self.selected = set()
        self.names = {}
        self.labels = {}

        top = tk.Frame(self.body, bg=BG)
        top.pack(fill="x", pady=(0, 14))
        Btn(top, "←  Back", lambda: app.navigate(MovieDetailsPage, movie),
            kind="ghost").pack(side="left")
        lbl(top, "Select your seats", 22, True).pack(side="left", padx=20)

        main = tk.Frame(self.body, bg=BG)
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, minsize=320)
        main.grid_rowconfigure(0, weight=1)
        self.build_seat_card(main)
        self.build_summary_card(main)

    # ----- left side: seat map -----
    def build_seat_card(self, parent):
        card = tk.Frame(parent, bg=CARD, padx=20, pady=20)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

        tk.Frame(card, bg=ACCENT, height=6).pack(fill="x", padx=60)
        lbl(card, "SCREEN", 9, True, fg=MUTED, bg=CARD).pack(pady=(6, 20))

        # The seat map gets its own scroll area so halls with many rows fit
        # even on smaller laptop screens. Keep the legend visible underneath.
        seat_scroll = ScrollFrame(card, bg=CARD)
        seat_scroll.pack(fill="both", expand=True, pady=(0, 8))
        grid = seat_scroll.inner
        seats = db.get_seat_map(self.showtime["showtime_id"])
        rows = sorted({s["row_label"] for s in seats})
        for index, row in enumerate(rows):
            lbl(grid, row, 11, True, fg=MUTED, bg=CARD).grid(row=index, column=0, padx=(0, 12))

        for s in seats:
            seat_id = s["seat_id"]
            self.names[seat_id] = f'{s["row_label"]}{s["seat_number"]}'
            booked = bool(s["is_booked"])
            seat = tk.Label(grid, text=str(s["seat_number"]), width=4,
                            bg=self.BOOKED if booked else self.FREE,
                            fg="#4a5068" if booked else "white",
                            font=(FONT, 10, "bold"),
                            cursor="arrow" if booked else "hand2")
            seat.grid(row=rows.index(s["row_label"]), column=int(s["seat_number"]),
                      padx=3, pady=3, ipady=6)
            if not booked:
                seat.bind("<Button-1>", lambda e, sid=seat_id: self.toggle(sid))
                seat.bind("<Enter>", lambda e, sid=seat_id: self.hover(sid, True))
                seat.bind("<Leave>", lambda e, sid=seat_id: self.hover(sid, False))
            self.labels[seat_id] = seat

        legend = tk.Frame(card, bg=CARD)
        legend.pack(pady=(24, 0))
        for text, color in (("Available", self.FREE), ("Selected", self.SELECTED),
                            ("Booked", self.BOOKED)):
            tk.Label(legend, bg=color, width=2).pack(side="left", padx=(14, 6))
            lbl(legend, text, 9, fg=MUTED, bg=CARD).pack(side="left")

    # ----- right side: summary -----
    def build_summary_card(self, parent):
        card = tk.Frame(parent, bg=CARD, padx=22, pady=22)
        card.grid(row=0, column=1, sticky="new")

        lbl(card, self.movie["title"], 16, True, bg=CARD, anchor="w", justify="left",
            wraplength=270).pack(fill="x")
        lbl(card, get_field(self.movie, "genre", "Movie"), 10, fg=MUTED, bg=CARD,
            anchor="w").pack(fill="x", pady=(2, 14))
        tk.Frame(card, bg=INPUT, height=1).pack(fill="x", pady=(0, 12))

        self.info_row(card, "Date", str(self.showtime["show_date"]))
        self.info_row(card, "Time", fmt_time(self.showtime["show_time"]))
        self.info_row(card, "Hall", str(self.showtime["hall_name"]))
        self.info_row(card, "Price per seat", f"{self.price:.2f} EGP")
        tk.Frame(card, bg=INPUT, height=1).pack(fill="x", pady=12)
        self.seats_label = self.info_row(card, "Seats", "none")

        total_row = tk.Frame(card, bg=CARD)
        total_row.pack(fill="x", pady=(10, 18))
        lbl(total_row, "Total", 11, fg=MUTED, bg=CARD).pack(side="left")
        self.total_label = lbl(total_row, "0.00 EGP", 18, True, fg=ACCENT, bg=CARD)
        self.total_label.pack(side="right")

        Btn(card, "Confirm Booking", self.confirm).pack(fill="x")

    def info_row(self, parent, key, value):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", pady=3)
        lbl(row, key, 10, fg=MUTED, bg=CARD).pack(side="left", anchor="n")
        value_label = lbl(row, value, 10, True, bg=CARD, justify="right", wraplength=190)
        value_label.pack(side="right")
        return value_label

    # ----- actions -----
    def hover(self, seat_id, inside):
        if seat_id not in self.selected:
            self.labels[seat_id].config(bg=self.HOVER if inside else self.FREE)

    def toggle(self, seat_id):
        if seat_id in self.selected:
            self.selected.remove(seat_id)
            self.labels[seat_id].config(bg=self.FREE, fg="white")
        else:
            self.selected.add(seat_id)
            self.labels[seat_id].config(bg=self.SELECTED, fg="#283238")
        names = sorted(self.names[s] for s in self.selected)
        self.seats_label.config(text=", ".join(names) if names else "none")
        self.total_label.config(text=f"{self.price * len(self.selected):.2f} EGP")

    def confirm(self):
        if not self.selected:
            show_modal(self.app, "Choose your seats", "Please select at least one available seat first.",
                       icon="!", accent="#758A93", confirm_text="Choose seats")
            return

        seat_names = sorted(self.names[s] for s in self.selected)
        total = self.price * len(self.selected)

        def save_booking():
            ok, msg = db.book_seats(self.app.current_user["user_id"],
                                    self.showtime["showtime_id"], list(self.selected))
            if ok:
                show_modal(self.app, "Booking confirmed!",
                           "Your seats are reserved. Enjoy the movie!",
                           icon="✓", accent=ACCENT, confirm_text="View my bookings",
                           on_confirm=lambda: self.app.navigate(MyBookingsPage),
                           details=[("Movie", self.movie["title"]),
                                    ("Seats", ", ".join(seat_names)),
                                    ("Total", f"{total:.2f} EGP")])
            else:
                show_modal(self.app, "Booking not completed", msg,
                           icon="!", accent="#B85C61", confirm_text="Try again",
                           on_confirm=lambda: self.app.navigate(BookingPage, self.movie, self.showtime))
                if "just booked" in msg:
                    # Refresh the seat map when another customer booked a seat.
                    self.app.after(50, lambda: self.app.navigate(BookingPage, self.movie, self.showtime))

        show_modal(self.app, "Confirm your booking?",
                   "Please review your selected seats before confirming.",
                   icon="?", accent=ACCENT, confirm_text="Confirm booking",
                   cancel_text="Go back", on_confirm=save_booking,
                   details=[("Movie", self.movie["title"]),
                            ("Showtime", f'{self.showtime["show_date"]} • {fmt_time(self.showtime["show_time"])}'),
                            ("Seats", ", ".join(seat_names)),
                            ("Total", f"{total:.2f} EGP")])



class MyBookingsPage(CustomerPage):
    def __init__(self, app):
        super().__init__(app, "bookings")
        page_title(self.body, "My Bookings", "Your tickets and reservations")

        bookings = db.get_user_bookings(app.current_user["user_id"])
        if not bookings:
            empty = tk.Frame(self.body, bg=CARD, padx=40, pady=40)
            empty.pack(fill="x")
            lbl(empty, "You have no bookings yet.", 13, True, bg=CARD).pack()
            lbl(empty, "Find a movie you like and book your first seats.", 10,
                fg=MUTED, bg=CARD).pack(pady=(4, 0))
            Btn(empty, "Browse Movies", lambda: app.navigate(HomePage)).pack(pady=(16, 0))
            return

        scroll = ScrollFrame(self.body)
        scroll.pack(fill="both", expand=True)
        for booking in bookings:
            self.add_ticket(scroll.inner, booking)

    def add_ticket(self, parent, b):
        ticket = tk.Frame(parent, bg=CARD)
        ticket.pack(fill="x", pady=6, padx=(0, 8))
        tk.Frame(ticket, bg=ACCENT, width=6).pack(side="left", fill="y")

        info = tk.Frame(ticket, bg=CARD)
        info.pack(side="left", padx=20, pady=16)
        lbl(info, b["title"], 15, True, bg=CARD).pack(anchor="w")
        lbl(info, f'{b["show_date"]}  •  {fmt_time(b["show_time"])}  •  {b["hall_name"]}',
            10, fg=MUTED, bg=CARD).pack(anchor="w", pady=(4, 6))
        lbl(info, f'Seats: {b["seats"]}', 11, bg=CARD).pack(anchor="w")

        right = tk.Frame(ticket, bg=CARD)
        right.pack(side="right", padx=20)
        lbl(right, f'{float(b["total_price"]):.2f} EGP', 14, True, fg=ACCENT,
            bg=CARD).pack(anchor="e", pady=(0, 8))
        Btn(right, "Cancel Booking", lambda bid=b["booking_id"]: self.cancel(bid),
            kind="danger").pack()

    def cancel(self, booking_id):
        def perform_cancel():
            ok, msg = db.cancel_booking(booking_id, self.app.current_user["user_id"])
            if ok:
                show_modal(self.app, "Booking cancelled",
                           "Your reservation has been cancelled successfully.",
                           icon="✓", accent="#758A93", confirm_text="Done",
                           on_confirm=lambda: self.app.navigate(MyBookingsPage))
            else:
                show_modal(self.app, "Could not cancel booking", msg,
                           icon="!", accent="#B85C61", confirm_text="Close",
                           on_confirm=lambda: self.app.navigate(MyBookingsPage))

        show_modal(self.app, "Cancel this booking?",
                   "This action will release the seats from your reservation.",
                   icon="!", accent="#B85C61", confirm_text="Yes, cancel booking",
                   cancel_text="Keep booking", on_confirm=perform_cancel,
                   details=[("Booking ID", str(booking_id))])


# =====================================================================
#  ADMIN PAGE (sidebar + sections)
# =====================================================================
class AdminPage(tk.Frame):
    SECTIONS = (("overview", "Dashboard"), ("movies", "Movies"),
                ("showtimes", "Showtimes"), ("bookings", "All Bookings"))

    def __init__(self, app):
        super().__init__(app, bg=BG)
        self.app = app

        side = tk.Frame(self, bg=NAV, width=230)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        brand = tk.Frame(side, bg=NAV)
        brand.pack(anchor="w", padx=24, pady=(24, 0))
        lbl(brand, "CINE", 16, True, fg=ACCENT, bg=NAV).pack(side="left")
        lbl(brand, "MA", 16, True, bg=NAV).pack(side="left")
        lbl(side, "Admin Panel", 9, fg=MUTED, bg=NAV).pack(anchor="w", padx=24, pady=(0, 24))

        Btn(side, "Logout", app.logout, kind="ghost").pack(side="bottom", fill="x",
                                                          padx=20, pady=20)
        lbl(side, app.current_user["full_name"], 10, fg=MUTED, bg=NAV).pack(
            side="bottom", pady=(0, 4))

        self.nav = {}
        for key, text in self.SECTIONS:
            item = tk.Label(side, text=text, anchor="w", padx=24, pady=12, bg=NAV,
                            fg=MUTED, font=(FONT, 11, "bold"), cursor="hand2")
            item.pack(fill="x")
            item.bind("<Button-1>", lambda e, k=key: self.show_section(k))
            self.nav[key] = item

        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="right", fill="both", expand=True, padx=30, pady=24)
        self.show_section("overview")

    def show_section(self, key):
        for k, item in self.nav.items():
            item.config(bg=ACCENT if k == key else NAV,
                        fg="white" if k == key else MUTED)
        for widget in self.content.winfo_children():
            widget.destroy()
        getattr(self, f"build_{key}")()

    # ----- Dashboard -----
    def build_overview(self):
        page_title(self.content, "Dashboard", "A quick look at your cinema")
        movies = db.get_movies()
        bookings = db.get_all_bookings()
        revenue = sum(float(b["total_price"] or 0) for b in bookings)
        tickets = sum(int(b["seats_count"] or 0) for b in bookings)

        stats = tk.Frame(self.content, bg=BG)
        stats.pack(fill="x", pady=10)
        items = (("Movies", len(movies), ACCENT),
                 ("Bookings", len(bookings), "#7c4dff"),
                 ("Tickets sold", tickets, "#00acc1"),
                 ("Revenue (EGP)", f"{revenue:,.0f}", "#fb8c00"))
        for i, (title, value, color) in enumerate(items):
            stats.grid_columnconfigure(i, weight=1, uniform="stat")
            card = tk.Frame(stats, bg=CARD)
            card.grid(row=0, column=i, sticky="nsew", padx=8)
            tk.Frame(card, bg=color, height=4).pack(fill="x")
            lbl(card, str(value), 26, True, bg=CARD).pack(anchor="w", padx=18, pady=(16, 0))
            lbl(card, title, 10, fg=MUTED, bg=CARD).pack(anchor="w", padx=18, pady=(0, 16))

    # ----- Movies -----
    def build_movies(self):
        page_title(self.content, "Movies", "Add, edit or remove movies")
        row = tk.Frame(self.content, bg=BG)
        row.pack(fill="both", expand=True, pady=(10, 0))

        form = tk.Frame(row, bg=CARD, padx=22, pady=22)
        form.pack(side="right", fill="y", padx=(20, 0))
        lbl(form, "Movie Details", 14, True, bg=CARD).pack(anchor="w", pady=(0, 14))
        self.m_title = field(form, "Title")
        self.m_genre = field(form, "Genre")
        self.m_duration = field(form, "Duration (minutes)")
        Btn(form, "Add Movie", self.add_movie).pack(fill="x", pady=(0, 8))
        Btn(form, "Update Selected", self.update_movie, kind="ghost").pack(fill="x", pady=(0, 8))
        Btn(form, "Delete Selected", self.delete_movie, kind="danger").pack(fill="x", pady=(0, 8))
        Btn(form, "Clear", self.clear_form, kind="ghost").pack(fill="x")

        table, self.movies_tree = make_table(row, [("id", "ID", 50), ("title", "Title", 260),
                                                   ("genre", "Genre", 120),
                                                   ("duration", "Minutes", 80)])
        table.pack(side="left", fill="both", expand=True)
        self.movies_tree.bind("<<TreeviewSelect>>", self.on_movie_select)
        self.load_movies()

    def load_movies(self):
        fill_tree(self.movies_tree, db.get_movies(),
                  ["movie_id", "title", "genre", "duration_min"], "movie_id")

    def on_movie_select(self, event=None):
        selected = self.movies_tree.selection()
        if not selected:
            return
        v = self.movies_tree.item(selected[0])["values"]
        self.clear_form()
        self.m_title.insert(0, v[1])
        self.m_genre.insert(0, v[2])
        self.m_duration.insert(0, v[3])

    def clear_form(self):
        for entry in (self.m_title, self.m_genre, self.m_duration):
            entry.delete(0, "end")

    def form_is_valid(self):
        if not self.m_title.get().strip() or not self.m_duration.get().strip().isdigit():
            messagebox.showwarning("Invalid data", "Title and a numeric duration are required.")
            return False
        return True

    def show_result(self, ok, msg):
        if ok:
            messagebox.showinfo("Done", msg)
            self.clear_form()
            self.load_movies()
        else:
            messagebox.showerror("Error", msg)

    def add_movie(self):
        if self.form_is_valid():
            self.show_result(*db.add_movie(self.m_title.get().strip(),
                                           self.m_genre.get().strip(),
                                           self.m_duration.get().strip()))

    def update_movie(self):
        selected = self.movies_tree.selection()
        if not selected:
            messagebox.showwarning("Select first", "Please select a movie from the table.")
            return
        if self.form_is_valid():
            self.show_result(*db.update_movie(int(selected[0]),
                                              self.m_title.get().strip(),
                                              self.m_genre.get().strip(),
                                              self.m_duration.get().strip()))

    def delete_movie(self):
        selected = self.movies_tree.selection()
        if not selected:
            messagebox.showwarning("Select first", "Please select a movie from the table.")
            return
        if messagebox.askyesno("Confirm", "Deleting a movie also deletes its showtimes and bookings. Continue?"):
            self.show_result(*db.delete_movie(int(selected[0])))

    # ----- Showtimes -----
    def build_showtimes(self):
        page_title(self.content, "Showtimes", "Schedule a movie in one of your halls")
        card = tk.Frame(self.content, bg=CARD, padx=30, pady=26)
        card.pack(anchor="nw", pady=10)
        lbl(card, "Add a New Showtime", 14, True, bg=CARD).pack(anchor="w", pady=(0, 14))

        lbl(card, "Movie", 9, fg=MUTED, bg=CARD, anchor="w").pack(fill="x")
        self.st_movie = ttk.Combobox(card, state="readonly", width=40)
        self.st_movie.pack(fill="x", ipady=4, pady=(4, 14))
        lbl(card, "Hall", 9, fg=MUTED, bg=CARD, anchor="w").pack(fill="x")
        self.st_hall = ttk.Combobox(card, state="readonly", width=40)
        self.st_hall.pack(fill="x", ipady=4, pady=(4, 14))
        self.st_movie["values"] = [f'{m["movie_id"]} - {m["title"]}' for m in db.get_movies()]
        self.st_hall["values"] = [f'{h["hall_id"]} - {h["hall_name"]}' for h in db.get_halls()]

        self.st_date = field(card, "Date (YYYY-MM-DD)")
        self.st_date.insert(0, date.today().isoformat())
        self.st_time = field(card, "Time (HH:MM)")
        self.st_time.insert(0, "18:00")
        self.st_price = field(card, "Price (EGP)")
        Btn(card, "Add Showtime", self.add_showtime).pack(fill="x", pady=(6, 0))

    def add_showtime(self):
        if not self.st_movie.get() or not self.st_hall.get() or not self.st_price.get().strip():
            messagebox.showwarning("Missing data", "Please fill in all fields.")
            return
        movie_id = int(self.st_movie.get().split(" - ")[0])
        hall_id = int(self.st_hall.get().split(" - ")[0])
        ok, msg = db.add_showtime(movie_id, hall_id, self.st_date.get().strip(),
                                  self.st_time.get().strip(), self.st_price.get().strip())
        if ok:
            messagebox.showinfo("Done", msg)
        else:
            messagebox.showerror("Error", msg)

    # ----- All bookings -----
    def build_bookings(self):
        page_title(self.content, "All Bookings", "Every booking made by your customers")
        table, self.all_tree = make_table(self.content, [
            ("id", "ID", 50), ("user", "Customer", 150), ("movie", "Movie", 200),
            ("date", "Date", 100), ("time", "Time", 70),
            ("count", "Seats", 60), ("total", "Total (EGP)", 100)])
        table.pack(fill="both", expand=True, pady=(10, 10))
        Btn(self.content, "Refresh", self.load_all_bookings).pack(anchor="e")
        self.load_all_bookings()

    def load_all_bookings(self):
        fill_tree(self.all_tree, db.get_all_bookings(),
                  ["booking_id", "full_name", "title", "show_date", "show_time",
                   "seats_count", "total_price"], "booking_id")


if __name__ == "__main__":
    CinemaApp().mainloop()