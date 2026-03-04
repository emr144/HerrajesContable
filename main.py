import tkinter as tk
from tkinter import ttk
import styles as st  # Importamos tu archivo de estilos

# Importamos los módulos como librerías en lugar de ejecutarlos
import presupuesto_visual
import catalogo_visual
import gestion_clientes
import gestion_proveedores
import gestion_productos
import historial_ventas
import importar_excel

# --- CONFIGURACIÓN DE LA VENTANA PRINCIPAL ---

root = tk.Tk()
root.title("HerrajesContable Pro - Panel de Control")
root.geometry("1200x800") # Aumentamos tamaño para acomodar las pestañas
st.aplicar_estilo_ventana(root) # Aplicamos el fondo oscuro desde styles.py

# --- ESTILO DE LAS PESTAÑAS (NOTEBOOK) ---
style = ttk.Style()
style.theme_use("clam")

# Configuración de colores para que coincida con tu tema oscuro
style.configure("TNotebook", background=st.BG_MAIN, borderwidth=0)
style.configure("TNotebook.Tab", 
                background=st.BG_CARD, 
                foreground="white", 
                padding=[25, 12], # Hacemos las pestañas más anchas y un poco más altas
                font=("Inter", 13, "bold")) # Aumentamos el tamaño de la fuente para agrandar íconos y texto
style.map("TNotebook.Tab", 
          background=[("selected", st.ACCENT)], 
          foreground=[("selected", "white")])

# --- CREACIÓN DEL SISTEMA DE PESTAÑAS ---
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

def agregar_pestana(titulo, modulo):
    """Crea una pestaña e incrusta la interfaz del módulo"""
    try:
        # Llamamos a la función 'montar_interfaz' que crearemos en cada archivo
        frame_contenido = modulo.montar_interfaz(notebook)
        notebook.add(frame_contenido, text=titulo)
    except AttributeError:
        # Por si algún archivo no ha sido actualizado aún
        lbl_error = tk.Label(notebook, text=f"Error cargando {titulo}\n(Falta función montar_interfaz)", fg="red", bg=st.BG_MAIN)
        notebook.add(lbl_error, text=titulo)

# 1. Ventas (Presupuesto)
agregar_pestana("🛒 VENTA / PRESUPUESTO", presupuesto_visual)

# 2. Productos
agregar_pestana("📚 PRODUCTOS", gestion_productos)

# 3. Clientes
agregar_pestana("👥 CLIENTES", gestion_clientes)

# 4. Historial
agregar_pestana("📜 HISTORIAL", historial_ventas)

# 5. Catálogo
agregar_pestana("🔍 CATÁLOGO", catalogo_visual)

# 6. Proveedores
agregar_pestana("🚚 PROVEEDORES", gestion_proveedores)

# 7. Importar Excel
agregar_pestana("📦 IMPORTAR EXCEL", importar_excel)

if __name__ == "__main__":
    root.mainloop()