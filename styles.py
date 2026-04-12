import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import os
# styles.py

# Paleta de Colores "Minimalist Slate" (Restaurada)
BG_MAIN = "#0F172A"      # Fondo profundo
BG_CARD = "#1E293B"      # Gris azulado para contenedores
BG_INPUT = "#333D5A"     # Azul Intenso para inputs
ACCENT = "#10B981"       # Verde Esmeralda (Éxito/Acción)
TEXT_PRIMARY = "#F8FAFC" # Blanco puro
TEXT_SECONDARY = "#94A3B8"# Gris frío para subtítulos
RED_ERROR = "#EF4444"    # Rojo moderno para borrar

# Medidas predefinidas tipo Word
NIVELES_FUENTE = {
    "Normal (100%)": 1.0,
    "Grande (120%)": 1.2,
    "Extra (140%)": 1.4,
    "Muy Grande (170%)": 1.7,
    "Gigante (200%)": 2.0,
    "Ultra (230%)": 2.3
}

# Tipografías
def cargar_factor_fuente():
    """Lee el factor de escala de la fuente desde un archivo local."""
    try:
        if os.path.exists("font_config.txt"):
            with open("font_config.txt", "r") as f:
                return float(f.read().strip())
    except: pass
    return 1.0 # Valor por defecto: Normal

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
            FONT_TITLE = tkfont.Font(family="Segoe UI", size=int(15 * f), weight="bold")
            FONT_LABEL = tkfont.Font(family="Segoe UI", size=int(9 * f), weight="bold")
            FONT_NORMAL = tkfont.Font(family="Segoe UI", size=int(9 * f))
            FONT_INPUT = tkfont.Font(family="Segoe UI", size=int(9 * f))
        else:
            FONT_TITLE.configure(size=int(15 * f))
            FONT_LABEL.configure(size=int(9 * f))
            FONT_NORMAL.configure(size=int(9 * f))
            FONT_INPUT.configure(size=int(9 * f))
    except:
        # Fallback por si se llama antes de que exista el root de TK
        FONT_TITLE = ("Segoe UI", int(15 * f), "bold")
        FONT_LABEL = ("Segoe UI", int(9 * f), "bold")
        FONT_NORMAL = ("Segoe UI", int(9 * f))
        FONT_INPUT = ("Segoe UI", int(9 * f))

actualizar_fuentes()

# Estilo para Entradas de Texto (Inputs)
def estilo_entrada():
    return {
        "bg": BG_INPUT,
        "fg": TEXT_PRIMARY,
        "font": FONT_INPUT,
        "bd": 0,
        "insertbackground": "white", # Color del cursor
        "relief": "flat",
        "highlightthickness": 1,
        "highlightbackground": "#4B5563", # Borde sutil (Gray 600)
        "highlightcolor": ACCENT          # Resalte Esmeralda al escribir
    }

# Estilo de Botones (Diccionario de configuración)
def get_btn_style(color=BG_CARD):
    return {
        "bg": color,
        "fg": TEXT_PRIMARY,
        "font": FONT_LABEL,
        "bd": 0,
        "padx": int(9 * FONT_SIZE_FACTOR),  # Reducido para un aspecto más compacto
        "pady": int(3 * FONT_SIZE_FACTOR),  # Reducido para un aspecto más compacto
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
                    tabmargins=[2, 2, 2, 0]) 
    
    # Padding dinámico para pestañas
    pad_x = int(10 * FONT_SIZE_FACTOR)
    pad_y = int(3 * FONT_SIZE_FACTOR)
    style.configure("TNotebook.Tab", 
                    background=BG_CARD, 
                    foreground=TEXT_SECONDARY,
                    padding=[pad_x, pad_y],       
                    font=FONT_LABEL,
                    borderwidth=0,
                    focuscolor=ACCENT)
    
    style.map("TNotebook.Tab", 
              background=[("selected", ACCENT), ("active", BG_INPUT)], 
              foreground=[("selected", "white"), ("active", "white")])

    # --- TABLAS (Treeview) ---
    # Cabecera
    h_pad = int(4 * FONT_SIZE_FACTOR)
    style.configure("Treeview.Heading", 
                    background=BG_CARD, 
                    foreground="white", 
                    font=FONT_LABEL, 
                    padding=[h_pad, h_pad], 
                    borderwidth=0)
    
    # Cuerpo de la tabla
    # Calculamos altura de fila: Fuente (10*factor) + espacio extra proporcional
    altura_fila = int(24 * FONT_SIZE_FACTOR)
    style.configure("Treeview", 
                    background=BG_CARD,
                    foreground=TEXT_PRIMARY,
                    fieldbackground=BG_CARD,
                    borderwidth=0, 
                    rowheight=altura_fila, 
                    font=FONT_NORMAL)
    
    style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", TEXT_PRIMARY)])

estilo_boton = get_btn_style
configurar_hover = aplicar_hover