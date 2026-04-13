import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
from datetime import datetime
from fpdf import FPDF
import styles as st # Importamos los estilos
import database # Importamos para obtener la ruta
import ttkbootstrap as tb

# --- Variables Globales ---
frame_lista = None
frame_edicion = None
tabla_pendientes = None
tabla_items_nuevo = None
lista_pedido_actual = []
codigo_seleccionado = ""
pedido_editando_id = None

# --- LÓGICA DE DATOS ---

def obtener_proveedores():
    conexion = sqlite3.connect(database.get_db_path())
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre FROM proveedores ORDER BY nombre ASC")
    filas = cursor.fetchall()
    conexion.close()
    return [f[0] for f in filas]

def cargar_pedidos_pendientes(event=None):
    """Llena la tabla de la vista principal con pedidos en estado PENDIENTE"""
    for row in tabla_pendientes.get_children():
        tabla_pendientes.delete(row)
    
    try:
        conexion = sqlite3.connect(database.get_db_path())
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT pf.id, prov.nombre, strftime('%d-%m-%Y', pf.fecha_creacion),
                   (SELECT COUNT(*) FROM pedidos_fabrica_detalle WHERE pedido_id = pf.id)
            FROM pedidos_fabrica pf
            JOIN proveedores prov ON pf.proveedor_id = prov.id
            WHERE pf.estado = 'PENDIENTE'
            ORDER BY pf.id DESC
        """)
        for f in cursor.fetchall():
            tabla_pendientes.insert("", "end", values=f + ("✏️", "🗑️"))
        conexion.close()
    except Exception as e:
        print(f"Error cargando pendientes: {e}")

def abrir_generador(pedido_id=None):
    """Cambia a la vista de generador de pedido"""
    global pedido_editando_id, lista_pedido_actual
    pedido_editando_id = pedido_id
    lista_pedido_actual.clear()
    for row in tabla_items_nuevo.get_children(): tabla_items_nuevo.delete(row)
    
    if pedido_id:
        # Cargar datos del pedido existente
        conexion = sqlite3.connect(database.get_db_path())
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
            combo_prov_gen.set(filas[0][0])
            for f in filas:
                item = {'prod_id': f[1], 'codigo': f[2], 'descripcion': f[3], 'cantidad': f[4], 'unidad': f[5]}
                lista_pedido_actual.append(item)
                tabla_items_nuevo.insert("", "end", values=(item['codigo'], item['descripcion'], item['cantidad'], item['unidad'], "📎", "🗑️"))
        conexion.close()
    else:
        combo_prov_gen.set("")
        ent_cant_gen.delete(0, tk.END)

    frame_lista.pack_forget()
    frame_edicion.pack(fill=tk.BOTH, expand=True)

def volver_a_lista():
    frame_edicion.pack_forget()
    frame_lista.pack(fill=tk.BOTH, expand=True)
    cargar_pedidos_pendientes()

def abrir_buscador_emergente():
    """Abre la ventana 3/4 con Código, Producto y Costo"""
    prov_sel = combo_prov_gen.get()
    if not prov_sel:
        messagebox.showwarning("Atención", "Seleccione una fábrica primero.")
        return

    top = tk.Toplevel()
    top.title("Buscador de Productos")
    sw, sh = top.winfo_screenwidth(), top.winfo_screenheight()
    top.geometry(f"{int(sw*0.75)}x{int(sh*0.75)}")
    st.aplicar_estilo_ventana(top)

    f_filtros = tk.Frame(top, bg=st.BG_MAIN, pady=10)
    f_filtros.pack(fill=tk.X, padx=10)
    
    tk.Label(f_filtros, text="Código:", bg=st.BG_MAIN, fg="white", font=st.FONT_LABEL).pack(side=tk.LEFT, padx=5)
    e_cod = tk.Entry(f_filtros, **st.estilo_entrada())
    e_cod.pack(side=tk.LEFT, padx=5)
    
    tk.Label(f_filtros, text="Producto:", bg=st.BG_MAIN, fg="white", font=st.FONT_LABEL).pack(side=tk.LEFT, padx=5)
    e_prod = tk.Entry(f_filtros, **st.estilo_entrada())
    e_prod.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    cols = ("cod", "desc", "costo")
    t_busca = ttk.Treeview(top, columns=cols, show="headings")
    t_busca.heading("cod", text="CÓDIGO"); t_busca.heading("desc", text="PRODUCTO"); t_busca.heading("costo", text="COSTO PROF.")
    t_busca.column("costo", anchor="e")
    t_busca.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def buscar(_=None):
        for r in t_busca.get_children(): t_busca.delete(r)
        conexion = sqlite3.connect(database.get_db_path())
        cursor = conexion.cursor()
        query = """
            SELECT p.codigo_proveedor, p.descripcion, p.costo_base, p.coeficiente_ganancia, p.iva, pr.descuento_global, pr.incremento_global
            FROM productos p JOIN proveedores pr ON p.proveedor_id = pr.id
            WHERE pr.nombre = ? AND p.codigo_proveedor LIKE ? AND p.descripcion LIKE ? AND p.estado = 'ACTIVO'
        """
        cursor.execute(query, (prov_sel, f"%{e_cod.get()}%", f"%{e_prod.get()}%"))
        for r in cursor.fetchall():
            precio = r[2] * (1 - (r[5] or 0)) * (1 + (r[6] or 0)) * r[3] * (1 + r[4])
            t_busca.insert("", "end", values=(r[0], r[1], f"$ {precio:.2f}"))
        conexion.close()

    e_cod.bind("<KeyRelease>", buscar); e_prod.bind("<KeyRelease>", buscar)
    
    def seleccionar():
        global codigo_seleccionado
        sel = t_busca.selection()
        if sel:
            val = t_busca.item(sel[0], 'values')
            codigo_seleccionado = val[0]
            lbl_prod_sel.config(text=f"SELECCIONADO: {val[0]} - {val[1][:40]}...", foreground=st.ACCENT)
            top.destroy()
            ent_cant_gen.focus()

    tk.Button(top, text="SELECCIONAR", command=seleccionar, **st.get_btn_style(st.ACCENT)).pack(pady=10)
    buscar()

def agregar_item():
    global codigo_seleccionado
    if not codigo_seleccionado: return
    try:
        cant = float(ent_cant_gen.get())
    except: 
        messagebox.showerror("Error", "Cantidad no válida"); return

    conexion = sqlite3.connect(database.get_db_path())
    cursor = conexion.cursor()
    cursor.execute("SELECT id, descripcion FROM productos WHERE codigo_proveedor = ?", (codigo_seleccionado,))
    res = cursor.fetchone()
    conexion.close()

    if res:
        item = {'prod_id': res[0], 'codigo': codigo_seleccionado, 'descripcion': res[1], 'cantidad': cant, 'unidad': combo_unid_gen.get()}
        lista_pedido_actual.append(item)
        tabla_items_nuevo.insert("", "end", values=(item['codigo'], item['descripcion'], item['cantidad'], item['unidad'], "📎", "🗑️"))
        codigo_seleccionado = ""
        lbl_prod_sel.config(text="")
        ent_cant_gen.delete(0, tk.END)

def guardar_pedido_db():
    if not lista_pedido_actual: return
    prov_nom = combo_prov_gen.get()
    try:
        conexion = sqlite3.connect(database.get_db_path())
        cursor = conexion.cursor()
        cursor.execute("SELECT id FROM proveedores WHERE nombre = ?", (prov_nom,))
        prov_id = cursor.fetchone()[0]
        
        if pedido_editando_id:
            cursor.execute("DELETE FROM pedidos_fabrica_detalle WHERE pedido_id = ?", (pedido_editando_id,))
            pid = pedido_editando_id
        else:
            cursor.execute("INSERT INTO pedidos_fabrica (proveedor_id, estado) VALUES (?, 'PENDIENTE')", (prov_id,))
            pid = cursor.lastrowid

        for i in lista_pedido_actual:
            cursor.execute("INSERT INTO pedidos_fabrica_detalle (pedido_id, producto_id, cantidad, unidad_medida) VALUES (?,?,?,?)",
                           (pid, i['prod_id'], i['cantidad'], i['unidad']))
        conexion.commit()
        conexion.close()
        messagebox.showinfo("Éxito", "Pedido Guardado")
        volver_a_lista()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def borrar_pedido_total(pid):
    if messagebox.askyesno("Confirmar", "¿Eliminar pedido permanentemente?"):
        conexion = sqlite3.connect(database.get_db_path())
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM pedidos_fabrica_detalle WHERE pedido_id = ?", (pid,))
        cursor.execute("DELETE FROM pedidos_fabrica WHERE id = ?", (pid,))
        conexion.commit()
        conexion.close()
        cargar_pedidos_pendientes()

def on_click_pendientes(event):
    item_id = tabla_pendientes.identify_row(event.y)
    col = tabla_pendientes.identify_column(event.x)
    if not item_id: return
    pid = tabla_pendientes.item(item_id, "values")[0]
    if col == "#5": abrir_generador(pid)
    elif col == "#6": borrar_pedido_total(pid)

def on_click_items_nuevo(event):
    item_id = tabla_items_nuevo.identify_row(event.y)
    col = tabla_items_nuevo.identify_column(event.x)
    if not item_id: return
    
    idx = tabla_items_nuevo.index(item_id)
    item = lista_pedido_actual[idx]
    
    if col == "#5": # Modificar Cantidad (Clip)
        nueva_cant = simpledialog.askfloat("Modificar Cantidad", f"Producto: {item['descripcion']}\nNueva cantidad:", initialvalue=item['cantidad'])
        if nueva_cant is not None and nueva_cant > 0:
            item['cantidad'] = nueva_cant
            tabla_items_nuevo.item(item_id, values=(item['codigo'], item['descripcion'], item['cantidad'], item['unidad'], "📎", "🗑️"))
    elif col == "#6": # Eliminar Item (Tachito)
        if messagebox.askyesno("Confirmar", "¿Quitar producto del pedido?"):
            lista_pedido_actual.pop(idx)
            tabla_items_nuevo.delete(item_id)

# --- INTERFAZ ---

def montar_interfaz(parent):
    global frame_lista, frame_edicion, tabla_pendientes, tabla_items_nuevo
    global combo_prov_gen, ent_cant_gen, combo_unid_gen, lbl_prod_sel

    container = tk.Frame(parent, bg=st.BG_MAIN)

    # 1. VISTA DE LISTA
    frame_lista = tk.Frame(container, bg=st.BG_MAIN)
    frame_lista.pack(fill=tk.BOTH, expand=True)

    tk.Button(frame_lista, text="➕ NUEVO PEDIDO", command=lambda: abrir_generador(), **st.estilo_boton(st.ACCENT)).pack(pady=20)
    
    tk.Label(frame_lista, text="PEDIDOS PENDIENTES", font=st.FONT_TITLE, bg=st.BG_MAIN, fg="white").pack()
    
    cols_p = ("id", "prov", "fecha", "items", "edit", "del")
    tabla_pendientes = ttk.Treeview(frame_lista, columns=cols_p, show="headings", height=15)
    for c in cols_p: tabla_pendientes.heading(c, text=c.upper())
    tabla_pendientes.column("edit", width=50, anchor="center"); tabla_pendientes.column("del", width=50, anchor="center")
    tabla_pendientes.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    tabla_pendientes.bind("<Button-1>", on_click_pendientes)

    # 2. VISTA GENERADOR (Edición)
    frame_edicion = tk.Frame(container, bg=st.BG_MAIN)
    
    # Barra superior generador
    f_top_gen = tk.Frame(frame_edicion, bg=st.BG_CARD, pady=10)
    f_top_gen.pack(fill=tk.X, padx=15, pady=10)

    tk.Label(f_top_gen, text="FABRICA:", bg=st.BG_CARD, fg="white", font=st.FONT_LABEL).grid(row=0, column=0, padx=5)
    combo_prov_gen = ttk.Combobox(f_top_gen, values=obtener_proveedores(), font=st.FONT_INPUT)
    combo_prov_gen.grid(row=0, column=1, padx=5)

    tk.Button(f_top_gen, text="📦 PRODUCTOS", command=abrir_buscador_emergente, **st.get_btn_style(st.ACCENT)).grid(row=0, column=2, padx=10)
    
    lbl_prod_sel = tk.Label(f_top_gen, text="", bg=st.BG_CARD, fg=st.ACCENT, font=st.FONT_NORMAL)
    lbl_prod_sel.grid(row=0, column=3, padx=10)

    tk.Label(f_top_gen, text="CANT:", bg=st.BG_CARD, fg="white", font=st.FONT_LABEL).grid(row=0, column=4, padx=5)
    ent_cant_gen = tk.Entry(f_top_gen, width=8, **st.estilo_entrada())
    ent_cant_gen.grid(row=0, column=5, padx=5)

    combo_unid_gen = ttk.Combobox(f_top_gen, values=["Unidad", "Dcpa", "Docena", "Caja"], width=10, font=st.FONT_INPUT)
    combo_unid_gen.set("Unidad")
    combo_unid_gen.grid(row=0, column=6, padx=5)

    tk.Button(f_top_gen, text="AÑADIR", command=agregar_item, **st.get_btn_style()).grid(row=0, column=7, padx=10)

    # Tabla de items del nuevo pedido
    cols_n = ("cod", "desc", "cant", "unid", "mod", "del")
    tabla_items_nuevo = ttk.Treeview(frame_edicion, columns=cols_n, show="headings")
    for c in cols_n: tabla_items_nuevo.heading(c, text=c.upper())
    tabla_items_nuevo.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    tabla_items_nuevo.bind("<Button-1>", on_click_items_nuevo)

    # Botonera inferior
    f_bot_gen = tk.Frame(frame_edicion, bg=st.BG_MAIN)
    f_bot_gen.pack(fill=tk.X, pady=20)
    
    tk.Button(f_bot_gen, text="❌ VOLVER", command=volver_a_lista, **st.estilo_boton(st.BG_CARD)).pack(side=tk.RIGHT, padx=10)
    tk.Button(f_bot_gen, text="💾 GUARDAR PEDIDO", command=guardar_pedido_db, **st.estilo_boton(st.ACCENT)).pack(side=tk.RIGHT, padx=10)

    cargar_pedidos_pendientes()
    return container

# --- Generación de PDF (Mantenida por compatibilidad) ---

def generar_pdf_pedido(pedido_id_actual):
    try:
        if not os.path.exists("pedidos_pdf"):
            os.makedirs("pedidos_pdf")
    except Exception as e:
        print(f"Error PDF: {e}")