import tkinter as tk
import os
import sys
import ctypes
import shutil
from datetime import datetime
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import styles as st  # Central de estilos pura en Tkinter

# --- TUS MÓDULOS ORIGINALES ---
import presupuesto_visual
import catalogo_visual
import gestion_clientes
import gestion_proveedores
import gestion_productos
import historial_ventas
import importar_excel
import pedidos_fabrica
import gestion_cuentas_fabrica
import database 
import migracion_actualizar_listas 
import migracion_pedidos 
import migracion_cuentas

class App(tb.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        
        # 1. Cargar Estética (Orden correcto para evitar errores de fuente) [4]
        st.actualizar_fuentes()
        st.configurar_estilos_ttk()
        st.aplicar_estilo_ventana(self)

        self.title("Herrajes Contable - Panel de Gestión")
        self.geometry("1200x800")
        self.configurar_icono_app()
        self.tab_icons = {}

        # 2. Configuración de Comboboxes (Estilo oscuro suave)
        self.option_add('*TCombobox*Listbox.background', st.BG_INPUT)
        self.option_add('*TCombobox*Listbox.foreground', 'white')
        self.option_add('*TCombobox*Listbox.selectBackground', st.ACCENT)
        
        # --- Sistema de Pestañas Principal ---
        self.notebook = tb.Notebook(self, bootstyle="primary")
        self.notebook.pack(pady=(20, 0), padx=0, fill="both", expand=True)
        
        # --- Montar tus solapas originales ---
        self.agregar_pestana(" VENTA", "venta", presupuesto_visual)
        self.agregar_pestana("📚 PRODUCTOS", "productos", gestion_productos)
        self.agregar_pestana("👥 CLIENTES", "clientes", gestion_clientes)
        self.agregar_pestana("📜 HISTORIAL", "historial", historial_ventas)
        self.agregar_pestana("🔍 CATÁLOGO", "catalogo", catalogo_visual)
        self.agregar_pestana("🚚 PROVEEDORES", "proveedores", gestion_proveedores)
        self.agregar_pestana("📦 IMPORTAR", "importar", importar_excel)
        self.agregar_pestana("🏭 PEDIDOS", "pedidos", pedidos_fabrica)
        self.agregar_pestana("💰 CUENTAS FÁBRICA", "cuentas", gestion_cuentas_fabrica)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.crear_menu_superior()

    def configurar_icono_app(self):
        try:
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            ruta_ico = os.path.join(base_dir, "img", "avocado.ico")
            if os.path.exists(ruta_ico):
                img = Image.open(ruta_ico)
                self.icono_ref = ImageTk.PhotoImage(img)
                self.iconphoto(True, self.icono_ref)
        except: pass

    def crear_menu_superior(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        archivo_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="☁️ Archivo & Nube", menu=archivo_menu)
        archivo_menu.add_command(label="⚙️ Configurar Letra", command=self.abrir_configuracion_fuente)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Salir", command=self.quit)

    def abrir_configuracion_fuente(self):
        ventana_cfg = tk.Toplevel(self)
        ventana_cfg.title("Configurar Tamaño de Letra")
        # Eliminamos la geometría fija para que la ventana se adapte al tamaño de los botones
        ventana_cfg.resizable(False, False) 
        st.aplicar_estilo_ventana(ventana_cfg)
        
        tk.Label(ventana_cfg, text="Seleccione el tamaño de letra:", 
                 font=st.FONT_LABEL, bg=st.BG_MAIN, fg="white").pack(pady=20)
        
        def cambiar(nivel):
            factor = st.NIVELES_FUENTE[nivel]
            st.guardar_factor_fuente(factor)
            st.actualizar_fuentes()
            st.configurar_estilos_ttk()
            self.update_idletasks() # Fuerza el redibujado de la interfaz
            ventana_cfg.destroy()

        for nivel in st.NIVELES_FUENTE.keys():
            btn = tb.Button(ventana_cfg, text=nivel, command=lambda n=nivel: cambiar(n), bootstyle="secondary")
            btn.pack(fill="x", padx=50, pady=8)

    def agregar_pestana(self, titulo_completo, icon_name, modulo):
        try:
            frame_contenido = modulo.montar_interfaz(self.notebook)
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "img", f"{icon_name}.png")
            texto_titulo = titulo_completo.split(" ", 1)[-1]

            if os.path.exists(icon_path):
                img = Image.open(icon_path).resize((22, 22), Image.Resampling.LANCZOS)
                image = ImageTk.PhotoImage(img)
                self.tab_icons[icon_name] = image
                self.notebook.add(frame_contenido, text=texto_titulo, image=image, compound=tk.LEFT)
            else:
                self.notebook.add(frame_contenido, text=titulo_completo)
        except Exception as e:
            lbl_error = tk.Label(self.notebook, text=f"Error: {e}", fg="red", bg=st.BG_MAIN)
            self.notebook.add(lbl_error, text=titulo_completo)

    def _on_tab_changed(self, _):
        try:
            tab_actual = self.notebook.tab(self.notebook.select(), "text")
            if "PRODUCTOS" in tab_actual: gestion_productos.cargar_productos()
            elif "CLIENTES" in tab_actual: gestion_clientes.cargar_clientes()
            elif "HISTORIAL" in tab_actual: historial_ventas.cargar_historial()
            elif "PROVEEDORES" in tab_actual: gestion_proveedores.cargar_proveedores()
            elif "PEDIDOS" in tab_actual: pedidos_fabrica.cargar_pedidos_pendientes()
        except: pass

if __name__ == "__main__":
    database.crear_base_datos()
    migracion_actualizar_listas.aplicar_migracion()
    migracion_pedidos.aplicar_migracion()
    migracion_cuentas.aplicar_migracion()
    app = App()
    app.mainloop()