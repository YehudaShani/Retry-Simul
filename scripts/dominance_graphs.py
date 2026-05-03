"""Build dominance graphs from ranking performance JSON files."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from retry_simul.wallet_enumerations import oneBitIndices

_DEFAULT_OUTPUT_DIR_NAME = "dominance_graphs"

Wallet = tuple[int, ...]
Edge = tuple[Wallet, Wallet]


def _repo_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else _REPO_ROOT / path


def wallet_key(wallet: Iterable[int]) -> Wallet:
    return tuple(int(bitmask) for bitmask in wallet)


def wallet_label(wallet: Wallet) -> str:
    return " ∨ ".join(_bitmask_label(bitmask) for bitmask in wallet)


def _bitmask_label(bitmask: int) -> str:
    indices = oneBitIndices(bitmask)
    return "(" + " ∧ ".join(indices) + ")" if indices else "0"


def load_ranking_cases(path: str | Path) -> list[dict[str, Any]]:
    input_path = _repo_path(path)
    with input_path.open("r", encoding="utf-8") as f:
        cases = json.load(f)

    if not isinstance(cases, list):
        raise ValueError(f"Expected a list of probability cases in {input_path}")

    for case_index, case in enumerate(cases):
        if not isinstance(case, dict) or not isinstance(case.get("wallets"), list):
            raise ValueError(
                f"Expected case {case_index} in {input_path} to contain a wallets list"
            )

    return cases


def collect_wallet_scores(cases: list[dict[str, Any]]) -> dict[Wallet, list[float]]:
    if not cases:
        raise ValueError("Cannot build a dominance graph from an empty case list")

    first_case_wallets = cases[0]["wallets"]
    wallet_order = [wallet_key(entry["wallet"]) for entry in first_case_wallets]
    expected_wallets = set(wallet_order)

    if len(wallet_order) != len(expected_wallets):
        raise ValueError("The first case contains duplicate wallets")

    scores: dict[Wallet, list[float]] = {wallet: [] for wallet in wallet_order}
    for case_index, case in enumerate(cases):
        case_scores: dict[Wallet, float] = {}
        for entry in case["wallets"]:
            wallet = wallet_key(entry["wallet"])
            if wallet in case_scores:
                raise ValueError(f"Case {case_index} contains duplicate wallet {wallet}")
            case_scores[wallet] = float(entry["success_probability"])

        case_wallets = set(case_scores)
        if case_wallets != expected_wallets:
            missing = sorted(expected_wallets - case_wallets)
            extra = sorted(case_wallets - expected_wallets)
            raise ValueError(
                f"Case {case_index} has a different wallet set. "
                f"Missing: {missing[:3]}; extra: {extra[:3]}"
            )

        for wallet in wallet_order:
            scores[wallet].append(case_scores[wallet])

    return scores


def dominates(
    dominator_scores: list[float],
    dominated_scores: list[float],
    epsilon: float = 0.0,
) -> bool:
    return all(
        dominator > dominated + epsilon
        for dominator, dominated in zip(dominator_scores, dominated_scores)
    )


def build_dominance_edges(
    scores_by_wallet: dict[Wallet, list[float]],
    epsilon: float = 0.0,
) -> set[Edge]:
    edges: set[Edge] = set()
    wallets = list(scores_by_wallet)

    for source in wallets:
        source_scores = scores_by_wallet[source]
        for target in wallets:
            if source == target:
                continue
            if dominates(source_scores, scores_by_wallet[target], epsilon):
                edges.add((source, target))

    return edges


def transitive_reduction(nodes: Iterable[Wallet], edges: set[Edge]) -> set[Edge]:
    adjacency = _adjacency(nodes, edges)
    reachable_cache: dict[Wallet, set[Wallet]] = {}

    def reachable_from(node: Wallet) -> set[Wallet]:
        if node in reachable_cache:
            return reachable_cache[node]

        reachable: set[Wallet] = set()
        for child in adjacency[node]:
            reachable.add(child)
            reachable.update(reachable_from(child))

        reachable_cache[node] = reachable
        return reachable

    reduced_edges = set(edges)
    for source, target in edges:
        for intermediate in adjacency[source]:
            if intermediate == target:
                continue
            if target in reachable_from(intermediate):
                reduced_edges.discard((source, target))
                break

    return reduced_edges


def graph_metadata(nodes: Iterable[Wallet], edges: set[Edge]) -> dict[str, Any]:
    node_list = list(nodes)
    components = _connected_components(node_list, edges)
    edge_count = len(edges)
    node_count = len(node_list)
    is_tree = node_count > 0 and edge_count == node_count - 1 and len(components) == 1

    notes = []
    if not is_tree:
        notes.append(
            "The immediate dominance graph is not a single tree; "
            "some wallets are incomparable or have multiple immediate relationships."
        )

    return {
        "node_count": node_count,
        "edge_count": edge_count,
        "component_count": len(components),
        "component_sizes": [len(component) for component in components],
        "graph_type": "tree" if is_tree else "forest",
        "notes": notes,
    }


def build_dominance_graph(
    cases: list[dict[str, Any]],
    source_file: str | None = None,
    epsilon: float = 0.0,
) -> dict[str, Any]:
    scores_by_wallet = collect_wallet_scores(cases)
    nodes = list(scores_by_wallet)
    full_edges = build_dominance_edges(scores_by_wallet, epsilon)
    immediate_edges = transitive_reduction(nodes, full_edges)
    metadata = graph_metadata(nodes, immediate_edges)
    node_ids = {wallet: f"w{index:04d}" for index, wallet in enumerate(nodes, start=1)}

    graph = {
        "source_file": source_file,
        "case_count": len(cases),
        **metadata,
        "full_edge_count": len(full_edges),
        "nodes": [
            {
                "id": node_ids[wallet],
                "wallet": list(wallet),
                "label": wallet_label(wallet),
                "success_probabilities": scores_by_wallet[wallet],
            }
            for wallet in nodes
        ],
        "edges": [
            {
                "source": node_ids[source],
                "target": node_ids[target],
                "source_wallet": list(source),
                "target_wallet": list(target),
            }
            for source, target in sorted(immediate_edges)
        ],
    }
    return graph


def write_graph_json(graph: dict[str, Any], output_path: str | Path) -> Path:
    output_path = _repo_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)
    return output_path


def render_graph_image(graph: dict[str, Any], output_path: str | Path) -> Path:
    import matplotlib.pyplot as plt

    output_path = _repo_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    node_ids = [node["id"] for node in graph["nodes"]]
    labels = {node["id"]: _plot_label(node["label"]) for node in graph["nodes"]}
    adjacency = {node_id: [] for node_id in node_ids}
    indegree = {node_id: 0 for node_id in node_ids}
    for edge in graph["edges"]:
        adjacency[edge["source"]].append(edge["target"])
        indegree[edge["target"]] += 1

    depths = _node_depths(node_ids, adjacency, indegree)
    layers: dict[int, list[str]] = defaultdict(list)
    for node_id in node_ids:
        layers[depths[node_id]].append(node_id)

    positions: dict[str, tuple[float, float]] = {}
    layer_y_positions: dict[int, float] = {}
    current_y = 0.0
    for depth in sorted(layers):
        layer_nodes = layers[depth]
        max_label_lines = max(labels[node_id].count("\n") + 1 for node_id in layer_nodes)
        layer_y_positions[depth] = -current_y
        current_y += max(1.8, max_label_lines * 0.45 + 1.0)

    for depth, layer_nodes in layers.items():
        layer_width = len(layer_nodes) - 1
        max_line_length = max(
            len(line)
            for node_id in layer_nodes
            for line in labels[node_id].splitlines()
        )
        horizontal_spacing = max(3.0, min(8.0, max_line_length * 0.16 + 1.0))
        for index, node_id in enumerate(layer_nodes):
            x = (index - layer_width / 2) * horizontal_spacing
            y = layer_y_positions[depth]
            positions[node_id] = (x, y)

    if positions:
        xs = [position[0] for position in positions.values()]
        ys = [position[1] for position in positions.values()]
        x_span = max(xs) - min(xs) + 2
        y_span = max(ys) - min(ys) + 2
    else:
        x_span = 8.0
        y_span = 5.0

    figure_width = max(10.0, min(240.0, x_span * 0.8))
    figure_height = max(6.0, min(240.0, y_span * 0.8))
    fig, ax = plt.subplots(figsize=(figure_width, figure_height))

    for edge in graph["edges"]:
        source = edge["source"]
        target = edge["target"]
        source_x, source_y = positions[source]
        target_x, target_y = positions[target]
        ax.annotate(
            "",
            xy=(target_x, target_y + 0.08),
            xytext=(source_x, source_y - 0.08),
            arrowprops={"arrowstyle": "->", "color": "0.35", "lw": 0.8},
            zorder=1,
        )

    for node_id, (x, y) in positions.items():
        label = labels[node_id]
        fontsize = 8 if len(node_ids) <= 120 else 7
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            color="black",
            fontsize=fontsize,
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": "white",
                "edgecolor": "tab:blue",
                "linewidth": 0.8,
                "alpha": 0.95,
            },
            zorder=3,
        )

    if positions:
        xs = [position[0] for position in positions.values()]
        ys = [position[1] for position in positions.values()]
        ax.set_xlim(min(xs) - 1, max(xs) + 1)
        ax.set_ylim(min(ys) - 1, max(ys) + 1)

    title_source = Path(graph["source_file"]).name if graph.get("source_file") else "ranking"
    ax.set_title(
        f"Dominance graph for {title_source}\n"
        f"{graph['graph_type']}: {graph['node_count']} nodes, {graph['edge_count']} edges"
    )
    ax.axis("off")
    dpi = 180 if len(node_ids) <= 120 else 150
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.01)
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
    return output_path


def render_graph_png(graph: dict[str, Any], output_path: str | Path) -> Path:
    return render_graph_image(graph, output_path)


def render_graph_svg(graph: dict[str, Any], output_path: str | Path) -> Path:
    return render_graph_image(graph, output_path)


def _plot_label(label: str) -> str:
    clauses = label.split(" ∨ ")
    if len(clauses) <= 2:
        return label

    wrapped_lines = [
        " ∨ ".join(clauses[index : index + 2])
        for index in range(0, len(clauses), 2)
    ]
    return "\n".join(wrapped_lines)


def process_ranking_file(path: str | Path, output_dir: str | Path | None = None) -> dict[str, Path]:
    input_path = _repo_path(path)
    if output_dir is None:
        output_dir = input_path.parent / _DEFAULT_OUTPUT_DIR_NAME
    else:
        output_dir = _repo_path(output_dir)

    cases = load_ranking_cases(input_path)
    graph = build_dominance_graph(cases, source_file=str(input_path.relative_to(_REPO_ROOT)))

    json_path = Path(output_dir) / f"{input_path.stem}_dominance_graph.json"
    png_path = Path(output_dir) / f"{input_path.stem}_dominance_graph.png"
    svg_path = Path(output_dir) / f"{input_path.stem}_dominance_graph.svg"
    write_graph_json(graph, json_path)
    render_graph_png(graph, png_path)
    render_graph_svg(graph, svg_path)

    return {
        "json": _repo_path(json_path),
        "png": _repo_path(png_path),
        "svg": _repo_path(svg_path),
    }


def discover_ranking_files(path: str | Path = "rankings") -> list[Path]:
    input_path = _repo_path(path)
    if input_path.is_file():
        return [input_path]

    if not input_path.is_dir():
        raise ValueError(f"Ranking path does not exist: {input_path}")

    if input_path.name == "rankings":
        candidates = sorted(input_path.glob("*/*.json"))
    else:
        candidates = sorted(input_path.glob("*.json"))

    return [
        candidate
        for candidate in candidates
        if candidate.parent.name != _DEFAULT_OUTPUT_DIR_NAME
        and not candidate.name.endswith("_dominance_graph.json")
    ]


def process_rankings(path: str | Path = "rankings") -> list[dict[str, Path]]:
    return [process_ranking_file(ranking_file) for ranking_file in discover_ranking_files(path)]


def _adjacency(nodes: Iterable[Wallet], edges: set[Edge]) -> dict[Wallet, set[Wallet]]:
    adjacency = {node: set() for node in nodes}
    for source, target in edges:
        adjacency[source].add(target)
    return adjacency


def _connected_components(nodes: list[Wallet], edges: set[Edge]) -> list[set[Wallet]]:
    neighbors = {node: set() for node in nodes}
    for source, target in edges:
        neighbors[source].add(target)
        neighbors[target].add(source)

    components: list[set[Wallet]] = []
    seen: set[Wallet] = set()
    for node in nodes:
        if node in seen:
            continue
        component = set()
        stack = [node]
        seen.add(node)
        while stack:
            current = stack.pop()
            component.add(current)
            for neighbor in neighbors[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(component)

    return components


def _node_depths(
    node_ids: list[str],
    adjacency: dict[str, list[str]],
    indegree: dict[str, int],
) -> dict[str, int]:
    remaining_indegree = dict(indegree)
    depths = {node_id: 0 for node_id in node_ids}
    queue = deque(node_id for node_id in node_ids if remaining_indegree[node_id] == 0)

    while queue:
        node_id = queue.popleft()
        for child in adjacency[node_id]:
            depths[child] = max(depths[child], depths[node_id] + 1)
            remaining_indegree[child] -= 1
            if remaining_indegree[child] == 0:
                queue.append(child)

    return depths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create immediate dominance graph JSON and PNG files from rankings."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="rankings",
        help="Ranking JSON file, ranking run directory, or rankings root directory.",
    )
    args = parser.parse_args()

    outputs = process_rankings(args.path)
    for output in outputs:
        print(f"Wrote {output['json']}")
        print(f"Wrote {output['png']}")
        print(f"Wrote {output['svg']}")


if __name__ == "__main__":
    main()
