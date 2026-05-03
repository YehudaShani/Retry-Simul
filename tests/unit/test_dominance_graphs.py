"""Unit tests for ranking dominance graph construction."""

import json

from scripts.dominance_graphs import (
    build_dominance_edges,
    build_dominance_graph,
    collect_wallet_scores,
    transitive_reduction,
    wallet_label,
    wallet_key,
    write_graph_json,
)


def _case(scores):
    return {
        "probability": {"1": 0.25, "2": 0.25, "3": 0.25, "4": 0.25},
        "wallets": [
            {"wallet": wallet, "success_probability": success_probability}
            for wallet, success_probability in scores
        ],
    }


def test_strict_dominance_requires_beating_in_every_case():
    cases = [
        _case([([1], 0.9), ([2], 0.8), ([3], 0.9)]),
        _case([([1], 0.85), ([2], 0.75), ([3], 0.8)]),
    ]

    scores = collect_wallet_scores(cases)
    edges = build_dominance_edges(scores)

    assert (wallet_key([1]), wallet_key([2])) in edges
    assert (wallet_key([1]), wallet_key([3])) not in edges


def test_transitive_reduction_keeps_immediate_dominance_chain():
    cases = [
        _case([([1], 0.9), ([2], 0.8), ([3], 0.7)]),
        _case([([1], 0.85), ([2], 0.75), ([3], 0.65)]),
    ]
    scores = collect_wallet_scores(cases)

    full_edges = build_dominance_edges(scores)
    reduced_edges = transitive_reduction(scores.keys(), full_edges)

    assert full_edges == {
        (wallet_key([1]), wallet_key([2])),
        (wallet_key([1]), wallet_key([3])),
        (wallet_key([2]), wallet_key([3])),
    }
    assert reduced_edges == {
        (wallet_key([1]), wallet_key([2])),
        (wallet_key([2]), wallet_key([3])),
    }


def test_build_dominance_graph_marks_single_chain_as_tree():
    cases = [
        _case([([1], 0.9), ([2], 0.8), ([3], 0.7)]),
        _case([([1], 0.85), ([2], 0.75), ([3], 0.65)]),
    ]

    graph = build_dominance_graph(cases, source_file="rankings/example.json")

    assert graph["graph_type"] == "tree"
    assert graph["node_count"] == 3
    assert graph["edge_count"] == 2
    assert graph["full_edge_count"] == 3
    assert [(edge["source"], edge["target"]) for edge in graph["edges"]] == [
        ("w0001", "w0002"),
        ("w0002", "w0003"),
    ]


def test_wallet_label_uses_conjunction_notation():
    assert wallet_label(wallet_key([3, 5])) == "(1 ∧ 2) ∨ (1 ∧ 3)"


def test_write_graph_json_uses_expected_output_shape(tmp_path):
    cases = [
        _case([([1], 0.5), ([2], 0.4)]),
        _case([([1], 0.6), ([2], 0.3)]),
    ]
    graph = build_dominance_graph(cases, source_file="rankings/example.json")
    output_path = tmp_path / "example_dominance_graph.json"

    write_graph_json(graph, output_path)

    with output_path.open("r", encoding="utf-8") as f:
        saved_graph = json.load(f)

    assert set(saved_graph) >= {
        "source_file",
        "nodes",
        "edges",
        "edge_count",
        "node_count",
        "graph_type",
        "notes",
    }
    assert saved_graph["nodes"][0]["wallet"] == [1]
    assert saved_graph["nodes"][0]["label"] == "(1)"
    assert saved_graph["edges"] == [
        {
            "source": "w0001",
            "target": "w0002",
            "source_wallet": [1],
            "target_wallet": [2],
        }
    ]
