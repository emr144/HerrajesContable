import sqlite3

def ver_productos():
    # 1. Nos conectamos a la base de datos
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()

    # 2. Hacemos una consulta (query) uniendo las tablas de productos y proveedores
    query = '''
        SELECT 
            p.codigo_proveedor, 
            p.descripcion, 
            pr.nombre AS proveedor,
            p.costo_base, 
            p.coeficiente_ganancia, 
            p.iva
        FROM productos p
        JOIN proveedores pr ON p.proveedor_id = pr.id
    '''
    
    cursor.execute(query)
    productos = cursor.fetchall() # Esto trae todos los resultados

    # 3. Imprimimos el encabezado de nuestra "tabla" en la consola
    print("\n" + "="*85)
    print(f"{'CÓDIGO':<10} | {'DESCRIPCIÓN':<30} | {'PROVEEDOR':<20} | {'PRECIO DE VENTA'}")
    print("="*85)

    # 4. Recorremos los productos y calculamos el precio final
    for prod in productos:
        codigo = prod[0]
        desc = prod[1]
        proveedor = prod[2]
        costo = prod[3]
        coef = prod[4]
        iva = prod[5]

        # La fórmula mágica: Costo * Ganancia * (1 + IVA)
        # Ejemplo: 1200 * 1.6 * 1.21
        precio_final = costo * coef * (1 + iva)

        # Imprimimos la fila dándole formato para que se vea ordenado
        print(f"{codigo:<10} | {desc:<30} | {proveedor:<20} | $ {precio_final:.2f}")

    print("="*85 + "\n")
    conexion.close()

if __name__ == '__main__':
    ver_productos()