"""
跨域知识融合引擎 (Cross-Domain Synthesis Engine)
================================================

这是系统的"跨域神经网络"，负责将不同领域的知识进行抽象融合。

核心功能：
1. 跨域类比生成 - 在迥异领域间建立结构化类比
2. 抽象原理提取 - 剥离具体现象，提取第一性原理
3. 融合效果评估 - 根据用户反馈优化融合质量

设计原则：
- 严禁平庸类比 - 必须触及深层结构共性
- 强调启发性 - 帮助用户理解本质，而非简单比喻
- 隐私保护 - 跨域融合应无痕运行，不暴露用户兴趣
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from llm.client import llm_client
from core.utils import get_logger

logger = get_logger(__name__)


# 预定义领域及其抽象特征
DOMAIN_ABSTRACTIONS = {
    "工业制造": {
        "抽象特征": ["压力控制", "能量流动", "材料变形", "热传导", "应力分布"],
        "典型概念": ["注塑", "冲压", "焊接", "铸造", "加工中心"]
    },
    "声学/音乐": {
        "抽象特征": ["振幅包络", "频率响应", "共振", "阻尼", "波形合成"],
        "典型概念": ["ADSR包络", "LFO调制", "滤波器", "混响", "合成器"]
    },
    "流体力学": {
        "抽象特征": ["压力梯度", "粘度", "层流/湍流", "表面张力", "伯努利原理"],
        "典型概念": ["管道流", "喷雾", "液压", "气泡", "液滴"]
    },
    "控制理论": {
        "抽象特征": ["反馈回路", "PID控制", "滞后补偿", "振荡抑制", "响应曲线"],
        "典型概念": ["伺服系统", "自动驾驶", "机器人", "无人机", "PLC"]
    },
    "生物学": {
        "抽象特征": ["反馈调节", "适应性", "新陈代谢", "信号传导", "稳态"],
        "典型概念": ["神经网络", "免疫系统", "进化", "激素调节", "细胞呼吸"]
    },
    "电子电路": {
        "抽象特征": ["阻抗匹配", "信号放大", "滤波", "振荡", "调制"],
        "典型概念": ["放大器", "振荡器", "滤波器", "调制解调", "电源"]
    },
    "纺织/材料": {
        "抽象特征": ["张力控制", "应力应变", "编织结构", "弹性模量", "疲劳寿命"],
        "典型概念": ["织机", "纺丝", "复合材料", "张力传感器", "弯曲刚度"]
    },
    "文学/艺术": {
        "抽象特征": ["叙事结构", "情感曲线", "节奏", "张力构建", "主题呼应"],
        "典型概念": ["小说", "诗歌", "戏剧", "绘画", "音乐作品"]
    }
}


class CrossDomainSynthesizer:
    """
    跨域合成引擎

    负责在不同领域间建立深层结构化类比，
    提取第一性原理，帮助用户理解复杂概念。
    """

    def __init__(self, client=None):
        self.client = client or llm_client

    async def generate_analogy(
        self,
        concept: str,
        domain_a: str,
        domain_b: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        在两个迥异的领域间建立结构化类比

        Args:
            concept: 核心概念
            domain_a: 源领域（如：工业制造）
            domain_b: 目标领域（如：声学/音乐）
            context: 额外上下文

        Returns:
            包含抽象原理、映射表和融合解释的字典
        """
        prompt = f"""任务：跨域知识合成。

## 核心概念
- 概念："{concept}"
- 源领域：{domain_a}
- 目标领域：{domain_b}
- 上下文：{context if context else "无"}

## 执行步骤

### 1. 剥离 (Abstraction)
提取 "{concept}" 的底层物理或逻辑原理（第一性原理）。
不要描述表面现象，要深入到能量、信息、物质流动的本质。

### 2. 映射 (Mapping)
在 {domain_b} 中寻找具备相同原理的现象。
建立结构化映射表，明确说明哪些参数/特性可以对应。

### 3. 合成 (Synthesis)
创建一个深度的类比解释，帮助理解概念的本质。
解释应该具有启发性，能揭示跨学科的共性。

## 输出要求

- 严禁平庸的口水话（如"就像..."这样的简单比喻）
- 必须包含结构映射表
- 融合解释应该专业且深刻

## 输出 JSON 格式
{{
    "abstract_principle": "底层原理（1-2句话）",
    "abstraction_details": {{
        "能量形式": "描述",
        "控制机制": "描述",
        "系统参数": "描述"
    }},
    "mapping": {{
        "domain_a特征": "domain_b对应特征"
    }},
    "structural_similarity": 0.0-1.0,
    "synthesized_explanation": "融合后的深度解释（200-400字）",
    "insight": "一句话洞见"
}}

请直接返回 JSON，不要其他文字。"""

        try:
            messages = [
                {"role": "system", "content": "你是一个跨学科知识融合专家，擅长在不同领域间建立深层类比。"},
                {"role": "user", "content": prompt}
            ]

            result = await self.client.structured_output(messages, {})

            if result:
                # 验证返回结构
                return {
                    "success": True,
                    "concept": concept,
                    "source_domain": domain_a,
                    "target_domain": domain_b,
                    "abstract_principle": result.get("abstract_principle", ""),
                    "abstraction_details": result.get("abstraction_details", {}),
                    "mapping": result.get("mapping", {}),
                    "structural_similarity": result.get("structural_similarity", 0.5),
                    "synthesized_explanation": result.get("synthesized_explanation", ""),
                    "insight": result.get("insight", "")
                }
            else:
                return {"success": False, "error": "LLM返回为空"}

        except Exception as e:
            logger.error(f"[跨域合成] 生成类比失败: {e}")
            return {"success": False, "error": str(e)}

    async def auto_synthesize(
        self,
        concept: str,
        known_domains: List[str] = None,
        max_domains: int = 3
    ) -> List[Dict[str, Any]]:
        """
        自动跨域合成 - 自动选择最合适的领域进行融合

        Args:
            concept: 核心概念
            known_domains: 用户已知的领域（用于排除）
            max_domains: 最多融合的领域数

        Returns:
            多个跨域融合结果
        """
        # 过滤掉已知领域，选择陌生但相关的领域
        available_domains = [
            d for d in DOMAIN_ABSTRACTIONS.keys()
            if not known_domains or d not in known_domains
        ]

        results = []
        for domain in available_domains[:max_domains]:
            # 假设concept属于第一个domain，选择最相关的目标domain
            result = await self.generate_analogy(
                concept=concept,
                domain_a=known_domains[0] if known_domains else "工业制造",
                domain_b=domain,
                context=""
            )
            if result.get("success"):
                results.append(result)

        return results

    async def find_bridges(
        self,
        domain: str,
        concept: str,
        session: AsyncSession
    ) -> List[Dict]:
        """
        从数据库中查找已有的跨域桥接

        Args:
            domain: 领域
            concept: 概念
            session: 数据库会话

        Returns:
            已有桥接列表
        """
        from db.models import DomainBridge

        result = await session.execute(
            select(DomainBridge).where(
                (DomainBridge.source_domain == domain) |
                (DomainBridge.target_domain == domain)
            ).limit(10)
        )
        bridges = result.scalars().all()

        return [
            {
                "id": b.id,
                "source_domain": b.source_domain,
                "target_domain": b.target_domain,
                "source_concept": b.source_concept,
                "target_concept": b.target_concept,
                "abstract_principle": b.abstract_principle,
                "synthesis_efficacy": b.synthesis_efficacy
            }
            for b in bridges
        ]

    async def save_bridge(
        self,
        data: Dict,
        session: AsyncSession
    ) -> bool:
        """
        保存跨域桥接到数据库

        Args:
            data: 桥接数据
            session: 数据库会话

        Returns:
            是否成功
        """
        from db.models import DomainBridge

        try:
            bridge = DomainBridge(
                source_domain=data.get("source_domain", ""),
                target_domain=data.get("target_domain", ""),
                source_concept=data.get("concept", ""),
                target_concept=data.get("mapping", {}).get("对应概念", ""),
                abstract_principle=data.get("abstract_principle", ""),
                mapping_logic=data.get("mapping", {}),
                structural_mapping=data.get("abstraction_details", {}),
                synthesized_explanation=data.get("synthesized_explanation", "")
            )
            session.add(bridge)
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"[跨域合成] 保存桥接失败: {e}")
            await session.rollback()
            return False

    async def rate_synthesis(
        self,
        bridge_id: int,
        efficacy: float,
        session: AsyncSession
    ) -> bool:
        """
        对融合效果进行评分

        Args:
            bridge_id: 桥接ID
            efficacy: 效果评分 (0-1)
            session: 数据库会话

        Returns:
            是否成功
        """
        from db.models import DomainBridge

        try:
            result = await session.execute(
                select(DomainBridge).where(DomainBridge.id == bridge_id)
            )
            bridge = result.scalar_one_or_none()

            if bridge:
                # 累加评分
                bridge.feedback_count += 1
                bridge.synthesis_efficacy = (
                    (bridge.synthesis_efficacy * (bridge.feedback_count - 1) + efficacy)
                    / bridge.feedback_count
                )
                await session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"[跨域合成] 评分失败: {e}")
            await session.rollback()
            return False


# 全局单例
_synthesizer = None


def get_synthesizer() -> CrossDomainSynthesizer:
    """获取跨域合成器单例"""
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = CrossDomainSynthesizer()
    return _synthesizer
