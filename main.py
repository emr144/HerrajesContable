import tkinter as tk
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

        # --- Estilos Globales para Pestañas ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=st.BG_MAIN, borderwidth=0)
        style.configure("TNotebook.Tab", 
                        background=st.BG_CARD, 
                        foreground="white", 
                        padding=[20, 10], 
                        font=("Inter", 11, "bold"))
        style.map("TNotebook.Tab", 
                  background=[("selected", st.ACCENT)], 
                  foreground=[("selected", "white")])
        
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
        self.agregar_pestana("🛒 VENTA", presupuesto_visual)
        self.agregar_pestana("📚 PRODUCTOS", gestion_productos)
        self.agregar_pestana("👥 CLIENTES", gestion_clientes)
        self.agregar_pestana("📜 HISTORIAL", historial_ventas)
        self.agregar_pestana("🔍 CATÁLOGO", catalogo_visual)
        self.agregar_pestana("🚚 PROVEEDORES", gestion_proveedores)
        self.agregar_pestana("📦 IMPORTAR", importar_excel)
        self.agregar_pestana("🏭 PEDIDOS", pedidos_fabrica)
        self.agregar_pestana("💰 CUENTAS FÁBRICA", gestion_cuentas_fabrica)

        # Bind para refrescar datos al cambiar de pestaña
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def agregar_pestana(self, titulo, modulo):
        try:
            frame_contenido = modulo.montar_interfaz(self.notebook)
            self.notebook.add(frame_contenido, text=titulo)
        except Exception as e:
            lbl_error = tk.Label(self.notebook, text=f"Error cargando {titulo}\n{e}", fg="red", bg=st.BG_MAIN)
            self.notebook.add(lbl_error, text=titulo)

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
    # --- Inicialización y Migraciones ---
    database.crear_base_datos()
    migracion_actualizar_listas.aplicar_migracion()
    migracion_pedidos.aplicar_migracion()
    migracion_cuentas.aplicar_migracion()

    app = App()
    app.mainloop()