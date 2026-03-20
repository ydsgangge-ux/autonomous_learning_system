# conversation.py - 对话上下文管理器（完全不依赖LLM）
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

@dataclass
class Intent:
    type: str          # query / learn / quiz / progress / general
    subtype: str = ""  # reading/strokes/meaning/usage/compare/memory/related/full
    entity: str = ""
    raw: str = ""

class ConversationContext:
    PRONOUNS = {"它","这个","那个","这字","那字","这个字","那个字",
                "此字","该字","刚才","刚刚","上面","前面","这词","这个词","那个词"}

    INTENT_RULES = [
        ("query","reading",   r"怎么读|读音|拼音|发音|怎么念|念什么|读什么"),
        ("query","strokes",   r"几画|笔画|笔顺|怎么写|字形|结构|部首"),
        ("query","meaning",   r"什么意思|是什么意思|含义|意思|意义|解释|表示什么"),
        ("query","usage",     r"组词|造句|例句|用法|怎么用|如何用|搭配"),
        ("query","compare",   r"有什么区别|和.*区别|区别|对比|比较|有什么不同"),
        ("query","memory",    r"怎么记|如何记|记忆方法|记忆技巧|联想"),
        ("query","related",   r"形近字|同音字|近义词|反义词|相关"),
        ("learn","",          r"我想学|学习|开始学|帮我学"),
        ("quiz","",           r"测试我|考考我|出题|测验|检验|来道题|给我出"),
        ("progress","",       r"进度|学了多少|完成了多少|还差多少|学会了吗"),
        ("query","full",      r"介绍一下|详细说|说说|讲讲|告诉我|是什么"),
    ]

    def __init__(self):
        self.current_topic: Optional[str] = None
        self.current_goal_id: Optional[str] = None
        self.current_goal_type: str = "general"
        self.recent_entities: List[str] = []
        self.dialog_log: List[Dict] = []

    def process(self, user_input: str) -> Intent:
        resolved = self.resolve_reference(user_input)
        entity = self.extract_entity(resolved)
        intent_type, subtype = self.detect_intent(resolved)
        return Intent(type=intent_type, subtype=subtype,
                      entity=entity or self.current_topic or "", raw=user_input)

    def resolve_reference(self, text: str) -> str:
        if not self.current_topic:
            return text
        result = text
        for p in sorted(self.PRONOUNS, key=len, reverse=True):
            if p in result:
                result = result.replace(p, self.current_topic)
        return result

    def detect_intent(self, text: str) -> Tuple[str, str]:
        for itype, subtype, pattern in self.INTENT_RULES:
            if re.search(pattern, text):
                return itype, subtype
        return "general", ""

    def extract_entity(self, text: str) -> Optional[str]:
        # 1. 引号
        quoted = re.findall(r'[「」""\'\']([\w\s]{1,20})[「」""\'\']', text)
        if quoted:
            return quoted[0].strip()
        # 2. "X字/X词"
        m = re.search(r'([\u4e00-\u9fff]{1,4})[字词]', text)
        if m:
            return m.group(1)
        # 3. 汉字目标的单字
        if self.current_goal_type == "characters":
            func = set("的了吗呢啊哦嗯嘛哈吧呀我你他她它们这那是有在什么怎么如何和有么")
            chars = [c for c in text if '\u4e00' <= c <= '\u9fff' and c not in func]
            if len(chars) == 1:
                return chars[0]
            # 尝试提取最前面的汉字（作为主语）
            for c in text:
                if '\u4e00' <= c <= '\u9fff' and c not in func:
                    return c
        # 4. 常用句式
        for pat in [r'什么是([\w\u4e00-\u9fff]{1,10})',
                    r'([\w\u4e00-\u9fff]{1,10})[是的]什么',
                    r'([\w\u4e00-\u9fff]{1,10})[怎么如何]',
                    r'关于([\w\u4e00-\u9fff]{1,10})']:
            m = re.search(pat, text)
            if m and len(m.group(1)) >= 1:
                return m.group(1).strip()
        # 5. recent_entities
        for e in self.recent_entities:
            if e in text:
                return e
        return None

    def update(self, user_input: str, response: str, entity: str = ""):
        if entity:
            self.current_topic = entity
            if entity in self.recent_entities:
                self.recent_entities.remove(entity)
            self.recent_entities.insert(0, entity)
            self.recent_entities = self.recent_entities[:10]
        self.dialog_log.append({
            "user": user_input, "response": response[:100],
            "entity": entity, "time": datetime.now().isoformat()
        })

    def set_goal(self, goal_id: str, goal_type: str):
        self.current_goal_id = goal_id
        self.current_goal_type = goal_type
        self.current_topic = None

    def get_context_summary(self) -> str:
        return (f"话题:{self.current_topic or '无'} | "
                f"近期:{self.recent_entities[:3]}")


def format_content(content: Any) -> str:
    if content is None: return "（暂无）"
    if isinstance(content, str): return content
    if isinstance(content, list):
        return "、".join(str(c) for c in content) if content else "（暂无）"
    if isinstance(content, dict):
        return "\n".join(f"{k}：{format_content(v)}" for k, v in content.items())
    return str(content)


def compose_answer(intent: Intent, node_title: str,
                   content: Any, unit: str, goal_type: str) -> str:
    fmt = format_content(content)
    if goal_type == "characters":
        labels = {
            "reading": f"「{unit}」读作：{fmt}",
            "strokes": f"「{unit}」{fmt}",
            "meaning": f"「{unit}」的意思：{fmt}",
            "usage":   f"「{unit}」{node_title}：{fmt}",
            "memory":  f"「{unit}」记忆方法：{fmt}",
        }
        return labels.get(intent.subtype, f"「{unit}」的{node_title}：{fmt}")
    return f"【{unit}】{node_title}：{fmt}" if intent.subtype else f"【{unit}】\n{fmt}"


if __name__ == "__main__":
    print("🧪 测试 conversation.py\n")
    ctx = ConversationContext()
    ctx.set_goal("g001", "characters")

    tests = [
        ("蠢字怎么读",       "query","reading",  "蠢"),
        ("它有几画",         "query","strokes",  "蠢"),
        ("这个字的部首",     "query","strokes",  "蠢"),
        ("蠢和舂有什么区别", "query","compare",  "蠢"),
        ("用蠢字组词",       "query","usage",    "蠢"),
        ("我想学Python",     "learn","",         "Python"),
        ("测试我",           "quiz", "",         ""),
    ]
    print(f"{'输入':<22} {'类型':<8} {'子类型':<10} {'实体'}")
    print("-" * 55)
    for text, et, es, ee in tests:
        i = ctx.process(text)
        ok = "✅" if i.type==et and i.subtype==es else "❌"
        print(f"{ok} {text:<20} {i.type:<8} {i.subtype:<10} {i.entity}")
        ctx.update(text, "ok", i.entity)

    print("\n代词解析：")
    ctx.current_topic = "蠢"
    for raw in ["那它有几画", "这个字怎么读", "它的部首是什么"]:
        r = ctx.resolve_reference(raw)
        print(f"  '{'✅' if '蠢' in r else '❌'}' {raw!r} → {r!r}")
    print("\n✅ 完成")
