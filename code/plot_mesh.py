import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
except ImportError as exc:
    raise SystemExit("Necesitas matplotlib para graficar: pip install matplotlib") from exc


def _parse_header_int(line: str, key: str) -> int:
    if key not in line:
        raise ValueError(f"No se encontró {key} en el archivo SU2.")
    return int(line.split("=")[1])


def load_su2(mesh_path: Path) -> Tuple[np.ndarray, List[List[int]], Dict[str, List[Tuple[int, int]]]]:
    """
    Carga un mallado SU2 2D (formato ASCII) y devuelve:
    - coords: array (N,2) con las coordenadas de cada nodo (índice según el archivo)
    - elements: lista de conectividades (solo índices de nodos, se ignora el tag final)
    - markers: dict con las aristas por marcador, cada arista es una tupla (n1, n2)
    """
    lines = mesh_path.read_text().splitlines()
    idx = 0

    ndime = _parse_header_int(lines[idx], "NDIME")
    if ndime != 2:
        raise ValueError(f"Solo se soportan mallas 2D, NDIME={ndime}")
    idx += 1

    nelem = _parse_header_int(lines[idx], "NELEM")
    idx += 1
    elements: List[List[int]] = []
    for _ in range(nelem):
        parts = lines[idx].split()
        if not parts:
            idx += 1
            continue
        # formato: <tipo> n1 n2 n3 n4 tag
        node_ids = [int(v) for v in parts[1:-1]]
        elements.append(node_ids)
        idx += 1

    npoin = _parse_header_int(lines[idx], "NPOIN")
    idx += 1
    nodes_map: Dict[int, Tuple[float, float]] = {}
    for i in range(npoin):
        parts = lines[idx].split()
        coords = tuple(float(v) for v in parts[:ndime])
        node_id = int(parts[ndime]) if len(parts) > ndime else i
        nodes_map[node_id] = coords
        idx += 1

    max_idx = max(nodes_map)
    coords = np.zeros((max_idx + 1, 2))
    for nid, xy in nodes_map.items():
        coords[nid] = xy

    nmark = _parse_header_int(lines[idx], "NMARK")
    idx += 1
    markers: Dict[str, List[Tuple[int, int]]] = {}
    for _ in range(nmark):
        tag_line = lines[idx]
        tag = tag_line.split("=", 1)[1].strip()
        idx += 1
        m_elems = _parse_header_int(lines[idx], "MARKER_ELEMS")
        idx += 1
        edges: List[Tuple[int, int]] = []
        for _ in range(m_elems):
            parts = lines[idx].split()
            if len(parts) < 3:
                idx += 1
                continue
            edges.append((int(parts[1]), int(parts[2])))
            idx += 1
        markers[tag] = edges

    return coords, elements, markers


def plot_mesh(mesh_path: Path, boundary_only: bool = False, save_path: Path | None = None) -> None:
    coords, elements, markers = load_su2(mesh_path)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(mesh_path.name)

    if not boundary_only:
        segs = []
        for conn in elements:
            pts = coords[conn]
            closed = np.vstack([pts, pts[0]])
            segs.extend(zip(closed[:-1], closed[1:]))
        if segs:
            lc = LineCollection(segs, colors="#b0b0b0", linewidths=0.3, alpha=0.8)
            ax.add_collection(lc)

    # Colores distintos para los marcadores
    color_cycle = ["#d62728", "#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b"]
    for i, (tag, edges) in enumerate(markers.items()):
        segs = [(coords[a], coords[b]) for a, b in edges]
        if not segs:
            continue
        lc = LineCollection(
            segs,
            colors=color_cycle[i % len(color_cycle)],
            linewidths=1.0 if tag.lower() == "airfoil" else 0.8,
            label=tag,
        )
        ax.add_collection(lc)

    ax.legend()
    ax.autoscale()
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.grid(True, linestyle="--", alpha=0.3)

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"[OK] Figura guardada en {save_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Graficar mallas SU2 2D (contornos o malla completa).")
    parser.add_argument("mesh", type=str, help="Ruta del archivo .su2 a visualizar")
    parser.add_argument("--boundary-only", action="store_true", help="Solo dibujar contornos (marcadores)")
    parser.add_argument("--save", type=str, default=None, help="Guardar PNG en la ruta indicada en lugar de mostrar")
    args = parser.parse_args()

    mesh_path = Path(args.mesh)
    if not mesh_path.exists():
        raise SystemExit(f"No se encontró el archivo: {mesh_path}")

    save_path = Path(args.save) if args.save else None
    plot_mesh(mesh_path, boundary_only=args.boundary_only, save_path=save_path)


if __name__ == "__main__":
    main()
