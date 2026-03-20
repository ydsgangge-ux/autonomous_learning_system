import networkx as nx
from typing import List, Dict, Any
from db.models import KnowledgeNode
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    async def build_from_db(self, session: AsyncSession):
        """Build graph from database nodes."""
        result = await session.execute(select(KnowledgeNode))
        nodes = result.scalars().all()
        for node in nodes:
            self.graph.add_node(node.id, title=node.title, type=node.node_type, extra_data=node.extra_data)
        # TODO: Add edges based on relationships
        pass

    def query_related(self, node_id: int, depth: int = 1) -> List[Dict]:
        """Get related nodes within depth."""
        if node_id not in self.graph:
            return []
        nodes = set()
        for _ in range(depth):
            neighbors = set(self.graph.successors(node_id)) | set(self.graph.predecessors(node_id))
            nodes.update(neighbors)
        return [{"id": n, "data": self.graph.nodes[n]} for n in nodes]

# Global graph instance (can be rebuilt periodically)
knowledge_graph = KnowledgeGraph()


# 兼容函数
async def get_all_topics(session: AsyncSession = None) -> List[Dict]:
    """获取所有主题/节点"""
    # 返回图中的所有节点
    return [{"id": n, "data": data} for n, data in knowledge_graph.graph.nodes(data=True)]

def find_isolated_nodes() -> List[int]:
    """查找孤立节点（没有连接的节点）"""
    return [n for n in knowledge_graph.graph.nodes() if knowledge_graph.graph.degree(n) == 0]

def get_graph() -> KnowledgeGraph:
    """获取全局图实例"""
    return knowledge_graph
