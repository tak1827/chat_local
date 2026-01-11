from typing import Optional
from sqlalchemy.orm import sessionmaker, Session
from database import engine
from chunks_table import ChunkTable


class DatabaseClient:
    """Database client for managing chunk storage operations."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the database client.

        Args:
            database_url: Optional database URL. If not provided, uses the engine from database module.
        """
        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)
        self._session: Optional[Session] = None

    def save_chunk(self, chunk_table: ChunkTable) -> int:
        """
        Save a chunk to the database.
        """
        if self._session is None:
            raise RuntimeError(
                "Session not initialized. Use context manager or call start_session() first."
            )
        self._session.add(chunk_table)
        self._session.commit()
        return chunk_table.id

    def start_session(self) -> Session:
        """Start a new database session."""
        if self._session is not None:
            raise RuntimeError(
                "Session already started. Close it first or use context manager."
            )
        self._session = self.Session()
        return self._session

    def close_session(self):
        """Close the current database session."""
        if self._session is not None:
            self._session.close()
            self._session = None

    def commit(self):
        """Commit the current transaction."""
        if self._session is None:
            raise RuntimeError("No active session.")
        self._session.commit()

    def rollback(self):
        """Rollback the current transaction."""
        if self._session is None:
            raise RuntimeError("No active session.")
        self._session.rollback()

    def __enter__(self):
        """Context manager entry."""
        self.start_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close_session()
