import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import styles as st  # Importamos tu archivo de estilos

# Variable global para controlar edición
cliente_seleccionado_id = None

def cargar_clientes(filtro=""):
    for row in tabla.get_children():
        tabla.delete(row)
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    
    if filtro:
        query = "SELECT * FROM clientes WHERE nombre LIKE ? OR email LIKE ? OR cuit_dni LIKE ? ORDER BY nombre ASC"
        param = f"%{filtro}%"
        cursor.execute(query, (param, param, param))
    else:
        cursor.execute("SELECT * FROM clientes ORDER BY nombre ASC")
        
    registros = cursor.fetchall()
    for cliente in registros:
        # Añadimos el icono de basura al final de los valores de cada cliente
        valores_con_accion = cliente + ('🗑️',)
        tabla.insert("", "end", values=valores_con_accion)
    label_contador.config(text=f"Total Clientes: {len(registros)}")
    conexion.close()

def limpiar_formulario(deseleccionar=False):
    global cliente_seleccionado_id
    cliente_seleccionado_id = None
    ent_nombre.delete(0, tk.END)
    ent_tel.delete(0, tk.END)
    ent_dir.delete(0, tk.END)
    ent_email.delete(0, tk.END)
    ent_cuit.delete(0, tk.END)
    btn_guardar.config(text="➕ GUARDAR NUEVO CLIENTE")
    if deseleccionar and tabla.selection():
        tabla.selection_remove(tabla.selection())

def guardar_cliente():
    global cliente_seleccionado_id
    nombre = ent_nombre.get().strip()
    if not nombre:
        messagebox.showwarning("Atención", "El nombre es obligatorio")
        return
    
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    
    if cliente_seleccionado_id:
        # UPDATE
        cursor.execute("""
            UPDATE clientes SET nombre=?, telefono=?, direccion=?, email=?, cuit_dni=? WHERE id=?
        """, (nombre, ent_tel.get(), ent_dir.get(), ent_email.get(), ent_cuit.get(), cliente_seleccionado_id))
        mensaje = "Cliente actualizado correctamente"
    else:
        # INSERT
        cursor.execute("""
            INSERT INTO clientes (nombre, telefono, direccion, email, cuit_dni) VALUES (?, ?, ?, ?, ?)
        """, (nombre, ent_tel.get(), ent_dir.get(), ent_email.get(), ent_cuit.get()))
        mensaje = "Cliente guardado correctamente"
        
    conexion.commit()
    conexion.close()
    messagebox.showinfo("Éxito", mensaje)
    limpiar_formulario()
    cargar_clientes()

def cargar_datos_edicion():
    global cliente_seleccionado_id
    seleccion = tabla.selection()
    if not seleccion:
        messagebox.showwarning("Atención", "Seleccione un cliente de la lista para modificar.")
        return
    
    item = tabla.item(seleccion)
    valores = item['values']
    
    limpiar_formulario()
    cliente_seleccionado_id = valores[0]
    
    ent_nombre.insert(0, valores[1])
    ent_tel.insert(0, str(valores[2]))
    ent_dir.insert(0, str(valores[3]))
    ent_email.insert(0, str(valores[4]))
    ent_cuit.insert(0, str(valores[5]))
    
    btn_guardar.config(text="💾 GUARDAR CAMBIOS")

def eliminar_cliente_por_id(cliente_id, nombre):
    """Elimina un cliente específico usando su ID y recarga la tabla."""
    if messagebox.askyesno("Confirmar", f"¿Eliminar a '{nombre}'?"):
        conexion = sqlite3.connect('herrajes.db')
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
        conexion.commit()
        conexion.close()
        cargar_clientes(ent_buscar.get()) # Recargamos usando el filtro actual
        limpiar_formulario(deseleccionar=True) # Limpiamos el form por si estaba seleccionado

def on_tabla_click(event):
    """Manejador de clics en la tabla para detectar el clic en el icono de borrar."""
    if tabla.identify_region(event.x, event.y) == "cell" and tabla.identify_column(event.x) == "#7": # Columna de acción
        item_id = tabla.identify_row(event.y)
        valores = tabla.item(item_id, 'values')
        eliminar_cliente_por_id(valores[0], valores[1])

# --- INTERFAZ SOBRIA ---
ventana = tk.Tk()
ventana.title("Agenda de Clientes Pro")
ventana.geometry("700x650")
st.aplicar_estilo_ventana(ventana) # Fondo oscuro

# Título
tk.Label(ventana, text="GESTIÓN DE CLIENTES", font=st.FONT_TITLE, 
         bg=st.BG_MAIN, fg=st.TEXT_PRIMARY).pack(pady=30)

# Contador de clientes
label_contador = tk.Label(ventana, text="Total Clientes: 0", font=st.FONT_LABEL, bg=st.BG_MAIN, fg=st.ACCENT)
label_contador.pack()

# Formulario (Tarjeta)
frame_form = tk.Frame(ventana, bg=st.BG_CARD, padx=20, pady=20)
frame_form.pack(padx=40, fill=tk.X)

def crear_campo(label, fila):
    tk.Label(frame_form, text=label, font=st.FONT_LABEL, bg=st.BG_CARD, fg=st.TEXT_SECONDARY).grid(row=fila, column=0, sticky="w", pady=5)
    entry = tk.Entry(frame_form, font=st.FONT_NORMAL, bg=st.BG_MAIN, fg="white", bd=0, insertbackground="white")
    entry.grid(row=fila, column=1, sticky="ew", padx=10, pady=5)
    return entry

frame_form.columnconfigure(1, weight=1)
ent_nombre = crear_campo("Nombre:", 0)
ent_tel = crear_campo("Teléfono:", 1)
ent_dir = crear_campo("Dirección:", 2)
ent_email = crear_campo("Email:", 3)
ent_cuit = crear_campo("CUIT/DNI:", 4)

# Botones Formulario (Guardar y Limpiar)
frame_btn_form = tk.Frame(ventana, bg=st.BG_MAIN)
frame_btn_form.pack(pady=20, padx=40, fill=tk.X)

btn_guardar = tk.Button(frame_btn_form, text="➕ GUARDAR NUEVO CLIENTE", command=guardar_cliente, **st.estilo_boton())
btn_guardar.pack(fill=tk.X, expand=True)
st.configurar_hover(btn_guardar)

# Buscador
frame_buscar = tk.Frame(ventana, bg=st.BG_MAIN)
frame_buscar.pack(fill=tk.X, padx=40, pady=(10, 0))
tk.Label(frame_buscar, text="🔍 Buscar Cliente:", font=st.FONT_LABEL, bg=st.BG_MAIN, fg="white").pack(side=tk.LEFT)
ent_buscar = tk.Entry(frame_buscar, font=st.FONT_NORMAL, bg=st.BG_CARD, fg="white", bd=0, insertbackground="white")
ent_buscar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
ent_buscar.bind("<KeyRelease>", lambda e: cargar_clientes(ent_buscar.get()))

# Tabla de Clientes
style_tabla = ttk.Style()
style_tabla.theme_use("clam")
# Configuramos la fuente para las filas y la cabecera
style_tabla.configure("Treeview", background=st.BG_CARD, foreground="white", fieldbackground=st.BG_CARD, borderwidth=0, rowheight=30, font=st.FONT_NORMAL)
style_tabla.map("Treeview", background=[('selected', st.ACCENT)])
style_tabla.configure("Treeview.Heading", font=st.FONT_LABEL)

columnas = ("id", "nombre", "tel", "dir", "email", "cuit", "accion")
tabla = ttk.Treeview(ventana, columns=columnas, show="headings")
for col in columnas: 
    tabla.heading(col, text=col.upper())
    tabla.column(col, width=100)

# Ajustamos el ancho de la columna de acción
tabla.column("accion", width=80, anchor="center")

tabla.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

# Botones de Acción (Modificar / Eliminar)
frame_acciones = tk.Frame(ventana, bg=st.BG_MAIN)
frame_acciones.pack(fill=tk.X, padx=40, pady=10)

btn_modificar = tk.Button(frame_acciones, text="✏️ MODIFICAR SELECCIONADO", command=cargar_datos_edicion, **st.estilo_boton(st.ACCENT))
btn_modificar.pack(fill=tk.X, expand=True)
st.configurar_hover(btn_modificar, st.ACCENT, st.BG_CARD)

tabla.bind("<ButtonRelease-1>", on_tabla_click)
cargar_clientes()
ventana.mainloop()