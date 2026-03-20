"""
知识卡片系统 - 目标类型识别
"""
import re
from typing import Dict, Optional


class GoalTypeDetector:
    """
    识别学习目标类型，决定如何拆解和生成知识单元
    """

    GOAL_TYPES = {
        "characters": {
            "keywords": ["汉字", "字", "文字", "生字"],
            "unit_name": "汉字",
            "card_template": "character",
            "searchable": True,
        },
        "vocabulary": {
            "keywords": ["单词", "词汇", "词语", "生词", "英语"],
            "unit_name": "词汇",
            "card_template": "vocabulary",
            "searchable": True,
        },
        "concepts": {
            "keywords": ["概念", "知识点", "理论", "原理", "定义"],
            "unit_name": "概念",
            "card_template": "concept",
            "searchable": True,
        },
        "programming": {
            "keywords": ["编程", "代码", "Python", "Java", "算法", "函数", "语法"],
            "unit_name": "知识点",
            "card_template": "programming",
            "searchable": True,
        },
        "skills": {
            "keywords": ["技能", "方法", "技巧", "如何", "怎么"],
            "unit_name": "技能",
            "card_template": "skill",
            "searchable": False,
        },
        "general": {
            "keywords": [],
            "unit_name": "知识点",
            "card_template": "general",
            "searchable": True,
        }
    }

    def detect(self, goal_description: str) -> str:
        desc = goal_description.lower()
        for goal_type, config in self.GOAL_TYPES.items():
            if any(kw in desc for kw in config["keywords"]):
                return goal_type
        return "general"

    def get_config(self, goal_type: str) -> Dict:
        return self.GOAL_TYPES.get(goal_type, self.GOAL_TYPES["general"])

    def extract_count(self, description: str) -> Optional[int]:
        """从描述中提取数量"""
        patterns = [r'(\d+)\s*个', r'(\d+)\s*字', r'(\d+)\s*词', r'(\d+)']
        for p in patterns:
            m = re.search(p, description)
            if m:
                return int(m.group(1))
        return None
