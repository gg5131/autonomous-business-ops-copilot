"""Leiden community detection algorithm runner using igraph and leidenalg."""

from __future__ import annotations

from typing import Any, Dict, List

import igraph as ig
import leidenalg as la

from src.observability.logging import get_logger

logger = get_logger(__name__)


class CommunityDetector:
    """Partitions graph nodes into cohesive communities using the Leiden algorithm."""

    @staticmethod
    def detect_communities(
        nodes: List[str],
        edges: List[tuple[str, str, float]],
        resolution: float = 1.0,
    ) -> List[List[str]]:
        """Executes Leiden community detection on the nodes/relationships, returning clusters."""
        if not nodes:
            return []

        logger.info(
            "Detecting communities using Leiden",
            node_count=len(nodes),
            edge_count=len(edges),
        )

        # Create mapping of node name to integer index for igraph
        node_to_idx = {name: idx for idx, name in enumerate(nodes)}
        idx_to_node = {idx: name for idx, name in enumerate(nodes)}

        # Build igraph instance
        g = ig.Graph(directed=False)
        g.add_vertices(len(nodes))

        # Add edges and track weights based on relationship confidence
        igraph_edges = []
        weights = []
        for src, dst, confidence in edges:
            if src in node_to_idx and dst in node_to_idx:
                igraph_edges.append((node_to_idx[src], node_to_idx[dst]))
                # Use confidence score as edge weight
                weights.append(float(confidence))

        if igraph_edges:
            g.add_edges(igraph_edges)
            g.es["weight"] = weights

        try:
            partition = la.find_partition(
                g,
                la.RBConfigurationVertexPartition,
                weights=g.es["weight"] if igraph_edges else None,
                resolution_parameter=resolution,
            )


            # Map index clusters back to node names
            communities: List[List[str]] = []
            for cluster in partition:
                cluster_nodes = [idx_to_node[idx] for idx in cluster]
                communities.append(cluster_nodes)

            logger.info("Leiden partitioning completed", community_count=len(communities))
            return communities

        except Exception as e:
            logger.error("Leiden community detection execution failed", error=str(e))
            # Fallback: treat each node as its own community in case of error
            return [[node] for node in nodes]
