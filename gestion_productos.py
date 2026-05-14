import tkinter as tk
from tkinter import ttk, messagebox
import styles as st
import database # Importamos para obtener la ruta

# --- Funciones Auxiliares para Normalización de Búsqueda ---
def _normalize_string_for_sql_search(column_name):
    """Genera un fragmento SQL para normalizar una cadena para búsqueda.
    Elimina espacios, guiones, guiones bajos, barras y acentos comunes en español.
    """
    n = f"LOWER({column_name})"
    n = f"REPLACE({n}, ' ', '')"
    n = f"REPLACE({n}, '-', '')"
    n = f"REPLACE({n}, '_', '')"
    n = f"REPLACE({n}, '/', '')"
    n = f"REPLACE({n}, 'á', 'a')"
    n = f"REPLACE({n}, 'é', 'e')"
    n = f"REPLACE({n}, 'í', 'i')"
    n = f"REPLACE({n}, 'ó', 'o')"
    n = f"REPLACE({n}, 'ú', 'u')"
    n = f"REPLACE({n}, 'ü', 'u')"
    n = f"REPLACE({n}, 'ñ', 'n')"
    return n

def _normalize_python_string_for_search(text):
    """Normaliza una cadena de Python para comparación, eliminando acentos y caracteres especiales."""
    text = text.lower().replace(' ', '').replace('-', '').replace('_', '').replace('/', '')
    return text.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ü', 'u').replace('ñ', 'n')

# Variable global para controlar edición
producto_seleccionado_id = None

# --- Variables globales para el buscador de edición ---
sugerencias_map = {}
lista_sugerencias_edicion = None

# Nuevas variables para filtros de búsqueda
combo_buscar_prov = None
ent_buscar_codigo = None
ent_buscar_desc = None
lista_proveedores_cache = []

combo_lista_precios = None

def obtener_multiplicador_precio():
    """Devuelve el factor de multiplicación según la lista seleccionada"""
    if not combo_lista_precios: return 1.0
    seleccion = combo_lista_precios.get()
    if "15%" in seleccion: return 1.15
    elif "30%" in seleccion: return 1.30
    return 1.0

def cargar_productos():
    """Carga y muestra los productos en la tabla con filtros de proveedor, código y descripción."""
    for row in tabla.get_children():
        tabla.delete(row)
    
    conexion = database.conectar()
    cursor = conexion.cursor()
    
    query = """
        SELECT p.id, p.codigo_proveedor, p.descripcion, pr.nombre, p.costo_base,
               p.coeficiente_ganancia, p.iva, p.estado, p.numero_lista, p.fecha_lista,
               pr.descuento_global, pr.incremento_global, pr.fecha_modif_coeficiente
        FROM productos p
        JOIN proveedores pr ON p.proveedor_id = pr.id
        WHERE 1=1
    """
    params = []
    
    # Filtro por Proveedor
    if combo_buscar_prov:
        prov_f = combo_buscar_prov.get()
        if prov_f and prov_f != "TODOS":
            query += " AND pr.nombre = %s"
            params.append(prov_f)
            
    # Filtro por Código
    if ent_buscar_codigo:
        cod_f = ent_buscar_codigo.get().strip()
        if cod_f:
            tokens = _normalize_python_string_for_search(cod_f).split()
            for t in tokens:
                query += f" AND {_normalize_string_for_sql_search('p.codigo_proveedor')} LIKE %s"
                params.append(f"%{t}%")
            
    # Filtro por Descripción
    if ent_buscar_desc:
        desc_f = ent_buscar_desc.get().strip()
        if desc_f:
            tokens = _normalize_python_string_for_search(desc_f).split()
            for t in tokens:
                query += f" AND {_normalize_string_for_sql_search('p.descripcion')} LIKE %s"
                params.append(f"%{t}%")
        
    query += " ORDER BY p.descripcion ASC"
    cursor.execute(query, params)

    multiplicador = obtener_multiplicador_precio()
        
    registros = cursor.fetchall()
    for prod in registros:
        p_id, cod, desc, prov, costo, coef, iva, estado, num_lista, fecha_lista, desc_g, inc_g, f_mod_coef = prod
        # Calculamos el precio de venta aplicando descuento e incremento global del proveedor
        precio_venta = costo * (1 - (desc_g or 0)) * (1 + (inc_g or 0)) * coef * (1 + iva) * multiplicador
        
        # Preparamos los valores para que se vean bien en la tabla
        valores_display = (cod, desc, prov, f"$ {costo:.2f}", coef, f"$ {precio_venta:.2f}")
        valores_con_accion = valores_display + ('✏️', '🗑️') # Los íconos de acción
        
        tabla.insert("", "end", values=valores_con_accion, iid=p_id)

    label_contador.config(text=f"Total Productos: {len(registros)}")
    conexion.close()

def limpiar_formulario(deseleccionar=False):
    """Limpia los campos del formulario de edición."""
    global producto_seleccionado_id
    producto_seleccionado_id = None
    ent_desc.delete(0, tk.END)
    ent_costo.delete(0, tk.END)
    ent_coef.delete(0, tk.END)
    btn_guardar.config(text="💾 GUARDAR CAMBIOS", state="disabled")
    if deseleccionar and tabla.selection():
        tabla.selection_remove(tabla.selection())

def guardar_producto():
    """Actualiza un producto existente en la base de datos."""
    if not producto_seleccionado_id:
        return

    try:
        desc = ent_desc.get().strip()
        costo = float(ent_costo.get().strip().replace('$', ''))
    except ValueError:
        messagebox.showerror("Error de Formato", "El costo debe ser un número válido.")
        return

    if not desc:
        messagebox.showwarning("Atención", "La descripción no puede estar vacía.")
        return

    conexion = database.conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE productos SET descripcion=%s, costo_base=%s
        WHERE id=%s
    """, (desc, costo, producto_seleccionado_id))
    conexion.commit()
    conexion.close()
    
    messagebox.showinfo("Éxito", "Producto actualizado correctamente.")
    limpiar_formulario()
    cargar_productos()

def cargar_datos_para_editar(item_id):
    """Carga los datos de un producto en el formulario para su edición."""
    global producto_seleccionado_id
    
    conexion = database.conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT descripcion, costo_base, coeficiente_ganancia FROM productos WHERE id=%s", (item_id,))
    valores = cursor.fetchone()
    conexion.close()

    if not valores: return

    limpiar_formulario()
    producto_seleccionado_id = item_id
    
    ent_desc.insert(0, valores[0])
    ent_costo.insert(0, f"{valores[1]:.2f}")
    ent_coef.insert(0, str(valores[2]))
    ent_coef.config(state="disabled") # El coeficiente no se edita manualmente aquí
    
    btn_guardar.config(state="normal")

def eliminar_producto_por_id(producto_id, descripcion):
    """Elimina un único producto, pidiendo confirmación."""
    msg = f"¿Eliminar el producto '{descripcion}' (ID: {producto_id})?"
    if messagebox.askyesno("Confirmar Eliminación", msg):
        try:
            conexion = database.conectar()
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
            conexion.commit()
            conexion.close()
            cargar_productos()
            limpiar_formulario(deseleccionar=True)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el producto: {e}")

def modificar_coef_por_proveedor_dialogo():
    """Abre un diálogo para cambiar el coeficiente de todos los productos de un proveedor."""
    dialog = tk.Toplevel(ventana)
    dialog.title("Modificar Coeficiente por Proveedor")
    dialog.geometry("450x400") # Aumentado para dar espacio a los botones
    st.aplicar_estilo_ventana(dialog)
    dialog.config(padx=20, pady=20)

    tk.Label(dialog, text="Cambiar coeficiente para un proveedor", 
             font=st.FONT_LABEL, bg=st.BG_MAIN, fg=st.TEXT_SECONDARY).pack(pady=10)

    # --- Frame para selección de proveedor ---
    frame_prov = tk.Frame(dialog, bg=st.BG_MAIN)
    frame_prov.pack(fill='x', pady=5)
    tk.Label(frame_prov, text="1. Seleccione Proveedor:", font=st.FONT_NORMAL, bg=st.BG_MAIN, fg='white').pack(anchor='w')
    
    conexion = database.conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM proveedores ORDER BY nombre")
    proveedores = cursor.fetchall()
    conexion.close()
    
    nombres_provs = [p[1] for p in proveedores]
    proveedor_map = {nombre: pid for pid, nombre in proveedores}
    
    def filtrar_provs(event):
        if event.keysym in ('Down', 'Up', 'Return', 'Escape', 'Tab', 'Left', 'Right'): return
        texto = combo.get().lower()
        if not texto:
            combo['values'] = nombres_provs
        else:
            filtrados = [p for p in nombres_provs if p.lower().startswith(texto)]
            combo['values'] = filtrados
            if filtrados:
                combo.event_generate('<Down>')

    def actualizar_valor_actual(event):
        """Busca el coeficiente actual de los productos de este proveedor."""
        nombre_prov = combo.get()
        if nombre_prov in proveedor_map:
            prov_id = proveedor_map[nombre_prov]
            conn = database.conectar()
            cur = conn.cursor()
            # Buscamos el coeficiente del primer producto activo que encontremos
            cur.execute("SELECT coeficiente_ganancia FROM productos WHERE proveedor_id = %s AND estado = 'ACTIVO' LIMIT 1", (prov_id,))
            res = cur.fetchone()
            conn.close()
            if res:
                ent_nuevo_coef.delete(0, tk.END)
                ent_nuevo_coef.insert(0, str(res[0]))

    combo = ttk.Combobox(dialog, values=nombres_provs, font=st.FONT_INPUT)
    combo.pack(fill="x", pady=5)
    combo.bind("<KeyRelease>", filtrar_provs)
    combo.bind("<<ComboboxSelected>>", actualizar_valor_actual)

    # --- Frame para nuevo coeficiente ---
    frame_coef = tk.Frame(dialog, bg=st.BG_MAIN)
    frame_coef.pack(fill='x', pady=10)
    tk.Label(frame_coef, text="2. Ingrese Nuevo Coeficiente:", font=st.FONT_NORMAL, bg=st.BG_MAIN, fg='white').pack(anchor='w')
    ent_nuevo_coef = tk.Entry(frame_coef, **st.estilo_entrada())
    ent_nuevo_coef.pack(fill="x", pady=5)
    ent_nuevo_coef.insert(0, "1.6")

    def confirmar_cambio():
        nombre_prov = combo.get()
        nuevo_coef_str = ent_nuevo_coef.get().strip()

        if not nombre_prov or not nuevo_coef_str:
            messagebox.showwarning("Datos incompletos", "Debe seleccionar un proveedor e ingresar un coeficiente.", parent=dialog)
            return
        
        try:
            nuevo_coef = float(nuevo_coef_str)
        except ValueError:
            messagebox.showerror("Error de formato", "El coeficiente debe ser un número (ej: 1.6).", parent=dialog)
            return

        proveedor_id = proveedor_map[nombre_prov]
        
        msg = (f"¿Confirma que desea cambiar el coeficiente de ganancia a '{nuevo_coef}' "
               f"para TODOS los productos del proveedor '{nombre_prov}'?")
        
        if messagebox.askyesno("Confirmar Cambio Masivo", msg, parent=dialog):
            try:
                conn = database.conectar()
                cur = conn.cursor()
                
                # 1. Actualizar productos
                cur.execute("UPDATE productos SET coeficiente_ganancia = %s WHERE proveedor_id = %s", (nuevo_coef, proveedor_id))
                actualizados = cur.rowcount
                
                # 2. Actualizar fecha en proveedor
                cur.execute("UPDATE proveedores SET fecha_modif_coeficiente = CURRENT_DATE WHERE id = %s", (proveedor_id,))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Éxito", f"Se actualizaron {actualizados} productos de '{nombre_prov}'.", parent=ventana)
                dialog.destroy()
                cargar_productos() # Recargar la tabla principal
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron actualizar los productos: {e}", parent=dialog)

    btn_confirmar = tk.Button(dialog, text="📈 APLICAR CAMBIO", command=confirmar_cambio, **st.estilo_boton(st.ACCENT))
    btn_confirmar.pack(fill="x", pady=(30, 10)) # Más margen superior

def eliminar_por_proveedor_dialogo():
    """Abre un diálogo para seleccionar un proveedor y borrar todos sus productos."""
    dialog = tk.Toplevel(ventana)
    dialog.title("Eliminar Productos por Proveedor") # Título de la ventana
    dialog.geometry("400x250") # Aumentamos la altura para que el botón sea visible
    st.aplicar_estilo_ventana(dialog)
    dialog.config(padx=20, pady=20)

    tk.Label(dialog, text="Seleccione un proveedor para\nborrar TODOS sus productos:", 
             font=st.FONT_LABEL, bg=st.BG_MAIN, fg=st.TEXT_SECONDARY).pack(pady=10)

    # Obtener proveedores
    conexion = database.conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM proveedores ORDER BY nombre")
    proveedores = cursor.fetchall()
    conexion.close()
    
    nombres_provs = [p[1] for p in proveedores]
    proveedor_map = {nombre: pid for pid, nombre in proveedores}

    def filtrar_provs(event):
        if event.keysym in ('Down', 'Up', 'Return', 'Escape', 'Tab', 'Left', 'Right'): return
        texto = combo.get().lower()
        if not texto:
            combo['values'] = nombres_provs
        else:
            filtrados = [p for p in nombres_provs if p.lower().startswith(texto)]
            combo['values'] = filtrados
            if filtrados:
                combo.event_generate('<Down>')

    combo = ttk.Combobox(dialog, values=nombres_provs, font=st.FONT_INPUT)
    combo.pack(fill="x", pady=5)
    combo.bind("<KeyRelease>", filtrar_provs)

    def confirmar_borrado():
        nombre_prov = combo.get()
        if not nombre_prov:
            messagebox.showwarning("Atención", "Debe seleccionar un proveedor.", parent=dialog)
            return
        
        proveedor_id = proveedor_map[nombre_prov]
        
        msg = (f"¡¡¡ATENCIÓN!!!\n\n"
               f"¿Está 100% seguro de que desea eliminar TODOS los productos del proveedor '{nombre_prov}'?\n\n"
               "Esta acción es IRREVERSIBLE.")
        
        if messagebox.askyesno("Confirmación Final Requerida", msg, icon='error', parent=dialog):
            try:
                conn = database.conectar()
                cur = conn.cursor()
                cur.execute("DELETE FROM productos WHERE proveedor_id = %s", (proveedor_id,))
                conn.commit()
                eliminados = cur.rowcount
                conn.close()
                messagebox.showinfo("Éxito", f"Se eliminaron {eliminados} productos de '{nombre_prov}'.", parent=ventana)
                dialog.destroy()
                cargar_productos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron eliminar los productos: {e}", parent=dialog)

    btn_confirmar = tk.Button(dialog, text="ELIMINAR PRODUCTOS", command=confirmar_borrado, **st.estilo_boton(st.RED_ERROR))
    btn_confirmar.pack(fill="x", pady=15)

def on_tabla_click(event):
    """Manejador de clics en la tabla para editar o eliminar."""
    if tabla.identify_region(event.x, event.y) != "cell": return

    columna_id_str = tabla.identify_column(event.x)
    item_id = tabla.identify_row(event.y)
    if not item_id: return
        
    valores = tabla.item(item_id, 'values')
    
    if columna_id_str == "#7": 
        cargar_datos_para_editar(item_id)
    elif columna_id_str == "#8": 
        eliminar_producto_por_id(item_id, valores[1]) # Pasamos ID y descripción

# --- FUNCIONES PARA BUSCADOR EN FORMULARIO DE EDICIÓN ---

def buscar_productos_para_edicion(termino):
    """Busca productos por descripción o código para el autocompletado de edición."""
    conn = database.conectar()
    cursor = conn.cursor()
    tokens = _normalize_python_string_for_search(termino).split()
    if not tokens: return []

    norm_desc = _normalize_string_for_sql_search("descripcion")
    norm_cod = _normalize_string_for_sql_search("codigo_proveedor")
    
    cond_desc = " AND ".join([f"{norm_desc} LIKE %s" for _ in tokens])
    cond_cod = " AND ".join([f"{norm_cod} LIKE %s" for _ in tokens])

    query = f"SELECT id, codigo_proveedor, descripcion FROM productos WHERE (({cond_desc}) OR ({cond_cod})) ORDER BY descripcion LIMIT 15"
    
    params = [f"%{t}%" for t in tokens] * 2
    cursor.execute(query, params) # Use %s placeholders
    resultados = cursor.fetchall()
    conn.close()
    return resultados

def actualizar_sugerencias_edicion(event=None):
    """Actualiza la lista de sugerencias debajo del campo de descripción."""
    if event.keysym in ('Down', 'Up', 'Return', 'Escape', 'Tab'):
        return

    texto = ent_desc.get().strip()
    
    lista_sugerencias_edicion.delete(0, tk.END)
    if len(texto) < 2:
        lista_sugerencias_edicion.place_forget()
        return

    productos = buscar_productos_para_edicion(texto)
    if productos:
        sugerencias_map.clear()
        
        for p_id, cod, desc in productos:
            display_text = f"{cod} | {desc}"
            lista_sugerencias_edicion.insert(tk.END, display_text)
            sugerencias_map[display_text] = p_id

        # Posicionar la lista de sugerencias usando coordenadas relativas a la ventana de la pestaña
        x_root = ent_desc.winfo_rootx() - ventana.winfo_rootx()
        y_root = ent_desc.winfo_rooty() - ventana.winfo_rooty()
        
        lista_sugerencias_edicion.place(x=x_root, 
                                        y=y_root + ent_desc.winfo_height(),
                                        width=ent_desc.winfo_width() * 3) # Hacemos la lista 3 veces más ancha
        lista_sugerencias_edicion.lift()
    else:
        lista_sugerencias_edicion.place_forget()

def seleccionar_producto_edicion(event=None):
    """Maneja la selección de un producto de la lista de sugerencias."""
    if not lista_sugerencias_edicion.curselection(): return
    
    seleccion_texto = lista_sugerencias_edicion.get(lista_sugerencias_edicion.curselection())
    lista_sugerencias_edicion.place_forget()
    producto_id_seleccionado = sugerencias_map.get(seleccion_texto)
    if producto_id_seleccionado:
        cargar_datos_para_editar(producto_id_seleccionado)
        ent_costo.focus()

# --- INTERFAZ GRÁFICA ---
def montar_interfaz(parent):
    global ent_desc, ent_costo, ent_coef, btn_guardar, ent_buscar_codigo, ent_buscar_desc, combo_buscar_prov, combo_lista_precios, label_contador, tabla, ventana, lista_sugerencias_edicion
    
    ventana = tk.Frame(parent, bg=st.BG_MAIN)
    # Nota: 'ventana' se usa en eliminar_por_proveedor_dialogo como parent, así que debe ser accesible

    frame_izquierdo = tk.Frame(ventana, bg=st.BG_MAIN, width=350); frame_izquierdo.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=20)
    frame_derecho = tk.Frame(ventana, bg=st.BG_MAIN); frame_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=20, padx=(0, 20))

    # --- Panel Izquierdo (Formulario y Acciones) ---
    # La lista de sugerencias debe ser hija de 'ventana' para poder flotar sobre todo
    lista_sugerencias_edicion = tk.Listbox(ventana, font=st.FONT_NORMAL, height=25, bg=st.BG_CARD, fg="white", selectbackground=st.ACCENT, bd=0)
    lista_sugerencias_edicion.bind('<<ListboxSelect>>', seleccionar_producto_edicion)

    tk.Label(frame_izquierdo, text="EDITAR PRODUCTO", font=st.FONT_TITLE, bg=st.BG_MAIN, fg=st.TEXT_PRIMARY).pack(pady=10, anchor="w")

    frame_form = tk.Frame(frame_izquierdo, bg=st.BG_CARD, padx=20, pady=20); frame_form.pack(fill=tk.X)
    def crear_campo(label, fila):
        tk.Label(frame_form, text=label, font=st.FONT_LABEL, bg=st.BG_CARD, fg=st.TEXT_SECONDARY).grid(row=fila, column=0, sticky="w", pady=8)
        entry = tk.Entry(frame_form, **st.estilo_entrada())
        entry.grid(row=fila, column=1, sticky="ew", padx=10, pady=8)
        return entry
    frame_form.columnconfigure(1, weight=1)
    ent_desc = crear_campo("Descripción:", 0)
    ent_desc.bind('<KeyRelease>', actualizar_sugerencias_edicion)
    ent_costo = crear_campo("Costo Base:", 1)
    ent_coef = crear_campo("Coeficiente:", 2)
    ent_coef.config(state="disabled") # Bloqueado por defecto

    btn_guardar = tk.Button(frame_izquierdo, text="💾 GUARDAR CAMBIOS", command=guardar_producto, **st.estilo_boton()); btn_guardar.pack(fill=tk.X, pady=15)
    btn_guardar.config(state="disabled")

    tk.Frame(frame_izquierdo, height=2, bg=st.BG_CARD).pack(fill=tk.X, pady=20)

    tk.Label(frame_izquierdo, text="ACCIONES MASIVAS", font=st.FONT_TITLE, bg=st.BG_MAIN, fg=st.TEXT_PRIMARY).pack(pady=10, anchor="w")
    btn_eliminar_prov = tk.Button(frame_izquierdo, text="🗑️ Eliminar por Proveedor", command=eliminar_por_proveedor_dialogo, **st.estilo_boton(st.RED_ERROR)); btn_eliminar_prov.pack(fill=tk.X, pady=10)

    # --- Panel Derecho (Buscador y Tabla) ---
    frame_filtros = tk.Frame(frame_derecho, bg=st.BG_MAIN)
    frame_filtros.pack(fill=tk.X, pady=(0, 10))
    
    # 1. Filtro Proveedor
    tk.Label(frame_filtros, text="Fábrica:", font=st.FONT_LABEL, bg=st.BG_MAIN, fg="white").grid(row=0, column=0, sticky="w")
    combo_buscar_prov = ttk.Combobox(frame_filtros, font=st.FONT_INPUT, width=18)
    combo_buscar_prov.grid(row=0, column=1, padx=5, sticky="ew")
    
    # 2. Selector de Lista de Precios
    tk.Label(frame_filtros, text="Lista:", font=st.FONT_LABEL, bg=st.BG_MAIN, fg="white").grid(row=0, column=2, sticky="w", padx=(10, 0))
    combo_lista_precios = ttk.Combobox(frame_filtros, values=["Profesional", "Particular 15%", "Particular 30%"], state="readonly", font=st.FONT_INPUT, width=15)
    combo_lista_precios.set("Profesional")
    combo_lista_precios.grid(row=0, column=3, padx=5, sticky="ew")
    combo_lista_precios.bind("<<ComboboxSelected>>", lambda e: cargar_productos())
    
    # 3. Filtro Código
    tk.Label(frame_filtros, text="Código:", font=st.FONT_LABEL, bg=st.BG_MAIN, fg="white").grid(row=0, column=4, sticky="w", padx=(10, 0))
    ent_buscar_codigo = tk.Entry(frame_filtros, width=12, **st.estilo_entrada())
    ent_buscar_codigo.grid(row=0, column=5, padx=5, sticky="ew")
    
    # 4. Filtro Descripción
    tk.Label(frame_filtros, text="Producto:", font=st.FONT_LABEL, bg=st.BG_MAIN, fg="white").grid(row=0, column=6, sticky="w", padx=(10, 0))
    ent_buscar_desc = tk.Entry(frame_filtros, **st.estilo_entrada())
    ent_buscar_desc.grid(row=0, column=7, padx=5, sticky="ew")
    
    label_contador = tk.Label(frame_filtros, text="Total: 0", font=st.FONT_LABEL, bg=st.BG_MAIN, fg=st.ACCENT)
    label_contador.grid(row=0, column=8, padx=(10, 0))
    
    frame_filtros.columnconfigure(7, weight=1)

    def filtrar_provs_busqueda(event):
        if event.keysym in ('Down', 'Up', 'Return', 'Escape', 'Tab', 'Left', 'Right'): return
        texto = combo_buscar_prov.get().lower()
        if not texto or texto == "todos":
            combo_buscar_prov['values'] = ["TODOS"] + lista_proveedores_cache
        else:
            filtrados = [p for p in lista_proveedores_cache if p.lower().startswith(texto)]
            combo_buscar_prov['values'] = filtrados
            if filtrados:
                combo_buscar_prov.event_generate('<Down>')
    
    def cargar_proveedores_filtro():
        conexion = database.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre FROM proveedores ORDER BY nombre")
        provs = [p[0] for p in cursor.fetchall()]
        conexion.close()
        lista_proveedores_cache.clear()
        lista_proveedores_cache.extend(provs)
        combo_buscar_prov['values'] = ["TODOS"] + provs
        combo_buscar_prov.set("TODOS")

    combo_buscar_prov.bind("<KeyRelease>", filtrar_provs_busqueda)
    combo_buscar_prov.bind("<<ComboboxSelected>>", lambda e: cargar_productos())
    ent_buscar_codigo.bind("<KeyRelease>", lambda e: cargar_productos())
    ent_buscar_desc.bind("<KeyRelease>", lambda e: cargar_productos())
    
    cargar_proveedores_filtro()

    columnas = ("código", "descripción", "proveedor", "costo", "coef", "p_venta", "editar", "eliminar")
    
    # Frame contenedor para tabla y scrollbar
    frame_tabla = tk.Frame(frame_derecho, bg=st.BG_MAIN)
    frame_tabla.pack(fill=tk.BOTH, expand=True)

    # Agregamos barras de desplazamiento tanto vertical como horizontal
    scroll_v = ttk.Scrollbar(frame_tabla, orient="vertical")
    scroll_h = ttk.Scrollbar(frame_derecho, orient="horizontal")
    
    tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings", 
                         yscrollcommand=scroll_v.set, xscrollcommand=scroll_h.set)
    
    scroll_v.config(command=tabla.yview)
    scroll_h.config(command=tabla.xview)
    
    scroll_v.pack(side=tk.RIGHT, fill=tk.Y)
    tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll_h.pack(fill=tk.X)

    # Definir los encabezados amigables para que se entienda qué es cada columna
    cabeceras = {
        "código": "CÓDIGO", "descripción": "PRODUCTO", 
        "proveedor": "FÁBRICA", "costo": "COSTO", "coef": "COEF.", 
        "p_venta": "P. VENTA", "editar": "✏️", "eliminar": "🗑️"
    }
    for col in columnas:
        tabla.heading(col, text=cabeceras.get(col, col.upper()))

    # Ajuste de anchos de columnas
    tabla.column("código", width=90)
    tabla.column("descripción", width=500) # Mucho más espacio para el nombre del producto
    tabla.column("proveedor", width=120)
    tabla.column("costo", width=80, anchor="e")
    tabla.column("coef", width=50, anchor="center")
    tabla.column("p_venta", width=110, anchor="e")
    tabla.column("editar", width=40, anchor="center")
    tabla.column("eliminar", width=40, anchor="center")

    tabla.bind("<Button-1>", on_tabla_click)
    cargar_productos()
    
    return ventana

if __name__ == '__main__':
    root = tk.Tk()
    st.aplicar_estilo_ventana(root)
    app = montar_interfaz(root)
    app.pack(fill="both", expand=True)
    root.mainloop()