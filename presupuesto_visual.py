import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

# Estas variables globales guardan la memoria del presupuesto mientras lo armamos
carrito = []
total_presupuesto = 0.0

def agregar_producto(event=None):
    global total_presupuesto
    
    codigo = entrada_codigo.get().strip().upper()
    try:
        cantidad = float(entrada_cantidad.get().strip())
    except ValueError:
        messagebox.showerror("Error", "La cantidad debe ser un número.")
        return

    if not codigo or cantidad <= 0:
        messagebox.showerror("Error", "Ingrese un código y una cantidad válida.")
        return

    # Buscamos en la base de datos
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT id, descripcion, costo_base, coeficiente_ganancia, iva 
        FROM productos WHERE codigo_proveedor = ?
    ''', (codigo,))
    producto = cursor.fetchone()
    conexion.close()

    if producto:
        prod_id, desc, costo, coef, iva = producto
        precio_unitario = costo * coef * (1 + iva)
        subtotal = precio_unitario * cantidad
        
        # 1. Guardamos los datos en la memoria invisible (el carrito)
        carrito.append({
            'prod_id': prod_id,
            'cantidad': cantidad,
            'precio_unitario': precio_unitario
        })
        
        # 2. Agregamos la fila a la tabla visual
        tabla.insert("", "end", values=(codigo, desc, cantidad, f"$ {precio_unitario:.2f}", f"$ {subtotal:.2f}"))
        
        # 3. Actualizamos el cartel del total
        total_presupuesto += subtotal
        label_total.config(text=f"TOTAL: $ {total_presupuesto:.2f}")
        
        # 4. Limpiamos las cajitas para que el vendedor ingrese el siguiente rápido
        entrada_codigo.delete(0, tk.END)
        entrada_cantidad.delete(0, tk.END)
        entrada_cantidad.insert(0, "1") # Volvemos a poner 1 por defecto
        entrada_codigo.focus() # Ponemos el cursor de texto de vuelta en el código
    else:
        messagebox.showwarning("No encontrado", f"El código '{codigo}' no existe.")

def guardar_presupuesto():
    global total_presupuesto, carrito
    
    if not carrito:
        messagebox.showwarning("Vacío", "No hay productos en el presupuesto.")
        return

    cliente = entrada_cliente.get().strip()
    if not cliente:
        cliente = "Consumidor Final"

    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()

    # 1. Guardamos la cabecera (y obtenemos el ID que nos da SQLite)
    cursor.execute("INSERT INTO presupuestos (cliente_nombre, total) VALUES (?, ?)", (cliente, total_presupuesto))
    presupuesto_id = cursor.lastrowid

    # 2. Guardamos todos los detalles asociados a ese ID
    for item in carrito:
        cursor.execute('''
            INSERT INTO presupuesto_detalles (presupuesto_id, producto_id, cantidad, precio_unitario_congelado)
            VALUES (?, ?, ?, ?)
        ''', (presupuesto_id, item['prod_id'], item['cantidad'], item['precio_unitario']))

    conexion.commit()
    conexion.close()

    messagebox.showinfo("¡Éxito!", f"Presupuesto N° {presupuesto_id} guardado correctamente en la base de datos.")
    
    # 3. Limpiamos TODA la pantalla para atender al siguiente cliente
    carrito.clear()
    total_presupuesto = 0.0
    label_total.config(text="TOTAL: $ 0.00")
    entrada_cliente.delete(0, tk.END)
    # Esto borra todas las filas de la tabla visual
    for row in tabla.get_children():
        tabla.delete(row)

# ==========================================
# DISEÑO DE LA VENTANA (INTERFAZ)
# ==========================================
ventana = tk.Tk()
ventana.title("Punto de Venta - HerrajesContable")
ventana.geometry("700x500")
ventana.config(padx=15, pady=15)

# --- Datos del Cliente ---
frame_cliente = tk.Frame(ventana)
frame_cliente.pack(fill=tk.X, pady=5)
tk.Label(frame_cliente, text="Cliente:", font=("Arial", 11, "bold")).pack(side=tk.LEFT)
entrada_cliente = tk.Entry(frame_cliente, font=("Arial", 11), width=40)
entrada_cliente.pack(side=tk.LEFT, padx=10)

# --- Buscador de Productos ---
frame_producto = tk.Frame(ventana)
frame_producto.pack(fill=tk.X, pady=10)

tk.Label(frame_producto, text="Código:", font=("Arial", 10)).pack(side=tk.LEFT)
entrada_codigo = tk.Entry(frame_producto, font=("Arial", 11), width=10)
entrada_codigo.pack(side=tk.LEFT, padx=5)
entrada_codigo.bind('<Return>', agregar_producto) # Presionar Enter agrega el producto

tk.Label(frame_producto, text="Cantidad:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(15, 0))
entrada_cantidad = tk.Entry(frame_producto, font=("Arial", 11), width=5)
entrada_cantidad.insert(0, "1") # Cantidad por defecto
entrada_cantidad.pack(side=tk.LEFT, padx=5)
entrada_cantidad.bind('<Return>', agregar_producto) # Presionar Enter también funciona aquí

tk.Button(frame_producto, text="Agregar al Presupuesto", command=agregar_producto, bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=15)

# --- Tabla Visual de Productos (Treeview) ---
# Definimos las columnas
columnas = ("codigo", "descripcion", "cantidad", "precio", "subtotal")
tabla = ttk.Treeview(ventana, columns=columnas, show="headings", height=12)

# Le ponemos nombre a los encabezados
tabla.heading("codigo", text="Código")
tabla.heading("descripcion", text="Descripción")
tabla.heading("cantidad", text="Cant.")
tabla.heading("precio", text="Precio Unit.")
tabla.heading("subtotal", text="Subtotal")

# Ajustamos el ancho de las columnas
tabla.column("codigo", width=80, anchor=tk.CENTER)
tabla.column("descripcion", width=250)
tabla.column("cantidad", width=50, anchor=tk.CENTER)
tabla.column("precio", width=100, anchor=tk.E)
tabla.column("subtotal", width=100, anchor=tk.E)

tabla.pack(fill=tk.BOTH, expand=True, pady=10)

# --- Zona de Total y Guardado ---
frame_inferior = tk.Frame(ventana)
frame_inferior.pack(fill=tk.X, pady=10)

label_total = tk.Label(frame_inferior, text="TOTAL: $ 0.00", font=("Arial", 20, "bold"), fg="darkgreen")
label_total.pack(side=tk.LEFT)

btn_guardar = tk.Button(frame_inferior, text="💾 GUARDAR PRESUPUESTO", command=guardar_presupuesto, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), padx=20, pady=5)
btn_guardar.pack(side=tk.RIGHT)


if __name__ == '__main__':
    ventana.mainloop()
