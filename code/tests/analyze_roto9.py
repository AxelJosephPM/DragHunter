"""
Analisis del perfil ROTO 9 a partir de airfoil_rankings.xlsx.
Genera tablas y graficas separadas por condicion de vuelo (Mach/Re/altitud/AoA set).
Ejecuta:
    python analyze_roto9.py
Requisitos: pandas, matplotlib, openpyxl (lector xlsx).
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

EXCEL_PATH = Path("airfoil_rankings.xlsx")
SHEET_NAME = "todo lo importante simulaciones"
HEADER_ROW = 3  # fila 4 (0-index) contiene los nombres de columna
PROFILE_FILTER = "roto 9"
OUT_DIR = Path("analysis_roto9")
# Opciones de ajuste/regresion
ENABLE_REGRESSION = False
# Umbral de AoA (grados) para separar zona lineal y zona de entrada en perdida (ajuste cuadratico)
REG_SPLIT_AOA = 8.0


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de columnas y elimina columnas vacias."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    # elimina columnas completamente NaN
    df = df.dropna(axis=1, how="all")
    return df


def load_roto9(path: Path) -> pd.DataFrame:
    """Lee el Excel y filtra filas del perfil ROTO 9."""
    df = pd.read_excel(path, sheet_name=SHEET_NAME, header=HEADER_ROW)
    df = _clean_columns(df)
    # mantengo solo filas con datos en 'perfil'
    df = df[df["perfil"].notna()]
    mask = df["perfil"].astype(str).str.contains(PROFILE_FILTER, case=False, na=False)
    df = df[mask].copy()
    # fuerza numericos donde aplica
    num_cols = ["Cl_true", "Cd_true", "Cm", "L", "D", "mach", "Re", "AoA"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # calcula razones utiles
    df["cl_cd"] = df.apply(
        lambda r: r["Cl_true"] / r["Cd_true"] if r.get("Cd_true", 0) not in (0, None) else None,
        axis=1,
    )
    if "L" in df.columns and "D" in df.columns:
        df["L_over_D"] = df.apply(
            lambda r: r["L"] / r["D"] if (r.get("D") not in (0, None)) else None,
            axis=1,
        )
    return df


def save_table(df: pd.DataFrame, name: str):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{name}.csv"
    df.to_csv(out, index=False)
    print(f"[CSV] {out}")


def _add_regression(ax, x, y, split_aoa: float = None, color_lin="#1f77b4", color_quad="#d62728"):
    """Dibuja regresiones: lineal en zona baja y cuadratica en zona alta si hay datos."""
    if split_aoa is None:
        return
    x = np.asarray(x)
    y = np.asarray(y)
    mask = ~np.isnan(x) & ~np.isnan(y)
    x = x[mask]
    y = y[mask]
    if len(x) < 3:
        return
    # Lineal para x <= split_aoa
    m_lin = x <= split_aoa
    if m_lin.sum() >= 2:
        coeffs = np.polyfit(x[m_lin], y[m_lin], 1)
        xs = np.linspace(x[m_lin].min(), x[m_lin].max(), 50)
        ys = np.polyval(coeffs, xs)
        ax.plot(xs, ys, color=color_lin, linestyle="--", label="reg linear")
    # Cuadratica para x > split_aoa (zona entrada en pérdida)
    m_quad = x > split_aoa
    if m_quad.sum() >= 3:
        coeffs = np.polyfit(x[m_quad], y[m_quad], 2)
        xs = np.linspace(x[m_quad].min(), x[m_quad].max(), 50)
        ys = np.polyval(coeffs, xs)
        ax.plot(xs, ys, color=color_quad, linestyle="-.", label="reg cuadratica")


def plot_xy(df: pd.DataFrame, x: str, y: str, fname: Path, title: str, ylabel: str, use_regression=False):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(df[x], df[y], s=28, color="#1f77b4", alpha=0.9, label="datos")
    if use_regression and x.lower() == "aoa" and ENABLE_REGRESSION:
        _add_regression(ax, df[x].to_numpy(), df[y].to_numpy(), split_aoa=REG_SPLIT_AOA)
    ax.set_xlabel(x)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.4)
    if any(hl.get_label() != "_nolegend_" for hl in ax.get_lines()) or len(ax.collections) > 0:
        ax.legend()
    fig.tight_layout()
    fig.savefig(fname, dpi=150)
    plt.close(fig)
    print(f"[PLOT] {fname}")


def plot_scatter(df: pd.DataFrame, x: str, y: str, fname: Path, title: str, xlabel: str, ylabel: str):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(df[x], df[y], alpha=0.8, s=28, color="#1f77b4", label="datos")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()
    fig.tight_layout()
    fig.savefig(fname, dpi=150)
    plt.close(fig)
    print(f"[PLOT] {fname}")


def plot_combined_xy(data_by_cond, x: str, y: str, fname: Path, title: str, ylabel: str, use_regression=False):
    """Graficas overlay de varias condiciones en una figura."""
    fig, ax = plt.subplots(figsize=(7.5, 5))
    colors = plt.cm.tab10.colors
    for i, (cond, sub) in enumerate(data_by_cond):
        color = colors[i % len(colors)]
        sub = sub.dropna(subset=[x, y])
        if sub.empty:
            continue
        ax.scatter(sub[x], sub[y], s=30, color=color, alpha=0.85, label=cond)
        if use_regression and x.lower() == "aoa" and ENABLE_REGRESSION:
            _add_regression(ax, sub[x].to_numpy(), sub[y].to_numpy(), split_aoa=REG_SPLIT_AOA, color_lin=color, color_quad=color)
    ax.set_xlabel(x)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fname.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(fname, dpi=150)
    plt.close(fig)
    print(f"[PLOT] {fname}")


def condition_key(row: pd.Series) -> str:
    """Etiqueta de condicion de vuelo."""
    mach = row.get("mach", None)
    Re = row.get("Re", None)
    alt = row.get("altitud", None)
    parts = []
    if pd.notna(mach):
        parts.append(f"M{float(mach):.3f}")
    if pd.notna(Re):
        parts.append(f"Re{int(Re):d}")
    if pd.notna(alt):
        parts.append(f"Alt{float(alt):.0f}")
    return "_".join(parts) if parts else "condicion_desconocida"


def main():
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"No existe {EXCEL_PATH}")

    df = load_roto9(EXCEL_PATH)
    if df.empty:
        print("No se encontraron filas para ROTO 9.")
        return

    # Tabla limpia principal (solo columnas con nombre util)
    keep_cols = [c for c in df.columns if not c.startswith("Unnamed")]
    df_clean = df[keep_cols]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    save_table(df_clean, "roto9_raw")

    # Analisis por condicion de vuelo (Mach/Re/altitud)
    df_clean.loc[:, "condicion"] = df_clean.apply(condition_key, axis=1)
    summary_rows = []

    data_by_cond = []
    for cond, sub in df_clean.groupby("condicion"):
        cond_dir = OUT_DIR / cond
        cond_dir.mkdir(parents=True, exist_ok=True)
        # ordenar por AoA
        sub = sub.sort_values(by="AoA")
        sub.to_csv(cond_dir / "data.csv", index=False)
        print(f"[COND] {cond} -> {len(sub)} filas")
        # plots por condicion
        plot_xy(sub, "AoA", "Cl_true", cond_dir / "cl_vs_aoa.png", f"Cl vs AoA ({cond})", "Cl", use_regression=True)
        plot_xy(sub, "AoA", "Cd_true", cond_dir / "cd_vs_aoa.png", f"Cd vs AoA ({cond})", "Cd", use_regression=True)
        plot_xy(sub, "AoA", "cl_cd", cond_dir / "clcd_vs_aoa.png", f"Cl/Cd vs AoA ({cond})", "Cl/Cd", use_regression=True)
        plot_scatter(sub, "Cd_true", "Cl_true", cond_dir / "polar_cl_cd.png", f"Polar Cl vs Cd ({cond})", "Cd", "Cl")
        if "L_over_D" in sub.columns and sub["L_over_D"].notna().any():
            plot_xy(sub, "AoA", "L_over_D", cond_dir / "ld_vs_aoa.png", f"L/D vs AoA ({cond})", "L/D", use_regression=True)
        # resumen simple
        summary_rows.append(
            {
                "condicion": cond,
                "AoA_min": sub["AoA"].min(),
                "AoA_max": sub["AoA"].max(),
                "Cl_max": sub["Cl_true"].max(),
                "Cd_min": sub["Cd_true"].min(),
                "ClCd_max": sub["cl_cd"].max(),
                "rows": len(sub),
            }
        )
        data_by_cond.append((cond, sub))

    summary_df = pd.DataFrame(summary_rows)
    save_table(summary_df, "resumen_condiciones")

    # Graficas combinadas (todas las condiciones en una sola)
    combined_dir = OUT_DIR / "combined"
    plot_combined_xy(data_by_cond, "AoA", "Cl_true", combined_dir / "cl_vs_aoa_all.png", "Cl vs AoA (todas las condiciones)", "Cl", use_regression=True)
    plot_combined_xy(data_by_cond, "AoA", "Cd_true", combined_dir / "cd_vs_aoa_all.png", "Cd vs AoA (todas las condiciones)", "Cd", use_regression=True)
    plot_combined_xy(data_by_cond, "AoA", "cl_cd", combined_dir / "clcd_vs_aoa_all.png", "Cl/Cd vs AoA (todas las condiciones)", "Cl/Cd", use_regression=True)
    # polar combinada
    plot_combined_xy(data_by_cond, "Cd_true", "Cl_true", combined_dir / "polar_cl_cd_all.png", "Polar Cl vs Cd (todas las condiciones)", "Cl", use_regression=False)
    # L/D combinado si existe
    has_ld = any("L_over_D" in sub.columns and sub["L_over_D"].notna().any() for _, sub in data_by_cond)
    if has_ld:
        plot_combined_xy(data_by_cond, "AoA", "L_over_D", combined_dir / "ld_vs_aoa_all.png", "L/D vs AoA (todas las condiciones)", "L/D", use_regression=True)

    print("\n[RESUMEN POR CONDICION]")
    print(summary_df)


if __name__ == "__main__":
    main()
