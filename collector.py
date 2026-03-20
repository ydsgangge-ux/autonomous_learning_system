# collector.py - 节点收集器
"""
系统"学习"的核心执行者。

核心逻辑：
- 思维导图每个节点有 collected=True/False
- collected=False 的节点 = 系统还不知道这个知识
- 遇到空节点就调LLM学习，存入，标记为已收集
- 整棵树收集完 = 这个目标学会了

对外只需要两个方法：
  collect_on_demand(query, root)   ← 用户提问时触发，按需收集
  collect_tree(root)               ← 主动批量收集整棵树
"""

import time
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from llm_client import LLMClient, get_client
from storage import DataManager


# ========== 节点数据结构 ==========

@dataclass
class MindMapNode:
    """
    思维导图节点
    collected=True 表示系统已经学会了这个节点的知识
    """
    id: str
    title: str
    content: Any = None
    collected: bool = False
    collected_at: str = ""
    collected_by: str = ""
    depth: int = 0
    importance: float = 0.5
    node_type: str = "concept"
    parent_id: str = ""
    children: List['MindMapNode'] = field(default_factory=list)

    def is_learned(self) -> bool:
        """自己收集了，且所有子节点都收集了"""
        if not self.collected:
            return False
        return all(child.is_learned() for child in self.children)

    def completion_rate(self) -> float:
        all_n = self._all_nodes()
        if not all_n:
            return 0.0
        return sum(1 for n in all_n if n.collected) / len(all_n)

    def _all_nodes(self) -> List['MindMapNode']:
        result = [self]
        for child in self.children:
            result.extend(child._all_nodes())
        return result

    def uncollected_nodes(self) -> List['MindMapNode']:
        nodes = [n for n in self._all_nodes() if not n.collected]
        return sorted(nodes, key=lambda x: -x.importance)

    def find_by_title(self, title: str) -> Optional['MindMapNode']:
        title_lower = title.lower()
        for node in self._all_nodes():
            if title_lower in node.title.lower() or node.title.lower() in title_lower:
                return node
        return None

    def find_by_path(self, path: List[str]) -> Optional['MindMapNode']:
        if not path:
            return self
        target = path[0].lower()
        for child in self.children:
            if target in child.title.lower():
                if len(path) == 1:
                    return child
                return child.find_by_path(path[1:])
        return None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "collected": self.collected,
            "collected_at": self.collected_at,
            "collected_by": self.collected_by,
            "depth": self.depth,
            "importance": self.importance,
            "node_type": self.node_type,
            "parent_id": self.parent_id,
            "children": [c.to_dict() for c in self.children],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'MindMapNode':
        node = cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            content=data.get("content"),
            collected=data.get("collected", False),
            collected_at=data.get("collected_at", ""),
            collected_by=data.get("collected_by", ""),
            depth=data.get("depth", 0),
            importance=data.get("importance", 0.5),
            node_type=data.get("node_type", "concept"),
            parent_id=data.get("parent_id", ""),
        )
        node.children = [cls.from_dict(c) for c in data.get("children", [])]
        return node


# ========== 目标类型配置 ==========

GOAL_TYPE_CONFIGS = {
    "characters": {
        "tree_template": {
            "title": "{unit}",
            "children": [
                {"title": "读音", "importance": 1.0, "node_type": "fact"},
                {"title": "字形", "importance": 0.9, "children": [
                    {"title": "笔画", "importance": 0.8, "node_type": "fact"},
                    {"title": "部首", "importance": 0.8, "node_type": "fact"},
                    {"title": "结构", "importance": 0.6, "node_type": "fact"},
                ]},
                {"title": "含义", "importance": 1.0, "node_type": "concept"},
                {"title": "用法", "importance": 0.9, "children": [
                    {"title": "组词", "importance": 0.9, "node_type": "example"},
                    {"title": "例句", "importance": 0.7, "node_type": "example"},
                ]},
                {"title": "记忆方法", "importance": 0.7, "node_type": "skill"},
                {"title": "关联", "importance": 0.5, "children": [
                    {"title": "形近字", "importance": 0.6, "node_type": "concept"},
                    {"title": "同音字", "importance": 0.5, "node_type": "concept"},
                ]},
            ]
        },
        "prompts": {
            "读音": '"{unit}"字的拼音读音是什么？只返回JSON：{{"content": "zhōng（第一声）"}}',
            "笔画": '"{unit}"字共几画？只返回JSON：{{"content": "X画"}}',
            "部首": '"{unit}"字的部首是什么？只返回JSON：{{"content": "X"}}',
            "结构": '"{unit}"字是什么结构？只返回JSON：{{"content": "XX结构"}}',
            "含义": '"{unit}"字有哪些含义？只返回JSON：{{"content": ["含义1", "含义2"]}}',
            "组词": '用"{unit}"字组4个常用词？只返回JSON：{{"content": ["词1", "词2", "词3", "词4"]}}',
            "例句": '用"{unit}"字造2个例句？只返回JSON：{{"content": ["例句1", "例句2"]}}',
            "记忆方法": '"{unit}"字有什么好的记忆方法？只返回JSON：{{"content": "记忆方法"}}',
            "形近字": '"{unit}"字有哪些形近字，如何区分？只返回JSON：{{"content": "形近字及区分"}}',
            "同音字": '"{unit}"字有哪些同音字？只返回JSON：{{"content": ["同音字1", "同音字2"]}}',
        },
        "default_prompt": '关于汉字"{unit}"的"{node_title}"，请给出内容。只返回JSON：{{"content": "内容"}}',
    },
    "vocabulary": {
        "tree_template": {
            "title": "{unit}",
            "children": [
                {"title": "发音", "importance": 1.0, "node_type": "fact"},
                {"title": "释义", "importance": 1.0, "node_type": "concept"},
                {"title": "例句", "importance": 0.9, "node_type": "example"},
                {"title": "搭配", "importance": 0.8, "node_type": "skill"},
                {"title": "同义词", "importance": 0.6, "node_type": "concept"},
                {"title": "记忆方法", "importance": 0.7, "node_type": "skill"},
            ]
        },
        "prompts": {
            "发音": '"{unit}"的发音是什么？只返回JSON：{{"content": "发音"}}',
            "释义": '"{unit}"的释义？只返回JSON：{{"content": ["释义1", "释义2"]}}',
            "例句": '"{unit}"的2个例句？只返回JSON：{{"content": ["例句1", "例句2"]}}',
            "搭配": '"{unit}"的常用搭配？只返回JSON：{{"content": ["搭配1", "搭配2"]}}',
            "同义词": '"{unit}"的同义词？只返回JSON：{{"content": ["词1", "词2"]}}',
            "记忆方法": '"{unit}"如何记忆？只返回JSON：{{"content": "方法"}}',
        },
        "default_prompt": '关于词汇"{unit}"的"{node_title}"，请给出内容。只返回JSON：{{"content": "内容"}}',
    },
    "programming": {
        "tree_template": {
            "title": "{unit}",
            "children": [
                {"title": "定义", "importance": 1.0, "node_type": "concept"},
                {"title": "语法", "importance": 1.0, "node_type": "skill"},
                {"title": "代码示例", "importance": 0.9, "node_type": "example"},
                {"title": "使用场景", "importance": 0.8, "node_type": "concept"},
                {"title": "常见错误", "importance": 0.8, "node_type": "fact"},
                {"title": "相关概念", "importance": 0.6, "node_type": "concept"},
            ]
        },
        "prompts": {
            "定义": '"{unit}"的定义是什么？只返回JSON：{{"content": "定义"}}',
            "语法": '"{unit}"的语法格式？只返回JSON：{{"content": "语法"}}',
            "代码示例": '"{unit}"的代码示例？只返回JSON：{{"content": "代码"}}',
            "使用场景": '"{unit}"适用场景？只返回JSON：{{"content": ["场景1", "场景2"]}}',
            "常见错误": '使用"{unit}"时的常见错误？只返回JSON：{{"content": ["错误1", "错误2"]}}',
            "相关概念": '与"{unit}"相关的概念？只返回JSON：{{"content": ["概念1", "概念2"]}}',
        },
        "default_prompt": '关于编程概念"{unit}"的"{node_title}"，请给出内容。只返回JSON：{{"content": "内容"}}',
    },
    "general": {
        "tree_template": {
            "title": "{unit}",
            "children": [
                {"title": "定义", "importance": 1.0, "node_type": "concept"},
                {"title": "核心要点", "importance": 0.9, "node_type": "concept"},
                {"title": "具体例子", "importance": 0.8, "node_type": "example"},
                {"title": "应用场景", "importance": 0.7, "node_type": "skill"},
                {"title": "记忆方法", "importance": 0.6, "node_type": "skill"},
            ]
        },
        "prompts": {},
        "default_prompt": '关于"{unit}"的"{node_title}"，请给出内容。只返回JSON：{{"content": "内容"}}',
    },
}


# ========== 节点收集器 ==========

class NodeCollector:
    """
    节点收集器 - 系统学习的执行者

    两种模式：
    1. collect_on_demand  用户提问时按需收集
    2. collect_tree       主动批量收集整棵树
    """

    def __init__(self, db: Optional[DataManager] = None,
                 llm: Optional[LLMClient] = None):
        self.db = db or DataManager()
        self.llm = llm or get_client()
        self._counter = 0

    def _gen_id(self) -> str:
        self._counter += 1
        return f"node_{int(time.time()*1000)}_{self._counter}"

    # ===== 树的创建 =====

    def build_tree_from_template(self, unit: str, goal_type: str) -> MindMapNode:
        """根据目标类型为知识单元创建空树（所有节点 collected=False）"""
        config = GOAL_TYPE_CONFIGS.get(goal_type, GOAL_TYPE_CONFIGS["general"])
        return self._tmpl_to_tree(config["tree_template"], unit, depth=0)

    def _tmpl_to_tree(self, tmpl: Dict, unit: str,
                      depth: int, parent_id: str = "") -> MindMapNode:
        title = tmpl["title"].replace("{unit}", unit)
        node = MindMapNode(
            id=self._gen_id(),
            title=title,
            depth=depth,
            importance=tmpl.get("importance", 0.5),
            node_type=tmpl.get("node_type", "concept"),
            parent_id=parent_id,
            collected=False,
        )
        for child_tmpl in tmpl.get("children", []):
            child = self._tmpl_to_tree(child_tmpl, unit, depth + 1, node.id)
            node.children.append(child)
        return node

    def build_tree_from_llm(self, unit: str,
                            goal_description: str, depth: int = 3) -> MindMapNode:
        """让LLM为知识单元设计思维导图结构（用于非标准类型）"""
        result = self.llm.generate_json(
            prompt=f"""为学习主题"{unit}"（来自：{goal_description}）
设计{depth}层思维导图结构。返回JSON：
{{
  "title": "{unit}",
  "children": [
    {{"title": "子主题", "importance": 0.9, "node_type": "concept",
      "children": [{{"title": "知识点", "importance": 0.8,
                    "node_type": "fact", "children": []}}]}}
  ]
}}
importance 0~1，node_type 从 concept/skill/example/fact 选。""",
            system="只返回JSON。"
        )
        if result:
            return self._tmpl_to_tree(result, unit, depth=0)
        return self.build_tree_from_template(unit, "general")

    # ===== 按需收集 =====

    def collect_on_demand(self, query: str, root: MindMapNode,
                          goal_type: str, unit: str = "") -> Tuple[Optional[MindMapNode], Any]:
        """
        用户提问时触发。
        找到对应节点 → 已收集直接返回 → 未收集就学 → 节点不存在就创建再学
        """
        node = self._find_best_match(query, root)

        if node and node.collected:
            return node, node.content

        if node and not node.collected:
            content = self._collect_single(node, unit or root.title, goal_type)
            return node, content

        # 节点不存在，创建并学习
        new_node = MindMapNode(
            id=self._gen_id(), title=query,
            depth=1, importance=0.5,
            node_type="concept", parent_id=root.id,
        )
        root.children.append(new_node)
        content = self._collect_single(new_node, unit or root.title, goal_type)
        return new_node, content

    def _find_best_match(self, query: str,
                         root: MindMapNode) -> Optional[MindMapNode]:
        query_lower = query.lower()
        best, best_score = None, 0.0
        for node in root._all_nodes():
            if node.id == root.id:
                continue
            node_lower = node.title.lower()
            if query_lower == node_lower:
                return node
            if query_lower in node_lower or node_lower in query_lower:
                score = len(node_lower) / max(len(query_lower), 1)
                if score > best_score:
                    best_score, best = score, node
        return best if best_score > 0.3 else None

    # ===== 单节点收集（唯一调用LLM的地方） =====

    def _collect_single(self, node: MindMapNode,
                        unit: str, goal_type: str) -> Any:
        prompt = self._build_prompt(node.title, unit, goal_type)
        
        try:
            result = self.llm.generate_json(prompt, max_tokens=400)

            if result and "content" in result:
                content = result["content"]
            elif result:
                content = result
            else:
                # 后备：尝试普通聊天
                content = self.llm.chat(
                    f'关于"{unit}"的"{node.title}"，请简洁回答。',
                    system="请用一两句话回答。"
                )
        except Exception as e:
            print(f"[警告] LLM调用失败: {e}")
            content = None

        # 即使 LLM 失败，也不要标记为已收集
        if content is None:
            print(f"[警告] 节点 '{node.title}' 学习失败，内容为空")
            return "（学习失败，请稍后重试）"
        
        node.content = content
        node.collected = True
        node.collected_at = datetime.now().isoformat()
        node.collected_by = f"llm:{self.llm.model}"
        return content

    def _build_prompt(self, node_title: str, unit: str, goal_type: str) -> str:
        config = GOAL_TYPE_CONFIGS.get(goal_type, GOAL_TYPE_CONFIGS["general"])
        prompts = config.get("prompts", {})
        if node_title in prompts:
            return prompts[node_title].replace("{unit}", unit)
        for key, tmpl in prompts.items():
            if key in node_title or node_title in key:
                return tmpl.replace("{unit}", unit)
        default = config.get("default_prompt",
                             '关于"{unit}"的"{node_title}"给出内容。只返回JSON：{{"content": "内容"}}')
        return default.replace("{unit}", unit).replace("{node_title}", node_title)

    # ===== 批量收集 =====

    def collect_tree(self, root: MindMapNode, unit: str,
                     goal_type: str, on_progress=None) -> Dict:
        """主动收集整棵树，按重要性顺序"""
        uncollected = root.uncollected_nodes()
        total, done, failed = len(uncollected), 0, 0

        for node in uncollected:
            try:
                self._collect_single(node, unit, goal_type)
                done += 1
            except Exception as e:
                failed += 1
                print(f"   ⚠️  {node.title}: {e}")
            if on_progress:
                on_progress(done + failed, total, node.title)
            time.sleep(0.3)

        return {"total": total, "done": done, "failed": failed,
                "completion": root.completion_rate()}

    # ===== 持久化 =====

    def save_tree(self, goal_id: str, unit: str, root: MindMapNode):
        self.db.storage.save("mindmap_trees", f"{goal_id}_{_safe_key(unit)}", {
            "goal_id": goal_id, "unit": unit,
            "tree": root.to_dict(),
            "saved_at": datetime.now().isoformat(),
            "completion_rate": root.completion_rate(),
        })

    def load_tree(self, goal_id: str, unit: str) -> Optional[MindMapNode]:
        data = self.db.storage.load("mindmap_trees", f"{goal_id}_{_safe_key(unit)}")
        if data and "tree" in data:
            return MindMapNode.from_dict(data["tree"])
        return None

    def save_goal_units(self, goal_id: str, units: List[str]):
        self.db.storage.save("goal_units", goal_id, {
            "goal_id": goal_id, "units": units,
            "saved_at": datetime.now().isoformat(),
        })

    def load_goal_units(self, goal_id: str) -> List[str]:
        data = self.db.storage.load("goal_units", goal_id)
        return data.get("units", []) if data else []

    def get_completion_report(self, goal_id: str, units: List[str]) -> Dict:
        total_nodes = collected_nodes = 0
        learned = 0
        for unit in units:
            tree = self.load_tree(goal_id, unit)
            if tree:
                all_n = tree._all_nodes()
                c = sum(1 for n in all_n if n.collected)
                total_nodes += len(all_n)
                collected_nodes += c
                if tree.is_learned():
                    learned += 1
        return {
            "total_units": len(units),
            "learned_units": learned,
            "total_nodes": total_nodes,
            "collected_nodes": collected_nodes,
            "overall_completion": collected_nodes / total_nodes if total_nodes else 0,
        }


def _safe_key(text: str) -> str:
    import hashlib
    prefix = re.sub(r'[^\w]', '', text[:4])
    h = hashlib.md5(text.encode()).hexdigest()[:8]
    return f"{prefix}_{h}"


# ========== 测试 ==========

if __name__ == "__main__":
    import shutil
    print("🧪 测试 collector.py\n")

    db = DataManager("./test_collector")
    collector = NodeCollector(db)

    # 构建树
    tree = collector.build_tree_from_template("蠢", "characters")
    all_n = tree._all_nodes()
    print(f"树构建完成：{len(all_n)}个节点，完成度 {tree.completion_rate():.0%}")

    def show(node, indent=0):
        print(f"{'  '*indent}{'✅' if node.collected else '❌'} {node.title}")
        for c in node.children:
            show(c, indent+1)
    show(tree)

    # 按需收集
    print("\n按需收集「读音」...")
    node, content = collector.collect_on_demand("读音", tree, "characters", "蠢")
    print(f"  内容: {content}")

    print("\n再次查询「读音」（应直接返回）...")
    node2, content2 = collector.collect_on_demand("读音", tree, "characters", "蠢")
    print(f"  内容: {content2}  已收集: {node2.collected}")

    # 持久化
    collector.save_tree("test_goal", "蠢", tree)
    loaded = collector.load_tree("test_goal", "蠢")
    reading = loaded.find_by_title("读音") if loaded else None
    print(f"\n持久化测试：加载后读音节点 collected={reading.collected if reading else '?'}")

    shutil.rmtree("./test_collector", ignore_errors=True)
    print("\n✅ 测试完成")
