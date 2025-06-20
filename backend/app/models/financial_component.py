from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID, DECIMAL
from sqlalchemy.sql import func
import uuid
import enum
from ..core.database import Base

class ComponentType(enum.Enum):
    income = "income"
    expense = "expense"
    goal = "goal"

class FinancialComponent(Base):
    __tablename__ = "financial_components"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(ComponentType), nullable=False, index=True)
    formula = Column(Text, nullable=False)
    variables = Column(JSON, nullable=False)
    schedule = Column(JSON, nullable=False)  # {"start_date": ..., "end_date": ..., "frequency": ...}
    is_shared_with_partner = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<FinancialComponent(id={self.id}, name={self.name}, type={self.type})>" 