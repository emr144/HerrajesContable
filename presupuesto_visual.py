import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime
from fpdf import FPDF

# Variables globales
carrito = []
total_presupuesto = 0.0
dict_clientes = {} # Para guardar ID -> Nombre de los clientes

def obtener_clientes():
    """Trae la lista de clientes de la DB para el desplegable"""
    global dict_clientes
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM clientes ORDER BY nombre ASC")
    filas = cursor.fetchall()
    conexion.close()
    
    # Limpiamos y cargamos el diccionario
    dict_clientes = {nombre: id for id, nombre in filas}
    return list(dict_clientes.keys())

def generar_pdf_ticket(nro_presupuesto, nombre_cliente, items_tabla, total):
    if not os.path.exists('presupuestos_pdf'):
        os.makedirs('presupuestos_pdf')

    pdf = FPDF('P', 'mm', (80, 200))
    pdf.add_page()
    pdf.set_margins(4, 4, 4)
    pdf.set_auto_page_break(False)

    # --- ENCABEZADO ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "HERRAJES CONTABLE", ln=True, align='C')
    
    pdf.set_font("Arial", size=8)
    pdf.cell(0, 5, f"Ticket Nro: {nro_presupuesto}", ln=True, align='L')
    pdf.cell(0, 5, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='L')
    pdf.cell(0, 5, f"Cliente: {nombre_cliente}", ln=True, align='L')
    
    pdf.cell(0, 2, "-" * 45, ln=True, align='C')

    # --- PRODUCTOS ---
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(35, 6, "Descripcion", 0)
    pdf.cell(8, 6, "Cant", 0, 0, 'C')
    pdf.cell(25, 6, "Subtotal", 0, 1, 'R')
    pdf.cell(0, 1, "-" * 45, ln=True, align='C')

    pdf.set_font("Arial", size=8)
    for row in items_tabla:
        desc_producto = str(row[1])[:22]
        pdf.cell(35, 6, desc_producto, 0)
        pdf.cell(8, 6, str(row[2]), 0, 0, 'C')
        pdf.cell(25, 6, str(row[4]), 0, 1, 'R')

    # --- TOTAL ---
    pdf.ln(3)
    pdf.cell(0, 1, "=" * 35, ln=True, align='C')
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, f"TOTAL: {total}", ln=True, align='R')
    
    pdf.set_font("Arial", 'I', 7)
    pdf.ln(2)
    pdf.cell(0, 5, "Gracias por su confianza", ln=True, align='C')

    nombre_archivo = f"presupuestos_pdf/Ticket_{nro_presupuesto}.pdf"
    pdf.output(nombre_archivo)
    return nombre_archivo

def agregar_producto(event=None):
    global total_presupuesto
    codigo = entrada_codigo.get().strip().upper()
    try:
        cantidad = float(entrada_cantidad.get().strip())
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
        tabla.insert("", "end", values=(codigo, desc, cantidad, f"$ {precio_unitario:.2f}", f"$ {subtotal:.2f}"))
        total_presupuesto += subtotal
        label_total.config(text=f"TOTAL: $ {total_presupuesto:.2f}")
        entrada_codigo.delete(0, tk.END)
        entrada_cantidad.delete(0, tk.END)
        entrada_cantidad.insert(0, "1")
        entrada_codigo.focus()
    else:
        messagebox.showwarning("No encontrado", f"El código '{codigo}' no existe.")

def guardar_presupuesto():
    global total_presupuesto, carrito
    if not carrito:
        messagebox.showwarning("Vacío", "No hay productos.")
        return

    # Obtenemos el nombre seleccionado en el Combobox
    nombre_cliente = combo_cliente.get().strip()
    if not nombre_cliente:
        nombre_cliente = "Consumidor Final"

    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()

    # Guardar Cabecera
    cursor.execute("INSERT INTO presupuestos (cliente_nombre, total) VALUES (?, ?)", (nombre_cliente, total_presupuesto))
    presupuesto_id = cursor.lastrowid

    datos_para_ticket = []
    for child in tabla.get_children():
        datos_para_ticket.append(tabla.item(child)["values"])

    for item in carrito:
        cursor.execute('INSERT INTO presupuesto_detalles (presupuesto_id, producto_id, cantidad, precio_unitario_congelado) VALUES (?, ?, ?, ?)',
                       (presupuesto_id, item['prod_id'], item['cantidad'], item['precio_unitario']))

    conexion.commit()
    conexion.close()

    ruta_ticket = generar_pdf_ticket(presupuesto_id, nombre_cliente, datos_para_ticket, f"$ {total_presupuesto:.2f}")
    
    messagebox.showinfo("¡Éxito!", f"Ticket N° {presupuesto_id} generado.")
    os.startfile(ruta_ticket)
    
    # Limpiar
    carrito.clear()
    total_presupuesto = 0.0
    label_total.config(text="TOTAL: $ 0.00")
    combo_cliente.set('')
    for row in tabla.get_children():
        tabla.delete(row)

# --- INTERFAZ ---
ventana = tk.Tk()
ventana.title("Punto de Venta Pro - HerrajesContable")
ventana.geometry("750x600")

# Fila Cliente con Buscador
frame_cliente = tk.Frame(ventana, pady=10)
frame_cliente.pack(fill=tk.X, padx=15)
tk.Label(frame_cliente, text="Seleccionar Cliente:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)

# Combo de Clientes
lista_nombres = obtener_clientes()
combo_cliente = ttk.Combobox(frame_cliente, values=lista_nombres, width=40, font=("Arial", 11))
combo_cliente.pack(side=tk.LEFT, padx=10)
# Si no hay clientes en la agenda, se puede escribir uno nuevo directamente
if not lista_nombres:
    combo_cliente.set("Consumidor Final")

# Buscador de Productos
frame_prod = tk.Frame(ventana, pady=10)
frame_prod.pack(fill=tk.X, padx=15)
tk.Label(frame_prod, text="Código:").pack(side=tk.LEFT)
entrada_codigo = tk.Entry(frame_prod, width=12, font=("Arial", 11))
entrada_codigo.pack(side=tk.LEFT, padx=5)
entrada_codigo.bind('<Return>', agregar_producto)

tk.Label(frame_prod, text="Cant:").pack(side=tk.LEFT, padx=5)
entrada_cantidad = tk.Entry(frame_prod, width=6, font=("Arial", 11))
entrada_cantidad.insert(0, "1")
entrada_cantidad.pack(side=tk.LEFT, padx=5)
entrada_cantidad.bind('<Return>', agregar_producto)

tk.Button(frame_prod, text="Agregar", command=agregar_producto, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=10)

# Tabla Treeview
columnas = ("codigo", "descripcion", "cantidad", "precio", "subtotal")
tabla = ttk.Treeview(ventana, columns=columnas, show="headings", height=12)
for col in columnas: tabla.heading(col, text=col.capitalize())
tabla.column("descripcion", width=300)
tabla.pack(fill=tk.BOTH, expand=True, padx=15)

# Pie
frame_inf = tk.Frame(ventana, pady=20)
frame_inf.pack(fill=tk.X, padx=15)
label_total = tk.Label(frame_inf, text="TOTAL: $ 0.00", font=("Arial", 24, "bold"), fg="darkgreen")
label_total.pack(side=tk.LEFT)
tk.Button(frame_inf, text="💾 GUARDAR E IMPRIMIR", command=guardar_presupuesto, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), padx=20, pady=10).pack(side=tk.RIGHT)

if __name__ == '__main__':
    ventana.mainloop()