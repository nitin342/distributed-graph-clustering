"""
contract.py - graph contraction and multi-level runner for DSLM-Mod.

After local moving, nodes in the same cluster are collapsed into a single
super-node. Inter-cluster edges are summed; intra-cluster edges become
self-loops so that deg(super-node) = vol(original cluster). The algorithm
then reruns on the smaller graph until nothing moves.
"""

from collections import defaultdict

from graph import compute_degrees, total_volume, singleton_clustering
from dslm import local_moving, _ts


def contract_graph(graph, clustering):
    """Collapse each cluster into a super-node.

    Returns (super_graph, node_to_super, super_to_nodes).
    """
    unique_clusters = sorted(set(clustering.values()))
    cluster_to_id = {c: i for i, c in enumerate(unique_clusters)}

    node_to_super = {v: cluster_to_id[clustering[v]] for v in graph}

    super_to_nodes = defaultdict(list)
    for v, sv in node_to_super.items():
        super_to_nodes[sv].append(v)

    n_super = len(unique_clusters)
    # Make sure every super-node appears as a key, even if it has no edges.
    super_graph = {i: defaultdict(float) for i in range(n_super)}

    for v, nbrs in graph.items():
        sv = node_to_super[v]
        for u, w in nbrs.items():
            su = node_to_super[u]
            if sv == su:
                # Intra-cluster edge: becomes a self-loop on the super-node.
                # Preserving this is critical: it keeps deg(super-node) = vol(original cluster),
                # which prevents the contracted graph from falsely merging communities.
                super_graph[sv][sv] += w
            else:
                super_graph[sv][su] += w

    return (
        {sv: dict(nbrs) for sv, nbrs in super_graph.items()},
        node_to_super,
        {sv: list(nodes) for sv, nodes in super_to_nodes.items()},
    )


def unpack_clustering(super_clustering, super_to_nodes):
    """Map super-node cluster assignments back to original nodes."""
    result = {}
    for sv, cluster in super_clustering.items():
        for v in super_to_nodes[sv]:
            result[v] = cluster
    return result


def run_multilevel(
    graph, degrees, total_vol, n_subrounds=4, max_rounds=8, seed=42, verbose=False
):
    """Run DSLM-Mod with multi-level contraction. Returns original-node clustering."""
    current_graph = graph
    current_degrees = degrees
    current_vol = total_vol
    current_clustering = singleton_clustering(graph)

    # Keep one super_to_nodes mapping per level so we can unpack at the end.
    stored_maps = []
    level = 0

    while True:
        if verbose:
            n_clusters_before = len(set(current_clustering.values()))
            print(
                f"[{_ts()}] Level {level}: {len(current_graph)} nodes, "
                f"{n_clusters_before} initial clusters",
                flush=True,
            )

        current_clustering, rounds, any_change = local_moving(
            current_graph,
            current_clustering,
            current_degrees,
            current_vol,
            n_subrounds=n_subrounds,
            max_rounds=max_rounds,
            seed=seed,
            verbose=verbose,
        )

        if not any_change:
            # Nothing moved at this level; we're done.
            _, _, super_to_nodes = contract_graph(current_graph, current_clustering)
            stored_maps.append(super_to_nodes)
            break

        super_graph, _, super_to_nodes = contract_graph(
            current_graph, current_clustering
        )
        stored_maps.append(super_to_nodes)

        if len(super_graph) >= len(current_graph):
            # Contraction did not reduce graph size; stop.
            break

        current_graph = super_graph
        current_degrees = compute_degrees(current_graph)
        current_vol = total_volume(current_degrees)
        current_clustering = singleton_clustering(current_graph)
        level += 1

    # Walk back through levels to get original-node assignments.
    result = current_clustering
    for super_to_nodes in reversed(stored_maps):
        result = unpack_clustering(result, super_to_nodes)

    return result
