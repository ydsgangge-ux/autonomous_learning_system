"""
数据库迁移脚本 - 添加元认知表
================================

用法: python db/migrate_add_reflections.py

此脚本会创建 meta_reflections 表，用于存储元认知反思记录。
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def migrate():
    """执行迁移"""
    from db.session import async_engine
    from db.models import Base, MetaReflection
    
    print("开始数据库迁移...")
    print(f"数据库: {async_engine.url}")
    
    # 检查表是否已存在
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # 检查表是否存在
        inspector = await conn.run_sync(lambda conn: inspect(conn))
        existing_tables = inspector.get_table_names()
        
        if "meta_reflections" in existing_tables:
            print("✓ meta_reflections 表已存在")
        else:
            await conn.run_sync(MetaReflection.__table__.create)
            print("✓ 成功创建 meta_reflections 表")
    
    print("\n元认知系统已就绪！")


if __name__ == "__main__":
    from sqlalchemy import inspect
    asyncio.run(migrate())
