from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from core.settings import settings

Base = declarative_base()

# Convert standard database URL to async (if needed)
def get_async_database_url(url: str) -> str:
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    get_async_database_url(settings.database_url),
    echo=settings.database_echo,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """Dependency for FastAPI to get DB session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Initialize database tables."""
    from db.models import KnowledgeNode  # 导入所有模型以注册它们
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
