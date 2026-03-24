import sqlite3
import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import styles as st
import database # Importamos para obtener la ruta

try:
    import pandas as pd
except ImportError:
    # Si estamos en un entorno gráfico, un print no se verá.
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Librería Faltante", "No tienes instalada la librería 'pandas'.\n\nEjecuta en tu terminal:\npip install pandas openpyxl")
    except tk.TclError:
        print("❌ ERROR: No tienes instalada la librería 'pandas'.", file=sys.stderr)
        print("Ejecuta en tu terminal: pip install pandas openpyxl", file=sys.stderr)
    sys.exit(1)

def _ejecutar_importacion(proveedor_id, archivo_excel, numero_lista, fecha_lista):
    """
    Importa o actualiza productos desde un Excel para un proveedor específico.
    Utiliza una operación UPSERT para mayor eficiencia.
    Incluye número y fecha de lista.
    """
    db_path = database.get_db_path()
    if not os.path.exists(archivo_excel):
        return f"❌ ERROR: No se encuentra el archivo '{archivo_excel}'"

    # --- FASE 1: PREPARACIÓN EN MEMORIA (SIN TOCAR LA DB) ---
    # Leemos y procesamos el Excel ANTES de abrir la conexión para evitar bloqueos.
    try:
        df = pd.read_excel(archivo_excel)
        df.columns = df.columns.astype(str).str.lower().str.strip()
        
        mapeo = {
            'código': 'codigo', 'codigo': 'codigo',
            'descripción': 'descripcion', 'descripcion': 'descripcion',
            'costo base': 'costo', 'costo': 'costo', 'precio': 'costo'
        }
        df.rename(columns=mapeo, inplace=True)
        
        for col in ['codigo', 'descripcion', 'costo']:
            if col not in df.columns:
                return f"❌ ERROR: Falta la columna obligatoria '{col}' en el Excel."
        
        productos_a_procesar = []
        for _, fila in df.iterrows():
            cod = str(fila.get('codigo', '')).strip()
            desc = str(fila.get('descripcion', '')).strip()
            try:
                prec = float(fila.get('costo', 0.0))
            except (ValueError, TypeError):
                prec = 0.0
            
            if not cod or cod == 'nan':
                continue
            
            # Añadimos numero_lista y fecha_lista a la tupla
            productos_a_procesar.append((proveedor_id, cod, desc, prec, 1.6, numero_lista, fecha_lista or None))
            
    except Exception as e:
        return f"❌ Error leyendo o procesando el Excel: {e}"

    # --- FASE 2: TRANSACCIÓN RÁPIDA EN BASE DE DATOS ---
    conexion = None
    try:
        conexion = sqlite3.connect(db_path)
        cursor = conexion.cursor()
        
        # 1. Aseguramos índice (DDL)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_producto_proveedor ON productos (codigo_proveedor, proveedor_id)")
        
        # 2. Marcar como inactivos (Inicia la transacción implícita)
        cursor.execute("UPDATE productos SET estado = 'INACTIVO' WHERE proveedor_id = ?", (proveedor_id,))

        # 3. Usar UPSERT para insertar o actualizar en bloque
        upsert_query = """
            INSERT INTO productos (proveedor_id, codigo_proveedor, descripcion, costo_base, coeficiente_ganancia, estado, ultima_actualizacion, numero_lista, fecha_lista)
            VALUES (?, ?, ?, ?, ?, 'ACTIVO', CURRENT_DATE, ?, ?)
            ON CONFLICT(codigo_proveedor, proveedor_id) DO UPDATE SET
                descripcion = excluded.descripcion,
                costo_base = excluded.costo_base,
                estado = 'ACTIVO',
                ultima_actualizacion = CURRENT_DATE,
                numero_lista = excluded.numero_lista,
                fecha_lista = excluded.fecha_lista;
        """
        cursor.executemany(upsert_query, productos_a_procesar)
        
        # 4. Confirmar cambios (Libera el lock inmediatamente)
        conexion.commit()

        # Generar un reporte del resultado
        cursor.execute("SELECT COUNT(*) FROM productos WHERE proveedor_id = ? AND estado = 'ACTIVO'", (proveedor_id,))
        activos_ahora = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM productos WHERE proveedor_id = ? AND estado = 'INACTIVO'", (proveedor_id,))
        inactivos_ahora = cursor.fetchone()[0]

        return (f"✨ ¡IMPORTACIÓN EXITOSA!\n\n"
                f"Proveedor ID: {proveedor_id}\n"
                f"Archivo: {os.path.basename(archivo_excel)}\n\n"
                f"✅ {len(productos_a_procesar)} productos del Excel procesados.\n"
                f"🔄 Total de productos ACTIVOS para este proveedor: {activos_ahora}\n"
                f"🗑️ Productos marcados como INACTIVOS: {inactivos_ahora}")
        
    except PermissionError:
        return "❌ ERROR: El Excel está abierto. Ciérralo y reintenta."
    except sqlite3.OperationalError as e:
        if "locked" in str(e):
            return "❌ ERROR: La base de datos está bloqueada. Cierra otras ventanas del programa e intenta de nuevo."
        return f"❌ Error Operacional de DB: {e}"
    except sqlite3.Error as e:
        if conexion: conexion.rollback()
        return f"❌ Error de Base de Datos: {e}"
    except Exception as e:
        if conexion: conexion.rollback()
        return f"❌ Error inesperado durante la importación: {e}"
    finally:
        if conexion:
            conexion.close()

def montar_interfaz(parent):
    """Crea una interfaz gráfica para seleccionar proveedor e importar el archivo."""
    
    def obtener_proveedores():
        try:
            conexion = sqlite3.connect(database.get_db_path())
            cursor = conexion.cursor()
            cursor.execute("SELECT id, nombre FROM proveedores ORDER BY nombre")
            proveedores = cursor.fetchall()
            conexion.close()
            return proveedores
        except Exception as e:
            messagebox.showerror("Error DB", f"No se pudo leer la lista de proveedores: {e}")
            return []

    def seleccionar_archivo():
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo de precios",
            filetypes=(("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*"))
        )
        if filepath:
            ruta_archivo.set(filepath)
            label_archivo.config(text=os.path.basename(filepath), fg=st.TEXT_PRIMARY)

    def iniciar_importacion():
        proveedor_seleccionado = combo_proveedores.get()
        archivo = ruta_archivo.get()

        if not proveedor_seleccionado or not archivo:
            messagebox.showwarning("Faltan datos", "Debes seleccionar un proveedor y un archivo Excel.")
            return

        proveedor_id = proveedor_map.get(proveedor_seleccionado)
        if not proveedor_id:
            messagebox.showerror("Error", "Proveedor no válido.")
            return

        numero_lista = entry_numero_lista.get().strip()
        fecha_lista = entry_fecha_lista.get().strip()

        fecha_para_db = None
        # Validación simple de formato de fecha
        if fecha_lista:
            try:
                # Convertimos de DD-MM-AAAA (Visual) a AAAA-MM-DD (Base de Datos)
                fecha_dt = pd.to_datetime(fecha_lista, format='%d-%m-%Y')
                fecha_para_db = fecha_dt.strftime('%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Error de Formato", "La fecha debe tener el formato DD-MM-AAAA.")
                return

        btn_importar.config(state="disabled", text="Importando...")
        ventana.update_idletasks()
        
        resultado = _ejecutar_importacion(proveedor_id, archivo, numero_lista, fecha_para_db)
        
        messagebox.showinfo("Resultado de Importación", resultado)
        btn_importar.config(state="normal", text="Iniciar Importación")
        # Ya no destruimos la ventana porque es una pestaña

    ventana = tk.Frame(parent, bg=st.BG_MAIN)
    ventana.config(padx=30, pady=20)

    tk.Label(ventana, text="Importar Lista de Precios", font=st.FONT_TITLE, bg=st.BG_MAIN, fg=st.TEXT_PRIMARY).pack(pady=(0, 20))

    frame_proveedor = tk.Frame(ventana, bg=st.BG_MAIN)
    frame_proveedor.pack(fill="x", pady=5)
    tk.Label(frame_proveedor, text="1. Seleccionar Proveedor:", font=st.FONT_LABEL, bg=st.BG_MAIN, fg=st.TEXT_SECONDARY).pack(anchor="w")
    
    proveedores_lista = obtener_proveedores()
    lista_nombres_prov = [nombre for pid, nombre in proveedores_lista]
    proveedor_map = {nombre: pid for pid, nombre in proveedores_lista}
    
    def filtrar_proveedores(event):
        if event.keysym in ('Down', 'Up', 'Return', 'Escape', 'Tab', 'Left', 'Right'): return
        
        texto = combo_proveedores.get().lower()
        
        if not texto:
            combo_proveedores['values'] = lista_nombres_prov
        else:
            filtrados = [p for p in lista_nombres_prov if p.lower().startswith(texto)]
            combo_proveedores['values'] = filtrados
            if filtrados:
                combo_proveedores.event_generate('<Down>')

    combo_proveedores = ttk.Combobox(frame_proveedor, values=lista_nombres_prov, font=st.FONT_INPUT)
    combo_proveedores.pack(fill="x", pady=5)
    combo_proveedores.bind("<KeyRelease>", filtrar_proveedores)

    # --- Nuevos campos para número y fecha de lista ---
    frame_datos_lista = tk.Frame(ventana, bg=st.BG_MAIN)
    frame_datos_lista.pack(fill="x", pady=10)
    tk.Label(frame_datos_lista, text="2. Datos de la Lista de Precios (Opcional):", font=st.FONT_LABEL, bg=st.BG_MAIN, fg=st.TEXT_SECONDARY).pack(anchor="w")

    sub_frame = tk.Frame(frame_datos_lista, bg=st.BG_CARD, padx=10, pady=10)
    sub_frame.pack(fill="x")
    sub_frame.columnconfigure(1, weight=1)

    tk.Label(sub_frame, text="N° de Lista:", font=st.FONT_NORMAL, bg=st.BG_CARD, fg="white").grid(row=0, column=0, sticky="w", pady=2)
    entry_numero_lista = tk.Entry(sub_frame, **st.estilo_entrada())
    entry_numero_lista.grid(row=0, column=1, sticky="ew", padx=10, pady=2)

    tk.Label(sub_frame, text="Fecha (DD-MM-AAAA):", font=st.FONT_NORMAL, bg=st.BG_CARD, fg="white").grid(row=1, column=0, sticky="w", pady=2)
    entry_fecha_lista = tk.Entry(sub_frame, **st.estilo_entrada())
    entry_fecha_lista.grid(row=1, column=1, sticky="ew", padx=10, pady=2)
    entry_fecha_lista.insert(0, pd.Timestamp.now().strftime('%d-%m-%Y'))

    frame_archivo = tk.Frame(ventana, bg=st.BG_MAIN)
    frame_archivo.pack(fill="x", pady=15)
    tk.Label(frame_archivo, text="3. Seleccionar Archivo Excel:", font=st.FONT_LABEL, bg=st.BG_MAIN, fg=st.TEXT_SECONDARY).pack(anchor="w")
    
    ruta_archivo = tk.StringVar()
    btn_seleccionar = tk.Button(frame_archivo, text="📂 Elegir Archivo (.xlsx)", command=seleccionar_archivo, **st.estilo_boton(st.ACCENT))
    st.configurar_hover(btn_seleccionar, st.ACCENT, st.BG_CARD)
    btn_seleccionar.pack(fill="x", pady=5)
    label_archivo = tk.Label(frame_archivo, text="Ningún archivo seleccionado", font=st.FONT_NORMAL, bg=st.BG_MAIN, fg="gray")
    label_archivo.pack(pady=5)

    btn_importar = tk.Button(ventana, text="🚀 Iniciar Importación", command=iniciar_importacion, **st.estilo_boton())
    st.configurar_hover(btn_importar)
    btn_importar.pack(fill="x", pady=(20, 0))

    return ventana

if __name__ == '__main__':
    root = tk.Tk()
    st.aplicar_estilo_ventana(root)
    app = montar_interfaz(root)
    app.pack(fill="both", expand=True)
    root.mainloop()