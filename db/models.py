from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Text, ForeignKey, Table, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# 枚举类
class TaskStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class MasteryStatus:
    UNSEEN = "unseen"
    LEARNING = "learning"
    REVIEWING = "reviewing"
    MASTERED = "mastered"


# ── Knowledge Item ─────────────────────────────────────────────────────────

class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    source = Column(String(512), nullable=True)
    tags = Column(JSON, default=list)
    embedding_id = Column(String(128), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Review Records ─────────────────────────────────────────────────────────

class ReviewRecord(Base):
    __tablename__ = "review_records"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_item_id = Column(Integer, ForeignKey("knowledge_items.id"), nullable=True)
    reviewed_at = Column(DateTime, default=datetime.utcnow)
    score = Column(Float, nullable=True)
    next_review_at = Column(DateTime, nullable=True)
    interval_days = Column(Integer, default=1)
    repetitions = Column(Integer, default=0)
    ease_factor = Column(Float, default=2.5)


# ── Learning Plan ─────────────────────────────────────────────────────────

class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    goal = Column(Text, nullable=False)
    priority = Column(Integer, default=5)
    estimated_hours = Column(Float, nullable=True)
    status = Column(String(32), default="pending")
    scheduled_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta = Column(JSON, default=dict)


class LearningTask(Base):
    __tablename__ = "learning_tasks"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=False)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    estimated_minutes = Column(Integer, default=30)
    status = Column(String(32), default="pending")
    order = Column(Integer, default=0)
    scheduled_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Learning Goal ─────────────────────────────────────────────────────────

class LearningGoal(Base):
    __tablename__ = "learning_goals"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    goal_type = Column(String(64), nullable=False)
    card_template = Column(String(64), nullable=False)
    unit_name = Column(String(64), nullable=False)
    estimated_count = Column(Integer, nullable=True)
    total_units = Column(Integer, default=0)
    populated_count = Column(Integer, default=0)
    populated = Column(Boolean, default=False)
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Knowledge Card ───────────────────────────────────────────────────────

class KnowledgeCard(Base):
    __tablename__ = "knowledge_cards"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("learning_goals.id"), nullable=False)
    unit = Column(String(256), nullable=False)
    goal_type = Column(String(64), nullable=False)
    content = Column(JSON, nullable=False)
    mastery_status = Column(String(32), default="unseen")
    mastery_score = Column(Float, default=0.0)
    mastery_attempts = Column(Integer, default=0)
    mastery_correct = Column(Integer, default=0)
    mastery_last_seen = Column(DateTime, nullable=True)
    mastery_next_review = Column(DateTime, nullable=True)
    ease_factor = Column(Float, default=2.5)
    interval_days = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Quiz Record ──────────────────────────────────────────────────────────

class QuizRecord(Base):
    __tablename__ = "quiz_records"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("knowledge_cards.id"), nullable=False)
    question_type = Column(String(64), nullable=False)
    question = Column(Text, nullable=False)
    user_answer = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=False)
    score = Column(Float, nullable=False)
    response_time_seconds = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Dialogue Session ──────────────────────────────────────────────────────

class DialogueSession(Base):
    __tablename__ = "dialogue_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_key = Column(String(128), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DialogueMessage(Base):
    __tablename__ = "dialogue_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("dialogue_sessions.id"), nullable=False)
    role = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Association tables for many-to-many relationships (if needed)
# knowledge_tag = Table('knowledge_tag', Base.metadata, ...)

class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text)
    node_type = Column(String)  # e.g., "concept", "fact", "resource"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_data = Column(JSON, default={})

    # relationships
    embeddings = relationship("Embedding", back_populates="node", cascade="all, delete-orphan")

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("knowledge_nodes.id"), nullable=False)
    vector_id = Column(String, unique=True, index=True)  # ID in vector store
    model = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    node = relationship("KnowledgeNode", back_populates="embeddings")

class SyncQueue(Base):
    __tablename__ = "sync_queue"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("knowledge_nodes.id"), nullable=False)
    action = Column(String)  # "create", "update", "delete"
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    node = relationship("KnowledgeNode")


# ── Meta-Cognition / 自我反思系统 ──────────────────────────────────────────

class MetaReflection(Base):
    """元认知反思记录 - 系统的"前额叶皮层" """
    __tablename__ = "meta_reflections"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(String(128), nullable=True)
    target_type = Column(String(32), nullable=True)
    
    logic_score = Column(JSON, nullable=True)
    depth_score = Column(JSON, nullable=True)
    is_generic = Column(Boolean, default=False)
    critique = Column(Text, nullable=True)
    recursive_advice = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ── 因果推理系统 (Causal Reasoning) ────────────────────────────────────────

class CausalNode(Base):
    """因果图谱节点 """
    __tablename__ = "causal_nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(128), unique=True, nullable=False, index=True)
    name = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    node_type = Column(String(64), nullable=True)
    domain = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CausalLink(Base):
    """因果图谱边 """
    __tablename__ = "causal_links"

    id = Column(Integer, primary_key=True, index=True)
    cause_node_id = Column(String(128), nullable=True, index=True)
    effect_node_id = Column(String(128), nullable=True, index=True)
    cause_id = Column(String(128), nullable=True, index=True)
    effect_id = Column(String(128), nullable=True, index=True)

    strength = Column(JSON, default=0.5)
    confidence = Column(JSON, default=0.5)
    mechanism = Column(Text, nullable=True)
    evidence_count = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)


# ── 探索任务 (Exploration Task) ───────────────────────────────────────────

class ExplorationTask(Base):
    """探索任务模型 - 用于因果发现和知识Gap检测"""
    __tablename__ = "exploration_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(64), nullable=False)  # "causal_extraction", "gap_detection", "bridge_task"
    status = Column(String(32), default="pending")
    priority = Column(Integer, default=5)

    target_id = Column(String(128), nullable=True)
    target_type = Column(String(64), nullable=True)
    description = Column(Text, nullable=True)

    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


# ── 跨域知识融合 (Cross-Domain Synthesis) ─────────────────────────────────

class DomainBridge(Base):
    """跨域知识桥接 - 存储不同领域间的抽象映射关系"""
    __tablename__ = "domain_bridges"

    id = Column(Integer, primary_key=True, index=True)
    source_domain = Column(String(256), nullable=False, index=True)    # 源领域
    target_domain = Column(String(256), nullable=False, index=True)    # 目标领域

    source_concept = Column(String(512), nullable=True)                # 源概念
    target_concept = Column(String(512), nullable=True)                 # 目标概念
    abstract_principle = Column(Text, nullable=True)                   # 抽象原理

    mapping_logic = Column(JSON, default=dict)                         # 映射逻辑字典
    structural_mapping = Column(JSON, default=dict)                    # 结构映射表

    synthesized_explanation = Column(Text, nullable=True)               # 融合后的解释

    synthesis_efficacy = Column(Float, default=0.0)                   # 融合效果评分
    feedback_count = Column(Integer, default=0)                       # 反馈次数

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DomainConcept(Base):
    """领域概念 - 存储领域的抽象特征"""
    __tablename__ = "domain_concepts"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(256), nullable=False, index=True)            # 领域名称

    concept = Column(String(512), nullable=False)                       # 概念名称
    abstraction_level = Column(Integer, default=1)                     # 抽象层级(1-5)

    core_principle = Column(Text, nullable=True)                       # 核心原理
    physical_model = Column(JSON, default=dict)                       # 物理模型参数

    related_domains = Column(JSON, default=list)                       # 相关领域列表
    created_at = Column(DateTime, default=datetime.utcnow)
