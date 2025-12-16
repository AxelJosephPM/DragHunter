# 🚀 Instalación del Entorno CFD — WSL + Miniconda + SU2 + su2env

Guía completa para instalar WSL2, Ubuntu, Miniconda, el entorno `su2env`, paquetes de generación de mallas (Gmsh/meshio/pygmsh) y SU2 v8.3.0 compilado desde fuente con soporte MPI.
Funciona en Windows 10/11.

------------------------------------------------------------
🟥 Fase 1 — Instalar WSL en Windows
------------------------------------------------------------

Ejecuta en PowerShell como Administrador:

    wsl --install

Esto instalará:
- WSL2
- Ubuntu por defecto

Reinicia el PC cuando termine.

------------------------------------------------------------
🟧 Fase 2 — Configuración dentro de Ubuntu (WSL)
------------------------------------------------------------

1. Actualizar sistema:

    sudo apt update && sudo apt upgrade -y

2. Instalar dependencias esenciales:

    sudo apt install -y \
        build-essential \
        git \
        python3 python3-pip python3.12-venv \
        ninja-build \
        mpich libmpich-dev \
        gfortran wget

3. Instalar Miniconda:

    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    bash miniconda.sh -b -p $HOME/miniconda3

Inicializar conda:

    eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
    conda init bash

Cierra y vuelve a abrir Ubuntu.

4. Crear entorno su2env:

    conda create -n su2env python=3.10 -y

Activarlo:

    conda activate su2env

5. Instalar librerías Python:

    pip install numpy scipy matplotlib pygmsh meshio gmsh

------------------------------------------------------------
🟦 Fase 3 — Instalar SU2 v8.3.0 (compilación oficial)
------------------------------------------------------------

6. Clonar SU2:

    cd ~
    git clone https://github.com/su2code/SU2.git
    cd SU2
    git checkout v8.3.0

7. Configurar compilación con Meson:

    ./meson.py setup build --prefix=$HOME/SU2 -Dwith-mpi=enabled

8. Compilar e instalar:

    ninja -C build install

9. Añadir SU2 al PATH:

    echo 'export PATH=$HOME/SU2/bin:$PATH' >> ~/.bashrc
    source ~/.bashrc

------------------------------------------------------------
🟩 Verificación
------------------------------------------------------------

1. Probar SU2:

    SU2_CFD -h

Debe aparecer:
"SU2 v8.3.0 Harrier"

2. Probar MPI:

    mpirun -np 2 SU2_CFD -h

3. Verificar librerías Python:

    python3 - << 'EOF'
    import gmsh, meshio, numpy
    print("OK: gmsh + meshio + numpy funcionando correctamente.")
    EOF

------------------------------------------------------------
🟦 Acceder a Windows desde WSL
------------------------------------------------------------

Ruta de Windows:

    C:\Users\Usuario\Documents

En WSL se accede como:

    /mnt/c/Users/Usuario/Documents

Ejemplo:

    cd /mnt/c/Users/Manolito/Documents/3ro/Aerodinamica/DragHunter

------------------------------------------------------------
🟪 Activar entorno cada vez que entres en Ubuntu
------------------------------------------------------------

    conda activate su2env







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

