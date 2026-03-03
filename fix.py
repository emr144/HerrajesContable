import sqlite3

# Ejecuta este código para crear la tabla que falta
conexion = sqlite3.connect('herrajes.db')
cursor = conexion.cursor()
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
# Insertamos un cliente por defecto para que el buscador no falle
cursor.execute("INSERT OR IGNORE INTO clientes (id, nombre) VALUES (1, 'Consumidor Final')")
conexion.commit()
conexion.close()
print("✅ Tabla 'clientes' creada. Ahora los botones deberían funcionar.")