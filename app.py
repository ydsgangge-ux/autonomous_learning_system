"""
FastAPI application factory.
- Sets up lifespan (DB init, background tasks, DB events)
- Registers all API routes
"""
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

try:
    from core.settings import settings
except Exception as e:
    print(f"Cannot import settings: {e}")
    sys.exit(1)

try:
    from db.session import init_db
    from db.events import register_events
except Exception as e:
    print(f"Cannot import database module: {e}")
    sys.exit(1)

# 后台任务（可能因为向量存储问题而失败）
try:
    from background.startup import start_background_tasks, stop_background_tasks
    BACKGROUND_TASKS_AVAILABLE = True
except Exception as e:
    print(f"Background tasks not available: {e}")
    BACKGROUND_TASKS_AVAILABLE = False

# API 路由 - 不阻塞系统启动
api_router = None
try:
    from interfaces.api.router import router as api_router
except Exception as e:
    print(f"API router not available: {e}")

try:
    from web_ui.server import router as web_ui_router
    WEB_UI_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Web UI 模块不可用: {e}")
    print("   网页界面将不可用")
    WEB_UI_AVAILABLE = False

# V2 学习系统（main_v2 包装）
try:
    from interfaces.api.endpoints import v2_learning
    V2_LEARNING_AVAILABLE = True
except Exception as e:
    print(f"⚠️  V2 学习系统模块不可用: {e}")
    print("   V2 界面将不可用")
    V2_LEARNING_AVAILABLE = False

# AGI 进化编排层
EVOLUTION_API_AVAILABLE = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 正在启动系统...")
    try:
        await init_db()
        print("✅ 数据库初始化完成")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        raise

    try:
        register_events()
        print("✅ 数据库事件注册完成")
    except Exception as e:
        print(f"❌ 数据库事件注册失败: {e}")
        import traceback
        traceback.print_exc()
        raise

    try:
        if BACKGROUND_TASKS_AVAILABLE:
            start_background_tasks()
            print("✅ 后台任务启动完成")
        else:
            print("⚠️  后台任务已禁用（Python 3.14 兼容性问题）")
    except Exception as e:
        print(f"❌ 后台任务启动失败: {e}")
        import traceback
        traceback.print_exc()
        print("⚠️  系统继续启动，但后台任务不可用")

    print("✅ 系统启动完成！")
    yield

    # Shutdown
    print("🛑 正在关闭系统...")
    if BACKGROUND_TASKS_AVAILABLE:
        try:
            stop_background_tasks()
            print("✅ 后台任务已停止")
        except Exception as e:
            print(f"⚠️  关闭后台任务时出错: {e}")
    else:
        print("✅ 系统关闭")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API 路由
    if api_router:
        app.include_router(api_router, prefix="/api/v1")
    
    # V2 学习系统 API
    if V2_LEARNING_AVAILABLE:
        app.include_router(v2_learning.router, prefix="/api/v1")
        print("[OK] V2 Learning API registered")

    # AGI 进化编排层 API
    try:
        from core.orchestrator import EvolutionOrchestrator
        from pydantic import BaseModel
        
        class EvolveRequest(BaseModel):
            content: str
            target_domain: str = "工业制造"
            context: str = ""
            auto_synthesis: bool = True
        
        @app.post("/api/v2/evolve")
        async def process_evolution(request: EvolveRequest):
            """
            一键打包触发：从碎片信息进化为深度知识节点
            
            完整流程：因果提取 -> 沙盒验证 -> 跨域合成 -> 元认知审计
            """
            orchestrator = EvolutionOrchestrator()
            
            result = await orchestrator.evolve_knowledge(
                raw_input=request.content,
                target_domain=request.target_domain,
                context=request.context,
                auto_synthesis=request.auto_synthesis
            )
            
            return {
                "status": "success",
                "original_input": result["original_input"],
                "final_output": result["final_output"],
                "refinement_count": result["refinement_count"],
                "processing_time_ms": result["processing_time_ms"],
                "insights": {
                    "causal_chains": result.get("causal_logic", {}).get("chains", []),
                    "synthesis": result.get("synthesis_insight", {}).get("insight", {}).get("synthesized_explanation", "") if result.get("synthesis_insight") else None,
                    "verification": result.get("verification", {})
                },
                "audit": result["audit"]
            }
        
        @app.post("/api/v2/evolve/batch")
        async def process_evolution_batch(request: dict, target_domain: str = "工业制造"):
            """
            批量进化多个输入
            """
            contents = request.get("contents", [])
            orchestrator = EvolutionOrchestrator()
            
            results = await orchestrator.evolve_batch(
                inputs=contents,
                target_domain=target_domain
            )
            
            return {
                "status": "success",
                "count": len(results),
                "results": results
            }
        
        @app.get("/api/v2/evolve/domains")
        async def get_available_domains():
            """获取可用的领域列表"""
            from core.synthesis import DOMAIN_ABSTRACTIONS
            return {
                "domains": list(DOMAIN_ABSTRACTIONS.keys()),
                "domain_details": DOMAIN_ABSTRACTIONS
            }
        
        print("[OK] AGI Evolution API registered")
        EVOLUTION_API_AVAILABLE = True
    except Exception as e:
        print(f"⚠️  AGI Evolution API 不可用: {e}")
        EVOLUTION_API_AVAILABLE = False

    # Web UI 路由 - 根路径直接返回V2新版页面
    from pathlib import Path
    from fastapi.responses import FileResponse
    
    @app.get("/")
    async def serve_v2_index():
        """直接返回V2新版学习页面"""
        v2_file = Path(__file__).parent / "web_ui" / "templates" / "v2_learning.html"
        return FileResponse(str(v2_file))
    
    if WEB_UI_AVAILABLE:
        app.include_router(web_ui_router)
        # 静态文件挂载
        static_dir = Path(__file__).parent / "web_ui" / "static"
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "app": settings.app_name,
            "background_tasks": BACKGROUND_TASKS_AVAILABLE,
            "v2_learning": V2_LEARNING_AVAILABLE,
            "evolution_api": EVOLUTION_API_AVAILABLE
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print(f"[START] {settings.app_name}")
    print("=" * 60)
    print(f"[INFO] API docs: http://localhost:8000/docs")
    print(f"[INFO] Health check: http://localhost:8000/health")
    print(f"[INFO] CLI Q&A: python -m interfaces.cli qa")
    if not BACKGROUND_TASKS_AVAILABLE:
        print("[WARN] Background tasks disabled (Python 3.14 compatibility issue)")
    print("=" * 60)
    print()

    try:
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=settings.debug)
    except KeyboardInterrupt:
        print("\n[INFO] User interrupted, exiting...")
    except Exception as e:
        print(f"\n[ERROR] Startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
