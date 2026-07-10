"""Unit tests for Knowledge Graph and OKF parser components — OKF parser, resolver, and Leiden partitions."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from src.knowledge_graph.resolver import EntityResolver
from src.knowledge_graph.community import CommunityDetector
from src.knowledge_graph.extractor import GraphExtractor
from src.okf.parser import OKFParser
from src.okf.builder import OKFBundleBuilder
from src.okf.versioning import OKFVersioner


def test_entity_resolver_normalization() -> None:
    """Validate name suffixes stripping and capital normalization."""
    resolver = EntityResolver()
    val = resolver.normalize_name("Google Inc.")
    print("VAL TYPE:", type(val), "VAL REPR:", repr(val))
    print("EXPECTED TYPE:", type("Google"), "EXPECTED REPR:", repr("Google"))
    assert val == "Google"
    assert resolver.normalize_name("Apple LLC") == "Apple"
    assert resolver.normalize_name("Microsoft Corporation") == "Microsoft Corporation"



def test_entity_resolver_mapping() -> None:
    """Validate list consolidation maps original values to resolved canonical representations."""
    resolver = EntityResolver()
    raw_entities = ["Google Inc.", "Google LLC", "Apple Corp.", "Apple LLC"]

    resolved = resolver.resolve_entities(raw_entities)
    # Both Google Inc. and Google LLC map to the first encountered canonical one: "Google Inc."
    assert resolved["Google Inc."] == "Google Inc."
    assert resolved["Google LLC"] == "Google Inc."
    assert resolved["Apple Corp."] == "Apple Corp."
    assert resolved["Apple LLC"] == "Apple Corp."


def test_community_detector_leiden() -> None:
    """Validate Leiden community detection splits graph elements."""
    detector = CommunityDetector()
    nodes = ["NodeA", "NodeB", "NodeC", "NodeD"]
    # Edges: A-B (conf 0.9), C-D (conf 0.8). No connection between A/B and C/D.
    edges = [
        ("NodeA", "NodeB", 0.9),
        ("NodeC", "NodeD", 0.8),
    ]

    communities = detector.detect_communities(nodes, edges)
    # Should partition into two distinct communities
    assert len(communities) == 2
    # Check that A and B are in the same community, C and D in the same
    comm_map = {}
    for cluster_idx, cluster in enumerate(communities):
        for node in cluster:
            comm_map[node] = cluster_idx

    assert comm_map["NodeA"] == comm_map["NodeB"]
    assert comm_map["NodeC"] == comm_map["NodeD"]
    assert comm_map["NodeA"] != comm_map["NodeC"]


@pytest.mark.asyncio
async def test_graph_extractor_fallback() -> None:
    """Validate heuristic entity extraction when API key is missing."""
    extractor = GraphExtractor(api_key=None)
    text = "The policy of Google and Microsoft is to enable security."

    result = await extractor.extract_graph(text, source_name="test_doc")
    # Rule-based fallback should extract capitalized words: "Google", "Microsoft"
    node_names = [n["name"] for n in result["nodes"]]
    assert "Google" in node_names
    assert "Microsoft" in node_names
    # Relationships should be created linking them
    assert len(result["relationships"]) > 0
    assert result["relationships"][0]["type"] == "RELATED_TO"


def test_okf_parser_header_body() -> None:
    """Validate YAML frontmatter extraction and content split."""
    raw_md = (
        "---\n"
        "title: Security Policy\n"
        "doc_type: policy\n"
        "tags: [security, compliance]\n"
        "lineage:\n"
        "  source: internal_drive\n"
        "---\n"
        "This is the actual policy description body."
    )

    metadata, body = OKFParser.parse_text(raw_md)
    assert metadata["title"] == "Security Policy"
    assert metadata["doc_type"] == "policy"
    assert "compliance" in metadata["tags"]
    assert body == "This is the actual policy description body."


def test_okf_bundle_builder() -> None:
    """Validate that bundle builder correctly schema checks frontmatter and hashes content."""
    raw_md = (
        "---\n"
        "title: Database Procedure\n"
        "doc_type: procedure\n"
        "tags: [db, migration]\n"
        "lineage:\n"
        "  source: internal_db\n"
        "---\n"
        "This is the backup procedure instruction text."
    )

    bundle = OKFBundleBuilder.build_from_text(raw_md)
    assert bundle.metadata.title == "Database Procedure"
    assert bundle.metadata.doc_type == "procedure"
    assert "db" in bundle.metadata.tags
    assert bundle.content == "This is the backup procedure instruction text."

    # Validate SHA-256 hash
    expected_hash = OKFVersioner.compute_sha256(bundle.content)
    assert bundle.sha256_hash == expected_hash
