# Versión original/legacy de comparación de perfiles (referencia).
# No se usa en el pipeline actual; mantenida solo para consulta.

import os


def write_airfoil(mean_Cl, mean_Cd, nombre_archivo):
    """
    Escribe los valores medios en un nuevo archivo
    """
    nombre_base = os.path.splitext(nombre_archivo)[0]  # Quita la extensión
    archivo_salida = f"{nombre_base}_CHECKED.txt"
    with open(archivo_salida, "w") as f:
        f.write(f"{mean_Cl:.6f},{mean_Cd:.6f}")
    print(f"✓ Resultados guardados en: {archivo_salida}")
    return archivo_salida


def calculate_airfoil(Cl, Cd, nombre_archivo):
    """
    Calcula los valores medios de Cl y Cd
    """
    if not Cl or not Cd:
        print("ERR: No hay datos para calcular")
        return
    mean_Cl = sum(Cl) / len(Cl)
    mean_Cd = sum(Cd) / len(Cd)
    print("RESULTADOS:")
    print(f"  Media de Cl: {mean_Cl:.6f}")
    print(f"  Media de Cd: {mean_Cd:.6f}")
    print(f"  Número de muestras: {len(Cl)}")
    write_airfoil(mean_Cl, mean_Cd, nombre_archivo)


def read_airfoil(nombre_archivo):
    """
    Lee el archivo y extrae los valores de Cl y Cd
    """
    Cl, Cd = [], []
    print(f"Leyendo archivo: {nombre_archivo}")
    try:
        with open(nombre_archivo, "r") as archivo:
            lineas_procesadas = 0
            lineas_ignoradas = 0
            for num_linea, linea in enumerate(archivo, 1):
                linea = linea.strip()
                if not linea:
                    lineas_ignoradas += 1
                    continue
                if linea.startswith("#"):
                    lineas_ignoradas += 1
                    continue
                partes = [p.strip() for p in linea.split(",")]
                if len(partes) == 3:
                    try:
                        valor_Cl = float(partes[1])
                        valor_Cd = float(partes[2])
                        Cl.append(valor_Cl)
                        Cd.append(valor_Cd)
                        lineas_procesadas += 1
                    except ValueError:
                        print(f" ERR. Línea {num_linea}: Valores no numéricos - '{linea}'")
                        lineas_ignoradas += 1
                else:
                    print(
                        f"  ⚠️  ERR. {num_linea}: Formato incorrecto (esperados 2 valores, encontrados {len(partes)})"
                    )
                    lineas_ignoradas += 1
        print(f"Líneas procesadas: {lineas_procesadas}")
        if lineas_ignoradas > 0:
            print(f"(!) Líneas ignoradas: {lineas_ignoradas}")
        if Cl and Cd:
            print("\n  Primeros valores:")
            print(f"    Cl[0] = {Cl[0]:.6f}, Cd[0] = {Cd[0]:.6f}")
            print("  Últimos valores:")
            print(f"    Cl[-1] = {Cl[-1]:.6f}, Cd[-1] = {Cd[-1]:.6f}")
        return Cl, Cd
    except FileNotFoundError:
        print(f"ERR: No se encontró el archivo '{nombre_archivo}'")
        return [], []
    except Exception as e:
        print(f"ERR: Error al leer el archivo: {e}")
        return [], []


def airfoil_comparison():
    print("=" * 50)
    print("ANÁLISIS DE PERFIL AERODINÁMICO")
    print("=" * 50)


def process_airfoil(nombre_archivo="ejemplo.txt"):
    print(f"Procesando archivo: {nombre_archivo}")
    Cl, Cd = read_airfoil(nombre_archivo)
    if Cl and Cd:
        calculate_airfoil(Cl, Cd, nombre_archivo)
    else:
        print("ERR: No se pudieron procesar los datos.")


if __name__ == "__main__":
    process_airfoil("ejemplo.txt")  # Cambia por el nombre de tu archivo
