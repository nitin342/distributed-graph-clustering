"""
dslm.py - DSLM-Mod: synchronous local moving for modularity optimization.

Reference: Hamann et al., Euro-Par 2018, arXiv:1710.09605

Louvain moves nodes sequentially, which creates data dependencies between
moves. DSLM fixes this by splitting each round into sub-rounds: every node
is assigned to one sub-round via a hash, and all nodes in that sub-round
move simultaneously using a frozen snapshot of the clustering. Within each
sub-round there are two steps -- bidding (collect neighbor cluster info) and
compare (pick the best move) -- then all moves are committed at once.

Paper settings: 4 sub-rounds, max 8 rounds per local-moving phase.
"""

import datetime
from collections import defaultdict

from quality import cluster_volumes, delta_modularity


def _ts():
    return datetime.datetime.now().strftime("%H:%M:%S")


def node_subround(node_id, round_num, seed, n_subrounds):
    """Hash a node to a sub-round index. Fast integer mixing, no crypto needed."""
    h = node_id ^ (round_num * 2246822519) ^ (seed * 2654435761)
    h = ((h >> 16) ^ h) * 0x45D9F3B
    h = ((h >> 16) ^ h) & 0xFFFFFFFF
    return h % n_subrounds


def compute_bids(v, graph, clustering, degrees, cluster_vol):
    """Collect the info needed to evaluate delta-Q for each cluster v touches.

    Returns bids[C] = (vol_C, w_v_C).
    For v's current cluster A: vol_C = vol(A) - deg(v), w_v_C = w(v, A\v).
    For a neighbor cluster C: vol_C = vol(C), w_v_C = w(v, C).
    """
    A = clustering[v]

    # Accumulate edge weights from v to each cluster it touches.
    # Skip self-loops: they represent contracted intra-cluster mass, not real edges to neighbours.
    w_to_cluster = defaultdict(float)
    for u, w in graph[v].items():
        if u != v:
            w_to_cluster[clustering[u]] += w

    bids = {}

    w_v_A = w_to_cluster.get(A, 0.0)
    bids[A] = (cluster_vol[A] - degrees[v], w_v_A)  # removal cost for current cluster

    for C, w_v_C in w_to_cluster.items():
        if C != A:
            bids[C] = (cluster_vol[C], w_v_C)

    return bids


def best_move(v, bids, current_cluster, deg_v, total_vol):
    """Pick the best cluster for v; return current_cluster if no strict gain."""
    A = current_cluster
    vol_A_minus_v, w_v_A = bids[A]

    best_cluster = A
    best_gain = 0.0  # only move if gain is strictly positive

    for C, (vol_C, w_v_C) in bids.items():
        if C == A:
            continue
        gain = delta_modularity(
            w_v_candidate=w_v_C,
            vol_candidate=vol_C,
            w_v_current=w_v_A,
            vol_current_minus_v=vol_A_minus_v,
            deg_v=deg_v,
            total_vol=total_vol,
        )
        if gain > best_gain:
            best_gain = gain
            best_cluster = C

    return best_cluster


def local_moving(
    graph,
    clustering,
    degrees,
    total_vol,
    n_subrounds=4,
    max_rounds=8,
    seed=42,
    verbose=False,
):
    """Run one DSLM-Mod local-moving phase. Modifies clustering in place.

    Returns (clustering, rounds_done, any_change).
    """
    nodes = list(graph.keys())
    any_change = False

    for round_num in range(max_rounds):
        round_changed = False

        # Assign every node to a sub-round once per round (not once per sub-round).
        subrounds = [[] for _ in range(n_subrounds)]
        for v in nodes:
            subrounds[node_subround(v, round_num, seed, n_subrounds)].append(v)

        # Track cluster volumes incrementally instead of recomputing each sub-round.
        cluster_vol = cluster_volumes(clustering, degrees)

        for sub in range(n_subrounds):
            active = subrounds[sub]
            if not active:
                continue

            # Bidding: all active nodes read the same frozen snapshot.
            all_bids = {
                v: compute_bids(v, graph, clustering, degrees, cluster_vol)
                for v in active
            }

            # Compare: each node independently picks its best move.
            moves = {
                v: best_move(v, all_bids[v], clustering[v], degrees[v], total_vol)
                for v in active
            }

            # Commit all moves at once.
            moves_made = 0
            for v, new_C in moves.items():
                old_C = clustering[v]
                if new_C != old_C:
                    deg_v = degrees[v]
                    cluster_vol[old_C] -= deg_v
                    cluster_vol[new_C] = cluster_vol.get(new_C, 0.0) + deg_v
                    clustering[v] = new_C
                    round_changed = True
                    any_change = True
                    moves_made += 1

            if verbose:
                n_clusters = len(set(clustering.values()))
                print(
                    f"  [{_ts()}] round {round_num + 1} | sub-round {sub} "
                    f"| moves: {moves_made} | clusters: {n_clusters}",
                    flush=True,
                )

        if verbose:
            status = "changes" if round_changed else "converged"
            print(f"  [{_ts()}] round {round_num + 1}: {status}", flush=True)

        if not round_changed:
            break

    return clustering, round_num + 1, any_change
