import tkinter as tk
from tkinter import ttk, messagebox
import styles as st
import database # Importamos para obtener la ruta

# Variable global para controlar edición
proveedor_seleccionado_id = None

def cargar_proveedores(filtro=""):
    """Carga los proveedores en la tabla, aplicando un filtro si se provee."""
    for row in tabla.get_children():
        tabla.delete(row)
    conexion = database.conectar()
    cursor = conexion.cursor()
    # Consultamos proveedores y verificamos si tienen productos (lista cargada)
    query_base = """
        SELECT id, nombre, contacto, fecha_modif_coeficiente,
        (SELECT COUNT(*) FROM productos WHERE proveedor_id = proveedores.id) as tiene_lista
        FROM proveedores
    """
    
    if filtro:
        query = f"SELECT * FROM ({query_base}) AS sub WHERE nombre ILIKE %s OR contacto ILIKE %s ORDER BY nombre ASC"
        param = f"{filtro}%"
        cursor.execute(query, (param, param))
    else:
        query = f"{query_base} ORDER BY nombre ASC"
        cursor.execute(query)
        
    registros = cursor.fetchall()
    for proveedor in registros:
        fecha_modif_coef = proveedor[3] if proveedor[3] else "---"
        check_lista = "✅" if proveedor[4] > 0 else ""
        valores_display = (proveedor[0], proveedor[1], proveedor[2], fecha_modif_coef, check_lista)
        # Añadimos los iconos de acción al final
        valores_con_accion = valores_display + ('✏️', '🗑️')
        # Usamos el ID de la DB como el ID del item en la tabla (más robusto)
        tabla.insert("", "end", values=valores_con_accion, iid=proveedor[0])

    label_contador.config(text=f"Total Proveedores: {len(registros)}")
    conexion.close()

def limpiar_formulario(deseleccionar=False):
    """Limpia los campos del formulario y resetea el estado de edición."""
    global proveedor_seleccionado_id
    proveedor_seleccionado_id = None
    ent_nombre.delete(0, tk.END)
    ent_contacto.delete(0, tk.END)
    btn_guardar.config(text="➕ GUARDAR NUEVO PROVEEDOR")
    if deseleccionar and tabla.selection():
        tabla.selection_remove(tabla.selection())

def guardar_proveedor():
    """Guarda un proveedor nuevo o actualiza uno existente."""
    global proveedor_seleccionado_id
    nombre = ent_nombre.get().strip()
    if not nombre:
        messagebox.showwarning("Atención", "El nombre es obligatorio.")
        return

    contacto = ent_contacto.get().strip()

    conexion = database.conectar()
    cursor = conexion.cursor()
    
    if proveedor_seleccionado_id:
        cursor.execute("UPDATE proveedores SET nombre=%s, contacto=%s WHERE id=%s", 
                       (nombre, contacto, proveedor_seleccionado_id))
        mensaje = "Proveedor actualizado correctamente."
    else:
        cursor.execute("INSERT INTO proveedores (nombre, contacto) VALUES (%s, %s)", 
                       (nombre, contacto))
        mensaje = "Proveedor guardado correctamente."
        
    conexion.commit()
    conexion.close()
    messagebox.showinfo("Éxito", mensaje)
    limpiar_formulario()
    cargar_proveedores(ent_buscar.get())

def cargar_datos_para_editar(item_id):
    """Carga los datos de un proveedor en el formulario para su edición."""
    global proveedor_seleccionado_id
    
    conexion = database.conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, contacto FROM proveedores WHERE id=%s", (item_id,))
    valores = cursor.fetchone()
    conexion.close()

    if not valores: return

    limpiar_formulario()
    proveedor_seleccionado_id = valores[0]
    
    ent_nombre.insert(0, valores[1])
    ent_contacto.insert(0, str(valores[2] or ''))
    
    btn_guardar.config(text="💾 GUARDAR CAMBIOS")

def eliminar_proveedor_por_id(proveedor_id, nombre):
    """Elimina un proveedor, con control de integridad referencial."""
    msg = (f"¿Eliminar al proveedor '{nombre}'?\n\n"
           "ADVERTENCIA: Esta acción no se puede deshacer.")
    if messagebox.askyesno("Confirmar Eliminación", msg):
        try:
            conexion = database.conectar()
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM proveedores WHERE id = %s", (proveedor_id,))
            conexion.commit()
            conexion.close()
            cargar_proveedores(ent_buscar.get())
            limpiar_formulario(deseleccionar=True)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el proveedor.\n\nEs probable que tenga productos asociados. Debe eliminarlos o reasignarlos primero.\n\nDetalle: {e}")

def on_tabla_click(event):
    """Manejador de clics en la tabla para disparar acciones de editar o eliminar."""
    try:
        region = tabla.identify_region(event.x, event.y)
        if region != "cell":
            return

        columna_id = tabla.identify_column(event.x)
        item_id = tabla.identify_row(event.y)
        if not item_id:
            return
            
        # Con la remoción de columnas, los índices visuales cambian.
        # Editar ahora es #6 y Eliminar #7
        if columna_id == "#6":
            cargar_datos_para_editar(item_id)
        elif columna_id == "#7":
            valores = tabla.item(item_id, 'values')
            eliminar_proveedor_por_id(item_id, valores[1])
    except Exception as e:
        messagebox.showerror("Error", f"Error al procesar acción: {e}")

# --- INTERFAZ GRÁFICA ---
def montar_interfaz(parent):
    global ent_nombre, ent_contacto, btn_guardar, ent_buscar, tabla, label_contador
    
    ventana = tk.Frame(parent, bg=st.BG_MAIN)

    tk.Label(ventana, text="GESTIÓN DE PROVEEDORES", font=st.FONT_TITLE, bg=st.BG_MAIN, fg=st.TEXT_PRIMARY).pack(pady=30)

    label_contador = tk.Label(ventana, text="Total Proveedores: 0", font=st.FONT_LABEL, bg=st.BG_MAIN, fg=st.ACCENT)
    label_contador.pack()

    frame_form = tk.Frame(ventana, bg=st.BG_CARD, padx=20, pady=20); frame_form.pack(padx=40, fill=tk.X)

    def crear_campo(label, fila):
        tk.Label(frame_form, text=label, font=st.FONT_LABEL, bg=st.BG_CARD, fg=st.TEXT_SECONDARY).grid(row=fila, column=0, sticky="w", pady=5)
        entry = tk.Entry(frame_form, **st.estilo_entrada())
        entry.grid(row=fila, column=1, sticky="ew", padx=10, pady=5)
        return entry

    frame_form.columnconfigure(1, weight=1)
    ent_nombre = crear_campo("Nombre:", 0)
    ent_contacto = crear_campo("Contacto (Tel/Email):", 1)

    frame_btn_form = tk.Frame(ventana, bg=st.BG_MAIN); frame_btn_form.pack(pady=20, padx=40, fill=tk.X)
    btn_guardar = tk.Button(frame_btn_form, text="➕ GUARDAR NUEVO PROVEEDOR", command=guardar_proveedor, **st.estilo_boton()); btn_guardar.pack(fill=tk.X, expand=True)

    frame_buscar = tk.Frame(ventana, bg=st.BG_MAIN); frame_buscar.pack(fill=tk.X, padx=40, pady=(10, 0))
    tk.Label(frame_buscar, text="🔍 Buscar Proveedor:", font=st.FONT_LABEL, bg=st.BG_MAIN, fg="white").pack(side=tk.LEFT)
    ent_buscar = tk.Entry(frame_buscar, **st.estilo_entrada()); ent_buscar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
    ent_buscar.bind("<KeyRelease>", lambda e: cargar_proveedores(ent_buscar.get()))

    columnas = ("id", "nombre", "contacto", "ult_modif_coef", "lista", "editar", "eliminar")
    tabla = ttk.Treeview(ventana, columns=columnas, show="headings"); tabla.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)
    tabla.heading("id", text="ID"); tabla.heading("nombre", text="NOMBRE"); tabla.heading("contacto", text="CONTACTO"); tabla.heading("ult_modif_coef", text="MODIF. COEF."); tabla.heading("lista", text="LISTA"); tabla.heading("editar", text="EDITAR"); tabla.heading("eliminar", text="ELIMINAR")

    tabla.column("id", width=50, anchor="center")
    tabla.column("nombre", width=200)
    tabla.column("contacto", width=200)
    tabla.column("ult_modif_coef", width=120, anchor="center")
    tabla.column("lista", width=60, anchor="center")
    tabla.column("editar", width=80, anchor="center")
    tabla.column("eliminar", width=80, anchor="center")

    tabla.bind("<Button-1>", on_tabla_click)
    cargar_proveedores()
    
    return ventana

if __name__ == '__main__':
    root = tk.Tk()
    st.aplicar_estilo_ventana(root)
    app = montar_interfaz(root)
    app.pack(fill="both", expand=True)
    root.mainloop()