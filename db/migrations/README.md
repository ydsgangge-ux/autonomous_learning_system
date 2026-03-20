# Run: alembic init db/migrations
# Then replace env.py target_metadata with:
#   from db.models import Base
#   target_metadata = Base.metadata
#
# This file is a placeholder. Initialize Alembic with:
#   alembic init db/migrations
#   alembic revision --autogenerate -m "init"
#   alembic upgrade head
