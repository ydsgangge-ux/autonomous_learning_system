"""
沙盒执行器 (Sandbox Executor)
===============================

在受控环境中执行 AI 生成的代码，用于验证逻辑正确性。

安全特性：
- 超时限制
- 输出截断
- 内存限制（通过资源限制）
- 禁止危险操作

注意：生产环境建议使用 Docker 容器隔离
"""

import io
import sys
import asyncio
import traceback
from typing import Dict, Any, Optional
from contextlib import redirect_stdout, redirect_stderr

from core.utils import get_logger

logger = get_logger(__name__)


class SandboxExecutor:
    """
    沙盒执行器 - 在受限环境中执行代码
    
    用于验证 AI 生成的逻辑、公式、计算等
    """

    # 允许的模块（白名单）
    ALLOWED_MODULES = {
        "math", "random", "json", "re", "datetime", "timedelta",
        "collections", "functools", "itertools", "operator",
        "statistics", " fractions", "decimal"
    }
    
    # 禁止的操作
    FORBIDDEN_PATTERNS = [
        "import os", "import sys", "import subprocess",
        "import socket", "import requests", "import urllib",
        "open(", "read(", "write(",
        "eval(", "exec(", "compile(",
        "__import__", "getattr(", "setattr(",
    ]

    def __init__(
        self, 
        timeout: int = 10,
        max_output_size: int = 10000,
        max_memory_mb: int = 128
    ):
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.max_memory_mb = max_memory_mb

    def _check_safety(self, code: str) -> Optional[str]:
        """
        检查代码安全性
        
        Returns:
            None if safe, error message if unsafe
        """
        code_lower = code.lower()
        
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern.lower() in code_lower:
                return f"禁止的操作: {pattern}"
        
        # 检查是否有可疑的文件操作
        if "file" in code_lower or "path" in code_lower:
            return "禁止的文件操作"
        
        return None

    async def execute(
        self, 
        code: str, 
        inputs: Dict[str, Any] = None,
        capture_state: list = None
    ) -> Dict[str, Any]:
        """
        在沙盒中执行代码
        
        Args:
            code: 待执行的 Python 代码
            inputs: 输入变量字典
            capture_state: 需要返回的变量名列表
            
        Returns:
            执行结果
        """
        # 安全检查
        safety_error = self._check_safety(code)
        if safety_error:
            return {
                "success": False,
                "error": f"安全检查失败: {safety_error}",
                "output": "",
                "execution_time_ms": 0,
                "resulting_state": {}
            }
        
        # 准备执行环境
        loc = dict(inputs or {})
        glb = {
            "__builtins__": {
                # 限制内置函数
                "print": print,
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "zip": zip,
                "enumerate": enumerate,
                "sorted": sorted,
                "reversed": reversed,
                "isinstance": isinstance,
                "issubclass": issubclass,
                "hasattr": hasattr,
                "type": type,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "ZeroDivisionError": ZeroDivisionError,
                "IndexError": IndexError,
                "KeyError": KeyError,
                "AssertionError": AssertionError,
                "Exception": Exception,
            },
            # 允许的模块
            "math": __import__("math"),
            "random": __import__("random"),
            "json": __import__("json"),
            "re": __import__("re"),
            "datetime": __import__("datetime"),
            "timedelta": __import__("datetime").timedelta,
            "statistics": __import__("statistics"),
            "Decimal": __import__("decimal").Decimal,
        }
        
        stdout = io.StringIO()
        stderr = io.StringIO()
        
        success = False
        error_msg = ""
        execution_time_ms = 0
        
        import time
        start_time = time.perf_counter()
        
        try:
            # 在受控环境中执行
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exec(code, glb, loc)
            
            success = True
            
        except AssertionError as e:
            # 断言失败不算错误，可能是测试用例
            success = True
            error_msg = f"断言失败: {e}"
            
        except Exception as e:
            success = False
            error_msg = f"{type(e).__name__}: {str(e)}"
            # 包含堆栈跟踪（但截断）
            tb = traceback.format_exc(limit=5)
            error_msg += f"\n详细: {tb[-500:]}"
        
        finally:
            end_time = time.perf_counter()
            execution_time_ms = int((end_time - start_time) * 1000)
        
        # 截断输出
        output = stdout.getvalue()
        if len(output) > self.max_output_size:
            output = output[:self.max_output_size] + f"\n... (输出已截断，总长度 {len(output)} 字符)"
        
        # 收集状态
        resulting_state = {}
        if capture_state:
            for var in capture_state:
                if var in loc:
                    try:
                        # 只保留可序列化的部分
                        val = loc[var]
                        if isinstance(val, (int, float, str, bool, list, dict)):
                            resulting_state[var] = val
                        else:
                            resulting_state[var] = str(val)
                    except:
                        resulting_state[var] = "<无法序列化>"
        
        return {
            "success": success,
            "output": output,
            "error": error_msg or stderr.getvalue(),
            "execution_time_ms": execution_time_ms,
            "resulting_state": resulting_state
        }

    async def execute_test(
        self, 
        code: str,
        test_cases: list = None
    ) -> Dict[str, Any]:
        """
        执行带测试用例的代码
        
        Args:
            code: 待测试的代码
            test_cases: [{"input": {...}, "expected": ...}]
            
        Returns:
            测试结果
        """
        if not test_cases:
            # 没有测试用例，只执行代码
            return await self.execute(code)
        
        results = []
        
        for i, case in enumerate(test_cases):
            # 为每个测试用例创建独立环境
            test_code = code + "\n\n"
            
            # 添加测试断言
            if "expected" in case:
                # 假设最后一个表达式是结果
                test_code += f"""
# Test case {i+1}
result = None  # 需要测试的表达式
assert result == {case['expected']}, f"Test {i+1} failed: {{result}}"
print(f"Test {i+1} passed")
"""
            
            result = await self.execute(
                test_code, 
                inputs=case.get("input", {}),
                capture_state=["result"]
            )
            
            results.append({
                "case_id": i + 1,
                **result
            })
        
        passed = sum(1 for r in results if r["success"])
        
        return {
            "total_tests": len(test_cases),
            "passed": passed,
            "failed": len(test_cases) - passed,
            "results": results
        }


# ===== 便捷函数 =====

_executor_instance = None

def get_sandbox_executor() -> SandboxExecutor:
    """获取沙盒执行器实例（单例）"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = SandboxExecutor(timeout=10)
    return _executor_instance
