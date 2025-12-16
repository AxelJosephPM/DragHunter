"""
Analisis y graficas CFD para airfoil_rankings.xlsx.
Genera:
  - Interpolacion polinomial Cl(alpha) (coeficientes guardados en TXT).
  - Graficas:
      * Mach vs Cd (lineas por AoA) -> drag divergence.
      * Cl vs AoA (curva de sustentacion, coloreada por Mach).
      * Polar Cl vs Cd.
      * Cd vs Altitud (lineas por Mach).
      * Drag (N) vs Altitud (lineas por Mach) usando densidad y Mach del dataset.
Salidas en: report_plots/

Ejecuta:
    python cfd_report.py
Requisitos: pandas, numpy, matplotlib, openpyxl.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

EXCEL_PATH = Path("airfoil_rankings.xlsx")
SHEET_NAME = "DATASET"  # nombre de la hoja en el Excel
HEADER_ROW = 17  # fila con headers reales en el Excel (0-index)
OUT_DIR = Path("report_plots")

# Parametros aero
GAMMA = 1.4
R_AIR = 287.05  # J/(kg*K)
SREF_M2 = 1.0   # area de referencia (m^2) -> AJUSTA A TU CASO

# Estilo global para plots (un poco más presentable)
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({
    "axes.facecolor": "#fcfcfd",
    "figure.facecolor": "white",
    "axes.edgecolor": "#b0b0b0",
    "grid.color": "#d0d0d0",
    "axes.titleweight": "bold",
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "legend.fontsize": 9,
    "font.size": 10,
})
PALETTE = plt.cm.tab10.colors


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(axis=1, how="all")
    return df


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=SHEET_NAME, header=HEADER_ROW)
    df = _clean_columns(df)
    # columnas clave que pueden traer espacios
    rename = {
        "perfil ": "perfil",
        "altitud ": "altitud",
        "y ": "y",
        "P_SIMULACION": "P_sim",
        "T_SIMULACION": "T_sim",
        "densidad ": "rho",
        "viscosidad": "mu",
    }
    df = df.rename(columns=rename)
    # filtrar filas con perfil no nulo
    df = df[df["perfil"].notna()]
    # numericos
    num_cols = ["mach", "AoA", "Cl_true", "Cd_true", "Cm", "rho", "Re", "altitud", "L", "D", "P_sim", "T_sim"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # derivado
    df["cl_cd"] = df.apply(
        lambda r: r["Cl_true"] / r["Cd_true"] if r.get("Cd_true") not in (0, None, np.nan) else np.nan, axis=1
    )
    # clean NaN rows for plotting convenience
    df = df.dropna(subset=["mach", "AoA", "Cl_true", "Cd_true", "altitud"], how="any")
    return df


def ensure_outdir():
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def plot_mach_cd(df: pd.DataFrame):
    """Drag divergence: Cd vs Mach, una linea por AoA."""
    ensure_outdir()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, aoa in enumerate(sorted(df["AoA"].unique())):
        sub = df[df["AoA"] == aoa].sort_values("mach")
        ax.plot(
            sub["mach"], sub["Cd_true"],
            marker="o", markersize=5, linewidth=2,
            color=PALETTE[i % len(PALETTE)],
            label=f"AoA {aoa:g}°",
        )
    ax.set_xlabel("Mach")
    ax.set_ylabel("Cd")
    ax.set_title("Cd vs Mach (Drag divergence)")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    path = OUT_DIR / "mach_vs_cd.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_cl_vs_aoa(df: pd.DataFrame):
    """Curva de sustentacion: Cl vs AoA, coloreado por Mach."""
    ensure_outdir()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    machs = sorted(df["mach"].unique())
    for i, m in enumerate(machs):
        sub = df[df["mach"] == m].sort_values("AoA")
        ax.plot(
            sub["AoA"], sub["Cl_true"],
            marker="o", markersize=5, linewidth=2,
            color=PALETTE[i % len(PALETTE)],
            label=f"M{m}",
        )
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel("Cl")
    ax.set_title("Cl vs AoA (curva de sustentacion)")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(title="Mach", fontsize=8)
    fig.tight_layout()
    path = OUT_DIR / "cl_vs_aoa.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_polar(df: pd.DataFrame):
    """Polar Cl vs Cd coloreada por Mach."""
    ensure_outdir()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    machs = sorted(df["mach"].unique())
    for i, m in enumerate(machs):
        sub = df[df["mach"] == m]
        ax.plot(
            sub["Cd_true"], sub["Cl_true"],
            marker="o", markersize=5, linewidth=2,
            color=PALETTE[i % len(PALETTE)],
            label=f"M{m}",
        )
    ax.set_xlabel("Cd")
    ax.set_ylabel("Cl")
    ax.set_title("Polar Cl vs Cd")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(title="Mach", fontsize=8)
    fig.tight_layout()
    path = OUT_DIR / "polar_cl_cd.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_cd_vs_alt(df: pd.DataFrame):
    """Cd vs altitud, lineas por Mach (AoA fijo default 0 si disponible)."""
    ensure_outdir()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    aoa_target = 0 if (df["AoA"] == 0).any() else df["AoA"].min()
    subset = df[df["AoA"] == aoa_target]
    for i, m in enumerate(sorted(subset["mach"].unique())):
        sub = subset[subset["mach"] == m].sort_values("altitud")
        ax.plot(
            sub["altitud"], sub["Cd_true"],
            marker="o", markersize=5, linewidth=2,
            color=PALETTE[i % len(PALETTE)],
            label=f"Mach {m}",
        )
    ax.set_xlabel("Altitud (m)")
    ax.set_ylabel("Cd")
    ax.set_title(f"Cd vs Altitud (AoA={aoa_target}°)")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = OUT_DIR / "cd_vs_altitud.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def build_cl_poly(df: pd.DataFrame, deg: int = 3):
    """Interpola Cl = f(AoA) (polinomio) con todos los datos disponibles."""
    aoa = df["AoA"].to_numpy()
    cl = df["Cl_true"].to_numpy()
    coeffs = np.polyfit(aoa, cl, deg=deg)
    poly = np.poly1d(coeffs)
    return poly


def save_poly(poly: np.poly1d):
    ensure_outdir()
    path = OUT_DIR / "cl_poly_coeffs.txt"
    terms = " + ".join([f"{coef:.6g} * x^{poly.order - i}" for i, coef in enumerate(poly.c)])
    with open(path, "w", encoding="utf-8") as f:
        f.write("Cl(AoA) polynomial fit (AoA en grados):\n")
        f.write(f"Cl(x) = {terms}\n\n")
        f.write("Uso en Python:\n")
        f.write("import numpy as np\n")
        f.write(f"poly = np.poly1d({poly.c.tolist()})\n")
        f.write("cl_est = poly(aoa_deg)\n")
    return path


def speed_of_sound(T):
    return np.sqrt(GAMMA * R_AIR * T)


def compute_drag(df: pd.DataFrame, sref_m2: float = SREF_M2) -> pd.DataFrame:
    """Calcula drag en N y retorna df con columna Drag_N."""
    df = df.copy()
    # si T_sim falta, usa ISA approx con lapse up to 11km
    def isa_temp(h):
        if h <= 11000:
            return 288.15 - 0.0065 * h
        else:
            return 216.65

    def rho_from_data(row):
        if pd.notna(row.get("rho")):
            return row["rho"]
        # fallback ISA simplificado
        h = row.get("altitud", 0) or 0
        T = isa_temp(h)
        p = 101325 * (T / 288.15) ** (9.81 / (287.05 * -0.0065)) if h <= 11000 else 22632 * np.exp(
            -9.81 * (h - 11000) / (287.05 * 216.65)
        )
        return p / (R_AIR * T)

    rho = df.apply(rho_from_data, axis=1)
    T = df.apply(lambda r: r["T_sim"] if pd.notna(r.get("T_sim")) else isa_temp(r.get("altitud", 0) or 0), axis=1)
    a = T.apply(speed_of_sound)
    V = df["mach"] * a
    q = 0.5 * rho * V * V  # N/m^2
    df["Drag_N"] = q * sref_m2 * df["Cd_true"]
    return df


def plot_drag_vs_alt(df: pd.DataFrame):
    """Drag vs altitud (usa Cd y rho, Mach de dataset)."""
    ensure_outdir()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, m in enumerate(sorted(df["mach"].unique())):
        sub = df[df["mach"] == m].sort_values("altitud")
        ax.plot(
            sub["altitud"], sub["Drag_N"],
            marker="o", markersize=5, linewidth=2,
            color=PALETTE[i % len(PALETTE)],
            label=f"Mach {m}",
        )
    ax.set_xlabel("Altitud (m)")
    ax.set_ylabel("Drag (N)")
    ax.set_title(f"Drag vs Altitud (Sref={SREF_M2} m^2)")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = OUT_DIR / "drag_vs_altitud.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def main():
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"No se encontró {EXCEL_PATH}")
    df = load_data(EXCEL_PATH)
    if df.empty:
        print("Dataset vacío.")
        return

    # Guardar polinomio Cl(AoA)
    poly = build_cl_poly(df, deg=3)
    poly_path = save_poly(poly)

    # Drag divergence (Mach vs Cd)
    mach_cd_path = plot_mach_cd(df)
    # Cl vs AoA
    cl_path = plot_cl_vs_aoa(df)
    # Polar
    polar_path = plot_polar(df)
    # Cd vs altitud (AoA fijo)
    cd_alt_path = plot_cd_vs_alt(df)
    # Drag vs altitud
    df_drag = compute_drag(df, sref_m2=SREF_M2)
    drag_alt_path = plot_drag_vs_alt(df_drag)

    # Resumen en consola
    print("\n[ARCHIVOS GENERADOS]")
    for p in (poly_path, mach_cd_path, cl_path, polar_path, cd_alt_path, drag_alt_path):
        print(f"- {p}")
    print("\nNota: Ajusta SREF_M2 en cfd_report.py al área real del radomo para fuerzas absolutas.")


if __name__ == "__main__":
    main()
