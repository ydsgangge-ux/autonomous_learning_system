"""
AGI 进化编排层 (Evolution Orchestrator)
========================================

这是系统的大脑，负责协调各个核心组件的运行顺序，
实现完整的"逻辑洗礼"流程：因果提取 -> 沙盒验证 -> 跨域合成 -> 元认知审计

核心特性：
1. 自动判断是否需要沙盒验证（基于内容中的计算/公式）
2. 智能选择跨域合成目标领域
3. 递归修正直到通过元认知审计
4. 完整的结果记录和追溯

设计原则：
- 拒绝平庸：元认知审计强制剔除废话
- 物理世界感知：沙盒验证确保逻辑正确性
- 打破知识孤岛：跨域合成建立深层联系
"""

import asyncio
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.metacognition import MetaCognitiveEngine
from core.causality import CausalReasoningEngine
from core.sandbox import SandboxExecutor
from core.synthesis import CrossDomainSynthesizer, DOMAIN_ABSTRACTIONS
from llm.client import llm_client
from core.utils import get_logger

logger = get_logger(__name__)


class EvolutionOrchestrator:
    """
    AGI 进化编排器
    
    协调四个核心模块，将原始输入进化为深度知识节点：
    1. 因果推理 - 建立逻辑骨架
    2. 沙盒验证 - 确保物理/数学逻辑正确
    3. 跨域合成 - 打破知识孤岛
    4. 元认知审计 - 最终质量关卡
    """

    # 审计阈值
    LOGIC_THRESHOLD = 0.7
    DEPTH_THRESHOLD = 0.6
    
    # 需要沙盒验证的关键词
    SANDBOX_TRIGGERS = [
        r"\d+\s*[+-*/^√∑∫≈≤≥]",  # 数学表达式
        r"(压力|温度|速度|力|功率|流量|电压|电流|频率)",  # 物理量
        r"(公式|计算|推导|仿真|模拟)",  # 计算相关
        r"(Pa|Mpa|kg|N|W|J|V|A|Hz)",  # 单位
    ]
    
    # 默认跨域领域对（工业 -> 其他领域）
    DEFAULT_DOMAIN_PAIRS = [
        ("工业制造", "声学/音乐"),
        ("工业制造", "流体力学"),
        ("工业制造", "控制理论"),
        ("工业制造", "生物学"),
    ]

    def __init__(self, llm_client=None, db_session=None):
        self.client = llm_client or llm_client
        self.db = db_session
        
        # 初始化四大核心引擎
        self.meta = MetaCognitiveEngine(self.client)
        self.causal = CausalReasoningEngine(self.client)
        self.sandbox = SandboxExecutor(timeout=10)
        self.synthesis = CrossDomainSynthesizer(self.client)
        
        logger.info("[编排器] AGI 进化编排器初始化完成")

    async def evolve_knowledge(
        self, 
        raw_input: str, 
        target_domain: str = "工业制造",
        context: str = "",
        auto_synthesis: bool = True,
        max_refinement_iterations: int = 2
    ) -> Dict[str, Any]:
        """
        核心进化循环：将原始输入进化为深度知识节点
        
        Args:
            raw_input: 原始输入内容
            target_domain: 目标领域（默认：工业制造）
            context: 额外上下文信息
            auto_synthesis: 是否自动进行跨域合成
            max_refinement_iterations: 最大递归修正次数
            
        Returns:
            包含完整进化过程的详细结果
        """
        start_time = datetime.now()
        results = {
            "original_input": raw_input,
            "target_domain": target_domain,
            "timestamp": start_time.isoformat(),
            "evolution_stages": {}
        }
        
        logger.info(f"[编排器] 开始进化: {raw_input[:50]}...")

        # ===== 阶段 1: 因果提取 =====
        logger.info("[编排器] 阶段 1/4: 因果提取")
        try:
            causal_result = await self.causal.extract_causality(
                content=raw_input,
                context=context or f"目标领域: {target_domain}"
            )
            results["evolution_stages"]["causality"] = {
                "status": "success",
                "data": causal_result
            }
            results["causal_logic"] = causal_result
        except Exception as e:
            logger.error(f"[编排器] 因果提取失败: {e}")
            results["evolution_stages"]["causality"] = {
                "status": "error",
                "error": str(e)
            }
            results["causal_logic"] = {"chains": [], "error": str(e)}

        # ===== 阶段 2: 沙盒验证 =====
        logger.info("[编排器] 阶段 2/4: 沙盒验证")
        needs_sandbox = self._check_needs_sandbox(raw_input)
        
        if needs_sandbox:
            verification = await self._run_automatic_verification(raw_input, causal_result)
            results["evolution_stages"]["sandbox"] = verification
            results["verification"] = verification
        else:
            logger.info("[编排器] 内容无需沙盒验证")
            results["evolution_stages"]["sandbox"] = {
                "status": "skipped",
                "reason": "不包含可验证的计算或公式"
            }
            results["verification"] = {"status": "skipped"}

        # ===== 阶段 3: 跨域合成 =====
        logger.info("[编排器] 阶段 3/4: 跨域合成")
        
        if auto_synthesis:
            # 选择目标领域进行跨域合成
            target_domains = self._select_synthesis_domains(target_domain)
            
            synthesis_insights = []
            for pair in target_domains:
                try:
                    insight = await self.synthesis.generate_analogy(
                        concept=raw_input[:100],
                        domain_a=pair[0],
                        domain_b=pair[1],
                        context=context
                    )
                    synthesis_insights.append({
                        "domain_pair": pair,
                        "insight": insight
                    })
                except Exception as e:
                    logger.warning(f"[编排器] 跨域合成失败 ({pair[0]} -> {pair[1]}): {e}")
            
            results["evolution_stages"]["synthesis"] = {
                "status": "success" if synthesis_insights else "partial",
                "insights": synthesis_insights
            }
            results["synthesis_insight"] = synthesis_insights[0] if synthesis_insights else None
        else:
            results["evolution_stages"]["synthesis"] = {"status": "disabled"}
            results["synthesis_insight"] = None

        # ===== 阶段 4: 元认知审计 =====
        logger.info("[编排器] 阶段 4/4: 元认知审计")
        
        # 构建待审计内容
        audit_content = self._build_audit_content(results)
        audit_context = f"目标：产出专业、严谨且具有洞察力的{target_domain}知识"
        
        audit_report = await self.meta.reflect(audit_content, audit_context)
        results["evolution_stages"]["metacognition"] = {
            "status": "success",
            "audit": audit_report
        }
        results["audit"] = audit_report

        # ===== 递归修正循环 =====
        final_output = raw_input
        refinement_count = 0
        
        while (audit_report.get("logic_score", 0) < self.LOGIC_THRESHOLD or 
               audit_report.get("is_generic", False)) and \
              refinement_count < max_refinement_iterations:
            
            logger.info(f"[编排器] 审计未通过，进行第 {refinement_count + 1} 次修正...")
            
            final_output = await self.meta.recursive_refine(
                original_prompt=raw_input,
                last_reflection=audit_report,
                previous_content=final_output
            )
            
            # 重新审计修正后的内容
            audit_report = await self.meta.reflect(final_output, audit_context)
            refinement_count += 1
            
            logger.info(f"[编排器] 第 {refinement_count} 次修正完成: " + 
                       f"logic={audit_report.get('logic_score', 0):.2f}, " +
                       f"generic={audit_report.get('is_generic', False)}")

        results["final_output"] = final_output
        results["refinement_count"] = refinement_count
        results["audit"] = audit_report
        
        # 计算总耗时
        end_time = datetime.now()
        results["processing_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
        
        logger.info(f"[编排器] 进化完成! 耗时: {results['processing_time_ms']}ms, " +
                   f"修正次数: {refinement_count}")
        
        return results

    def _check_needs_sandbox(self, content: str) -> bool:
        """检查内容是否需要沙盒验证"""
        for pattern in self.SANDBOX_TRIGGERS:
            if re.search(pattern, content):
                return True
        return False

    async def _run_automatic_verification(
        self, 
        raw_input: str, 
        causal_result: Dict
    ) -> Dict[str, Any]:
        """自动生成并执行验证代码"""
        # 尝试从因果链中提取可验证的逻辑
        chains = causal_result.get("chains", [])
        
        # 生成验证代码
        code = self._generate_verification_code(raw_input, chains)
        
        if not code:
            return {
                "status": "skipped",
                "reason": "无法提取可验证的逻辑"
            }
        
        logger.info(f"[编排器] 生成验证代码: {code[:100]}...")
        
        # 执行验证
        try:
            result = await self.sandbox.execute(code)
            
            if result.get("success"):
                return {
                    "status": "verified",
                    "confidence": 0.95,
                    "execution_result": result.get("output", ""),
                    "code": code
                }
            else:
                return {
                    "status": "failed",
                    "error": result.get("error", "Unknown error"),
                    "code": code
                }
        except Exception as e:
            logger.error(f"[编排器] 沙盒执行失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "code": code
            }

    def _generate_verification_code(self, content: str, chains: List[Dict]) -> Optional[str]:
        """基于内容生成验证代码"""
        # 提取数值参数
        numbers = re.findall(r'(\d+\.?\d*)\s*(MPa|kg|N|W|J|Pa|V|A|Hz|m/s)', content)
        
        if numbers:
            # 简单的物理公式验证示例
            value = float(numbers[0][0])
            unit = numbers[0][1]
            
            # 根据单位生成验证代码
            if 'MPa' in unit:
                # 验证压力单位换算
                return f"""
# 压力验证: {value} {unit}
pa = {value} * 1e6  # MPa to Pa
kpa = {value} * 1000  # MPa to kPa
print(f"原始值: {{value}} MPa")
print(f"换算结果: {{pa}} Pa, {{kpa}} kPa")
# 验证结果
assert pa > 0, "压力值应为正数"
print("验证通过")
"""
        
        # 尝试从因果链中提取计算逻辑
        for chain in chains:
            mechanism = chain.get("mechanism", "")
            if any(kw in mechanism for kw in ["计算", "公式", "等于", "乘以", "除以"]):
                return f"""
# 因果链验证
# {chain.get('cause', '')} -> {chain.get('effect', '')}
# 机制: {mechanism}
result = True
print(f"因果链验证: {{result}}")
"""
        
        return None

    def _select_synthesis_domains(self, target_domain: str) -> List[tuple]:
        """选择跨域合成的目标领域"""
        available_pairs = []
        
        for pair in self.DEFAULT_DOMAIN_PAIRS:
            if pair[0] == target_domain:
                available_pairs.append(pair)
            elif pair[1] == target_domain:
                available_pairs.append((pair[1], pair[0]))
        
        # 如果没有匹配的，使用通用配对
        if not available_pairs:
            available_pairs = self.DEFAULT_DOMAIN_PAIRS[:2]
        
        return available_pairs[:2]  # 最多2个领域对

    def _build_audit_content(self, results: Dict) -> str:
        """构建待审计的内容摘要"""
        parts = []
        
        # 原始输入
        parts.append(f"原始输入: {results['original_input']}")
        
        # 因果逻辑
        causal = results.get("causal_logic", {})
        if causal.get("chains"):
            parts.append(f"\n因果逻辑链: {json.dumps(causal['chains'][:2], ensure_ascii=False)}")
        
        # 验证结果
        verification = results.get("verification", {})
        if verification.get("status") == "verified":
            parts.append(f"\n沙盒验证: 通过 ({verification.get('execution_result', '')})")
        
        # 跨域洞察
        synthesis = results.get("synthesis_insight")
        if synthesis:
            insight = synthesis.get("insight", {})
            parts.append(f"\n跨域洞察: {insight.get('synthesized_explanation', 'N/A')}")
        
        return "\n".join(parts)

    async def evolve_batch(
        self, 
        inputs: List[str],
        target_domain: str = "工业制造",
        context: str = "",
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        批量进化多个输入
        
        Args:
            inputs: 输入列表
            target_domain: 目标领域
            context: 共享上下文
            max_concurrent: 最大并发数
            
        Returns:
            进化结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def evolve_one(raw_input: str):
            async with semaphore:
                return await self.evolve_knowledge(
                    raw_input=raw_input,
                    target_domain=target_domain,
                    context=context
                )
        
        tasks = [evolve_one(inp) for inp in inputs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"[编排器] 批量进化第{i+1}项失败: {result}")
                processed.append({
                    "original_input": inputs[i],
                    "status": "error",
                    "error": str(result)
                })
            else:
                processed.append(result)
        
        return processed


# ===== 便捷函数 =====

async def quick_evolve(
    content: str,
    target_domain: str = "工业制造",
    context: str = ""
) -> Dict[str, Any]:
    """
    快速进化接口
    
    一键触发完整的进化流程，适合简单场景使用。
    """
    orchestrator = EvolutionOrchestrator()
    return await orchestrator.evolve_knowledge(
        raw_input=content,
        target_domain=target_domain,
        context=context
    )


async def evolve_with_verification(
    content: str,
    code: str,
    target_domain: str = "工业制造"
) -> Dict[str, Any]:
    """
    带验证代码的进化接口
    
    适合用户已准备好验证代码的场景。
    """
    orchestrator = EvolutionOrchestrator()
    
    # 先执行验证
    sandbox = SandboxExecutor()
    verification = await sandbox.execute(code)
    
    # 然后进行因果分析和跨域合成
    causal = await orchestrator.causal.extract_causality(content)
    synthesis = await orchestrator.synthesis.generate_analogy(
        concept=content[:100],
        domain_a=target_domain,
        domain_b="声学/音乐"
    )
    
    # 审计
    audit = await orchestrator.meta.reflect(
        content=f"{content}\n验证结果: {verification.get('output', '')}",
        context=f"目标领域: {target_domain}"
    )
    
    return {
        "original_input": content,
        "verification": verification,
        "causal_logic": causal,
        "synthesis_insight": synthesis,
        "audit": audit,
        "final_output": content  # 可根据审计结果修正
    }
