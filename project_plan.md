# CSC 502 Project Plan: Distributed Graph Clustering

## Context
Solo project based on "Distributed Graph Clustering using Modularity and Map Equation" (Hamann et al., Euro-Par 2018). The course requires at least one non-trivial phase. Phase 2 (implementation) is the non-trivial centerpiece, with Phase 1 (explanation) forming the bulk of the report and Phase 3 (experiments) providing validation.

---

## Deliverables
- Written report: 5-10 pages, IEEE double-column format
- In-class presentation

---

## Phase 1: Paper Explanation (report sections 1-3)

### 1.1 Problem Statement
- Define graph clustering: nodes, edges, clusters, internally dense / externally sparse
- Motivate with social networks (friend groups) and web graphs
- Explain why scale matters: graphs too large for one machine
- Briefly describe why sequential/shared-memory approaches fail

### 1.2 Quality Measures
- Modularity: formula, intuition, known limitation (resolution limit)
- Map equation: formula, information-theoretic intuition (random walk description length), plogp notation
- Side-by-side comparison of the two measures

### 1.3 Toy Graph Walkthrough
- Create a small graph (~10-12 nodes, 3 clear communities) by hand
- Show initial singleton clustering
- Walk through one full sub-round: hash assignment, bidding step, compare step, cluster update
- Show modularity delta computation for one node move
- This is the "small dataset" the course description asks for

---

## Phase 2: Implementation (non-trivial phase)

### Stack
- Python with NetworkX (graph ops), NumPy, and standard library
- Virtual environment via `venv` (`src/venv/`, gitignored)
- No actual distributed system needed: simulate the MapReduce steps with Python functions that mirror the DIA operations (map, flatmap, groupby, zip)

### Scope: DSLM-Mod only (modularity)
- Map equation implementation is ~2x harder and the paper itself notes DSLM-Mod is the cleaner algorithm
- DSLM-Map mentioned as future work in the report

### Components to implement
1. `graph.py` - load graph from edge list, compute degrees, volumes, cuts
2. `quality.py` - modularity score, delta-modularity for a node move
3. `dslm.py` - core algorithm:
   - Sub-round hash assignment: `h(node_id, round, seed) -> sub_round`
   - Bidding step: for each active node, emit bids `(cluster, node, vol_minus_v, cut_v_cluster, cut_cluster)`
   - Compare step: for each active node, pick best cluster by max delta-modularity
   - Full local moving loop (4 sub-rounds, max 8 rounds)
4. `contract.py` - contract graph after local moving, unpack cluster assignments
5. `main.py` - tie everything together, CLI entry point

### What to skip
- Implement one-level DSLM-Mod (no contraction) first, add contraction if time permits
- Distributed execution: simulate sequentially but keep the data flow structure faithful to the paper

---

## Phase 3: Experiments (report section 5)

### Datasets
- **com-LiveJournal** (4M nodes, 34M edges) from SNAP - manageable on a laptop
- **com-Orkut** (3M nodes, 117M edges) from SNAP - optional, heavier
- Toy graph from Phase 1 as a sanity check

### Baselines
- NetworkX / python-igraph built-in Louvain (greedy modularity) as sequential baseline

### Metrics
- Modularity score of output clustering
- Running time
- Compare against numbers reported in the paper (Table 1 and 2) as a reference point, not a direct benchmark (different hardware)

### What to report
- Modularity scores vs. baseline
- How clustering quality changes with number of sub-rounds (ablation: 1, 2, 4 sub-rounds)
- Optionally: how running time scales with graph size

---

## Report Outline (IEEE, 5-10 pages)

1. Introduction (0.5 pages) - problem motivation, paper overview
2. Background (1 page) - modularity, map equation, prior work (Louvain, GossipMap)
3. Algorithm (2 pages) - DSLM explained with toy walkthrough and figures
4. Implementation (1 page) - design choices, what was simplified and why
5. Experiments (1.5 pages) - datasets, results, comparison
6. Conclusion (0.5 pages) - summary, limitations, future work (DSLM-Map, full contraction)

---

## File Structure
```
csc502/
  paper_summary.md        # done
  project_description.md  # done
  project_plan.md         # this file
  CLAUDE.md
  report/
    main.tex              # IEEE LaTeX report
    figures/              # toy graph diagrams, result plots
  src/
    graph.py
    quality.py
    dslm.py
    contract.py
    main.py
  data/                   # downloaded SNAP datasets (gitignored)
  results/                # experiment output CSVs
```

---

## Order of Work
1. Toy graph + Phase 1 report writeup (builds intuition before coding)
2. Implement DSLM-Mod core (dslm.py + quality.py), validate on toy graph
3. Add graph loader and run on LiveJournal
4. Write report sections, add figures
5. Prepare presentation slides

---

## Verification
- Toy graph: manually verify modularity delta computations match hand calculations
- Implementation: run on toy graph, confirm clusters match visually obvious communities
- Sanity check: modularity score should be positive and higher than random assignment
- LiveJournal: compare modularity score to PLM/Louvain baseline from the paper (Table 2: PLM gets 0.713)
