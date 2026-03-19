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

## Quick start

```bash
# Built-in 12-node toy graph (3 communities)
python main.py

# Run on a SNAP edge list
python main.py --input ../data/com-lj.ungraph.txt --verbose

# One level only (no contraction)
python main.py --input ../data/com-lj.ungraph.txt --no-contraction
```

See `src/README.md` for full usage and implementation details.

## Files

```
src/
  graph.py      graph loading, degree computation
  quality.py    modularity score and delta-modularity
  dslm.py       bidding step, compare step, local moving loop
  contract.py   graph contraction and multi-level runner
  main.py       CLI entry point

paper_summary.md          summary of the paper
project_plan.md           project phases and report outline
requirements.txt          Python dependencies
```
