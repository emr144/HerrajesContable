import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

def abrir_presupuesto():
    # Abre el generador de tickets para la impresora de 80mm
    subprocess.Popen([sys.executable, 'presupuesto_visual.py'])

def abrir_catalogo():
    # Abre el visor de productos con fotos
    subprocess.Popen([sys.executable, 'catalogo_visual.py'])

def abrir_historial():
    # Abre el explorador de presupuestos viejos y re-impresión
    subprocess.Popen([sys.executable, 'historial_ventas.py'])
    
def abrir_clientes():
    subprocess.Popen([sys.executable, 'gestion_clientes.py'])

# En la zona de botones del main:
btn5 = tk.Button(frame_botones, text="👥 AGENDA DE CLIENTES", bg="#607D8B", fg="white", 
                 command=abrir_clientes, **estilo_btn)
btn5.pack(pady=10)

def abrir_importador():
    # Ejecuta el script de carga masiva desde Excel
    respuesta = messagebox.askyesno("Confirmar", "¿Deseas importar la lista de precios desde 'lista_precios.xlsx'?")
    if respuesta:
        try:
            # Usamos run para esperar a que termine antes de mostrar el mensaje de éxito
            subprocess.run([sys.executable, 'importar_excel.py'], check=True)
            messagebox.showinfo("Listo", "Proceso de importación finalizado con éxito.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar el Excel: {e}")

# --- Configuración de la Ventana Principal ---
root = tk.Tk()
root.title("HerrajesContable v1.0 - Panel de Control")
root.geometry("500x550") # Aumentamos un poco el alto para el nuevo botón
root.configure(bg="#f0f0f0")

# Título Bienvenida
tk.Label(root, text="HERRAJES CONTABLE", font=("Helvetica", 24, "bold"), bg="#f0f0f0", fg="#333").pack(pady=30)
tk.Label(root, text="Seleccione una operación:", font=("Helvetica", 12), bg="#f0f0f0", fg="#666").pack(pady=5)

# Contenedor de Botones
frame_botones = tk.Frame(root, bg="#f0f0f0")
frame_botones.pack(pady=10)

# Estilo común para los botones
estilo_btn = {"font": ("Arial", 12, "bold"), "width": 30, "height": 2, "cursor": "hand2"}

# --- BOTONES PRINCIPALES ---

# 1. Ventas
btn_presupuesto = tk.Button(frame_botones, text="🛒 NUEVO PRESUPUESTO (TICKET)", bg="#4CAF50", fg="white", 
                            command=abrir_presupuesto, **estilo_btn)
btn_presupuesto.pack(pady=10)

# 2. Catálogo
btn_catalogo = tk.Button(frame_botones, text="🔍 VER CATÁLOGO FOTOGRÁFICO", bg="#2196F3", fg="white", 
                         command=abrir_catalogo, **estilo_btn)
btn_catalogo.pack(pady=10)

# 3. Historial
btn_historial = tk.Button(frame_botones, text="📊 HISTORIAL DE VENTAS", bg="#9C27B0", fg="white", 
                          command=abrir_historial, **estilo_btn)
btn_historial.pack(pady=10)

# 4. Inventario
btn_importar = tk.Button(frame_botones, text="📦 ACTUALIZAR DESDE EXCEL", bg="#FF9800", fg="white", 
                         command=abrir_importador, **estilo_btn)
btn_importar.pack(pady=10)

# --- Pie de página ---
tk.Label(root, text="Sistema de Gestión Interna - v1.0", font=("Arial", 9, "italic"), bg="#f0f0f0", fg="#999").pack(side=tk.BOTTOM, pady=15)

# Ejecutar la aplicación
if __name__ == "__main__":
    root.mainloop()