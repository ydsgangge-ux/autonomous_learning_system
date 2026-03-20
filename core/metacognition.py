"""
元认知引擎 (Meta-Cognition Engine)
====================================

这是系统的"前额叶皮层"，负责执行自我审计。
它不仅检查答案是否正确，还反思"我是如何思考的"以及"我的表达是否过于平庸"。

核心功能：
1. 自我审计 - 对生成内容进行多维度评价
2. 递归修正 - 根据反思结果重写内容
3. 经验积累 - 存储反思记录供未来参考

设计原则：
- 消除"AI味" - 避免陈词滥调和泛化表达
- 追求深度 - 触及底层原理
- 逻辑严密 - 因果推理无跳跃
"""

import json
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime

from llm.client import llm_client
from core.utils import get_logger

logger = get_logger(__name__)


class MetaCognitiveEngine:
    """
    元认知引擎
    
    负责对 AI 生成的内容进行自我审计和递归优化，
    使系统具备"知道自己知道什么"的能力。
    """

    # 审计阈值
    DEFAULT_LOGIC_THRESHOLD = 0.7
    DEFAULT_DEPTH_THRESHOLD = 0.6
    MAX_REFLECTION_ITERATIONS = 2  # 最多递归修正次数

    def __init__(self, client=None):
        self.client = client or llm_client
        self._system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你现在是自主智能学习系统(ALS)的『审计人格』。
你的任务不是回答用户问题，而是评价和批评 AI 生成的输出质量。

审计准则：
1. 逻辑严密性：是否存在因果倒置或推导跳跃？
2. 消除平庸：是否使用了"口水话"、陈词滥调或泛化的废话？
3. 深度检测：是否触及了底层原理（如物理机制、逻辑本质）？
4. 表达清晰：是否容易被理解？是否有模糊的表述？

你必须严格、苛刻地评价，因为你的反馈将直接决定内容是否需要重写。
不要给出安慰性的评价，要实事求是。"""

    async def reflect(self, content: str, context: str = "") -> Dict[str, Any]:
        """
        对生成的内容进行自我审计
        
        Args:
            content: 待审计的内容
            context: 上下文信息（如用户问题、目标描述等）
            
        Returns:
            包含各项评分和批评意见的字典
        """
        prompt = f"""{self._system_prompt}

待审计内容：
---
{content}
---

上下文（参考）：
{context if context else "无"}

请以严格的 JSON 格式返回评价结果：
{{
    "logic_score": 0.0-1.0 (逻辑自洽性，低于0.7说明有明显的逻辑问题),
    "depth_score": 0.0-1.0 (深度/原创性，低于0.6说明内容过于浅显),
    "clarity_score": 0.0-1.0 (表达清晰度),
    "is_generic": true/false (是否使用了泛化的废话，如"一般来说"、"通常情况下"),
    "critique": "具体指出2-3个最严重的问题，使用简洁有力的语言",
    "recursive_advice": "下次生成类似内容时，必须注意的1-2个核心改进点"
}}

只返回 JSON，不要其他文字。"""

        try:
            # 调用 LLM 进行审计
            messages = [
                {"role": "system", "content": "你是一个严格的内容审计AI，只返回JSON。"},
                {"role": "user", "content": prompt}
            ]
            result = await self.client.structured_output(messages, {})

            if result:
                # 解析结果
                parsed = self._parse_audit_result(result)
                logger.info(f"[元认知] 审计完成: logic={parsed['logic_score']:.2f}, depth={parsed['depth_score']:.2f}, generic={parsed['is_generic']}")
                return parsed
            else:
                logger.warning("[元认知] LLM 返回为空，使用默认评分")
                return self._default_reflection()

        except Exception as e:
            logger.error(f"[元认知] 审计失败: {e}")
            return self._default_reflection()

    async def reflect_batch(self, contents: list, context: str = "") -> list:
        """
        批量审计多个内容
        
        Args:
            contents: 内容列表
            context: 共享的上下文
            
        Returns:
            审计结果列表
        """
        tasks = [self.reflect(content, context) for content in contents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"[元认知] 批量审计第{i+1}项失败: {result}")
                processed.append(self._default_reflection())
            else:
                processed.append(result)
                
        return processed

    async def recursive_refine(
        self,
        original_prompt: str,
        last_reflection: Dict[str, Any],
        previous_content: str = ""
    ) -> str:
        """
        根据反思结果重写内容（递归修正）
        
        Args:
            original_prompt: 用户的原始请求
            last_reflection: 上一次的反思结果
            previous_content: 上一次生成的内容（供参考）
            
        Returns:
            优化后的内容
        """
        refine_prompt = f"""你是一个追求极致质量的 AI 内容生成器。

用户原始请求：{original_prompt}

基于你上一次的失败反思：
"{last_reflection['critique']}"

以及改进策略：
"{last_reflection['recursive_advice']}"

{'上一次生成的内容（需要改进）：' + previous_content if previous_content else ''}

请重新生成内容，要求：
1. 必须避开上述缺陷
2. 追求极高的逻辑精准度
3. 禁止使用任何泛化的废话
4. 直接给出高质量的答案，不要有铺垫

只返回内容本身，不要有"下面是..."之类的开场白。"""

        try:
            result = self.client.chat(
                message=refine_prompt,
                system="你是一个追求极致质量的内容生成器。直接、有深度、不说废话。"
            )
            logger.info(f"[元认知] 完成递归修正")
            return result
        except Exception as e:
            logger.error(f"[元认知] 递归修正失败: {e}")
            return previous_content  # 返回原始内容

    async def reflective_generate(
        self,
        prompt: str,
        context: str = "",
        auto_refine: bool = True
    ) -> Dict[str, Any]:
        """
        带元认知的生成流程
        
        这是对外的主要接口，封装了"生成->审计->可能修正"的完整流程。
        
        Args:
            prompt: 生成内容的提示
            context: 上下文信息
            auto_refine: 是否自动修正低质量内容
            
        Returns:
            {{
                "content": 最终内容,
                "reflection": 反思结果,
                "was_refined": 是否经过修正,
                "iterations": 迭代次数
            }}
        """
        # 第一次生成
        logger.info("[元认知] 开始生成内容...")
        content = await self._generate_content(prompt)
        
        # 审计
        reflection = await self.reflect(content, context)
        
        iterations = 1
        was_refined = False
        
        # 如果启用了自动修正且评分过低
        if auto_refine and (reflection['logic_score'] < self.DEFAULT_LOGIC_THRESHOLD 
                           or reflection['is_generic']):
            logger.info(f"[元认知] 内容评分过低，开始递归修正...")
            
            for i in range(self.MAX_REFLECTION_ITERATIONS):
                # 递归修正
                new_content = await self.recursive_refine(prompt, reflection, content)
                
                # 再次审计
                new_reflection = await self.reflect(new_content, context)
                
                # 检查是否达标
                if (new_reflection['logic_score'] >= self.DEFAULT_LOGIC_THRESHOLD 
                    and not new_reflection['is_generic']
                    and new_reflection['depth_score'] >= self.DEFAULT_DEPTH_THRESHOLD):
                    content = new_content
                    reflection = new_reflection
                    was_refined = True
                    iterations = i + 2
                    logger.info(f"[元认知] 第{i+1}次修正成功，评分达标")
                    break
                else:
                    # 更新反思结果，继续迭代
                    reflection = new_reflection
                    content = new_content
                    was_refined = True
                    iterations = i + 2
                    logger.warning(f"[元认知] 第{i+1}次修正后评分仍偏低，继续...")

        return {
            "content": content,
            "reflection": reflection,
            "was_refined": was_refined,
            "iterations": iterations
        }

    async def _generate_content(self, prompt: str) -> str:
        """内部：生成内容"""
        try:
            return self.client.chat(
                message=prompt,
                system="你是一个知识渊博、表达清晰的助手。"
            )
        except Exception as e:
            logger.error(f"[元认知] 内容生成失败: {e}")
            return ""

    def _parse_audit_result(self, raw: Dict) -> Dict:
        """解析审计结果，提供默认值"""
        return {
            "logic_score": max(0.0, min(1.0, raw.get("logic_score", 0.5))),
            "depth_score": max(0.0, min(1.0, raw.get("depth_score", 0.5))),
            "clarity_score": max(0.0, min(1.0, raw.get("clarity_score", 0.5))),
            "is_generic": raw.get("is_generic", False),
            "critique": raw.get("critique", "无批评意见"),
            "recursive_advice": raw.get("recursive_advice", "")
        }

    def _default_reflection(self) -> Dict:
        """默认反思结果（当LLM调用失败时）"""
        return {
            "logic_score": 0.5,
            "depth_score": 0.5,
            "clarity_score": 0.5,
            "is_generic": False,
            "critique": "LLM调用失败，无法进行审计",
            "recursive_advice": "检查LLM服务是否正常"
        }


# ===== 数据库操作 =====

async def save_reflection(db_session, reflection_data: Dict, target_id: str, target_type: str):
    """
    保存反思记录到数据库
    
    Args:
        db_session: 数据库会话
        reflection_data: 反思结果
        target_id: 关联目标ID
        target_type: 目标类型
    """
    from sqlalchemy import select
    from db.models import MetaReflection

    # 查找是否已有相关反思
    result = await db_session.execute(
        select(MetaReflection)
        .where(MetaReflection.target_id == str(target_id))
        .where(MetaReflection.target_type == target_type)
        .order_by(MetaReflection.reflection_count.desc())
    )
    existing = result.scalar_one_or_none()

    if existing:
        # 更新已有记录
        existing.logic_score = reflection_data.get("logic_score", 0.5)
        existing.depth_score = reflection_data.get("depth_score", 0.5)
        existing.clarity_score = reflection_data.get("clarity_score", 0.5)
        existing.is_generic = reflection_data.get("is_generic", False)
        existing.critique = reflection_data.get("critique", "")
        existing.recursive_advice = reflection_data.get("recursive_advice", "")
        existing.reflection_count = existing.reflection_count + 1
        existing.updated_at = datetime.utcnow()
    else:
        # 创建新记录
        new_reflection = MetaReflection(
            target_id=str(target_id),
            target_type=target_type,
            logic_score=reflection_data.get("logic_score", 0.5),
            depth_score=reflection_data.get("depth_score", 0.5),
            clarity_score=reflection_data.get("clarity_score", 0.5),
            is_generic=reflection_data.get("is_generic", False),
            critique=reflection_data.get("critique", ""),
            recursive_advice=reflection_data.get("recursive_advice", ""),
            final_content=reflection_data.get("final_content", ""),
        )
        db_session.add(new_reflection)

    await db_session.commit()


async def get_recent_reflections(db_session, target_type: str = None, limit: int = 10):
    """
    获取最近的反思记录
    
    Args:
        db_session: 数据库会话
        target_type: 目标类型过滤
        limit: 返回数量
        
    Returns:
        反思记录列表
    """
    from sqlalchemy import select, desc
    from db.models import MetaReflection

    query = select(MetaReflection).order_by(desc(MetaReflection.created_at))
    
    if target_type:
        query = query.where(MetaReflection.target_type == target_type)
    
    query = query.limit(limit)
    
    result = await db_session.execute(query)
    return result.scalars().all()


async def get_improvement_advice(db_session, target_type: str) -> str:
    """
    获取针对某类目标的改进建议（用于优化 System Prompt）
    
    Args:
        db_session: 数据库会话
        target_type: 目标类型
        
    Returns:
        合并的改进建议字符串
    """
    from sqlalchemy import select, desc
    from db.models import MetaReflection

    result = await db_session.execute(
        select(MetaReflection)
        .where(MetaReflection.target_type == target_type)
        .where(MetaReflection.recursive_advice.isnot(None))
        .order_by(desc(MetaReflection.created_at))
        .limit(5)
    )
    reflections = result.scalars().all()

    if not reflections:
        return ""

    # 合并所有改进建议
    advice_list = [r.recursive_advice for r in reflections if r.recursive_advice]
    return " | ".join(advice_list)


# ===== 便捷函数 =====

def get_meta_engine() -> MetaCognitiveEngine:
    """获取元认知引擎实例"""
    return MetaCognitiveEngine()
