import sqlite3

def ver_productos():
    # 1. Nos conectamos a la base de datos
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()

    # 2. Hacemos la consulta agregando 'p.stock'
    query = '''
        SELECT 
            p.codigo_proveedor, 
            p.descripcion, 
            pr.nombre AS proveedor,
            p.costo_base, 
            p.coeficiente_ganancia, 
            p.iva,
            p.stock
        FROM productos p
        JOIN proveedores pr ON p.proveedor_id = pr.id
    '''
    
    cursor.execute(query)
    productos = cursor.fetchall()

    # 3. Encabezado más ancho para que entre el Stock
    print("\n" + "="*105)
    print(f"{'CÓDIGO':<10} | {'DESCRIPCIÓN':<30} | {'PROVEEDOR':<20} | {'STOCK':<8} | {'PRECIO DE VENTA'}")
    print("="*105)

    # 4. Recorremos los productos
    for prod in productos:
        codigo, desc, proveedor, costo, coef, iva, stock = prod # Desempaquetamos los 7 datos

        # Fórmula: Costo * Ganancia * (1 + IVA)
        precio_final = costo * coef * (1 + iva)

        # Imprimimos la fila con el stock incluido
        print(f"{codigo:<10} | {desc:<30} | {proveedor:<20} | {stock:<8} | $ {precio_final:.2f}")

    print("="*105 + "\n")
    conexion.close()

if __name__ == '__main__':
    ver_productos()