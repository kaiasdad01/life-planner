from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from uuid import UUID

from ....core.database import get_db
from ....models import User, Scenario, ScenarioComponent, MonthlyProjection, Partnership, FinancialComponent
from ....schemas import (
    Scenario as ScenarioSchema,
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioWithComponents,
    MonthlyProjection as MonthlyProjectionSchema,
    ProjectionSummary
)
from ....engines.projection_engine import projection_engine
from ...deps import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[ScenarioSchema])
async def get_scenarios(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get user's scenarios"""
    
    stmt = select(Scenario).where(
        Scenario.user_id == current_user.id
    ).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    scenarios = result.scalars().all()
    
    return scenarios


@router.post("/", response_model=ScenarioSchema)
async def create_scenario(
    scenario_in: ScenarioCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a new scenario"""
    
    # If this is the default scenario, unset other defaults
    if scenario_in.is_default:
        stmt = select(Scenario).where(
            Scenario.user_id == current_user.id,
            Scenario.is_default == True
        )
        result = await db.execute(stmt)
        existing_defaults = result.scalars().all()
        
        for existing in existing_defaults:
            existing.is_default = False
    
    # Create scenario
    scenario = Scenario(
        user_id=current_user.id,
        **scenario_in.dict()
    )
    
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)
    
    return scenario


@router.get("/{scenario_id}", response_model=ScenarioWithComponents)
async def get_scenario(
    scenario_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get a specific scenario with its components"""
    
    # Get scenario
    stmt = select(Scenario).where(
        Scenario.id == scenario_id,
        Scenario.user_id == current_user.id
    )
    result = await db.execute(stmt)
    scenario = result.scalar_one_or_none()
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    
    # Get scenario components
    stmt = select(ScenarioComponent).where(
        ScenarioComponent.scenario_id == scenario_id
    )
    result = await db.execute(stmt)
    scenario_components = result.scalars().all()
    
    # Create response
    response_data = ScenarioWithComponents(
        **scenario.__dict__,
        scenario_components=scenario_components
    )
    
    return response_data


@router.put("/{scenario_id}", response_model=ScenarioSchema)
async def update_scenario(
    scenario_id: UUID,
    scenario_in: ScenarioUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update a scenario"""
    
    # Get existing scenario
    stmt = select(Scenario).where(
        Scenario.id == scenario_id,
        Scenario.user_id == current_user.id
    )
    result = await db.execute(stmt)
    scenario = result.scalar_one_or_none()
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    
    # Handle default scenario changes
    if scenario_in.is_default and not scenario.is_default:
        # Unset other defaults
        stmt = select(Scenario).where(
            Scenario.user_id == current_user.id,
            Scenario.is_default == True,
            Scenario.id != scenario_id
        )
        result = await db.execute(stmt)
        existing_defaults = result.scalars().all()
        
        for existing in existing_defaults:
            existing.is_default = False
    
    # Update scenario
    update_data = scenario_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scenario, field, value)
    
    await db.commit()
    await db.refresh(scenario)
    
    return scenario


@router.delete("/{scenario_id}")
async def delete_scenario(
    scenario_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Delete a scenario"""
    
    # Get existing scenario
    stmt = select(Scenario).where(
        Scenario.id == scenario_id,
        Scenario.user_id == current_user.id
    )
    result = await db.execute(stmt)
    scenario = result.scalar_one_or_none()
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    
    # Delete associated projections first
    stmt = select(MonthlyProjection).where(
        MonthlyProjection.scenario_id == scenario_id
    )
    result = await db.execute(stmt)
    projections = result.scalars().all()
    
    for projection in projections:
        await db.delete(projection)
    
    # Delete scenario components
    stmt = select(ScenarioComponent).where(
        ScenarioComponent.scenario_id == scenario_id
    )
    result = await db.execute(stmt)
    components = result.scalars().all()
    
    for component in components:
        await db.delete(component)
    
    # Delete scenario
    await db.delete(scenario)
    await db.commit()
    
    return {"message": "Scenario deleted"}


@router.post("/{scenario_id}/calculate")
async def calculate_scenario(
    scenario_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Calculate projections for a scenario"""
    
    try:
        projections = await projection_engine.recalculate_scenario(
            db, str(scenario_id), str(current_user.id)
        )
        
        return {
            "message": f"Calculated {len(projections)} months of projections",
            "projections_count": len(projections)
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calculation failed: {str(e)}"
        )


@router.get("/{scenario_id}/projections", response_model=List[MonthlyProjectionSchema])
async def get_scenario_projections(
    scenario_id: UUID,
    skip: int = 0,
    limit: int = 60,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get projections for a scenario"""
    
    # Verify scenario exists and belongs to user
    stmt = select(Scenario).where(
        Scenario.id == scenario_id,
        Scenario.user_id == current_user.id
    )
    result = await db.execute(stmt)
    scenario = result.scalar_one_or_none()
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    
    # Get projections
    stmt = select(MonthlyProjection).where(
        MonthlyProjection.scenario_id == scenario_id,
        MonthlyProjection.user_id == current_user.id
    ).order_by(MonthlyProjection.month_number).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    projections = result.scalars().all()
    
    return projections


@router.get("/{scenario_id}/summary", response_model=ProjectionSummary)
async def get_scenario_summary(
    scenario_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get summary statistics for a scenario"""
    
    # Verify scenario exists and belongs to user
    stmt = select(Scenario).where(
        Scenario.id == scenario_id,
        Scenario.user_id == current_user.id
    )
    result = await db.execute(stmt)
    scenario = result.scalar_one_or_none()
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    
    # Get all projections for the scenario
    stmt = select(MonthlyProjection).where(
        MonthlyProjection.scenario_id == scenario_id,
        MonthlyProjection.user_id == current_user.id
    ).order_by(MonthlyProjection.month_number)
    
    result = await db.execute(stmt)
    projections = result.scalars().all()
    
    if not projections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No projections found for this scenario"
        )
    
    # Calculate summary statistics
    from decimal import Decimal
    
    total_months = len(projections)
    total_income = sum(p.total_income for p in projections)
    total_expenses = sum(p.total_expenses for p in projections)
    total_cash_flow = sum(p.net_cash_flow for p in projections)
    
    average_monthly_income = total_income / total_months
    average_monthly_expenses = total_expenses / total_months
    average_monthly_cash_flow = total_cash_flow / total_months
    
    final_net_worth = projections[-1].net_worth
    initial_net_worth = projections[0].net_worth
    net_worth_change = final_net_worth - initial_net_worth
    
    # Find best and worst months
    best_month = max(projections, key=lambda p: p.net_cash_flow)
    worst_month = min(projections, key=lambda p: p.net_cash_flow)
    
    return ProjectionSummary(
        start_date=projections[0].projection_date,
        end_date=projections[-1].projection_date,
        total_months=total_months,
        average_monthly_income=average_monthly_income,
        average_monthly_expenses=average_monthly_expenses,
        average_monthly_cash_flow=average_monthly_cash_flow,
        final_net_worth=final_net_worth,
        net_worth_change=net_worth_change,
        best_month=best_month.projection_date,
        worst_month=worst_month.projection_date
    )


@router.get("/shared", response_model=List[ScenarioSchema])
async def get_shared_scenarios(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get scenarios shared with the current user by their active partner(s)."""
    # Find active partnerships
    stmt = select(Partnership).where(
        or_(Partnership.user1_id == current_user.id, Partnership.user2_id == current_user.id),
        Partnership.is_active == True
    )
    result = await db.execute(stmt)
    partnerships = result.scalars().all()
    partner_ids = set()
    for p in partnerships:
        if p.user1_id == current_user.id:
            partner_ids.add(p.user2_id)
        else:
            partner_ids.add(p.user1_id)
    if not partner_ids:
        return []
    # Get scenarios from partners
    stmt = select(Scenario).where(
        Scenario.user_id.in_(partner_ids)
    )
    result = await db.execute(stmt)
    scenarios = result.scalars().all()
    return scenarios


@router.patch("/{scenario_id}/add-component")
async def add_component_to_scenario(
    scenario_id: UUID,
    component_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Add a component to a scenario."""
    stmt = select(Scenario).where(
        Scenario.id == scenario_id,
        Scenario.user_id == current_user.id
    )
    result = await db.execute(stmt)
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    # Add component if not already present
    ids = set(scenario.component_ids or [])
    ids.add(str(component_id))
    scenario.component_ids = list(ids)
    await db.commit()
    await db.refresh(scenario)
    return {"message": "Component added", "component_ids": scenario.component_ids}


@router.patch("/{scenario_id}/remove-component")
async def remove_component_from_scenario(
    scenario_id: UUID,
    component_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Remove a component from a scenario."""
    stmt = select(Scenario).where(
        Scenario.id == scenario_id,
        Scenario.user_id == current_user.id
    )
    result = await db.execute(stmt)
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    ids = set(scenario.component_ids or [])
    ids.discard(str(component_id))
    scenario.component_ids = list(ids)
    await db.commit()
    await db.refresh(scenario)
    return {"message": "Component removed", "component_ids": scenario.component_ids}


@router.post("/compare")
async def compare_scenarios(
    scenario_ids: List[UUID],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Compare two scenarios side-by-side (projections for each)."""
    if len(scenario_ids) != 2:
        raise HTTPException(status_code=400, detail="Exactly two scenario IDs required")
    projections = []
    for sid in scenario_ids:
        # Only allow access to own or shared scenarios
        stmt = select(Scenario).where(Scenario.id == sid)
        result = await db.execute(stmt)
        scenario = result.scalar_one_or_none()
        if not scenario:
            raise HTTPException(status_code=404, detail=f"Scenario {sid} not found")
        if scenario.user_id != current_user.id:
            # Check if shared by partner
            stmt2 = select(Partnership).where(
                or_(Partnership.user1_id == current_user.id, Partnership.user2_id == current_user.id),
                Partnership.is_active == True
            )
            result2 = await db.execute(stmt2)
            partnerships = result2.scalars().all()
            partner_ids = set()
            for p in partnerships:
                if p.user1_id == current_user.id:
                    partner_ids.add(p.user2_id)
                else:
                    partner_ids.add(p.user1_id)
            if scenario.user_id not in partner_ids:
                raise HTTPException(status_code=403, detail=f"No access to scenario {sid}")
        # Calculate projections
        proj = await projection_engine.calculate_scenario_projection(db, scenario, str(current_user.id))
        projections.append({"scenario_id": str(sid), "projections": [p.dict() for p in proj]})
    return {"comparisons": projections} 