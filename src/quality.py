r"""
quality.py - Modularity computation and delta-modularity for a node move.

Modularity (Brandes et al. 2008):

    Q = sum_C [ (vol(C) - cut(C)) / vol(V)  -  (vol(C) / vol(V))^2 ]

where:
    vol(C)  = sum of degrees of nodes in C
    cut(C)  = total weight of edges between C and V\C
    vol(V)  = sum of all degrees = 2 * total edge weight

Delta-modularity for moving node v from cluster A to cluster B:

    dQ = [ 2*w(v,B)/M  -  2*deg(v)*vol(B)/M^2 ]
       - [ 2*w(v,A\v)/M  -  2*deg(v)*vol(A\v)/M^2 ]

where M = vol(V).
"""

from collections import defaultdict


def cluster_volumes(clustering, degrees):
    """Return {cluster_id: vol(cluster)} for all clusters."""
    vols = defaultdict(float)
    for node, cluster in clustering.items():
        vols[cluster] += degrees[node]
    return dict(vols)


def modularity(graph, clustering, degrees, total_vol):
    """Compute the modularity Q of a clustering."""
    if total_vol == 0:
        return 0.0

    vols = cluster_volumes(clustering, degrees)

    # Sum intra-cluster edge weight per cluster.
    # Each undirected edge (u,v) appears as both u->v and v->u in the adjacency,
    # so divide by 2 at the end.
    intra = defaultdict(float)
    for u, nbrs in graph.items():
        cu = clustering[u]
        for v, w in nbrs.items():
            if clustering[v] == cu:
                intra[cu] += w

    q = 0.0
    for cluster, vol in vols.items():
        two_intra = intra.get(cluster, 0.0)  # already doubled
        q += two_intra / total_vol - (vol / total_vol) ** 2

    return q


def delta_modularity(w_v_candidate, vol_candidate,
                     w_v_current, vol_current_minus_v,
                     deg_v, total_vol):
    """Delta-Q for moving v from its current cluster A to candidate cluster C.

    gain_add    = benefit of joining C
    gain_remove = savings from leaving A (negative cost)
    """
    M = total_vol
    gain_add    =  2 * w_v_candidate / M - 2 * deg_v * vol_candidate    / (M * M)
    gain_remove = -(2 * w_v_current  / M - 2 * deg_v * vol_current_minus_v / (M * M))
    return gain_add + gain_remove
