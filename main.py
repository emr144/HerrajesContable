import tkinter as tk
from tkinter import messagebox
import subprocess # Esto nos permite abrir tus otros archivos
import sys

def abrir_presupuesto():
    # Abrimos el generador de presupuestos
    subprocess.Popen([sys.executable, 'presupuesto_visual.py'])

def abrir_catalogo():
    # Abrimos el visor con fotos
    subprocess.Popen([sys.executable, 'catalogo_visual.py'])

def abrir_importador():
    # Abrimos el importador de Excel
    respuesta = messagebox.askyesno("Confirmar", "¿Deseas importar la lista de precios desde Excel?")
    if respuesta:
        subprocess.run([sys.executable, 'importar_excel.py'])
        messagebox.showinfo("Listo", "Proceso de importación finalizado.")

# --- Configuración de la Ventana Principal ---
root = tk.Tk()
root.title("HerrajesContable v1.0 - Panel de Control")
root.geometry("500x400")
root.configure(bg="#f0f0f0")

# Título Bienvenida
tk.Label(root, text="HERRAJES CONTABLE", font=("Helvetica", 24, "bold"), bg="#f0f0f0", fg="#333").pack(pady=30)
tk.Label(root, text="Seleccione una operación:", font=("Helvetica", 12), bg="#f0f0f0", fg="#666").pack(pady=5)

# Contenedor de Botones
frame_botones = tk.Frame(root, bg="#f0f0f0")
frame_botones.pack(pady=20)

# Estilo de los botones
estilo_btn = {"font": ("Arial", 12, "bold"), "width": 25, "height": 2, "cursor": "hand2"}

btn1 = tk.Button(frame_botones, text="🛒 NUEVO PRESUPUESTO", bg="#4CAF50", fg="white", 
                 command=abrir_presupuesto, **estilo_btn)
btn1.pack(pady=10)

btn2 = tk.Button(frame_botones, text="🔍 VER CATÁLOGO FOTOGRÁFICO", bg="#2196F3", fg="white", 
                 command=abrir_catalogo, **estilo_btn)
btn2.pack(pady=10)

btn3 = tk.Button(frame_botones, text="📦 ACTUALIZAR DESDE EXCEL", bg="#FF9800", fg="white", 
                 command=abrir_importador, **estilo_btn)
btn3.pack(pady=10)

# Pie de página
tk.Label(root, text="Sistema de Gestión Interna", font=("Arial", 9, "italic"), bg="#f0f0f0", fg="#999").pack(side=tk.BOTTOM, pady=10)

root.mainloop()