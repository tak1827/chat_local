from typing import Optional, List, Tuple
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import text
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
        # Flush to generate the ID without committing
        self._session.flush()
        return chunk_table.id

    def similar_chunks(
        self,
        embedding: List[float],
        top_k: int = 3,
        threshold: Optional[float] = None,
    ) -> List[Tuple[ChunkTable, float]]:
        """
        Search for chunks in the database that are similar to the embedding using cosine similarity.

        Returns:
            List of tuples containing (ChunkTable, distance) ordered by similarity.
            Distance is cosine distance (0 = identical, 2 = opposite).
        """
        if self._session is None:
            raise RuntimeError("No active session.")

        # Convert embedding list to string format for pgvector
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

        # Use raw SQL query to avoid SQLAlchemy limitations with text() expressions in subqueries
        # This approach directly uses pgvector's cosine distance operator
        # Note: embedding_str is safely formatted (comes from our code, not user input)
        try:
            if threshold is not None:
                # Format embedding directly in SQL string (safe - from our code)
                # Parameterize only threshold and top_k
                sql_query = text(f"""
                    SELECT id, title, content, meta, embedding,
                           embedding <=> '{embedding_str}'::vector AS distance
                    FROM chunk_table
                    WHERE embedding <=> '{embedding_str}'::vector <= :threshold
                    ORDER BY distance
                    LIMIT :top_k
                """)
                result = self._session.execute(
                    sql_query,
                    {
                        "threshold": float(threshold),
                        "top_k": int(top_k),
                    },
                )
            else:
                # Format embedding directly in SQL string (safe - from our code)
                # Parameterize only top_k
                sql_query = text(f"""
                    SELECT id, title, content, meta, embedding,
                           embedding <=> '{embedding_str}'::vector AS distance
                    FROM chunk_table
                    ORDER BY embedding <=> '{embedding_str}'::vector
                    LIMIT :top_k
                """)
                result = self._session.execute(
                    sql_query,
                    {
                        "top_k": int(top_k),
                    },
                )

            # Convert results to ChunkTable objects with distances
            results = []
            for row in result:
                # Create ChunkTable object from row data
                chunk = ChunkTable(
                    id=row.id,
                    title=row.title,
                    content=row.content,
                    meta=row.meta,
                    embedding=row.embedding,
                )
                results.append((chunk, float(row.distance)))

            return results

        except Exception as e:
            # Provide more detailed error information
            error_msg = f"Error in similar_chunks query: {type(e).__name__}: {str(e)}"
            raise RuntimeError(error_msg) from e

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
