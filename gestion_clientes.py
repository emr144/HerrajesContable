import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import styles as st  # Importamos tu archivo de estilos
import database # Importamos para obtener la ruta

# Variable global para controlar edición
cliente_seleccionado_id = None

def cargar_clientes(filtro=""):
    for row in tabla.get_children():
        tabla.delete(row)
    conexion = sqlite3.connect(database.get_db_path())
    cursor = conexion.cursor()
    
    # Seleccionamos explícitamente las columnas para evitar problemas si la tabla cambia
    query_base = "SELECT id, nombre, telefono, email, cuit_dni FROM clientes"
    
    if filtro:
        query = f"{query_base} WHERE nombre LIKE ? OR email LIKE ? OR cuit_dni LIKE ? ORDER BY nombre ASC"
        param = f"%{filtro}%"
        cursor.execute(query, (param, param, param))
    else:
        query = f"{query_base} ORDER BY nombre ASC"
        cursor.execute(query)
        
    registros = cursor.fetchall()
    for cliente in registros:
        # Añadimos los iconos de acción al final de los valores de cada cliente
        valores_con_accion = cliente + ('✏️', '🗑️')
        tabla.insert("", "end", values=valores_con_accion)
    label_contador.config(text=f"Total Clientes: {len(registros)}")
    conexion.close()

def limpiar_formulario(deseleccionar=False):
    global cliente_seleccionado_id
    cliente_seleccionado_id = None
    ent_nombre.delete(0, tk.END)
    ent_tel.delete(0, tk.END)
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
    
    conexion = sqlite3.connect(database.get_db_path())
    cursor = conexion.cursor()
    
    if cliente_seleccionado_id:
        # UPDATE
        cursor.execute("""
            UPDATE clientes SET nombre=?, telefono=?, email=?, cuit_dni=? WHERE id=?
        """, (nombre, ent_tel.get(), ent_email.get(), ent_cuit.get(), cliente_seleccionado_id))
        mensaje = "Cliente actualizado correctamente"
    else:
        # INSERT
        cursor.execute("""
            INSERT INTO clientes (nombre, telefono, email, cuit_dni) VALUES (?, ?, ?, ?)
        """, (nombre, ent_tel.get(), ent_email.get(), ent_cuit.get()))
        mensaje = "Cliente guardado correctamente"
        
    conexion.commit()
    conexion.close()
    messagebox.showinfo("Éxito", mensaje)
    limpiar_formulario()
    cargar_clientes()

def cargar_datos_para_editar(valores):
    """Carga los datos de una fila en el formulario para su edición."""
    global cliente_seleccionado_id
    
    limpiar_formulario()
    # El ID está en la primera posición de los valores de la fila
    cliente_seleccionado_id = valores[0]
    
    ent_nombre.insert(0, valores[1])
    ent_tel.insert(0, str(valores[2]))
    # La dirección ya no existe, los índices se corren
    ent_email.insert(0, str(valores[3]))
    ent_cuit.insert(0, str(valores[4]))
    
    btn_guardar.config(text="💾 GUARDAR CAMBIOS")

def eliminar_cliente_por_id(cliente_id, nombre):
    """Elimina un cliente específico usando su ID y recarga la tabla."""
    if messagebox.askyesno("Confirmar", f"¿Eliminar a '{nombre}'?"):
        conexion = sqlite3.connect(database.get_db_path())
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
        conexion.commit()
        conexion.close()
        cargar_clientes(ent_buscar.get()) # Recargamos usando el filtro actual
        limpiar_formulario(deseleccionar=True) # Limpiamos el form por si estaba seleccionado

def on_tabla_click(event):
    """Manejador de clics en la tabla para editar o eliminar."""
    region = tabla.identify_region(event.x, event.y)
    if region != "cell":
        return

    columna_id = tabla.identify_column(event.x)
    item_id = tabla.identify_row(event.y)
    if not item_id:
        return
        
    valores = tabla.item(item_id, 'values')
    
    if columna_id == "#6": # Columna de Editar
        cargar_datos_para_editar(valores)
    elif columna_id == "#7": # Columna de Eliminar
        eliminar_cliente_por_id(valores[0], valores[1])

# --- INTERFAZ SOBRIA ---
def montar_interfaz(parent):
    global ent_nombre, ent_tel, ent_email, ent_cuit, btn_guardar, ent_buscar, tabla, label_contador
    
    ventana = tk.Frame(parent, bg=st.BG_MAIN)

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
        entry = tk.Entry(frame_form, **st.estilo_entrada())
        entry.grid(row=fila, column=1, sticky="ew", padx=10, pady=5)
        return entry

    frame_form.columnconfigure(1, weight=1)
    ent_nombre = crear_campo("Nombre:", 0)
    ent_tel = crear_campo("Teléfono:", 1)
    ent_email = crear_campo("Email:", 2)
    ent_cuit = crear_campo("CUIT/DNI:", 3)

    # Botones Formulario (Guardar y Limpiar)
    frame_btn_form = tk.Frame(ventana, bg=st.BG_MAIN)
    frame_btn_form.pack(pady=20, padx=40, fill=tk.X)

    btn_guardar = tk.Button(frame_btn_form, text="➕ GUARDAR NUEVO CLIENTE", command=guardar_cliente, **st.estilo_boton())
    btn_guardar.pack(fill=tk.X, expand=True)

    # Buscador
    frame_buscar = tk.Frame(ventana, bg=st.BG_MAIN)
    frame_buscar.pack(fill=tk.X, padx=40, pady=(10, 0))
    tk.Label(frame_buscar, text="🔍 Buscar Cliente:", font=st.FONT_LABEL, bg=st.BG_MAIN, fg="white").pack(side=tk.LEFT)
    ent_buscar = tk.Entry(frame_buscar, **st.estilo_entrada())
    ent_buscar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
    ent_buscar.bind("<KeyRelease>", lambda e: cargar_clientes(ent_buscar.get()))

    columnas = ("id", "nombre", "tel", "email", "cuit", "editar", "eliminar")
    tabla = ttk.Treeview(ventana, columns=columnas, show="headings")
    for col in columnas: 
        tabla.heading(col, text=col.upper())
        tabla.column(col, width=100)

    # Ajustamos el ancho de las columnas de acción
    tabla.column("id", width=60, anchor="center")
    tabla.column("editar", width=80, anchor="center")
    tabla.column("eliminar", width=80, anchor="center")

    tabla.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

    # Usamos <Button-1> para que la acción sea inmediata al hacer clic
    tabla.bind("<Button-1>", on_tabla_click)
    cargar_clientes()
    
    return ventana

if __name__ == '__main__':
    root = tk.Tk()
    st.aplicar_estilo_ventana(root)
    app = montar_interfaz(root)
    app.pack(fill="both", expand=True)
    root.mainloop()