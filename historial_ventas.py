import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import os

def cargar_datos():
    # Limpiamos la tabla antes de recargar
    for row in tabla.get_children():
        tabla.delete(row)
        
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    
    try:
        # Traemos los presupuestos ordenados por el más reciente
        cursor.execute("SELECT id, fecha, cliente_nombre, total FROM presupuestos ORDER BY id DESC")
        ventas = cursor.fetchall()
        
        suma_total = 0
        for v in ventas:
            tabla.insert("", "end", values=(v[0], v[1], v[2], f"$ {v[3]:.2f}"))
            suma_total += v[3]
        
        label_resumen.config(text=f"Ventas Totales Registradas: $ {suma_total:.2f}")
    except sqlite3.OperationalError:
        # Esto ocurre si la tabla 'presupuestos' aún no existe en la base de datos
        label_resumen.config(text="No se encontraron registros de ventas.")
    conexion.close()

def abrir_pdf_seleccionado():
    item_seleccionado = tabla.selection()
    if not item_seleccionado:
        messagebox.showwarning("Atención", "Por favor, selecciona un presupuesto de la lista.")
        return
    
    # Obtenemos el ID del presupuesto de la fila seleccionada
    valores = tabla.item(item_seleccionado)["values"]
    nro_presupuesto = valores[0]
    
    ruta_pdf = f"presupuestos_pdf/Ticket_{nro_presupuesto}.pdf"
    
    if os.path.exists(ruta_pdf):
        os.startfile(ruta_pdf)
    else:
        messagebox.showerror("Error", f"No se encontró el archivo PDF: {ruta_pdf}")

# --- Interfaz ---
ventana = tk.Tk()
ventana.title("Historial de Ventas - HerrajesContable")
ventana.geometry("650x500")
ventana.config(padx=20, pady=20)

tk.Label(ventana, text="HISTORIAL DE PRESUPUESTOS", font=("Arial", 16, "bold")).pack(pady=10)

# Tabla de historial
columnas = ("id", "fecha", "cliente", "total")
tabla = ttk.Treeview(ventana, columns=columnas, show="headings", height=15)
tabla.heading("id", text="Nro")
tabla.heading("fecha", text="Fecha")
tabla.heading("cliente", text="Cliente")
tabla.heading("total", text="Total")

tabla.column("id", width=50, anchor=tk.CENTER)
tabla.column("fecha", width=120, anchor=tk.CENTER)
tabla.column("cliente", width=250)
tabla.column("total", width=100, anchor=tk.E)
tabla.pack(fill=tk.BOTH, expand=True)

label_resumen = tk.Label(ventana, text="Ventas Totales: $ 0.00", font=("Arial", 12, "bold"), fg="darkblue")
label_resumen.pack(pady=15)

# Botones
frame_acciones = tk.Frame(ventana)
frame_acciones.pack(fill=tk.X)

tk.Button(frame_acciones, text="🔄 Actualizar Lista", command=cargar_datos, bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
tk.Button(frame_acciones, text="📄 Re-imprimir / Ver PDF", command=abrir_pdf_seleccionado, bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side=tk.RIGHT, padx=5)

# Cargar datos al iniciar
cargar_datos()

ventana.mainloop()