import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
from datetime import datetime
from fpdf import FPDF
import styles as st # Importamos los estilos
import database # Importamos para obtener la ruta

# --- Funciones Auxiliares para Normalización de Búsqueda ---
def _normalize_string_for_sql_search(column_name):
    """Genera un fragmento SQL para normalizar una cadena para búsqueda.
    Elimina espacios, guiones, guiones bajos, barras y acentos comunes en español.
    """
    # Primero pasamos a minúsculas para que los REPLACE de acentos funcionen con mayúsculas acentuadas
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

# Variables globales
carrito = []
total_sin_descuento = 0.0
combo_lista_precios = None # Nuevo selector de lista de precios
lista_proveedores_cache = [] # Cache para filtrado
tabla_busqueda = None # Tabla de resultados en el paso 2
label_subtotal_carrito = None # Nuevo label para el subtotal del carrito
var_tarjeta = None # Variable para el recargo de tarjeta
producto_id_seleccionado = None
codigo_seleccionado = "" # Se mantiene solo para el label visual
desc_seleccionada = None # Variable de control visual

# --- FUNCIONES DE LÓGICA ---

def obtener_clientes():
    conexion = database.conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre FROM clientes ORDER BY nombre ASC")
    filas = cursor.fetchall()
    conexion.close()
    return [f[0] for f in filas]

def obtener_proveedores_lista():
    conexion = database.conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre FROM proveedores ORDER BY nombre ASC")
    filas = cursor.fetchall()
    conexion.close()
    global lista_proveedores_cache
    lista_proveedores_cache = [f[0] for f in filas]
    return lista_proveedores_cache

def buscar_productos_db(termino="", filtro_proveedor=None, filtro_codigo=""):
    conexion = database.conectar()
    cursor = conexion.cursor()
    
    query = '''
        SELECT p.id, p.codigo_proveedor, p.descripcion, pr.nombre,
               p.costo_base, p.coeficiente_ganancia, p.iva,
               pr.descuento_global, pr.incremento_global
        FROM productos p
        JOIN proveedores pr ON p.proveedor_id = pr.id
        WHERE p.estado = 'ACTIVO'
    '''
    args = []

    if filtro_codigo:
        tokens = _normalize_python_string_for_search(filtro_codigo).split()
        for t in tokens:
            query += f" AND {_normalize_string_for_sql_search('p.codigo_proveedor')} LIKE %s"
            args.append(f'%{t}%')

    if termino:
        tokens = _normalize_python_string_for_search(termino).split()
        for t in tokens:
            query += f" AND {_normalize_string_for_sql_search('p.descripcion')} LIKE %s"
            args.append(f'%{t}%')

    if filtro_proveedor:
        query += " AND pr.nombre = %s"
        args.append(filtro_proveedor)

    query += " ORDER BY p.descripcion ASC"

    cursor.execute(query, tuple(args))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def obtener_multiplicador_precio():
    """Devuelve el factor de multiplicación según la lista seleccionada"""
    if not combo_lista_precios: return 1.0
    seleccion = combo_lista_precios.get()
    
    if "15%" in seleccion:
        return 1.15
    elif "30%" in seleccion:
        return 1.30
    else:
        return 1.0 # Profesional (Precio de lista estándar)

def actualizar_total_visual():
    global total_sin_descuento
    
    multiplicador_tarjeta = 1.10 if var_tarjeta.get() else 1.0
    total_final = total_sin_descuento * multiplicador_tarjeta
    
    if total_sin_descuento == 0:
        label_total.config(text="TOTAL: $ -", fg=st.ACCENT)
        label_subtotal_carrito.config(text="SUBTOTAL CARRITO: $ 0.00")
    else:
        label_total.config(text=f"TOTAL: $ {total_final:.2f}", fg="darkgreen")
        label_subtotal_carrito.config(text=f"SUBTOTAL CARRITO: $ {total_sin_descuento:.2f}")

    # Gestionar Renglón de Total en la Tabla
    if tabla.exists("total_row"):
        tabla.delete("total_row")
    
    if total_sin_descuento > 0:
        # Insertamos el renglón al final con un estilo destacado (tag)
        tabla.insert("", "end", iid="total_row", values=(
            "", ">> TOTAL PRODUCTOS <<", "", "", f"$ {total_sin_descuento:.2f}", "", ""
        ), tags=('total_tag',))

def recalcular_carrito(event=None):
    """Recalcula los precios de todo el carrito cuando se cambia la lista de precios"""
    global total_sin_descuento
    
    # Limpiamos la tabla visual y el total
    for item in tabla.get_children():
        tabla.delete(item)
    total_sin_descuento = 0.0

    multiplicador = obtener_multiplicador_precio()

    # Recorremos el carrito y actualizamos precios
    for item in carrito:
        # Recuperamos el precio base original que guardamos
        precio_base = item['precio_base_lista']
        
        # Calculamos nuevo precio final
        nuevo_precio_unitario = precio_base * multiplicador
        nuevo_subtotal = nuevo_precio_unitario * item['cantidad']
        
        # Actualizamos el diccionario del carrito
        item['precio_unitario'] = nuevo_precio_unitario
        
        # Re-insertamos en la tabla visual
        # Necesitamos recuperar codigo y descripcion. 
        # Nota: Idealmente deberíamos guardarlos en el dict carrito para no consultar DB,
        # pero para mantener compatibilidad rápida, usaremos los datos que ya tenemos o consultamos si faltan.
        # En este código, 'carrito' solo tiene IDs. 
        # Para evitar re-consultar DB masivamente, usaremos los valores almacenados en 'item' si los agregamos.
        
        # Mejor estrategia: Al agregar al carrito, guardamos descripcion y codigo tambien.
        # Ver funcion agregar_producto abajo modificada.

        tabla.insert("", "end", values=(item['codigo'], item['descripcion'], item['cantidad'], f"$ {nuevo_precio_unitario:.2f}", f"$ {nuevo_subtotal:.2f}", "📎", "🗑️"))
        total_sin_descuento += nuevo_subtotal

    actualizar_total_visual()


def agregar_producto(event=None):
    global total_sin_descuento, producto_id_seleccionado, codigo_seleccionado
    if producto_id_seleccionado is None: return

    try:
        if not entrada_cantidad.get().strip():
            return
        cantidad = int(entrada_cantidad.get().strip())
    except ValueError:
        messagebox.showerror("Error", "La cantidad debe ser un número.")
        return

    if cantidad <= 0: return

    conexion = database.conectar()
    cursor = conexion.cursor()
    query = '''
        SELECT p.id, p.descripcion, p.costo_base, p.coeficiente_ganancia, p.iva, pr.descuento_global, pr.incremento_global, p.codigo_proveedor
        FROM productos p
        JOIN proveedores pr ON p.proveedor_id = pr.id
        WHERE p.id = %s
    '''
    cursor.execute(query, (producto_id_seleccionado,))
    producto = cursor.fetchone()
    conexion.close()

    if producto:
        prod_id, desc, costo, coef, iva, desc_g, inc_g, cod_prov = producto
        # Precio base (Profesional / Lista) aplicando el descuento del proveedor
        precio_base = costo * (1 - (desc_g or 0)) * (1 + (inc_g or 0)) * coef * (1 + iva)
        
        # Precio final con el aumento seleccionado
        multiplicador = obtener_multiplicador_precio()
        precio_unitario = precio_base * multiplicador
        
        subtotal = precio_unitario * cantidad
        
        # Guardamos precio_base_lista para poder recalcular si cambiamos de categoria
        carrito.append({'prod_id': prod_id, 'cantidad': cantidad, 'precio_unitario': precio_unitario, 'precio_base_lista': precio_base, 'codigo': cod_prov, 'descripcion': desc})
        
        # INSERTAMOS EN LA TABLA CON LA COLUMNA SUBTOTAL
        tabla.insert("", "end", values=(cod_prov, desc, cantidad, f"$ {precio_unitario:.2f}", f"$ {subtotal:.2f}", "📎", "🗑️"))
        
        total_sin_descuento += subtotal
        actualizar_total_visual()
        
        producto_id_seleccionado = None
        codigo_seleccionado = ""
        label_prod_sel.config(text="")
        entrada_cantidad.delete(0, tk.END)
        ent_p2_desc.focus_set() # Volver al buscador automáticamente
    else:
        messagebox.showwarning("No encontrado", f"El código '{codigo}' no existe.")

def borrar_item_especifico(item_id):
    """Elimina el producto seleccionado de la tabla y resta su valor del total"""
    global total_sin_descuento
    valores = tabla.item(item_id, "values")
    subtotal_item = float(valores[4].replace("$ ", ""))
    total_sin_descuento -= subtotal_item
    
    indice = tabla.index(item_id)
    if indice < len(carrito):
        carrito.pop(indice)
        
    tabla.delete(item_id)
    
    actualizar_total_visual()

def generar_ticket_pdf(presupuesto_id=None, vista_previa=False):
    """Genera un PDF con el detalle de la venta. Si presupuesto_id es None, usa el carrito actual."""
    try:
        if not vista_previa and presupuesto_id:
            conexion = database.conectar()
            cursor = conexion.cursor()
            cursor.execute("SELECT cliente_nombre, fecha, total, cliente_tipo FROM presupuestos WHERE id = %s", (presupuesto_id,))
            datos_venta = cursor.fetchone()
            cursor.execute('''
                SELECT p.descripcion, d.cantidad, d.precio_unitario_congelado 
                FROM presupuesto_detalles d
                JOIN productos p ON d.producto_id = p.id
                WHERE d.presupuesto_id = %s
            ''', (presupuesto_id,))
            items = cursor.fetchall()
            conexion.close()
            if not datos_venta: return
            cliente, fecha, total, tipo_cliente = datos_venta
            ticket_num = str(presupuesto_id)
        else:
            cliente = combo_cliente.get() or "Consumidor Final"
            fecha = datetime.now().strftime("%d/%m/%Y")
            total = total_sin_descuento
            tipo_cliente = combo_lista_precios.get()
            items = [(i['descripcion'], i['cantidad'], i['precio_unitario']) for i in carrito]
            ticket_num = "PREVIEW"
        
        # 3. Construimos el PDF (Formato Ticket 58mm)
        # Calculamos altura dinámica: Base 80mm + 10mm por producto
        altura_ticket = 80 + (len(items) * 10)
        
        pdf = FPDF(orientation='P', unit='mm', format=(58, altura_ticket))
        pdf.set_margins(2, 2, 2) # Márgenes estrechos (2mm)
        pdf.add_page()
        
        # Encabezado
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 5, "Herrajes Santa Fe", ln=True, align="C")
        pdf.set_font("Arial", size=8)
        pdf.cell(0, 5, "Comprobante de Venta", ln=True, align="C")
        pdf.ln(2)
        
        # Datos Cliente
        pdf.set_font("Arial", "B", 8)
        pdf.cell(0, 4, f"Ticket N: {ticket_num}", ln=True)
        pdf.cell(0, 4, f"Fecha: {fecha}", ln=True)
        pdf.multi_cell(0, 4, f"Cliente: {cliente}")
        pdf.ln(2)
        
        # Tabla de Productos
        # Anchos ajustados para 58mm: Desc(22) + Cant(6) + Precio(12) + Total(14) = 54mm
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("Arial", "B", 6)
        pdf.cell(22, 5, "Desc", 1, 0, 'C', 1)
        pdf.cell(6, 5, "Cant", 1, 0, 'C', 1)
        pdf.cell(12, 5, "Precio", 1, 0, 'C', 1)
        pdf.cell(14, 5, "Total", 1, 1, 'C', 1)
        
        pdf.set_font("Arial", size=6)
        for desc, cant, precio in items:
            subtotal = cant * precio
            # Recortar descripción para que entre en una línea corta
            desc_fmt = (desc[:12] + '..') if len(desc) > 14 else desc
            
            pdf.cell(22, 5, desc_fmt, 1)
            pdf.cell(6, 5, f"{cant:g}", 1, 0, 'C')
            pdf.cell(12, 5, f"{precio:.2f}", 1, 0, 'R')
            pdf.cell(14, 5, f"{subtotal:.2f}", 1, 1, 'R')
            
        # Total
        pdf.ln(4)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "TOTAL:", 0, 1, 'R') # Mover "TOTAL" a su propia línea
        pdf.set_font("Arial", "B", 14) # Aumentamos el tamaño del número
        pdf.cell(0, 8, f"$ {total:.2f}", 0, 1, 'R') # Valor total en la siguiente línea con más altura

        # Mensaje condicional según categoría
        if tipo_cliente and "Profesional" in tipo_cliente:
            pdf.ln(2)
            pdf.set_font("Arial", "I", 6)
            pdf.cell(0, 4, "** Descuento Cliente Frecuente / Gremio **", ln=True, align="C")

        # Pie
        pdf.ln(4)
        pdf.set_font("Arial", "I", 7)
        pdf.cell(0, 4, "Gracias por su compra", ln=True, align="C")
        
        # 4. Guardar y Abrir
        if not os.path.exists("comprobantes"):
            os.makedirs("comprobantes")
        
        nombre_archivo = f"ticket_{ticket_num}.pdf"
        ruta_pdf = os.path.abspath(f"comprobantes/{nombre_archivo}")
        pdf.output(ruta_pdf)
        
        # Abrir archivo (Windows)
        os.startfile(ruta_pdf)
        
    except Exception as e:
        messagebox.showerror("Error PDF", f"No se pudo generar el PDF: {e}")

def guardar_presupuesto(imprimir=False):
    global total_sin_descuento, carrito
    if not carrito: 
        messagebox.showwarning("Atención", "El carrito está vacío.")
        return
    
    total_final = total_sin_descuento # El total ya incluye los aumentos/precios finales
    
    # Aplicamos recargo de tarjeta si corresponde
    if var_tarjeta.get():
        total_final *= 1.10

    try:
        nombre_cliente = combo_cliente.get().strip() or "Consumidor Final"
        tipo_cliente = combo_lista_precios.get() + (" + TARJETA" if var_tarjeta.get() else "")
        
        conexion = database.conectar()
        cursor = conexion.cursor()
        # Guardamos el tipo de cliente (Profesional, Particular 15%, etc)
        cursor.execute("INSERT INTO presupuestos (cliente_nombre, total, cliente_tipo) VALUES (%s, %s, %s) RETURNING id", (nombre_cliente, float(total_final), tipo_cliente))
        presupuesto_id = cursor.fetchone()[0]
        
        for item in carrito:
            cursor.execute('INSERT INTO presupuesto_detalles (presupuesto_id, producto_id, cantidad, precio_unitario_congelado) VALUES (%s, %s, %s, %s)',
                           (presupuesto_id, item['prod_id'], item['cantidad'], item['precio_unitario']))
        conexion.commit()
        conexion.close()

        if imprimir:
            generar_ticket_pdf(presupuesto_id)
        
        messagebox.showinfo("Éxito", f"Presupuesto N° {presupuesto_id} guardado.")
        cancelar_venta()
    except Exception as e:
        messagebox.showerror("Error al guardar", f"No se pudo guardar la venta: {e}")

def cancelar_venta():
    global total_sin_descuento, carrito, codigo_seleccionado, var_tarjeta
    carrito.clear()
    total_sin_descuento = 0.0
    codigo_seleccionado = ""
    if var_tarjeta: var_tarjeta.set(False)
    label_prod_sel.config(text="")
    label_feedback_p2.config(text="")
    actualizar_total_visual()
    for row in tabla.get_children(): tabla.delete(row)
    entrada_cantidad.delete(0, tk.END)

def buscar_p2(_=None):
    """Lógica de búsqueda integrada en Paso 2"""
    for row in tabla_busqueda.get_children(): 
        tabla_busqueda.delete(row)
    
    prov = None if combo_p2_prov.get() == "TODOS" else combo_p2_prov.get()
    res = buscar_productos_db(termino=ent_p2_desc.get(), filtro_proveedor=prov, filtro_codigo=ent_p2_cod.get())
    
    for r in res:
        p_id, cod, desc, prov_nom, costo, coef, iva, desc_g, inc_g = r
        precio_prof = costo * (1 - (desc_g or 0)) * (1 + (inc_g or 0)) * coef * (1 + iva)
        # El ID se guarda en el 'iid' del Treeview (invisible para el usuario)
        tabla_busqueda.insert("", "end", iid=p_id, values=(cod, desc, prov_nom, f"$ {precio_prof:.2f}"))

def seleccionar_p2(event=None):
    """Selecciona un producto de la tabla de búsqueda"""
    global producto_id_seleccionado, codigo_seleccionado
    sel = tabla_busqueda.selection()
    if sel:
        producto_id_seleccionado = sel[0] # El iid que es el ID de la DB
        val = tabla_busqueda.item(sel[0], 'values')
        codigo_seleccionado = val[0]
        label_prod_sel.config(text=f"Seleccionado: {val[0]} | {val[1][:40]}...")
        entrada_cantidad.focus_set()

def filtrar_provs_p2(event):
    if event.keysym in ('Down', 'Up', 'Return', 'Escape', 'Tab', 'Left', 'Right'): return
    texto = combo_p2_prov.get().lower()
    if not texto or texto == "todos":
        combo_p2_prov['values'] = ["TODOS"] + lista_proveedores_cache
    else:
        filtrados = [p for p in lista_proveedores_cache if p.lower().startswith(texto)]
        combo_p2_prov['values'] = filtrados
        if filtrados:
            combo_p2_prov.event_generate('<Down>')

def on_tabla_click(event):
    region = tabla.identify_region(event.x, event.y)
    if region != "cell": return
    col = tabla.identify_column(event.x)
    item_id = tabla.identify_row(event.y)
    if not item_id or item_id == "total_row": return

    if col == "#6": # Modificar (Clip)
        valores = tabla.item(item_id, 'values')
        nueva_cant = simpledialog.askinteger("Modificar Cantidad", f"Producto: {valores[1]}\nIngrese nueva cantidad:", initialvalue=int(valores[2]))
        if nueva_cant is not None and nueva_cant > 0:
            idx = tabla.index(item_id)
            carrito[idx]['cantidad'] = nueva_cant
            recalcular_carrito()
    elif col == "#7": # Eliminar (Tachito)
        borrar_item_especifico(item_id)

# --- INTERFAZ ---
def montar_interfaz(parent):
    global combo_cliente, entrada_cantidad, tabla, label_total, combo_lista_precios, label_prod_sel, var_tarjeta, label_subtotal_carrito
    global tabla_busqueda, ent_p2_cod, ent_p2_desc, combo_p2_prov # ent_p2_cod ya no es dummy
    
    ventana = tk.Frame(parent, bg=st.BG_MAIN)
    var_tarjeta = tk.BooleanVar(value=False)

    # --- CABECERA: CLIENTE Y CONFIGURACIÓN ---
    f_header = tk.Frame(ventana, bg=st.BG_CARD, padx=15, pady=10)
    f_header.pack(fill=tk.X, padx=15, pady=(10, 5))

    tk.Label(f_header, text="CLIENTE:", font=st.FONT_LABEL, bg=st.BG_CARD, fg=st.TEXT_SECONDARY).pack(side=tk.LEFT, padx=5)
    combo_cliente = ttk.Combobox(f_header, values=obtener_clientes(), font=st.FONT_INPUT, width=30)
    combo_cliente.pack(side=tk.LEFT, padx=5)

    tk.Label(f_header, text="LISTA:", font=st.FONT_LABEL, bg=st.BG_CARD, fg=st.TEXT_SECONDARY).pack(side=tk.LEFT, padx=(20, 5))
    combo_lista_precios = ttk.Combobox(f_header, values=["Profesional", "Particular 15%", "Particular 30%"], state="readonly", font=st.FONT_INPUT, width=15)
    combo_lista_precios.set("Particular 15%")
    combo_lista_precios.pack(side=tk.LEFT, padx=5)
    combo_lista_precios.bind("<<ComboboxSelected>>", recalcular_carrito)

    chk_tarjeta = tk.Checkbutton(f_header, text="TARJETA (+10%)", variable=var_tarjeta, 
                                 command=actualizar_total_visual, bg=st.BG_CARD, fg=st.ACCENT, 
                                 selectcolor=st.BG_MAIN, font=st.FONT_LABEL, activebackground=st.BG_CARD)
    chk_tarjeta.pack(side=tk.LEFT, padx=20)

    # --- BOTONES DE ACCIÓN RÁPIDA (ARRIBA A LA DERECHA) ---
    f_acciones_header = tk.Frame(f_header, bg=st.BG_CARD)
    f_acciones_header.pack(side=tk.RIGHT)

    tk.Button(f_acciones_header, text="❌ CANCELAR", command=cancelar_venta, **st.estilo_boton(st.RED_ERROR)).pack(side=tk.RIGHT, padx=5)
    tk.Button(f_acciones_header, text="💾 GUARDAR", command=lambda: guardar_presupuesto(False), **st.estilo_boton(st.ACCENT)).pack(side=tk.RIGHT, padx=5)
    tk.Button(f_acciones_header, text="💾🖨️ IMPRIMIR", command=lambda: guardar_presupuesto(True), **st.estilo_boton()).pack(side=tk.RIGHT, padx=5)

    # --- SECCIÓN BÚSQUEDA (Panel Superior) ---
    f_busqueda = tk.Frame(ventana, bg=st.BG_MAIN, padx=15)
    f_busqueda.pack(fill=tk.X, pady=5)
    
    # Usamos grid para mejor control de los campos de búsqueda
    f_busqueda.columnconfigure(1, weight=1) # Columna para ent_p2_cod
    f_busqueda.columnconfigure(3, weight=2) # Columna para ent_p2_desc

    tk.Label(f_busqueda, text="CÓDIGO:", font=st.FONT_LABEL, bg=st.BG_MAIN, fg="white").grid(row=0, column=0, padx=5, sticky="w")
    ent_p2_cod = tk.Entry(f_busqueda, font=st.FONT_INPUT, bg=st.BG_INPUT, fg="white", bd=0)
    ent_p2_cod.grid(row=0, column=1, padx=5, sticky="ew")
    ent_p2_cod.bind("<KeyRelease>", buscar_p2)

    tk.Label(f_busqueda, text="DESCRIPCIÓN:", font=st.FONT_LABEL, bg=st.BG_MAIN, fg="white").grid(row=0, column=2, padx=(15, 5), sticky="w")
    ent_p2_desc = tk.Entry(f_busqueda, font=st.FONT_INPUT, bg=st.BG_INPUT, fg="white", bd=0)
    ent_p2_desc.grid(row=0, column=3, padx=5, sticky="ew")
    ent_p2_desc.bind("<KeyRelease>", buscar_p2)

    tk.Label(f_busqueda, text="FÁBRICA:", font=st.FONT_LABEL, bg=st.BG_MAIN, fg="white").grid(row=0, column=4, padx=(15, 5), sticky="w")
    combo_p2_prov = ttk.Combobox(f_busqueda, values=["TODOS"] + obtener_proveedores_lista(), font=st.FONT_INPUT, width=15)
    combo_p2_prov.set("TODOS")
    combo_p2_prov.grid(row=0, column=5, padx=5, sticky="ew")
    combo_p2_prov.bind("<<ComboboxSelected>>", buscar_p2)
    combo_p2_prov.bind("<KeyRelease>", filtrar_provs_p2) # Re-añadido para filtrar sugerencias

    # Tabla de Resultados de Búsqueda (Compacta)
    cols_b = ("cod", "desc", "prov", "precio")
    tabla_busqueda = ttk.Treeview(ventana, columns=cols_b, show="headings", height=5)
    tabla_busqueda.heading("cod", text="CÓDIGO"); tabla_busqueda.heading("desc", text="DESCRIPCIÓN"); tabla_busqueda.heading("prov", text="PROVEEDOR"); tabla_busqueda.heading("precio", text="P. PROFESIONAL")
    tabla_busqueda.column("cod", width=100); tabla_busqueda.column("desc", width=400); tabla_busqueda.column("prov", width=150); tabla_busqueda.column("precio", width=120, anchor="e")
    tabla_busqueda.pack(fill=tk.X, padx=15, pady=5)
    tabla_busqueda.bind("<<TreeviewSelect>>", seleccionar_p2)
    tabla_busqueda.bind("<Double-1>", lambda e: entrada_cantidad.focus_set())

    # --- BARRA DE ACCIÓN: CANTIDAD Y AÑADIR ---
    f_add = tk.Frame(ventana, bg=st.BG_MAIN, pady=5)
    f_add.pack(fill=tk.X, padx=15)
    
    label_prod_sel = tk.Label(f_add, text="", font=st.FONT_NORMAL, fg=st.ACCENT, bg=st.BG_MAIN)
    label_prod_sel.pack(side=tk.LEFT, padx=10)
    
    tk.Label(f_add, text="CANT:", bg=st.BG_MAIN, fg="white").pack(side=tk.LEFT, padx=5)
    entrada_cantidad = tk.Entry(f_add, width=6, font=st.FONT_INPUT, justify="center")
    entrada_cantidad.pack(side=tk.LEFT, padx=5)
    entrada_cantidad.bind("<Return>", agregar_producto)
    tk.Button(f_add, text="➕ AÑADIR", command=agregar_producto, **st.estilo_boton(st.ACCENT)).pack(side=tk.LEFT, padx=10)

    # --- TABLA DE CARRITO (Panel Inferior - Expandible) ---
    columnas = ("cod", "desc", "cant", "p_unit", "subtotal", "mod", "del")
    tabla = ttk.Treeview(ventana, columns=columnas, show="headings")
    tabla.heading("cod", text="CÓDIGO"); tabla.heading("desc", text="DESCRIPCIÓN"); tabla.heading("cant", text="CANT."); tabla.heading("p_unit", text="P. UNITARIO"); tabla.heading("subtotal", text="SUBTOTAL"); tabla.heading("mod", text="📎"); tabla.heading("del", text="🗑️")
    tabla.column("cod", width=100); tabla.column("desc", width=400); tabla.column("cant", width=80, anchor="center"); tabla.column("p_unit", width=120, anchor="e"); tabla.column("subtotal", width=120, anchor="e"); tabla.column("mod", width=40, anchor="center"); tabla.column("del", width=40, anchor="center")
    tabla.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
    tabla.bind("<Button-1>", on_tabla_click)
    tabla.tag_configure('total_tag', background=st.BG_CARD, foreground=st.ACCENT, font=st.FONT_LABEL)
    
    # Nuevo label para el subtotal del carrito
    label_subtotal_carrito = tk.Label(ventana, text="SUBTOTAL CARRITO: $ 0.00", font=st.FONT_LABEL, bg=st.BG_MAIN, fg=st.TEXT_PRIMARY)
    label_subtotal_carrito.pack(fill=tk.X, padx=15, pady=(0, 5), anchor="e")

    # --- PIE: TOTALES Y CIERRE ---
    f_footer = tk.Frame(ventana, bg=st.BG_MAIN, pady=10)
    f_footer.pack(fill=tk.X, padx=15)
    
    label_total = tk.Label(f_footer, text="TOTAL: $ -", font=("Inter", 24, "bold"), fg=st.ACCENT, bg=st.BG_MAIN)
    label_total.pack(side=tk.LEFT)

    f_acciones_finales = tk.Frame(f_footer, bg=st.BG_MAIN)
    f_acciones_finales.pack(side=tk.RIGHT)

    tk.Button(f_acciones_finales, text="❌ CANCELAR TODO", command=cancelar_venta, **st.estilo_boton(st.RED_ERROR)).pack(side=tk.RIGHT, padx=5)
    tk.Button(f_acciones_finales, text="💾 GUARDAR VENTA", command=lambda: guardar_presupuesto(False), **st.estilo_boton(st.ACCENT)).pack(side=tk.RIGHT, padx=5)
    tk.Button(f_acciones_finales, text="💾🖨️ GUARDAR E IMPRIMIR", command=lambda: guardar_presupuesto(True), **st.estilo_boton()).pack(side=tk.RIGHT, padx=5)

    return ventana

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("1000x800")
    st.aplicar_estilo_ventana(root)
    app = montar_interfaz(root)
    app.pack(fill="both", expand=True)
    root.mainloop()