from sqlalchemy import Column, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..core.database import Base

class Partnership(Base):
    __tablename__ = "partnerships"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user1_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user2_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint('user1_id', 'user2_id', name='uq_user_pair'),
    )

    def __repr__(self):
        return f"<Partnership(user1_id={self.user1_id}, user2_id={self.user2_id}, active={self.is_active})>" 