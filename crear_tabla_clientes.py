import sqlite3

def crear_base_datos_clientes():
    try:
        # Nos conectamos a tu base de datos actual
        conexion = sqlite3.connect('herrajes.db')
        cursor = conexion.cursor()
        
        print("Conectado a la base de datos. Creando tabla...")
        
        # Creamos la tabla de clientes con todos los campos que tus otros archivos esperan
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT,
                direccion TEXT,
                email TEXT,
                cuit_dni TEXT
            )
        ''')
        
        # Insertamos un cliente por defecto para que el sistema tenga algo que leer
        cursor.execute("INSERT OR IGNORE INTO clientes (id, nombre) VALUES (1, 'Consumidor Final')")
        
        conexion.commit()
        conexion.close()
        print("✅ ¡ÉXITO! La tabla 'clientes' ya existe en herrajes.db")
        
    except Exception as e:
        print(f"❌ Error al crear la tabla: {e}")

if __name__ == "__main__":
    crear_base_datos_clientes()