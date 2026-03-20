import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    from db.session import init_db
    print("初始化数据库表...")
    await init_db()
    print("完成!")

if __name__ == "__main__":
    asyncio.run(main())
