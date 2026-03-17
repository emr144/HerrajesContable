import os
import sys
import shutil
import subprocess

def instalar_dependencia():
    print("⏳ Instalando PyInstaller para crear el ejecutable...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def crear_ejecutable():
    print("\n" + "="*50)
    print(" 🚀 INICIANDO CONSTRUCCIÓN DE HERRAJES CONTABLE ")
    print("="*50)

    # 1. Verificar carpetas
    if os.path.exists("dist"):
        shutil.rmtree("dist") # Limpiamos construcciones previas
    
    if not os.path.exists("img"):
        print("⚠️  ADVERTENCIA: No se encontró la carpeta 'img'. El ícono no se cargará.")
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

    print("\n" + "="*50)
    print(" ✅ ¡CONSTRUCCIÓN EXITOSA!")
    print(" 📂 Tu programa está listo en la carpeta: 'dist/HerrajesContable'")
    print(" 👉 Dentro encontrarás 'HerrajesContable.exe' con el ícono del avocado.")
    print("="*50 + "\n")

if __name__ == "__main__":
    try:
        import PyInstaller
    except ImportError:
        instalar_dependencia()
    
    crear_ejecutable()

