
[Setup]
AppName=HerrajesContable
AppVersion=1.0
DefaultDirName={autopf}\HerrajesContable
DefaultGroupName=HerrajesContable
OutputDir=C:\Users\herra\HerrajesContable
OutputBaseFilename=Instalador_HerrajesContable
Compression=lzma
SolidCompression=yes
SetupIconFile=C:\Users\herra\HerrajesContable\img\avocado.ico
UninstallDisplayIcon={app}\HerrajesContable.exe

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copiamos todo el contenido de la carpeta dist/HerrajesContable
Source: "C:\Users\herra\HerrajesContable\dist\HerrajesContable\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Acceso directo en el Menú Inicio
Name: "{group}\HerrajesContable"; Filename: "{app}\HerrajesContable.exe"; IconFilename: "{app}\img\avocado.ico"
; Acceso directo en el Escritorio (si el usuario lo elige)
Name: "{commondesktop}\HerrajesContable"; Filename: "{app}\HerrajesContable.exe"; Tasks: desktopicon; IconFilename: "{app}\img\avocado.ico"

[Run]
Filename: "{app}\HerrajesContable.exe"; Description: "{cm:LaunchProgram,HerrajesContable}"; Flags: nowait postinstall skipifsilent
