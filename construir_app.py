import os
import sys
import shutil
import subprocess

def crear_acceso_directo(target_exe, icon_path):
    """Crea un acceso directo en el Escritorio automáticamente."""
    try:
        import win32com.client
        shell = win32com.client.Dispatch('WScript.Shell')
        
        # Usamos SpecialFolders: encuentra el Escritorio real (aunque uses OneDrive)
        desktop = shell.SpecialFolders("Desktop")
        path_link = os.path.join(desktop, "Herrajes Contable.lnk")
        
        shortcut = shell.CreateShortcut(path_link)
        shortcut.TargetPath = target_exe
        shortcut.WorkingDirectory = os.path.dirname(target_exe)
        shortcut.IconLocation = f"{icon_path},0"
        shortcut.save()
        print(f"Acceso directo creado en el Escritorio: {path_link}")
    except Exception as e:
        print(f"No se pudo crear el acceso directo automáticamente: {e}")

def instalar_dependencia():
    print("⏳ Instalando dependencias de construcción (PyInstaller, pywin32)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "pywin32"])

def crear_ejecutable():
    print("\n" + "="*50)
    print(" INICIANDO CONSTRUCCIÓN DE HERRAJES CONTABLE ")
    print("="*50)

    # 1. Verificar carpetas
    if os.path.exists("dist"):
        shutil.rmtree("dist") # Limpiamos construcciones previas
    
    if not os.path.exists("img"):
        print("ADVERTENCIA: No se encontró la carpeta 'img'. El ícono no se cargará.")
        os.makedirs("img", exist_ok=True)

    # 2. Definir argumentos de PyInstaller
    # --noconfirm: Sobrescribir sin preguntar
    # --onedir: Crear una carpeta (más rápido y seguro para bases de datos)
    # --windowed: No mostrar la consola negra al abrir
    # --icon: Tu ícono de avocado
    # --name: Nombre del archivo final
    args = [
        'main.py',
        '--noconfirm',
        '--onedir',
        '--windowed',
        '--name=HerrajesContable',
        '--add-data=styles.py;.', # Incluimos estilos
        # Incluir migraciones explícitamente si es necesario, aunque PyInstaller suele detectarlas
        '--hidden-import=migracion_actualizar_listas',
        '--clean'
    ]

    # Si existe el ícono, lo agregamos al ejecutable
    icono_path = os.path.join("img", "avocado.ico")
    if os.path.exists(icono_path):
        print(f"🥑 Ícono encontrado: {icono_path}")
        args.append(f'--icon={icono_path}')
        args.append(f'--add-data=img;img') # Incluimos la carpeta img dentro del exe
    else:
        print("⚠️  No se encontró 'img/avocado.ico'. Se usará el ícono por defecto.")

    # 3. Ejecutar PyInstaller
    import PyInstaller.__main__
    PyInstaller.__main__.run(args)

    # 4. Post-Procesamiento: Copiar configuración de Drive si existe
    dist_folder = os.path.join("dist", "HerrajesContable")
    exe_path = os.path.abspath(os.path.join(dist_folder, "HerrajesContable.exe"))
    
    if os.path.exists("ruta_db.txt"):
        shutil.copy2("ruta_db.txt", os.path.join(dist_folder, "ruta_db.txt"))
        print("☁️ Configuración de Google Drive copiada al ejecutable.")

    # 5. Crear Acceso Directo
    if os.path.exists(exe_path):
        crear_acceso_directo(exe_path, exe_path)

    print("\n" + "="*50)
    print(" ✅ ¡CONSTRUCCIÓN EXITOSA!")
    print(f" 📂 Carpeta del programa: {dist_folder}")
    print(" 🚀 Busca el ícono 'Herrajes Contable' en tu ESCRITORIO.")
    print("="*50 + "\n")

if __name__ == "__main__":
    try:
        import PyInstaller
        import win32com.client
    except ImportError:
        instalar_dependencia()
    
    crear_ejecutable()
