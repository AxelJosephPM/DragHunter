# 🚀 Instalación del Entorno CFD — WSL + Miniconda + SU2 + su2env

Esta guía explica cómo instalar WSL, Ubuntu, Miniconda, el entorno `su2env`, SU2 v8.3.0 y las librerías necesarias para generar mallas con Gmsh y ejecutar simulaciones automáticas desde Python.

Funciona en **Windows 10/11**.

---

## 🟥 Fase 1 — Instalación de WSL en Windows

Abrir **PowerShell como Administrador** y ejecutar:

```powershell
wsl --install
```

Esto instalará:

- WSL2  
- Ubuntu por defecto  

🔄 **Reinicia el PC cuando termine**.

---

## 🟧 Fase 2 — Instalación dentro de Ubuntu (WSL)

Cuando reinicies, abre **Ubuntu** desde el menú inicio.

---

### 1. Actualizar sistema

```bash
sudo apt update && sudo apt upgrade -y
```

---

### 2. Instalar dependencias esenciales

```bash
sudo apt install -y build-essential cmake git wget gfortran python3-dev \
                    libopenmpi-dev openmpi-bin
```

---

### 3. Instalar Miniconda

Descargar:

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
```

Instalar:

```bash
bash miniconda.sh -b -p $HOME/miniconda3
```

Inicializar conda:

```bash
eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
conda init bash
```

🔄 **Cierra y vuelve a abrir Ubuntu**.

---

### 4. Crear el entorno su2env

```bash
conda create -n su2env python=3.10 -y
```

Activarlo:

```bash
conda activate su2env
```

---

### 5. Instalar librerías de Python

```bash
pip install numpy scipy matplotlib pygmsh meshio gmsh
```

---

### 6. Instalar SU2 v8.3.0 (binarios precompilados)

Descargar:

```bash
wget https://github.com/su2code/SU2/releases/download/v8.3.0/SU2_v8.3.0_linux.tar.gz
```

Descomprimir:

```bash
tar -xvzf SU2_v8.3.0_linux.tar.gz
```

Mover a /usr/local:

```bash
sudo mv SU2_v8.3.0_linux /usr/local/SU2
```

Añadir SU2 al PATH permanentemente:

```bash
echo 'export PATH=/usr/local/SU2/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

---

## 🟩 Verificación

### Probar SU2:

```bash
SU2_CFD --version
```

Debe mostrar el banner de **SU2 v8.3.0 Harrier**.

---

### Probar librerías de Python

```bash
python3 - << 'EOF'
import gmsh, meshio, numpy
print("OK: gmsh + meshio + numpy funcionando correctamente.")
EOF
```

---

## 🟦 Acceder a archivos de Windows desde WSL

Rutas Windows como:

```
C:\Users\tu_usuario\Documents\Proyecto
```

se acceden así:

```
/mnt/c/Users/tu_usuario/Documents/Proyecto
```

Ejemplo:

```bash
cd /mnt/c/Users/Manolito/Documents/3ro/Aerodinamica/DragHunter
```

---

## 🟪 Activar el entorno cada vez que abras Ubuntu

```bash
conda activate su2env
```

---

## 🟦 Resumen de instalación

| Componente | Estado |
|-----------|--------|
| WSL2 + Ubuntu | ✔ |
| Miniconda | ✔ |
| Entorno `su2env` | ✔ |
| Python 3.10 | ✔ |
| Gmsh | ✔ |
| MeshIO | ✔ |
| pygmsh | ✔ |
| SU2 v8.3.0 | ✔ |

---

## 🟩 ¿Problemas?

Puedes abrir un issue en el repositorio o contactar con el desarrollador.

---

