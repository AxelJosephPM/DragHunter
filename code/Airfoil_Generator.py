import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# AUXILIARY FUNCTIONS
# ============================================================

def cosine_spacing(n_points):
    beta = np.linspace(0, np.pi, n_points)
    return 0.5 * (1 - np.cos(beta))


def naca00xx_thickness(x, t_rel):
    return 5 * t_rel * (
        0.2969 * np.sqrt(x)
        - 0.1260*x
        - 0.3516*x**2
        + 0.2843*x**3
        - 0.1015*x**4
    )


def assemble_airfoil(x, yt):
    # upper and lower
    xu, yu = x, yt
    xl, yl = x, -yt

    # XFOIL REQUIERE ESTE ORDEN:
    # 1. TE (upper)
    # 2. upper surface hacia atrás
    # 3. LE
    # 4. lower surface hacia adelante
    # 5. TE (lower)

    x_coords = np.concatenate([
        [xu[-1]],       # TE upper
        xu[::-1],       # upper surface (right→left)
        xl[1:],         # lower surface (left→right)
    ])

    y_coords = np.concatenate([
        [yu[-1]],       # TE upper
        yu[::-1],
        yl[1:],
    ])

    return x_coords, y_coords


# ============================================================
# AIRFOIL CLASS
# ============================================================

class Airfoil:
    """
    Clase que representa un perfil aerodinámico.
    Los datos pueden almacenarse en forma ADIMENSIONAL o REAL.
    """

    def __init__(self, name, x_nd, y_nd, c=1.0, normalize=True):
        """
        normalize=True → el objeto guarda x_nd, y_nd como datos principales.
        normalize=False → guarda X, Y directamente.
        """
        self.name = name
        self.c = c
        self.normalize = normalize

        # Guardar coordenadas según preferencia
        if normalize:
            self.x_nd = x_nd
            self.y_nd = y_nd
            self.X = c * x_nd
            self.Y = c * y_nd
        else:
            self.x_nd = x_nd
            self.y_nd = y_nd
            self.X = x_nd     # Aquí x_nd ya vienen reales
            self.Y = y_nd

    # ------------------------------------------------------------
    # Método de clase para generar NACA 00xx
    # ------------------------------------------------------------
    @classmethod
    def naca00xx(cls, t_rel=0.08, c=1.0, n_points=200, normalize=True):
        x = cosine_spacing(n_points)
        yt = naca00xx_thickness(x, t_rel)
        x_nd, y_nd = assemble_airfoil(x, yt)

        name = f"NACA00{int(t_rel*100):02d}"

        # Si normalize=False → el usuario quiere directamente X, Y
        if not normalize:
            x_real = c * x_nd
            y_real = c * y_nd
            return cls(name, x_real, y_real, c, normalize=False)

        return cls(name, x_nd, y_nd, c, normalize=True)

    # ------------------------------------------------------------
    # EXPORTACIÓN
    # ------------------------------------------------------------
    def save_dat(self, filename, non_dim=False):
        """
        non_dim=True  → guarda (x/c, y/c)
        non_dim=False → guarda (X, Y) reales
        """
        with open(filename, "w") as f:
            f.write(self.name + "\n")

            if non_dim:
                for xi, yi in zip(self.x_nd, self.y_nd):
                    f.write(f"{xi:.6f} {yi:.6f}\n")
            else:
                for Xi, Yi in zip(self.X, self.Y):
                    f.write(f"{Xi:.6f} {Yi:.6f}\n")

        print(f"[OK] Archivo .dat guardado: {filename}")

    # ------------------------------------------------------------
    # GRAFICAR
    # ------------------------------------------------------------
    def plot(self, show=True, save_path=None, figsize=(8,3)):
        plt.figure(figsize=figsize)
        plt.plot(self.X, self.Y, '-', lw=1.4)

        plt.gca().set_aspect("equal", "box")
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.xlabel("x" if not self.normalize else "x (c)")
        plt.ylabel("y" if not self.normalize else "y (c)")
        plt.title(self.name)

        if save_path is not None:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"[OK] Gráfico guardado en: {save_path}")

        if show:
            plt.show()

        plt.close()
