from typing import Optional, List, Dict, Any
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

    def save_chunk(
        self,
        title: str,
        content: str,
        embedding: List[float],
        meta: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Save a chunk to the database.

        Args:
            title: Title of the chunk
            content: Content/text of the chunk
            embedding: Embedding vector (list of floats)
            meta: Optional metadata dictionary

        Returns:
            The ID of the saved chunk

        Raises:
            Exception: If the database operation fails
        """
        if self._session is None:
            raise RuntimeError(
                "Session not initialized. Use context manager or call start_session() first."
            )

        chunk_record = ChunkTable(
            title=title,
            content=content,
            meta=meta or {},
            embedding=embedding,
        )
        self._session.add(chunk_record)
        self._session.commit()
        return chunk_record.id

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
