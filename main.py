import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os
import styles as st  # Importamos tu archivo de estilos

# --- FUNCIONES DE NAVEGACIÓN ---

def abrir_presupuesto():
    ejecutar_archivo('presupuesto_visual.py')

def abrir_catalogo():
    ejecutar_archivo('catalogo_visual.py')

def abrir_historial():
    ejecutar_archivo('historial_ventas.py')
    
def abrir_clientes():
    ejecutar_archivo('gestion_clientes.py')

def ejecutar_archivo(nombre_archivo):
    """Función auxiliar para abrir archivos con manejo de errores"""
    if os.path.exists(nombre_archivo):
        subprocess.Popen([sys.executable, nombre_archivo])
    else:
        messagebox.showerror("Error", f"No se encontró el archivo: {nombre_archivo}")

def abrir_importador():
    mensaje = ("¿Deseas actualizar la base de datos desde 'lista_precios.xlsx'?\n\n"
               "Este proceso hará lo siguiente:\n"
               "1. Agregará los productos nuevos del Excel.\n"
               "2. Actualizará los precios de los productos existentes.\n"
               "3. Marcará como 'inactivos' los productos que ya no estén en el Excel (sin borrarlos del historial).")
    respuesta = messagebox.askyesno("Confirmar Actualización de Productos", mensaje)
    if respuesta:
        try:
            proceso = subprocess.run([sys.executable, 'importar_excel.py'], check=True, capture_output=True, text=True, encoding='utf-8')
            messagebox.showinfo("Proceso Finalizado", f"Se completó la actualización:\n\n{proceso.stdout}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error de Importación", f"Ocurrió un error durante la ejecución del script:\n\n{e.stderr}")

# --- CONFIGURACIÓN DE LA VENTANA PRINCIPAL ---

root = tk.Tk()
root.title("HerrajesContable Pro - Panel de Control")
root.geometry("600x750")
st.aplicar_estilo_ventana(root) # Aplicamos el fondo oscuro desde styles.py

# Encabezado
tk.Label(
    root, text="HERRAJES CONTABLE", 
    font=st.FONT_TITLE, bg=st.BG_MAIN, fg=st.TEXT_PRIMARY
).pack(pady=(50, 5))

tk.Label(
    root, text="Gestión Operativa Profesional", 
    font=("Inter", 10), bg=st.BG_MAIN, fg=st.TEXT_SECONDARY
).pack(pady=(0, 30))

# Contenedor de Botones (La "Tarjeta" central)
frame_botones = tk.Frame(root, bg=st.BG_CARD, padx=40, pady=40)
frame_botones.pack(pady=10, padx=50, fill=tk.BOTH, expand=True)

# --- CREACIÓN DE BOTONES USANDO EL ESTILO DE STYLES.PY ---

def crear_boton_menu(texto, comando):
    # Creamos el botón usando el diccionario **st.estilo_boton()
    btn = tk.Button(frame_botones, text=texto, command=comando, **st.estilo_boton())
    btn.pack(pady=12, fill=tk.X)
    # Aplicamos el efecto de pasar el mouse
    st.configurar_hover(btn)
    return btn

# 1. Ventas
crear_boton_menu("🛒  NUEVO PRESUPUESTO", abrir_presupuesto)

# 2. Catálogo
crear_boton_menu("🔍  CATÁLOGO FOTOGRÁFICO", abrir_catalogo)

# 3. Clientes
crear_boton_menu("👥  AGENDA DE CLIENTES", abrir_clientes)

# 4. Historial
crear_boton_menu("📊  HISTORIAL DE VENTAS", abrir_historial)

# 5. Inventario
crear_boton_menu("📦  ACTUALIZAR DESDE EXCEL", abrir_importador)

# --- Pie de página ---
tk.Label(
    root, text="v2.5 Professional Edition", 
    font=("Inter", 9), bg=st.BG_MAIN, fg=st.TEXT_SECONDARY
).pack(side=tk.BOTTOM, pady=20)

if __name__ == "__main__":
    root.mainloop()