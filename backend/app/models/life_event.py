from sqlalchemy import Column, String, DateTime, Text, JSON, Date, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class LifeEvent(Base):
    __tablename__ = "life_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Event metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String(100), nullable=False)  # job_change, baby, house_purchase, etc.
    
    # Timing
    event_date = Column(Date, nullable=False)
    is_recurring = Column(Boolean, default=False)  # For annual events like bonuses
    
    # Financial impact
    component_impacts = Column(JSON, nullable=False)  # How this affects existing components
    new_components = Column(JSON, nullable=True)  # New components to create
    
    # Example component_impacts:
    # {
    #   "component_id": "uuid",
    #   "variable_changes": {"base_salary": 120000},
    #   "start_date_change": "2026-01-01"
    # }
    
    # Visibility and sharing
    is_private = Column(Boolean, default=True)
    shared_with_partner = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<LifeEvent(id={self.id}, name={self.name}, date={self.event_date})>" 