"""
知识卡片生成器 - 为知识单元生成结构化内容
"""
import time
from datetime import datetime
from typing import Dict, Iterator, List, Optional

from llm.client import chat_completion_json
from core.utils import get_logger

logger = get_logger(__name__)


class KnowledgeCardGenerator:
    """知识卡片生成器"""

    CARD_TEMPLATES = {
        "character": """为汉字"{unit}"生成完整学习卡片，返回JSON：
{{
  "unit": "{unit}",
  "reading": "拼音（含声调，如：zhōng）",
  "strokes": 笔画数,
  "radical": "部首",
  "meanings": ["含义1", "含义2"],
  "compounds": ["组词1", "组词2", "组词3", "组词4"],
  "sentences": ["例句1", "例句2"],
  "memory_tip": "记忆口诀或联想方法（生动有趣）",
  "common_mistakes": "常见错误或易混淆字",
  "usage_level": "最常用/常用/较常用"
}}""",

        "vocabulary": """为词汇"{unit}"生成学习卡片，返回JSON：
{{
  "unit": "{unit}",
  "pronunciation": "发音",
  "definitions": ["定义1", "定义2"],
  "examples": ["例句1", "例句2"],
  "synonyms": ["同义词"],
  "antonyms": ["反义词"],
  "collocations": ["常用搭配1", "常用搭配2"],
  "memory_tip": "记忆方法"
}}""",

        "programming": """为编程概念"{unit}"生成学习卡片，返回JSON：
{{
  "unit": "{unit}",
  "definition": "简洁定义（一句话）",
  "explanation": "详细解释（2-3句话）",
  "syntax": "语法格式或用法",
  "code_example": "可运行的代码示例",
  "common_use_cases": ["使用场景1", "使用场景2"],
  "common_mistakes": ["常见错误1", "常见错误2"],
  "related_concepts": ["相关概念1", "相关概念2"],
  "difficulty": "初级/中级/高级"
}}""",

        "concept": """为概念"{unit}"生成学习卡片，返回JSON：
{{
  "unit": "{unit}",
  "definition": "核心定义",
  "explanation": "详细解释",
  "examples": ["具体例子1", "具体例子2"],
  "analogies": "类比或比喻帮助理解",
  "related_concepts": ["相关概念"],
  "applications": ["实际应用场景"],
  "key_points": ["要点1", "要点2", "要点3"]
}}""",

        "general": """为"{unit}"生成学习卡片，返回JSON：
{{
  "unit": "{unit}",
  "summary": "核心摘要（2-3句话）",
  "key_points": ["要点1", "要点2", "要点3"],
  "examples": ["例子1", "例子2"],
  "memory_tip": "记忆方法",
  "related": ["相关知识"]
}}""",
    }

    def __init__(self):
        pass

    async def generate_card(self, unit: str, card_template: str) -> Dict:
        """生成单个知识卡片"""
        template = self.CARD_TEMPLATES.get(card_template, self.CARD_TEMPLATES["general"])
        prompt = template.replace("{unit}", unit)

        try:
            logger.info(f"开始生成卡片: {unit}, 模板: {card_template}")
            result = await chat_completion_json(
                messages=[{"role": "user", "content": prompt}],
                schema_hint=f'{{"unit": "{unit}"}}'
            )
            logger.info(f"卡片生成成功: {unit}")

            if not result or not isinstance(result, dict):
                logger.warning(f"生成卡片返回空或格式错误: {unit}, 结果: {result}")
                return self._fallback_card(unit, card_template)

            result["_generated_at"] = datetime.now().isoformat()
            result["_template"] = card_template
            return result

        except Exception as e:
            logger.error(f"生成卡片失败 {unit}: {type(e).__name__}: {e}")
            return self._fallback_card(unit, card_template)

    def _fallback_card(self, unit: str, card_template: str) -> Dict:
        """生成简化版卡片作为备用"""
        return {
            "unit": unit,
            "summary": f"关于{unit}的知识（生成失败，请重试）",
            "key_points": ["暂无详细内容"],
            "_generated_at": datetime.now().isoformat(),
            "_template": card_template,
            "_failed": True,
        }

    async def generate_batch(self,
                           units: List[str],
                           card_template: str,
                           batch_size: int = 5) -> Iterator[Dict]:
        """
        批量生成知识卡片
        """
        for i, unit in enumerate(units):
            card = await self.generate_card(unit, card_template)
            yield card

            # 避免API限速
            if i < len(units) - 1:
                await asyncio.sleep(0.2)


import asyncio  # 放在底部避免导入循环
