import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime
from fpdf import FPDF
import styles as st # Importamos los estilos

# Variables globales
carrito = []
total_sin_descuento = 0.0

# --- FUNCIONES DE LÓGICA ---

def obtener_clientes():
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre FROM clientes ORDER BY nombre ASC")
    filas = cursor.fetchall()
    conexion.close()
    return [f[0] for f in filas]

def buscar_productos_db(termino):
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    query = '''
        SELECT p.codigo_proveedor, p.descripcion, pr.nombre
        FROM productos p
        JOIN proveedores pr ON p.proveedor_id = pr.id
        WHERE (p.codigo_proveedor LIKE ? 
           OR p.descripcion LIKE ? 
           OR pr.nombre LIKE ?)
           AND p.estado = 'ACTIVO'
        LIMIT 10
    '''
    patron = f'%{termino}%'
    cursor.execute(query, (patron, patron, patron))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def actualizar_total_visual():
    global total_sin_descuento
    if check_desc_var.get():
        total_con_descuento = total_sin_descuento * 0.90
        label_total.config(text=f"TOTAL: $ {total_con_descuento:.2f}", fg="red")
        label_info_desc.config(text="(Descuento 10% Aplicado)")
    else:
        label_total.config(text=f"TOTAL: $ {total_sin_descuento:.2f}", fg="darkgreen")
        label_info_desc.config(text="")

def seleccionar_producto(event=None):
    if not lista_sugerencias.curselection(): return
    seleccion = lista_sugerencias.get(lista_sugerencias.curselection())
    codigo = seleccion.split(" | ")[0]
    entrada_codigo.delete(0, tk.END)
    entrada_codigo.insert(0, codigo)
    lista_sugerencias.place_forget()
    entrada_cantidad.focus()

def actualizar_sugerencias(event=None):
    texto = entrada_codigo.get().strip()
    lista_sugerencias.delete(0, tk.END)
    if len(texto) < 2:
        lista_sugerencias.place_forget()
        return
    productos = buscar_productos_db(texto)
    if productos:
        for p in productos:
            lista_sugerencias.insert(tk.END, f"{p[0]} | {p[1]} | {p[2]}")
        lista_sugerencias.place(x=entrada_codigo.winfo_x(), y=entrada_codigo.winfo_y() + entrada_codigo.winfo_height())
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

    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    cursor.execute('SELECT id, descripcion, costo_base, coeficiente_ganancia, iva FROM productos WHERE codigo_proveedor = ?', (codigo,))
    producto = cursor.fetchone()
    conexion.close()

    if producto:
        prod_id, desc, costo, coef, iva = producto
        precio_unitario = costo * coef * (1 + iva)
        subtotal = precio_unitario * cantidad
        
        carrito.append({'prod_id': prod_id, 'cantidad': cantidad, 'precio_unitario': precio_unitario})
        
        # INSERTAMOS EN LA TABLA CON LA COLUMNA SUBTOTAL
        tabla.insert("", "end", values=(codigo, desc, cantidad, f"$ {precio_unitario:.2f}", f"$ {subtotal:.2f}"))
        
        total_sin_descuento += subtotal
        actualizar_total_visual()
        
        entrada_codigo.delete(0, tk.END)
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
        conexion = sqlite3.connect('herrajes.db')
        cursor = conexion.cursor()
        
        # 1. Recuperamos datos de la cabecera
        cursor.execute("SELECT cliente_nombre, fecha, total FROM presupuestos WHERE id = ?", (presupuesto_id,))
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

        cliente, fecha, total = datos_venta
        
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
    
    total_final = total_sin_descuento * 0.9 if check_desc_var.get() else total_sin_descuento
    nombre_cliente = combo_cliente.get().strip() or "Consumidor Final"
    
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO presupuestos (cliente_nombre, total) VALUES (?, ?)", (nombre_cliente, total_final))
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
    check_desc_var.set(False)
    actualizar_total_visual()
    for row in tabla.get_children(): tabla.delete(row)

# --- INTERFAZ ---
def montar_interfaz(parent):
    global combo_cliente, entrada_codigo, entrada_cantidad, lista_sugerencias, tabla, label_total, check_desc_var, label_info_desc
    
    ventana = tk.Frame(parent, bg=st.BG_MAIN)
    # ventana.title("Punto de Venta - HerrajesContable") -> Ya no es necesario
    # ventana.geometry("1000x800") -> El tamaño lo maneja el main
    # st.aplicar_estilo_ventana(ventana) -> El frame ya tiene bg=st.BG_MAIN

    # --- Estilos para widgets TTK ---
    style = ttk.Style()
    style.theme_use("clam")
    # Treeview
    style.configure("Treeview", background=st.BG_CARD, foreground="white", fieldbackground=st.BG_CARD, borderwidth=0, rowheight=25)
    style.map("Treeview", background=[('selected', st.ACCENT)])
    style.configure("Treeview.Heading", background=st.BG_CARD, foreground=st.TEXT_SECONDARY, font=st.FONT_LABEL, padding=10)
    # Combobox
    parent.option_add('*TCombobox*Listbox.background', st.BG_CARD)
    parent.option_add('*TCombobox*Listbox.foreground', 'white')
    parent.option_add('*TCombobox*Listbox.selectBackground', st.ACCENT)
    style.configure("TCombobox", fieldbackground=st.BG_MAIN, background=st.BG_CARD, foreground='white', borderwidth=0, padding=5)

    # Buscador y Cliente (Frames superiores)
    frame_top = tk.Frame(ventana, pady=10, bg=st.BG_MAIN); frame_top.pack(fill=tk.X, padx=15)
    tk.Label(frame_top, text="Cliente:", bg=st.BG_MAIN, fg=st.TEXT_SECONDARY, font=st.FONT_LABEL).pack(side=tk.LEFT)
    combo_cliente = ttk.Combobox(frame_top, values=obtener_clientes(), width=30, font=st.FONT_NORMAL); combo_cliente.pack(side=tk.LEFT, padx=10)

    frame_busqueda = tk.Frame(ventana, pady=10, bg=st.BG_MAIN); frame_busqueda.pack(fill=tk.X, padx=15)
    tk.Label(frame_busqueda, text="Producto:", bg=st.BG_MAIN, fg=st.TEXT_SECONDARY, font=st.FONT_LABEL).pack(side=tk.LEFT)
    entrada_codigo = tk.Entry(frame_busqueda, width=40, font=st.FONT_NORMAL, bg=st.BG_CARD, fg="white", bd=0, insertbackground="white"); entrada_codigo.pack(side=tk.LEFT, padx=5)
    entrada_codigo.bind('<KeyRelease>', actualizar_sugerencias)

    tk.Label(frame_busqueda, text="Cant:", bg=st.BG_MAIN, fg=st.TEXT_SECONDARY, font=st.FONT_LABEL).pack(side=tk.LEFT, padx=5)
    entrada_cantidad = tk.Entry(frame_busqueda, width=5, font=st.FONT_NORMAL, bg=st.BG_CARD, fg="white", bd=0, insertbackground="white"); entrada_cantidad.insert(0, "1"); entrada_cantidad.pack(side=tk.LEFT, padx=5)

    btn_agregar = tk.Button(frame_busqueda, text="➕ Agregar", command=agregar_producto, **st.estilo_boton(st.ACCENT))
    st.configurar_hover(btn_agregar, st.ACCENT, st.BG_CARD)
    btn_agregar.pack(side=tk.LEFT, padx=10)

    lista_sugerencias = tk.Listbox(ventana, font=st.FONT_NORMAL, width=50, height=6, bg=st.BG_CARD, fg="white", selectbackground=st.ACCENT, bd=0)
    lista_sugerencias.bind('<<ListboxSelect>>', seleccionar_producto)

    # TABLA CON COLUMNA SUBTOTAL
    columnas = ("cod", "desc", "cant", "p_unit", "subtotal")
    tabla = ttk.Treeview(ventana, columns=columnas, show="headings", style="Treeview")
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

    check_desc_var = tk.BooleanVar()
    check_descuento = tk.Checkbutton(frame_bot, text="Descuento 10% (Gremio)", variable=check_desc_var, 
                                     command=actualizar_total_visual, font=st.FONT_NORMAL, bg=st.BG_MAIN, fg="white",
                                     selectcolor=st.BG_CARD, activebackground=st.BG_MAIN, activeforeground="white")
    check_descuento.pack(side=tk.LEFT, padx=20)

    label_info_desc = tk.Label(frame_bot, text="", fg=st.RED_ERROR, bg=st.BG_MAIN, font=st.FONT_NORMAL)
    label_info_desc.pack(side=tk.LEFT)

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