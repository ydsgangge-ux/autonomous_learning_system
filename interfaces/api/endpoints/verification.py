"""
验证系统 API 接口
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from db.session import get_db
from exploration.verifier import get_verifier, AutonomousVerifier
from core.sandbox import get_sandbox_executor

router = APIRouter()


# ===== 请求模型 =====

class VerifyKnowledgeRequest(BaseModel):
    """验证知识请求"""
    content: str
    knowledge_type: str = "formula"  # formula, logic, calculation, code
    context: str = ""


class VerifyHypothesisRequest(BaseModel):
    """验证假设请求"""
    hypothesis: str
    domain: str = "general"


class RunSandboxRequest(BaseModel):
    """沙盒执行请求"""
    code: str
    inputs: Optional[Dict[str, Any]] = {}
    capture_state: Optional[List[str]] = None


class BatchVerifyRequest(BaseModel):
    """批量验证请求"""
    items: List[Dict[str, Any]]  # [{"content": ..., "type": ..., "context": ...}]


# ===== API 端点 =====

@router.post("/verify/knowledge")
async def verify_knowledge(
    request: VerifyKnowledgeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    验证知识内容
    
    自动生成验证脚本并在沙盒中执行，检查知识是否正确。
    
    用法示例：
    ```json
    {
        "content": "R = ρ * L / A",
        "knowledge_type": "formula",
        "context": "电阻计算"
    }
    ```
    """
    verifier = get_verifier()
    
    result = await verifier.verify_knowledge(
        knowledge_content=request.content,
        knowledge_type=request.knowledge_type,
        context=request.context
    )
    
    return result


@router.post("/verify/hypothesis")
async def verify_hypothesis(
    request: VerifyHypothesisRequest
):
    """
    验证科学假设
    
    生成实验代码并执行，验证假设是否成立。
    
    用法示例：
    ```json
    {
        "hypothesis": "当温度升高时，金属的电阻会增加",
        "domain": "physics"
    }
    ```
    """
    verifier = get_verifier()
    
    result = await verifier.verify_hypothesis(
        hypothesis=request.hypothesis,
        domain=request.domain
    )
    
    return result


@router.post("/verify/batch")
async def batch_verify(
    request: BatchVerifyRequest
):
    """
    批量验证多个知识项
    
    用法示例：
    ```json
    {
        "items": [
            {"content": "F = ma", "type": "formula", "context": "物理学"},
            {"content": "欧姆定律", "type": "formula", "context": "电学"}
        ]
    }
    ```
    """
    verifier = get_verifier()
    
    results = await verifier.batch_verify(request.items)
    
    # 统计
    verified_count = sum(1 for r in results if r.get("verified", False))
    
    return {
        "total": len(results),
        "verified": verified_count,
        "failed": len(results) - verified_count,
        "results": results
    }


# ===== 沙盒执行接口 =====

@router.post("/sandbox/run")
async def run_sandbox(
    request: RunSandboxRequest
):
    """
    直接在沙盒中执行代码
    
    注意：这是危险操作，请确保代码来源可靠。
    系统会自动检查安全性。
    
    用法示例：
    ```json
    {
        "code": "result = 2 + 2\nprint(f'2 + 2 = {result}')",
        "capture_state": ["result"]
    }
    ```
    """
    sandbox = get_sandbox_executor()
    
    result = await sandbox.execute(
        code=request.code,
        inputs=request.inputs or {},
        capture_state=request.capture_state or []
    )
    
    return result


@router.post("/sandbox/test")
async def run_sandbox_test(
    request: RunSandboxRequest
):
    """
    在沙盒中执行带测试用例的代码
    
    用法示例：
    ```json
    {
        "code": "result = value * 2",
        "inputs": {"value": 5},
        "capture_state": ["result"]
    }
    ```
    """
    sandbox = get_sandbox_executor()
    
    # 自动创建测试用例
    test_cases = []
    if request.inputs:
        # 简单测试：输入 -> 输出
        test_cases.append({
            "input": request.inputs,
            "expected": None  # 不检查预期结果
        })
    
    result = await sandbox.execute_test(
        code=request.code,
        test_cases=test_cases
    )
    
    return result


# ===== 验证统计 =====

@router.get("/verify/stats")
async def get_verification_stats():
    """
    获取验证统计信息
    """
    # TODO: 从数据库读取验证历史
    return {
        "total_verifications": 0,
        "verified_count": 0,
        "failed_count": 0,
        "pending": 0
    }
