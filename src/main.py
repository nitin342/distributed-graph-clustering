"""
main.py - entry point for DSLM-Mod.

Run from src/:
    python main.py                          # built-in toy graph
    python main.py --input ../data/graph.txt
    python main.py --input ../data/graph.txt --output ../results/out.txt
    python main.py --no-contraction --verbose
"""

import argparse
import time
from collections import defaultdict

from graph import (
    load_edge_list, make_ids_consecutive,
    compute_degrees, total_volume, singleton_clustering,
)
from quality import modularity
from dslm import local_moving
from contract import run_multilevel


# 12-node toy graph with 3 clear communities (K4 each) and 3 bridge edges.
# A: 0-3, B: 4-7, C: 8-11, bridges: 3-4, 7-8, 2-9
TOY_EDGES = [
    (0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3),   # A
    (4, 5), (4, 6), (4, 7), (5, 6), (5, 7), (6, 7),   # B
    (8, 9), (8, 10), (8, 11), (9, 10), (9, 11), (10, 11),  # C
    (3, 4), (7, 8), (2, 9),                             # bridges
]


def build_toy_graph():
    graph = defaultdict(lambda: defaultdict(float))
    for u, v in TOY_EDGES:
        graph[u][v] += 1.0
        graph[v][u] += 1.0
    return {node: dict(nbrs) for node, nbrs in graph.items()}


def run(args):
    if args.input:
        max_nodes = args.max_nodes if args.max_nodes else None
        suffix = f" (first {max_nodes} nodes)" if max_nodes else ""
        print(f"Loading graph from {args.input}{suffix} ...")
        graph = load_edge_list(args.input, max_nodes=max_nodes)
        graph, _ = make_ids_consecutive(graph)
    else:
        print("No input file given -- using built-in toy graph (12 nodes, 3 communities)")
        graph = build_toy_graph()

    degrees = compute_degrees(graph)
    total_vol = total_volume(degrees)
    n_edges = sum(len(v) for v in graph.values()) // 2
    print(f"Graph loaded: {len(graph)} nodes, {n_edges} edges")

    t0 = time.time()

    if args.no_contraction:
        clustering = singleton_clustering(graph)
        clustering, rounds, _ = local_moving(
            graph, clustering, degrees, total_vol,
            n_subrounds=args.subrounds,
            max_rounds=args.max_rounds,
            seed=args.seed,
            verbose=args.verbose,
        )
        print(f"Local moving done in {rounds} round(s)")
    else:
        clustering = run_multilevel(
            graph, degrees, total_vol,
            n_subrounds=args.subrounds,
            max_rounds=args.max_rounds,
            seed=args.seed,
            verbose=args.verbose,
        )

    elapsed = time.time() - t0

    q = modularity(graph, clustering, degrees, total_vol)
    n_clusters = len(set(clustering.values()))

    print(f"Clusters found : {n_clusters}")
    print(f"Modularity     : {q:.6f}")
    print(f"Time           : {elapsed:.3f}s")

    if args.output:
        with open(args.output, "w") as f:
            for node in sorted(clustering):
                f.write(f"{node}\t{clustering[node]}\n")
        print(f"Clustering saved to {args.output}")

    return clustering, q


def main():
    parser = argparse.ArgumentParser(
        description="DSLM-Mod: graph clustering via synchronous local moving"
    )
    parser.add_argument(
        "--input", type=str, default=None,
        help="Edge list file (tab or space separated; lines starting with # are skipped)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output file for clustering (node TAB cluster, one per line)",
    )
    parser.add_argument(
        "--subrounds", type=int, default=4,
        help="Sub-rounds per round (default: 4, as in the paper)",
    )
    parser.add_argument(
        "--max-rounds", type=int, default=8,
        help="Max rounds per local-moving phase (default: 8, as in the paper)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Hash seed for sub-round assignment (default: 42)",
    )
    parser.add_argument(
        "--no-contraction", action="store_true",
        help="Run one local-moving phase only, skip contraction (DSLM-Mod w/o Cont.)",
    )
    parser.add_argument(
        "--max-nodes", type=int, default=None,
        help="Only load the first N distinct node IDs (useful for testing on large graphs)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print per-round progress",
    )
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
