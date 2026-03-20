"""
V2 学习系统 API 路由 - 包装 main_v2.py 的全部功能
"""
import asyncio
import json
import threading
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 导入 main_v2 的核心模块
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 延迟导入，避免循环依赖
_learning_system = None
_lock = threading.Lock()

def get_learning_system():
    """获取学习系统实例（延迟初始化，单例）"""
    global _learning_system
    if _learning_system is None:
        with _lock:
            if _learning_system is None:
                from main_v2 import LearningSystem
                _learning_system = LearningSystem(data_dir="./learning_data")
                print("[V2] 学习系统实例已创建")
    return _learning_system

router = APIRouter()


# ===== 请求/响应模型 =====

class GoalCreate(BaseModel):
    description: str


class AskRequest(BaseModel):
    question: str


class QuizStart(BaseModel):
    count: int = 5


class AnswerSubmit(BaseModel):
    question: str
    answer: str


# ===== 目标管理 =====

@router.get("/v2/goals")
async def list_goals():
    """列出所有学习目标"""
    try:
        sys_ = get_learning_system()
        goals = sys_.db.load_all_goals()
        
        # 增强每个目标的信息
        result = []
        for g in goals:
            goal_id = g.get("id", "")
            units = sys_.col.load_goal_units(goal_id) if goal_id else []
            report = sys_.col.get_completion_report(goal_id, units[:50]) if goal_id and units else {
                "total_units": 0, "learned_units": 0, "collected_nodes": 0, 
                "total_nodes": 0, "overall_completion": 0
            }
            result.append({
                "id": goal_id,
                "description": g.get("description", ""),
                "status": g.get("status", "unknown"),
                "goal_type": sys_._goal_type.get(goal_id, "general"),
                "total_units": len(units),
                "learned_units": report.get("learned_units", 0),
                "completion": report.get("overall_completion", 0),
            })
        return {"goals": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/goals")
async def create_goal(request: GoalCreate):
    """创建新的学习目标"""
    try:
        sys_ = get_learning_system()
        goal_id = sys_.create_goal(request.description)
        return {"success": True, "goal_id": goal_id, "message": f"目标已创建: {request.description}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/goals/{goal_id}/select")
async def select_goal(goal_id: str):
    """切换当前目标"""
    try:
        sys_ = get_learning_system()
        goal_type = sys_._goal_type.get(goal_id, "general")
        sys_.ctx.set_goal(goal_id, goal_type)
        return {"success": True, "message": f"已切换到目标: {goal_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/v2/goals/{goal_id}")
async def delete_goal(goal_id: str):
    """删除学习目标"""
    try:
        sys_ = get_learning_system()
        success = sys_.db.delete_goal(goal_id)
        if goal_id in sys_._trees:
            del sys_._trees[goal_id]
        if goal_id in sys_._goal_type:
            del sys_._goal_type[goal_id]
        return {"success": success, "message": f"目标已删除: {goal_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== 知识填充 =====

@router.post("/v2/goals/{goal_id}/learn")
async def learn_goal(goal_id: str, limit: Optional[int] = None):
    """批量填充知识（主动学习）"""
    try:
        sys_ = get_learning_system()
        
        # 检查目标是否存在
        goal = sys_.db.load_goal(goal_id)
        if not goal:
            raise HTTPException(status_code=404, detail="目标不存在")
        
        # 执行填充
        sys_.populate_goal(goal_id, limit)
        
        return {"success": True, "message": f"知识填充完成: {goal_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== 问答交互 =====

@router.post("/v2/ask")
async def ask_question(request: AskRequest):
    """提问（核心问答功能）"""
    try:
        print(f"[问答] 问题: {request.question}")
        sys_ = get_learning_system()
        
        # 检查是否有活跃目标
        if not sys_.ctx.current_goal_id:
            print("[问答] 没有活跃目标")
            # 返回提示信息
            return {
                "success": True,
                "question": request.question,
                "answer": "请先创建一个学习目标，然后进行学习后再提问。\n\n使用方式：\n1. 点击左上角「目标管理」创建目标\n2. 点击「批量学习」填充知识\n3. 然后可以提问",
                "context": "无目标",
                "current_goal": None,
                "current_topic": None,
            }
        
        print(f"[问答] 当前目标: {sys_.ctx.current_goal_id}, 话题: {sys_.ctx.current_topic}")
        answer = sys_.answer(request.question)
        
        # 获取当前上下文
        context = sys_.ctx.get_context_summary()
        
        return {
            "success": True,
            "question": request.question,
            "answer": answer,
            "context": context,
            "current_goal": sys_.ctx.current_goal_id,
            "current_topic": sys_.ctx.current_topic,
        }
    except Exception as e:
        import traceback
        print(f"[问答] 错误: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ===== 测验 =====

@router.get("/v2/quiz/start")
async def start_quiz(count: int = 5):
    """开始测验"""
    try:
        sys_ = get_learning_system()
        goal_id = sys_.ctx.current_goal_id
        
        if not goal_id:
            raise HTTPException(status_code=400, detail="请先创建或选择一个学习目标")
        
        units = sys_.col.load_goal_units(goal_id)
        if not units:
            raise HTTPException(status_code=400, detail="目标还没有知识单元，请先执行 learn")
        
        # 获取已收集的节点
        import random
        random.shuffle(units)
        
        questions = []
        for unit in units[:count]:
            tree = sys_._get_tree(goal_id, unit, sys_._goal_type.get(goal_id, "general"))
            if not tree:
                continue
            
            collected = [n for n in tree._all_nodes() if n.collected and n.depth > 0]
            if not collected:
                continue
            
            node = random.choice(collected)
            
            q_map = {
                "读音": f"「{unit}」怎么读？",
                "含义": f"「{unit}」是什么意思？",
                "组词": f"用「{unit}」组一个词",
                "笔画": f"「{unit}」共几画？",
                "部首": f"「{unit}」的部首是什么？",
                "结构": f"「{unit}」是什么结构？",
            }
            question_text = q_map.get(node.title, f"「{unit}」的{node.title}是什么？")
            
            questions.append({
                "unit": unit,
                "question": question_text,
                "answer": node.content if node.content else "（暂无）",
                "node_title": node.title,
            })
        
        return {
            "success": True,
            "questions": questions,
            "total": len(questions),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/quiz/submit")
async def submit_quiz(answer: AnswerSubmit):
    """提交测验答案"""
    try:
        sys_ = get_learning_system()
        
        # 简单评分
        score = sys_._simple_score(answer.answer, answer.answer)  # 这里简化处理
        
        # 直接返回参考答案（实际应该记录成绩）
        return {
            "success": True,
            "user_answer": answer.answer,
            "correct_answer": answer.answer,
            "score": 1.0,  # 简化
            "feedback": "已提交",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== 进度查看 =====

@router.get("/v2/progress")
async def get_progress():
    """获取当前目标的学习进度"""
    try:
        sys_ = get_learning_system()
        goal_id = sys_.ctx.current_goal_id
        
        if not goal_id:
            return {"success": True, "has_goal": False, "message": "没有活跃目标"}
        
        units = sys_.col.load_goal_units(goal_id)
        report = sys_.col.get_completion_report(goal_id, units[:50])
        
        # 获取目标信息
        goal = sys_.db.load_goal(goal_id)
        
        return {
            "success": True,
            "has_goal": True,
            "goal_id": goal_id,
            "goal_description": goal.get("description", "") if goal else "",
            "goal_type": sys_._goal_type.get(goal_id, "general"),
            "total_units": report.get("total_units", 0),
            "learned_units": report.get("learned_units", 0),
            "collected_nodes": report.get("collected_nodes", 0),
            "total_nodes": report.get("total_nodes", 0),
            "completion": report.get("overall_completion", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== 上下文状态 =====

@router.get("/v2/context")
async def get_context():
    """获取当前对话上下文"""
    try:
        sys_ = get_learning_system()
        return {
            "success": True,
            "current_goal_id": sys_.ctx.current_goal_id,
            "current_topic": sys_.ctx.current_topic,
            "current_goal_type": sys_.ctx.current_goal_type,
            "recent_entities": sys_.ctx.recent_entities[:5],
            "dialog_log_count": len(sys_.ctx.dialog_log),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== 知识树查看 =====

@router.get("/v2/knowledge/{unit}")
async def get_knowledge_tree(unit: str):
    """获取指定知识单元的树结构"""
    try:
        sys_ = get_learning_system()
        goal_id = sys_.ctx.current_goal_id
        goal_type = sys_._goal_type.get(goal_id, "general") if goal_id else "general"
        
        tree = sys_._get_tree(goal_id, unit, goal_type)
        if not tree:
            return {"success": False, "message": "知识树不存在"}
        
        # 转换为可序列化的格式
        def node_to_dict(node):
            return {
                "id": node.id,
                "title": node.title,
                "content": node.content,
                "collected": node.collected,
                "importance": node.importance,
                "depth": node.depth,
                "children": [node_to_dict(c) for c in node.children],
            }
        
        return {
            "success": True,
            "unit": unit,
            "tree": node_to_dict(tree),
            "completion_rate": tree.completion_rate(),
            "is_learned": tree.is_learned(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v2/units")
async def list_units():
    """列出当前目标的所有知识单元"""
    try:
        sys_ = get_learning_system()
        goal_id = sys_.ctx.current_goal_id
        
        if not goal_id:
            return {"success": True, "units": [], "message": "没有活跃目标"}
        
        units = sys_.col.load_goal_units(goal_id)
        
        # 为每个单元添加完成度
        result = []
        for unit in units:
            tree = sys_.col.load_tree(goal_id, unit)
            if tree:
                result.append({
                    "unit": unit,
                    "completion": tree.completion_rate(),
                    "is_learned": tree.is_learned(),
                    "collected_nodes": sum(1 for n in tree._all_nodes() if n.collected),
                })
            else:
                result.append({
                    "unit": unit,
                    "completion": 0,
                    "is_learned": False,
                    "collected_nodes": 0,
                })
        
        return {"success": True, "units": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== 系统状态 =====

@router.get("/v2/status")
async def get_status():
    """获取系统状态"""
    try:
        sys_ = get_learning_system()
        
        stats = sys_.db.get_statistics()
        
        return {
            "success": True,
            "active_goals": stats.get("active_goals", 0),
            "total_goals": stats.get("total_goals", 0),
            "total_knowledge_nodes": stats.get("total_knowledge_nodes", 0),
            "current_goal": sys_.ctx.current_goal_id,
            "current_topic": sys_.ctx.current_topic,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== 对话历史 =====

@router.get("/v2/history")
async def get_history(limit: int = 20):
    """获取对话历史"""
    try:
        sys_ = get_learning_system()
        history = sys_.ctx.dialog_log[-limit:] if sys_.ctx.dialog_log else []
        
        return {
            "success": True,
            "history": [
                {
                    "user": h.get("user", ""),
                    "response": h.get("response", ""),
                    "entity": h.get("entity", ""),
                    "time": h.get("time", ""),
                }
                for h in history
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
