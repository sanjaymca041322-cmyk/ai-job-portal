from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# Import models so SQLAlchemy registers them with Base.metadata
from app.modules.candidates.model import Candidate
from app.modules.jobs.model import Job
from app.modules.users.model import User


if engine is None:
    raise RuntimeError("Database engine is not configured.")

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Database tables created successfully.")
print("Tables:", ", ".join(Base.metadata.tables.keys()))
