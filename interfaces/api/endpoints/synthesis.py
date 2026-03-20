"""
跨域知识融合 API 接口
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from db.session import get_db
from core.synthesis import get_synthesizer, CrossDomainSynthesizer, DOMAIN_ABSTRACTIONS

router = APIRouter()


# ===== 请求模型 =====

class GenerateAnalogyRequest(BaseModel):
    """生成跨域类比请求"""
    concept: str
    source_domain: str
    target_domain: str
    context: str = ""


class AutoSynthesizeRequest(BaseModel):
    """自动跨域合成请求"""
    concept: str
    known_domains: Optional[List[str]] = None
    max_domains: int = 3


class RateSynthesisRequest(BaseModel):
    """评分请求"""
    bridge_id: int
    efficacy: float  # 0.0 - 1.0


class SearchBridgesRequest(BaseModel):
    """搜索桥接请求"""
    domain: Optional[str] = None
    concept: Optional[str] = None


# ===== API 端点 =====

@router.get("/domains")
async def list_domains():
    """
    获取可用的领域列表

    返回所有支持跨域融合的领域及其抽象特征。
    """
    domains = []
    for name, info in DOMAIN_ABSTRACTIONS.items():
        domains.append({
            "name": name,
            "abstract_features": info.get("抽象特征", []),
            "typical_concepts": info.get("典型概念", [])
        })

    return {
        "domains": domains,
        "count": len(domains)
    }


@router.post("/analogy")
async def generate_analogy(
    request: GenerateAnalogyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    生成跨域类比

    在两个不同领域间建立结构化类比，提取第一性原理。

    用法示例：
    ```json
    {
        "concept": "注塑保压过程",
        "source_domain": "工业制造",
        "target_domain": "声学/音乐",
        "context": "理解能量在模具中的流动与消散"
    }
    ```
    """
    synthesizer = get_synthesizer()

    result = await synthesizer.generate_analogy(
        concept=request.concept,
        domain_a=request.source_domain,
        domain_b=request.target_domain,
        context=request.context
    )

    if result.get("success"):
        # 保存到数据库
        await synthesizer.save_bridge(result, db)

    return result


@router.post("/auto")
async def auto_synthesize(
    request: AutoSynthesizeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    自动跨域合成

    自动选择多个相关领域进行跨域融合。

    用法示例：
    ```json
    {
        "concept": "压力控制",
        "known_domains": ["工业制造"],
        "max_domains": 3
    }
    ```
    """
    synthesizer = get_synthesizer()

    results = await synthesizer.auto_synthesize(
        concept=request.concept,
        known_domains=request.known_domains,
        max_domains=request.max_domains
    )

    # 保存所有结果
    for result in results:
        await synthesizer.save_bridge(result, db)

    return {
        "concept": request.concept,
        "syntheses": results,
        "count": len(results)
    }


@router.post("/rate")
async def rate_synthesis(
    request: RateSynthesisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    对跨域融合效果进行评分

    用法示例：
    ```json
    {
        "bridge_id": 1,
        "efficacy": 0.8
    }
    ```
    """
    if not 0.0 <= request.efficacy <= 1.0:
        raise HTTPException(status_code=400, detail="评分必须在0-1之间")

    synthesizer = get_synthesizer()
    success = await synthesizer.rate_synthesis(
        bridge_id=request.bridge_id,
        efficacy=request.efficacy,
        session=db
    )

    if success:
        return {"success": True, "message": "评分已保存"}
    else:
        raise HTTPException(status_code=404, detail="桥接不存在")


@router.get("/bridges")
async def search_bridges(
    domain: str = None,
    concept: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    搜索已有的跨域桥接

    用法：
    GET /api/v1/synthesis/bridges?domain=工业制造
    """
    synthesizer = get_synthesizer()

    if domain:
        bridges = await synthesizer.find_bridges(domain, concept or "", db)
    else:
        from db.models import DomainBridge
        result = await db.execute(select(DomainBridge).limit(20))
        bridges = result.scalars().all()
        bridges = [
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

    return {"bridges": bridges, "count": len(bridges)}


@router.get("/insights/random")
async def random_insight(
    db: AsyncSession = Depends(get_db)
):
    """
    获取随机跨域洞见

    用于展示系统的跨域联想能力。
    """
    synthesizer = get_synthesizer()

    # 预定义一些有趣的跨域洞见
    insights = [
        {
            "concept": "注塑保压",
            "domain_a": "工业制造",
            "domain_b": "声学/音乐",
            "insight": "保压阶段的压力衰减曲线与ADSR包络的Decay阶段本质相同——都是能量耗散的物理过程。"
        },
        {
            "concept": "线束应力",
            "domain_a": "材料工程",
            "domain_b": "乐器弦乐",
            "insight": "线束的弯曲疲劳与吉他弦的张力-频率关系都遵循胡克定律的数学本质。"
        },
        {
            "concept": "PID控制",
            "domain_a": "控制理论",
            "domain_b": "生物学",
            "insight": "PID控制器的积分项与人体稳态调节类似——都是通过累积误差来消除系统偏差。"
        },
        {
            "concept": "滤波电路",
            "domain_a": "电子电路",
            "domain_b": "流体力学",
            "insight": "低通滤波器对高频信号的衰减，与流体通过筛网的过滤效果遵循相似的频率选择原理。"
        }
    ]

    import random
    return random.choice(insights)


@router.get("/stats")
async def get_synthesis_stats(db: AsyncSession = Depends(get_db)):
    """获取跨域融合统计信息"""
    from db.models import DomainBridge
    from sqlalchemy import func

    result = await db.execute(
        select(
            func.count(DomainBridge.id).label("total"),
            func.avg(DomainBridge.synthesis_efficacy).label("avg_efficacy"),
            func.max(DomainBridge.synthesis_efficacy).label("max_efficacy")
        )
    )
    stats = result.one()

    # 按领域统计
    domain_result = await db.execute(
        select(DomainBridge.source_domain, func.count(DomainBridge.id))
        .group_by(DomainBridge.source_domain)
    )
    domain_counts = domain_result.all()

    return {
        "total_bridges": stats.total or 0,
        "average_efficacy": float(stats.avg_efficacy or 0),
        "max_efficacy": float(stats.max_efficacy or 0),
        "domain_distribution": {
            d: c for d, c in domain_counts
        }
    }
