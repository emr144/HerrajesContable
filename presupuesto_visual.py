import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime
from fpdf import FPDF
import styles as st # Importamos los estilos
import database # Importamos para obtener la ruta

# Variables globales
carrito = []
total_sin_descuento = 0.0
combo_fabrica = None 
entrada_busqueda = None
combo_lista_precios = None # Nuevo selector de lista de precios
lista_proveedores_cache = [] # Cache para filtrado

# --- FUNCIONES DE LÓGICA ---

def obtener_clientes():
    conexion = sqlite3.connect(database.get_db_path())
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre FROM clientes ORDER BY nombre ASC")
    filas = cursor.fetchall()
    conexion.close()
    return [f[0] for f in filas]

def obtener_proveedores_lista():
    conexion = sqlite3.connect(database.get_db_path())
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre FROM proveedores ORDER BY nombre ASC")
    filas = cursor.fetchall()
    conexion.close()
    global lista_proveedores_cache
    lista_proveedores_cache = [f[0] for f in filas]
    return lista_proveedores_cache

def buscar_productos_db(termino, filtro_proveedor=None):
    conexion = sqlite3.connect(database.get_db_path())
    cursor = conexion.cursor()
    query = '''
        SELECT p.codigo_proveedor, p.descripcion, pr.nombre
        FROM productos p
        JOIN proveedores pr ON p.proveedor_id = pr.id
        WHERE (p.codigo_proveedor LIKE ? 
           OR p.descripcion LIKE ? 
           OR pr.nombre LIKE ?)
           AND p.estado = 'ACTIVO'
        LIMIT 60
    '''
    args = [f'%{termino}%', f'%{termino}%', f'%{termino}%']
    
    if filtro_proveedor:
        query = query.replace("LIMIT 60", "AND pr.nombre = ? LIMIT 60")
        args.append(filtro_proveedor)

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
    # Ahora el total es simplemente la suma de los items (que ya tienen el aumento aplicado si corresponde)
    label_total.config(text=f"TOTAL: $ {total_sin_descuento:.2f}", fg="darkgreen")

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
        
        codigo = item.get('codigo', '---')
        desc = item.get('descripcion', '---')
        
        tabla.insert("", "end", values=(codigo, desc, item['cantidad'], f"$ {nuevo_precio_unitario:.2f}", f"$ {nuevo_subtotal:.2f}"))
        total_sin_descuento += nuevo_subtotal

    actualizar_total_visual()

def seleccionar_producto(event=None):
    if not lista_sugerencias.curselection(): return
    seleccion = lista_sugerencias.get(lista_sugerencias.curselection())
    codigo = seleccion.split(" | ")[0]
    entrada_codigo.delete(0, tk.END)
    entrada_codigo.insert(0, codigo)
    if entrada_busqueda:
        entrada_busqueda.delete(0, tk.END)
    lista_sugerencias.place_forget()
    entrada_cantidad.focus()

def actualizar_sugerencias(event=None):
    texto = entrada_busqueda.get().strip()
    prov_filtro = combo_fabrica.get().strip() if combo_fabrica else None
    
    lista_sugerencias.delete(0, tk.END)
    if len(texto) < 2:
        lista_sugerencias.place_forget()
        return
    productos = buscar_productos_db(texto, prov_filtro)
    if productos:
        # Ajustamos dinámicamente la altura y ancho de la lista
        # "3 veces más largo" -> Aumentamos el límite visual a 40 renglones y el ancho a 100 caracteres
        lista_sugerencias.config(height=min(len(productos), 40), width=100)
        
        for p in productos:
            lista_sugerencias.insert(tk.END, f"{p[0]} | {p[1]} | {p[2]}")
        lista_sugerencias.place(x=entrada_busqueda.winfo_x(), y=entrada_busqueda.winfo_y() + entrada_busqueda.winfo_height())
        lista_sugerencias.lift()
    else:
        lista_sugerencias.place_forget()

def agregar_producto(event=None):
    global total_sin_descuento
    codigo = entrada_codigo.get().strip().upper()
    try:
        cantidad = int(entrada_cantidad.get().strip())
    except ValueError:
        messagebox.showerror("Error", "La cantidad debe ser un número.")
        return

    if not codigo or cantidad <= 0: return

    conexion = sqlite3.connect(database.get_db_path())
    cursor = conexion.cursor()
    query = '''
        SELECT p.id, p.descripcion, p.costo_base, p.coeficiente_ganancia, p.iva, pr.descuento_global, pr.incremento_global
        FROM productos p
        JOIN proveedores pr ON p.proveedor_id = pr.id
        WHERE p.codigo_proveedor = ?
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
        tabla.insert("", "end", values=(codigo, desc, cantidad, f"$ {precio_unitario:.2f}", f"$ {subtotal:.2f}"))
        
        total_sin_descuento += subtotal
        actualizar_total_visual()
        
        entrada_codigo.delete(0, tk.END)
        if entrada_busqueda:
            entrada_busqueda.delete(0, tk.END)
        entrada_cantidad.delete(0, tk.END)
        entrada_cantidad.insert(0, "1")
        entrada_codigo.focus()
        lista_sugerencias.place_forget()
    else:
        messagebox.showwarning("No encontrado", f"El código '{codigo}' no existe.")

def borrar_item():
    """Elimina el producto seleccionado de la tabla y resta su valor del total"""
    global total_sin_descuento
    seleccion = tabla.selection()
    if not seleccion:
        messagebox.showwarning("Atención", "Seleccione un producto para eliminar.")
        return
    
    for item in seleccion:
        valores = tabla.item(item, "values")
        # El subtotal está en la posición 4, le quitamos el "$" para volverlo número
        subtotal_item = float(valores[4].replace("$ ", ""))
        total_sin_descuento -= subtotal_item
        
        # También lo quitamos del carrito (buscando por índice o posición)
        indice = tabla.index(item)
        if indice < len(carrito):
            carrito.pop(indice)
            
        tabla.delete(item)
    
    actualizar_total_visual()

def generar_ticket_pdf(presupuesto_id):
    """Genera un PDF con el detalle de la venta y lo abre automáticamente"""
    try:
        conexion = sqlite3.connect(database.get_db_path())
        cursor = conexion.cursor()
        
        # 1. Recuperamos datos de la cabecera
        # Agregamos cliente_tipo para saber si mostrar leyenda
        cursor.execute("SELECT cliente_nombre, fecha, total, cliente_tipo FROM presupuestos WHERE id = ?", (presupuesto_id,))
        datos_venta = cursor.fetchone()
        
        # 2. Recuperamos los productos
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
        pdf.cell(0, 4, f"Ticket N: {presupuesto_id}", ln=True)
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
            pdf.cell(6, 5, str(cant), 1, 0, 'C')
            pdf.cell(12, 5, f"{precio:.2f}", 1, 0, 'R')
            pdf.cell(14, 5, f"{subtotal:.2f}", 1, 1, 'R')
            
        # Total
        pdf.ln(4)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(38, 6, "TOTAL:", 0, 0, 'R')
        pdf.cell(16, 6, f"$ {total:.2f}", 0, 1, 'R')

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
            
        ruta_pdf = os.path.abspath(f"comprobantes/ticket_{presupuesto_id}.pdf")
        pdf.output(ruta_pdf)
        
        # Abrir archivo (Windows)
        os.startfile(ruta_pdf)
        
    except Exception as e:
        messagebox.showerror("Error PDF", f"No se pudo generar el PDF: {e}")

def guardar_presupuesto():
    global total_sin_descuento, carrito
    if not carrito: return
    
    total_final = total_sin_descuento # El total ya incluye los aumentos/precios finales
    nombre_cliente = combo_cliente.get().strip() or "Consumidor Final"
    tipo_cliente = combo_lista_precios.get() # Guardamos qué lista se usó
    
    conexion = sqlite3.connect(database.get_db_path())
    cursor = conexion.cursor()
    # Guardamos el tipo de cliente (Profesional, Particular 15%, etc)
    cursor.execute("INSERT INTO presupuestos (cliente_nombre, total, cliente_tipo) VALUES (?, ?, ?)", (nombre_cliente, total_final, tipo_cliente))
    presupuesto_id = cursor.lastrowid
    
    for item in carrito:
        cursor.execute('INSERT INTO presupuesto_detalles (presupuesto_id, producto_id, cantidad, precio_unitario_congelado) VALUES (?, ?, ?, ?)',
                       (presupuesto_id, item['prod_id'], item['cantidad'], item['precio_unitario']))
    conexion.commit()
    conexion.close()

    # Generar Ticket PDF
    generar_ticket_pdf(presupuesto_id)
    
    messagebox.showinfo("Éxito", f"Presupuesto N° {presupuesto_id} guardado.")
    
    # Reset
    carrito.clear()
    total_sin_descuento = 0.0
    actualizar_total_visual()
    for row in tabla.get_children(): tabla.delete(row)

def filtrar_combo_proveedores(event):
    """Filtra la lista de fábricas al escribir"""
    # Ignoramos teclas de navegación para no interferir
    if event.keysym in ('Down', 'Up', 'Return', 'Escape', 'Tab', 'Left', 'Right', 'Control_L', 'Control_R'): 
        return
    
    texto = combo_fabrica.get().lower()
    
    if not texto:
        combo_fabrica['values'] = lista_proveedores_cache
    else:
        filtrados = [p for p in lista_proveedores_cache if p.lower().startswith(texto)]
        combo_fabrica['values'] = filtrados
        
        # Solo abrimos si hay resultados y no está vacía la búsqueda
        if filtrados:
            combo_fabrica.event_generate('<Down>')

# --- INTERFAZ ---
def montar_interfaz(parent):
    global combo_cliente, combo_fabrica, entrada_codigo, entrada_busqueda, entrada_cantidad, lista_sugerencias, tabla, label_total, combo_lista_precios
    
    ventana = tk.Frame(parent, bg=st.BG_MAIN)
    # ventana.title("Punto de Venta - HerrajesContable") -> Ya no es necesario
    # ventana.geometry("1000x800") -> El tamaño lo maneja el main
    # st.aplicar_estilo_ventana(ventana) -> El frame ya tiene bg=st.BG_MAIN

    # --- Estilos para widgets TTK ---
    # Los estilos globales (Treeview, Notebook) ahora se cargan desde styles.py / main.py
    # para mantener consistencia y el look moderno.
    # Solo configuramos columnas específicas aquí si es necesario.

    # Buscador y Cliente (Frames superiores)
    frame_top = tk.Frame(ventana, pady=10, bg=st.BG_MAIN)
    frame_top.pack(fill=tk.X, padx=15)
    
    tk.Label(frame_top, text="Cliente:", bg=st.BG_MAIN, fg=st.TEXT_SECONDARY, font=st.FONT_LABEL).pack(side=tk.LEFT)
    combo_cliente = ttk.Combobox(frame_top, values=obtener_clientes(), width=30, font=st.FONT_INPUT); combo_cliente.pack(side=tk.LEFT, padx=10)

    # Filtro de Fábrica (Opcional)
    tk.Label(frame_top, text="Fábrica (Filtro):", bg=st.BG_MAIN, fg=st.TEXT_SECONDARY, font=st.FONT_LABEL).pack(side=tk.LEFT, padx=(20, 5))
    combo_fabrica = ttk.Combobox(frame_top, values=obtener_proveedores_lista(), width=25, font=st.FONT_INPUT)
    combo_fabrica.pack(side=tk.LEFT, padx=5)
    combo_fabrica.bind("<KeyRelease>", filtrar_combo_proveedores)

    frame_busqueda = tk.Frame(ventana, pady=10, bg=st.BG_MAIN)
    frame_busqueda.pack(fill=tk.X, padx=15)
    
    tk.Label(frame_busqueda, text="Código:", bg=st.BG_MAIN, fg=st.TEXT_SECONDARY, font=st.FONT_LABEL).pack(side=tk.LEFT)
    
    # Entrada de código directo (más corta)
    entrada_codigo = tk.Entry(frame_busqueda, width=15, **st.estilo_entrada())
    entrada_codigo.pack(side=tk.LEFT, padx=5)
    entrada_codigo.bind('<Return>', agregar_producto)

    tk.Label(frame_busqueda, text="Buscador (Nombre):", bg=st.BG_MAIN, fg=st.TEXT_SECONDARY, font=st.FONT_LABEL).pack(side=tk.LEFT, padx=(10, 0))
    entrada_busqueda = tk.Entry(frame_busqueda, **st.estilo_entrada())
    entrada_busqueda.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    entrada_busqueda.bind('<KeyRelease>', actualizar_sugerencias)

    tk.Label(frame_busqueda, text="Cant:", bg=st.BG_MAIN, fg=st.TEXT_SECONDARY, font=st.FONT_LABEL).pack(side=tk.LEFT, padx=5)
    entrada_cantidad = tk.Entry(frame_busqueda, width=8, **st.estilo_entrada())
    entrada_cantidad.insert(0, "1")
    entrada_cantidad.pack(side=tk.LEFT, padx=5)

    btn_agregar = tk.Button(frame_busqueda, text="➕ Agregar", command=agregar_producto, **st.estilo_boton(st.ACCENT))
    st.configurar_hover(btn_agregar, st.ACCENT, st.BG_CARD)
    btn_agregar.pack(side=tk.LEFT, padx=10)

    # Aumentamos el ancho base de la lista a 100 para que se vean bien las descripciones largas
    lista_sugerencias = tk.Listbox(ventana, font=st.FONT_NORMAL, width=100, height=6, bg=st.BG_CARD, fg="white", selectbackground=st.ACCENT, bd=0)
    lista_sugerencias.bind('<<ListboxSelect>>', seleccionar_producto)

    # TABLA CON COLUMNA SUBTOTAL
    columnas = ("cod", "desc", "cant", "p_unit", "subtotal")
    tabla = ttk.Treeview(ventana, columns=columnas, show="headings")
    tabla.heading("cod", text="CÓDIGO")
    tabla.heading("desc", text="DESCRIPCIÓN")
    tabla.heading("cant", text="CANT.")
    tabla.heading("p_unit", text="P. UNITARIO")
    tabla.heading("subtotal", text="SUBTOTAL")

    tabla.column("cod", width=100)
    tabla.column("desc", width=400)
    tabla.column("cant", width=80, anchor="center")
    tabla.column("p_unit", width=150, anchor="e")
    tabla.column("subtotal", width=150, anchor="e")
    tabla.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

    # Botón para borrar ítem de la tabla
    btn_borrar = tk.Button(ventana, text="❌ Eliminar Producto", command=borrar_item, **st.estilo_boton(st.RED_ERROR))
    st.configurar_hover(btn_borrar, st.RED_ERROR, st.BG_CARD)
    btn_borrar.pack(anchor="e", padx=15)

    # Pie de ventana
    frame_bot = tk.Frame(ventana, pady=20, bg=st.BG_MAIN); frame_bot.pack(fill=tk.X, padx=15)
    label_total = tk.Label(frame_bot, text="TOTAL: $ 0.00", font=("Inter", 28, "bold"), fg="darkgreen", bg=st.BG_MAIN)
    label_total.pack(side=tk.LEFT)

    # SECTOR LISTA DE PRECIOS (NUEVO)
    tk.Label(frame_bot, text="Lista de Precios:", font=st.FONT_LABEL, bg=st.BG_MAIN, fg=st.TEXT_SECONDARY).pack(side=tk.LEFT, padx=(20, 5))
    
    opciones_precios = ["Profesional", "Particular 15%", "Particular 30%"]
    combo_lista_precios = ttk.Combobox(frame_bot, values=opciones_precios, state="readonly", font=st.FONT_INPUT, width=15)
    combo_lista_precios.set("Particular 15%") # Valor por defecto seguro (Particular)
    combo_lista_precios.pack(side=tk.LEFT)
    combo_lista_precios.bind("<<ComboboxSelected>>", recalcular_carrito)

    btn_guardar = tk.Button(frame_bot, text="💾 GUARDAR VENTA", command=guardar_presupuesto, **st.estilo_boton())
    st.configurar_hover(btn_guardar)
    btn_guardar.pack(side=tk.RIGHT)
    
    return ventana

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("1000x800")
    st.aplicar_estilo_ventana(root)
    app = montar_interfaz(root)
    app.pack(fill="both", expand=True)
    root.mainloop()