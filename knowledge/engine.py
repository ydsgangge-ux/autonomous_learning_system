"""
知识引擎 - 系统学习的核心模块
负责将学习目标拆解为知识单元，并生成结构化的知识卡片
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import LearningGoal, KnowledgeCard, MasteryStatus
from knowledge.goal_detector import GoalTypeDetector
from knowledge.unit_generator import UnitListGenerator
from knowledge.card_generator import KnowledgeCardGenerator
from core.utils import get_logger

logger = get_logger(__name__)


class KnowledgeEngine:
    """
    知识引擎 - 系统"学习"的核心

    工作流程：
    1. analyze_goal()     → 分析目标，确定类型和单元数
    2. populate_goal()    → 拆解目标，批量生成知识卡片
    3. search_card()     → 搜索知识卡片
    4. generate_quiz()    → 生成测试题
    5. update_mastery()   → 更新掌握状态
    6. get_due_items()    → 获取到期复习项目
    """

    def __init__(self):
        self.type_detector = GoalTypeDetector()
        self.unit_gen = UnitListGenerator()
        self.card_gen = KnowledgeCardGenerator()

    # ===== 目标分析 =====

    async def analyze_goal(self, goal_description: str) -> Dict:
        """分析目标，返回类型、单元数等元信息"""
        goal_type = self.type_detector.detect(goal_description)
        config = self.type_detector.get_config(goal_type)

        # 提取数量
        count = self.type_detector.extract_count(goal_description)

        return {
            "goal_type": goal_type,
            "unit_name": config["unit_name"],
            "card_template": config["card_template"],
            "searchable": config["searchable"],
            "estimated_count": count,
            "can_be_populated": True,
        }

    # ===== 知识填充（核心） =====

    async def populate_goal(self,
                          goal_id: int,
                          goal_description: str,
                          session: AsyncSession,
                          on_progress: Optional[Callable] = None) -> Dict:
        """
        为学习目标填充知识内容（真正的"学习"发生在这里）
        """
        print(f"\n🧠 开始为目标填充知识内容: {goal_description}")

        # 分析目标
        meta = await self.analyze_goal(goal_description)
        goal_type = meta["goal_type"]
        card_template = meta["card_template"]
        count = meta["estimated_count"]

        # 获取目标对象
        result = await session.execute(
            select(LearningGoal).where(LearningGoal.id == goal_id)
        )
        goal = result.scalar_one_or_none()
        if not goal:
            return {"success": False, "error": "目标不存在"}

        # 更新目标元信息
        goal.goal_type = goal_type
        goal.card_template = card_template
        goal.unit_name = meta["unit_name"]
        goal.estimated_count = count

        # 步骤1：生成知识单元列表
        print(f"📋 步骤1/3：生成知识单元列表...")
        units = await self.unit_gen.generate_unit_list(goal_description, goal_type, count)
        if not units:
            return {"success": False, "error": "无法生成知识单元列表"}

        print(f"   生成了 {len(units)} 个{meta['unit_name']}")
        goal.total_units = len(units)

        # 步骤2：批量生成知识卡片
        print(f"📚 步骤2/3：批量生成知识卡片...")
        generated = 0
        failed = 0

        i = 0
        async for card_content in self.card_gen.generate_batch(units, card_template):
            unit = card_content.get("unit", "")
            if unit:
                # 创建知识卡片
                card = KnowledgeCard(
                    goal_id=goal_id,
                    unit=unit,
                    goal_type=goal_type,
                    content=card_content,
                    mastery_status=MasteryStatus.unseen,
                    mastery_score=0.0,
                    ease_factor=2.5,
                    interval_days=1
                )
                session.add(card)

                if card_content.get("_failed"):
                    failed += 1
                else:
                    generated += 1

                if on_progress:
                    on_progress(generated + failed, len(units), unit)

                # 每50个保存一次
                if (generated + failed) % 50 == 0:
                    goal.populated_count = generated
                    goal.updated_at = datetime.utcnow()
                    await session.commit()
                    print(f"   进度: {generated + failed}/{len(units)}")

            i += 1

        # 步骤3：更新目标元信息
        print(f"✅ 步骤3/3：完成")
        goal.populated = True
        goal.populated_count = generated
        goal.updated_at = datetime.utcnow()
        await session.commit()

        result = {
            "success": True,
            "total_units": len(units),
            "generated": generated,
            "failed": failed,
            "goal_type": goal_type,
        }

        print(f"\n✅ 知识填充完成！")
        print(f"   成功: {generated}个 | 失败: {failed}个")
        return result

    # ===== 查询与搜索 =====

    async def search_cards(self,
                          keywords: List[str],
                          goal_id: Optional[int] = None,
                          session: AsyncSession = None) -> List[Dict]:
        """搜索知识库，返回最匹配的卡片列表"""
        query = select(KnowledgeCard)

        if goal_id:
            query = query.where(KnowledgeCard.goal_id == goal_id)

        # 关键词匹配
        for keyword in keywords:
            if keyword:
                query = query.where(KnowledgeCard.unit.ilike(f"%{keyword}%"))

        result = await session.execute(query)
        cards = result.scalars().all()

        # 转换为字典
        return [self._card_to_dict(card) for card in cards[:10]]

    async def get_card(self, card_id: int, session: AsyncSession) -> Optional[Dict]:
        """获取单个知识卡片"""
        result = await session.execute(
            select(KnowledgeCard).where(KnowledgeCard.id == card_id)
        )
        card = result.scalar_one_or_none()
        return self._card_to_dict(card) if card else None

    # ===== 测试题生成 =====

    async def generate_quiz(self,
                           goal_id: int,
                           count: int = 5,
                           mode: str = "mixed",
                           session: AsyncSession = None) -> List[Dict]:
        """生成测试题"""
        # 获取目标的所有卡片
        result = await session.execute(
            select(KnowledgeCard).where(KnowledgeCard.goal_id == goal_id)
        )
        cards = result.scalars().all()

        if not cards:
            return []

        # 根据模式选择卡片
        if mode == "unseen":
            selected = [c for c in cards if c.mastery_status == MasteryStatus.unseen]
        elif mode == "weak":
            selected = sorted(cards, key=lambda x: x.mastery_score)[:count * 2]
        elif mode == "due_review":
            now = datetime.utcnow()
            selected = [c for c in cards if c.mastery_next_review and c.mastery_next_review <= now]
        else:  # mixed
            unseen = [c for c in cards if c.mastery_status == MasteryStatus.unseen]
            weak = [c for c in cards if c.mastery_score < 0.6 and c.mastery_status != MasteryStatus.unseen]
            selected = (unseen + weak)[:count * 2]

        import random
        random.shuffle(selected)
        selected = selected[:count]

        # 生成测试题
        quizzes = []
        for card in selected:
            quiz = self._make_quiz_question(card)
            quiz["card_id"] = card.id
            quizzes.append(quiz)

        return quizzes

    def _make_quiz_question(self, card: KnowledgeCard) -> Dict:
        """生成测试题"""
        unit = card.unit
        content = card.content or {}

        if card.goal_type == "character":
            import random
            question_type = random.choice(["reading", "meaning", "compound"])
            if question_type == "reading":
                return {
                    "question": f"「{unit}」怎么读？",
                    "answer": content.get("reading", ""),
                    "hint": content.get("memory_tip", ""),
                    "type": "reading",
                }
            elif question_type == "meaning":
                return {
                    "question": f"「{unit}」是什么意思？",
                    "answer": "；".join(content.get("meanings", [])),
                    "hint": content.get("compounds", [""])[0],
                    "type": "meaning",
                }
            else:
                return {
                    "question": f"用「{unit}」组一个词",
                    "answer": "、".join(content.get("compounds", [])[:3]),
                    "hint": content.get("sentences", [""])[0],
                    "type": "compound",
                }
        else:
            return {
                "question": f"请解释「{unit}」",
                "answer": content.get("definition") or content.get("summary") or "",
                "hint": str(content.get("examples", [""])[0])[:50],
                "type": "explanation",
            }

    # ===== 掌握度更新（SM-2算法） =====

    async def update_mastery(self,
                            card_id: int,
                            score: float,
                            response_time_seconds: float = 10.0,
                            session: AsyncSession = None) -> Dict:
        """更新知识单元掌握度（SM-2 + 响应时间修正）"""
        result = await session.execute(
            select(KnowledgeCard).where(KnowledgeCard.id == card_id)
        )
        card = result.scalar_one_or_none()
        if not card:
            return {}

        # 响应时间修正：30秒以上降低分数
        time_penalty = max(0, (response_time_seconds - 30) / 60) * 0.2
        effective_score = max(0, score - time_penalty)

        # SM-2算法
        card.mastery_attempts += 1
        if effective_score >= 0.6:
            card.mastery_correct += 1

        # 更新ease factor
        card.ease_factor = max(1.3, card.ease_factor +
                              0.1 - (0.08 * (effective_score * 5)) * (1.1 - effective_score * 5) * 0.02)

        # 更新间隔
        if effective_score < 0.6:
            card.interval_days = 1
        elif card.mastery_attempts == 1:
            card.interval_days = 1
        elif card.mastery_attempts == 2:
            card.interval_days = 6
        else:
            card.interval_days = min(365, round(card.interval_days * card.ease_factor))

        # 更新状态
        if card.mastery_attempts == 0:
            card.mastery_status = MasteryStatus.unseen
        else:
            success_rate = card.mastery_correct / card.mastery_attempts
            card.mastery_score = success_rate

            if success_rate >= 0.85 and card.mastery_attempts >= 3:
                card.mastery_status = MasteryStatus.mastered
            elif success_rate >= 0.6:
                card.mastery_status = MasteryStatus.familiar
            else:
                card.mastery_status = MasteryStatus.learning

        card.mastery_last_seen = datetime.utcnow()
        card.mastery_next_review = datetime.utcnow() + timedelta(days=card.interval_days)
        card.updated_at = datetime.utcnow()

        await session.commit()

        return {
            "status": card.mastery_status.value,
            "score": card.mastery_score,
            "interval_days": card.interval_days,
            "next_review": card.mastery_next_review.isoformat(),
        }

    # ===== 进度统计 =====

    async def get_goal_progress(self,
                               goal_id: int,
                               session: AsyncSession) -> Dict:
        """获取目标的详细学习进度"""
        result = await session.execute(
            select(KnowledgeCard).where(KnowledgeCard.goal_id == goal_id)
        )
        cards = result.scalars().all()

        if not cards:
            return {
                "populated": False,
                "message": "知识库尚未填充，请先执行 populate"
            }

        status_counts = {
            MasteryStatus.unseen: 0,
            MasteryStatus.learning: 0,
            MasteryStatus.familiar: 0,
            MasteryStatus.mastered: 0
        }
        scores = []

        for card in cards:
            status_counts[card.mastery_status] += 1
            scores.append(card.mastery_score)

        total = len(cards)
        learned = total - status_counts[MasteryStatus.unseen]

        return {
            "total_units": total,
            "learned": learned,
            "unseen": status_counts[MasteryStatus.unseen],
            "learning": status_counts[MasteryStatus.learning],
            "familiar": status_counts[MasteryStatus.familiar],
            "mastered": status_counts[MasteryStatus.mastered],
            "completion_rate": learned / total if total else 0,
            "mastery_rate": status_counts[MasteryStatus.mastered] / total if total else 0,
            "avg_score": sum(scores) / len(scores) if scores else 0,
        }

    async def get_due_items(self,
                           goal_id: int,
                           limit: int = 20,
                           session: AsyncSession = None) -> List[Dict]:
        """获取到期复习的知识单元"""
        now = datetime.utcnow()
        result = await session.execute(
            select(KnowledgeCard)
            .where(KnowledgeCard.goal_id == goal_id)
            .where(KnowledgeCard.mastery_next_review <= now)
            .order_by(KnowledgeCard.mastery_next_review)
            .limit(limit)
        )
        cards = result.scalars().all()

        return [self._card_to_dict(card) for card in cards]

    # ===== 内部工具 =====

    def _card_to_dict(self, card: KnowledgeCard) -> Dict:
        """将卡片对象转换为字典"""
        return {
            "id": card.id,
            "goal_id": card.goal_id,
            "unit": card.unit,
            "goal_type": card.goal_type,
            "content": card.content,
            "mastery": {
                "status": card.mastery_status.value,
                "score": card.mastery_score,
                "attempts": card.mastery_attempts,
                "correct": card.mastery_correct,
                "last_seen": card.mastery_last_seen.isoformat() if card.mastery_last_seen else None,
                "next_review": card.mastery_next_review.isoformat() if card.mastery_next_review else None,
                "ease_factor": card.ease_factor,
                "interval_days": card.interval_days,
            }
        }
