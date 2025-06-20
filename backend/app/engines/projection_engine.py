from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import Scenario, FinancialComponent, MonthlyProjection, ScenarioComponent
from ..schemas import MonthlyProjectionCreate
from .formula_engine import formula_engine


class ProjectionEngine:
    """Engine for calculating financial projections"""
    
    def __init__(self):
        self.formula_engine = formula_engine
    
    async def calculate_scenario_projection(
        self, 
        db: AsyncSession, 
        scenario: Scenario,
        user_id: str
    ) -> List[MonthlyProjectionCreate]:
        """Calculate monthly projections for a scenario"""
        
        # Get scenario components
        stmt = select(ScenarioComponent).where(ScenarioComponent.scenario_id == scenario.id)
        result = await db.execute(stmt)
        scenario_components = result.scalars().all()
        
        # Get financial components
        component_ids = [sc.financial_component_id for sc in scenario_components]
        stmt = select(FinancialComponent).where(FinancialComponent.id.in_(component_ids))
        result = await db.execute(stmt)
        financial_components = {fc.id: fc for fc in result.scalars().all()}
        
        projections = []
        current_date = scenario.start_date
        
        for month_num in range(1, scenario.projection_months + 1):
            # Calculate component values for this month
            component_breakdown = {}
            total_income = Decimal('0')
            total_expenses = Decimal('0')
            total_assets = Decimal('0')
            total_liabilities = Decimal('0')
            
            for sc in scenario_components:
                fc = financial_components.get(sc.financial_component_id)
                if not fc:
                    continue
                
                # Check if component is active this month
                if not self._is_component_active(fc, sc, current_date):
                    continue
                
                # Calculate component value
                try:
                    value = self._calculate_component_value(fc, sc, current_date, month_num)
                    component_breakdown[fc.name] = {
                        'value': value,
                        'category': fc.category,
                        'component_id': str(fc.id)
                    }
                    
                    # Add to totals
                    if fc.category == 'income':
                        total_income += value
                    elif fc.category == 'expense':
                        total_expenses += value
                    elif fc.category == 'asset':
                        total_assets += value
                    elif fc.category == 'liability':
                        total_liabilities += value
                        
                except Exception as e:
                    # Log error but continue with other components
                    component_breakdown[fc.name] = {
                        'value': Decimal('0'),
                        'category': fc.category,
                        'component_id': str(fc.id),
                        'error': str(e)
                    }
            
            # Calculate net values
            net_cash_flow = total_income - total_expenses
            net_worth = total_assets - total_liabilities
            
            # Create projection
            projection = MonthlyProjectionCreate(
                projection_date=current_date,
                month_number=month_num,
                total_income=total_income,
                total_expenses=total_expenses,
                net_cash_flow=net_cash_flow,
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                net_worth=net_worth,
                component_breakdown=component_breakdown,
                active_life_events=self._get_active_life_events(scenario, current_date)
            )
            
            projections.append(projection)
            
            # Move to next month
            current_date = self._add_months(current_date, 1)
        
        return projections
    
    def _is_component_active(
        self, 
        component: FinancialComponent, 
        scenario_component: ScenarioComponent, 
        current_date: date
    ) -> bool:
        """Check if a component is active for the given date"""
        
        # Use scenario overrides if available
        start_date = scenario_component.start_date_override or component.start_date
        end_date = scenario_component.end_date_override or component.end_date
        
        # Check date range
        if current_date < start_date:
            return False
        
        if end_date and current_date > end_date:
            return False
        
        return True
    
    def _calculate_component_value(
        self, 
        component: FinancialComponent, 
        scenario_component: ScenarioComponent, 
        current_date: date, 
        month_num: int
    ) -> Decimal:
        """Calculate the value of a component for a specific month"""
        
        # Merge variables with scenario overrides
        variables = component.variables.copy()
        if scenario_component.variable_overrides:
            variables.update(scenario_component.variable_overrides)
        
        # Add time-based variables
        variables.update({
            'month': month_num,
            'year': current_date.year,
            'month_name': current_date.strftime('%B').lower(),
            'days_in_month': (current_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        })
        
        # Evaluate formula
        base_value = self.formula_engine.evaluate_formula(component.formula, variables)
        
        # Apply frequency adjustments
        if component.frequency == 'yearly':
            # Only apply in January
            if current_date.month != 1:
                return Decimal('0')
            base_value = base_value / 12  # Distribute over 12 months
        elif component.frequency == 'quarterly':
            # Only apply in first month of each quarter
            if current_date.month not in [1, 4, 7, 10]:
                return Decimal('0')
            base_value = base_value / 3  # Distribute over 3 months
        elif component.frequency == 'one-time':
            # Only apply in the first month
            if month_num > 1:
                return Decimal('0')
        
        # Apply seasonal factors
        if component.seasonal_factors:
            month_key = current_date.strftime('%b').lower()
            if month_key in component.seasonal_factors:
                base_value *= Decimal(str(component.seasonal_factors[month_key]))
        
        return base_value
    
    def _get_active_life_events(self, scenario: Scenario, current_date: date) -> Optional[Dict[str, Any]]:
        """Get life events active for the current date"""
        if not scenario.life_events:
            return None
        
        active_events = []
        for event in scenario.life_events:
            event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
            if event_date <= current_date:
                active_events.append(event)
        
        return {'active_events': active_events} if active_events else None
    
    def _add_months(self, date_obj: date, months: int) -> date:
        """Add months to a date, handling year rollover"""
        year = date_obj.year + ((date_obj.month - 1 + months) // 12)
        month = ((date_obj.month - 1 + months) % 12) + 1
        return date_obj.replace(year=year, month=month)
    
    async def recalculate_scenario(
        self, 
        db: AsyncSession, 
        scenario_id: str,
        user_id: str
    ) -> List[MonthlyProjectionCreate]:
        """Recalculate projections for a scenario and update database"""
        
        # Get scenario
        stmt = select(Scenario).where(Scenario.id == scenario_id, Scenario.user_id == user_id)
        result = await db.execute(stmt)
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            raise ValueError("Scenario not found")
        
        # Calculate new projections
        projections = await self.calculate_scenario_projection(db, scenario, user_id)
        
        # Delete existing projections
        stmt = select(MonthlyProjection).where(
            MonthlyProjection.scenario_id == scenario_id,
            MonthlyProjection.user_id == user_id
        )
        result = await db.execute(stmt)
        existing_projections = result.scalars().all()
        
        for projection in existing_projections:
            await db.delete(projection)
        
        # Create new projections
        new_projections = []
        for projection_data in projections:
            projection = MonthlyProjection(
                user_id=user_id,
                scenario_id=scenario_id,
                **projection_data.dict()
            )
            db.add(projection)
            new_projections.append(projection)
        
        await db.commit()
        
        return projections


# Global instance
projection_engine = ProjectionEngine() 