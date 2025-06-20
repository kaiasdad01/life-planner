from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from uuid import UUID

from ....core.database import get_db
from ....models import User, FinancialComponent, Partnership
from ....schemas import (
    FinancialComponent as FinancialComponentSchema,
    FinancialComponentCreate,
    FinancialComponentUpdate,
    FinancialComponentWithCalculation
)
from ....engines.formula_engine import formula_engine
from ...deps import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[FinancialComponentSchema])
async def get_financial_components(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get user's financial components"""
    
    stmt = select(FinancialComponent).where(
        FinancialComponent.user_id == current_user.id
    ).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    components = result.scalars().all()
    
    return components


@router.post("/", response_model=FinancialComponentSchema)
async def create_financial_component(
    component_in: FinancialComponentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a new financial component"""
    
    # Validate formula
    try:
        formula_engine.validate_formula(component_in.formula)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid formula: {str(e)}"
        )
    
    # Create component
    component = FinancialComponent(
        user_id=current_user.id,
        **component_in.dict()
    )
    
    db.add(component)
    await db.commit()
    await db.refresh(component)
    
    return component


@router.get("/{component_id}", response_model=FinancialComponentSchema)
async def get_financial_component(
    component_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get a specific financial component (owned or shared with partner)"""
    # Try to get as owner
    stmt = select(FinancialComponent).where(
        FinancialComponent.id == component_id,
        FinancialComponent.user_id == current_user.id
    )
    result = await db.execute(stmt)
    component = result.scalar_one_or_none()
    if component:
        return component
    # If not owner, check if shared by partner
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
        raise HTTPException(status_code=404, detail="Financial component not found")
    stmt = select(FinancialComponent).where(
        FinancialComponent.id == component_id,
        FinancialComponent.user_id.in_(partner_ids),
        FinancialComponent.is_shared_with_partner == True
    )
    result = await db.execute(stmt)
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(status_code=404, detail="Financial component not found")
    return component


@router.put("/{component_id}", response_model=FinancialComponentSchema)
async def update_financial_component(
    component_id: UUID,
    component_in: FinancialComponentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update a financial component"""
    
    # Get existing component
    stmt = select(FinancialComponent).where(
        FinancialComponent.id == component_id,
        FinancialComponent.user_id == current_user.id
    )
    result = await db.execute(stmt)
    component = result.scalar_one_or_none()
    
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial component not found"
        )
    
    # Validate formula if provided
    if component_in.formula:
        try:
            formula_engine.validate_formula(component_in.formula)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid formula: {str(e)}"
            )
    
    # Update component
    update_data = component_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(component, field, value)
    
    await db.commit()
    await db.refresh(component)
    
    return component


@router.delete("/{component_id}")
async def delete_financial_component(
    component_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Delete a financial component"""
    
    # Get existing component
    stmt = select(FinancialComponent).where(
        FinancialComponent.id == component_id,
        FinancialComponent.user_id == current_user.id
    )
    result = await db.execute(stmt)
    component = result.scalar_one_or_none()
    
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial component not found"
        )
    
    await db.delete(component)
    await db.commit()
    
    return {"message": "Financial component deleted"}


@router.post("/{component_id}/test", response_model=FinancialComponentWithCalculation)
async def test_financial_component(
    component_id: UUID,
    test_variables: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Test a financial component with given variables"""
    
    # Get component
    stmt = select(FinancialComponent).where(
        FinancialComponent.id == component_id,
        FinancialComponent.user_id == current_user.id
    )
    result = await db.execute(stmt)
    component = result.scalar_one_or_none()
    
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial component not found"
        )
    
    # Test formula
    try:
        calculated_value = formula_engine.evaluate_formula(
            component.formula, 
            test_variables
        )
        calculation_error = None
    except Exception as e:
        calculated_value = None
        calculation_error = str(e)
    
    # Create response
    response_data = FinancialComponentWithCalculation(
        **component.__dict__,
        calculated_value=calculated_value,
        calculation_error=calculation_error
    )
    
    return response_data


@router.post("/validate-formula")
async def validate_formula(
    formula: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Validate a formula without creating a component"""
    
    try:
        formula_engine.validate_formula(formula)
        return {"valid": True, "message": "Formula is valid"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


@router.get("/shared", response_model=List[FinancialComponentSchema])
async def get_shared_components(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get components shared with the current user by their active partner(s)."""
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
    # Get shared components from partners
    stmt = select(FinancialComponent).where(
        FinancialComponent.user_id.in_(partner_ids),
        FinancialComponent.is_shared_with_partner == True
    )
    result = await db.execute(stmt)
    components = result.scalars().all()
    return components


@router.patch("/{component_id}/sharing", response_model=FinancialComponentSchema)
async def update_sharing_setting(
    component_id: UUID,
    is_shared_with_partner: bool,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update sharing setting for a financial component."""
    stmt = select(FinancialComponent).where(
        FinancialComponent.id == component_id,
        FinancialComponent.user_id == current_user.id
    )
    result = await db.execute(stmt)
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(status_code=404, detail="Financial component not found")
    component.is_shared_with_partner = is_shared_with_partner
    await db.commit()
    await db.refresh(component)
    return component 