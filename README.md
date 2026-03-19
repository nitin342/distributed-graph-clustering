# Distributed Graph Clustering: DSLM-Mod

CSC 502 Big Data project -- University of Victoria, 2026.

Sequential Python simulation of the DSLM-Mod algorithm from:

> Hamann, Strasser, Wagner, Zeitz. "Distributed Graph Clustering using Modularity and Map Equation." Euro-Par 2018. https://arxiv.org/abs/1710.09605

## What this is

DSLM (Distributed Synchronous Local Moving) is a graph clustering algorithm designed to run on MapReduce-style distributed systems. It partitions graph nodes into communities that are internally dense and externally sparse, optimizing a quality measure called modularity.

The key idea is a sub-round structure: instead of moving nodes one at a time (like Louvain), DSLM assigns nodes to sub-rounds via a hash function and moves all nodes in a sub-round simultaneously based on a frozen snapshot of the clustering. This eliminates sequential data dependencies and allows parallel execution.

This implementation is a sequential simulation in Python that preserves the structural logic of the distributed algorithm, including the bidding/compare steps and multi-level graph contraction.

## Results

Evaluated on the LiveJournal social network (3.99M nodes, 34.7M edges):

| Method | Q | Time |
|---|---|---|
| Louvain (paper, C++, 8 hosts) | 0.713 | 99s |
| DSLM-Mod (paper, C++, 8 hosts) | 0.710 | 31s |
| Our DSLM-Mod (Python, 1 laptop) | **0.753** | 1119s |

Our simulation exceeds the paper's baselines because it runs 8 rounds over 6 contraction levels, giving more optimization passes than the paper's single-machine Louvain baseline.

## Setup

```bash
cd src/
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
```

## Usage

```bash
# Built-in 12-node toy graph (3 communities)
python main.py

# Run on an edge list file
python main.py --input ../data/graph.txt

# Save clustering to file
python main.py --input ../data/graph.txt --output ../results/clustering.txt

# One-level only (no contraction)
python main.py --no-contraction

# Verbose output (per-round progress)
python main.py --verbose
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--input` | (toy graph) | Edge list file (tab/space separated, `#` for comments) |
| `--output` | (none) | Write clustering to file (node TAB cluster) |
| `--subrounds` | 4 | Sub-rounds per round |
| `--max-rounds` | 8 | Max rounds per local-moving phase |
| `--seed` | 42 | Hash seed for sub-round assignment |
| `--no-contraction` | off | Skip contraction (one-level DSLM-Mod w/o Cont.) |
| `--verbose` | off | Print per-round progress |

## Input Format

Plain edge list, one edge per line:

```
# comment lines are skipped
0  1
0  2
1  2
```

Parallel edges are summed. Self-loops are ignored.

## How It Works

### The Files and What They Do

**`graph.py` -- Loading and Basic Math**
Reads an edge list file and turns it into a Python dictionary. Also computes the degree of each node and the total volume (sum of all degrees = twice the total edge weight).

**`quality.py` -- Measuring How Good a Clustering Is**
Contains two things:
- `modularity()` -- given a clustering, scores it. Higher is better. It rewards clusters that have many internal edges and few external ones.
- `delta_modularity()` -- answers "if I move this one node to a different cluster, how much does the score change?" This is the core math used to decide whether to move a node.

**`dslm.py` -- The Heart of the Algorithm**
Three parts:
1. `node_subround()` -- uses a hash function to assign each node a sub-round number (0-3). Deterministic: given the same node, round, and seed, you always get the same sub-round.
2. `compute_bids()` -- for a given node, looks at all its neighbors and figures out which clusters are nearby and how strongly connected the node is to each one.
3. `local_moving()` -- the main loop. Runs up to 8 rounds, each with 4 sub-rounds. In each sub-round: active nodes compute bids simultaneously from a snapshot, independently pick their best cluster, then all moves commit at once.

**`contract.py` -- Shrinking the Graph Between Levels**
After local moving converges, every cluster becomes a single super-node. Edges between clusters become edges between super-nodes; edges within a cluster become a self-loop on the super-node (this preserves the cluster's volume so the algorithm does not get confused at the next level). Runs local moving again on the smaller graph, repeats until nothing changes, then unpacks super-node assignments back to the original nodes.

**`main.py` -- Putting It All Together**
Command-line program with a built-in 12-node toy graph (3 communities of 4 nodes each, 3 bridge edges). Pass your own edge list with `--input`.

### How a Full Run Looks (Toy Graph)

```
Level 0: 12 nodes
  sub-round 0: some nodes move to their neighbours' clusters
  sub-round 1: more nodes consolidate
  round 2: nothing changes, stop
  → 3 clusters: {0,1,2,3}, {4,5,6,7}, {8,9,10,11}

Level 1: contract to 3 super-nodes
  round 1: nothing changes (already optimal)
  → done

Final: 3 clusters, Q = 0.524
```

### One Important Design Detail

When contracting the graph, intra-cluster edges must be kept as self-loops on the super-node. Without them, a super-node's degree only reflects its bridge edges, so the algorithm thinks the super-nodes are barely connected to anything and merges them all into one cluster (Q = 0). With self-loops, the super-node's degree correctly equals the total volume of the original cluster.

## Files

| File | Description |
|---|---|
| `src/graph.py` | Graph loading, degree computation, utilities |
| `src/quality.py` | Modularity score and delta-modularity |
| `src/dslm.py` | Bidding step, compare step, local moving loop |
| `src/contract.py` | Graph contraction and multi-level runner |
| `src/main.py` | CLI entry point and toy graph definition |
| `requirements.txt` | Python dependencies |
