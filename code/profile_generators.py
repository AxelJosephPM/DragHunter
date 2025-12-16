"""
Generadores de perfiles adicionales (NACA con antena, Rotodomo elíptico y perfil simétrico Bézier).
Devuelven un diccionario {nombre: {"dat": ruta_dat, "img": ruta_png_opcional}} listo para usarse en main.py.
Las gráficas se guardan solo si matplotlib está disponible o si se solicita.
"""

from pathlib import Path
import numpy as np

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
except ImportError:  # pragma: no cover - dependencia opcional
    plt = None
    patches = None


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def _warn_matplotlib():
    print("[WARN] matplotlib no está instalado; se omiten las imágenes de perfiles.")


def _save_png(fig, path: Path):
    _ensure_dir(path.parent)
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def generate_naca_antenna_profiles(
    chord_start=4.6,
    chord_end=10.0,
    chord_step=0.1,
    thickness_min=0.02,
    thickness_max=0.5,
    positions_count=10,
    antenna_length=4.5,
    antenna_height=0.3,
    n_points=200,
    output_dir="generated_profiles",
    save_plots=False,
):
    output = {}
    out_dir = Path(output_dir)
    img_dir = out_dir / "img" / "naca_antenna"
    _ensure_dir(out_dir)
    if save_plots and plt is None:
        _warn_matplotlib()
        save_plots = False

    def naca4_half_upper(chord, thickness_percent):
        x = np.linspace(0, chord, n_points)
        t = thickness_percent
        yt = 5 * t * chord * (
            0.2969 * np.sqrt(x / chord)
            - 0.1260 * (x / chord)
            - 0.3516 * (x / chord) ** 2
            + 0.2843 * (x / chord) ** 3
            - 0.1015 * (x / chord) ** 4
        )
        return x, yt

    def check_fit(x_perfil, y_perfil, c, pos_x_inicio):
        x_end = pos_x_inicio + antenna_length
        h_req = antenna_height / 2
        if pos_x_inicio < 0 or x_end > x_perfil[-1]:
            return False
        indices = (x_perfil >= pos_x_inicio) & (x_perfil <= x_end)
        y_zona = y_perfil[indices]
        if len(y_zona) == 0:
            return False
        margen = 0.005
        if np.min(y_zona) < (h_req + margen):
            return False
        return True

    chords = np.arange(chord_start, chord_end + 1e-6, chord_step)
    thickness_range = np.arange(thickness_min, thickness_max + 1e-9, 0.01)
    counter = 0
    for c in chords:
        espacio_libre = c - antenna_length
        if espacio_libre <= 0:
            continue
        posiciones_x = np.linspace(0.05, espacio_libre * 0.9, positions_count)
        for pos_x in posiciones_x:
            for t_pct in thickness_range:
                x, y = naca4_half_upper(c, t_pct)
                if check_fit(x, y, c, pos_x):
                    t_pct_int = int(round(t_pct * 100))
                    name = f"C{c:.1f}_NACA00{t_pct_int:02d}_Pos{pos_x:.2f}m"
                    dat_path = out_dir / f"{name}.dat"
                    with dat_path.open("w") as f:
                        f.write(f"{name}\n")
                        x_full = np.concatenate((x[::-1], x[1:]))
                        y_full = np.concatenate((y[::-1], -y[1:]))
                        for xi, yi in zip(x_full, y_full):
                            f.write(f" {xi:.6f}  {yi:.6f}\n")
                    info = {"dat": str(dat_path)}
                    if save_plots:
                        fig = plt.figure(figsize=(12, 5))
                        plt.plot(x, y, "k-", linewidth=2)
                        plt.plot(x, -y, "k-", linewidth=2)
                        plt.fill_between(x, y, -y, color="lightgray", alpha=0.3)
                        rect = patches.Rectangle(
                            (pos_x, -antenna_height / 2),
                            antenna_length,
                            antenna_height,
                            linewidth=2,
                            edgecolor="red",
                            facecolor="red",
                            alpha=0.4,
                        )
                        plt.gca().add_patch(rect)
                        plt.axis("equal")
                        plt.grid(True, linestyle="--", alpha=0.6)
                        img_path = img_dir / f"{name}.png"
                        _save_png(fig, img_path)
                        info["img"] = str(img_path)
                    output[name] = info
                    counter += 1
                    break  # espesor mínimo válido para esta posición
    print(f"[NACA-ANTENA] Generados {counter} perfiles.")
    return output


def generate_rotodomo_profiles(
    chord_start=4.6,
    chord_end=11.0,
    chord_step=0.1,
    thickness_min=0.05,
    thickness_max=0.45,
    antenna_length=4.5,
    antenna_height=0.3,
    n_points=200,
    output_dir="generated_profiles",
    save_plots=False,
):
    output = {}
    out_dir = Path(output_dir)
    img_dir = out_dir / "img" / "rotodomo"
    _ensure_dir(out_dir)
    if save_plots and plt is None:
        _warn_matplotlib()
        save_plots = False

    chords = np.arange(chord_start, chord_end + 1e-6, chord_step)
    thickness_range = np.arange(thickness_min, thickness_max + 1e-9, 0.01)
    counter = 0
    for c in chords:
        espacio_libre = c - antenna_length
        if espacio_libre <= 0:
            continue
        pos_x = (c / 2.0) - (antenna_length / 2.0)
        for t_pct in thickness_range:
            a = c / 2.0
            b = (c * t_pct) / 2.0
            cx = c / 2.0
            # Chequeo matemático de las esquinas de la antena
            esquinas = [
                (pos_x, antenna_height / 2.0),
                (pos_x + antenna_length, antenna_height / 2.0),
                (pos_x, -antenna_height / 2.0),
                (pos_x + antenna_length, -antenna_height / 2.0),
            ]
            fits = True
            for (px, py) in esquinas:
                val = ((px - cx) ** 2 / a**2) + (py**2 / b**2)
                if val > 0.99:
                    fits = False
                    break
            if not fits:
                continue
            theta = np.linspace(0, 2 * np.pi, n_points)
            x = cx + a * np.cos(theta)
            y = b * np.sin(theta)
            t_pct_int = int(round(t_pct * 100))
            name = f"ROTO_c{c:.1f}_t{t_pct_int:02d}"
            dat_path = out_dir / f"{name}.dat"
            with dat_path.open("w") as f:
                f.write(f"{name}\n")
                for xi, yi in zip(x, y):
                    f.write(f" {xi:.6f}  {yi:.6f}\n")
            info = {"dat": str(dat_path)}
            if save_plots:
                fig = plt.figure(figsize=(10, 5))
                plt.plot(x, y, "k-", linewidth=2)
                plt.fill(x, y, color="lightgray", alpha=0.3)
                rect = patches.Rectangle(
                    (pos_x, -antenna_height / 2),
                    antenna_length,
                    antenna_height,
                    linewidth=2,
                    edgecolor="red",
                    facecolor="red",
                    alpha=0.5,
                )
                plt.gca().add_patch(rect)
                plt.axis("equal")
                plt.grid(True, linestyle="--", alpha=0.5)
                img_path = img_dir / f"{name}.png"
                _save_png(fig, img_path)
                info["img"] = str(img_path)
            output[name] = info
            counter += 1
            break  # espesor mínimo válido para este diámetro
    print(f"[ROTODO] Generados {counter} perfiles.")
    return output


def generate_bezier_profiles(
    chord_start=6.0,
    chord_end=10.0,
    chord_step=0.5,
    thickness_min=0.05,
    thickness_max=0.55,
    sharpness_list=None,
    antenna_length=4.5,
    antenna_height=0.3,
    n_points=200,
    output_dir="generated_profiles",
    save_plots=False,
):
    output = {}
    out_dir = Path(output_dir)
    img_dir = out_dir / "img" / "bezier"
    _ensure_dir(out_dir)
    if save_plots and plt is None:
        _warn_matplotlib()
        save_plots = False
    if sharpness_list is None:
        sharpness_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]

    def bezier_symmetric_profile(chord, thickness_percent, sharpness=0.5):
        half_chord = chord / 2.0
        y_max = (chord * thickness_percent) / 2.0
        P0 = np.array([0.0, 0.0])
        P3 = np.array([half_chord, y_max])
        P1 = np.array([half_chord * (0.5 * sharpness), 0.0])
        P2 = np.array([half_chord * (1.0 - 0.2), y_max])
        t = np.linspace(0, 1, n_points // 2)
        curve_half = (
            np.outer((1 - t) ** 3, P0)
            + np.outer(3 * (1 - t) ** 2 * t, P1)
            + np.outer(3 * (1 - t) * t**2, P2)
            + np.outer(t**3, P3)
        )
        x_half = curve_half[:, 0]
        y_half = curve_half[:, 1]
        x_back = chord - x_half[::-1]
        y_back = y_half[::-1]
        x_total = np.concatenate([x_half, x_back[1:]])
        y_total = np.concatenate([y_half, y_back[1:]])
        return x_total, y_total

    def check_fit(x_perfil, y_top, y_bot, pos_x_inicio):
        x_end_antena = pos_x_inicio + antenna_length
        if pos_x_inicio < x_perfil[0] or x_end_antena > x_perfil[-1]:
            return False
        indices = (x_perfil >= pos_x_inicio) & (x_perfil <= x_end_antena)
        y_techo_zona = y_top[indices]
        y_suelo_zona = y_bot[indices]
        if len(y_techo_zona) == 0:
            return False
        margen = 0.01
        hueco = y_techo_zona - y_suelo_zona
        if np.min(hueco) < (antenna_height + margen):
            return False
        return True

    chords = np.arange(chord_start, chord_end + 1e-6, chord_step)
    thickness_range = np.arange(thickness_min, thickness_max + 1e-9, 0.01)
    counter = 0
    for c in chords:
        pos_x = (c / 2.0) - (antenna_length / 2.0)
        for sharp in sharpness_list:
            for t_pct in thickness_range:
                x, y_top = bezier_symmetric_profile(c, t_pct, sharpness=sharp)
                y_bot = -y_top
                if not check_fit(x, y_top, y_bot, pos_x):
                    continue
                t_pct_int = int(round(t_pct * 100))
                name = f"SYM_c{c:.1f}_s{int(sharp*10)}_t{t_pct_int:02d}"
                dat_path = out_dir / f"{name}.dat"
                with dat_path.open("w") as f:
                    f.write(f"{name}\n")
                    for xi, yi in zip(x, y_top):
                        f.write(f" {xi:.6f}  {yi:.6f}\n")
                    for xi, yi in zip(x[::-1], y_bot[::-1]):
                        f.write(f" {xi:.6f}  {yi:.6f}\n")
                info = {"dat": str(dat_path)}
                if save_plots:
                    fig = plt.figure(figsize=(12, 4))
                    plt.plot(x, y_top, "k-", linewidth=2)
                    plt.plot(x, y_bot, "k-", linewidth=2)
                    plt.fill_between(x, y_top, y_bot, color="cyan", alpha=0.1)
                    rect = patches.Rectangle(
                        (pos_x, -antenna_height / 2),
                        antenna_length,
                        antenna_height,
                        linewidth=2,
                        edgecolor="red",
                        facecolor="red",
                        alpha=0.5,
                    )
                    plt.gca().add_patch(rect)
                    plt.axis("equal")
                    plt.grid(True, linestyle="--", alpha=0.5)
                    img_path = img_dir / f"{name}.png"
                    _save_png(fig, img_path)
                    info["img"] = str(img_path)
                output[name] = info
                counter += 1
                break  # espesor mínimo para este sharpness
    print(f"[BEZIER] Generados {counter} perfiles.")
    return output
