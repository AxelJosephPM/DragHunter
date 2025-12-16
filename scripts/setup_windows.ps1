Param(
    [switch]$EnableWSL = $false,
    [string]$PythonExe = "python",
    [string]$VenvDir = ".venv",
    [string]$GmshPath = $env:GMSH_CMD
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Write-Host "[INFO] Repo: $repoRoot"

# --- Opcional: habilitar WSL/Ubuntu si se solicita ---
if ($EnableWSL) {
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
    if (-not $isAdmin) {
        Write-Warning "Ejecuta este script en PowerShell como Administrador para habilitar WSL/VMPlatform."
    }
    else {
        Write-Host "[WSL] Habilitando características WSL y VMPlatform (requiere reinicio si no estaban activas)..."
        & dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart | Out-Null
        & dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart | Out-Null
        Write-Host "[WSL] Ejecutando wsl --install (puede pedir reinicio)."
        try {
            & wsl --install -d Ubuntu
        }
        catch {
            Write-Warning "No se pudo completar wsl --install. Ejecuta manualmente en una consola de administrador si es necesario."
        }
    }
}

# --- Crear/actualizar entorno virtual ---
$venvPath = Join-Path $repoRoot $VenvDir
if (-not (Test-Path $venvPath)) {
    Write-Host "[PY] Creando venv en $venvPath"
    & $PythonExe -m venv $venvPath
}
else {
    Write-Host "[PY] Reutilizando venv existente en $venvPath"
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
Write-Host "[PY] Usando python: $venvPython"

& $venvPython -m pip install --upgrade pip

$reqCandidates = @("requirements.txt", "code\requirements.txt")
$installedReq = $false
foreach ($rel in $reqCandidates) {
    $full = Join-Path $repoRoot $rel
    if (Test-Path $full) {
        Write-Host "[PY] Instalando dependencias desde $rel"
        & $venvPython -m pip install -r $full
        $installedReq = $true
        break
    }
}

if (-not $installedReq) {
    $basePkgs = @("numpy", "matplotlib", "pandas", "gmsh", "pyside6", "aerosandbox")
    Write-Host "[PY] No se encontró requirements.txt; instalando base: $($basePkgs -join ', ')"
    & $venvPython -m pip install $basePkgs
}

# --- Configurar Gmsh ---
if ($GmshPath) {
    Write-Host "[GMSH] Registrando GMSH_CMD=$GmshPath en variables de usuario."
    [Environment]::SetEnvironmentVariable("GMSH_CMD", $GmshPath, "User")
}
else {
    Write-Host "[GMSH] No se proporcionó ruta; si no está en PATH, exporta GMSH_CMD manualmente."
}

# --- Comprobaciones rápidas ---
Write-Host "`n[CHECK] WSL estado (ignora si no instalado aún):"
try { & wsl --status } catch { Write-Warning "WSL no disponible o requiere reinicio." }

Write-Host "`n[CHECK] SU2_CFD dentro de WSL (si ya instalado):"
try { & wsl -e bash -lc "command -v ${SU2_CMD:-SU2_CFD} || echo 'SU2 no encontrado'" } catch { }

Write-Host "`n[INFO] Entorno listo. Activa el venv cuando uses el proyecto:"
Write-Host "       `"$venvPath\Scripts\activate`""
Write-Host "Ejemplo: `"`$env:GMSH_CMD=...; $venvPath\Scripts\activate; python code\\run_simulations.py`"`"
