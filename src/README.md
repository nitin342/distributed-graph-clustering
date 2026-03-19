# DSLM-Mod: Distributed Synchronous Local Moving (Modularity)

Python implementation of the DSLM-Mod algorithm from:

> Hamann, Strasser, Wagner, Zeitz. "Distributed Graph Clustering using Modularity and Map Equation." Euro-Par 2018. https://arxiv.org/abs/1710.09605

This is a sequential simulation that faithfully mirrors the paper's MapReduce data flow (bidding step, compare step, contraction) without requiring an actual distributed system.

---

## Setup

```bash
cd src/
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
```

---

## Usage

```bash
# Run on the built-in toy graph (12 nodes, 3 communities)
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

| Flag               | Default     | Description                                            |
| ------------------ | ----------- | ------------------------------------------------------ |
| `--input`          | (toy graph) | Edge list file (tab/space separated, `#` for comments) |
| `--output`         | (none)      | Write clustering to file (node TAB cluster)            |
| `--subrounds`      | 4           | Sub-rounds per round                                   |
| `--max-rounds`     | 8           | Max rounds per local-moving phase                      |
| `--seed`           | 42          | Hash seed for sub-round assignment                     |
| `--no-contraction` | off         | Skip contraction (one-level DSLM-Mod w/o Cont.)        |
| `--verbose`        | off         | Print per-round progress                               |

---

## Input Format

Plain edge list, one edge per line:

```
# comment lines are skipped
0  1
0  2
1  2  2.5   # optional weight
```

Parallel edges are summed. Self-loops are ignored.

---

## How It Works

### The Files and What They Do

**`graph.py` — Loading and Basic Math**
Reads an edge list file (just a text file with two node IDs per line) and turns it into a Python dictionary. Also computes the degree of each node (how many edge-weights connect to it) and the total volume (sum of all degrees = twice the total edge weight).

**`quality.py` — Measuring How Good a Clustering Is**
Contains two things:

- `modularity()` — given a clustering, scores it. Higher is better. It rewards clusters that have many internal edges and few external ones.
- `delta_modularity()` — answers the question: "if I move this one node to a different cluster, how much does the score change?" This is the core math used to decide whether to move a node.

**`dslm.py` — The Heart of the Algorithm**
Three parts:

1. `node_subround()` — uses a hash function to assign each node a sub-round number (0, 1, 2, or 3). Deterministic: given the same node, round, and seed, you always get the same sub-round. This is how the paper avoids coordination between machines.
2. `compute_bids()` — for a given node, looks at all its neighbors and figures out which clusters are nearby and how strongly connected the node is to each one. Packages this as "bids", one per candidate cluster.
3. `local_moving()` — the main loop. Runs up to 8 rounds. Each round has 4 sub-rounds. In each sub-round: figure out which nodes are active (via the hash), all active nodes compute their bids simultaneously using a snapshot of the current state, all active nodes independently pick their best cluster, all moves happen at once. Repeat until nothing changes.

**`contract.py` — Shrinking the Graph Between Levels**
After local moving converges, we "zoom out": every cluster becomes a single super-node, edges between clusters become edges between super-nodes, and edges within a cluster become a self-loop on the super-node (important — this preserves the cluster's weight so the algorithm does not get confused at the next level). Then we run local moving again on the smaller graph. This repeats until nothing changes. At the end, we unpack the super-node assignments back to the original nodes.

**`main.py` — Putting It All Together**
A command-line program. Has a built-in toy graph (12 nodes, 3 obvious communities of 4 nodes each, with 3 bridge edges between them). You can also pass your own edge list file. Prints the number of clusters found, modularity score, and time taken.

### How a Full Run Looks (Toy Graph)

```
Level 0: 12 nodes
  sub-round 1: some nodes move to their neighbours' clusters
  sub-round 2: more nodes consolidate
  sub-round 3: nothing changes, stop
  → 3 clusters found: {0,1,2,3}, {4,5,6,7}, {8,9,10,11}

Level 1: contract to 3 super-nodes
  sub-round 1: nothing changes (clusters are already optimal)
  → done

Final: 3 clusters, modularity 0.524
```

### One Important Design Detail

When we contract the graph, we must keep internal edges as self-loops on the super-node. Without them, a super-node's degree looks tiny (only its bridge edges), so the algorithm thinks "these super-nodes are barely connected to anything, let's just merge them all" — collapsing everything into one cluster with modularity 0. With self-loops, the super-node's degree correctly reflects the total volume of the original cluster.

---

## File Overview

| File          | Description                                                  |
| ------------- | ------------------------------------------------------------ |
| `graph.py`    | Graph loading, degree computation, utilities                 |
| `quality.py`  | Modularity score and delta-modularity                        |
| `dslm.py`     | DSLM local-moving phase (bidding + compare + sub-round hash) |
| `contract.py` | Graph contraction and multi-level runner                     |
| `main.py`     | CLI entry point and toy graph definition                     |
