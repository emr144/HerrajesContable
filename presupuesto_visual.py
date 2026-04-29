import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
from datetime import datetime
from fpdf import FPDF
import styles as st # Importamos los estilos
import database # Importamos para obtener la ruta

# Variables globales
carrito = []
total_sin_descuento = 0.0
combo_lista_precios = None # Nuevo selector de lista de precios
lista_proveedores_cache = [] # Cache para filtrado
var_tarjeta = None # Variable para el recargo de tarjeta

codigo_seleccionado = ""
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
        SELECT p.codigo_proveedor, p.descripcion, pr.nombre,
               p.costo_base, p.coeficiente_ganancia, p.iva,
               pr.descuento_global, pr.incremento_global
        FROM productos p
        JOIN proveedores pr ON p.proveedor_id = pr.id
        WHERE p.estado = 'ACTIVO'
    '''
    args = []

    if filtro_codigo:
        query += " AND p.codigo_proveedor LIKE %s"
        args.append(f'%{filtro_codigo}%')

    if termino:
        query += " AND p.descripcion LIKE %s"
        args.append(f'%{termino}%')

    if filtro_proveedor:
        query += " AND pr.nombre = %s"
        args.append(filtro_proveedor)

    query += " LIMIT 60"

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
    else:
        label_total.config(text=f"TOTAL: $ {total_final:.2f}", fg="darkgreen")

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
    global total_sin_descuento, codigo_seleccionado
    codigo = codigo_seleccionado
    try:
        cantidad = int(entrada_cantidad.get().strip())
    except ValueError:
        messagebox.showerror("Error", "La cantidad debe ser un número.")
        return

    if not codigo or cantidad <= 0: return

    conexion = database.conectar()
    cursor = conexion.cursor()
    query = '''
        SELECT p.id, p.descripcion, p.costo_base, p.coeficiente_ganancia, p.iva, pr.descuento_global, pr.incremento_global
        FROM productos p
        JOIN proveedores pr ON p.proveedor_id = pr.id
        WHERE p.codigo_proveedor = %s
    '''
    cursor.execute(query, (codigo,))
    producto = cursor.fetchone()
    conexion.close()

    if producto:
        prod_id, desc, costo, coef, iva, desc_g, inc_g = producto
        # Precio base (Profesional / Lista) aplicando el descuento del proveedor
        precio_base = costo * (1 - (desc_g or 0)) * (1 + (inc_g or 0)) * coef * (1 + iva)
        
        # Precio final con el aumento seleccionado
        multiplicador = obtener_multiplicador_precio()
        precio_unitario = precio_base * multiplicador
        
        subtotal = precio_unitario * cantidad
        
        # Guardamos precio_base_lista para poder recalcular si cambiamos de categoria
        carrito.append({'prod_id': prod_id, 'cantidad': cantidad, 'precio_unitario': precio_unitario, 'precio_base_lista': precio_base, 'codigo': codigo, 'descripcion': desc})
        
        # INSERTAMOS EN LA TABLA CON LA COLUMNA SUBTOTAL
        tabla.insert("", "end", values=(codigo, desc, cantidad, f"$ {precio_unitario:.2f}", f"$ {subtotal:.2f}", "📎", "🗑️"))
        
        total_sin_descuento += subtotal
        actualizar_total_visual()
        
        codigo_seleccionado = ""
        label_prod_sel.config(text="")
        entrada_cantidad.delete(0, tk.END)
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

def cancelar_venta():
    global total_sin_descuento, carrito, codigo_seleccionado, var_tarjeta
    carrito.clear()
    total_sin_descuento = 0.0
    codigo_seleccionado = ""
    var_tarjeta.set(False)
    label_prod_sel.config(text="")
    actualizar_total_visual()
    for row in tabla.get_children(): tabla.delete(row)
    entrada_cantidad.delete(0, tk.END)

def abrir_buscador_productos():
    top = tk.Toplevel()
    top.title("Buscador de Productos")
    
    # Obtener dimensiones de la pantalla para calcular el 3/4 (75%)
    screen_width = top.winfo_screenwidth()
    screen_height = top.winfo_screenheight()
    width = int(screen_width * 0.75)
    height = int(screen_height * 0.75)
    # Calcular coordenadas para centrar la ventana
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    top.geometry(f"{width}x{height}+{x}+{y}")
    
    st.aplicar_estilo_ventana(top)
    
    frame_f = tk.Frame(top, bg=st.BG_MAIN, padx=10, pady=10)
    frame_f.pack(fill=tk.X)
    
    tk.Label(frame_f, text="Fábrica:", bg=st.BG_MAIN, fg="white").grid(row=0, column=0, padx=5)
    c_prov = ttk.Combobox(frame_f, values=["TODOS"] + obtener_proveedores_lista(), state="readonly")
    c_prov.set("TODOS")
    c_prov.grid(row=0, column=1, padx=5)
    
    tk.Label(frame_f, text="Código:", bg=st.BG_MAIN, fg="white").grid(row=0, column=2, padx=5)
    e_cod = tk.Entry(frame_f, **st.estilo_entrada())
    e_cod.grid(row=0, column=3, padx=5)
    
    tk.Label(frame_f, text="Producto:", bg=st.BG_MAIN, fg="white").grid(row=0, column=4, padx=5)
    e_desc = tk.Entry(frame_f, **st.estilo_entrada())
    e_desc.grid(row=0, column=5, padx=5)
    
    cols = ("cod", "desc", "prov", "precio")
    t_busca = ttk.Treeview(top, columns=cols, show="headings")
    t_busca.heading("cod", text="CÓDIGO"); t_busca.heading("desc", text="DESCRIPCIÓN"); t_busca.heading("prov", text="PROVEEDOR"); t_busca.heading("precio", text="P. PROFESIONAL")
    t_busca.column("cod", width=100); t_busca.column("desc", width=350); t_busca.column("prov", width=150); t_busca.column("precio", width=120, anchor="e")
    t_busca.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def buscar(_=None):
        for row in t_busca.get_children(): t_busca.delete(row)
        prov = None if c_prov.get() == "TODOS" else c_prov.get()
        res = buscar_productos_db(termino=e_desc.get(), filtro_proveedor=prov, filtro_codigo=e_cod.get())
        for r in res:
            cod, desc, prov_nom, costo, coef, iva, desc_g, inc_g = r
            precio_prof = costo * (1 - (desc_g or 0)) * (1 + (inc_g or 0)) * coef * (1 + iva)
            t_busca.insert("", "end", values=(cod, desc, prov_nom, f"$ {precio_prof:.2f}"))

    e_cod.bind("<KeyRelease>", buscar); e_desc.bind("<KeyRelease>", buscar); c_prov.bind("<<ComboboxSelected>>", buscar)
    
    def seleccionar():
        global codigo_seleccionado
        sel = t_busca.selection()
        if sel:
            val = t_busca.item(sel[0], 'values')
            codigo_seleccionado = val[0]
            label_prod_sel.config(text=f"{val[0]} | {val[1][:50]}...", foreground=st.ACCENT)
            top.destroy()
            entrada_cantidad.focus()

    f_btn = tk.Frame(top, bg=st.BG_MAIN, pady=10)
    f_btn.pack(fill=tk.X)
    tk.Button(f_btn, text="ACEPTAR", command=seleccionar, **st.get_btn_style(st.ACCENT)).pack(side=tk.RIGHT, padx=10)
    tk.Button(f_btn, text="CANCELAR", command=top.destroy, **st.get_btn_style(st.RED_ERROR)).pack(side=tk.RIGHT, padx=10)
    
    buscar()

def on_tabla_click(event):
    region = tabla.identify_region(event.x, event.y)
    if region != "cell": return
    col = tabla.identify_column(event.x)
    item_id = tabla.identify_row(event.y)
    if not item_id: return

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
    global combo_cliente, entrada_cantidad, tabla, label_total, combo_lista_precios, label_prod_sel, var_tarjeta
    
    ventana = tk.Frame(parent, bg=st.BG_MAIN)

    # --- Barra de Venta Refinada y Funcional ---
    frame_top = ttk.Frame(ventana, style="Venta.TFrame", padding=(15, 10))
    frame_top.pack(fill=tk.X, padx=15, pady=(10, 5))

    # Configuración de pesos para un diseño elástico y profesional
    frame_top.columnconfigure(1, weight=1)  # Cliente
    frame_top.columnconfigure(6, weight=2)  # Info producto seleccionado
    var_tarjeta = tk.BooleanVar(value=False)

    # 1. CLIENTE Y LISTA DE PRECIOS
    ttk.Label(frame_top, text="CLIENTE:", style="Venta.TLabel").grid(row=0, column=0, padx=(5, 5), sticky="w")
    combo_cliente = ttk.Combobox(frame_top, values=obtener_clientes(), font=st.FONT_INPUT)
    combo_cliente.grid(row=0, column=1, padx=(0, 15), sticky="ew")

    ttk.Label(frame_top, text="LISTA:", style="Venta.TLabel").grid(row=0, column=2, padx=(10, 5), sticky="w")
    opciones_precios = ["Profesional", "Particular 15%", "Particular 30%"]
    combo_lista_precios = ttk.Combobox(frame_top, values=opciones_precios, state="readonly", font=st.FONT_INPUT, width=15)
    combo_lista_precios.set("Particular 15%")
    combo_lista_precios.grid(row=0, column=3, padx=(0, 15), sticky="w")
    combo_lista_precios.bind("<<ComboboxSelected>>", recalcular_carrito)
    
    chk_tarjeta = tk.Checkbutton(frame_top, text="TARJETA (+10%)", variable=var_tarjeta, command=actualizar_total_visual, bg=st.BG_CARD, fg=st.ACCENT, selectcolor=st.BG_MAIN, activebackground=st.BG_CARD, font=st.FONT_LABEL)
    chk_tarjeta.grid(row=0, column=4, padx=(10, 15))

    # 2. BÚSQUEDA Y PRODUCTO SELECCIONADO
    btn_abrir_busca = ttk.Button(frame_top, text="🔍 BUSCAR PRODUCTO", command=abrir_buscador_productos, bootstyle="info-outline")
    btn_abrir_busca.grid(row=0, column=5, padx=(10, 10))

    label_prod_sel = ttk.Label(frame_top, text="", font=st.FONT_NORMAL, foreground=st.ACCENT, background=st.BG_CARD)
    label_prod_sel.grid(row=0, column=6, sticky="w", padx=(5, 15))

    # 3. CANTIDAD Y ACCIÓN
    frame_accion = ttk.Frame(frame_top, style="Venta.TFrame")
    frame_accion.grid(row=0, column=7, columnspan=3, sticky="e")

    ttk.Label(frame_accion, text="CANT:", style="Venta.TLabel").pack(side=tk.LEFT, padx=(5, 5))
    entrada_cantidad = ttk.Entry(frame_accion, width=6, font=st.FONT_INPUT, justify="center")
    entrada_cantidad.pack(side=tk.LEFT, padx=(0, 10))
    entrada_cantidad.bind("<Return>", agregar_producto)

    btn_agregar = ttk.Button(frame_accion, text="➕ AÑADIR", command=agregar_producto, bootstyle="success-outline")
    btn_agregar.pack(side=tk.LEFT)

    # TABLA CON COLUMNA SUBTOTAL
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
    tabla.column("p_unit", width=150, anchor="e")
    tabla.column("subtotal", width=150, anchor="e")
    tabla.column("mod", width=40, anchor="center")
    tabla.column("del", width=40, anchor="center")
    tabla.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
    tabla.bind("<Button-1>", on_tabla_click)

    # Pie de ventana
    frame_bot = tk.Frame(ventana, pady=20, bg=st.BG_MAIN); frame_bot.pack(fill=tk.X, padx=15)
    label_total = tk.Label(frame_bot, text="TOTAL: $ -", font=("Inter", 28, "bold"), fg=st.ACCENT, bg=st.BG_MAIN)
    label_total.pack(side=tk.LEFT)

    btn_cancelar = tk.Button(frame_bot, text="❌ CANCELAR", command=cancelar_venta, **st.estilo_boton(st.RED_ERROR))
    btn_cancelar.pack(side=tk.RIGHT, padx=5)

    btn_aceptar = tk.Button(frame_bot, text="✔️ ACEPTAR (GUARDAR)", command=lambda: guardar_presupuesto(False), **st.estilo_boton(st.ACCENT))
    btn_aceptar.pack(side=tk.RIGHT, padx=5)

    btn_imprimir = tk.Button(frame_bot, text="💾🖨️ IMPRIMIR (GUARDAR)", command=lambda: guardar_presupuesto(True), **st.estilo_boton())
    btn_imprimir.pack(side=tk.RIGHT, padx=5)
    
    return ventana

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("1000x800")
    st.aplicar_estilo_ventana(root)
    app = montar_interfaz(root)
    app.pack(fill="both", expand=True)
    root.mainloop()