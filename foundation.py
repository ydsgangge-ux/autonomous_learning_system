# foundation.py - 基础数据结构和管理器
"""
新架构 v3.2 的基础模块：
- LearningGoal: 学习目标数据结构
- FoundationManager: 目标管理器
- 工具函数：generate_id
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import re


# ========== 枚举类型 ==========

class GoalScale(Enum):
    """目标规模"""
    MICRO = "micro"      # 单字/单词
    SMALL = "small"      # 10-50个
    MEDIUM = "medium"    # 50-200个
    LARGE = "large"      # 200-1000个
    MASSIVE = "massive"  # 1000+个


class GoalDifficulty(Enum):
    """目标难度"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


# ========== 学习目标 ==========

@dataclass
class LearningGoal:
    """学习目标"""
    id: str
    description: str
    goal_type: str = "general"
    status: str = "active"
    scale: GoalScale = GoalScale.MEDIUM
    difficulty: GoalDifficulty = GoalDifficulty.MEDIUM
    estimated_units: int = 0
    created_at: str = ""
    updated_at: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""
        return {
            "id": self.id,
            "description": self.description,
            "goal_type": self.goal_type,
            "status": self.status,
            "scale": self.scale.value if isinstance(self.scale, GoalScale) else self.scale,
            "difficulty": self.difficulty.value if isinstance(self.difficulty, GoalDifficulty) else self.difficulty,
            "estimated_units": self.estimated_units,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "meta": self.meta,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningGoal':
        """从字典创建对象"""
        return cls(
            id=data["id"],
            description=data["description"],
            goal_type=data.get("goal_type", "general"),
            status=data.get("status", "active"),
            scale=GoalScale(data.get("scale", "medium")) if data.get("scale") in [e.value for e in GoalScale] else GoalScale.MEDIUM,
            difficulty=GoalDifficulty(data.get("difficulty", "medium")) if data.get("difficulty") in [e.value for e in GoalDifficulty] else GoalDifficulty.MEDIUM,
            estimated_units=data.get("estimated_units", 0),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            meta=data.get("meta", {}),
        )


# ========== 基础管理器 ==========

class FoundationManager:
    """基础管理器 - 处理学习目标的CRUD"""

    def __init__(self, storage=None):
        self.storage = storage  # DataManager 实例
        self._counter = 0

    def create_learning_goal(self, description: str) -> LearningGoal:
        """创建新的学习目标"""
        goal_id = generate_id()
        goal = LearningGoal(
            id=goal_id,
            description=description,
        )
        return goal

    def generate_id(self) -> str:
        """生成唯一ID（备用方法）"""
        return generate_id()


# ========== 工具函数 ==========

_counter = 0

def generate_id() -> str:
    """生成唯一ID"""
    global _counter
    _counter += 1
    import time
    return f"goal_{int(time.time()*1000)}_{_counter}"


def detect_scale(description: str) -> GoalScale:
    """根据描述推断目标规模"""
    desc = description.lower()
    count_match = re.search(r'(\d+)', description)
    if count_match:
        count = int(count_match.group(1))
        if count <= 1:
            return GoalScale.MICRO
        elif count <= 50:
            return GoalScale.SMALL
        elif count <= 200:
            return GoalScale.MEDIUM
        elif count <= 1000:
            return GoalScale.LARGE
        else:
            return GoalScale.MASSIVE

    # 关键词判断
    if any(k in desc for k in ["3500", "常用字"]):
        return GoalScale.MASSIVE
    elif any(k in desc for k in ["基础", "入门", "初学"]):
        return GoalScale.SMALL

    return GoalScale.MEDIUM


def detect_difficulty(description: str) -> GoalDifficulty:
    """根据描述推断目标难度"""
    desc = description.lower()
    if any(k in desc for k in ["入门", "基础", "简单", "初学"]):
        return GoalDifficulty.EASY
    elif any(k in desc for k in ["进阶", "中级", "深入"]):
        return GoalDifficulty.HARD
    elif any(k in desc for k in ["高级", "专家", "精通", "专业"]):
        return GoalDifficulty.EXPERT
    return GoalDifficulty.MEDIUM


# ========== 测试 ==========

if __name__ == "__main__":
    print("🧪 测试 foundation.py\n")

    # 测试 ID 生成
    id1 = generate_id()
    id2 = generate_id()
    print(f"✅ 生成ID: {id1}")
    print(f"✅ 生成ID: {id2}")

    # 测试目标创建
    manager = FoundationManager()
    goal = manager.create_learning_goal("学习50个常用汉字")
    print(f"✅ 创建目标: {goal.description}")
    print(f"   ID: {goal.id}")
    print(f"   类型: {goal.goal_type}")
    print(f"   状态: {goal.status}")

    # 测试序列化
    goal_dict = goal.to_dict()
    print(f"\n✅ 序列化:")
    print(f"   {goal_dict}")

    # 测试反序列化
    restored = LearningGoal.from_dict(goal_dict)
    print(f"\n✅ 反序列化:")
    print(f"   {restored.description} ({restored.id})")

    # 测试规模检测
    tests = [
        ("学习1个字", GoalScale.MICRO),
        ("学习10个单词", GoalScale.SMALL),
        ("学习100个汉字", GoalScale.MEDIUM),
        ("学习3500常用字", GoalScale.MASSIVE),
    ]
    print("\n✅ 规模检测:")
    for desc, expected in tests:
        detected = detect_scale(desc)
        match = "✅" if detected == expected else "❌"
        print(f"   {match} '{desc}' → {detected.value}")

    print("\n✅ 测试完成")
