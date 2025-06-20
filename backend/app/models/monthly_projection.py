from sqlalchemy import Column, DateTime, JSON, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class MonthlyProjection(Base):
    __tablename__ = "monthly_projections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=False)
    
    # Projection period
    projection_date = Column(Date, nullable=False)  # First day of the month
    month_number = Column(Integer, nullable=False)  # 1, 2, 3... for easy querying
    
    # Financial summary
    total_income = Column(DECIMAL(15, 2), nullable=False, default=0)
    total_expenses = Column(DECIMAL(15, 2), nullable=False, default=0)
    net_cash_flow = Column(DECIMAL(15, 2), nullable=False, default=0)
    
    # Asset and liability tracking
    total_assets = Column(DECIMAL(15, 2), nullable=False, default=0)
    total_liabilities = Column(DECIMAL(15, 2), nullable=False, default=0)
    net_worth = Column(DECIMAL(15, 2), nullable=False, default=0)
    
    # Component breakdown
    component_breakdown = Column(JSON, nullable=False)  # Detailed breakdown by component
    
    # Life events affecting this month
    active_life_events = Column(JSON, nullable=True)  # List of life events active this month
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="monthly_projections")
    scenario = relationship("Scenario", back_populates="monthly_projections")
    
    def __repr__(self):
        return f"<MonthlyProjection(date={self.projection_date}, net_worth={self.net_worth})>" 