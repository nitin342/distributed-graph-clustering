# Paper Summary: Distributed Graph Clustering using Modularity and Map Equation

**Authors:** Michael Hamann, Ben Strasser, Dorothea Wagner, Tim Zeitz
**Affiliation:** Karlsruhe Institute of Technology (KIT), Germany
**Venue:** Euro-Par 2018
**arXiv:** https://arxiv.org/abs/1710.09605
**Code:** https://github.com/kit-algo/distributed_clustering_thrill

---

## Problem

Given a very large undirected weighted graph G = (V, E, ω) that doesn't fit in the memory of a single machine, partition nodes V into disjoint clusters that are **internally dense and externally sparse** — the classic community detection problem at massive scale.

Challenges:
- Sequential and shared-memory parallel algorithms fail on graphs too large for one machine
- Existing distributed approaches (e.g., GossipMap) are slow, memory-hungry, and produce poor-quality results
- The Louvain/Infomap local-moving phase has sequential data dependencies that resist direct parallelization

---

## Quality Measures

### Modularity (higher is better)
$$Q(\mathcal{C}) = \sum_{C} \frac{\text{vol}(C) - \text{cut}(C)}{\text{vol}(V)} - \sum_{C} \frac{\text{vol}(C)^2}{\text{vol}(V)^2}$$

### Map Equation (lower is better)
$$L(\mathcal{C}) = \text{plogp}\!\left(\sum_{C} \frac{\text{cut}(C)}{\text{vol}(V)}\right) - 2\sum_{C}\text{plogp}\!\left(\frac{\text{cut}(C)}{\text{vol}(V)}\right) + \sum_{C}\text{plogp}\!\left(\frac{\text{cut}(C)+\text{vol}(C)}{\text{vol}(V)}\right) - \text{const}$$

where `plogp(x) = x log x`.

---

## Key Contribution: DSLM (Distributed Synchronous Local Moving)

Two algorithms — **DSLM-Mod** (modularity) and **DSLM-Map** (map equation) — built on the **Thrill** distributed C++ MapReduce framework, using Distributed Immutable Arrays (DIAs).

### Overall Algorithm (same structure as Louvain/Infomap)

1. Initialize: every node in its own singleton cluster
2. **Local Moving Phase (DSLM):** move nodes to better-quality neighboring clusters
3. **Contraction Phase:** merge nodes of each cluster into one super-node
4. Recurse on contracted graph
5. Unpack cluster assignments back to original nodes
6. Terminate when no moves occur

### Data Representation (two DIAs sorted by node ID)

- **Graph DIA:** `(v, [neighbors u_i], [weights w_i])`
- **Clustering DIA:** `(v, cluster_C)`

### Sub-round Parallelization (core innovation)

Each local moving round is split into **4 sub-rounds**. Nodes are assigned to sub-rounds via a global hash function `h(node_id, round, seed)`. Within each sub-round, all assigned nodes move **simultaneously and in parallel** — eliminating sequential dependencies.

#### Bidding Step (per sub-round):
1. Zip clustering + graph DIAs
2. Aggregate by cluster C → each cluster has all its nodes + their neighborhoods
3. FlatMap: for each active node v (in or adjacent to cluster C), emit a bid:
   `(C, v, vol(C\v), cut(v, C\v), cut(C\v))`
   These three values are sufficient to compute quality gain ΔQ or ΔL.

#### Compare Step (per sub-round):
1. Aggregate bids by node v → all bids for each active node collected
2. Zip with graph DIA to get node degree
3. For each active node, pick cluster C* that maximizes ΔQ (or minimizes ΔL)
4. Output updated clustering DIA

### Distributed Contraction

1. Aggregate by cluster C; relabel cluster IDs as consecutive integers
2. Build new clustering DIA; store intermediate `(C, [v_i])` for later unpacking
3. Build contracted graph DIA: emit edges between clusters, aggregate to merge multi-edges

### Unpacking

Zip contracted clustering `(v, C_v)` with stored `(v, [v_i])` → flatmap assigns cluster back to all original nodes.

---

## Experiments

### Hardware
- 32 compute hosts, each: 2× Intel Xeon E5-2660 v4 (14-core, 2 GHz), 128 GiB RAM, 480 GiB SSD
- InfiniBand 4X FDR interconnect, 16 threads per host

### Datasets

| Graph | Nodes | Edges | Type |
|---|---|---|---|
| com-LiveJournal | 4M | 34M | social (SNAP) |
| com-Orkut | 3M | 117M | social (SNAP) |
| com-Friendster | 66M | 1806M | social (SNAP) |
| uk-2002 | 18M | 261M | web (DIMACS) |
| uk-2007-05 | 105M | 3302M | web (DIMACS) |
| LFR synthetic | 16M–512M | up to 68B | benchmark |

### Baselines

| Algorithm | Type | Measure |
|---|---|---|
| Louvain | Sequential | Modularity |
| PLM | Shared-memory parallel | Modularity |
| Infomap | Sequential | Map equation |
| RelaxMap | Shared-memory parallel | Map equation (directed) |
| GossipMap | Distributed (GraphLab) | Map equation (directed) |

### Key Results

- **Weak scaling (LFR):** GossipMap crashes (OOM) on all large instances. DSLM-Mod w/o Cont. achieves near-perfect weak scaling. Full DSLM scales well in practice.
- **Quality (LFR):** DSLM-Map achieves ARI ≈ 1.0 on all sizes. Full DSLM-Mod degrades on larger graphs due to modularity's resolution limit.
- **Running time (real-world):** DSLM-Map is 5–20× faster than RelaxMap and ~10× faster than GossipMap.
- **Largest graph tested:** uk-2007-05 (105M nodes, 3.3B edges) — GossipMap took 4211s; DSLM-Map took 214s.

---

## Limitations

1. All edges incident to nodes in one cluster must fit in memory of a single host (not an issue in practice for typical graphs)
2. Full DSLM-Mod suffers from modularity's resolution limit on large LFR graphs
3. DSLM-Map is ~2× slower than DSLM-Mod (can't apply pairwise reduction optimization)
4. Directed map equation (used by GossipMap/RelaxMap) vs. undirected (used here) makes quality comparison slightly nuanced

---

## Implementation Parameters

| Parameter | Value |
|---|---|
| Sub-rounds per round | 4 |
| Max rounds per local moving phase | 8 |
| Threads per host | 16 |
| Thrill block size | 128 KiB |

---

## Relevance to CSC 502

This paper is an ideal fit for a big data course project:
- Clearly defined **big data problem** (graph too large for one machine)
- Uses a well-known **MapReduce-style distributed framework** (Thrill)
- Two well-understood **quality measures** (modularity, map equation) with clean math
- **Implementation-friendly**: the DSLM algorithm is modular and the paper describes data flow step-by-step
- **Extensible**: code + evaluation scripts publicly available
- Strong **experimental evaluation** on real and synthetic datasets to replicate
