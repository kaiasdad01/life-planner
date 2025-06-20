from typing import Optional, Dict, Any
from pydantic import BaseModel, UUID4
from datetime import date, datetime
from decimal import Decimal


class MonthlyProjectionBase(BaseModel):
    projection_date: date
    month_number: int
    total_income: Decimal
    total_expenses: Decimal
    net_cash_flow: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    component_breakdown: Dict[str, Any]
    active_life_events: Optional[Dict[str, Any]] = None


class MonthlyProjectionCreate(MonthlyProjectionBase):
    pass


class MonthlyProjectionUpdate(BaseModel):
    total_income: Optional[Decimal] = None
    total_expenses: Optional[Decimal] = None
    net_cash_flow: Optional[Decimal] = None
    total_assets: Optional[Decimal] = None
    total_liabilities: Optional[Decimal] = None
    net_worth: Optional[Decimal] = None
    component_breakdown: Optional[Dict[str, Any]] = None
    active_life_events: Optional[Dict[str, Any]] = None


class MonthlyProjectionInDB(MonthlyProjectionBase):
    id: UUID4
    user_id: UUID4
    scenario_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MonthlyProjection(MonthlyProjectionInDB):
    pass


class ProjectionSummary(BaseModel):
    """Summary statistics for a projection period"""
    start_date: date
    end_date: date
    total_months: int
    average_monthly_income: Decimal
    average_monthly_expenses: Decimal
    average_monthly_cash_flow: Decimal
    final_net_worth: Decimal
    net_worth_change: Decimal
    best_month: Optional[date] = None
    worst_month: Optional[date] = None 