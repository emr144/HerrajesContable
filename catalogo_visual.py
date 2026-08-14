import tkinter as tk
from tkinter import messagebox, ttk
import os
import psycopg2
import sqlite3 # Import sqlite3
from PIL import Image, ImageTk # Keep PIL imports
import styles as st # Importamos los estilos
import database # Importamos para obtener la ruta

# --- Funciones Auxiliares para Normalización de Búsqueda ---
def _normalize_string_for_sql_search(column_name):
    """Genera un fragmento SQL para normalizar una cadena para búsqueda.
    Elimina espacios, guiones, guiones bajos, barras y acentos comunes en español.
    """
    n = f"LOWER({column_name})"
    for char in [" ", "-", "_", "/", ".", ",", "(", ")", "[", "]", "*", "+", "|", ":", ";"]:
        n = f"REPLACE({n}, '{char}', '')"
    replacements = [
        ('á','a'),('é','e'),('í','i'),('ó','o'),('ú','u'),('ü','u'),('ñ','n'),('ç','c'),
        ('Á','a'),('É','e'),('Í','i'),('Ó','o'),('Ú','u'),('Ü','u'),('Ñ','n'),('Ç','c')
    ]
    for old, new in replacements:
        n = f"REPLACE({n}, '{old}', '{new}')"
    return n

def _normalize_python_string_for_search(text):
    """Normaliza una cadena de Python para comparación, eliminando acentos y caracteres especiales."""
    text = text.lower().replace(' ', '').replace('-', '').replace('_', '').replace('/', '')
    return text.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ü', 'u').replace('ñ', 'n')

# Global para mapear sugerencias
sugerencias_map = {}

def obtener_productos(filtro=""):
    """Consulta la DB buscando por código o descripción.
    Búsqueda flexible: encuentra palabras en cualquier orden.
    """
    conexion = database.conectar()
    if not conexion: return []
    cursor = conexion.cursor()
    tokens = _normalize_python_string_for_search(filtro).split()
    if not tokens: return []

    norm_cod = _normalize_string_for_sql_search("codigo_proveedor")
    norm_desc = _normalize_string_for_sql_search("descripcion")
    
    # Busca: código O descripción deben contener TODAS las palabras
    cond_parts = []
    params = []
    for t in tokens:
        if t:
            cond_parts.append(f"({norm_cod} LIKE ? OR {norm_desc} LIKE ?)")
            params.extend([f"%{t}%", f"%{t}%"])
    
    if not cond_parts: return []
    
    where_clause = " AND ".join(cond_parts) + " AND estado = 'ACTIVO'"
    query = f"SELECT id, codigo_proveedor, descripcion FROM productos WHERE {where_clause} LIMIT 10"
    
    cursor.execute(query, tuple(params))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def actualizar_sugerencias(event=None):
    """Se ejecuta cada vez que el usuario escribe en la caja de búsqueda"""
    texto = entrada_busqueda.get().strip()
    lista_sugerencias.delete(0, tk.END)
    sugerencias_map.clear()
    
    if len(texto) < 2:
        lista_sugerencias.place_forget()
        return

    productos = obtener_productos(texto)
    
    if productos:
        for p in productos:
            display = f"{p[1]} - {p[2]}"
            lista_sugerencias.insert(tk.END, display)
            sugerencias_map[display] = p[0] # Guardamos el ID
        
        # Posicionamiento dinámico de la lista
        lista_sugerencias.place(x=entrada_busqueda.winfo_x(), 
                                 y=entrada_busqueda.winfo_y() + entrada_busqueda.winfo_height())
        lista_sugerencias.lift()
    else:
        lista_sugerencias.place_forget()

def seleccionar_producto(event=None):
    """Carga el producto seleccionado de la lista"""
    if not lista_sugerencias.curselection():
        return
    
    seleccion = lista_sugerencias.get(lista_sugerencias.curselection())
    producto_id = sugerencias_map.get(seleccion)
    
    entrada_busqueda.delete(0, tk.END)
    # Insertamos el código solo visualmente
    entrada_busqueda.insert(0, seleccion.split(" - ")[0])
    lista_sugerencias.place_forget()
    mostrar_detalle(producto_id=producto_id)

def mostrar_detalle(codigo_buscado=None, producto_id=None):
    """Muestra la info y la foto en tamaño grande"""
    conexion = database.conectar()
    if not conexion: return # No need to import sqlite3 here, database.py handles it
    cursor = conexion.cursor()

    if producto_id:
        where_clause = "WHERE p.id = ?"
        param = producto_id
    else:
        where_clause = "WHERE p.codigo_proveedor = ?"
        param = entrada_busqueda.get().strip().upper()

    query = '''
        SELECT p.descripcion, p.costo_base, p.coeficiente_ganancia, p.iva, pr.descuento_global, pr.incremento_global, p.codigo_proveedor
        FROM productos p
        JOIN proveedores pr ON p.proveedor_id = pr.id
        {where_clause}
    ''' # Use %s placeholder
    cursor.execute(query, (param,))
    producto = cursor.fetchone()
    conexion.close()

    if producto:
        desc, costo, coef, iva, desc_g, inc_g, cod_real = producto
        # Aplicamos el descuento e incremento del proveedor al precio final
        precio_final = costo * (1 - (desc_g or 0)) * (1 + (inc_g or 0)) * coef * (1 + iva)
        
        label_desc.config(text=desc)
        label_codigo_info.config(text=f"Código: {cod_real}")
        label_precio.config(text=f"Precio Venta: $ {precio_final:.2f}")

        # --- GESTIÓN DE IMAGEN ---
        ruta_imagen = f"imagenes_productos/{cod_real}.jpg"
        if os.path.exists(ruta_imagen):
            try:
                img = Image.open(ruta_imagen)
                # Redimensionar a 500px manteniendo proporción y alta calidad
                img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                
                label_imagen.config(image=img_tk, text="") 
                label_imagen.image = img_tk 
            except Exception as e:
                label_imagen.config(image='', text=f"[ Error: {e} ]", fg="red")
        else:
            label_imagen.config(image='', text="[ Sin imagen disponible ]", fg="gray")
    else:
        messagebox.showwarning("No encontrado", f"El código '{codigo_buscado}' no existe.")

# --- INTERFAZ GRÁFICA ---
def montar_interfaz(parent):
    global entrada_busqueda, lista_sugerencias, label_desc, label_codigo_info, label_precio, label_imagen
    
    ventana = tk.Frame(parent, bg=st.BG_MAIN)
    ventana.config(padx=25, pady=25) # Mantenemos el padding

    tk.Label(ventana, text="Buscar por Nombre o Código:", font=st.FONT_LABEL, 
             bg=st.BG_MAIN, fg=st.TEXT_SECONDARY).pack(anchor="w")

    frame_busqueda = tk.Frame(ventana, bg=st.BG_MAIN)
    frame_busqueda.pack(fill=tk.X, pady=5)

    entrada_busqueda = tk.Entry(frame_busqueda, width=40, **st.estilo_entrada())
    entrada_busqueda.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    entrada_busqueda.bind('<KeyRelease>', actualizar_sugerencias)
    entrada_busqueda.bind('<Return>', lambda e: mostrar_detalle())

    btn_buscar = tk.Button(frame_busqueda, text=" 🔍 BUSCAR ", command=mostrar_detalle, **st.estilo_boton(st.ACCENT))
    btn_buscar.pack(side=tk.RIGHT)

    # Sugerencias flotantes
    lista_sugerencias = tk.Listbox(ventana, font=st.FONT_NORMAL, height=5, width=60, 
                                   bg=st.BG_CARD, fg="white", selectbackground=st.ACCENT, bd=0)
    lista_sugerencias.bind('<<ListboxSelect>>', seleccionar_producto)

    tk.Frame(ventana, height=2, bg=st.BG_CARD).pack(fill=tk.X, pady=20)

    # Datos del producto
    label_desc = tk.Label(ventana, text="Esperando búsqueda...", font=st.FONT_TITLE, wraplength=550,
                          bg=st.BG_MAIN, fg=st.TEXT_PRIMARY)
    label_desc.pack(pady=5)

    label_codigo_info = tk.Label(ventana, text="Código: ---", font=st.FONT_LABEL, 
                                 bg=st.BG_MAIN, fg=st.TEXT_SECONDARY)
    label_codigo_info.pack()

    label_precio = tk.Label(ventana, text="$ 0.00", font=("Inter", 24, "bold"), 
                            bg=st.BG_MAIN, fg=st.ACCENT)
    label_precio.pack(pady=15)

    # Contenedor de Imagen (Sin anchos fijos para que la imagen mande)
    label_imagen = tk.Label(ventana, text="[ Imagen del Producto ]", font=st.FONT_NORMAL, 
                            bg=st.BG_CARD, fg=st.TEXT_SECONDARY, relief="flat")
    label_imagen.pack(pady=10, fill=tk.BOTH, expand=True)
    
    return ventana

if __name__ == '__main__':
    root = tk.Tk()
    st.aplicar_estilo_ventana(root)
    app = montar_interfaz(root)
    app.pack(fill="both", expand=True)
    root.mainloop()