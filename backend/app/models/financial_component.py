from sqlalchemy import Column, String, DateTime, Text, JSON, Date, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class FinancialComponent(Base):
    __tablename__ = "financial_components"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Component metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)  # income, expense, asset, liability
    
    # Formula and variables
    formula = Column(Text, nullable=False)  # User-defined Python formula
    variables = Column(JSON, nullable=False)  # {"base_salary": 100000, "bonus_rate": 0.15}
    
    # Timing and frequency
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # None for ongoing
    frequency = Column(String(50), default="monthly")  # monthly, quarterly, yearly, one-time
    
    # Seasonal variations (optional)
    seasonal_factors = Column(JSON, nullable=True)  # {"jan": 1.1, "dec": 0.9}
    
    # Visibility and sharing
    is_private = Column(Boolean, default=True)
    shared_with_partner = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="financial_components")
    scenario_components = relationship("ScenarioComponent", back_populates="financial_component")
    
    def __repr__(self):
        return f"<FinancialComponent(id={self.id}, name={self.name}, category={self.category})>" 