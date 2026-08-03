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
    Elimina espacios, tildes y símbolos comunes de separación.
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
    if not text: return ""
    text = text.lower()
    for char in [" ", "-", "_", "/", ".", ",", "(", ")", "[", "]", "*", "+", "|", ":", ";"]:
        text = text.replace(char, "")
    replacements = [('á','a'),('é','e'),('í','i'),('ó','o'),('ú','u'),('ü','u'),('ñ','n'),('ç','c')]
    for old, new in replacements:
        text = text.replace(old, new)
    return text

# Variables globales
carrito = []
total_sin_descuento = 0.0
combo_lista_precios = None
lista_proveedores_cache = []
tabla_busqueda = None
label_subtotal_carrito = None
var_tarjeta = None
producto_id_seleccionado = None
codigo_seleccionado = ""
desc_seleccionada = None

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
            query += f" AND {_normalize_string_for_sql_search('p.codigo_proveedor')} LIKE ?"
            args.append(f'%{t}%')

    if termino:
        tokens = _normalize_python_string_for_search(termino).split()
        for t in tokens:
            query += f" AND {_normalize_string_for_sql_search('p.descripcion')} LIKE ?"
            args.append(f'%{t}%')

    if filtro_proveedor:
        query += " AND pr.nombre = ?"
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
        return 1.0

def actualizar_total_visual():
    global total_sin_descuento
    
    multiplicador_tarjeta = 1.10 if var_tarjeta.get() else 1.0
    total_final = round(total_sin_descuento * multiplicador_tarjeta, 2)
    
    if total_sin_descuento <= 0:
        label_total.config(text="TOTAL: $ -", fg=st.ACCENT)
        label_subtotal_carrito.config(text="SUBTOTAL CARRITO: $ 0.00")
    else:
        label_total.config(text=f"TOTAL: $ {total_final:.2f}", fg="darkgreen")
        label_subtotal_carrito.config(text=f"SUBTOTAL CARRITO: $ {total_sin_descuento:.2f}")

    if tabla.exists("total_row"):
        tabla.delete("total_row")
    
    if total_sin_descuento > 0:
        texto_total = ">> TOTAL (CON TARJETA) <<" if var_tarjeta.get() else ">> TOTAL PRODUCTOS <<"
        valor_mostrar = total_final if var_tarjeta.get() else total_sin_descuento
        tabla.insert("", "end", iid="total_row", values=(
            "", texto_total, "", "", f"$ {valor_mostrar:.2f}", "", ""
        ), tags=('total_tag',))

def recalcular_carrito(event=None):
    """Recalcular precios del carrito"""
    global total_sin_descuento
    
    for item in tabla.get_children():
        tabla.delete(item)
    total_sin_descuento = 0.0

    multiplicador = obtener_multiplicador_precio()

    for item in carrito:
        precio_base = item['precio_base_lista']
        nuevo_precio_unitario = precio_base * multiplicador
        nuevo_subtotal = nuevo_precio_unitario * item['cantidad']
        
        item['precio_unitario'] = nuevo_precio_unitario

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
        WHERE p.id = ?
    '''
    cursor.execute(query, (producto_id_seleccionado,))
    producto = cursor.fetchone()
    conexion.close()

    if producto:
        prod_id, desc, costo, coef, iva, desc_g, inc_g, cod_prov = producto
        precio_base = costo * (1 - (desc_g or 0)) * (1 + (inc_g or 0)) * coef * (1 + iva)
        
        multiplicador = obtener_multiplicador_precio()
        precio_unitario = precio_base * multiplicador
        
        subtotal = precio_unitario * cantidad
        
        carrito.append({'prod_id': prod_id, 'cantidad': cantidad, 'precio_unitario': precio_unitario, 'precio_base_lista': precio_base, 'codigo': cod_prov, 'descripcion': desc})
        
        tabla.insert("", "end", values=(cod_prov, desc, cantidad, f"$ {precio_unitario:.2f}", f"$ {subtotal:.2f}", "📎", "🗑️"))
        
        total_sin_descuento += subtotal
        actualizar_total_visual()
        
        producto_id_seleccionado = None
        codigo_seleccionado = ""
        label_prod_sel.config(text="")
        entrada_cantidad.delete(0, tk.END)
        ent_p2_desc.focus_set()
    else:
        messagebox.showwarning("No encontrado", "El producto no existe.")

def borrar_item_especifico(item_id):
    global total_sin_descuento
    valores = tabla.item(item_id, "values")
    subtotal_item = float(valores[4].replace("$ ", ""))
    total_sin_descuento -= subtotal_item
    
    indice = tabla.index(item_id)
    if indice < len(carrito):
        carrito.pop(indice)
        
    tabla.delete(item_id)
    actualizar_total_visual()

# --- NUEVA FUNCIÓN DE TICKET LIMPIA Y SIN ENJAULADO ---
def generar_ticket_pdf(presupuesto_id=None, vista_previa=False):
    """Genera un PDF con formato de ticket térmico (58mm), descripciones multilínea y sin recuadros."""
    try:
        if not vista_previa and presupuesto_id:
            conexion = database.conectar()
            cursor = conexion.cursor()
            cursor.execute("SELECT cliente_nombre, fecha, total, cliente_tipo FROM presupuestos WHERE id = ?", (presupuesto_id,))
            datos_venta = cursor.fetchone()
            cursor.execute('''
                SELECT p.descripcion, d.cantidad, d.precio_unitario_congelado 
                FROM presupuesto_detalles d
                JOIN productos p ON d.producto_id = p.id
                WHERE d.presupuesto_id = ?
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

        # 1. Ajuste de formato: 58mm de ancho, alto dinámico estimado
        # Estimamos ~10mm por item considerando que pueden ocupar 2 renglones
        altura_ticket = 85 + (len(items) * 12)
        
        pdf = FPDF(orientation='P', unit='mm', format=(58, altura_ticket))
        pdf.set_margins(1.5, 2, 1.5) # Márgenes mínimos laterales (1.5mm)
        pdf.set_auto_page_break(auto=True, margin=2)
        pdf.add_page()
        
        # 2. Encabezado
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 4, "HERRAJES SANTA FE", ln=True, align="C")
        pdf.set_font("Arial", "", 7)
        pdf.cell(0, 4, "Comprobante de Venta", ln=True, align="C")
        
        # Línea separadora limpia
        pdf.set_font("Arial", "", 7)
        pdf.cell(0, 3, "- " * 22, ln=True, align="C")
        
        # 3. Datos del Cliente
        pdf.set_font("Arial", "B", 7)
        pdf.cell(14, 3.5, "Ticket N°:", 0, 0)
        pdf.set_font("Arial", "", 7)
        pdf.cell(0, 3.5, str(ticket_num), ln=True)
        
        pdf.set_font("Arial", "B", 7)
        pdf.cell(14, 3.5, "Fecha:", 0, 0)
        pdf.set_font("Arial", "", 7)
        pdf.cell(0, 3.5, str(fecha), ln=True)
        
        pdf.set_font("Arial", "B", 7)
        pdf.cell(14, 3.5, "Cliente:", 0, 0)
        pdf.set_font("Arial", "", 7)
        pdf.multi_cell(0, 3.5, str(cliente))
        
        # Línea separadora limpia
        pdf.cell(0, 3, "- " * 22, ln=True, align="C")
        
        # 4. Cabecera de Productos (Sin bordes/casilleros)
        pdf.set_font("Arial", "B", 7)
        pdf.cell(8, 4, "Cant", 0, 0, 'L')
        pdf.cell(32, 4, "Descripción", 0, 0, 'L')
        pdf.cell(15, 4, "Total", 0, 1, 'R')
        pdf.cell(0, 2, "- " * 22, ln=True, align="C")
        
        # 5. Lista de Productos
        pdf.set_font("Arial", "", 7)
        for desc, cant, precio in items:
            subtotal = cant * precio
            y_inicial = pdf.get_y()
            
            # Imprime Cantidad a la izquierda
            pdf.cell(8, 3.5, f"{cant:g}", 0, 0, 'L')
            
            # Imprime Descripción con multi_cell para permitir 2 o más renglones
            # Ancho de 32mm para dar espacio a la columna de Total
            pdf.multi_cell(32, 3.5, str(desc), border=0, align='L')
            y_final_desc = pdf.get_y()
            
            # Coloca el Total alineado con la primera línea del producto
            pdf.set_xy(41.5, y_inicial)
            pdf.cell(15, 3.5, f"${subtotal:.2f}", 0, 1, 'R')
            
            # Mueve el cursor al punto más bajo (por si la descripción ocupó 2 o 3 renglones)
            if y_final_desc > pdf.get_y():
                pdf.set_y(y_final_desc)
                
            pdf.ln(1) # Pequeño espacio entre productos
            
        # 6. Totalización
        pdf.cell(0, 2, "- " * 22, ln=True, align="C")
        pdf.ln(1)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(25, 4, "TOTAL:", 0, 0, 'L')
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 4, f"$ {total:.2f}", 0, 1, 'R')
        
        if tipo_cliente and "Profesional" in tipo_cliente:
            pdf.ln(1)
            pdf.set_font("Arial", "I", 6)
            pdf.cell(0, 3, "* Descuento Gremio Aplicado *", ln=True, align="C")

        # Pie
        pdf.ln(3)
        pdf.set_font("Arial", "I", 7)
        pdf.cell(0, 4, "¡Gracias por su compra!", ln=True, align="C")
        
        # Guardar y abrir
        if not os.path.exists("comprobantes"):
            os.makedirs("comprobantes")
        
        nombre_archivo = f"ticket_{ticket_num}.pdf"
        ruta_pdf = os.path.abspath(f"comprobantes/{nombre_archivo}")
        pdf.output(ruta_pdf)
        
        os.startfile(ruta_pdf)
        
    except Exception as e:
        messagebox.showerror("Error PDF", f"No se pudo generar el PDF: {e}")

def guardar_presupuesto(imprimir=False):
    global total_sin_descuento, carrito
    if not carrito: 
        messagebox.showwarning("Atención", "El carrito está vacío.")
        return
    
    total_final = round(total_sin_descuento, 2)
    
    if var_tarjeta.get():
        total_final = round(total_final * 1.10, 2)

    try:
        nombre_cliente = combo_cliente.get().strip() or "Consumidor Final"
        tipo_cliente = combo_lista_precios.get() + (" + TARJETA" if var_tarjeta.get() else "")
        
        conexion = database.conectar()
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO presupuestos (cliente_nombre, total, cliente_tipo) VALUES (?, ?, ?) RETURNING id", (nombre_cliente, float(total_final), tipo_cliente))
        presupuesto_id = cursor.fetchone()[0]
        
        for item in carrito:
            cursor.execute('INSERT INTO presupuesto_detalles (presupuesto_id, producto_id, cantidad, precio_unitario_congelado) VALUES (?, ?, ?, ?)',
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
    try: label_feedback_p2.config(text="")
    except: pass
    actualizar_total_visual()
    for row in tabla.get_children(): tabla.delete(row)
    entrada_cantidad.delete(0, tk.END)
    ent_p2_cod.delete(0, tk.END)
    ent_p2_desc.delete(0, tk.END)

def limpiar_busqueda():
    ent_p2_cod.delete(0, tk.END)
    ent_p2_desc.delete(0, tk.END)
    buscar_p2()

def buscar_p2(_=None):
    for row in tabla_busqueda.get_children(): 
        tabla_busqueda.delete(row)
    
    prov = None if combo_p2_prov.get() == "TODOS" else combo_p2_prov.get()
    res = buscar_productos_db(termino=ent_p2_desc.get(), filtro_proveedor=prov, filtro_codigo=ent_p2_cod.get())
    
    for r in res:
        p_id, cod, desc, prov_nom, costo, coef, iva, desc_g, inc_g = r
        precio_prof = costo * (1 - (desc_g or 0)) * (1 + (inc_g or 0)) * coef * (1 + iva)
        tabla_busqueda.insert("", "end", iid=p_id, values=(cod, desc, prov_nom, f"$ {precio_prof:.2f}"))

def seleccionar_p2(event=None):
    global producto_id_seleccionado, codigo_seleccionado
    sel = tabla_busqueda.selection()
    if sel:
        producto_id_seleccionado = sel[0]
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

    if col == "#6":
        valores = tabla.item(item_id, 'values')
        nueva_cant = simpledialog.askinteger("Modificar Cantidad", f"Producto: {valores[1]}\nIngrese nueva cantidad:", initialvalue=int(valores[2]))
        if nueva_cant is not None and nueva_cant > 0:
            idx = tabla.index(item_id)
            carrito[idx]['cantidad'] = nueva_cant
            recalcular_carrito()
    elif col == "#7":
        borrar_item_especifico(item_id)

# --- INTERFAZ ---
def montar_interfaz(parent):
    global combo_cliente, entrada_cantidad, tabla, label_total, combo_lista_precios, label_prod_sel, var_tarjeta, label_subtotal_carrito
    global tabla_busqueda, ent_p2_cod, ent_p2_desc, combo_p2_prov
    
    ventana = tk.Frame(parent, bg=st.BG_MAIN)
    var_tarjeta = tk.BooleanVar(value=False)

    # CABECERA
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

    # BOTONES DE ACCIÓN RÁPIDA
    f_acciones_header = tk.Frame(f_header, bg=st.BG_CARD)
    f_acciones_header.pack(side=tk.RIGHT)

    tk.Button(f_acciones_header, text="❌ CANCELAR", command=cancelar_venta, **st.estilo_boton(st.RED_ERROR)).pack(side=tk.RIGHT, padx=5)
    tk.Button(f_acciones_header, text="💾 GUARDAR", command=lambda: guardar_presupuesto(False), **st.estilo_boton(st.ACCENT)).pack(side=tk.RIGHT, padx=5)
    tk.Button(f_acciones_header, text="💾🖨️ IMPRIMIR", command=lambda: guardar_presupuesto(True), **st.estilo_boton()).pack(side=tk.RIGHT, padx=5)
    tk.Button(f_acciones_header, text="🧹 LIMPIAR", command=cancelar_venta, **st.estilo_boton(st.ORANGE)).pack(side=tk.RIGHT, padx=5)

    # SECCIÓN BÚSQUEDA
    f_busqueda = tk.Frame(ventana, bg=st.BG_MAIN, padx=15)
    f_busqueda.pack(fill=tk.X, pady=5)
    
    f_busqueda.columnconfigure(1, weight=1)
    f_busqueda.columnconfigure(3, weight=2)

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
    combo_p2_prov.bind("<KeyRelease>", filtrar_provs_p2)
    tk.Button(f_busqueda, text="🧹", command=limpiar_busqueda, **st.estilo_boton(st.BG_CARD)).grid(row=0, column=6, padx=5)

    # TABLA BÚSQUEDA
    cols_b = ("cod", "desc", "prov", "precio")
    tabla_busqueda = ttk.Treeview(ventana, columns=cols_b, show="headings", height=5)
    tabla_busqueda.heading("cod", text="CÓDIGO")
    tabla_busqueda.heading("desc", text="DESCRIPCIÓN")
    tabla_busqueda.heading("prov", text="PROVEEDOR")
    tabla_busqueda.heading("precio", text="P. PROFESIONAL")
    tabla_busqueda.column("cod", width=100)
    tabla_busqueda.column("desc", width=400)
    tabla_busqueda.column("prov", width=150)
    tabla_busqueda.column("precio", width=120, anchor="e")
    tabla_busqueda.pack(fill=tk.X, padx=15, pady=5)
    tabla_busqueda.bind("<<TreeviewSelect>>", seleccionar_p2)
    tabla_busqueda.bind("<Double-1>", lambda e: entrada_cantidad.focus_set())

    # CANTIDAD Y AÑADIR
    f_add = tk.Frame(ventana, bg=st.BG_MAIN, pady=5)
    f_add.pack(fill=tk.X, padx=15)
    
    label_prod_sel = tk.Label(f_add, text="", font=st.FONT_NORMAL, fg=st.ACCENT, bg=st.BG_MAIN)
    label_prod_sel.pack(side=tk.LEFT, padx=10)
    
    tk.Label(f_add, text="CANT:", bg=st.BG_MAIN, fg="white").pack(side=tk.LEFT, padx=5)
    entrada_cantidad = tk.Entry(f_add, width=6, font=st.FONT_INPUT, justify="center")
    entrada_cantidad.pack(side=tk.LEFT, padx=5)
    entrada_cantidad.bind("<Return>", agregar_producto)
    tk.Button(f_add, text="➕ AÑADIR", command=agregar_producto, **st.estilo_boton(st.ACCENT)).pack(side=tk.LEFT, padx=10)

    # TABLA CARRITO
    columnas = ("cod", "desc", "cant", "p_unit", "subtotal", "mod", "del")
    tabla = ttk.Treeview(ventana, columns=columnas, show="headings")
    tabla.heading("cod", text="CÓDIGO")
    tabla.heading("desc", text="DESCRIPCIÓN")
    tabla.heading("cant", text="CANT.")
    tabla.heading("p_unit", text="P. UNITARIO")
    tabla.heading("subtotal", text="SUBTOTAL")
    tabla.heading("mod", text="📎")
    tabla.heading("del", text="🗑️")
    tabla.column("cod", width=100)
    tabla.column("desc", width=400)
    tabla.column("cant", width=80, anchor="center")
    tabla.column("p_unit", width=120, anchor="e")
    tabla.column("subtotal", width=120, anchor="e")
    tabla.column("mod", width=40, anchor="center")
    tabla.column("del", width=40, anchor="center")
    tabla.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
    tabla.bind("<Button-1>", on_tabla_click)
    tabla.tag_configure('total_tag', background=st.BG_CARD, foreground=st.ACCENT, font=st.FONT_LABEL)
    
    label_subtotal_carrito = tk.Label(ventana, text="SUBTOTAL CARRITO: $ 0.00", font=st.FONT_LABEL, bg=st.BG_MAIN, fg=st.TEXT_PRIMARY)
    label_subtotal_carrito.pack(fill=tk.X, padx=15, pady=(0, 5), anchor="e")

    # PIE: TOTALES
    f_footer = tk.Frame(ventana, bg=st.BG_MAIN, pady=10)
    f_footer.pack(fill=tk.X, padx=15)
    
    label_total = tk.Label(f_footer, text="TOTAL: $ -", font=("Inter", 24, "bold"), fg=st.ACCENT, bg=st.BG_MAIN)
    label_total.pack(side=tk.LEFT)

    f_acciones_finales = tk.Frame(f_footer, bg=st.BG_MAIN)
    f_acciones_finales.pack(side=tk.RIGHT)

    tk.Button(f_acciones_finales, text="🧹 LIMPIAR TODO", command=cancelar_venta, **st.estilo_boton(st.ORANGE)).pack(side=tk.RIGHT, padx=5)
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