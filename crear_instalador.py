import os
import subprocess
import sys

# --- CONFIGURACIÓN DEL INSTALADOR ---
APP_NAME = "HerrajesContable"
APP_VERSION = "1.0"
OUTPUT_NAME = "Instalador_HerrajesContable"

# Rutas absolutas para evitar confusiones
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist", "HerrajesContable")
ICO_FILE = os.path.join(BASE_DIR, "img", "avocado.ico")

def generar_script_iss():
    print("📝 Generando script de configuración 'setup_script.iss'...")
    
    # Contenido del script de Inno Setup
    # Define cómo se instalará el programa, dónde poner el ícono, qué archivos copiar, etc.
    iss_content = f"""
[Setup]
AppName={APP_NAME}
AppVersion={APP_VERSION}
DefaultDirName={{autopf}}\\{APP_NAME}
DefaultGroupName={APP_NAME}
OutputDir={BASE_DIR}
OutputBaseFilename={OUTPUT_NAME}
Compression=lzma
SolidCompression=yes
SetupIconFile={ICO_FILE}
UninstallDisplayIcon={{app}}\\{APP_NAME}.exe

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

[Files]
; Copiamos todo el contenido de la carpeta dist/HerrajesContable
Source: "{DIST_DIR}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Acceso directo en el Menú Inicio
Name: "{{group}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"; IconFilename: "{{app}}\\img\\avocado.ico"
; Acceso directo en el Escritorio (si el usuario lo elige)
Name: "{{commondesktop}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"; Tasks: desktopicon; IconFilename: "{{app}}\\img\\avocado.ico"

[Run]
Filename: "{{app}}\\{APP_NAME}.exe"; Description: "{{cm:LaunchProgram,{APP_NAME}}}"; Flags: nowait postinstall skipifsilent
"""
    with open("setup_script.iss", "w", encoding="utf-8") as f:
        f.write(iss_content)
    print("✅ Archivo 'setup_script.iss' creado con éxito.")

def compilar_iss():
    # Buscamos si Inno Setup está instalado en las rutas habituales
    rutas_inno = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe"
    ]
    
    compilador = None
    for r in rutas_inno:
        if os.path.exists(r):
            compilador = r
            break
            
    if compilador:
        print("⏳ Compilando el instalador automáticamente (esto puede tardar unos segundos)...")
        subprocess.run([compilador, "setup_script.iss"])
        print(f"\n🎉 ¡LISTO! Tu instalador está en: {os.path.join(BASE_DIR, OUTPUT_NAME + '.exe')}")
    else:
        print("\n⚠️  No se encontró Inno Setup instalado.")
        print("👉 Paso 1: Descarga e instala 'Inno Setup' (es gratis): https://jrsoftware.org/isdl.php")
        print("👉 Paso 2: Vuelve a ejecutar este script O dale doble clic al archivo 'setup_script.iss' y pulsa 'Compile'.")

if __name__ == "__main__":
    if not os.path.exists(DIST_DIR):
        print("❌ Error: No se encuentra la carpeta 'dist/HerrajesContable'.")
        print("Ejecuta primero: python construir_app.py")
    else:
        generar_script_iss()
        compilar_iss()
