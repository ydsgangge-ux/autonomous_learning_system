"""
Web UI 服务器 - 提供静态文件和页面
"""
import os
from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

# 获取 Web UI 目录
WEB_UI_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_UI_DIR / "templates"
STATIC_DIR = WEB_UI_DIR / "static"


@router.get("/")
async def serve_index():
    """V2 学习系统主页"""
    v2_file = TEMPLATES_DIR / "v2_learning.html"
    if v2_file.exists():
        return FileResponse(str(v2_file))
    return {"error": "v2_learning.html not found"}


@router.get("/v1")
async def serve_v1():
    """V1 旧版主页"""
    index_file = TEMPLATES_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"error": "index.html not found"}


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "web-ui"}
