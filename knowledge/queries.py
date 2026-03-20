from knowledge.graph_builder import knowledge_graph
from typing import List, Dict

def get_related_concepts(node_id: int, depth: int = 2) -> List[Dict]:
    """Retrieve related concepts from the graph."""
    return knowledge_graph.query_related(node_id, depth)
