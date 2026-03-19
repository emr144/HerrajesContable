import tkinter as tk
import os
import sys
import ctypes
import shutil
from datetime import datetime
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from tkinter import ttk
import styles as st  
import migracion_actualizar_listas 
import migracion_pedidos 
import migracion_cuentas

# --- IMPORTACIÓN DE MÓDULOS ---
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

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        st.aplicar_estilo_ventana(self)
        self.title("Herrajes Contable - Panel de Gestión")
        self.geometry("1200x800")
        
        # --- Configuración del Ícono (Avocado) ---
        # Intenta cargar el icono .ico o .png de la carpeta img
        try:
            # Rutina robusta para encontrar la ruta (funciona en dev y en exe instalado)
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            ruta_icono = os.path.join(base_path, "img", "avocado.ico")
            if os.path.exists(ruta_icono):
                self.iconbitmap(ruta_icono)
            # Si tuvieras un .png en lugar de .ico, usarías: tk.PhotoImage(file="img/avocado.png")
        except Exception: pass

        # --- Estilos Globales para Pestañas ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=st.BG_MAIN, borderwidth=0)
        style.configure("TNotebook.Tab", 
                        background=st.BG_CARD, 
                        foreground="white",
                        padding=[15, 8], # Padding ajustado para íconos
                        font=("Inter", 11, "bold"))
        style.map("TNotebook.Tab", 
                  background=[("selected", st.ACCENT)], 
                  foreground=[("selected", "white")])
        
        # Diccionario para mantener una referencia a los íconos y evitar que el recolector de basura los borre
        self.tab_icons = {}

        # --- Estilos Globales para Inputs y Comboboxes ---
        # Configuración para que los desplegables sean azules y grandes
        self.option_add('*TCombobox*Listbox.background', st.BG_INPUT)
        self.option_add('*TCombobox*Listbox.foreground', 'white')
        self.option_add('*TCombobox*Listbox.selectBackground', st.ACCENT)
        self.option_add('*TCombobox*Listbox.font', st.FONT_INPUT)
        
        style.configure("TCombobox", fieldbackground=st.BG_INPUT, background=st.BG_MAIN, 
                        foreground='white', arrowcolor='white', borderwidth=0)
        style.map("TCombobox", fieldbackground=[('readonly', st.BG_INPUT)])
        
        # --- Sistema de Pestañas ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)
        
        # --- Carga de Módulos ---
        self.agregar_pestana(" VENTA", "venta", presupuesto_visual)
        self.agregar_pestana("📚 PRODUCTOS", "productos", gestion_productos)
        self.agregar_pestana("👥 CLIENTES", "clientes", gestion_clientes)
        self.agregar_pestana("📜 HISTORIAL", "historial", historial_ventas)
        self.agregar_pestana("🔍 CATÁLOGO", "catalogo", catalogo_visual)
        self.agregar_pestana("🚚 PROVEEDORES", "proveedores", gestion_proveedores)
        self.agregar_pestana("📦 IMPORTAR", "importar", importar_excel)
        self.agregar_pestana("🏭 PEDIDOS", "pedidos", pedidos_fabrica)
        self.agregar_pestana("💰 CUENTAS FÁBRICA", "cuentas", gestion_cuentas_fabrica)

        # Bind para refrescar datos al cambiar de pestaña
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        # --- Menú Superior (NUEVO) ---
        self.crear_menu_superior()

    def crear_menu_superior(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        archivo_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="☁️ Archivo & Nube", menu=archivo_menu)
        archivo_menu.add_command(label="💾 Crear Copia de Seguridad", command=self.hacer_backup)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Salir", command=self.quit)

    def hacer_backup(self):
        """Genera una copia timestamped de la base de datos actual (sea local o nube)"""
        try:
            db_origen = database.get_db_path()
            fecha = datetime.now().strftime("%Y-%m-%d_%H-%M")
            nombre_backup = f"herrajes_backup_{fecha}.db"
            
            # Preguntamos dónde guardar, por defecto en el escritorio o documentos
            destino = filedialog.asksaveasfilename(
                defaultextension=".db",
                initialfile=nombre_backup,
                title="Guardar Copia de Seguridad"
            )
            
            if destino:
                shutil.copy2(db_origen, destino)
                messagebox.showinfo("Backup Exitoso", f"Se guardó la copia en:\n{destino}")
        except Exception as e:
            messagebox.showerror("Error de Backup", f"No se pudo crear el respaldo:\n{e}")

    def agregar_pestana(self, titulo_completo, icon_name, modulo):
        try:
            frame_contenido = modulo.montar_interfaz(self.notebook)

            # Rutina para encontrar la ruta de las imágenes (funciona en dev y en exe)
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(base_path, "img", f"{icon_name}.png")

            image = None
            texto_titulo = titulo_completo.split(" ", 1)[-1]

            if os.path.exists(icon_path):
                # Si la imagen existe, la cargamos y la usamos
                img = Image.open(icon_path).resize((22, 22), Image.Resampling.LANCZOS)
                image = ImageTk.PhotoImage(img)
                self.tab_icons[icon_name] = image
                self.notebook.add(frame_contenido, text=texto_titulo, image=image, compound=tk.LEFT)
            else:
                # Si no, usamos el texto original con el emoji (que se verá blanco)
                self.notebook.add(frame_contenido, text=titulo_completo)

        except Exception as e:
            # En caso de error, mostramos un mensaje en la pestaña
            lbl_error = tk.Label(self.notebook, text=f"Error cargando {titulo_completo}\n{e}", fg="red", bg=st.BG_MAIN)
            self.notebook.add(lbl_error, text=titulo_completo)

    def _on_tab_changed(self, _):
        try:
            tab_actual_texto = self.notebook.tab(self.notebook.select(), "text")
            if "PRODUCTOS" in tab_actual_texto:
                gestion_productos.cargar_productos()
            elif "CLIENTES" in tab_actual_texto:
                gestion_clientes.cargar_clientes()
            elif "HISTORIAL" in tab_actual_texto:
                historial_ventas.cargar_historial()
            elif "PROVEEDORES" in tab_actual_texto:
                gestion_proveedores.cargar_proveedores()
            elif "PEDIDOS" in tab_actual_texto:
                pedidos_fabrica.cargar_pedidos_pendientes()
        except: pass

if __name__ == "__main__":
    # --- Configuración para Windows (Forzar ícono en la barra de tareas) ---
    try:
        # Definimos un ID único para la aplicación
        myappid = 'herrajes.contable.gestion.v1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    # --- Inicialización y Migraciones ---
    database.crear_base_datos()
    migracion_actualizar_listas.aplicar_migracion()
    migracion_pedidos.aplicar_migracion()
    migracion_cuentas.aplicar_migracion()

    app = App()
    app.mainloop()