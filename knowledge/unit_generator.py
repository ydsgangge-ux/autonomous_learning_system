"""
知识单元生成器 - 将目标拆解为知识单元列表
"""
import asyncio
from typing import List, Optional

from llm.client import chat_completion_json
from core.utils import get_logger

logger = get_logger(__name__)


class UnitListGenerator:
    """
    第一步：把目标拆解成具体的知识单元列表
    例如："学习3500常用汉字" → ["一", "乙", "二", "十", ...]
    """

    # 内置的标准列表
    BUILTIN_LISTS = {
        "hsk_chars_basic": None,
    }

    def __init__(self):
        pass

    async def generate_unit_list(self,
                                 goal_description: str,
                                 goal_type: str,
                                 count_hint: Optional[int] = None) -> List[str]:
        """
        生成知识单元列表
        """
        print(f"📋 生成知识单元列表: {goal_description}")

        # 汉字特殊处理：使用标准常用汉字表
        if goal_type == "characters" and count_hint and count_hint >= 100:
            units = self._get_standard_chars(count_hint)
            if units:
                print(f"✅ 使用标准汉字表：{len(units)}个汉字")
                return units

        # 其他情况用LLM生成列表
        return await self._llm_generate_list(goal_description, goal_type, count_hint)

    def _get_standard_chars(self, count: int) -> List[str]:
        """返回标准常用汉字（按使用频率排序）"""
        # 最高频的200个常用汉字
        top_200 = list("的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看先存而已通如被比于知质量再都特提到进后来来的"
        )

        # 去重并保留顺序
        seen = set()
        unique = []
        for char in top_200:
            if char not in seen and '\u4e00' <= char <= '\u9fff':
                seen.add(char)
                unique.append(char)

        return unique[:count]

    async def _llm_generate_list(self,
                                 goal: str,
                                 goal_type: str,
                                 count: Optional[int]) -> List[str]:
        """用LLM生成知识单元列表"""
        count_str = f"恰好{count}个" if count else "合理数量的"

        type_hints = {
            "vocabulary": "单词或词组",
            "concepts": "核心概念名称",
            "programming": "编程知识点名称（如：变量、函数、循环等）",
            "skills": "技能步骤或子技能",
            "general": "知识单元",
        }
        unit_hint = type_hints.get(goal_type, "知识单元")

        try:
            result = await chat_completion_json(
                messages=[{
                    "role": "user",
                    "content": f"""对于学习目标："{goal}"
请生成{count_str}{unit_hint}的列表。
这些是需要逐个学习的最小单元，每个单元都会单独生成知识卡片。
只返回JSON数组，如：["单元1", "单元2", ...]"""
                }],
                schema_hint='["string", "string"]'
            )

            if isinstance(result, list):
                return [str(item) for item in result if item]
        except Exception as e:
            logger.error(f"生成知识单元列表失败: {e}")

        return []
