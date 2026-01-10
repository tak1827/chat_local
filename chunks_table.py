from sqlalchemy import Column, Integer, Text, JSON
from pgvector.sqlalchemy import Vector
from database import Base


class ChunkTable(Base):
    __tablename__ = "chunk_table"

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    meta = Column(JSON, nullable=True)

    # ministral-3:3b → 3072 dims
    embedding = Column(Vector(3072), nullable=False)
