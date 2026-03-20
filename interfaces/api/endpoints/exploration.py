from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from db.session import get_db
from exploration.manager import run_exploration_cycle, get_pending_tasks
from background.task_runner import list_jobs
from exploration.causal_explorer import get_gap_detector
from core.causality import get_causal_engine

router = APIRouter()


@router.post("/run")
async def trigger_exploration(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger an exploration cycle."""
    count = await run_exploration_cycle(db)
    return {"status": "complete", "tasks_created": count}


@router.get("/tasks")
async def list_exploration_tasks(db: AsyncSession = Depends(get_db)):
    """List pending exploration tasks."""
    tasks = await get_pending_tasks(db)
    return {
        "tasks": [
            {"id": t.id, "topic": t.topic, "gap_reason": t.gap_reason, "status": t.status.value}
            for t in tasks
        ]
    }


@router.get("/scheduler/jobs")
async def get_scheduler_jobs():
    """List scheduled background jobs."""
    return {"jobs": list_jobs()}


# ==================== 因果推理接口 ====================

class ExtractCausalRequest(BaseModel):
    content: str
    context: str = ""


@router.post("/causal/extract")
async def extract_causality(
    request: ExtractCausalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    从文本中提取因果关系
    
    用法：
    POST /api/v1/exploration/causal/extract
    {
        "content": "当模具温度升高时，原材料的粘度会下降，流动性增加...",
        "context": "注塑工艺"
    }
    """
    engine = get_causal_engine()
    result = await engine.extract_causality(
        content=request.content,
        context=request.context,
        source_type="api"
    )
    return result


@router.get("/causal/query")
async def counterfactual_query(
    node: str,
    depth: int = 3
):
    """
    反事实推理查询
    
    用法：
    GET /api/v1/exploration/causal/query?node=模具温度&depth=3
    """
    engine = get_causal_engine()
    result = engine.counterfactual_query(node, depth)
    return result


@router.get("/causal/gaps")
async def detect_causal_gaps(
    domain: str = None,
    min_cluster_size: int = 2
):
    """
    检测因果缺口
    
    用法：
    GET /api/v1/exploration/causal/gaps?domain=注塑工艺&min_cluster_size=2
    """
    detector = get_gap_detector()
    result = await detector.detect_gaps(domain, min_cluster_size)
    return result


@router.get("/causal/gaps/{gap_type}/task")
async def generate_bridge_task(
    gap_type: str = "ISOLATED_CLUSTER",
    cause: str = "",
    effect: str = "",
    mechanism: str = "",
    strength: float = 0.5
):
    """
    根据缺口生成桥接任务
    
    用法：
    GET /api/v1/exploration/causal/gaps/ISOLATED_CLUSTER/task
    """
    detector = get_gap_detector()
    
    # 构建假想的 gap 对象
    if gap_type == "ISOLATED_CLUSTER":
        gap = {
            "type": "ISOLATED_CLUSTER",
            "cluster": [cause, effect] if cause and effect else ["概念A", "概念B"],
            "description": f"发现孤立的逻辑簇"
        }
    elif gap_type == "WEAK_CAUSALITY":
        gap = {
            "type": "WEAK_CAUSALITY",
            "link": {"cause": cause, "effect": effect, "mechanism": mechanism, "strength": strength},
            "description": f"因果链强度较弱"
        }
    else:
        gap = {
            "type": gap_type,
            "description": "因果冲突",
            "conflict": {"message": "检测到逻辑冲突"}
        }
    
    task = await detector.generate_bridge_task(gap)
    return task


@router.get("/causal/stats")
async def get_causal_stats():
    """获取因果图谱统计"""
    engine = get_causal_engine()
    return engine.get_statistics()


@router.get("/causal/conflicts")
async def detect_conflicts():
    """检测因果冲突"""
    engine = get_causal_engine()
    conflicts = engine.detect_conflicts()
    return {"conflicts": conflicts, "count": len(conflicts)}
