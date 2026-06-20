"""
Knowledge Graph skeleton (NetworkX).
Not used until 200+ alphas are accumulated — placeholder for future expansion.
"""
from __future__ import annotations


class KnowledgeGraph:
    """Minimal graph: nodes = concepts/fields/operators, edges = co-occurrence in alpha."""

    def __init__(self):
        try:
            import networkx as nx
            self._g = nx.DiGraph()
        except ImportError:
            self._g = None

    def add_alpha_edges(self, alpha_id: str, fields: list[str], operators: list[str]) -> None:
        if self._g is None:
            return
        for f in fields:
            self._g.add_node(f, type="field")
        for op in operators:
            self._g.add_node(op, type="operator")
        for f in fields:
            for op in operators:
                if self._g.has_edge(f, op):
                    self._g[f][op]["weight"] += 1
                else:
                    self._g.add_edge(f, op, weight=1, alpha_id=alpha_id)

    def neighbors(self, node: str) -> list[str]:
        if self._g is None or node not in self._g:
            return []
        return list(self._g.neighbors(node))

    def stats(self) -> dict:
        if self._g is None:
            return {"error": "networkx not installed"}
        return {"nodes": self._g.number_of_nodes(), "edges": self._g.number_of_edges()}
