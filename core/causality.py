"""
因果推理引擎 (Causal Reasoning Engine)
========================================

这是系统的"因果神经网络"，负责从知识中提取因果逻辑并进行推理。

核心功能：
1. 因果提取 - 从文本中识别因果链
2. 因果图谱管理 - 构建和维护因果 DAG
3. 反事实推理 - 预测干预的效果
4. 冲突检测 - 发现逻辑矛盾

设计原则：
- 只提取物理或逻辑上的必然联系，排除单纯相关性
- 记录作用机制（mechanism），强制深入底层原理
- 支持反事实推理（如果...会怎样）
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
from collections import defaultdict

import networkx as nx

from llm.client import llm_client
from core.utils import get_logger

logger = get_logger(__name__)


class CausalReasoningEngine:
    """
    因果推理引擎
    
    负责：
    1. 从文本中提取因果关系
    2. 构建和维护因果有向无环图 (DAG)
    3. 进行反事实推理
    4. 检测逻辑冲突
    """

    def __init__(self, client=None):
        self.client = client or llm_client
        # 内存中的因果图（定期持久化到数据库）
        self.dag = nx.DiGraph()
        self._node_cache: Dict[str, Dict] = {}  # node_id -> node_data
        
    # ==================== 因果提取 ====================

    async def extract_causality(
        self, 
        content: str, 
        context: str = "",
        source_type: str = "text"
    ) -> Dict[str, Any]:
        """
        利用 LLM 从摄入的内容中提取因果逻辑链
        
        Args:
            content: 待分析的文本内容
            context: 上下文信息
            source_type: 来源类型
            
        Returns:
            提取结果统计
        """
        prompt = f"""你是一个因果逻辑分析专家。

任务：从以下文本中提取因果逻辑链。

要求：
1. 只提取物理或逻辑上的必然联系（因果关系），排除单纯的相关性
2. 每个因果链包含：起因(cause)、作用机制(mechanism)、结果(effect)
3. 机制描述要具体，不能是空泛的套话
4. 评估因果强度(strength)：0-1分，1表示必然因果，0.5表示大概率

文本内容：
---
{content}
---

上下文：
{context if context else "无"}

请以严格的 JSON 格式返回：
{{
    "causal_chains": [
        {{
            "cause": "起因（简洁描述）",
            "mechanism": "作用机制（为什么会导致）",
            "effect": "结果（会导致什么）",
            "strength": 0.0-1.0,
            "domain": "所属领域（如工业制造/物理/逻辑等）"
        }}
    ],
    "summary": "这段内容涉及的因果逻辑总结（1-2句话）"
}}

只返回 JSON，不要其他文字。"""

        try:
            messages = [
                {"role": "system", "content": "你是一个因果逻辑分析专家，只返回JSON。"},
                {"role": "user", "content": prompt}
            ]
            result = await self.client.structured_output(messages, {})

            if not result:
                return {"success": False, "error": "LLM返回为空"}
            
            # 解析并更新图谱
            extracted = result.get("causal_chains", [])
            added_count = 0
            conflicts = []
            
            for chain in extracted:
                success, conflict = self._add_causal_link(
                    cause=chain.get("cause", ""),
                    effect=chain.get("effect", ""),
                    mechanism=chain.get("mechanism", ""),
                    strength=chain.get("strength", 0.5),
                    domain=chain.get("domain", "general")
                )
                if success:
                    added_count += 1
                if conflict:
                    conflicts.append(conflict)
            
            logger.info(f"[因果引擎] 从内容中提取了 {len(extracted)} 条因果链，新增 {added_count} 条")
            
            return {
                "success": True,
                "extracted_count": len(extracted),
                "added_count": added_count,
                "conflicts": conflicts,
                "summary": result.get("summary", "")
            }
            
        except Exception as e:
            logger.error(f"[因果引擎] 提取失败: {e}")
            return {"success": False, "error": str(e)}

    def _add_causal_link(
        self,
        cause: str,
        effect: str,
        mechanism: str,
        strength: float = 0.5,
        domain: str = "general"
    ) -> Tuple[bool, Optional[Dict]]:
        """
        添加因果边到图谱
        
        Returns:
            (是否成功, 冲突信息)
        """
        if not cause or not effect:
            return False, None
            
        # 创建或获取节点
        cause_node_id = self._get_or_create_node(cause, domain, "cause")
        effect_node_id = self._get_or_create_node(effect, domain, "effect")
        
        # 检查是否已存在相同的边
        if self.dag.has_edge(cause_node_id, effect_node_id):
            # 更新强度（取平均值）
            old_strength = self.dag[cause_node_id][effect_node_id].get("strength", 0.5)
            new_strength = (old_strength + strength) / 2
            self.dag[cause_node_id][effect_node_id]["strength"] = new_strength
            self.dag[cause_node_id][effect_node_id]["evidence_count"] += 1
            return True, None
        
        # 检查反向边（冲突检测）
        if self.dag.has_edge(effect_node_id, cause_node_id):
            reverse_strength = self.dag[effect_node_id][cause_node_id].get("strength", 0.5)
            if strength > 0.7 and reverse_strength > 0.7:
                # 严重冲突！
                return False, {
                    "type": "bidirectional_conflict",
                    "cause": cause,
                    "effect": effect,
                    "message": f"检测到逻辑冲突：'{cause}' 既促进又抑制 '{effect}'"
                }
        
        # 添加边
        self.dag.add_edge(
            cause_node_id, 
            effect_node_id,
            mechanism=mechanism,
            strength=strength,
            evidence_count=1,
            domain=domain,
            created_at=datetime.utcnow().isoformat()
        )
        
        return True, None

    def _get_or_create_node(self, name: str, domain: str, node_type: str = "concept") -> str:
        """获取或创建节点"""
        # 标准化节点ID
        node_id = name.lower().strip()
        
        if node_id not in self.dag:
            self.dag.add_node(
                node_id,
                name=name,
                domain=domain,
                node_type=node_type,
                created_at=datetime.utcnow().isoformat()
            )
            self._node_cache[node_id] = {
                "name": name,
                "domain": domain,
                "node_type": node_type
            }
        
        return node_id

    # ==================== 反事实推理 ====================

    def counterfactual_query(
        self, 
        intervention_node: str, 
        target_depth: int = 3
    ) -> Dict[str, Any]:
        """
        反事实推理：如果 [节点] 发生改变，会对系统产生什么链式反应？
        
        Args:
            intervention_node: 干预的节点
            target_depth: 追溯的深度
            
        Returns:
            影响链分析结果
        """
        node_id = intervention_node.lower().strip()
        
        if node_id not in self.dag:
            return {
                "found": False,
                "message": f"未在现有知识库中发现 '{intervention_node}' 的因果路径"
            }
        
        # 获取所有受影响的下游节点
        descendants = nx.descendants(self.dag, node_id)
        
        if not descendants:
            return {
                "found": True,
                "intervention": intervention_node,
                "impact": "无下游影响",
                "message": "该节点不影响其他变量"
            }
        
        # 计算影响路径
        impact_chains = []
        for descendant in descendants:
            try:
                # 找到最短路径
                path = nx.shortest_path(self.dag, node_id, descendant)
                
                # 计算路径上的因果强度乘积
                path_strength = 1.0
                path_mechanisms = []
                
                for i in range(len(path) - 1):
                    edge_data = self.dag[path[i]][path[i+1]]
                    path_strength *= edge_data.get("strength", 0.5)
                    if edge_data.get("mechanism"):
                        path_mechanisms.append(edge_data["mechanism"])
                
                impact_chains.append({
                    "effect": self.dag.nodes[descendant].get("name", descendant),
                    "path": " -> ".join([self.dag.nodes[n].get("name", n) for n in path]),
                    "path_length": len(path) - 1,
                    "cumulative_strength": round(path_strength, 3),
                    "mechanisms": path_mechanisms
                })
            except nx.NetworkXNoPath:
                continue
        
        # 按因果强度排序
        impact_chains.sort(key=lambda x: x["cumulative_strength"], reverse=True)
        
        return {
            "found": True,
            "intervention": intervention_node,
            "total_affected": len(impact_chains),
            "impact_chains": impact_chains[:10],  # 返回前10个最强烈的影响
            "message": f"干预 '{intervention_node}' 可能引发 {len(impact_chains)} 个下游变量变化"
        }

    # ==================== 因果冲突检测 ====================

    def detect_conflicts(self) -> List[Dict]:
        """
        检测因果图谱中的逻辑冲突
        
        Returns:
            冲突列表
        """
        conflicts = []
        
        # 检查双向边（A->B 且 B->A 都强）
        for node_a, node_b in self.dag.edges():
            if self.dag.has_edge(node_b, node_a):
                strength_ab = self.dag[node_a][node_b].get("strength", 0)
                strength_ba = self.dag[node_b][node_a].get("strength", 0)
                
                if strength_ab > 0.6 and strength_ba > 0.6:
                    conflicts.append({
                        "type": "bidirectional",
                        "node_a": self.dag.nodes[node_a].get("name", node_a),
                        "node_b": self.dag.nodes[node_b].get("name", node_b),
                        "message": f"双向强因果：'{node_a}' 与 '{node_b}' 相互影响",
                        "severity": "high"
                    })
        
        # 检查弱因果链（某节点被大量弱边指向但无强边）
        for node in self.dag.nodes():
            in_edges = self.dag.in_edges(node, data=True)
            if len(in_edges) > 3:
                avg_strength = sum(e[2].get("strength", 0) for e in in_edges) / len(in_edges)
                if avg_strength < 0.4:
                    conflicts.append({
                        "type": "weak_causality",
                        "node": self.dag.nodes[node].get("name", node),
                        "incoming_count": len(in_edges),
                        "avg_strength": round(avg_strength, 2),
                        "message": f"'{node}' 被多个弱因果链指向，可能不是真正的因果",
                        "severity": "low"
                    })
        
        return conflicts

    # ==================== 图谱统计 ====================

    def get_statistics(self) -> Dict:
        """获取因果图谱统计信息"""
        return {
            "total_nodes": self.dag.number_of_nodes(),
            "total_edges": self.dag.number_of_edges(),
            "avg_degree": sum(dict(self.dag.degree()).values()) / max(1, self.dag.number_of_nodes()),
            "domains": self._count_domains(),
            "strong_causal_links": self._count_strong_links(),
            "is_dag": nx.is_directed_acyclic_graph(self.dag),
            "connected_components": nx.number_weakly_connected_components(self.dag)
        }

    def _count_domains(self) -> Dict[str, int]:
        """统计各领域的因果链数量"""
        domains = defaultdict(int)
        for _, _, data in self.dag.edges(data=True):
            domain = data.get("domain", "general")
            domains[domain] += 1
        return dict(domains)

    def _count_strong_links(self) -> int:
        """统计强因果链数量（strength > 0.7）"""
        return sum(
            1 for _, _, data in self.dag.edges(data=True) 
            if data.get("strength", 0) > 0.7
        )

    # ==================== 导出/导入 ====================

    def export_graph(self) -> Dict:
        """导出图谱为可序列化的格式"""
        return {
            "nodes": [
                {
                    "id": node_id,
                    "name": data.get("name", node_id),
                    "domain": data.get("domain", "general"),
                    "node_type": data.get("node_type", "concept")
                }
                for node_id, data in self.dag.nodes(data=True)
            ],
            "links": [
                {
                    "source": u,
                    "target": v,
                    "mechanism": data.get("mechanism", ""),
                    "strength": data.get("strength", 0.5),
                    "domain": data.get("domain", "general")
                }
                for u, v, data in self.dag.edges(data=True)
            ]
        }


# ===== 数据库操作 =====

async def save_causal_extraction_log(
    db_session,
    source_content: str,
    extracted_links: List[Dict],
    source_type: str = "text",
    status: str = "success"
):
    """保存因果提取日志"""
    from db.models import CausalExtractionLog
    
    log = CausalExtractionLog(
        source_content=source_content[:2000],  # 截断
        source_type=source_type,
        extracted_links=extracted_links,
        status=status
    )
    db_session.add(log)
    await db_session.commit()
    return log


async def get_causal_nodes(db_session, domain: str = None, limit: int = 100):
    """获取因果节点"""
    from sqlalchemy import select
    from db.models import CausalNode
    
    query = select(CausalNode)
    if domain:
        query = query.where(CausalNode.domain == domain)
    query = query.limit(limit)
    
    result = await db_session.execute(query)
    return result.scalars().all()


async def get_causal_links(db_session, min_strength: float = 0.0, limit: int = 100):
    """获取因果边"""
    from sqlalchemy import select
    from db.models import CausalLink
    
    query = select(CausalLink).where(CausalLink.strength >= min_strength)
    query = query.limit(limit)
    
    result = await db_session.execute(query)
    return result.scalars().all()


# ===== 便捷函数 =====

def get_causal_engine() -> CausalReasoningEngine:
    """获取因果推理引擎实例"""
    return CausalReasoningEngine()
