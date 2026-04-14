import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import ttkbootstrap as tb
import os

# ==========================================
# PALETA SLATE & EMERALD (Puro Tkinter)
# ==========================================
BG_MAIN = "#0F172A"       # Fondo profundo (Slate 900)
BG_CARD = "#1E293B"       # Contenedores (Slate 800)
BG_INPUT = "#334155"      # Inputs (Slate 700)
ACCENT = "#10B981"        # Emerald 500
TEXT_PRIMARY = "#F8FAFC"  # Slate 50
TEXT_SECONDARY = "#94A3B8" # Slate 400
RED_ERROR = "#F43F5E"     # Rose 500
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
        # Usamos objetos Font de tkinter para permitir actualizaciones en tiempo real.
        # Verificamos si ya son objetos Font comparando si tienen el método 'configure'
        if FONT_LABEL is None or not hasattr(FONT_LABEL, 'configure'):
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
    """Configura ttkbootstrap para un look moderno, curvo y espaciado"""
    style = tb.Style(theme="darkly")
    f = cargar_factor_fuente()

    # 1. Configuración Global para widgets TTK (Etiquetas, Botones TTK, etc.)
    style.configure(".", font=FONT_NORMAL)
    
    # 2. Tablas (Treeview): Filas más altas y look minimalista
    style.configure("Treeview", 
                    font=FONT_NORMAL, 
                    rowheight=int(40 * f), 
                    relief="flat",
                    borderwidth=0)
    style.configure("Treeview.Heading", 
                    font=FONT_LABEL, 
                    padding=[10, 12],
                    background=BG_CARD)
    
    style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

    # 3. Notebook (Pestañas): Efecto redondeado mediante padding y márgenes
    style.configure("TNotebook", tabmargins=[2, 5, 2, 0], borderwidth=0)
    
    style.configure("TNotebook.Tab", 
                    font=FONT_LABEL, 
                    padding=[15, 12], 
                    width=int(28 / f), 
                    anchor="center",
                    relief="flat")

    # 4. Botones TTK: Forzamos un aspecto más curvo aumentando el padding interno
    style.configure("TButton", font=FONT_LABEL, padding=[20, 10])
    style.configure("Outline.TButton", font=FONT_LABEL, padding=[20, 10])
    
    return style

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
        "highlightbackground": "#475569",
        "highlightcolor": ACCENT,
        "relief": "flat",
        "justify": "center"
    }

def estilo_boton(color=BG_CARD):
    """Estilo moderno y plano para botones de Tkinter en todo el programa"""
    return {
        "bg": color,
        "fg": "white",
        "font": FONT_LABEL,
        "bd": 0,
        "padx": 30,
        "pady": 5,
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
    
