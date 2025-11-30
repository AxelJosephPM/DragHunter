import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# 1. GENERACIÓN DE GEOMETRÍA
# ============================================================

def cosine_spacing(n_points):
    """
    Genera una distribución coseno desde 0 a 1.
    Se usa para concentrar puntos en el borde de ataque y de salida.
    """
    beta = np.linspace(0, np.pi, n_points)
    return 0.5 * (1 - np.cos(beta))


def naca00xx_thickness(x, t_rel):
    """
    Devuelve la distribución de espesor simétrico para un NACA 00xx.
    """
    return 5 * t_rel * (
        0.2969 * np.sqrt(x)
        - 0.1260 * x
        - 0.3516 * x**2
        + 0.2843 * x**3
        - 0.1015 * x**4
    )


def assemble_airfoil(x, yt):
    """
    Dado un array x creciente y su espesor yt,
    genera el perfil superior e inferior simétrico.
    """
    xu, yu = x, yt           # superficie superior
    xl, yl = x[::-1], -yt[::-1]  # superficie inferior

    x_non_dim = np.concatenate([xu, xl[1:]])
    y_non_dim = np.concatenate([yu, yl[1:]])

    return x_non_dim, y_non_dim


def naca00xx_points(t_rel=0.08, c=1.0, n_points=200):
    """
    Función principal para generar un perfil NACA 00xx.
    Retorna coordenadas adimensionales y reales.
    """
    x = cosine_spacing(n_points)      # distribución coseno
    yt = naca00xx_thickness(x, t_rel) # espesor NACA 00xx

    x_non_dim, y_non_dim = assemble_airfoil(x, yt)

    # Escalado a dimensiones reales
    X = c * x_non_dim
    Y = c * y_non_dim

    return x_non_dim, y_non_dim, X, Y



# ============================================================
# 2. EXPORTACIÓN A ARCHIVOS
# ============================================================

def save_dat(filename, X, Y, name="CUSTOM"):
    """
    Guarda un archivo .dat tipo XFOIL/XFLR5 con coordenadas X, Y.
    """
    with open(filename, "w") as f:
        f.write(name + "\n")
        for xi, yi in zip(X, Y):
            f.write(f"{xi:.6f} {yi:.6f}\n")
    print(f"[OK] Archivo .dat guardado: {filename}")



# ============================================================
# 3. VISUALIZACIÓN DEL PERFIL
# ============================================================

def plot_airfoil(X, Y, title="Airfoil", show=True, save_path=None):
    """
    Grafica un perfil en coordenadas reales.
    """

    plt.figure(figsize=(8, 3))
    plt.plot(X, Y, '-', linewidth=1.4)
    plt.gca().set_aspect("equal", "box")
    plt.grid(True, linestyle="--", alpha=0.5)

    plt.xlabel("x")
    plt.ylabel("y")
    plt.title(title)

    if save_path is not None:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"[OK] Gráfico guardado en: {save_path}")

    if show:
        plt.show()

    plt.close()
