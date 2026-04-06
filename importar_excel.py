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

def _ejecutar_importacion(proveedor_id, archivo_excel, numero_lista, fecha_lista, descuento_prov=None, incremento_prov=None, margen_defecto=1.6):
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
            productos_a_procesar.append((proveedor_id, cod, desc, prec, margen_defecto, numero_lista, fecha_lista or None))
            
    except Exception as e:
        return f"❌ Error leyendo o procesando el Excel: {e}"

    # --- FASE 2: TRANSACCIÓN RÁPIDA EN BASE DE DATOS ---
    conexion = None
    try:
        conexion = sqlite3.connect(db_path)
        cursor = conexion.cursor()
        
        # 1. Aseguramos índice (DDL)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_producto_proveedor ON productos (codigo_proveedor, proveedor_id)")
        
        # 1.5 Actualizamos el descuento global del proveedor si se indicó en el formulario
        if descuento_prov is not None:
            cursor.execute("UPDATE proveedores SET descuento_global = ? WHERE id = ?", (descuento_prov, proveedor_id))
        
        # Actualizamos el incremento global
        if incremento_prov is not None:
            cursor.execute("UPDATE proveedores SET incremento_global = ? WHERE id = ?", (incremento_prov, proveedor_id))

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
    
    def cargar_proveedores():
        try:
            conexion = sqlite3.connect(database.get_db_path())
            cursor = conexion.cursor()
            cursor.execute("SELECT id, nombre FROM proveedores ORDER BY nombre")
            proveedores = cursor.fetchall()
            conexion.close()
            
            nombres = [nombre for pid, nombre in proveedores]
            ventana.proveedor_map = {nombre: pid for pid, nombre in proveedores}
            ventana.lista_nombres_prov = nombres
            combo_proveedores['values'] = nombres
        except Exception as e:
            messagebox.showerror("Error DB", f"No se pudo leer la lista de proveedores: {e}")

    def seleccionar_archivo():
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo de precios",
            filetypes=(("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*"))
        )
        if filepath:
            ruta_archivo.set(filepath)
            label_archivo.config(text=os.path.basename(filepath), fg=st.TEXT_PRIMARY)

    def actualizar_solo_coeficientes():
        """Actualiza el descuento e incremento global del proveedor sin procesar un Excel."""
        proveedor_seleccionado = combo_proveedores.get()
        if not proveedor_seleccionado:
            messagebox.showwarning("Faltan datos", "Debes seleccionar un proveedor.")
            return

        proveedor_id = ventana.proveedor_map.get(proveedor_seleccionado)
        
        descuento_lista = entry_descuento_lista.get().strip().replace('%', '').replace(',', '.')
        incremento_lista = entry_incremento_lista.get().strip().replace('%', '').replace(',', '.')

        try:
            descuento_val = float(descuento_lista) / 100.0 if descuento_lista else 0.0
            incremento_val = float(incremento_lista) / 100.0 if incremento_lista else 0.0
        except ValueError:
            messagebox.showerror("Error", "Los valores de descuento e incremento deben ser números válidos.")
            return

        try:
            conexion = sqlite3.connect(database.get_db_path())
            cursor = conexion.cursor()
            cursor.execute("""
                UPDATE proveedores 
                SET descuento_global = ?, incremento_global = ?, fecha_modif_coeficiente = CURRENT_DATE 
                WHERE id = ?
            """, (descuento_val, incremento_val, proveedor_id))
            conexion.commit()
            conexion.close()
            messagebox.showinfo("Éxito", f"Coeficientes actualizados correctamente para {proveedor_seleccionado}.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar la base de datos: {e}")

    def iniciar_importacion():
        proveedor_seleccionado = combo_proveedores.get()
        archivo = ruta_archivo.get()

        if not proveedor_seleccionado or not archivo:
            messagebox.showwarning("Faltan datos", "Debes seleccionar un proveedor y un archivo Excel.")
            return

        proveedor_id = ventana.proveedor_map.get(proveedor_seleccionado)
        if not proveedor_id:
            messagebox.showerror("Error", "Proveedor no válido.")
            return

        numero_lista = entry_numero_lista.get().strip()
        fecha_lista = entry_fecha_lista.get().strip()
        descuento_lista = entry_descuento_lista.get().strip().replace('%', '').replace(',', '.')
        incremento_lista = entry_incremento_lista.get().strip().replace('%', '').replace(',', '.')
        margen_lista = entry_margen_lista.get().strip().replace(',', '.')

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

        try:
            descuento_val = float(descuento_lista) / 100.0 if descuento_lista else None
        except ValueError:
            messagebox.showerror("Error", "El descuento debe ser un número válido.")
            return

        try:
            incremento_val = float(incremento_lista) / 100.0 if incremento_lista else None
        except ValueError:
            messagebox.showerror("Error", "El incremento debe ser un número válido.")
            return

        try:
            margen_val = float(margen_lista) if margen_lista else 1.6
        except ValueError:
            messagebox.showerror("Error", "El margen de ganancia debe ser un número válido (ej: 1.6).")
            return

        btn_importar.config(state="disabled", text="Importando...")
        ventana.update_idletasks()
        
        resultado = _ejecutar_importacion(proveedor_id, archivo, numero_lista, fecha_para_db, descuento_val, incremento_val, margen_val)
        
        messagebox.showinfo("Resultado de Importación", resultado)
        btn_importar.config(state="normal", text="Iniciar Importación")
        # Ya no destruimos la ventana porque es una pestaña

    ventana = tk.Frame(parent, bg=st.BG_MAIN)
    ventana.config(padx=30, pady=20)
    ventana.refrescar_contenido = cargar_proveedores # Exponer función para el main.py

    tk.Label(ventana, text="Importar Lista de Precios", font=st.FONT_TITLE, bg=st.BG_MAIN, fg=st.TEXT_PRIMARY).pack(pady=(0, 20))

    frame_proveedor = tk.Frame(ventana, bg=st.BG_MAIN)
    frame_proveedor.pack(fill="x", pady=5)
    tk.Label(frame_proveedor, text="1. Seleccionar Proveedor:", font=st.FONT_LABEL, bg=st.BG_MAIN, fg=st.TEXT_SECONDARY).pack(anchor="w")
    
    def filtrar_proveedores(event):
        if event.keysym in ('Down', 'Up', 'Return', 'Escape', 'Tab', 'Left', 'Right'): return
        
        texto = combo_proveedores.get().lower()
        lista_completa = getattr(ventana, 'lista_nombres_prov', [])
        
        if not texto:
            combo_proveedores['values'] = lista_completa
        else:
            # Cambiado a 'in' para búsqueda más flexible
            filtrados = [p for p in lista_completa if texto in p.lower()]
            combo_proveedores['values'] = filtrados
            if filtrados:
                combo_proveedores.event_generate('<Down>')

    def cargar_datos_proveedor_seleccionado(event):
        """Carga el descuento e incremento actual del proveedor seleccionado."""
        nombre = combo_proveedores.get()
        pid = ventana.proveedor_map.get(nombre)
        if not pid: return
        
        try:
            conexion = sqlite3.connect(database.get_db_path())
            cursor = conexion.cursor()
            cursor.execute("SELECT descuento_global, incremento_global FROM proveedores WHERE id = ?", (pid,))
            res = cursor.fetchone()
            conexion.close()
            
            if res:
                desc, inc = res
                entry_descuento_lista.delete(0, tk.END)
                entry_descuento_lista.insert(0, f"{(desc or 0.0) * 100:.2f}")
                entry_incremento_lista.delete(0, tk.END)
                entry_incremento_lista.insert(0, f"{(inc or 0.0) * 100:.2f}")
        except Exception as e:
            print(f"Error al cargar coeficientes: {e}")

    combo_proveedores = ttk.Combobox(frame_proveedor, font=st.FONT_INPUT)
    combo_proveedores.pack(fill="x", pady=5)
    combo_proveedores.bind("<KeyRelease>", filtrar_proveedores)
    combo_proveedores.bind("<<ComboboxSelected>>", cargar_datos_proveedor_seleccionado)

    cargar_proveedores()

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

    tk.Label(sub_frame, text="Descuento de Lista (%):", font=st.FONT_NORMAL, bg=st.BG_CARD, fg="white").grid(row=2, column=0, sticky="w", pady=2)
    entry_descuento_lista = tk.Entry(sub_frame, **st.estilo_entrada())
    entry_descuento_lista.grid(row=2, column=1, sticky="ew", padx=10, pady=2)
    entry_descuento_lista.insert(0, "0")

    tk.Label(sub_frame, text="Incremento de Lista (%):", font=st.FONT_NORMAL, bg=st.BG_CARD, fg="white").grid(row=3, column=0, sticky="w", pady=2)
    entry_incremento_lista = tk.Entry(sub_frame, **st.estilo_entrada())
    entry_incremento_lista.grid(row=3, column=1, sticky="ew", padx=10, pady=2)
    entry_incremento_lista.insert(0, "0")

    tk.Label(sub_frame, text="Margen Ganancia (Ej: 1.6):", font=st.FONT_NORMAL, bg=st.BG_CARD, fg="white").grid(row=4, column=0, sticky="w", pady=2)
    entry_margen_lista = tk.Entry(sub_frame, **st.estilo_entrada())
    entry_margen_lista.grid(row=4, column=1, sticky="ew", padx=10, pady=2)
    entry_margen_lista.insert(0, "1.6")

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

    btn_solo_coef = tk.Button(ventana, text="⚡ Actualizar Solo Coeficientes (Sin Excel)", command=actualizar_solo_coeficientes, **st.estilo_boton(st.ACCENT))
    st.configurar_hover(btn_solo_coef, st.ACCENT, st.BG_CARD)
    btn_solo_coef.pack(fill="x", pady=(10, 0))

    return ventana

if __name__ == '__main__':
    root = tk.Tk()
    st.aplicar_estilo_ventana(root)
    app = montar_interfaz(root)
    app.pack(fill="both", expand=True)
    root.mainloop()