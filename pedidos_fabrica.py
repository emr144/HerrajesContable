import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
from datetime import datetime
import styles as st 
import database 
import ttkbootstrap as tb

# --- Funciones Auxiliares para Normalización de Búsqueda ---
def _normalize_string_for_sql_search(column_name):
    """Genera un fragmento SQL para normalizar una cadena para búsqueda.
    Elimina espacios, guiones, guiones bajos, barras y acentos comunes en español.
    """
    n = f"LOWER({column_name})"
    for char in [" ", "-", "_", "/", ".", ",", "(", ")", "[", "]", "*", "+", "|", ":", ";"]:
        n = f"REPLACE({n}, '{char}', '')"
    replacements = [
        ('á','a'),('é','e'),('í','i'),('ó','o'),('ú','u'),('ü','u'),('ñ','n'),('ç','c'),
        ('Á','a'),('É','e'),('Í','i'),('Ó','o'),('Ú','u'),('Ü','u'),('Ñ','n'),('Ç','c')
    ]
    for old, new in replacements:
        n = f"REPLACE({n}, '{old}', '{new}')"
    return n

def _normalize_python_string_for_search(text):
    """Normaliza una cadena de Python para comparación, eliminando acentos y caracteres especiales."""
    text = text.lower().replace(' ', '').replace('-', '').replace('_', '').replace('/', '')
    return text.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ü', 'u').replace('ñ', 'n')


# --- Variables Globales ---
frame_lista = None
frame_edicion = None
tabla_pendientes = None
tabla_items_nuevo = None
lista_pedido_actual = []
codigo_seleccionado = ""
producto_id_seleccionado = None
pedido_editando_id = None
combo_prov_gen = None
ent_cant_gen = None
combo_unid_gen = None
lbl_prod_sel_display = None 
var_prov_pedido = None # Variable para almacenar el proveedor seleccionado

ent_buscar_prod = None
lista_sugerencias_prod = None
sugerencias_map_prod = {}

# --- LÓGICA DE DATOS ---

def obtener_proveedores():
    conexion = database.conectar()
    cursor = None
    if not conexion: return []
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre FROM proveedores ORDER BY nombre ASC")
        filas = cursor.fetchall()
        return [f[0] for f in filas]
    except Exception as e:
        print(f"Error al obtener proveedores: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conexion: conexion.close()

def buscar_productos_para_pedido(termino="", proveedor_nombre=None):
    """Busca productos por descripción o código para el autocompletado de pedidos."""
    conexion = database.conectar()
    cursor = None
    if not conexion: return []
    
    try:
        cursor = conexion.cursor()
        tokens = _normalize_python_string_for_search(termino).split()
        if not tokens: return []

        norm_desc = _normalize_string_for_sql_search("p.descripcion")
        norm_cod = _normalize_string_for_sql_search("p.codigo_proveedor")
        
        cond_parts = []
        params = []
        for t in tokens:
            cond_parts.append(f"({norm_desc} LIKE ? OR {norm_cod} LIKE ?)")
            params.extend([f"%{t}%", f"%{t}%"])
        
        query = f"""
            SELECT p.id, p.codigo_proveedor, p.descripcion, pr.nombre, 
                   p.costo_base, p.coeficiente_ganancia, p.iva, pr.descuento_global, pr.incremento_global 
            FROM productos p 
            JOIN proveedores pr ON p.proveedor_id = pr.id 
            WHERE pr.nombre = ? AND {' AND '.join(cond_parts)} 
            ORDER BY p.descripcion
        """
        cursor.execute(query, (proveedor_nombre,) + tuple(params))
        return cursor.fetchall()
    finally:
        if cursor: cursor.close()
        if conexion: conexion.close()

def cargar_pedidos_pendientes(event=None):
    for row in tabla_pendientes.get_children():
        tabla_pendientes.delete(row)
    
    conexion = database.conectar()
    cursor = None
    if conexion:
        try:
            cursor = conexion.cursor()
            # Ajustado para compatibilidad estándar de SQL
            cursor.execute("""
                SELECT pf.id, prov.nombre, pf.fecha_creacion,
                       (SELECT COUNT(*) FROM pedidos_fabrica_detalle WHERE pedido_id = pf.id)
                FROM pedidos_fabrica pf
                JOIN proveedores prov ON pf.proveedor_id = prov.id
                WHERE pf.estado = 'PENDIENTE'
                ORDER BY pf.id DESC
            """)
            for f in cursor.fetchall():
                tabla_pendientes.insert("", "end", values=f + ("✏️", "🗑️"))
        except Exception as e:
            print(f"Error al cargar pedidos: {e}")
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close() # Ensure connection is closed

def agregar_item_a_pedido():
    """Agrega el producto seleccionado al pedido actual."""
    global lista_pedido_actual, producto_id_seleccionado, codigo_seleccionado
    
    if not producto_id_seleccionado:
        messagebox.showwarning("Atención", "Primero seleccione un producto.")
        return

    # Obtenemos descripción de la base de datos solo para visualización
    conexion = database.conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT descripcion FROM productos WHERE id = ?", (producto_id_seleccionado,))
    res_desc = cursor.fetchone()
    conexion.close()
    descripcion = res_desc[0] if res_desc else "Desconocido"

    try:
        cantidad = float(ent_cant_gen.get())
        if cantidad <= 0: raise ValueError
    except ValueError:
        messagebox.showerror("Error", "Cantidad inválida. Debe ser un número positivo.")
        return
    
    unidad = combo_unid_gen.get()

    # Verificar si el producto ya está en la lista y actualizar cantidad
    for item in lista_pedido_actual:
        if item['prod_id'] == producto_id_seleccionado and item['unidad'] == unidad:
            item['cantidad'] += cantidad
            # Actualizar en la tabla visual
            for child in tabla_items_nuevo.get_children():
                values = tabla_items_nuevo.item(child, 'values')
                if values[0] == codigo_seleccionado and values[3] == unidad:
                    tabla_items_nuevo.item(child, values=(item['codigo'], item['descripcion'], item['cantidad'], item['unidad'], "📎", "🗑️"))
                    ent_cant_gen.delete(0, tk.END)
                    ent_cant_gen.insert(0, "1")
                    lbl_prod_sel_display.config(text="")
                    codigo_seleccionado = ""
                    producto_id_seleccionado = None
                    return

    # Si no está, agregarlo como nuevo
    item = {'prod_id': producto_id_seleccionado, 'codigo': codigo_seleccionado, 'descripcion': descripcion, 'cantidad': cantidad, 'unidad': unidad}
    lista_pedido_actual.append(item)
    tabla_items_nuevo.insert("", "end", values=(item['codigo'], item['descripcion'], item['cantidad'], item['unidad'], "📎", "🗑️"))
    
    ent_cant_gen.delete(0, tk.END)
    ent_cant_gen.insert(0, "1")
    lbl_prod_sel_display.config(text="")
    codigo_seleccionado = ""
    producto_id_seleccionado = None

def modificar_item_pedido(item_id):
    """Modifica la cantidad o unidad de un item en el pedido actual."""
    global lista_pedido_actual
    
    idx = tabla_items_nuevo.index(item_id)
    if idx < len(lista_pedido_actual):
        item = lista_pedido_actual[idx]
        
        nueva_cant = simpledialog.askfloat("Modificar Cantidad", f"Producto: {item['descripcion']}\nCantidad actual: {item['cantidad']}\nIngrese nueva cantidad:", initialvalue=item['cantidad'])
        if nueva_cant is not None and nueva_cant > 0:
            item['cantidad'] = nueva_cant
            tabla_items_nuevo.item(item_id, values=(item['codigo'], item['descripcion'], item['cantidad'], item['unidad'], "📎", "🗑️"))
        
        # Podríamos añadir un simpledialog para la unidad también si fuera necesario

def eliminar_item_pedido(item_id):
    """Elimina un item del pedido actual."""
    global lista_pedido_actual
    if messagebox.askyesno("Confirmar", "¿Eliminar este producto del pedido?"):
        idx = tabla_items_nuevo.index(item_id)
        if idx < len(lista_pedido_actual):
            lista_pedido_actual.pop(idx)
            tabla_items_nuevo.delete(item_id)

def guardar_pedido_final():
    """Guarda o actualiza el pedido en la base de datos."""
    global pedido_editando_id, lista_pedido_actual
    if not lista_pedido_actual:
        messagebox.showwarning("Atención", "El pedido está vacío.")
        return
    
    proveedor_nombre = var_prov_pedido.get()
    if not proveedor_nombre:
        messagebox.showwarning("Atención", "Debe seleccionar un proveedor.")
        return

    conexion = database.conectar()
    cursor = conexion.cursor()
    
    cursor.execute("SELECT id FROM proveedores WHERE nombre = ?", (proveedor_nombre,))
    prov_id = cursor.fetchone()[0]

    if pedido_editando_id:
        # Actualizar pedido existente
        cursor.execute("UPDATE pedidos_fabrica SET proveedor_id = ?, fecha_creacion = CURRENT_TIMESTAMP WHERE id = ?", (prov_id, pedido_editando_id))
        cursor.execute("DELETE FROM pedidos_fabrica_detalle WHERE pedido_id = ?", (pedido_editando_id,))
    else:
        # Crear nuevo pedido
        cursor.execute("INSERT INTO pedidos_fabrica (proveedor_id) VALUES (?) RETURNING id", (prov_id,))
        pedido_editando_id = cursor.fetchone()[0]

    for item in lista_pedido_actual:
        cursor.execute("INSERT INTO pedidos_fabrica_detalle (pedido_id, producto_id, cantidad, unidad_medida) VALUES (?, ?, ?, ?)",
                       (pedido_editando_id, item['prod_id'], item['cantidad'], item['unidad']))
    
    conexion.commit()
    conexion.close()
    
    messagebox.showinfo("Éxito", f"Pedido N° {pedido_editando_id} guardado correctamente.")
    volver_a_lista()

def abrir_generador(pedido_id=None, proveedor_fijo=None):
    """Abre el panel de edición. Si es nuevo, recibe el proveedor_fijo."""
    global pedido_editando_id, lista_pedido_actual
    pedido_editando_id = pedido_id
    lista_pedido_actual.clear()
    for row in tabla_items_nuevo.get_children(): tabla_items_nuevo.delete(row)
    
    if pedido_id:
        conexion = database.conectar()
        cursor = None
        if not conexion: return
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT p.nombre, pfd.producto_id, prod.codigo_proveedor, prod.descripcion, pfd.cantidad, pfd.unidad_medida
                FROM pedidos_fabrica pf
                JOIN proveedores p ON pf.proveedor_id = p.id
                JOIN pedidos_fabrica_detalle pfd ON pf.id = pfd.pedido_id
                JOIN productos prod ON pfd.producto_id = prod.id
                WHERE pf.id = ?
            """, (pedido_id,))
            filas = cursor.fetchall()
            if filas:
                var_prov_pedido.set(filas[0][0])
                for f in filas: # f[0] es nombre proveedor, f[1] es prod_id, f[2] es codigo, f[3] es descripcion, f[4] es cantidad, f[5] es unidad
                    item = {'prod_id': f[1], 'codigo': f[2], 'descripcion': f[3], 'cantidad': float(f[4]), 'unidad': f[5]}
                    lista_pedido_actual.append(item)
                    tabla_items_nuevo.insert("", "end", values=(item['codigo'], item['descripcion'], item['cantidad'], item['unidad'], "📎", "🗑️"))
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()
    elif proveedor_fijo:
        var_prov_pedido.set(proveedor_fijo)

    frame_lista.pack_forget()
    frame_edicion.pack(fill=tk.BOTH, expand=True)
    ent_cant_gen.insert(0, "1") # Default quantity

def abrir_buscador_productos_pedido():
    """Buscador avanzado tipo Ventas, filtrado por el proveedor actual."""
    prov_actual = var_prov_pedido.get()
    if not prov_actual: return

    top = tk.Toplevel()
    top.title(f"Buscador de Productos - {prov_actual}")
    
    # 75% de pantalla
    width = int(top.winfo_screenwidth() * 0.75)
    height = int(top.winfo_screenheight() * 0.75)
    x = (top.winfo_screenwidth() // 2) - (width // 2)
    y = (top.winfo_screenheight() // 2) - (height // 2)
    top.geometry(f"{width}x{height}+{x}+{y}")
    st.aplicar_estilo_ventana(top)

    frame_f = tk.Frame(top, bg=st.BG_MAIN, padx=10, pady=10)
    frame_f.pack(fill=tk.X)

    tk.Label(frame_f, text="Código:", bg=st.BG_MAIN, fg="white").grid(row=0, column=0, padx=5)
    e_cod = tk.Entry(frame_f, **st.estilo_entrada())
    e_cod.grid(row=0, column=1, padx=5)
    
    tk.Label(frame_f, text="Producto:", bg=st.BG_MAIN, fg="white").grid(row=0, column=2, padx=5)
    e_desc = tk.Entry(frame_f, **st.estilo_entrada())
    e_desc.grid(row=0, column=3, padx=5, sticky="ew")
    frame_f.columnconfigure(3, weight=1)

    cols = ("cod", "desc", "prov", "precio")
    t_busca = ttk.Treeview(top, columns=cols, show="headings")
    t_busca.heading("cod", text="CÓDIGO"); t_busca.heading("desc", text="DESCRIPCIÓN"); t_busca.heading("prov", text="PROVEEDOR"); t_busca.heading("precio", text="P. PROFESIONAL")
    t_busca.column("cod", width=120); t_busca.column("desc", width=350); t_busca.column("prov", width=150); t_busca.column("precio", width=120, anchor="e")
    t_busca.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def buscar(_=None):
        for row in t_busca.get_children(): t_busca.delete(row)
        # Combinamos los términos de búsqueda si el usuario escribe en ambos campos
        termino = f"{e_cod.get()} {e_desc.get()}".strip()
        res = buscar_productos_para_pedido(termino, prov_actual)
        for r in res: 
            # r: (id, cod, desc, prov, costo, coef, iva, desc_g, inc_g)
            costo, coef, iva, desc_g, inc_g = r[4], r[5], r[6], r[7], r[8]
            precio_prof = costo * (1 - (desc_g or 0)) * (1 + (inc_g or 0)) * coef * (1 + iva)
            t_busca.insert("", "end", iid=r[0], values=(r[1], r[2], r[3], f"$ {precio_prof:.2f}"))

    e_cod.bind("<KeyRelease>", buscar); e_desc.bind("<KeyRelease>", buscar)
    
    def seleccionar():
        global producto_id_seleccionado, codigo_seleccionado
        sel = t_busca.selection()
        if sel:
            val = t_busca.item(sel[0], 'values')
            # En el buscador avanzado, asumimos que el primer valor es el código. 
            # Para ser precisos, obtendremos el ID real desde la base de datos en la función buscar.
            # Modificar la función buscar para que guarde el ID en el Treeview:
            producto_id_seleccionado = sel[0]
            codigo_seleccionado = val[0]
            lbl_prod_sel_display.config(text=f"{val[0]} | {val[1][:50]}...", foreground=st.ACCENT)
            top.destroy()
            ent_cant_gen.focus()

    f_btn = tk.Frame(top, bg=st.BG_MAIN, pady=10)
    f_btn.pack(fill=tk.X)
    tk.Button(f_btn, text="ACEPTAR", command=seleccionar, **st.estilo_boton(st.ACCENT)).pack(side=tk.RIGHT, padx=10)
    
    buscar()

def solicitar_proveedor_nuevo():
    """Ventana emergente para elegir proveedor antes de empezar un pedido nuevo."""
    dialog = tk.Toplevel()
    dialog.title("Nuevo Pedido: Seleccionar Fábrica")
    dialog.geometry("400x250")
    st.aplicar_estilo_ventana(dialog)
    
    tk.Label(dialog, text="¿A qué fábrica desea realizar el pedido?", 
             font=st.FONT_LABEL, bg=st.BG_MAIN, fg="white").pack(pady=20)
    
    lista_provs = obtener_proveedores()
    combo = ttk.Combobox(dialog, values=lista_provs, font=st.FONT_INPUT, state="readonly")
    combo.pack(pady=10, padx=20, fill="x")
    if lista_provs: combo.set(lista_provs[0])

    def confirmar():
        prov = combo.get()
        if prov:
            dialog.destroy()
            abrir_generador(None, prov)

    tk.Button(dialog, text="COMENZAR PEDIDO", command=confirmar, **st.estilo_boton(st.ACCENT)).pack(pady=20)
    dialog.grab_set() # Bloquea interacción con otras ventanas

def eliminar_pedido_seleccionado(pedido_id):
    """Elimina un pedido completo de la base de datos."""
    if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar el Pedido N° {pedido_id}?\nEsta acción es IRREVERSIBLE."):
        conexion = database.conectar()
        cursor = None
        if not conexion: return
        try:
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM pedidos_fabrica_detalle WHERE pedido_id = %s", (pedido_id,))
            cursor.execute("DELETE FROM pedidos_fabrica WHERE id = %s", (pedido_id,))
            conexion.commit()
            messagebox.showinfo("Éxito", f"Pedido N° {pedido_id} eliminado correctamente.")
            cargar_pedidos_pendientes()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el pedido: {e}")
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()

def volver_a_lista():
    frame_edicion.pack_forget()
    frame_lista.pack(fill=tk.BOTH, expand=True)
    cargar_pedidos_pendientes()

def on_tabla_pendientes_click(event):
    """Manejador de clics en la tabla de pedidos pendientes para editar o eliminar."""
    region = tabla_pendientes.identify_region(event.x, event.y)
    if region != "cell": return

    columna_id_str = tabla_pendientes.identify_column(event.x)
    item_id = tabla_pendientes.identify_row(event.y)
    if not item_id: return
        
    # item_id en Treeview es el ID de la DB
    
    if columna_id_str == "#5": # Columna de Editar (edit)
        abrir_generador(item_id)
    elif columna_id_str == "#6": # Columna de Eliminar (del)
        eliminar_pedido_seleccionado(item_id)

def on_tabla_items_nuevo_click(event):
    """Manejador de clics en la tabla de items del nuevo pedido para editar o eliminar."""
    region = tabla_items_nuevo.identify_region(event.x, event.y)
    if region != "cell": return

    columna_id_str = tabla_items_nuevo.identify_column(event.x)
    item_id = tabla_items_nuevo.identify_row(event.y)
    if not item_id: return
    
    if columna_id_str == "#5": # Columna de Modificar (mod)
        modificar_item_pedido(item_id)
    elif columna_id_str == "#6": # Columna de Eliminar (del)
        eliminar_item_pedido(item_id)

def actualizar_sugerencias_prod(event=None):
    """Actualiza la lista de sugerencias de productos."""
    global codigo_seleccionado
    if event.keysym in ('Down', 'Up', 'Return', 'Escape', 'Tab'): return

    texto = ent_buscar_prod.get().strip()
    lista_sugerencias_prod.delete(0, tk.END)
    sugerencias_map_prod.clear()
    
    if len(texto) < 2:
        lista_sugerencias_prod.place_forget()
        return

    proveedor_actual = var_prov_pedido.get()
    if not proveedor_actual: return

    productos = buscar_productos_para_pedido(texto, proveedor_actual)
    if productos:
        for p in productos:
            p_id, cod, desc = p[0], p[1], p[2]
            display_text = f"{cod} - {desc}"
            lista_sugerencias_prod.insert(tk.END, display_text)
            sugerencias_map_prod[display_text] = {'id': p_id, 'codigo': cod, 'descripcion': desc}

        x_root = ent_buscar_prod.winfo_rootx() - frame_edicion.winfo_rootx()
        y_root = ent_buscar_prod.winfo_rooty() - frame_edicion.winfo_rooty()
        
        lista_sugerencias_prod.place(x=x_root, 
                                        y=y_root + ent_buscar_prod.winfo_height(),
                                        width=ent_buscar_prod.winfo_width())
        lista_sugerencias_prod.lift()
    else:
        lista_sugerencias_prod.place_forget()

def seleccionar_producto_para_pedido(event=None):
    """Maneja la selección de un producto de la lista de sugerencias."""
    global producto_id_seleccionado, codigo_seleccionado
    if not lista_sugerencias_prod.curselection(): return
    
    seleccion_texto = lista_sugerencias_prod.get(lista_sugerencias_prod.curselection())
    lista_sugerencias_prod.place_forget()
    
    prod_info = sugerencias_map_prod.get(seleccion_texto)
    if prod_info:
        producto_id_seleccionado = prod_info['id']
        codigo_seleccionado = prod_info['codigo']
        lbl_prod_sel_display.config(text=f"{prod_info['codigo']} | {prod_info['descripcion'][:50]}...")
        ent_buscar_prod.delete(0, tk.END)
        ent_cant_gen.focus()

# --- INTERFAZ ---

def montar_interfaz(parent):
    global frame_lista, frame_edicion, tabla_pendientes, tabla_items_nuevo, lista_sugerencias_prod, var_prov_pedido
    global ent_cant_gen, combo_unid_gen, lbl_prod_sel_display, ent_buscar_prod

    container = tk.Frame(parent, bg=st.BG_MAIN)

    # 1. VISTA DE LISTA
    frame_lista = tk.Frame(container, bg=st.BG_MAIN)
    frame_lista.pack(fill=tk.BOTH, expand=True)

    tk.Button(frame_lista, text="➕ NUEVO PEDIDO", command=solicitar_proveedor_nuevo, **st.estilo_boton(st.ACCENT)).pack(pady=20)
    
    tk.Label(frame_lista, text="PEDIDOS PENDIENTES", font=st.FONT_TITLE, bg=st.BG_MAIN, fg="white").pack()
    
    cols_p = ("id", "prov", "fecha", "items", "edit", "del")
    tabla_pendientes = ttk.Treeview(frame_lista, columns=cols_p, show="headings", height=15)
    for c in cols_p: tabla_pendientes.heading(c, text=c.upper())
    tabla_pendientes.column("id", width=50, anchor="center")
    tabla_pendientes.column("edit", width=50, anchor="center")
    tabla_pendientes.column("del", width=50, anchor="center")
    tabla_pendientes.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # 2. VISTA GENERADOR
    frame_edicion = tk.Frame(container, bg=st.BG_MAIN)
    
    var_prov_pedido = tk.StringVar()

    # La lista de sugerencias debe ser hija de 'frame_edicion' para poder flotar sobre todo
    lista_sugerencias_prod = tk.Listbox(frame_edicion, font=st.FONT_NORMAL, height=12, bg=st.BG_CARD, fg="white", selectbackground=st.ACCENT, bd=0)
    lista_sugerencias_prod.bind('<<ListboxSelect>>', seleccionar_producto_para_pedido)

    f_top_gen = tk.Frame(frame_edicion, bg=st.BG_CARD, pady=10)
    f_top_gen.pack(fill=tk.X, padx=15, pady=10)

    # Proveedor estático (Label)
    lbl_prov_estatico = tk.Label(f_top_gen, textvariable=var_prov_pedido, bg=st.BG_CARD, fg="white", font=("Segoe UI", 12, "bold"))
    lbl_prov_estatico.grid(row=0, column=0, columnspan=2, padx=15)

    # Botón de Búsqueda Avanzada (Estilo Ventas)
    tb.Button(f_top_gen, text="🔍 BUSCAR AVANZADO", command=abrir_buscador_productos_pedido, bootstyle="info-outline").grid(row=0, column=2, padx=5)

    # Buscador de productos
    tk.Label(f_top_gen, text="CÓDIGO/DESC:", bg=st.BG_CARD, fg="white", font=st.FONT_LABEL).grid(row=0, column=3, padx=5)
    ent_buscar_prod = tk.Entry(f_top_gen, width=20, **st.estilo_entrada())
    ent_buscar_prod.grid(row=0, column=4, padx=5)
    ent_buscar_prod.bind('<KeyRelease>', actualizar_sugerencias_prod)
    ent_buscar_prod.bind('<Return>', seleccionar_producto_para_pedido)

    lbl_prod_sel_display = tk.Label(f_top_gen, text="", bg=st.BG_CARD, fg=st.ACCENT, font=st.FONT_NORMAL)
    lbl_prod_sel_display.grid(row=0, column=5, padx=10)

    tk.Label(f_top_gen, text="CANT:", bg=st.BG_CARD, fg="white", font=st.FONT_LABEL).grid(row=0, column=6, padx=5)
    ent_cant_gen = tk.Entry(f_top_gen, width=5, **st.estilo_entrada())
    ent_cant_gen.grid(row=0, column=7, padx=5)
    ent_cant_gen.bind("<Return>", lambda e: agregar_item_a_pedido())

    tk.Label(f_top_gen, text="UNIDAD:", bg=st.BG_CARD, fg="white", font=st.FONT_LABEL).grid(row=0, column=8, padx=5)
    combo_unid_gen = ttk.Combobox(f_top_gen, values=["Unidad", "Docena", "Caja"], width=8, font=st.FONT_INPUT)
    combo_unid_gen.set("Unidad")
    combo_unid_gen.grid(row=0, column=9, padx=5)

    tb.Button(f_top_gen, text="➕", command=agregar_item_a_pedido, bootstyle="success").grid(row=0, column=10, padx=5)

    cols_n = ("cod", "desc", "cant", "unid", "mod", "del")
    tabla_items_nuevo = ttk.Treeview(frame_edicion, columns=cols_n, show="headings")
    for c in cols_n: tabla_items_nuevo.heading(c, text=c.upper())
    tabla_items_nuevo.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    f_bot_gen = tk.Frame(frame_edicion, bg=st.BG_MAIN)
    tabla_items_nuevo.bind("<Button-1>", on_tabla_items_nuevo_click)
    f_bot_gen.pack(fill=tk.X, pady=20)
    
    tk.Button(f_bot_gen, text="❌ VOLVER", command=volver_a_lista, **st.estilo_boton(st.BG_CARD)).pack(side=tk.RIGHT, padx=10)
    # BOTÓN GUARDAR CORREGIDO PARA LLAMAR A LA LÓGICA
    tk.Button(f_bot_gen, text="💾 GUARDAR", command=guardar_pedido_final, **st.estilo_boton(st.ACCENT)).pack(side=tk.RIGHT, padx=10)

    cargar_pedidos_pendientes()
    tabla_pendientes.bind("<Button-1>", on_tabla_pendientes_click)
    return container