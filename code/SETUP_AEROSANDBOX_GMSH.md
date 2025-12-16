# Setup rápido (AeroSandbox + Gmsh)

## Requisitos generales
- Python 3.10+ (probado con 3.12).
- `pip` actualizado: `python -m pip install --upgrade pip`.
- Clonar el repo y trabajar desde la carpeta raíz del proyecto.

## AeroSandbox (NeuralFoil)
1) Instala desde PyPI:
   ```bash
   python -m pip install aerosandbox
   ```
   Si prefieres usar el `requirements.txt` del proyecto:
   ```bash
   python -m pip install -r requirements.txt
   ```
2) Verifica que la función `get_aero_from_neuralfoil` esté disponible; es la que usa `main.py`. Un smoke-test rápido:
   ```bash
   python - <<'PY'
   import aerosandbox as asb
   import aerosandbox.numpy as np
   coords = np.array([[0,0],[1,0],[0.5,0.1]])
   af = asb.Airfoil(name="test", coordinates=coords)
   print(hasattr(af, "get_aero_from_neuralfoil"))
   PY
   ```
3) No se necesita GPU; funciona en CPU. Si falla la importación, revisa que el entorno activo sea el correcto (venv/conda).

## Gmsh (mallado SU2)
1) Descarga/instala Gmsh:
   - Windows: https://gmsh.info (instalador o zip). Asegúrate de tener `gmsh.exe` accesible.
   - Linux: `sudo apt-get install gmsh` o descarga el binario oficial.
2) Expón la ruta a Gmsh para el pipeline:
   - Opción A: añade Gmsh al `PATH`.
   - Opción B: define la variable de entorno `GMSH_CMD` apuntando al ejecutable:
     - PowerShell: `$env:GMSH_CMD = "C:\Ruta\a\gmsh.exe"`
     - CMD: `set GMSH_CMD=C:\Ruta\a\gmsh.exe`
     - Linux: `export GMSH_CMD=/usr/bin/gmsh`
   El código intentará auto-detectar Gmsh en rutas típicas, pero `GMSH_CMD` asegura que lo encuentre.
3) Smoke-test desde la raíz del repo:
   ```bash
   python - <<'PY'
   import mesh_generator
   print("Gmsh cmd:", mesh_generator.GMSH_CMD)
   PY
   ```
   Si no imprime una ruta válida, revisa PATH o `GMSH_CMD`.

### Comandos rápidos para configurar PATH / GMSH_CMD
- PowerShell (sesión actual):
  ```powershell
  $env:GMSH_CMD = "C:\Ruta\a\gmsh.exe"
  $env:PATH = "$env:PATH;C:\Ruta\a\gmsh\bin"
  ```
- CMD (sesión actual):
  ```cmd
  set GMSH_CMD=C:\Ruta\a\gmsh.exe
  set PATH=%PATH%;C:\Ruta\a\gmsh\bin
  ```
- Linux/macOS (bash/zsh):
  ```bash
  export GMSH_CMD=/usr/bin/gmsh
  export PATH="$PATH:/usr/local/bin"
  ```

## Notas rápidas
- El resto del pipeline usa rutas relativas; no necesitas editar paths en el código.
- Para evitar sorpresas, prueba primero con un caso pequeño: `python main.py --generate-only --profile-types naca --t-list 0.06 --c-list 1.0`.
