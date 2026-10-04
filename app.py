"""
MDrip — Convert any file to Markdown.

Backend: Microsoft MarkItDown + Instant Fast-Path Engine.
UI: Refined frosted mint-aqua glass aesthetics, pixel-art sprites, adaptive smooth animations.
Optimizations:
  1. Lazy Engine Pre-Warming (instant startup window)
  2. Persistent Engine Singleton (zero reload delay)
  3. Fast-Path for Plain Text / Code / CSV (sub-millisecond conversion)
  4. Adaptive Frame Rate (Focus & Idle throttling for 0% background CPU)
  5. Instant Visual Drop Feedback (zero-latency card response)
"""

import os
import sys
import csv
import time
import math
import threading
import subprocess
import ctypes
from ctypes import wintypes

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk

# ── DPI Awareness ────────────────────────────────────────────────────────────
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ── UI Configuration ─────────────────────────────────────────────────────────
CONFIG = {
    "app_name": "MDrip",
    "win_width": 650,
    "win_height": 360,
    "status_height": 28,
    "drop_zone": {
        "x1": 95, "y1": 36, "x2": 555, "y2": 204, "radius": 16,
        "border_color": "#5AD6C4",
        "border_active": "#24F0D6",
        "border_width": 2,
        "active_width": 3,
    },
    "button": {
        "x": 225, "y": 224, "width": 200, "height": 42,
    },
    "colors": {
        "navy_text": "#1E2D3D",
        "grey_hint": "#647B8C",
        "grey_sub": "#7A92A0",
        "status_bg": "#EBF5F3",
        "status_ready": "#8E9E9C",
        "status_working": "#0D9488",
        "status_done": "#16A34A",
        "status_error": "#DC2626",
        "link_teal": "#0D9488",
        "badge_bg": "#3ED8C2",
        "badge_fg": "#1E2D3D",
        "clear_hover": "#D8EFEB",
    },
    "fonts": {
        "main": ("Segoe UI", 14, "bold"),
        "sub": ("Segoe UI", 10),
        "card_name": ("Segoe UI", 12, "bold"),
        "card_sub": ("Segoe UI", 10),
        "card_hint": ("Segoe UI", 9),
        "card_badge": ("Segoe UI", 8, "bold"),
        "status": ("Segoe UI", 9),
        "status_link": ("Segoe UI", 9, "underline"),
    },
    "timings": {
        "active_fps_ms": 35,         # ~28 FPS when user is interacting / hovering
        "focused_fps_ms": 70,        # ~14 FPS when window is focused but idle
        "unfocused_fps_ms": 250,     # ~4 FPS when window is in background
        "marching_step_ticks": 2,    # Border marching step interval
    }
}

DZ = CONFIG["drop_zone"]
BTN = CONFIG["button"]
CLR = CONFIG["colors"]
FNT = CONFIG["fonts"]
TIM = CONFIG["timings"]

# ── Fast-Path File Extensions ────────────────────────────────────────────────
FAST_TEXT_EXTS = {".txt", ".log", ".md"}

FAST_CODE_EXTS = {
    ".py": "python", ".js": "javascript", ".jsx": "jsx", ".ts": "typescript", ".tsx": "tsx",
    ".html": "html", ".htm": "html", ".css": "css", ".json": "json", ".xml": "xml",
    ".yaml": "yaml", ".yml": "yaml", ".sql": "sql", ".sh": "bash", ".bash": "bash",
    ".bat": "bat", ".cmd": "bat", ".ps1": "powershell",
    ".c": "c", ".cpp": "cpp", ".h": "c", ".hpp": "cpp", ".cs": "csharp",
    ".java": "java", ".go": "go", ".rs": "rust",
    ".ini": "ini", ".cfg": "ini", ".conf": "ini", ".toml": "toml", ".env": "env"
}

def asset_path(name: str) -> str:
    """Returns absolute path to an asset, compatible with PyInstaller bundles."""
    if getattr(sys, "_MEIPASS", None):
        base = os.path.join(sys._MEIPASS, "assets")
    else:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    return os.path.join(base, name)

def set_titlebar_color(root):
    """
    Sets the title bar color to soft white-mint with dark text via Windows DWM.
    Applies to the top-level parent HWND. Safe fallbacks for older Windows versions.
    """
    try:
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        if not hwnd:
            hwnd = root.winfo_id()

        DwmSetWindowAttribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        DwmSetWindowAttribute.argtypes = [
            wintypes.HWND,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.DWORD
        ]
        DwmSetWindowAttribute.restype = ctypes.HRESULT

        # Force light mode: DWMWA_USE_IMMERSIVE_DARK_MODE (20 or 19) = 0
        light = ctypes.c_int(0)
        for attr in (20, 19):
            try:
                DwmSetWindowAttribute(hwnd, attr, ctypes.byref(light), ctypes.sizeof(light))
            except Exception:
                pass

        # Windows 11 DWM caption & text color (BGR format: 0x00BBGGRR)
        # Soft mint caption: RGB(235, 248, 246) -> BGR(246, 248, 235) = 0x00F6F8EB
        mint = ctypes.c_uint32(0x00F6F8EB)
        DwmSetWindowAttribute(hwnd, 35, ctypes.byref(mint), ctypes.sizeof(mint))

        # Dark navy caption text: RGB(30, 45, 60) -> BGR(60, 45, 30) = 0x003C2D1E
        dark = ctypes.c_uint32(0x003C2D1E)
        DwmSetWindowAttribute(hwnd, 36, ctypes.byref(dark), ctypes.sizeof(dark))

        # Soft mint border: RGB(210, 240, 235) -> BGR(235, 240, 210) = 0x00EBF0D2
        border = ctypes.c_uint32(0x00EBF0D2)
        DwmSetWindowAttribute(hwnd, 34, ctypes.byref(border), ctypes.sizeof(border))
    except Exception:
        pass

def format_file_size(size_bytes: int) -> str:
    """Formats file size into human-readable B, KB, MB, or GB."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def truncate_middle(text: str, max_chars: int = 34) -> str:
    """Truncates long text in the middle with '...'."""
    if len(text) <= max_chars:
        return text
    keep = (max_chars - 3) // 2
    return text[:keep] + "..." + text[-keep:]

def get_rounded_rect_points(x1, y1, x2, y2, r):
    """Calculates points for smooth rounded rectangle perimeter."""
    pts = []
    pts.extend([x1 + r, y1, x2 - r, y1])
    for a in range(0, 91, 15):
        rad = math.radians(a - 90)
        pts.extend([x2 - r + r * math.cos(rad), y1 + r + r * math.sin(rad)])
    pts.extend([x2, y1 + r, x2, y2 - r])
    for a in range(0, 91, 15):
        rad = math.radians(a)
        pts.extend([x2 - r + r * math.cos(rad), y2 - r + r * math.sin(rad)])
    pts.extend([x2 - r, y2, x1 + r, y2])
    for a in range(0, 91, 15):
        rad = math.radians(a + 90)
        pts.extend([x1 + r + r * math.cos(rad), y2 - r + r * math.sin(rad)])
    pts.extend([x1, y2 - r, x1, y1 + r])
    for a in range(0, 91, 15):
        rad = math.radians(a + 180)
        pts.extend([x1 + r + r * math.cos(rad), y1 + r + r * math.sin(rad)])
    return pts

def unique_md_path(source_path: str) -> str:
    """Generates unique destination path in the source folder."""
    folder = os.path.dirname(source_path)
    base, ext = os.path.splitext(os.path.basename(source_path))

    if ext.lower() == ".md":
        candidate = os.path.join(folder, f"{base}_converted.md")
        if not os.path.exists(candidate):
            return candidate
        n = 2
        while True:
            candidate = os.path.join(folder, f"{base}_converted{n}.md")
            if not os.path.exists(candidate):
                return candidate
            n += 1

    candidate = os.path.join(folder, f"{base}.md")
    if not os.path.exists(candidate):
        return candidate
    candidate = os.path.join(folder, f"{base}_converted.md")
    if not os.path.exists(candidate):
        return candidate
    n = 2
    while True:
        candidate = os.path.join(folder, f"{base}_converted{n}.md")
        if not os.path.exists(candidate):
            return candidate
        n += 1

# ── Fast-Path Converter ──────────────────────────────────────────────────────

def csv_to_markdown_table(filepath: str, delimiter: str = ",") -> str:
    """Converts CSV/TSV data into a clean GitHub Flavored Markdown table."""
    rows = []
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with open(filepath, "r", encoding=enc, errors="replace") as f:
                reader = csv.reader(f, delimiter=delimiter)
                for row in reader:
                    rows.append([cell.strip().replace("\n", " ").replace("|", "\\|") for cell in row])
            break
        except Exception:
            continue

    if not rows:
        return ""

    num_cols = max(len(r) for r in rows)
    if num_cols == 0:
        return ""

    for r in rows:
        if len(r) < num_cols:
            r.extend([""] * (num_cols - len(r)))

    header = rows[0]
    lines = []
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * num_cols) + " |")
    for r in rows[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines) + "\n"

def try_fast_convert(filepath: str):
    """
    Attempts instant conversion for text, code, and CSV.
    Returns markdown string if handled, or None to route to MarkItDown engine.
    """
    _, ext = os.path.splitext(filepath)
    ext_lower = ext.lower()

    # 1. Tabular data (CSV / TSV)
    if ext_lower in (".csv", ".tsv"):
        sep = "\t" if ext_lower == ".tsv" else ","
        try:
            res = csv_to_markdown_table(filepath, delimiter=sep)
            if res:
                return res
        except Exception:
            return None

    # 2. Source code and markup
    if ext_lower in FAST_CODE_EXTS:
        lang = FAST_CODE_EXTS[ext_lower]
        for enc in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                with open(filepath, "r", encoding=enc, errors="replace") as f:
                    content = f.read()
                return f"```{lang}\n{content}\n```\n"
            except Exception:
                continue

    # 3. Plain text / logs
    if ext_lower in FAST_TEXT_EXTS:
        for enc in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                with open(filepath, "r", encoding=enc, errors="replace") as f:
                    return f.read()
            except Exception:
                continue

    return None


class ToolTip:
    """Lightweight hover tooltip for widgets and canvas regions."""
    def __init__(self, widget, text_provider):
        self.widget = widget
        self.text_provider = text_provider
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        text = self.text_provider()
        if not text or self.tip_window:
            return
        x, y = self.widget.winfo_pointerxy()
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x + 12}+{y + 16}")
        label = tk.Label(tw, text=text, justify="left",
                         background="#243342", foreground="#FFFFFF",
                         relief="solid", borderwidth=0,
                         font=("Segoe UI", 8), padx=7, pady=4)
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class AppWindow(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.selected_file = None
        self.last_saved_path = None
        self.is_converting = False
        self.btn_state = "disabled"

        # Engine pre-warming & singleton state
        self._engine = None
        self._engine_loading = False

        # Animation & responsiveness state
        self._anim_tick = 0
        self._dash_offset = 0
        self._anim_running = True
        self._shake_frames = []

        # Adaptive FPS tracking
        self._is_focused = True
        self._last_user_activity = time.time()

        # Configure window
        self.title(CONFIG["app_name"])
        self.geometry(f"{CONFIG['win_width']}x{CONFIG['win_height']}")
        self.resizable(False, False)

        icon_p = asset_path("app_icon.ico")
        if os.path.exists(icon_p):
            self.iconbitmap(icon_p)

        self.after(50, lambda: set_titlebar_color(self))

        # Load Assets
        self._load_assets()

        # Build UI
        self._build_ui()

        # Start animation ticker
        self._start_animations()

        # Optimization 1: Lazy background engine pre-warming
        threading.Thread(target=self._prewarm_engine, daemon=True).start()

    def _prewarm_engine(self):
        """Pre-warms the MarkItDown engine singleton silently in background thread."""
        self._engine_loading = True
        try:
            from markitdown import MarkItDown
            self._engine = MarkItDown()
        except Exception as exc:
            print("Engine pre-warming warning:", exc)
        finally:
            self._engine_loading = False

    def _load_assets(self):
        """Loads and caches all pre-rendered UI images."""
        self.bg_img = ImageTk.PhotoImage(Image.open(asset_path("background.png")))
        self.icon_idle_img = ImageTk.PhotoImage(Image.open(asset_path("icon_idle.png")))
        self.file_card_img = ImageTk.PhotoImage(Image.open(asset_path("file_card.png")))
        self.icon_doc_img = ImageTk.PhotoImage(Image.open(asset_path("icon_doc.png")))

        self.icon_check_img = ImageTk.PhotoImage(Image.open(asset_path("icon_check.png")))
        self.icon_warn_img = ImageTk.PhotoImage(Image.open(asset_path("icon_warn.png")))

        # Button states
        self.btn_imgs = {
            "disabled": ImageTk.PhotoImage(Image.open(asset_path("btn_disabled.png"))),
            "enabled": ImageTk.PhotoImage(Image.open(asset_path("btn_enabled.png"))),
            "hover": ImageTk.PhotoImage(Image.open(asset_path("btn_hover.png"))),
            "pressed": ImageTk.PhotoImage(Image.open(asset_path("btn_pressed.png"))),
            "converting": ImageTk.PhotoImage(Image.open(asset_path("btn_converting.png"))),
            "done": ImageTk.PhotoImage(Image.open(asset_path("btn_done.png"))),
        }

    def _build_ui(self):
        # 1. Main Background Canvas
        c_w = CONFIG["win_width"]
        c_h = CONFIG["win_height"] - CONFIG["status_height"]
        self.canvas = tk.Canvas(self, width=c_w, height=c_h, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Static background
        self.canvas.create_image(c_w // 2, c_h // 2, image=self.bg_img, anchor="center")

        # 2. Drop Zone Marching Border
        pts = get_rounded_rect_points(DZ["x1"], DZ["y1"], DZ["x2"], DZ["y2"], DZ["radius"])
        self.border_id = self.canvas.create_line(
            *pts, fill=DZ["border_color"], width=DZ["border_width"],
            dash=(6, 5), dashoffset=0
        )

        # 3. Drop Zone Idle Items
        cx = (DZ["x1"] + DZ["x2"]) // 2
        self.idle_icon_base_y = DZ["y1"] + 54
        self.idle_icon_id = self.canvas.create_image(cx, self.idle_icon_base_y, image=self.icon_idle_img, anchor="center")

        self.idle_main_text = self.canvas.create_text(
            cx, DZ["y1"] + 112,
            text="Drop a file here  –  or click to browse",
            font=FNT["main"], fill=CLR["navy_text"]
        )
        self.idle_sub_text = self.canvas.create_text(
            cx, DZ["y1"] + 140,
            text="Any file type  →  clean Markdown",
            font=FNT["sub"], fill=CLR["grey_hint"]
        )

        # 4. File Chosen Card Items (initially hidden)
        fc_y = DZ["y1"] + (DZ["y2"] - DZ["y1"]) // 2 - 12
        self.card_bg_id = self.canvas.create_image(cx, fc_y, image=self.file_card_img, anchor="center", state="hidden")
        self.card_doc_id = self.canvas.create_image(cx - 150, fc_y, image=self.icon_doc_img, anchor="center", state="hidden")

        # Small extension badge
        self.card_badge_rect = self.canvas.create_rectangle(
            cx - 168, fc_y + 10, cx - 132, fc_y + 24,
            fill=CLR["badge_bg"], outline="", state="hidden"
        )
        self.card_badge_text = self.canvas.create_text(
            cx - 150, fc_y + 17, text="", font=FNT["card_badge"], fill=CLR["badge_fg"], state="hidden"
        )

        # File name and file size
        self.card_name_text = self.canvas.create_text(
            cx - 118, fc_y - 10, text="", font=FNT["card_name"], fill=CLR["navy_text"], anchor="w", state="hidden"
        )
        self.card_size_text = self.canvas.create_text(
            cx - 118, fc_y + 12, text="", font=FNT["card_sub"], fill=CLR["grey_hint"], anchor="w", state="hidden"
        )

        # Clear '✕' button
        self.clear_btn_circle = self.canvas.create_oval(
            cx + 140, fc_y - 14, cx + 168, fc_y + 14,
            fill="", outline="", state="hidden"
        )
        self.clear_btn_text = self.canvas.create_text(
            cx + 154, fc_y, text="✕", font=("Segoe UI", 11, "bold"), fill=CLR["grey_hint"], state="hidden"
        )

        # Secondary hint below file card
        self.card_change_hint = self.canvas.create_text(
            cx, DZ["y2"] - 18, text="Click or drop to change file",
            font=FNT["card_hint"], fill=CLR["grey_sub"], state="hidden"
        )

        # 5. Convert Button
        self.btn_id = self.canvas.create_image(BTN["x"], BTN["y"], image=self.btn_imgs["disabled"], anchor="nw")

        # 6. Status Bar
        self.status_frame = tk.Frame(self, bg=CLR["status_bg"], height=CONFIG["status_height"])
        self.status_frame.pack(side="bottom", fill="x")
        self.status_frame.pack_propagate(False)

        # Status icon / dot
        self.status_icon_label = tk.Label(self.status_frame, bg=CLR["status_bg"], text="●", fg=CLR["status_ready"], font=("Segoe UI", 8))
        self.status_icon_label.pack(side="left", padx=(12, 4))

        # Status message label
        self.status_label = tk.Label(self.status_frame, text="Ready", bg=CLR["status_bg"], fg=CLR["grey_hint"], font=FNT["status"])
        self.status_label.pack(side="left", padx=2)

        # Tooltip on status label for full path
        self.status_tooltip = ToolTip(self.status_label, self._get_status_tooltip_text)

        # Resize grip
        grip = tk.Label(self.status_frame, text="⠿", bg=CLR["status_bg"], fg="#B4C8C5", font=("Segoe UI", 10))
        grip.pack(side="right", padx=8)

        # 7. Drag-and-Drop Setup
        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind("<<DropEnter>>", self._on_drag_enter)
        self.canvas.dnd_bind("<<DropLeave>>", self._on_drag_leave)
        self.canvas.dnd_bind("<<Drop>>", self._on_drop)

        # Mouse Events
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)

        # Optimization 4: Focus & Window state tracking for adaptive FPS
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Unmap>", lambda e: self._set_anim_state(False))
        self.bind("<Map>", lambda e: self._set_anim_state(True))

    # ── Adaptive Animation Loop ──
    def _on_focus_in(self, event):
        self._is_focused = True
        self._last_user_activity = time.time()

    def _on_focus_out(self, event):
        self._is_focused = False

    def _set_anim_state(self, running: bool):
        self._anim_running = running
        if running:
            self._start_animations()

    def _start_animations(self):
        self._on_tick()

    def _on_tick(self):
        if not self._anim_running:
            return

        self._anim_tick += 1

        # 1. Marching border dots (every 2 ticks)
        if self._anim_tick % TIM["marching_step_ticks"] == 0:
            self._dash_offset = (self._dash_offset + 1) % 11
            self.canvas.itemconfig(self.border_id, dashoffset=self._dash_offset)

        # 2. Gentle sinusoidal icon float in idle state
        if not self.selected_file:
            offset = math.sin(self._anim_tick * 0.08) * 2.5
            cx = (DZ["x1"] + DZ["x2"]) // 2
            self.canvas.coords(self.idle_icon_id, cx, self.idle_icon_base_y + offset)

        # 3. Drop zone shake animation on error
        if self._shake_frames:
            dx = self._shake_frames.pop(0)
            self._apply_shake_offset(dx)

        # Optimization 4: Adaptive Framerate Scaling
        now = time.time()
        is_user_active = (now - self._last_user_activity) < 2.5

        if self.is_converting or self._shake_frames:
            next_delay = TIM["active_fps_ms"]
        elif is_user_active:
            next_delay = TIM["active_fps_ms"]
        elif self._is_focused:
            next_delay = TIM["focused_fps_ms"]
        else:
            # Unfocused / background window -> throttle to ~4 FPS (0% CPU)
            next_delay = TIM["unfocused_fps_ms"]

        self.after(next_delay, self._on_tick)

    def _trigger_shake(self):
        """Snappy 300ms horizontal shake animation."""
        self._shake_frames = [-8, 8, -6, 6, -4, 4, -2, 2, 0]

    def _apply_shake_offset(self, dx: int):
        cx = (DZ["x1"] + DZ["x2"]) // 2 + dx
        self.canvas.coords(self.idle_icon_id, cx, self.idle_icon_base_y)
        self.canvas.coords(self.idle_main_text, cx, DZ["y1"] + 112)
        self.canvas.coords(self.idle_sub_text, cx, DZ["y1"] + 140)

        fc_y = DZ["y1"] + (DZ["y2"] - DZ["y1"]) // 2 - 12
        self.canvas.coords(self.card_bg_id, cx, fc_y)
        self.canvas.coords(self.card_doc_id, cx - 150, fc_y)
        self.canvas.coords(self.card_badge_rect, cx - 168, fc_y + 10, cx - 132, fc_y + 24)
        self.canvas.coords(self.card_badge_text, cx - 150, fc_y + 17)
        self.canvas.coords(self.card_name_text, cx - 118, fc_y - 10)
        self.canvas.coords(self.card_size_text, cx - 118, fc_y + 12)
        self.canvas.coords(self.clear_btn_circle, cx + 140, fc_y - 14, cx + 168, fc_y + 14)
        self.canvas.coords(self.clear_btn_text, cx + 154, fc_y)
        self.canvas.coords(self.card_change_hint, cx, DZ["y2"] - 18)

    # ── State Updates ──
    def _set_button_state(self, state: str):
        self.btn_state = state
        self.canvas.itemconfig(self.btn_id, image=self.btn_imgs[state])

    def _show_idle_ui(self):
        """Switches drop zone view to idle state."""
        self.canvas.itemconfig(self.idle_icon_id, state="normal")
        self.canvas.itemconfig(self.idle_main_text, state="normal", text="Drop a file here  –  or click to browse")
        self.canvas.itemconfig(self.idle_sub_text, state="normal")

        for item in (self.card_bg_id, self.card_doc_id, self.card_badge_rect,
                     self.card_badge_text, self.card_name_text, self.card_size_text,
                     self.clear_btn_circle, self.clear_btn_text, self.card_change_hint):
            self.canvas.itemconfig(item, state="hidden")

        self.canvas.itemconfig(self.border_id, fill=DZ["border_color"], width=DZ["border_width"])

    def _show_file_card_ui(self):
        """Switches drop zone view to file card state."""
        self.canvas.itemconfig(self.idle_icon_id, state="hidden")
        self.canvas.itemconfig(self.idle_main_text, state="hidden")
        self.canvas.itemconfig(self.idle_sub_text, state="hidden")

        for item in (self.card_bg_id, self.card_doc_id, self.card_badge_rect,
                     self.card_badge_text, self.card_name_text, self.card_size_text,
                     self.clear_btn_circle, self.clear_btn_text, self.card_change_hint):
            self.canvas.itemconfig(item, state="normal")

        self.canvas.itemconfig(self.border_id, fill=DZ["border_color"], width=DZ["border_width"])

    def _set_status(self, text: str, mode: str = "ready", link_path: str = None):
        """Updates the status bar text, indicator icon, and click behavior."""
        self.last_saved_path = link_path
        self.status_label.unbind("<Button-1>")

        if mode == "ready":
            self.status_icon_label.config(text="●", fg=CLR["status_ready"], image="")
            self.status_label.config(text=text, fg=CLR["grey_hint"], font=FNT["status"], cursor="")
        elif mode == "working":
            self.status_icon_label.config(text="●", fg=CLR["status_working"], image="")
            self.status_label.config(text=text, fg=CLR["status_working"], font=FNT["status"], cursor="")
        elif mode == "success":
            self.status_icon_label.config(image=self.icon_check_img, text="")
            self.status_label.config(text=text, fg=CLR["link_teal"], font=FNT["status_link"], cursor="hand2")
            if link_path:
                self.status_label.bind("<Button-1>", lambda e: self._open_in_explorer(link_path))
        elif mode == "error":
            self.status_icon_label.config(image=self.icon_warn_img, text="")
            self.status_label.config(text=text, fg=CLR["status_error"], font=FNT["status"], cursor="")

    def _get_status_tooltip_text(self) -> str:
        if self.last_saved_path:
            return f"Click to reveal in Explorer:\n{self.last_saved_path}"
        if self.selected_file:
            return self.selected_file
        return ""

    def _open_in_explorer(self, file_path: str):
        """Reveals the converted file in Windows Explorer."""
        try:
            norm = os.path.normpath(file_path)
            subprocess.Popen(f'explorer /select,"{norm}"')
        except Exception:
            try:
                os.startfile(os.path.dirname(file_path))
            except Exception:
                pass

    # ── Drag and Drop Handlers ──
    def _on_drag_enter(self, event):
        self._last_user_activity = time.time()
        self.canvas.itemconfig(self.border_id, fill=DZ["border_active"], width=DZ["active_width"])
        if not self.selected_file:
            self.canvas.itemconfig(self.idle_main_text, text="Release to add your file")

    def _on_drag_leave(self, event):
        self.canvas.itemconfig(self.border_id, fill=DZ["border_color"], width=DZ["border_width"])
        if not self.selected_file:
            self.canvas.itemconfig(self.idle_main_text, text="Drop a file here  –  or click to browse")

    def _on_drop(self, event):
        self._last_user_activity = time.time()
        self._on_drag_leave(None)
        files = self.tk.splitlist(event.data)
        if files:
            self._set_file(files[0])

    # ── Mouse Interaction Handlers ──
    def _is_in_drop_zone(self, x, y) -> bool:
        return DZ["x1"] <= x <= DZ["x2"] and DZ["y1"] <= y <= DZ["y2"]

    def _is_in_button(self, x, y) -> bool:
        return BTN["x"] <= x <= BTN["x"] + BTN["width"] and BTN["y"] <= y <= BTN["y"] + BTN["height"]

    def _is_in_clear_btn(self, x, y) -> bool:
        if not self.selected_file:
            return False
        cx = (DZ["x1"] + DZ["x2"]) // 2
        fc_y = DZ["y1"] + (DZ["y2"] - DZ["y1"]) // 2 - 12
        return (cx + 140 <= x <= cx + 168) and (fc_y - 14 <= y <= fc_y + 14)

    def _on_click(self, event):
        self._last_user_activity = time.time()
        if self.is_converting:
            return

        if self._is_in_clear_btn(event.x, event.y):
            self._clear_file()
            return

        if self._is_in_button(event.x, event.y):
            if self.btn_state in ("enabled", "hover"):
                self._set_button_state("pressed")
            elif self.btn_state == "done":
                self._clear_file()
            return

        if self._is_in_drop_zone(event.x, event.y):
            self._browse()

    def _on_release(self, event):
        self._last_user_activity = time.time()
        if self.is_converting:
            return

        if self.btn_state == "pressed":
            if self._is_in_button(event.x, event.y):
                self._start_conversion()
            else:
                self._set_button_state("enabled")

    def _on_motion(self, event):
        self._last_user_activity = time.time()
        if self.is_converting:
            self.config(cursor="")
            return

        # Clear button hover
        if self._is_in_clear_btn(event.x, event.y):
            self.canvas.itemconfig(self.clear_btn_circle, fill=CLR["clear_hover"])
            self.config(cursor="hand2")
            return
        elif self.selected_file:
            self.canvas.itemconfig(self.clear_btn_circle, fill="")

        # Button hover
        if self._is_in_button(event.x, event.y):
            if self.btn_state in ("enabled", "hover"):
                self._set_button_state("hover")
                self.config(cursor="hand2")
            elif self.btn_state == "done":
                self.config(cursor="hand2")
            else:
                self.config(cursor="")
            return
        else:
            if self.btn_state == "hover":
                self._set_button_state("enabled")

        # Drop zone hover
        if self._is_in_drop_zone(event.x, event.y):
            self.config(cursor="hand2")
        else:
            self.config(cursor="")

    # ── File Handling (Optimization 5: Instant Visual Drop Feedback) ──
    def _browse(self):
        path = filedialog.askopenfilename(title="Select a file to convert")
        if path:
            self._set_file(path)

    def _clear_file(self):
        """Clears chosen file and returns to idle state."""
        self.selected_file = None
        self._show_idle_ui()
        self._set_button_state("disabled")
        self._set_status("Ready", "ready")
        self.config(cursor="")

    def _set_file(self, path: str):
        """Instant visual feedback on drop or file pick."""
        norm_path = os.path.normpath(path)
        if not os.path.isfile(norm_path):
            self._set_status("Selected item is not a valid file.", "error")
            self._trigger_shake()
            return

        self.selected_file = norm_path
        filename = os.path.basename(self.selected_file)
        ext = os.path.splitext(filename)[1].lstrip(".").upper() or "FILE"
        if len(ext) > 4:
            ext = ext[:4]

        # Instant display
        display_name = truncate_middle(filename, 30)
        self.canvas.itemconfig(self.card_name_text, text=display_name)
        self.canvas.itemconfig(self.card_badge_text, text=ext)
        self.canvas.itemconfig(self.card_size_text, text="")

        # Show card instantly
        self._show_file_card_ui()
        self._set_button_state("enabled")
        self._set_status(f"Selected: {filename}", "ready")

        # Calculate file size without blocking UI
        threading.Thread(target=self._async_fetch_file_size, args=(self.selected_file,), daemon=True).start()

    def _async_fetch_file_size(self, file_path: str):
        try:
            sz_bytes = os.path.getsize(file_path)
            sz_str = format_file_size(sz_bytes)
            self.after(0, lambda: self.canvas.itemconfig(self.card_size_text, text=sz_str))
        except Exception:
            pass

    # ── Conversion Task (Optimizations 2 & 3: Fast-Path + Engine Singleton) ──
    def _start_conversion(self):
        if not self.selected_file or self.is_converting:
            return

        self.is_converting = True
        self._set_button_state("converting")
        self._set_status("Converting to Markdown...", "working")
        self.config(cursor="watch")

        thread = threading.Thread(target=self._convert_task, daemon=True)
        thread.start()

    def _convert_task(self):
        try:
            out_path = unique_md_path(self.selected_file)

            # Optimization 3: Fast-Path check (sub-millisecond conversion for text/code/csv)
            fast_result = try_fast_convert(self.selected_file)
            if fast_result is not None:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(fast_result)
                self.after(0, self._on_success, out_path)
                return

            # Optimization 2: Reuse persistent MarkItDown engine singleton
            if self._engine is None:
                # Wait briefly if still pre-warming, or instantiate on demand
                while self._engine_loading and self._engine is None:
                    time.sleep(0.05)
                if self._engine is None:
                    from markitdown import MarkItDown
                    self._engine = MarkItDown()

            result = self._engine.convert(self.selected_file)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(result.text_content)

            self.after(0, self._on_success, out_path)
        except Exception as exc:
            self.after(0, self._on_error, str(exc))

    def _on_success(self, out_path: str):
        self.is_converting = False
        out_name = os.path.basename(out_path)
        trunc_name = truncate_middle(out_name, 36)

        self._set_button_state("done")
        self._set_status(f"Saved: {trunc_name}", "success", link_path=out_path)
        self.config(cursor="")

    def _on_error(self, error_msg: str):
        self.is_converting = False
        self._set_button_state("enabled")
        self._set_status("Conversion failed. Please try again.", "error")
        self._trigger_shake()
        self.config(cursor="")
        messagebox.showerror("Conversion Failed", error_msg)


if __name__ == "__main__":
    app = AppWindow()
    app.mainloop()
