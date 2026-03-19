import tkinter as tk
from tkinter import ttk
# styles.py

# Paleta de Colores "Minimalist Slate"
BG_MAIN = "#0F172A"      # Fondo profundo
BG_CARD = "#1E293B"      # Gris azulado para contenedores
BG_INPUT = "#333D5A"     # Azul Intenso para inputs (NUEVO)
ACCENT = "#10B981"       # Verde Esmeralda (Éxito/Acción)
TEXT_PRIMARY = "#F8FAFC" # Blanco puro
TEXT_SECONDARY = "#94A3B8"# Gris frío para subtítulos
RED_ERROR = "#EF4444"    # Rojo moderno para borrar

# Tipografías
# Usamos "Segoe UI" que es la fuente nativa moderna de Windows.
FONT_TITLE = ("Segoe UI", 24, "bold")
FONT_LABEL = ("Segoe UI", 11, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_INPUT = ("Segoe UI", 12) # Fuente más grande para inputs

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
        "font": ("Segoe UI", 11, "bold"),
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
                    tabmargins=[10, 10, 30, 0]) # Márgenes más amplios
    
    style.configure("TNotebook.Tab", 
                    background=BG_CARD, 
                    foreground="#94A3B8",
                    padding=[25, 12],       # Pestañas más grandes y cómodas
                    font=("Segoe UI", 11, "bold"),
                    borderwidth=0,
                    focuscolor=BG_MAIN)
    
    style.map("TNotebook.Tab", 
              background=[("selected", ACCENT), ("active", BG_INPUT)], 
              foreground=[("selected", "white"), ("active", "white")])

    # --- TABLAS (Treeview) ---
    # Cabecera
    style.configure("Treeview.Heading", 
                    background=BG_CARD, 
                    foreground="white", 
                    font=("Segoe UI", 10, "bold"), 
                    padding=[10, 10], # Cabecera más alta
                    borderwidth=0)
    
    # Cuerpo de la tabla
    style.configure("Treeview", 
                    background="#1E293B", 
                    foreground="white", 
                    fieldbackground="#1E293B", 
                    borderwidth=0, 
                    rowheight=35, # FILAS MÁS ALTAS (Look moderno)
                    font=("Segoe UI", 10))
    
    style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "white")])

estilo_boton = get_btn_style
configurar_hover = aplicar_hover