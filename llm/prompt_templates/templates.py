SUMMARIZE_KNOWLEDGE = """
你是一个学习助手。请用中文简洁地总结以下内容（3-5句话），
重点突出关键概念和它们之间的关系。

内容:
{content}
"""

GAP_DETECTION = """
你是一个专业的课程设计专家。请分析以下知识图谱中的主题，
识别概念缺口或缺失的关联。

已知主题:
{topics}

请返回JSON格式: {{"gaps": [{{"topic": str, "reason": str, "priority": int (1-5)}}]}}
"""

TASK_GENERATION = """
为以下知识缺口生成学习任务。

缺口: {gap}
背景: {context}

请返回JSON格式: {{"tasks": [{{"title": str, "description": str, "estimated_minutes": int}}]}}
"""

QA_SYSTEM = """
你是一个知识渊博的学习助手。请基于提供的上下文回答用户的问题。
要求：简洁、准确、使用中文。
如果上下文中没有足够的信息，请明确说明。

上下文:
{context}
"""

LEARNING_ADVICE = """
根据用户的学习进度和历史记录，提供个性化的学习建议。

学习进度摘要:
{progress}

近期活动:
{activity}

请提供2-3条具体、可操作的建议。
"""

MINDMAP_GENERATION = """
为以下主题创建思维导图结构。

主题: {topic}
内容: {content}

请返回JSON格式: {{
  "root": str,
  "branches": [{{
    "label": str,
    "children": [{{"label": str}}]
  }}]
}}
"""
