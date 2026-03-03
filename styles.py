# styles.py

# Paleta de Colores "Minimalist Slate"
BG_MAIN = "#0F172A"      # Fondo profundo
BG_CARD = "#1E293B"      # Gris azulado para contenedores
ACCENT = "#10B981"       # Verde Esmeralda (Éxito/Acción)
TEXT_PRIMARY = "#F8FAFC" # Blanco puro
TEXT_SECONDARY = "#94A3B8"# Gris frío para subtítulos
RED_ERROR = "#EF4444"    # Rojo moderno para borrar

# Tipografías
FONT_TITLE = ("Inter", 26, "bold")
FONT_LABEL = ("Inter", 13, "bold")
FONT_NORMAL = ("Inter", 12)

# Estilo de Botones (Diccionario de configuración)
def get_btn_style(color=BG_CARD):
    return {
        "bg": color,
        "fg": TEXT_PRIMARY,
        "font": ("Inter", 12, "bold"),
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

estilo_boton = get_btn_style
configurar_hover = aplicar_hover