import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import styles as st
from database import db

def _ejecutar_importacion(proveedor_id, archivo_excel, numero_lista, fecha_lista, descuento_prov=None, incremento_prov=None, margen_defecto=1.6):
    """Lógica de procesamiento de archivo y carga a la nube."""
    if not os.path.exists(archivo_excel):
        return f"❌ ERROR: No se encuentra el archivo '{archivo_excel}'"

    try:
        df = pd.read_excel(archivo_excel)
        df.columns = df.columns.astype(str).str.lower().str.strip()
        
        mapeo = {'código': 'codigo', 'codigo': 'codigo', 'descripción': 'descripcion', 
                 'descripcion': 'descripcion', 'costo base': 'costo', 'costo': 'costo', 'precio': 'costo'}
        df.rename(columns=mapeo, inplace=True)
        
        for col in ['codigo', 'descripcion', 'costo']:
            if col not in df.columns:
                return f"❌ ERROR: Columna '{col}' no encontrada en el Excel."
        
        productos_a_procesar = []
        for _, fila in df.iterrows():
            cod = str(fila.get('codigo', '')).strip()
            if not cod or cod == 'nan': continue
            
            try:
                prec = float(fila.get('costo', 0.0))
            except:
                prec = 0.0
            
            productos_a_procesar.append({
                "proveedor_id": proveedor_id,
                "codigo_proveedor": cod,
                "descripcion": str(fila.get('descripcion', '')).strip(),
                "costo_base": prec,
                "coeficiente_ganancia": margen_defecto,
                "estado": 'ACTIVO',
                "numero_lista": numero_lista,
                "fecha_lista": fecha_lista,
                "ultima_actualizacion": pd.Timestamp.now().strftime('%Y-%m-%d')
            })
            
        # 1. Actualizar datos del proveedor
        db.ejecutar_consulta("""
            UPDATE proveedores SET descuento_global = %s, incremento_global = %s, 
            fecha_modif_coeficiente = CURRENT_DATE WHERE id = %s
        """, (descuento_prov, incremento_prov, proveedor_id))

        # 2. Marcar historial como inactivo
        db.ejecutar_consulta("UPDATE productos SET estado = 'INACTIVO' WHERE proveedor_id = %s", (proveedor_id,))

        # 3. Cargar nuevos datos (UPSERT)
        db.table("productos").upsert(productos_a_procesar)

        return f"✨ Importación exitosa.\nSe procesaron {len(productos_a_procesar)} productos."

    except Exception as e:
        return f"❌ Error en el proceso: {e}"

def montar_interfaz(parent):
    def cargar_proveedores():
        try:
            resp = db.table("proveedores").select("id, nombre").order("nombre").execute()
            nombres = [p['nombre'] for p in resp.data]
            ventana.proveedor_map = {p['nombre']: p['id'] for p in resp.data}
            combo_proveedores['values'] = nombres
        except: pass

    def seleccionar_archivo():
        path = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx")])
        if path:
            ruta_archivo.set(path)
            label_archivo.config(text=os.path.basename(path))

    def actualizar_solo_coeficientes():
        """Actualiza coeficientes en la base compartida y sincroniza la copia local."""
        prov = combo_proveedores.get()
        if not prov:
            messagebox.showwarning("Atención", "Seleccione un proveedor primero.")
            return
        
        proveedor_id = ventana.proveedor_map.get(prov)
        
        try:
            desc = float(entry_desc.get().replace(',','.')) / 100
            inc = float(entry_inc.get().replace(',','.')) / 100
            coef = float(entry_coef.get().replace(',','.'))
        except ValueError:
            messagebox.showerror("Error", "Los valores numéricos no son válidos.")
            return

        confirmar = messagebox.askyesno("Confirmar", f"¿Desea actualizar los coeficientes de {prov} y todos sus productos en la nube?")
        if not confirmar: return

        try:
            consultas = [
                ("""
                    UPDATE proveedores SET descuento_global = %s, incremento_global = %s, 
                    fecha_modif_coeficiente = CURRENT_DATE WHERE id = %s
                """, (desc, inc, proveedor_id)),
                ("""
                    UPDATE productos SET coeficiente_ganancia = %s 
                    WHERE proveedor_id = %s AND estado = 'ACTIVO'
                """, (coef, proveedor_id)),
            ]

            for query, params in consultas:
                if not db.ejecutar_consulta(query, params):
                    raise RuntimeError("No se pudo actualizar la base compartida.")

            messagebox.showinfo("Éxito", f"Coeficientes de {prov} actualizados correctamente en la base compartida.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar: {e}")

    def iniciar():
        prov = combo_proveedores.get()
        arch = ruta_archivo.get()
        if not prov or not arch:
            messagebox.showwarning("Atención", "Seleccione proveedor y archivo.")
            return
        
        try:
            f_db = pd.to_datetime(entry_fecha.get(), dayfirst=True).strftime('%Y-%m-%d')
            d = float(entry_desc.get().replace(',','.')) / 100
            i = float(entry_inc.get().replace(',','.')) / 100
            c = float(entry_coef.get().replace(',','.'))
        except:
            messagebox.showerror("Error", "Revise los campos numéricos y la fecha.")
            return

        btn_importar.config(state="disabled", text="Sincronizando...")
        ventana.update_idletasks()
        
        res = _ejecutar_importacion(ventana.proveedor_map[prov], arch, entry_num.get(), f_db, d, i, c)
        
        messagebox.showinfo("Resultado", res)
        btn_importar.config(state="normal", text="🚀 Iniciar Importación")

    ventana = tk.Frame(parent, bg=st.BG_MAIN, padx=30, pady=20)
    ventana.refrescar_contenido = cargar_proveedores

    tk.Label(ventana, text="Sincronización de Precios", font=st.FONT_TITLE, bg=st.BG_MAIN, fg=st.TEXT_PRIMARY).pack(pady=10)
    
    combo_proveedores = ttk.Combobox(ventana, font=st.FONT_INPUT, state="readonly")
    combo_proveedores.pack(fill="x", pady=5)

    f = tk.Frame(ventana, bg=st.BG_CARD, padx=15, pady=15)
    f.pack(fill="x", pady=10)
    
    # Entradas
    tk.Label(f, text="N° Lista:", bg=st.BG_CARD, fg="white").grid(row=0, column=0, sticky="w")
    entry_num = tk.Entry(f, **st.estilo_entrada()); entry_num.grid(row=0, column=1, pady=2)
    
    tk.Label(f, text="Fecha:", bg=st.BG_CARD, fg="white").grid(row=1, column=0, sticky="w")
    entry_fecha = tk.Entry(f, **st.estilo_entrada()); entry_fecha.grid(row=1, column=1, pady=2)
    entry_fecha.insert(0, pd.Timestamp.now().strftime('%d-%m-%Y'))

    tk.Label(f, text="Descuento %:", bg=st.BG_CARD, fg="white").grid(row=2, column=0, sticky="w")
    entry_desc = tk.Entry(f, **st.estilo_entrada()); entry_desc.grid(row=2, column=1, pady=2); entry_desc.insert(0, "0")

    tk.Label(f, text="Incremento %:", bg=st.BG_CARD, fg="white").grid(row=3, column=0, sticky="w")
    entry_inc = tk.Entry(f, **st.estilo_entrada()); entry_inc.grid(row=3, column=1, pady=2); entry_inc.insert(0, "0")

    tk.Label(f, text="Coeficiente:", bg=st.BG_CARD, fg="white").grid(row=4, column=0, sticky="w")
    entry_coef = tk.Entry(f, **st.estilo_entrada()); entry_coef.grid(row=4, column=1, pady=2); entry_coef.insert(0, "1.6")

    f.columnconfigure(1, weight=1)

    # Selección de Archivo
    ruta_archivo = tk.StringVar()
    btn_file = tk.Button(ventana, text="📂 Seleccionar Excel", command=seleccionar_archivo, **st.estilo_boton(st.ACCENT))
    btn_file.pack(fill="x", pady=5)
    label_archivo = tk.Label(ventana, text="Ningún archivo seleccionado", bg=st.BG_MAIN, fg="gray")
    label_archivo.pack()

    # Botones de Acción
    btn_importar = tk.Button(ventana, text="🚀 Iniciar Importación Completa", command=iniciar, **st.estilo_boton())
    btn_importar.pack(fill="x", pady=(10, 5))

    btn_solo_coef = tk.Button(ventana, text="⚡ Actualizar Solo Coeficientes (Sin Excel)", command=actualizar_solo_coeficientes, **st.estilo_boton(st.ACCENT))
    btn_solo_coef.pack(fill="x", pady=5)

    cargar_proveedores()
    return ventana