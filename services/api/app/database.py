import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://inspect:inspect@localhost:5432/inspect_ai")

try:
    if DATABASE_URL.startswith("postgresql"):
        # Test postgres engine
        engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            pass
    else:
        engine = create_engine(DATABASE_URL)
except Exception:
    # Fallback to persistent SQLite database
    SQLITE_PATH = os.path.join(os.path.dirname(__file__), "..", "inspect_ai.db")
    DATABASE_URL = f"sqlite:///{os.path.abspath(SQLITE_PATH)}"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
