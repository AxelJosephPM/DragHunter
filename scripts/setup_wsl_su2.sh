#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Instalador SU2 para WSL (Ubuntu recomendado)"

if ! grep -qi microsoft /proc/version; then
  echo "[ERROR] Este script debe ejecutarse dentro de WSL." >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y build-essential cmake git gfortran libopenmpi-dev openmpi-bin \
    python3 python3-pip pkg-config

SU2_VERSION="${SU2_VERSION:-v7.5.1}"
SU2_SRC="${SU2_SRC:-$HOME/SU2}"
SU2_PREFIX="${SU2_PREFIX:-$HOME/.local}"

if [ ! -d "$SU2_SRC" ]; then
  echo "[SU2] Clonando SU2 ($SU2_VERSION) en $SU2_SRC"
  git clone --depth 1 --branch "$SU2_VERSION" https://github.com/su2code/SU2.git "$SU2_SRC"
else
  echo "[SU2] Reutilizando repo en $SU2_SRC (pull para actualizar)"
  git -C "$SU2_SRC" pull --ff-only || true
fi

mkdir -p "$SU2_SRC/build"
cd "$SU2_SRC/build"
cmake -DENABLE_OPENMP=ON -DENABLE_MPI=ON -DCMAKE_INSTALL_PREFIX="$SU2_PREFIX" ..
make -j"$(nproc)"
make install

echo "[SU2] Instalado en $SU2_PREFIX"

SU2_BIN="$SU2_PREFIX/bin/SU2_CFD"

add_if_missing() {
  local line="$1"
  local file="$2"
  grep -qxF "$line" "$file" 2>/dev/null || echo "$line" >> "$file"
}

add_if_missing "export PATH=\"$SU2_PREFIX/bin:\$PATH\"" "$HOME/.bashrc"
add_if_missing "export SU2_CMD=\"$SU2_BIN\"" "$HOME/.bashrc"

if command -v "$SU2_BIN" >/dev/null 2>&1; then
  echo "[CHECK] SU2_CFD encontrado en $SU2_BIN"
else
  echo "[WARN] No se encontró SU2_CFD en PATH; revisa $SU2_BIN"
fi

echo "[DONE] Cierra y reabre la shell WSL (o ejecuta 'source ~/.bashrc')."
echo "       Prueba: SU2_CFD -h"
