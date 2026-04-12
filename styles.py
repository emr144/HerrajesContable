import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import os

# ==========================================
# PALETA SLATE & EMERALD (Puro Tkinter)
# ==========================================
BG_MAIN = "#0F172A"       # Fondo profundo
BG_CARD = "#1E293B"       # Contenedores y Tablas
BG_INPUT = "#0F172A"      # Fondo de inputs
ACCENT = "#10B981"        # Verde Esmeralda suave
TEXT_PRIMARY = "#F8FAFC"  # Blanco suave
TEXT_SECONDARY = "#94A3B8" # Gris Slate
RED_ERROR = "#EF4444"     # Rojo moderno

# Configuración de fuentes
FONT_SIZE_FACTOR = 1.0
FONT_INPUT = None
FONT_LABEL = None
FONT_NORMAL = None

def aplicar_hover(widget, color_in=ACCENT, color_out=BG_CARD):
    widget.bind("<Enter>", lambda e: widget.config(bg=color_in))
    widget.bind("<Leave>", lambda e: widget.config(bg=color_out))
    
def cargar_factor_fuente():
    try:
        if os.path.exists("font_config.txt"):
            with open("font_config.txt", "r") as f:
                return float(f.read().strip())
    except: pass
    return 1.0

def actualizar_fuentes():
    global FONT_INPUT, FONT_LABEL, FONT_NORMAL
    f = cargar_factor_fuente()
    FONT_LABEL = ("Segoe UI", int(10 * f), "bold")
    FONT_NORMAL = ("Segoe UI", int(10 * f))
    FONT_INPUT = ("Segoe UI", int(10 * f))

def configurar_estilos_ttk():
    """Configura el motor visual para un look moderno y suave """
    style = ttk.Style()
    style.theme_use("clam")

    # --- PESTAÑAS (Notebook) ---
    style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
    style.configure("TNotebook.Tab", background=BG_CARD, foreground=TEXT_SECONDARY,
                    padding=[3, 4], font=FONT_NORMAL, borderwidth=0)
    
    # SOLUCIÓN: Llenamos los corchetes para que la selección funcione [5, 2]
    style.map("TNotebook.Tab", 
              background= [("selected", BG_MAIN), ("active", BG_CARD)],
              foreground=[("selected", "white"), ("active", "white")])

    # --- TABLAS (Treeview) ---
    style.configure("Treeview", background=BG_CARD, foreground=TEXT_PRIMARY,
                    fieldbackground=BG_CARD, rowheight=35, borderwidth=0, font=FONT_NORMAL)
    
    style.configure("Treeview.Heading", background=BG_CARD, foreground=TEXT_SECONDARY,
                    font=FONT_LABEL, padding=[10, 10], borderwidth=0)
    
    # SOLUCIÓN: Color verde al seleccionar una fila 
    style.map("Treeview", 
              background=[("selected", ACCENT)], 
              foreground=[("selected", "white")])

# ==========================================
# FUNCIONES DE ESTILO PARA WIDGETS CLÁSICOS
# ==========================================

def estilo_entrada():
    """SOLUCIÓN AL ERROR: Esta función es la que tus módulos están buscando """
    return {
        "bg": BG_INPUT,
        "fg": TEXT_PRIMARY,
        "font": ("Segoe UI", 10),
        "bd": 0,
        "insertbackground": "white",
        "highlightthickness": 1,
        "highlightbackground": "#334155",
        "highlightcolor": ACCENT,
        "relief": "flat"
    }

def get_btn_style(color=BG_CARD):
    """Estilo suave para botones estándar """
    return {
        "bg": color, "fg": "white", "font": ("Segoe UI", 9, "bold"),
        "bd": 0, "padx": 20, "pady": 8, "cursor": "hand2",
        "activebackground": ACCENT, "relief": "flat"
    }

def aplicar_hover(widget, color_in=ACCENT, color_out=BG_CARD):
    widget.bind("<Enter>", lambda e: widget.config(bg=color_in))
    widget.bind("<Leave>", lambda e: widget.config(bg=color_out))

def aplicar_estilo_ventana(ventana):
    ventana.configure(bg=BG_MAIN)