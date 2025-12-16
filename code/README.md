# DragHunter / Simulador de perfiles

Pipeline en Python para generar perfiles aerodinamicos (NACA 00xx, variantes con antena, rotodomos y curvas Bezier), mallar con Gmsh, correr SU2 (via WSL) y/o AeroSandbox NeuralFoil, y comparar resultados en CSV y graficos.

## Requisitos
- Python 3.10+ con `pip`.
- Paquetes: `numpy`, `matplotlib` (opcional para plots), `aerosandbox` (NeuralFoil). Instala con `python -m pip install -r requirements.txt` y agrega `aerosandbox` si no esta incluido.
- Gmsh instalable y accesible. Exporta `GMSH_CMD` con la ruta a `gmsh.exe` si no esta en `PATH` (ver `SETUP_AEROSANDBOX_GMSH.md`).
- SU2 disponible dentro de WSL. Se detecta `SU2_CFD` en PATH de WSL o la variable `SU2_CMD` con la ruta absoluta en WSL (ej. `/usr/local/bin/SU2_CFD`). Requiere WSL y un SU2 compilado/instalado alli.
- Opcional: `matplotlib` para guardar figuras de perfiles y ranking; sin el paquete se saltan los plots.

## Flujo principal
1. **Generacion de perfiles** (`Airfoil_Generator.py`, `profile_generators.py`): crea .dat en `generated_profiles/` (o la carpeta que pases) para:
   - `naca`: NACA 00xx basicos.
   - `naca_antenna`: NACA con espacio para una antena rectangular (barrido de cuerdas/espesores/posiciones).
   - `rotodomo`: elipse simetrica que respeta la ventana de antena.
   - `bezier`: perfil simetrico con curva Bezier parametrizada (sharpness + espesor).
   Cada entrada en el diccionario de perfiles es `{nombre: {"dat": ruta, "img": ruta_png_opcional}}`.
2. **Mallado** (`mesh_generator.py`): lee el .dat, corrige el borde de salida, arma un loop ordenado y llama a Gmsh para producir un `.su2`. El dominio externo es un cuadrado de 20c con capa limite alrededor del perfil.
3. **Simulacion** (`su2_runner.py`, `pipeline.py`): usa plantillas SU2 en `config/` para casos inviscid (RANS OFF), viscous (RANS) o incomprensible. Corre SU2 dentro de WSL, escribe logs (`su2_stdout.log`, `su2_stderr.log`), `forces_breakdown.dat` y `run_summary.json` en `results/su2/<caso>/(inviscid|viscous)/`.
4. **Postproceso** (`main.py`): combina filas de SU2 y Aerosandbox en `results/combined_results.csv` (y opcionalmente `results/simulations_clcdcm.csv`). Puede validar salidas SU2 y extraer valores finales.
5. **Ranking y plots** (`airfoil_comparison.py`, `plotting.py`): lee el CSV combinado, agrega metricas (cd_mean, cd_min, cl_mean, clcd_mean, clcd_max), genera `results/airfoil_rankings.csv` y plots opcionales (ranking y polar CL vs CD).

## Scripts clave
- `main.py`: punto de entrada general. Genera perfiles, corre AeroSandbox y/o SU2 y exporta CSV.
- `run_simulations.py`: envoltura de conveniencia; edita las constantes al inicio (listas de AoA/Mach/Re, tipos de perfiles, rangos de cuerdas/espesores, opciones de comparacion) y ejecuta `main.py` con esos parametros. Ideal para barridos grandes.
- `pipeline.py`: helpers para nombres de casos y ejecucion de un caso SU2 puntual (`run_case`) reutilizado por `main.py`.
- `mesh_generator.py`, `su2_configurator.py`: utilidades para mallado y generacion de configs SU2 a partir de plantillas.
- `airfoil_comparison.py`, `plotting.py`: ranking y graficos a partir de los CSV.

## Como ejecutar
1) **Smoke-test sin SU2** (solo generacion de perfiles):
```bash
python main.py --generate-only --profile-types naca --t-list 0.06 --c-list 1.0 --save-profile-plots
```
2) **Caso simple con SU2 y Aerosandbox** (inviscid + RANS o incomprensible segun flags):
```bash
python main.py --aoa 0 --mach 0.32 --Re 3.7e7 --profile-types naca --t-list 0.06 --c-list 1.0 --max-iter 500 --export-csv results/combined_results.csv
```
   - Usa `--compressible` para inviscid+viscous compresible; sin el flag corre solo RANS incomprensible.
   - Usa `--skip-su2` o `--skip-aerosb` para omitir un solver.
   - `--mesh-file` permite reutilizar una malla `.su2` existente.
3) **Barrido configurado**:
   - Ajusta las constantes en la cabecera de `run_simulations.py` (listas de AoA/Mach/Re, rangos de perfiles, metricas de ranking, ubicacion de plots/CSVs).
   - Ejecuta `python run_simulations.py`. Se imprimen los comandos completos usados para invocar `main.py`.
4) **Ranking standalone**:
```bash
python airfoil_comparison.py --input results/combined_results.csv --metric cd_mean --solver su2-incomp --plot --plot-dir results/plots --top-n 20
```

## Resultados y estructura de carpetas
- `generated_profiles/`: .dat de perfiles y opcionalmente `img/` con PNG.
- `meshes/`: mallas `.su2` generadas por caso (`<caso>/<caso>_airfoil_mesh.su2`).
- `results/su2/<caso>/inviscid|viscous/`: logs, `forces_breakdown.dat`, `run_summary.json`, `history.csv`.
- `results/combined_results.csv`: filas de `solver, airfoil, alpha, Re, mach, CL, CD, CM` combinadas (AeroSandbox + SU2).
- `results/airfoil_rankings.csv`: ranking agregado; `results/plots/` contiene los PNG si se habilitan.
- `results/summary.csv`: resumen incremental por caso (usado en `pipeline.py`).

## Variables de entorno utiles
- `GMSH_CMD`: ruta al ejecutable de Gmsh si no esta en PATH.
- `SU2_CMD`: ruta en WSL al binario SU2_CFD (se detecta en PATH o en el env conda `su2env` si existe).
- `SU2_MAX_ITER`: limite de iteraciones para pipeline basico en `pipeline.py`.

## Tests
Suite en `tests/` con Pytest para configurador SU2, parser de fuerzas, reintentos de SU2, generacion de carpetas y smoke-tests de `main.py`. Ejecuta con:
```bash
python -m pytest -q
```
Algunas pruebas que invocan SU2 o Gmsh necesitan que esas dependencias esten disponibles; de lo contrario puedes omitirlas ajustando tu entorno.

## Notas rapidas de solucion de problemas
- **SU2 no encontrado**: confirma WSL instalado, SU2 en PATH de WSL o `SU2_CMD` definido. `su2_runner.is_su2_available()` devuelve `False` si no se resuelve.
- **Gmsh no encontrado**: define `GMSH_CMD` o agrega el binario a PATH. Consulta `SETUP_AEROSANDBOX_GMSH.md`.
- **CSV vacio**: revisa flags `--skip-*`, que existan filas en `results/su2/.../run_summary.json` o que AeroSandbox este instalado (se imprime un warning si falta).
