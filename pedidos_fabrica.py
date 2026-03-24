import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import os
from fpdf import FPDF
import styles as st
import database # Importamos para obtener la ruta

# --- Variables Globales ---
ventana_principal = None
frame_lista, frame_edicion = None, None
tabla_pedidos, tabla_temporal = None, None
combo_proveedores, combo_producto, ent_cantidad, combo_unidad_medida = None, None, None, None
label_titulo_edicion = None
btn_imprimir_pdf = None
btn_borrar_pedido = None 

proveedor_map = {}
productos_proveedor_lista = []
pedido_temporal = []
pedido_id_actual = None

# --- Lógica de Base de Datos ---

def cargar_pedidos_pendientes():
    if not tabla_pedidos: return
    for row in tabla_pedidos.get_children():
        tabla_pedidos.delete(row)
    try:
        conexion = sqlite3.connect(database.get_db_path())
        cursor = conexion.cursor()
        query = """
            SELECT pf.id, prov.nombre, strftime('%d-%m-%Y', pf.fecha_creacion),
                   COUNT(pfd.id), SUM(pfd.cantidad)
            FROM pedidos_fabrica pf
            JOIN proveedores prov ON pf.proveedor_id = prov.id
            JOIN pedidos_fabrica_detalle pfd ON pf.id = pfd.pedido_id
            WHERE pf.estado = 'PENDIENTE'
            GROUP BY pf.id, prov.nombre, pf.fecha_creacion
            ORDER BY pf.id DESC
        """
        cursor.execute(query)
        for reg in cursor.fetchall():
            # reg contiene: (id, nombre_prov, fecha, count_items, sum_cantidad)
            tabla_pedidos.insert("", "end", values=reg + ("✏️", "🗑️"), iid=reg[0])
        conexion.close()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron cargar los pedidos: {e}")

def guardar_cambios():
    global pedido_id_actual
    if not pedido_temporal:
        messagebox.showwarning("Aviso", "El pedido está vacío.")
        return
    
    nombre_prov = combo_proveedores.get()
    prov_id = proveedor_map.get(nombre_prov)
    
    if not prov_id:
        messagebox.showerror("Error", "Seleccione un proveedor válido.")
        return

    try:
        conn = sqlite3.connect(database.get_db_path())
        cursor = conn.cursor()
        
        if pedido_id_actual:
            cursor.execute("DELETE FROM pedidos_fabrica_detalle WHERE pedido_id = ?", (pedido_id_actual,))
            id_p = pedido_id_actual
        else:
            cursor.execute("INSERT INTO pedidos_fabrica (proveedor_id, estado) VALUES (?, 'PENDIENTE')", (prov_id,))
            id_p = cursor.lastrowid
        
        detalles = [(id_p, i['id'], i['cant'], i['unidad']) for i in pedido_temporal]
        cursor.executemany("INSERT INTO pedidos_fabrica_detalle (pedido_id, producto_id, cantidad, unidad_medida) VALUES (?, ?, ?, ?)", detalles)
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Éxito", "Pedido guardado correctamente.")
        mostrar_vista_lista()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar: {e}")

# --- Funciones de Eliminación ---

def eliminar_producto_temporal():
    """Elimina una fila de la tabla de edición antes de guardar"""
    seleccion = tabla_temporal.selection()
    if not seleccion:
        messagebox.showwarning("Aviso", "Seleccione un producto de la tabla para quitarlo.")
        return
    
    indice = tabla_temporal.index(seleccion[0])
    del pedido_temporal[indice]
    actualizar_tabla_temporal()

def eliminar_pedido_completo():
    """Borra el pedido actual de la base de datos"""
    global pedido_id_actual
    if not pedido_id_actual:
        return

    confirmar = messagebox.askyesno("Confirmar", f"¿Desea ELIMINAR permanentemente el pedido N° {pedido_id_actual}?")
    if confirmar:
        try:
            conn = sqlite3.connect(database.get_db_path())
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pedidos_fabrica_detalle WHERE pedido_id = ?", (pedido_id_actual,))
            cursor.execute("DELETE FROM pedidos_fabrica WHERE id = ?", (pedido_id_actual,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Eliminado", "El pedido ha sido borrado.")
            mostrar_vista_lista()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar: {e}")

def eliminar_pedido_desde_lista(pedido_id):
    """Borra un pedido desde la vista de lista (botón tachito)"""
    confirmar = messagebox.askyesno("Confirmar", f"¿Desea ELIMINAR permanentemente el pedido N° {pedido_id}?")
    if confirmar:
        try:
            conn = sqlite3.connect(database.get_db_path())
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pedidos_fabrica_detalle WHERE pedido_id = ?", (pedido_id,))
            cursor.execute("DELETE FROM pedidos_fabrica WHERE id = ?", (pedido_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Eliminado", "El pedido ha sido borrado.")
            cargar_pedidos_pendientes() 
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar: {e}")

# --- Generación de PDF (58mm) ---

def generar_pdf_pedido():
    if not pedido_id_actual: 
        messagebox.showwarning("Aviso", "Guarda el pedido antes de imprimir.")
        return
        
    proveedor_nombre = combo_proveedores.get()

    try:
        if not os.path.exists("pedidos_pdf"):
            os.makedirs("pedidos_pdf")
        
        altura = 80 + (len(pedido_temporal) * 10)
        filename = f"pedidos_pdf/Pedido_{pedido_id_actual}_{proveedor_nombre.replace(' ', '_')}.pdf"
        
        pdf = FPDF(orientation='P', unit='mm', format=(58, altura))
        pdf.set_margins(2, 2, 2)
        pdf.add_page()

        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, "ORDEN DE PEDIDO", ln=True, align="C")
        pdf.set_font("Arial", "B", 8)
        pdf.cell(0, 5, f"Nro: {pedido_id_actual}", ln=True, align="C")
        pdf.ln(2)
        
        pdf.set_font("Arial", size=7)
        pdf.multi_cell(0, 4, f"Proveedor:\n{proveedor_nombre}", align="L")
        pdf.ln(2)
        
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("Arial", "B", 6)
        pdf.cell(10, 5, "Cod", 1, 0, 'C', 1)
        pdf.cell(22, 5, "Desc", 1, 0, 'C', 1)
        pdf.cell(8, 5, "Cant", 1, 0, 'C', 1)
        pdf.cell(14, 5, "Unid", 1, 1, 'C', 1)

        pdf.set_font("Arial", size=6)
        for item_detalle in pedido_temporal:
            desc_fmt = (item_detalle['desc'][:12] + '..') if len(item_detalle['desc']) > 14 else item_detalle['desc']
            pdf.cell(10, 5, str(item_detalle['cod']), 1)
            pdf.cell(22, 5, desc_fmt, 1)
            pdf.cell(8, 5, str(item_detalle['cant']), 1, 0, 'C')
            pdf.cell(14, 5, str(item_detalle['unidad']), 1, 1, 'C')

        pdf.output(filename)
        os.startfile(os.path.abspath(filename))

    except Exception as e:
        messagebox.showerror("Error PDF", f"No se pudo generar el archivo: {e}")

# --- Interfaz de Usuario ---

def cargar_proveedores():
    global proveedor_map
    conn = sqlite3.connect(database.get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM proveedores ORDER BY nombre")
    proveedor_map = {nombre: pid for pid, nombre in cursor.fetchall()}
    conn.close()
    combo_proveedores.config(values=list(proveedor_map.keys()))

def cargar_productos_proveedor(event=None):
    global productos_proveedor_lista
    prov_id = proveedor_map.get(combo_proveedores.get())
    productos_proveedor_lista = []
    if prov_id:
        conn = sqlite3.connect(database.get_db_path())
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, codigo_proveedor, descripcion FROM productos WHERE proveedor_id = ? AND estado = 'ACTIVO' ORDER BY descripcion",
            (prov_id,)
        )
        for pid, cod, desc in cursor.fetchall():
            productos_proveedor_lista.append({'id': pid, 'cod': cod, 'desc': desc, 'display': f"{cod} - {desc}"})
        conn.close()
    combo_producto.config(values=[p['display'] for p in productos_proveedor_lista])
    combo_producto.set('')

def filtrar_productos(event):
    """Busca coincidencias en tiempo real y despliega la lista"""
    if event.keysym in ('Down', 'Up', 'Return', 'Escape', 'Tab'):
        return
    
    texto = combo_producto.get().lower()
    
    if not texto:
        filtrados = [p['display'] for p in productos_proveedor_lista]
    else:
        # Filtra si el texto está contenido en cualquier parte del display
        filtrados = [p['display'] for p in productos_proveedor_lista if texto in p['display'].lower()]
    
    combo_producto.config(values=filtrados)
    
    if filtrados and texto != "":
        combo_producto.event_generate('<Down>')

def filtrar_proveedores(event):
    """Filtra el combo de proveedores al escribir"""
    if event.keysym in ('Down', 'Up', 'Return', 'Escape', 'Tab', 'Left', 'Right'): return
    
    texto = combo_proveedores.get().lower()
    todos = list(proveedor_map.keys())
    
    if not texto:
        combo_proveedores['values'] = todos
    else:
        filtrados = [p for p in todos if p.lower().startswith(texto)]
        combo_proveedores['values'] = filtrados
        if filtrados:
            combo_proveedores.event_generate('<Down>')

def mostrar_vista_lista():
    frame_edicion.pack_forget()
    frame_lista.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    cargar_pedidos_pendientes()

def mostrar_vista_edicion(event=None):
    global pedido_id_actual, pedido_temporal
    pedido_temporal.clear()
    pedido_id_actual = None
    
    if event: 
        seleccion = tabla_pedidos.selection()
        if seleccion:
            pedido_id_actual = tabla_pedidos.item(seleccion[0], 'values')[0]

    if pedido_id_actual:
        label_titulo_edicion.config(text=f"EDITAR PEDIDO N° {pedido_id_actual}")
        btn_imprimir_pdf.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        btn_borrar_pedido.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        try:
            conn = sqlite3.connect(database.get_db_path())
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.codigo_proveedor, p.descripcion, pfd.cantidad, prov.nombre, pfd.unidad_medida 
                FROM pedidos_fabrica_detalle pfd
                JOIN productos p ON pfd.producto_id = p.id
                JOIN pedidos_fabrica pf ON pfd.pedido_id = pf.id
                JOIN proveedores prov ON pf.proveedor_id = prov.id
                WHERE pfd.pedido_id = ?
            """, (pedido_id_actual,))
            filas = cursor.fetchall()
            conn.close()
            
            for f in filas:
                pedido_temporal.append({'id': f[0], 'cod': f[1], 'desc': f[2], 'cant': f[3], 'unidad': f[5]})
            
            if filas:
                combo_proveedores.set(filas[0][4])
                combo_proveedores.config(state="disabled")
                cargar_productos_proveedor() # Cargar productos del proveedor actual
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al cargar detalles: {e}")
    else:
        cargar_proveedores()
        label_titulo_edicion.config(text="NUEVO PEDIDO A FÁBRICA")
        btn_imprimir_pdf.pack_forget()
        btn_borrar_pedido.pack_forget() 
        combo_proveedores.set('')
        combo_proveedores.config(state="normal")
        productos_proveedor_lista.clear()
        combo_producto.config(values=[])

    actualizar_tabla_temporal()
    frame_lista.pack_forget()
    frame_edicion.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

def actualizar_tabla_temporal():
    for row in tabla_temporal.get_children():
        tabla_temporal.delete(row)
    for item in pedido_temporal:
        tabla_temporal.insert("", "end", values=(item['cod'], item['desc'], item['cant'], item['unidad']))

def agregar_producto_al_pedido():
    if not combo_proveedores.get():
        messagebox.showwarning("Aviso", "Seleccione un proveedor primero.")
        return

    texto_sel = combo_producto.get().strip()
    producto_sel = next((p for p in productos_proveedor_lista if p['display'] == texto_sel), None)
    
    if not producto_sel:
        messagebox.showwarning("Error", "Seleccione un producto válido de la lista desplegable.")
        return

    try:
        cantidad = int(ent_cantidad.get())
        if cantidad <= 0: raise ValueError
    except ValueError:
        messagebox.showerror("Error", "Cantidad inválida.")
        return

    unidad = combo_unidad_medida.get()
    prod_id = producto_sel['id']

    for item in pedido_temporal:
        if item['id'] == prod_id:
            item['cant'] += cantidad
            item['unidad'] = unidad
            break
    else:
        pedido_temporal.append({'id': prod_id, 'cod': producto_sel['cod'], 'desc': producto_sel['desc'], 'cant': cantidad, 'unidad': unidad})

    actualizar_tabla_temporal()
    combo_producto.set('')
    ent_cantidad.delete(0, tk.END)
    ent_cantidad.insert(0, "1")
    combo_producto.focus()

def on_tabla_click(event):
    """Manejador de clics en la tabla de lista de pedidos"""
    region = tabla_pedidos.identify_region(event.x, event.y)
    if region != "cell": return

    col_id = tabla_pedidos.identify_column(event.x)
    row_id = tabla_pedidos.identify_row(event.y)
    
    if not row_id: return

    # Columnas: #1=id, #2=prov, #3=fecha, #4=#items, #5=total_unidades, #6=EDITAR, #7=ELIMINAR
    if col_id == "#6": # Editar
        # Seleccionamos la fila y abrimos la edición
        tabla_pedidos.selection_set(row_id)
        mostrar_vista_edicion(event)
    elif col_id == "#7": # Eliminar
        # row_id es el ID del pedido porque usamos iid=id en el insert
        eliminar_pedido_desde_lista(row_id)

def montar_interfaz(parent):
    global ventana_principal, frame_lista, frame_edicion, tabla_pedidos, tabla_temporal
    global combo_proveedores, combo_producto, ent_cantidad, combo_unidad_medida, proveedor_map
    global label_titulo_edicion, btn_imprimir_pdf, btn_borrar_pedido

    ventana_principal = tk.Frame(parent, bg=st.BG_MAIN)

    # --- VISTA LISTA ---
    frame_lista = tk.Frame(ventana_principal, bg=st.BG_MAIN)
    f_botones_lista = tk.Frame(frame_lista, bg=st.BG_MAIN)
    f_botones_lista.pack(fill=tk.X, pady=10)
    tk.Button(f_botones_lista, text="➕ Nuevo Pedido", command=mostrar_vista_edicion, **st.estilo_boton()).pack(side=tk.LEFT)

    columnas_lista = ("id", "prov", "fecha", "#items", "total_unidades", "editar", "eliminar")
    tabla_pedidos = ttk.Treeview(frame_lista, columns=columnas_lista, show="headings")
    
    for col in columnas_lista: 
        if col in ["editar", "eliminar"]:
            tabla_pedidos.heading(col, text=col.replace("editar", "✏️").replace("eliminar", "🗑️"))
            tabla_pedidos.column(col, width=50, anchor="center")
        else:
            tabla_pedidos.heading(col, text=col.upper())
            
    tabla_pedidos.column("id", width=50, anchor="center")
    tabla_pedidos.column("prov", width=250)
    tabla_pedidos.column("fecha", width=120, anchor="center")
    
    tabla_pedidos.pack(fill=tk.BOTH, expand=True, pady=10)
    tabla_pedidos.bind("<Double-1>", mostrar_vista_edicion)
    tabla_pedidos.bind("<Button-1>", on_tabla_click)

    # --- VISTA EDICIÓN ---
    frame_edicion = tk.Frame(ventana_principal, bg=st.BG_MAIN)
    label_titulo_edicion = tk.Label(frame_edicion, text="NUEVO PEDIDO", font=st.FONT_TITLE, bg=st.BG_MAIN, fg=st.TEXT_PRIMARY)
    label_titulo_edicion.pack(pady=10)

    f_controles = tk.Frame(frame_edicion, bg=st.BG_CARD, padx=15, pady=15)
    f_controles.pack(fill=tk.X, pady=10)

    tk.Label(f_controles, text="Proveedor:", bg=st.BG_CARD, fg="white").grid(row=0, column=0, sticky='w')
    combo_proveedores = ttk.Combobox(f_controles, values=[], width=30, font=st.FONT_INPUT)
    combo_proveedores.grid(row=0, column=1, sticky='w', padx=5)
    combo_proveedores.bind("<<ComboboxSelected>>", cargar_productos_proveedor)
    combo_proveedores.bind("<KeyRelease>", filtrar_proveedores)

    tk.Label(f_controles, text="Producto:", bg=st.BG_CARD, fg="white").grid(row=1, column=0, pady=10, sticky='w')
    # Definimos combo_producto con altura para ver más resultados
    combo_producto = ttk.Combobox(f_controles, values=[], width=35, height=12, font=st.FONT_INPUT) 
    combo_producto.grid(row=1, column=1, sticky='w', padx=5)
    combo_producto.bind("<KeyRelease>", filtrar_productos)

    tk.Label(f_controles, text="Cant:", bg=st.BG_CARD, fg="white").grid(row=1, column=2, padx=5)
    ent_cantidad = tk.Entry(f_controles, width=5, **st.estilo_entrada())
    ent_cantidad.insert(0, "1")
    ent_cantidad.grid(row=1, column=3, sticky='w')

    tk.Label(f_controles, text="Unidad:", bg=st.BG_CARD, fg="white").grid(row=1, column=4, padx=(10, 0))
    unidades_medida = ["Unidad", "Decena", "Docena", "Dcpa", "Millar", "Caja", "Cajon", "Bulto"]
    combo_unidad_medida = ttk.Combobox(f_controles, values=unidades_medida, state="readonly", width=8, font=st.FONT_INPUT)
    combo_unidad_medida.set("Unidad")
    combo_unidad_medida.grid(row=1, column=5, sticky='w')

    tk.Button(f_controles, text="Agregar", command=agregar_producto_al_pedido, **st.estilo_boton(st.ACCENT)).grid(row=1, column=6, padx=10)

    columnas_edicion = ("cod", "desc", "cant", "unidad")
    tabla_temporal = ttk.Treeview(frame_edicion, columns=columnas_edicion, show="headings", height=8)
    for col in columnas_edicion: tabla_temporal.heading(col, text=col.upper())
    tabla_temporal.column("unidad", width=80, anchor="center")
    tabla_temporal.pack(fill=tk.BOTH, expand=True, pady=5)

    tk.Button(frame_edicion, text="🗑️ Quitar Producto Seleccionado", command=eliminar_producto_temporal, **st.estilo_boton(st.RED_ERROR)).pack(pady=5)

    f_footer = tk.Frame(frame_edicion, bg=st.BG_MAIN)
    f_footer.pack(fill=tk.X, pady=10)

    tk.Button(f_footer, text="💾 GUARDAR", command=guardar_cambios, **st.estilo_boton()).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
    
    btn_imprimir_pdf = tk.Button(f_footer, text="🖨️ PDF", command=generar_pdf_pedido, **st.estilo_boton(st.ACCENT))
    btn_imprimir_pdf.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

    btn_borrar_pedido = tk.Button(f_footer, text="💣 ELIMINAR PEDIDO", command=eliminar_pedido_completo, **st.estilo_boton(st.RED_ERROR))
    btn_borrar_pedido.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

    tk.Button(f_footer, text="❌ VOLVER", command=mostrar_vista_lista, **st.estilo_boton(st.BG_CARD)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

    mostrar_vista_lista()
    return ventana_principal