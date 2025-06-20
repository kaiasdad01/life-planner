from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class Scenario(Base):
    __tablename__ = "scenarios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Scenario metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Scenario settings
    component_ids = Column(JSON, nullable=False)  # List of component UUIDs
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Scenario(id={self.id}, name={self.name})>"


class ScenarioComponent(Base):
    __tablename__ = "scenario_components"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=False)
    financial_component_id = Column(UUID(as_uuid=True), ForeignKey("financial_components.id"), nullable=False)
    
    # Component overrides for this scenario
    variable_overrides = Column(JSON, nullable=True)  # Override component variables
    start_date_override = Column(Date, nullable=True)
    end_date_override = Column(Date, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    scenario = relationship("Scenario", back_populates="scenario_components")
    financial_component = relationship("FinancialComponent", back_populates="scenario_components")
    
    def __repr__(self):
        return f"<ScenarioComponent(scenario_id={self.scenario_id}, component_id={self.financial_component_id})>" 