from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Partnership fields
    partner_id = Column(UUID(as_uuid=True), nullable=True)
    partnership_status = Column(String(50), default="single")  # single, partnered, pending
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    financial_components = relationship("FinancialComponent", back_populates="user")
    scenarios = relationship("Scenario", back_populates="user")
    monthly_projections = relationship("MonthlyProjection", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>" 