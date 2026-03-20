"""
自主验证器 (Autonomous Verifier)
=================================

将"因果推理"与"沙盒验证"结合，让系统能够自主验证假设。

工作流程：
1. 接收假设/知识
2. 生成验证脚本
3. 沙盒执行
4. 分析结果
5. 与元认知模块集成（触发反思）
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.sandbox import get_sandbox_executor, SandboxExecutor
from llm_client import LLMClient, get_client
from core.utils import get_logger

logger = get_logger(__name__)


class AutonomousVerifier:
    """
    自主验证器
    
    核心功能：
    1. 为假设生成验证脚本
    2. 沙盒执行验证
    3. 分析实验结果
    4. 与元认知集成，触发自我反思
    """

    def __init__(self, client: LLMClient = None, sandbox: SandboxExecutor = None):
        self.llm = client or get_client()
        self.sandbox = sandbox or get_sandbox_executor()

    async def verify_knowledge(
        self,
        knowledge_content: str,
        knowledge_type: str = "formula",
        context: str = ""
    ) -> Dict[str, Any]:
        """
        验证知识卡片中的内容
        
        Args:
            knowledge_content: 知识内容（如公式、逻辑）
            knowledge_type: 类型：formula, logic, calculation, code
            context: 上下文信息
            
        Returns:
            验证结果
        """
        logger.info(f"[验证器] 开始验证: {knowledge_type}")
        
        # 1. 生成验证脚本
        code = await self._generate_verification_code(
            knowledge_content, 
            knowledge_type,
            context
        )
        
        if not code:
            return {
                "success": False,
                "error": "无法生成验证脚本"
            }
        
        # 2. 执行验证
        result = await self.sandbox.execute(
            code,
            capture_state=["result", "verified", "test_results"]
        )
        
        # 3. 分析结果
        analysis = await self._analyze_result(
            knowledge_content,
            code,
            result
        )
        
        return {
            "verified": result["success"],
            "knowledge_type": knowledge_type,
            "code": code,
            "execution_result": result,
            "analysis": analysis
        }

    async def verify_hypothesis(
        self,
        hypothesis: str,
        domain: str = "general"
    ) -> Dict[str, Any]:
        """
        验证科学假设
        
        Args:
            hypothesis: 假设描述
            domain: 领域
            
        Returns:
            验证结果
        """
        # 1. 生成验证脚本
        code = await self._generate_hypothesis_test(hypothesis, domain)
        
        if not code:
            return {
                "success": False,
                "error": "无法生成测试代码"
            }
        
        # 2. 执行
        result = await self.sandbox.execute(
            code,
            capture_state=["hypothesis", "result", "conclusion"]
        )
        
        # 3. 得出结论
        conclusion = self._extract_conclusion(result)
        
        return {
            "hypothesis": hypothesis,
            "domain": domain,
            "code": code,
            "execution": result,
            "conclusion": conclusion,
            "requires_review": not result["success"]
        }

    async def _generate_verification_code(
        self,
        knowledge_content: str,
        knowledge_type: str,
        context: str
    ) -> Optional[str]:
        """生成验证脚本"""
        
        prompts = {
            "formula": f"""请为以下公式生成 Python 验证代码。

公式: {knowledge_content}
上下文: {context}

要求：
1. 使用多个测试用例验证公式在不同输入下的正确性
2. 包含断言检查预期结果
3. 输出验证结果

只输出代码，不要其他文字。""",

            "logic": f"""请为以下逻辑生成 Python 验证代码。

逻辑: {knowledge_content}
上下文: {context}

要求：
1. 将逻辑转化为可执行的测试
2. 覆盖边界情况
3. 输出验证结果

只输出代码，不要其他文字。""",

            "calculation": f"""请为以下计算逻辑生成 Python 验证代码。

计算: {knowledge_content}
上下文: {context}

要求：
1. 验证计算逻辑的正确性
2. 包含多个测试用例
3. 输出验证结果

只输出代码，不要其他文字。""",
            
            "code": f"""请为以下代码逻辑生成 Python 验证测试。

代码逻辑: {knowledge_content}
上下文: {context}

要求：
1. 执行代码并验证输出
2. 检查边界情况
3. 输出验证结果

只输出代码，不要其他文字。"""
        }
        
        prompt = prompts.get(knowledge_type, prompts["logic"])
        
        try:
            result = self.llm.chat(
                message=prompt,
                system="你是一个专业的代码验证专家。只输出代码，不要解释。"
            )
            
            # 提取代码块
            code = self._extract_code(result)
            return code
            
        except Exception as e:
            logger.error(f"[验证器] 生成验证代码失败: {e}")
            return None

    async def _generate_hypothesis_test(
        self,
        hypothesis: str,
        domain: str
    ) -> Optional[str]:
        """生成假设测试代码"""
        
        prompt = f"""现有一个科学假设："{hypothesis}"

领域: {domain}

请编写 Python 代码来验证这个假设。
要求：
1. 设计实验/测试用例
2. 包含断言验证假设
3. 输出结论

只输出代码，不要其他文字。"""
        
        try:
            result = self.llm.chat(
                message=prompt,
                system="你是一个科学实验设计专家。只输出代码，不要解释。"
            )
            
            return self._extract_code(result)
            
        except Exception as e:
            logger.error(f"[验证器] 生成假设测试失败: {e}")
            return None

    def _extract_code(self, text: str) -> str:
        """从LLM输出中提取代码"""
        import re
        
        # 尝试提取代码块
        code_block = re.search(r"```python\n(.*?)```", text, re.DOTALL)
        if code_block:
            return code_block.group(1)
        
        code_block = re.search(r"```\n(.*?)```", text, re.DOTALL)
        if code_block:
            return code_block.group(1)
        
        # 如果没有代码块，返回整个文本
        return text.strip()

    async def _analyze_result(
        self,
        knowledge_content: str,
        code: str,
        execution_result: Dict
    ) -> Dict[str, Any]:
        """分析验证结果"""
        
        if execution_result["success"]:
            return {
                "status": "verified",
                "message": "验证通过",
                "output": execution_result.get("output", "")[:500],
                "confidence": "high" if execution_result["execution_time_ms"] < 1000 else "medium"
            }
        else:
            return {
                "status": "failed",
                "message": execution_result.get("error", "验证失败"),
                "requires_review": True,
                "reason": "可能是知识内容有误或测试用例设计不当"
            }

    def _extract_conclusion(self, result: Dict) -> str:
        """从执行结果提取结论"""
        
        if result["success"]:
            output = result.get("output", "").lower()
            
            if "pass" in output or "成功" in output or "correct" in output:
                return "假设可能成立"
            elif "fail" in output or "失败" in output:
                return "假设可能不成立"
            else:
                return "需要更多验证"
        else:
            return f"验证执行失败: {result.get('error', '未知错误')}"

    async def batch_verify(
        self,
        knowledge_items: List[Dict]
    ) -> List[Dict]:
        """
        批量验证多个知识项
        
        Args:
            knowledge_items: [{"content": ..., "type": ..., "context": ...}]
            
        Returns:
            验证结果列表
        """
        import asyncio
        
        tasks = [
            self.verify_knowledge(
                item["content"],
                item.get("type", "formula"),
                item.get("context", "")
            )
            for item in knowledge_items
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed.append({
                    "item_id": i,
                    "verified": False,
                    "error": str(result)
                })
            else:
                result["item_id"] = i
                processed.append(result)
        
        return processed


# ===== 数据库操作 =====

async def save_verification_log(db_session, verification_result: Dict):
    """保存验证日志"""
    from db.models import Base
    # 可以扩展 db/models.py 添加验证日志表
    pass


# ===== 便捷函数 =====

def get_verifier() -> AutonomousVerifier:
    """获取验证器实例"""
    return AutonomousVerifier()
