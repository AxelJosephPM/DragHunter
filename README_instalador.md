# Instalación asistida (Windows + WSL + SU2 + Gmsh)

Este repo incluye scripts para automatizar lo máximo posible la instalación. Se separan las partes Windows y WSL.

## 0) Requisitos previos
- Windows 10/11 con permisos de administrador para habilitar WSL.
- Conexión a internet.
- Espacio libre ~10 GB (WSL + SU2 + dependencias).

## 1) Preparar Windows (venv, Python, Gmsh)
1. Abre **PowerShell**. Para habilitar WSL desde el script, ábrelo como **Administrador**.
2. Desde la raíz del repo, ejecuta:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   .\scripts\setup_windows.ps1 -EnableWSL
   ```
   - El flag `-EnableWSL` habilita WSL/VMPlatform y lanza `wsl --install -d Ubuntu` si no está instalado (puede pedir reinicio). Si ya tienes WSL, puedes omitir el flag.
   - El script crea `.venv` y instala dependencias (usa requirements.txt si existe; si no, instala numpy/matplotlib/PySide6/aerosandbox).
   - Si tienes Gmsh instalado en otra ruta, añade `-GmshPath "C:\ruta\a\gmsh.exe"` para registrar `GMSH_CMD`.

## 2) Preparar WSL (Ubuntu) y SU2
1. Si fue la primera vez con WSL, completa la creación de usuario Ubuntu tras el reinicio.
2. Abre WSL:
   ```powershell
   wsl
   ```
3. Dentro de WSL, ve a la carpeta del repo (ajusta la ruta a tu usuario):
   ```bash
   cd /mnt/c/Users/lo1mo/Documents/3ro/Aerodinamica/DragHunter
   bash scripts/setup_wsl_su2.sh
   ```
   - Instala dependencias, compila e instala SU2 en `~/.local`.
   - Añade `SU2_CMD` y `PATH` al `~/.bashrc`. Cierra y abre WSL o ejecuta `source ~/.bashrc`.
   - Prueba: `SU2_CFD -h`.

## 3) Verificar entorno
De vuelta en PowerShell (no necesita admin):
```powershell
.\scripts\check_env.ps1
```
Esto valida WSL, SU2 en WSL, Gmsh en Windows y paquetes Python del venv.

## 4) Ejecutar el proyecto
En PowerShell:
```powershell
.\.venv\Scripts\activate
python code\run_simulations.py
```
Para la GUI:
```powershell
.\.venv\Scripts\activate
python code\gui\app.py
```

## Notas
- Si prefieres no automatizar WSL, instala manualmente con `wsl --install -d Ubuntu` (PowerShell admin) y luego ejecuta solo `scripts/setup_wsl_su2.sh` dentro de WSL.
- Para recompilar SU2 en otra versión, exporta `SU2_VERSION` antes de lanzar el script dentro de WSL (ejemplo: `SU2_VERSION=v7.5.0 bash scripts/setup_wsl_su2.sh`).
