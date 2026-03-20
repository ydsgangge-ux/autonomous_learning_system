"""
因果缺口检测器 (Causal Gap Detector)
======================================

集成到探索系统，检测知识体系中的因果逻辑断层。

功能：
1. 寻找孤立的逻辑簇
2. 检测未验证的因果链
3. 生成桥接任务
"""

from typing import Dict, List, Optional
import asyncio

from core.causality import CausalReasoningEngine, get_causal_engine
from core.utils import get_logger

logger = get_logger(__name__)


class CausalGapDetector:
    """
    因果缺口检测器
    
    检测知识体系中的逻辑断层：
    - 孤立的逻辑簇（没有因果桥接）
    - 未验证的因果链（需要实验确认）
    - 冲突的因果关系
    """

    def __init__(self):
        self.causal_engine = get_causal_engine()

    async def detect_gaps(
        self, 
        domain: Optional[str] = None,
        min_cluster_size: int = 2
    ) -> Dict[str, Any]:
        """
        检测因果缺口
        
        Args:
            domain: 限定领域（可选）
            min_cluster_size: 最小簇大小
            
        Returns:
            检测结果
        """
        gaps = []
        
        # 1. 检测孤立的逻辑簇
        isolated_clusters = self._find_isolated_clusters(min_cluster_size)
        for cluster in isolated_clusters:
            gaps.append({
                "type": "ISOLATED_CLUSTER",
                "severity": "medium",
                "description": f"发现孤立的逻辑簇: {', '.join(cluster)}",
                "suggestion": "探索这些概念与其他知识之间的潜在联系",
                "cluster": cluster
            })
        
        # 2. 检测弱因果链（需要更多证据）
        weak_links = self._find_weak_causal_links()
        for link in weak_links:
            gaps.append({
                "type": "WEAK_CAUSALITY",
                "severity": "low",
                "description": f"因果链强度较弱: {link['cause']} -> {link['effect']}",
                "suggestion": "需要更多证据验证因果关系",
                "link": link
            })
        
        # 3. 检测冲突
        conflicts = self.causal_engine.detect_conflicts()
        for conflict in conflicts:
            gaps.append({
                "type": "CAUSAL_CONFLICT",
                "severity": conflict.get("severity", "high"),
                "description": conflict.get("message", ""),
                "suggestion": "需要人工介入或实验验证",
                "conflict": conflict
            })
        
        # 4. 检测未完成的因果链（有头无尾或有尾无头）
        incomplete = self._find_incomplete_chains()
        for item in incomplete:
            gaps.append({
                "type": "INCOMPLETE_CHAIN",
                "severity": "low",
                "description": item["description"],
                "suggestion": item["suggestion"],
                "node": item["node"]
            })
        
        return {
            "total_gaps": len(gaps),
            "high_priority": sum(1 for g in gaps if g["severity"] == "high"),
            "medium_priority": sum(1 for g in gaps if g["severity"] == "medium"),
            "low_priority": sum(1 for g in gaps if g["severity"] == "low"),
            "gaps": gaps
        }

    def _find_isolated_clusters(self, min_size: int) -> List[List[str]]:
        """寻找孤立的逻辑簇"""
        import networkx as nx
        
        if self.causal_engine.dag.number_of_nodes() == 0:
            return []
        
        # 找弱连通分量
        components = list(nx.weakly_connected_components(self.causal_engine.dag))
        
        # 过滤出足够大的孤立簇
        isolated = [
            [self.causal_engine.dag.nodes[n].get("name", n) for n in comp]
            for comp in components
            if len(comp) >= min_size
        ]
        
        return isolated

    def _find_weak_causal_links(self) -> List[Dict]:
        """寻找弱因果链"""
        weak = []
        
        for u, v, data in self.causal_engine.dag.edges(data=True):
            strength = data.get("strength", 0)
            if strength < 0.5:
                weak.append({
                    "cause": self.causal_engine.dag.nodes[u].get("name", u),
                    "effect": self.causal_engine.dag.nodes[v].get("name", v),
                    "strength": strength,
                    "mechanism": data.get("mechanism", "")
                })
        
        return weak[:10]  # 返回前10个

    def _find_incomplete_chains(self) -> List[Dict]:
        """寻找不完整的因果链"""
        incomplete = []
        
        # 找只有出边没有入边的节点（有头无尾）
        for node in self.causal_engine.dag.nodes():
            in_degree = self.causal_engine.dag.in_degree(node)
            out_degree = self.causal_engine.dag.out_degree(node)
            
            name = self.causal_engine.dag.nodes[node].get("name", node)
            
            if out_degree > 0 and in_degree == 0:
                incomplete.append({
                    "node": name,
                    "description": f"'{name}' 是起始节点但没有前因",
                    "suggestion": "探索是什么导致了这个问题"
                })
            elif in_degree > 0 and out_degree == 0:
                incomplete.append({
                    "node": name,
                    "description": f"'{name}' 是终端节点但没有后果",
                    "suggestion": "探索这个问题会导致什么结果"
                })
        
        return incomplete[:10]

    async def generate_bridge_task(
        self, 
        gap: Dict
    ) -> Dict:
        """
        根据缺口生成桥接任务
        
        Args:
            gap: 检测到的缺口
            
        Returns:
            可执行的任务
        """
        gap_type = gap.get("type", "")
        
        if gap_type == "ISOLATED_CLUSTER":
            cluster = gap.get("cluster", [])
            if len(cluster) >= 2:
                return {
                    "task_type": "CAUSAL_BRIDGE",
                    "title": f"探索因果连接: {cluster[0]} 与 {cluster[1]}",
                    "description": f"分析 '{cluster[0]}' 和 '{cluster[1]}' 之间是否存在因果关系",
                    "prompt": f"请研究以下两个概念之间的潜在因果关系：{cluster[0]} 和 {cluster[1]}。\n\n"
                                f"请分析：\n"
                                f"1. 它们之间是否存在因果关系？\n"
                                f"2. 如果存在，作用机制是什么？\n"
                                f"3. 因果强度如何？\n\n"
                                f"请给出详细的分析报告。",
                    "priority": "high"
                }
        
        elif gap_type == "WEAK_CAUSALITY":
            link = gap.get("link", {})
            return {
                "task_type": "CAUSAL_VERIFY",
                "title": f"验证因果关系: {link.get('cause', '')} -> {link.get('effect', '')}",
                "description": f"验证弱因果链 '{link.get('cause', '')}' -> '{link.get('effect', '')}'",
                "prompt": f"请验证以下因果关系的有效性：\n\n"
                            f"起因：{link.get('cause', '')}\n"
                            f"结果：{link.get('effect', '')}\n"
                            f"已知机制：{link.get('mechanism', '')}\n\n"
                            f"请提供：\n"
                            f"1. 更多支持或反驳的证据\n"
                            f"2. 更精确的作用机制描述\n"
                            f"3. 因果强度的重新评估",
                "priority": "medium"
            }
        
        elif gap_type == "CAUSAL_CONFLICT":
            conflict = gap.get("conflict", {})
            return {
                "task_type": "CONFLICT_RESOLUTION",
                "title": f"解决因果冲突",
                "description": conflict.get("message", ""),
                "prompt": f"检测到因果逻辑冲突：\n\n{conflict.get('message', '')}\n\n"
                            f"请分析并解决这个冲突：\n"
                            f"1. 哪个因果关系更可能是正确的？\n"
                            f"2. 是否存在其他因素导致了这个矛盾？\n"
                            f"3. 需要什么条件或实验来验证？",
                "priority": "high"
            }
        
        return {
            "task_type": "GENERAL_EXPLORATION",
            "title": "探索因果关系",
            "description": gap.get("description", ""),
            "prompt": gap.get("suggestion", ""),
            "priority": "low"
        }


# ===== 便捷函数 =====

def get_gap_detector() -> CausalGapDetector:
    """获取缺口检测器实例"""
    return CausalGapDetector()
