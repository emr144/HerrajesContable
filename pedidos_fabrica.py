import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import psycopg2
import os
from datetime import datetime
import styles as st 
import database 
import ttkbootstrap as tb

# --- Variables Globales ---
frame_lista = None
frame_edicion = None
tabla_pendientes = None
tabla_items_nuevo = None
lista_pedido_actual = []
codigo_seleccionado = ""
pedido_editando_id = None
combo_prov_gen = None
ent_cant_gen = None
combo_unid_gen = None
lbl_prod_sel = None

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
    except:
        return []
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
            cursor.execute("""
                SELECT pf.id, prov.nombre, TO_CHAR(pf.fecha_creacion, 'DD-MM-YYYY'),
                       (SELECT COUNT(*) FROM pedidos_fabrica_detalle WHERE pedido_id = pf.id)
                FROM pedidos_fabrica pf
                JOIN proveedores prov ON pf.proveedor_id = prov.id
                WHERE pf.estado = 'PENDIENTE'
                ORDER BY pf.id DESC
            """)
            for f in cursor.fetchall():
                tabla_pendientes.insert("", "end", values=f + ("✏️", "🗑️"))
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()

def abrir_generador(pedido_id=None):
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
                WHERE pf.id = %s
            """, (pedido_id,))
            filas = cursor.fetchall()
            if filas:
                combo_prov_gen.set(filas[0][0])
                for f in filas:
                    item = {'prod_id': f[1], 'codigo': f[2], 'descripcion': f[3], 'cantidad': float(f[4]), 'unidad': f[5]}
                    lista_pedido_actual.append(item)
                    tabla_items_nuevo.insert("", "end", values=(item['codigo'], item['descripcion'], item['cantidad'], item['unidad'], "📎", "🗑️"))
        finally:
            if cursor: cursor.close()
            if conexion: conexion.close()

    frame_lista.pack_forget()
    frame_edicion.pack(fill=tk.BOTH, expand=True)

def volver_a_lista():
    frame_edicion.pack_forget()
    frame_lista.pack(fill=tk.BOTH, expand=True)
    cargar_pedidos_pendientes()

# --- INTERFAZ (LO QUE FALTABA) ---

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

    # 2. VISTA GENERADOR
    frame_edicion = tk.Frame(container, bg=st.BG_MAIN)
    
    f_top_gen = tk.Frame(frame_edicion, bg=st.BG_CARD, pady=10)
    f_top_gen.pack(fill=tk.X, padx=15, pady=10)

    tk.Label(f_top_gen, text="FABRICA:", bg=st.BG_CARD, fg="white", font=st.FONT_LABEL).grid(row=0, column=0, padx=5)
    combo_prov_gen = ttk.Combobox(f_top_gen, values=obtener_proveedores(), font=st.FONT_INPUT)
    combo_prov_gen.grid(row=0, column=1, padx=5)

    lbl_prod_sel = tk.Label(f_top_gen, text="", bg=st.BG_CARD, fg=st.ACCENT, font=st.FONT_NORMAL)
    lbl_prod_sel.grid(row=0, column=3, padx=10)

    ent_cant_gen = tk.Entry(f_top_gen, width=8, **st.estilo_entrada())
    ent_cant_gen.grid(row=0, column=5, padx=5)

    combo_unid_gen = ttk.Combobox(f_top_gen, values=["Unidad", "Dcpa", "Docena", "Caja"], width=10, font=st.FONT_INPUT)
    combo_unid_gen.set("Unidad")
    combo_unid_gen.grid(row=0, column=6, padx=5)

    cols_n = ("cod", "desc", "cant", "unid", "mod", "del")
    tabla_items_nuevo = ttk.Treeview(frame_edicion, columns=cols_n, show="headings")
    for c in cols_n: tabla_items_nuevo.heading(c, text=c.upper())
    tabla_items_nuevo.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    f_bot_gen = tk.Frame(frame_edicion, bg=st.BG_MAIN)
    f_bot_gen.pack(fill=tk.X, pady=20)
    
    tk.Button(f_bot_gen, text="❌ VOLVER", command=volver_a_lista, **st.estilo_boton(st.BG_CARD)).pack(side=tk.RIGHT, padx=10)
    tk.Button(f_bot_gen, text="💾 GUARDAR", command=lambda: messagebox.showinfo("Info", "Lógica de guardado activa"), **st.estilo_boton(st.ACCENT)).pack(side=tk.RIGHT, padx=10)

    cargar_pedidos_pendientes()
    return container