from typing import Optional, Dict, Any
from pydantic import BaseModel, UUID4, validator
from datetime import date, datetime


class FinancialComponentBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str  # income, expense, asset, liability
    formula: str
    variables: Dict[str, Any]
    start_date: date
    end_date: Optional[date] = None
    frequency: str = "monthly"  # monthly, quarterly, yearly, one-time
    seasonal_factors: Optional[Dict[str, float]] = None
    is_private: bool = True
    shared_with_partner: bool = False
    
    @validator('category')
    def validate_category(cls, v):
        allowed_categories = ['income', 'expense', 'asset', 'liability']
        if v not in allowed_categories:
            raise ValueError(f'Category must be one of: {allowed_categories}')
        return v
    
    @validator('frequency')
    def validate_frequency(cls, v):
        allowed_frequencies = ['monthly', 'quarterly', 'yearly', 'one-time']
        if v not in allowed_frequencies:
            raise ValueError(f'Frequency must be one of: {allowed_frequencies}')
        return v
    
    @validator('formula')
    def validate_formula(cls, v):
        if len(v) > 1000:  # Max formula length
            raise ValueError('Formula too long (max 1000 characters)')
        return v


class FinancialComponentCreate(FinancialComponentBase):
    pass


class FinancialComponentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    formula: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    frequency: Optional[str] = None
    seasonal_factors: Optional[Dict[str, float]] = None
    is_private: Optional[bool] = None
    shared_with_partner: Optional[bool] = None


class FinancialComponentInDB(FinancialComponentBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FinancialComponent(FinancialComponentInDB):
    pass


class FinancialComponentWithCalculation(FinancialComponent):
    calculated_value: Optional[float] = None
    calculation_error: Optional[str] = None 