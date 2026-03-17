import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import styles as st 

def montar_interfaz(notebook):
    frame = tk.Frame(notebook, bg=st.BG_MAIN)
    frame.editando_id = None # Variable para saber si estamos editando un registro
    
    # --- Variables ---
    var_proveedor = tk.StringVar()
    var_tipo_cuenta = tk.StringVar(value="Formal")
    var_tipo_mov = tk.StringVar(value="Factura")
    var_monto = tk.StringVar(value="0")
    var_desc = tk.StringVar()

    # --- Título y Selector de Fábrica ---
    header = tk.Frame(frame, bg=st.BG_MAIN)
    header.pack(fill="x", padx=20, pady=10)
    
    tk.Label(header, text="ESTADO DE CUENTA:", font=("Inter", 14, "bold"), fg="white", bg=st.BG_MAIN).pack(side="left")
    
    combo_prov = ttk.Combobox(header, textvariable=var_proveedor, state="readonly", font=st.FONT_INPUT)
    combo_prov.pack(side="left", padx=10)
    
    tk.Label(header, text="Cuenta:", fg="white", bg=st.BG_MAIN).pack(side="left", padx=5)
    selector_cuenta = ttk.OptionMenu(header, var_tipo_cuenta, "Formal", "Formal", "Informal")
    selector_cuenta.pack(side="left")

    # --- Formulario de Carga Rápida ---
    form = tk.Frame(frame, bg=st.BG_CARD, padx=15, pady=10)
    form.pack(padx=20, fill="x", pady=5)

    tk.Label(form, text="Acción:", fg="white", bg=st.BG_CARD).grid(row=0, column=0, padx=5)
    ttk.OptionMenu(form, var_tipo_mov, "Factura", "Factura", "Pago", "Saldo Inicial").grid(row=0, column=1, padx=5)

    tk.Label(form, text="Monto $:", fg="white", bg=st.BG_CARD).grid(row=0, column=2, padx=5)
    tk.Entry(form, textvariable=var_monto, width=15, **st.estilo_entrada()).grid(row=0, column=3, padx=5)

    tk.Label(form, text="Detalle:", fg="white", bg=st.BG_CARD).grid(row=0, column=4, padx=5)
    tk.Entry(form, textvariable=var_desc, width=25, **st.estilo_entrada()).grid(row=0, column=5, padx=5)
    
    # Definimos los botones aquí para poder configurarlos luego
    btn_registrar = tk.Button(form, text="REGISTRAR", bg=st.ACCENT, fg="white", font=("Inter", 9, "bold"))
    btn_registrar.grid(row=0, column=6, padx=10)
    
    btn_cancelar = tk.Button(form, text="CANCELAR", bg=st.RED_ERROR, fg="white", font=("Inter", 9, "bold"))
    # El botón cancelar lo ocultamos inicialmente (.grid_forget() se llamará al resetear)

    # --- Tabla Tipo "Libro Mayor" ---
    tree_frame = tk.Frame(frame, bg=st.BG_MAIN)
    tree_frame.pack(padx=20, pady=10, fill="both", expand=True)

    columnas = ("Fecha", "Detalle", "Debe (Factura)", "Haber (Pago)", "Saldo", "Editar", "Eliminar")
    tree = ttk.Treeview(tree_frame, columns=columnas, show='headings')
    
    for col in columnas:
        tree.heading(col, text=col.replace("Editar", "✏️").replace("Eliminar", "🗑️")) # Iconos en cabecera
        
        if col in ["Editar", "Eliminar"]:
            tree.column(col, width=50, anchor="center")
        else:
            tree.column(col, width=120, anchor="center")
    
    # Ajuste para detalle más ancho
    tree.column("Detalle", width=250, anchor="w")
    
    tree.pack(side="left", fill="both", expand=True)

    # --- Lógica de Cálculos ---
    def reset_form():
        """Limpia el formulario y sale del modo edición"""
        frame.editando_id = None
        var_monto.set("0")
        var_desc.set("")
        var_tipo_mov.set("Factura")
        btn_registrar.config(text="REGISTRAR", bg=st.ACCENT)
        btn_cancelar.grid_forget()

    def calcular_y_mostrar(_=None):
        """Calcula el saldo acumulado línea por línea"""
        for item in tree.get_children(): tree.delete(item)
        
        prov_nombre = var_proveedor.get()
        t_cuenta = var_tipo_cuenta.get()
        if not prov_nombre: return

        try:
            conn = sqlite3.connect('herrajes.db')
            cursor = conn.cursor()
            
            # Buscamos el ID
            cursor.execute("SELECT id FROM proveedores WHERE nombre=?", (prov_nombre,))
            res_prov = cursor.fetchone()
            if not res_prov: return
            prov_id = res_prov[0]

            # Traemos movimientos ordenados por fecha/id
            cursor.execute("""
                SELECT id, fecha, tipo_movimiento, monto, descripcion 
                FROM cuenta_corriente_proveedores 
                WHERE id_proveedor = ? AND tipo_cuenta = ?
                ORDER BY id ASC
            """, (prov_id, t_cuenta))
            
            saldo_acumulado = 0.0
            for row_id, fecha, tipo, monto, desc in cursor.fetchall():
                debe = ""
                haber = ""
                
                if tipo in ['Factura', 'Saldo Inicial']:
                    debe = f"$ {monto:,.2f}"
                    saldo_acumulado += monto
                else: # Es un Pago
                    haber = f"$ {monto:,.2f}"
                    saldo_acumulado -= monto
                
                # Insertamos la fila, usando el ID de base de datos como el ID del item (iid)
                tree.insert("", "end", iid=row_id, values=(fecha, desc, debe, haber, f"$ {saldo_acumulado:,.2f}", "✏️", "🗑️"))
            
            conn.close()
        except Exception as e:
            print(f"Error: {e}")

    def cargar_edicion(row_id):
        """Carga los datos de la fila seleccionada en el formulario"""
        try:
            conn = sqlite3.connect('herrajes.db')
            cursor = conn.cursor()
            cursor.execute("SELECT tipo_movimiento, monto, descripcion FROM cuenta_corriente_proveedores WHERE id=?", (row_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                frame.editando_id = row_id
                var_tipo_mov.set(row[0])
                var_monto.set(str(row[1]))
                var_desc.set(row[2])
                
                # Cambiamos visualmente el botón para indicar edición
                btn_registrar.config(text="💾 GUARDAR CAMBIOS", bg="#D97706") # Naranja
                btn_cancelar.grid(row=0, column=7, padx=5) # Mostramos botón cancelar
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar para editar: {e}")

    def eliminar_registro(row_id):
        """Elimina el registro de la DB"""
        if messagebox.askyesno("Confirmar", "¿Eliminar este movimiento?\nEsto recalculará el saldo."):
            try:
                conn = sqlite3.connect('herrajes.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cuenta_corriente_proveedores WHERE id=?", (row_id,))
                conn.commit()
                conn.close()
                
                if frame.editando_id == row_id:
                    reset_form()
                
                calcular_y_mostrar()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar: {e}")

    def on_tree_click(event):
        """Detecta clic en las columnas de editar o eliminar"""
        region = tree.identify_region(event.x, event.y)
        if region != "cell": return
        
        col_id = tree.identify_column(event.x)
        row_id = tree.identify_row(event.y)
        
        if not row_id: return
        
        # Columnas: #1..#5 datos, #6 Editar, #7 Eliminar
        if col_id == "#6": # Columna Editar
            cargar_edicion(row_id)
        elif col_id == "#7": # Columna Eliminar
            eliminar_registro(row_id)

    def guardar():
        conn = None
        try:
            # 1. Validaciones previas
            monto_str = var_monto.get()
            if not monto_str: 
                messagebox.showwarning("Atención", "Por favor ingrese un monto.")
                return
            monto_f = float(monto_str)
            
            prov_nombre = var_proveedor.get()
            if not prov_nombre:
                messagebox.showwarning("Atención", "Debe seleccionar un proveedor.")
                return
                
            desc = var_desc.get()
            tipo = var_tipo_mov.get()

            conn = sqlite3.connect('herrajes.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM proveedores WHERE nombre=?", (prov_nombre,))
            res = cursor.fetchone()
            
            if not res:
                messagebox.showerror("Error", "El proveedor seleccionado no existe en la base de datos.")
                return
                
            prov_id = res[0]
            
            if frame.editando_id:
                # MODO EDICIÓN: ACTUALIZAR
                cursor.execute("""
                    UPDATE cuenta_corriente_proveedores 
                    SET tipo_movimiento=?, monto=?, descripcion=?, tipo_cuenta=?
                    WHERE id=?
                """, (tipo, monto_f, desc, var_tipo_cuenta.get(), frame.editando_id))
            else:
                # MODO NUEVO: INSERTAR
                cursor.execute("""
                    INSERT INTO cuenta_corriente_proveedores 
                    (id_proveedor, tipo_cuenta, tipo_movimiento, monto, metodo_pago, descripcion)
                    VALUES (?, ?, ?, ?, 'N/A', ?)
                """, (prov_id, var_tipo_cuenta.get(), tipo, monto_f, desc))
            
            conn.commit()
            
            reset_form()
            calcular_y_mostrar()
            
        except ValueError:
            messagebox.showerror("Error de Formato", "El monto debe ser un número válido.")
        except Exception as e:
            messagebox.showerror("Error al Guardar", f"Ocurrió un error inesperado:\n{e}")
        finally:
            if conn: conn.close()

    def cargar_provs():
        try:
            conn = sqlite3.connect('herrajes.db')
            cursor = conn.cursor()
            cursor.execute("SELECT nombre FROM proveedores")
            combo_prov['values'] = [r[0] for r in cursor.fetchall()]
            conn.close()
        except: pass

    # Botones y Eventos
    # Asignamos los comandos a los botones que creamos arriba
    btn_registrar.config(command=guardar)
    btn_cancelar.config(command=reset_form)
    
    tree.bind("<Button-1>", on_tree_click)
    
    combo_prov.bind("<<ComboboxSelected>>", calcular_y_mostrar)
    # Si cambias de Blanco a Negro, que se refresque la tabla
    var_tipo_cuenta.trace_add("write", lambda *args: calcular_y_mostrar())

    cargar_provs()
    return frame