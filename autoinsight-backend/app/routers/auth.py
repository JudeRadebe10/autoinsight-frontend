from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_current_user
from app.models.models import User, Role, UserRole, UserSettings
from app.schemas.schemas import UserCreate, UserLogin, UserResponse, Token, ProfileUpdate

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

async def get_or_create_role(db: AsyncSession, name: str) -> Role:
    result = await db.execute(select(Role).where(Role.name == name))
    role = result.scalar_one_or_none()
    if not role:
        role = Role(name=name, description=f"{name.capitalize()} Role")
        db.add(role)
        await db.flush()
    return role

def get_primary_role(user: User) -> str:
    roles = [ur.role.name for ur in user.user_roles if ur.role]
    if "super_admin" in roles:
        return "super_admin"
    if "admin" in roles:
        return "admin"
    return "client"

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address already registered",
        )
    
    # Hash password and create User
    hashed = hash_password(body.password)
    user = User(
        email=body.email,
        hashed_password=hashed,
        full_name=body.full_name,
        is_active=True
    )
    db.add(user)
    await db.flush()

    # Assign default role 'client'
    client_role = await get_or_create_role(db, "client")
    user_role = UserRole(user_id=user.id, role_id=client_role.id)
    db.add(user_role)

    # Assign default settings
    user_settings = UserSettings(
        user_id=user.id,
        theme="light",
        email_marketing=True,
        email_price_alerts=True,
        email_product_updates=True
    )
    db.add(user_settings)
    await db.flush()

    await db.commit()

    # Fetch fresh user with relations
    user_q = await db.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role), selectinload(User.settings))
        .where(User.id == user.id)
    )
    fresh_user = user_q.scalar_one()

    # Generate tokens
    access = create_access_token(fresh_user.id)
    refresh = create_refresh_token(fresh_user.id)
    
    return Token(
        access_token=access,
        refresh_token=refresh,
        role="client"
    )

@router.post("/login", response_model=Token)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role), selectinload(User.settings))
        .where(User.email == body.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    primary_role = get_primary_role(user)
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    return Token(
        access_token=access,
        refresh_token=refresh,
        role=primary_role
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
        
    user_id = payload.get("sub")
    result = await db.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    primary_role = get_primary_role(user)
    access = create_access_token(user.id)
    new_refresh = create_refresh_token(user.id)

    return Token(
        access_token=access,
        refresh_token=new_refresh,
        role=primary_role
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    roles = [ur.role.name for ur in current_user.user_roles if ur.role]
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        roles=roles,
        settings=current_user.settings
    )

@router.put("/me/profile", response_model=UserResponse)
async def update_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if body.full_name is not None:
        current_user.full_name = body.full_name
    await db.commit()
    await db.refresh(current_user)
    roles = [ur.role.name for ur in current_user.user_roles if ur.role]
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        roles=roles,
        settings=current_user.settings
    )
