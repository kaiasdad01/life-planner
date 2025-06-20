from typing import Optional, List, Dict, Any
from pydantic import BaseModel, UUID4, validator
from datetime import date, datetime


class ScenarioBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_default: bool = False
    projection_months: int = 60
    start_date: date
    life_events: Optional[List[Dict[str, Any]]] = None
    is_private: bool = True
    shared_with_partner: bool = False
    
    @validator('projection_months')
    def validate_projection_months(cls, v):
        if v < 1 or v > 120:  # Max 10 years
            raise ValueError('Projection months must be between 1 and 120')
        return v


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    projection_months: Optional[int] = None
    start_date: Optional[date] = None
    life_events: Optional[List[Dict[str, Any]]] = None
    is_private: Optional[bool] = None
    shared_with_partner: Optional[bool] = None


class ScenarioInDB(ScenarioBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Scenario(ScenarioInDB):
    pass


class ScenarioComponentBase(BaseModel):
    financial_component_id: UUID4
    variable_overrides: Optional[Dict[str, Any]] = None
    start_date_override: Optional[date] = None
    end_date_override: Optional[date] = None


class ScenarioComponentCreate(ScenarioComponentBase):
    pass


class ScenarioComponentUpdate(BaseModel):
    variable_overrides: Optional[Dict[str, Any]] = None
    start_date_override: Optional[date] = None
    end_date_override: Optional[date] = None


class ScenarioComponentInDB(ScenarioComponentBase):
    id: UUID4
    scenario_id: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True


class ScenarioComponent(ScenarioComponentInDB):
    pass


class ScenarioWithComponents(Scenario):
    scenario_components: List[ScenarioComponent] = [] 