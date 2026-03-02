import sqlite3

def nuevo_presupuesto():
    print("\n" + "="*40)
    print(" 📝 NUEVO PRESUPUESTO ")
    print("="*40)
    
    cliente = input("Nombre del cliente (o presiona Enter para 'Consumidor Final'): ").strip()
    if not cliente:
        cliente = "Consumidor Final"

    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()

    # 1. Creamos la "Cabecera" del presupuesto en la base de datos
    cursor.execute("INSERT INTO presupuestos (cliente_nombre) VALUES (?)", (cliente,))
    # ¡Magia! Obtenemos el número de presupuesto que SQLite acaba de inventar
    presupuesto_id = cursor.lastrowid 

    total_presupuesto = 0.0
    items = [] # Para guardar el resumen visual

    # 2. Empezamos a escanear productos en bucle
    while True:
        codigo = input("\nIngrese código del producto (o escriba 'fin' para terminar): ").strip().upper()
        
        if codigo == 'FIN':
            break

        # Buscamos el producto en la base de datos
        cursor.execute('''
            SELECT id, descripcion, costo_base, coeficiente_ganancia, iva 
            FROM productos WHERE codigo_proveedor = ?
        ''', (codigo,))
        producto = cursor.fetchone()

        if producto:
            prod_id, desc, costo, coef, iva = producto
            # Calculamos el precio de venta
            precio_unitario = costo * coef * (1 + iva)
            
            print(f"👉 {desc} - Precio unitario: $ {precio_unitario:.2f}")
            
            # Pedimos la cantidad
            try:
                cantidad = float(input("¿Qué cantidad lleva?: "))
            except ValueError:
                print("❌ Cantidad inválida. Se cancela este producto.")
                continue

            subtotal = precio_unitario * cantidad
            total_presupuesto += subtotal

            # 3. Guardamos el detalle CON EL PRECIO CONGELADO (como diseñaste tu base de datos)
            cursor.execute('''
                INSERT INTO presupuesto_detalles (presupuesto_id, producto_id, cantidad, precio_unitario_congelado)
                VALUES (?, ?, ?, ?)
            ''', (presupuesto_id, prod_id, cantidad, precio_unitario))
            
            items.append(f"{cantidad}x {desc[:20]:<20} | $ {precio_unitario:>8.2f} | Sub: $ {subtotal:>8.2f}")
            print(f"✅ Agregado. (Subtotal acumulado: $ {total_presupuesto:.2f})")
        else:
            print("❌ Producto no encontrado. Intente de nuevo.")

    # 4. Actualizamos el total general en la cabecera
    cursor.execute("UPDATE presupuestos SET total = ? WHERE id = ?", (total_presupuesto, presupuesto_id))
    
    # Guardamos todos los cambios en la base de datos
    conexion.commit()
    conexion.close()

    # 5. Imprimimos el "Ticket" final
    print("\n" + "="*50)
    print(f"🏠 HERRAJES CONTABLE - PRESUPUESTO N° {presupuesto_id}")
    print(f"👤 Cliente: {cliente}")
    print("-" * 50)
    for item in items:
        print(item)
    print("-" * 50)
    print(f"💰 TOTAL A PAGAR: $ {total_presupuesto:.2f}")
    print("="*50 + "\n")

if __name__ == '__main__':
    nuevo_presupuesto()