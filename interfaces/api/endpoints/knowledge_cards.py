"""
知识卡片系统 API 接口
"""
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from db.session import get_db
from db.models import LearningGoal, KnowledgeCard
from knowledge.engine import KnowledgeEngine
from core.metacognition import MetaCognitiveEngine, save_reflection

router = APIRouter()
engine = KnowledgeEngine()
meta_engine = MetaCognitiveEngine()


# ===== Pydantic 模型 =====

class GoalCreate(BaseModel):
    description: str


class GoalResponse(BaseModel):
    id: int
    description: str
    goal_type: str
    unit_name: str
    estimated_count: Optional[int]
    total_units: int
    populated_count: int
    populated: bool
    created_at: str


class QuizSubmit(BaseModel):
    card_id: int
    answer: str
    response_time: float


class MasteryUpdate(BaseModel):
    card_id: int
    score: float
    response_time: float = 10.0


# ===== API 接口 =====

@router.post("/goals", response_model=GoalResponse)
async def create_goal(goal: GoalCreate, db: AsyncSession = Depends(get_db)):
    """创建学习目标"""
    # 分析目标
    meta = await engine.analyze_goal(goal.description)

    # 创建目标记录
    new_goal = LearningGoal(
        description=goal.description,
        goal_type=meta["goal_type"],
        card_template=meta["card_template"],
        unit_name=meta["unit_name"],
        estimated_count=meta["estimated_count"],
    )
    db.add(new_goal)
    await db.commit()
    await db.refresh(new_goal)

    return {
        "id": new_goal.id,
        "description": new_goal.description,
        "goal_type": new_goal.goal_type,
        "unit_name": new_goal.unit_name,
        "estimated_count": new_goal.estimated_count,
        "total_units": new_goal.total_units,
        "populated_count": new_goal.populated_count,
        "populated": new_goal.populated,
        "created_at": new_goal.created_at.isoformat(),
    }


@router.get("/goals", response_model=List[GoalResponse])
async def list_goals(db: AsyncSession = Depends(get_db)):
    """列出所有学习目标"""
    from sqlalchemy import select

    result = await db.execute(select(LearningGoal))
    goals = result.scalars().all()

    return [
        {
            "id": g.id,
            "description": g.description,
            "goal_type": g.goal_type,
            "unit_name": g.unit_name,
            "estimated_count": g.estimated_count,
            "total_units": g.total_units,
            "populated_count": g.populated_count,
            "populated": g.populated,
            "created_at": g.created_at.isoformat(),
        }
        for g in goals
    ]


@router.post("/goals/{goal_id}/populate")
async def populate_goal(
    goal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """为目标填充知识卡片（自动学习）"""
    # 获取目标
    from sqlalchemy import select
    result = await db.execute(select(LearningGoal).where(LearningGoal.id == goal_id))
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail="目标不存在")

    # 开始填充
    result = await engine.populate_goal(
        goal_id=goal_id,
        goal_description=goal.description,
        session=db
    )

    return result


@router.get("/goals/{goal_id}/progress")
async def get_progress(goal_id: int, db: AsyncSession = Depends(get_db)):
    """获取学习进度"""
    progress = await engine.get_goal_progress(goal_id, db)
    return progress


@router.get("/goals/{goal_id}/cards")
async def list_cards(goal_id: int, db: AsyncSession = Depends(get_db)):
    """列出目标的所有知识卡片"""
    from sqlalchemy import select

    result = await db.execute(
        select(KnowledgeCard).where(KnowledgeCard.goal_id == goal_id)
    )
    cards = result.scalars().all()

    return [engine._card_to_dict(card) for card in cards]


@router.get("/cards/{card_id}")
async def get_card(card_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个知识卡片"""
    card = await engine.get_card(card_id, db)
    if not card:
        raise HTTPException(status_code=404, detail="知识卡片不存在")
    return card


@router.post("/goals/{goal_id}/quiz")
async def generate_quiz(
    goal_id: int,
    count: int = 5,
    mode: str = "mixed",
    db: AsyncSession = Depends(get_db)
):
    """生成测试题"""
    quizzes = await engine.generate_quiz(goal_id, count, mode, db)
    return {"quizzes": quizzes}


@router.post("/mastery/update")
async def update_mastery(
    data: MasteryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新掌握度"""
    result = await engine.update_mastery(
        card_id=data.card_id,
        score=data.score,
        response_time_seconds=data.response_time,
        session=db
    )
    return result


@router.get("/goals/{goal_id}/due-review")
async def get_due_review(
    goal_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """获取到期复习的知识卡片"""
    due_items = await engine.get_due_items(goal_id, limit, db)
    return {"items": due_items}


@router.get("/cards/search")
async def search_cards(
    keywords: str,
    goal_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """搜索知识卡片"""
    keyword_list = [kw.strip() for kw in keywords.split(",")]
    results = await engine.search_cards(keyword_list, goal_id, db)
    return {"results": results}


# ===== 元认知增强的生成接口 =====

@router.post("/goals/{goal_id}/populate-with-reflection")
async def populate_with_reflection(
    goal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    带元认知反思的填充接口
    
    这是一个增强版的知识卡片生成接口：
    1. 正常生成知识卡片
    2. 对生成的卡片内容进行自我审计
    3. 如果评分过低，自动重写优化
    4. 存储反思记录供系统学习
    """
    from sqlalchemy import select
    
    # 获取目标
    result = await db.execute(select(LearningGoal).where(LearningGoal.id == goal_id))
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(status_code=404, detail="目标不存在")
    
    # 首先执行正常的填充流程
    populate_result = await engine.populate_goal(
        goal_id=goal_id,
        goal_description=goal.description,
        session=db
    )
    
    if not populate_result.get("success"):
        return populate_result
    
    # 获取刚生成的卡片
    result = await db.execute(
        select(KnowledgeCard).where(KnowledgeCard.goal_id == goal_id)
    )
    cards = result.scalars().all()
    
    # 对每个卡片进行元认知审计
    reflected_count = 0
    improved_count = 0
    
    for card in cards:
        # 提取卡片内容用于审计
        content = str(card.content)
        
        # 执行元认知审计
        reflection = await meta_engine.reflect(
            content=content,
            context=f"学习目标: {goal.description}, 单元: {card.unit}"
        )
        
        # 如果评分过低，尝试递归修正
        if reflection['logic_score'] < 0.7 or reflection['is_generic']:
            refined = await meta_engine.recursive_refine(
                original_prompt=f"为 {card.unit} 生成知识卡片",
                last_reflection=reflection,
                previous_content=content
            )
            
            # 尝试解析为JSON（如果成功则更新卡片）
            try:
                import json
                refined_data = json.loads(refined)
                if isinstance(refined_data, dict):
                    # 更新卡片内容
                    for key, value in refined_data.items():
                        if key != "unit":
                            card.content[key] = value
                    improved_count += 1
            except:
                pass  # 解析失败，保留原内容
        
        # 保存反思记录
        await save_reflection(
            db_session=db,
            reflection_data=reflection,
            target_id=str(card.id),
            target_type="card"
        )
        
        reflected_count += 1
    
    await db.commit()
    
    return {
        "success": True,
        "total_units": len(cards),
        "reflected": reflected_count,
        "improved": improved_count,
        "message": f"完成元认知审计 {reflected_count} 个卡片，其中 {improved_count} 个被优化"
    }


@router.get("/reflections")
async def list_reflections(
    target_type: Optional[str] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """获取元认知反思记录"""
    from core.metacognition import get_recent_reflections
    
    reflections = await get_recent_reflections(db, target_type, limit)
    
    return {
        "reflections": [
            {
                "id": r.id,
                "target_id": r.target_id,
                "target_type": r.target_type,
                "logic_score": r.logic_score,
                "depth_score": r.depth_score,
                "is_generic": r.is_generic,
                "critique": r.critique,
                "recursive_advice": r.recursive_advice,
                "reflection_count": r.reflection_count,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in reflections
        ]
    }
