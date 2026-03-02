import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

def cargar_clientes():
    for row in tabla.get_children():
        tabla.delete(row)
    
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM clientes ORDER BY nombre ASC")
    for c in cursor.fetchall():
        tabla.insert("", "end", values=c)
    conexion.close()

def guardar_cliente():
    nombre = ent_nombre.get().strip()
    tel = ent_tel.get().strip()
    if not nombre:
        messagebox.showwarning("Error", "El nombre es obligatorio")
        return

    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO clientes (nombre, telefono, direccion) VALUES (?, ?, ?)", 
                   (nombre, tel, ent_dir.get()))
    conexion.commit()
    conexion.close()
    
    messagebox.showinfo("Éxito", "Cliente guardado")
    limpiar_campos()
    cargar_clientes()

def limpiar_campos():
    ent_nombre.delete(0, tk.END)
    ent_tel.delete(0, tk.END)
    ent_dir.delete(0, tk.END)

# --- Interfaz ---
ventana = tk.Tk()
ventana.title("Agenda de Clientes - HerrajesContable")
ventana.geometry("600x500")

# Formulario
frame_form = tk.LabelFrame(ventana, text=" Nuevo Cliente ", padx=10, pady=10)
frame_form.pack(fill="x", padx=10, pady=10)

tk.Label(frame_form, text="Nombre:").grid(row=0, column=0)
ent_nombre = tk.Entry(frame_form, width=30)
ent_nombre.grid(row=0, column=1, padx=5)

tk.Label(frame_form, text="Teléfono:").grid(row=0, column=2)
ent_tel = tk.Entry(frame_form, width=15)
ent_tel.grid(row=0, column=3, padx=5)

tk.Label(frame_form, text="Dirección:").grid(row=1, column=0, pady=5)
ent_dir = tk.Entry(frame_form, width=30)
ent_dir.grid(row=1, column=1, padx=5)

tk.Button(frame_form, text="💾 Guardar", command=guardar_cliente, bg="#4CAF50", fg="white").grid(row=1, column=3)

# Tabla
columnas = ("id", "nombre", "tel", "dir", "email", "cuit")
tabla = ttk.Treeview(ventana, columns=columnas, show="headings")
tabla.heading("nombre", text="Nombre")
tabla.heading("tel", text="Teléfono")
tabla.heading("dir", text="Dirección")
tabla.column("id", width=0, stretch=tk.NO) # Ocultamos el ID
tabla.pack(fill="both", expand=True, padx=10, pady=10)

cargar_clientes()
ventana.mainloop()