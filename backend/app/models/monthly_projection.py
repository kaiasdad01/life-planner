from sqlalchemy import Column, DateTime, JSON, ForeignKey, Date, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class MonthlyProjection(Base):
    __tablename__ = "monthly_projections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=False, index=True)
    month = Column(Date, nullable=False, index=True)
    
    # Financial summary
    total_income = Column(DECIMAL(15, 2), nullable=False, default=0)
    total_expenses = Column(DECIMAL(15, 2), nullable=False, default=0)
    net_flow = Column(DECIMAL(15, 2), nullable=False, default=0)
    
    # Asset and liability tracking
    running_balance = Column(DECIMAL(15, 2), nullable=False, default=0)
    
    # Component breakdown
    component_details = Column(JSON, nullable=False)  # Detailed breakdown by component
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<MonthlyProjection(month={self.month}, net_flow={self.net_flow})>" 