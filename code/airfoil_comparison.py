"""
Ranking y visualizacion de resultados aerodinamicos.
Se invoca desde main.py (flag --run-comparison) o como script standalone.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:  # matplotlib es opcional
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - dependencia opcional
    plt = None


NUM_FIELDS = ("alpha", "Re", "mach", "CL", "CD", "CM")


@dataclass
class Row:
    solver: str
    airfoil: str
    alpha: float
    Re: float
    mach: float
    CL: float
    CD: float
    CM: float

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> Optional["Row"]:
        try:
            return cls(
                solver=data.get("solver", ""),
                airfoil=data.get("airfoil", ""),
                alpha=float(data.get("alpha", 0.0)),
                Re=float(data.get("Re", 0.0)),
                mach=float(data.get("mach", 0.0)),
                CL=float(data.get("CL", 0.0)),
                CD=float(data.get("CD", 0.0)),
                CM=float(data.get("CM", 0.0)),
            )
        except Exception:
            return None


def _read_rows(csv_in: Path) -> List[Row]:
    if not csv_in.exists():
        raise FileNotFoundError(f"No se encontró el CSV de entrada: {csv_in}")
    rows: List[Row] = []
    with csv_in.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            r = Row.from_dict(raw)
            if r is not None:
                rows.append(r)
    return rows


def _filter_rows(
    rows: Iterable[Row],
    solver: Optional[str] = None,
    aoa_min: Optional[float] = None,
    aoa_max: Optional[float] = None,
) -> List[Row]:
    out = []
    for r in rows:
        if solver and r.solver != solver:
            continue
        if aoa_min is not None and r.alpha < aoa_min:
            continue
        if aoa_max is not None and r.alpha > aoa_max:
            continue
        out.append(r)
    return out


def _group_by_airfoil(rows: Iterable[Row]) -> Dict[str, List[Row]]:
    groups: Dict[str, List[Row]] = {}
    for r in rows:
        groups.setdefault(r.airfoil, []).append(r)
    return groups


def _metric_value(rows: List[Row], metric: str) -> Optional[float]:
    if not rows:
        return None
    metric = metric.lower()
    if metric == "cd_mean":
        vals = [r.CD for r in rows]
        return sum(vals) / len(vals)
    if metric == "cd_min":
        return min(r.CD for r in rows)
    if metric == "cl_mean":
        vals = [r.CL for r in rows]
        return sum(vals) / len(vals)
    if metric == "clcd_mean":
        ratios = [r.CL / r.CD for r in rows if r.CD != 0]
        return (sum(ratios) / len(ratios)) if ratios else None
    if metric == "clcd_max":
        ratios = [r.CL / r.CD for r in rows if r.CD != 0]
        return max(ratios) if ratios else None
    raise ValueError(f"Métrica desconocida: {metric}")


def _sort_key(metric: str):
    metric = metric.lower()
    # cd_* -> menor es mejor; resto mayor es mejor
    if metric in ("cd_mean", "cd_min"):
        return lambda item: item["value"]
    return lambda item: -item["value"]


def compute_ranking(
    csv_in: Path,
    metric: str = "cd_mean",
    solver: Optional[str] = None,
    aoa_min: Optional[float] = None,
    aoa_max: Optional[float] = None,
) -> List[Dict[str, float]]:
    rows = _filter_rows(_read_rows(csv_in), solver=solver, aoa_min=aoa_min, aoa_max=aoa_max)
    groups = _group_by_airfoil(rows)
    ranking: List[Dict[str, float]] = []
    for airfoil, rws in groups.items():
        value = _metric_value(rws, metric)
        if value is None:
            continue
        ranking.append(
            {
                "airfoil": airfoil,
                "metric": metric,
                "value": value,
                "count": len(rws),
                "solver": solver or "all",
            }
        )
    ranking.sort(key=_sort_key(metric))
    return ranking


def _plot_ranking(ranking: List[Dict[str, float]], metric: str, plot_dir: Path, top_n: int = 10):
    if plt is None:
        print("[WARN] matplotlib no está instalado; no se generan gráficos.")
        return
    plot_dir.mkdir(parents=True, exist_ok=True)
    trimmed = ranking[:top_n]
    if not trimmed:
        print("[WARN] No hay datos para graficar.")
        return
    labels = [r["airfoil"] for r in trimmed]
    values = [r["value"] for r in trimmed]
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(range(len(trimmed)), values, color="#f03a47")
    ax.invert_yaxis()
    ax.set_xlabel(metric.upper())
    ax.set_title(f"TOP {top_n} - {metric.upper()}")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.set_yticks(range(len(trimmed)))
    ax.set_yticklabels(labels, fontsize=8)
    # destacar primer lugar
    if bars:
        bars[0].set_color("#2de2e6")
    out_path = plot_dir / f"ranking_{metric}.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"[PLOT] Ranking guardado en {out_path}")


def _plot_polar(rows: Iterable[Row], plot_dir: Path):
    if plt is None:
        return
    rows = list(rows)
    if not rows:
        return
    plot_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    for solver in sorted({r.solver for r in rows}):
        solver_rows = [r for r in rows if r.solver == solver]
        ax.scatter([r.CD for r in solver_rows], [r.CL for r in solver_rows], label=solver, s=30, alpha=0.8)
    ax.set_xlabel("CD")
    ax.set_ylabel("CL")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend()
    out_path = plot_dir / "polar_cl_cd.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"[PLOT] Polar CL-CD guardado en {out_path}")


def save_csv(ranking: List[Dict[str, float]], csv_out: Path):
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    with csv_out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["airfoil", "metric", "value", "count", "solver"])
        writer.writeheader()
        for row in ranking:
            writer.writerow(row)
    print(f"[CSV] Ranking exportado a {csv_out}")


def run_comparison(
    csv_in: Path,
    csv_out: Path,
    metric: str = "cd_mean",
    solver: Optional[str] = None,
    aoa_min: Optional[float] = None,
    aoa_max: Optional[float] = None,
    plot: bool = False,
    plot_dir: Optional[Path] = None,
    top_n: int = 10,
) -> List[Dict[str, float]]:
    ranking = compute_ranking(csv_in, metric=metric, solver=solver, aoa_min=aoa_min, aoa_max=aoa_max)
    save_csv(ranking, csv_out)
    if plot:
        plot_target = plot_dir or csv_out.parent
        _plot_ranking(ranking, metric, plot_target, top_n=top_n)
        rows = _filter_rows(_read_rows(csv_in), solver=solver, aoa_min=aoa_min, aoa_max=aoa_max)
        _plot_polar(rows, plot_target)
    return ranking


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ranking y plots de perfiles a partir de un CSV combinado.")
    parser.add_argument("--input", type=Path, required=True, help="CSV de entrada (combined_results.csv)")
    parser.add_argument("--metric", type=str, default="cd_mean",
                        help="cd_mean, cd_min, cl_mean, clcd_mean, clcd_max")
    parser.add_argument("--solver", type=str, default=None, help="Filtrar solver (su2-incomp, aerosandbox-neuralfoil...)")
    parser.add_argument("--aoa-min", type=float, default=None, help="Ángulo mínimo")
    parser.add_argument("--aoa-max", type=float, default=None, help="Ángulo máximo")
    parser.add_argument("--output", type=Path, default=Path("results/airfoil_rankings.csv"), help="CSV de salida")
    parser.add_argument("--plot", action="store_true", help="Generar gráficos")
    parser.add_argument("--plot-dir", type=Path, default=None, help="Directorio para los PNG")
    parser.add_argument("--top-n", type=int, default=10, help="Top-N para el ranking de barras")
    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()
    run_comparison(
        csv_in=args.input,
        csv_out=args.output,
        metric=args.metric,
        solver=args.solver,
        aoa_min=args.aoa_min,
        aoa_max=args.aoa_max,
        plot=args.plot,
        plot_dir=args.plot_dir,
        top_n=args.top_n,
    )


if __name__ == "__main__":
    main()
