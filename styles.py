import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import os
# styles.py

# Paleta de Colores "Minimalist Slate"
BG_MAIN = "#0F172A"      # Fondo profundo
BG_CARD = "#1E293B"      # Gris azulado para contenedores
BG_INPUT = "#333D5A"     # Azul Intenso para inputs
ACCENT = "#10B981"       # Verde Esmeralda (Éxito/Acción)
TEXT_PRIMARY = "#F8FAFC" # Blanco puro
TEXT_SECONDARY = "#94A3B8"# Gris frío para subtítulos
RED_ERROR = "#EF4444"    # Rojo moderno para borrar

# Medidas predefinidas tipo Word
NIVELES_FUENTE = {
    "Pequeño (80%)": 0.8,
    "Normal (100%)": 1.0,
    "Grande (120%)": 1.2,
    "Muy Grande (150%)": 1.5,
    "Gigante (200%)": 2.0,
    "Ultra Gigante (240%)": 2.4
}

# Tipografías
def cargar_factor_fuente():
    """Lee el factor de escala de la fuente desde un archivo local."""
    try:
        if os.path.exists("font_config.txt"):
            with open("font_config.txt", "r") as f:
                return float(f.read().strip())
    except: pass
    return 1.5 # Valor por defecto: Muy Grande (150%)

def guardar_factor_fuente(factor):
    """Guarda el factor de escala de la fuente para persistencia."""
    with open("font_config.txt", "w") as f:
        f.write(str(factor))

FONT_SIZE_FACTOR = cargar_factor_fuente()

# Inicializamos las variables de fuente como None
FONT_TITLE = None
FONT_LABEL = None
FONT_NORMAL = None
FONT_INPUT = None

def actualizar_fuentes():
    """Crea o actualiza los objetos de fuente para permitir cambios en tiempo real."""
    global FONT_TITLE, FONT_LABEL, FONT_NORMAL, FONT_INPUT
    f = FONT_SIZE_FACTOR
    
    try:
        # Si las fuentes no existen, las creamos. Si existen, las configuramos.
        # Esto hace que todos los widgets que las usan se actualicen SOLOS.
        if FONT_TITLE is None:
            FONT_TITLE = tkfont.Font(family="Segoe UI", size=int(24 * f), weight="bold")
            FONT_LABEL = tkfont.Font(family="Segoe UI", size=int(11 * f), weight="bold")
            FONT_NORMAL = tkfont.Font(family="Segoe UI", size=int(10 * f))
            FONT_INPUT = tkfont.Font(family="Segoe UI", size=int(12 * f))
        else:
            FONT_TITLE.configure(size=int(24 * f))
            FONT_LABEL.configure(size=int(11 * f))
            FONT_NORMAL.configure(size=int(10 * f))
            FONT_INPUT.configure(size=int(12 * f))
    except:
        # Fallback por si se llama antes de que exista el root de TK
        FONT_TITLE = ("Segoe UI", int(24 * f), "bold")
        FONT_LABEL = ("Segoe UI", int(11 * f), "bold")
        FONT_NORMAL = ("Segoe UI", int(10 * f))
        FONT_INPUT = ("Segoe UI", int(12 * f))

actualizar_fuentes()

# Estilo para Entradas de Texto (Inputs)
def estilo_entrada():
    return {
        "bg": BG_INPUT,
        "fg": "white",
        "font": FONT_INPUT,
        "bd": 0,
        "insertbackground": "white", # Color del cursor
        "relief": "flat", # Plano, sin bordes 3D antiguos
        "highlightthickness": 1,
        "highlightbackground": "#3B82F6", # Borde azul claro
        "highlightcolor": "#60A5FA"       # Borde al hacer click
    }

# Estilo de Botones (Diccionario de configuración)
def get_btn_style(color=BG_CARD):
    return {
        "bg": color,
        "fg": TEXT_PRIMARY,
        "font": FONT_LABEL,
        "bd": 0,
        "height": 2,
        "cursor": "hand2",
        "activebackground": ACCENT,
        "activeforeground": "white"
    }

# Función para aplicar el efecto Hover (pasar el mouse)
def aplicar_hover(widget, color_entrar=ACCENT, color_salir=BG_CARD):
    widget.bind("<Enter>", lambda e: widget.config(bg=color_entrar))
    widget.bind("<Leave>", lambda e: widget.config(bg=color_salir))

# --- AGREGADOS PARA COMPATIBILIDAD ---
def aplicar_estilo_ventana(ventana):
    ventana.configure(bg=BG_MAIN)

def configurar_estilos_ttk():
    """Configura globalmente los widgets TTK para un look moderno y plano."""
    style = ttk.Style()
    style.theme_use("clam") # 'Clam' permite más personalización de colores
    
    # --- PESTAÑAS (Notebook) ---
    style.configure("TNotebook", 
                    background=BG_MAIN, 
                    borderwidth=0, 
                    tabmargins=[5, 5, 5, 0]) 
    
    style.configure("TNotebook.Tab", 
                    background=BG_CARD, 
                    foreground="#94A3B8",
                    padding=[15, 5],       
                    font=FONT_LABEL,
                    borderwidth=0,
                    focuscolor=ACCENT)
    
    style.map("TNotebook.Tab", 
              background=[("selected", ACCENT), ("active", BG_INPUT)], 
              foreground=[("selected", "white"), ("active", "white")])

    # --- TABLAS (Treeview) ---
    # Cabecera
    style.configure("Treeview.Heading", 
                    background=BG_CARD, 
                    foreground="white", 
                    font=FONT_LABEL, 
                    padding=[10, 10], 
                    borderwidth=0)
    
    # Cuerpo de la tabla
    style.configure("Treeview", 
                    background="#1E293B", 
                    foreground="white", 
                    fieldbackground="#1E293B", 
                    borderwidth=0, 
                    rowheight=30, 
                    font=FONT_NORMAL)
    
    style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "white")])

estilo_boton = get_btn_style
configurar_hover = aplicar_hover