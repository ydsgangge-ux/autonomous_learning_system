"""
Vision Engine: evaluates learning decisions against configured values/goals.
Acts as a values-based filter for the system's autonomous decisions.
"""
from pathlib import Path
import json
from core.utils import get_logger

logger = get_logger(__name__)

PROFILES_DIR = Path(__file__).parent / "profiles"


class VisionEngine:
    def __init__(self, profile_name: str = "default"):
        self.profile = self._load_profile(profile_name)

    def _load_profile(self, name: str) -> dict:
        path = PROFILES_DIR / f"{name}.json"
        if path.exists():
            with open(path) as f:
                return json.load(f)
        logger.warning(f"Profile '{name}' not found, using defaults.")
        return self._default_profile()

    def _default_profile(self) -> dict:
        return {
            "priorities": ["depth_over_breadth", "practical_application", "concept_mastery"],
            "avoid": ["rote_memorization", "passive_reading"],
            "daily_goal_hours": 1.0,
            "preferred_difficulty": "challenging",
        }

    def evaluate_task(self, task: dict) -> dict:
        """
        Evaluate whether a task aligns with vision profile.
        Returns {score: float (0-1), reason: str, recommended: bool}
        """
        score = 0.5
        reasons = []

        # Example rules
        title_lower = task.get("title", "").lower()
        if any(p.replace("_", " ") in title_lower for p in self.profile.get("priorities", [])):
            score += 0.3
            reasons.append("Aligns with priority values")

        if any(a.replace("_", " ") in title_lower for a in self.profile.get("avoid", [])):
            score -= 0.3
            reasons.append("Conflicts with avoided patterns")

        score = max(0.0, min(1.0, score))
        return {
            "score": round(score, 2),
            "reason": "; ".join(reasons) or "Neutral evaluation",
            "recommended": score >= 0.4,
        }

    def get_daily_goal(self) -> float:
        return self.profile.get("daily_goal_hours", 1.0)


# Singleton
_engine: VisionEngine | None = None

def get_vision_engine(profile: str = "default") -> VisionEngine:
    global _engine
    if _engine is None:
        _engine = VisionEngine(profile)
    return _engine
