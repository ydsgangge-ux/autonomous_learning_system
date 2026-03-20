from fastapi import APIRouter
from interfaces.api.endpoints import qa, perception, exploration, planning, knowledge_cards, verification, synthesis

router = APIRouter()

router.include_router(qa.router, prefix="/qa", tags=["QA"])
router.include_router(perception.router, prefix="/perception", tags=["Perception"])
router.include_router(exploration.router, prefix="/exploration", tags=["Exploration"])
router.include_router(planning.router, prefix="/planning", tags=["Planning"])
router.include_router(knowledge_cards.router, prefix="/knowledge", tags=["Knowledge Cards"])
router.include_router(verification.router, prefix="/verify", tags=["Verification"])
router.include_router(verification.router, prefix="/sandbox", tags=["Sandbox"])
router.include_router(synthesis.router, prefix="/synthesis", tags=["Cross-Domain Synthesis"])
