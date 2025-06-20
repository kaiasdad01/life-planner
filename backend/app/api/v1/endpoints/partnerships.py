from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from uuid import UUID

from ....core.database import get_db
from ....models import User, Partnership
from ...deps import get_current_active_user

router = APIRouter()

@router.post("/invite")
async def invite_partner(
    partner_email: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Invite a partner by email."""
    # Find the partner user
    stmt = select(User).where(User.email == partner_email)
    result = await db.execute(stmt)
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    if partner.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot partner with yourself")
    # Check if partnership already exists
    stmt = select(Partnership).where(
        or_(
            and_(Partnership.user1_id == current_user.id, Partnership.user2_id == partner.id),
            and_(Partnership.user1_id == partner.id, Partnership.user2_id == current_user.id)
        )
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Partnership already exists or pending")
    # Create partnership (pending, is_active=False)
    partnership = Partnership(
        user1_id=current_user.id,
        user2_id=partner.id,
        is_active=False
    )
    db.add(partnership)
    await db.commit()
    await db.refresh(partnership)
    return {"message": "Invitation sent", "partnership_id": str(partnership.id)}

@router.post("/accept/{partnership_id}")
async def accept_partnership(
    partnership_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Accept a partnership invitation."""
    stmt = select(Partnership).where(Partnership.id == partnership_id)
    result = await db.execute(stmt)
    partnership = result.scalar_one_or_none()
    if not partnership:
        raise HTTPException(status_code=404, detail="Partnership not found")
    if partnership.user2_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to accept this invitation")
    if partnership.is_active:
        raise HTTPException(status_code=400, detail="Partnership already active")
    partnership.is_active = True
    await db.commit()
    return {"message": "Partnership accepted"}

@router.post("/revoke/{partnership_id}")
async def revoke_partnership(
    partnership_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Revoke (delete) a partnership (either user can revoke)."""
    stmt = select(Partnership).where(Partnership.id == partnership_id)
    result = await db.execute(stmt)
    partnership = result.scalar_one_or_none()
    if not partnership:
        raise HTTPException(status_code=404, detail="Partnership not found")
    if current_user.id not in [partnership.user1_id, partnership.user2_id]:
        raise HTTPException(status_code=403, detail="Not authorized to revoke this partnership")
    await db.delete(partnership)
    await db.commit()
    return {"message": "Partnership revoked"}

@router.get("/list", response_model=List[dict])
async def list_partnerships(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """List all partnerships for the current user."""
    stmt = select(Partnership).where(
        or_(Partnership.user1_id == current_user.id, Partnership.user2_id == current_user.id)
    )
    result = await db.execute(stmt)
    partnerships = result.scalars().all()
    # Return basic info for each partnership
    return [
        {
            "id": str(p.id),
            "user1_id": str(p.user1_id),
            "user2_id": str(p.user2_id),
            "is_active": p.is_active,
            "created_at": p.created_at
        }
        for p in partnerships
    ] 