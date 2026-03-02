import sqlite3

def actualizar_estructura():
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    
    # Creamos la tabla de clientes formalmente
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
    
    conexion.commit()
    conexion.close()
    print("✅ Tabla de clientes creada con éxito.")

if __name__ == "__main__":
    actualizar_estructura()