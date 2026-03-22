# Speaker Notes
CSC 502: Systems for Massive Datasets
Nitin Gupta | Spring 2026 | day1_group1

Target: 8 minutes. Rough pacing: ~50 seconds per slide, slightly longer on Algorithm Flow and Results.

---

## Slide 1: Title

"Hi, I am Nitin. My project is on distributed graph clustering, based on a paper from Euro-Par 2018 by researchers at KIT."

---

## Slide 2: The Paper

"The paper is called Distributed Graph Clustering using Modularity and Map Equation. The authors propose two algorithms for finding communities in very large graphs: graphs with hundreds of millions of nodes and billions of edges.

I picked this paper because the problem is squarely in the big-data space: the graph literally does not fit on one machine. And the algorithm maps cleanly onto a MapReduce data flow, which made it a good fit for this course and for a sequential simulation."

---

## Slide 3: The Problem

"The left side of this diagram captures the problem. Traditional algorithms like Louvain move one node at a time, in order. That is inherently sequential and cannot be distributed across machines.

The DSLM solution, in the middle, breaks that dependency with three steps: group nodes by a hash function, move all nodes in each group simultaneously, and then contract clusters into super-nodes and repeat. The result, on the right, is communities found at scale, up to 10 times faster than the previous best distributed method."

---

## Slide 4: What the Algorithm Looks Like

"This figure walks through the same idea on a small six-node example.

Start: every node is its own cluster. Then the hash splits them into three color-coded groups. Each group evaluates its neighbors and moves simultaneously, using a snapshot of the graph taken before any moves in that group. After all groups have moved, the two real communities have formed. Contraction then collapses each community into a single super-node and the algorithm recurses."

---

## Slide 5: Algorithm Flow: Local Moving Phase

"Here is the actual control flow. After initializing each node in its own cluster, the algorithm enters the local moving phase.

Each round starts by hashing every node into one of four sub-rounds. For each sub-round, cluster volumes are frozen as a snapshot. Active nodes then run the bidding step: scan all neighbors and collect the weight of edges going to each neighboring cluster. The compare step picks the best cluster by computing the delta-modularity for each candidate. All moves commit simultaneously using the frozen snapshot, so there is no coordination needed between machines.

If any node moved, start the next round. Up to 8 rounds run before moving on to contraction."

---

## Slide 6: Algorithm Flow: Contraction and Unpacking

"Once the local moving phase converges, each cluster collapses into a single super-node. Inter-cluster edges become edges between super-nodes with summed weights. Intra-cluster edges become self-loops, and this is important: without them the super-node degree drops and the algorithm falsely merges communities at the next level. I learned this the hard way during implementation.

The algorithm recurses on the much smaller super-graph. On LiveJournal, level zero alone shrank the graph from 4 million nodes down to 280 thousand. We went through 6 levels before the graph stopped getting smaller, at which point we walk back through all the stored mappings to recover the original node labels."

---

## Slide 7: How I Coded It

"I implemented DSLM-Mod in Python as a sequential simulation. The five modules mirror the distributed data flow from the paper: graph loading, quality computation, the local moving core, and the multi-level contraction runner.

Two optimizations were necessary to handle LiveJournal at all. Graph loading with pandas instead of row-by-row iteration brought load time from several minutes down to 52 seconds. And instead of recomputing cluster volumes from scratch after each sub-round, I maintain a running dict and update it as nodes move."

---

## Slide 8: Results vs. the Paper

"I ran on the full LiveJournal graph: 4 million nodes, 34.7 million edges.

The paper's DSLM-Mod gets modularity Q of 0.710. My Python simulation gets 0.753, which actually beats all their baselines including sequential Louvain. This is not because my implementation is better. It is because I run 8 rounds across 6 contraction levels, giving more optimization passes than the paper's benchmarks used. NetworkX Louvain also gets 0.746 on the same graph, which confirms the gap is about search depth, not the algorithm.

On running time: 1119 seconds on my laptop versus 31 seconds on a 32-host C++ cluster. That difference is exactly what you would expect and does not reflect algorithmic inefficiency."

---

## Slide 9: Conclusion

"To summarize: DSLM's key insight is the sub-round hash. By grouping nodes deterministically and moving each group from a frozen snapshot, you break the sequential dependency in Louvain without any coordination between machines. The paper shows this scales to graphs with 100 million nodes where the previous best distributed method either crashes or is 10 times slower.

The implementation confirmed the algorithm is correct. The one thing that caught me was self-loops during contraction. Dropping them silently collapses all clusters into one at the next level, because the super-node volumes go to near zero. Once you understand why it happens it makes sense, but it is not obvious from reading the paper.

Thank you."

---

## Timing Check

| Slide | Target |
|---|---|
| Title | 20 sec |
| The Paper | 50 sec |
| The Problem | 50 sec |
| What the Algorithm Looks Like | 60 sec |
| Local Moving Phase | 90 sec |
| Contraction and Unpacking | 90 sec |
| How I Coded It | 60 sec |
| Results | 75 sec |
| Conclusion | 60 sec |
| **Total** | **~8 min** |
