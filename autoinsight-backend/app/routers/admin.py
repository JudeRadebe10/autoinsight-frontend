from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.orm import selectinload
from typing import List
import uuid

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.models import User, Role, UserRole
from app.schemas.schemas import UserResponse, RoleAssignment, StatusUpdate

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("super_admin", "admin"))
):
    result = await db.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role), selectinload(User.settings))
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    
    response = []
    for user in users:
        roles = [ur.role.name for ur in user.user_roles if ur.role]
        response.append(
            UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                avatar_url=user.avatar_url,
                is_active=user.is_active,
                roles=roles,
                settings=user.settings
            )
        )
    return response

@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def assign_role(
    user_id: uuid.UUID,
    body: RoleAssignment,
    db: AsyncSession = Depends(get_db),
    _super: User = Depends(require_roles("super_admin"))
):
    if body.role not in ["super_admin", "admin", "client"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Role must be either 'super_admin', 'admin', or 'client'",
        )

    # Check if target user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Invalidate previous roles
    await db.execute(delete(UserRole).where(UserRole.user_id == user_id))

    # Get or create role
    role_result = await db.execute(select(Role).where(Role.name == body.role))
    role = role_result.scalar_one_or_none()
    if not role:
        role = Role(name=body.role, description=f"{body.role.capitalize()} Role")
        db.add(role)
        await db.flush()

    user_role = UserRole(user_id=user.id, role_id=role.id)
    db.add(user_role)
    await db.commit()

    # Get fresh user
    user_q = await db.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role), selectinload(User.settings))
        .where(User.id == user.id)
    )
    fresh_user = user_q.scalar_one()
    roles = [ur.role.name for ur in fresh_user.user_roles if ur.role]

    return UserResponse(
        id=fresh_user.id,
        email=fresh_user.email,
        full_name=fresh_user.full_name,
        avatar_url=fresh_user.avatar_url,
        is_active=fresh_user.is_active,
        roles=roles,
        settings=fresh_user.settings
    )

@router.patch("/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: uuid.UUID,
    body: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("super_admin", "admin"))
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_active = body.is_active
    await db.commit()

    # Get fresh user
    user_q = await db.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role), selectinload(User.settings))
        .where(User.id == user.id)
    )
    fresh_user = user_q.scalar_one()
    roles = [ur.role.name for ur in fresh_user.user_roles if ur.role]

    return UserResponse(
        id=fresh_user.id,
        email=fresh_user.email,
        full_name=fresh_user.full_name,
        avatar_url=fresh_user.avatar_url,
        is_active=fresh_user.is_active,
        roles=roles,
        settings=fresh_user.settings
    )
