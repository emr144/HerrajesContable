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
ORANGE = "#D97706"        # Naranja para avisos/edición

# Medidas predefinidas para la escala de fuente
NIVELES_FUENTE = {
    "Pequeño (80%)": 0.8,
    "Normal (100%)": 1.0,
    "Grande (120%)": 1.2,
    "Muy Grande (150%)": 1.5,
    "Gigante (200%)": 2.0,
    "Ultra Gigante (240%)": 2.4
}

# Configuración de fuentes
FONT_SIZE_FACTOR = 1.0
FONT_INPUT = None
FONT_LABEL = None
FONT_NORMAL = None
FONT_TITLE = None


    
def cargar_factor_fuente():
    try:
        if os.path.exists("font_config.txt"):
            with open("font_config.txt", "r") as f:
                return float(f.read().strip())
    except: pass
    return 1.0

def guardar_factor_fuente(factor):
    with open("font_config.txt", "w") as f:
        f.write(str(factor))

def actualizar_fuentes():
    global FONT_INPUT, FONT_LABEL, FONT_NORMAL, FONT_TITLE
    f = cargar_factor_fuente()
    try:
        # Usamos objetos Font de tkinter para que el cambio sea instantáneo en toda la app
        if FONT_LABEL is None or isinstance(FONT_LABEL, tuple):
            FONT_LABEL = tkfont.Font(family="Segoe UI", size=int(10 * f), weight="bold")
            FONT_NORMAL = tkfont.Font(family="Segoe UI", size=int(10 * f))
            FONT_INPUT = tkfont.Font(family="Segoe UI", size=int(10 * f))
            FONT_TITLE = tkfont.Font(family="Segoe UI", size=int(16 * f), weight="bold")
        else:
            FONT_LABEL.configure(size=int(10 * f))
            FONT_NORMAL.configure(size=int(10 * f))
            FONT_INPUT.configure(size=int(10 * f))
            FONT_TITLE.configure(size=int(16 * f))
    except Exception:
        # Fallback si se llama antes de iniciar Tkinter (root no existe)
        FONT_LABEL = ("Segoe UI", int(10 * f), "bold")
        FONT_NORMAL = ("Segoe UI", int(10 * f))
        FONT_INPUT = ("Segoe UI", int(10 * f))
        FONT_TITLE = ("Segoe UI", int(16 * f), "bold")

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
        "font": FONT_INPUT,
        "bd": 0,
        "insertbackground": "white",
        "highlightthickness": 1,
        "highlightbackground": "#334155",
        "highlightcolor": ACCENT,
        "relief": "flat"
    }

def estilo_boton(color=BG_CARD):
    """Estilo moderno y plano para botones de Tkinter en todo el programa"""
    return {
        "bg": color,
        "fg": "white",
        "font": FONT_LABEL,
        "bd": 0,
        "padx": 20,
        "pady": 8,
        "cursor": "hand2",
        "activebackground": ACCENT,
        "activeforeground": "white",
        "relief": "flat"
    }

get_btn_style = estilo_boton # Alias para compatibilidad

def aplicar_hover(widget, color_in=ACCENT, color_out=BG_CARD):
    pass

def aplicar_estilo_ventana(ventana):
    ventana.configure(bg=BG_MAIN)
    
