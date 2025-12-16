Param(
    [string]$VenvDir = ".venv"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot "$VenvDir\Scripts\python.exe"

Write-Host "[INFO] Repo: $repoRoot"
Write-Host "[INFO] Venv: $venvPython"

# WSL
Write-Host "`n[CHECK] WSL:"
try {
    & wsl --status
}
catch {
    Write-Warning "WSL no disponible. Instala con 'wsl --install' (admin)."
}

# SU2 en WSL
Write-Host "`n[CHECK] SU2 en WSL:"
try {
    & wsl -e bash -lc "command -v ${SU2_CMD:-SU2_CFD} >/dev/null && echo 'SU2 OK' || echo 'SU2 no encontrado'"
}
catch {
    Write-Warning "No se pudo comprobar SU2 en WSL."
}

# Gmsh en Windows
Write-Host "`n[CHECK] Gmsh en Windows:"
$gmshCmd = $env:GMSH_CMD
if (-not $gmshCmd) {
    $gmsh = Get-Command gmsh.exe -ErrorAction SilentlyContinue
    if ($gmsh) { $gmshCmd = $gmsh.Path }
}
if ($gmshCmd) {
    Write-Host "Gmsh encontrado: $gmshCmd"
}
else {
    Write-Warning "Gmsh no encontrado. Define GMSH_CMD o agrega gmsh.exe al PATH."
}

# Paquetes Python principales
Write-Host "`n[CHECK] Paquetes Python en el venv:"
if (Test-Path $venvPython) {
    $pyCheck = @"
import importlib, sys
pkgs = ["numpy", "matplotlib", "aerosandbox", "PySide6"]
missing = []
for p in pkgs:
    try:
        importlib.import_module(p)
        print(f"[OK] {p}")
    except Exception as e:
        missing.append(p)
        print(f"[MISS] {p}: {e}", file=sys.stderr)
if missing:
    sys.exit(1)
"@
    & $venvPython -c $pyCheck
}
else {
    Write-Warning "No existe el venv en $VenvDir. Ejecuta scripts/setup_windows.ps1 primero."
}

Write-Host "`n[DONE] Chequeo completado."
