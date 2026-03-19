"""
graph.py - loading graphs and basic utilities

Graph format: dict of dicts  {node: {neighbor: weight, ...}, ...}
Undirected, weighted (weight=1 if not given in the file).
"""

from collections import defaultdict

import numpy as np
import pandas as pd


def load_edge_list(filepath, comment="#", max_nodes=None):
    """Load an undirected graph from a SNAP-style edge list.

    Uses pandas for fast parsing on large files.
    Self-loops are dropped; parallel edges are summed.
    If max_nodes is set, only keep edges where both endpoints are in
    the first max_nodes distinct IDs (handy for quick tests).
    Returns {node: {neighbor: weight}}.
    """
    df = pd.read_csv(
        filepath,
        sep=r"\s+",
        comment=comment,
        header=None,
        usecols=[0, 1],
        names=["u", "v"],
        dtype=np.int64,
        engine="c",
    )

    # Remove self-loops
    df = df[df["u"] != df["v"]]

    if max_nodes is not None:
        all_nodes = np.unique(df[["u", "v"]].values)
        keep = set(all_nodes[:max_nodes].tolist())
        df = df[df["u"].isin(keep) & df["v"].isin(keep)]

    # Build adjacency dict from numpy arrays (avoid Python-level row iteration)
    u_arr = df["u"].values
    v_arr = df["v"].values

    # Use pandas groupby to aggregate weights efficiently
    # Each edge appears twice (u->v and v->u)
    both_u = np.concatenate([u_arr, v_arr])
    both_v = np.concatenate([v_arr, u_arr])
    weights = np.ones(len(both_u), dtype=np.float64)

    agg = pd.DataFrame({"u": both_u, "v": both_v, "w": weights})
    agg = agg.groupby(["u", "v"], sort=False)["w"].sum().reset_index()

    graph = defaultdict(dict)
    for row in agg.itertuples(index=False):
        graph[row.u][row.v] = row.w

    return dict(graph)


def make_ids_consecutive(graph):
    """Remap node IDs to 0..n-1. Returns (new_graph, old_to_new)."""
    nodes = sorted(graph.keys())
    old_to_new = {old: new for new, old in enumerate(nodes)}
    new_graph = {
        old_to_new[u]: {old_to_new[v]: w for v, w in nbrs.items()}
        for u, nbrs in graph.items()
    }
    return new_graph, old_to_new


def compute_degrees(graph):
    """Weighted degree for each node."""
    return {v: sum(graph[v].values()) for v in graph}


def total_volume(degrees):
    """vol(V) = sum of all degrees = 2 * total edge weight."""
    return sum(degrees.values())


def singleton_clustering(graph):
    """Each node starts in its own cluster."""
    return {v: v for v in graph}
