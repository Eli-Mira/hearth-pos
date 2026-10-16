"""Database engine and session management."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


_engine: Engine | None = None
_session_factory: sessionmaker | None = None
_test_engine: Engine | None = None
_test_session_factory: sessionmaker | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False},
        )
        # Enable WAL mode and foreign keys for SQLite
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
    return _engine


def get_test_engine() -> Engine:
    """Get an in-memory SQLite engine for testing."""
    global _test_engine
    if _test_engine is None:
        _test_engine = create_engine(
            "sqlite:///:memory:",
            echo=False,
            future=True,
            connect_args={"check_same_thread": False},
        )
        @event.listens_for(_test_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
    return _test_engine


def get_session_factory() -> sessionmaker:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            class_=Session,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


def get_test_session_factory() -> sessionmaker:
    global _test_session_factory
    if _test_session_factory is None:
        _test_session_factory = sessionmaker(
            bind=get_test_engine(),
            class_=Session,
            expire_on_commit=False,
            autoflush=False,
        )
    return _test_session_factory


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def test_session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope for tests using in-memory database."""
    session = get_test_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Initialize database - create tables if they don't exist."""
    from app.db.models import Base
    Base.metadata.create_all(get_engine())


def init_test_db() -> None:
    """Initialize test database - create tables in memory."""
    from app.db.models import Base
    Base.metadata.create_all(get_test_engine())


def reset_db() -> None:
    """Drop and recreate all tables (for testing)."""
    from app.db.models import Base
    Base.metadata.drop_all(get_engine())
    Base.metadata.create_all(get_engine())


def reset_test_db() -> None:
    """Drop and recreate test database tables."""
    from app.db.models import Base
    Base.metadata.drop_all(get_test_engine())
    Base.metadata.create_all(get_test_engine())