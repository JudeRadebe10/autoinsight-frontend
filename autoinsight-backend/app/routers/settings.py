from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User, UserSettings
from app.schemas.schemas import SettingsUpdate, SettingsResponse

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("/me", response_model=SettingsResponse)
async def get_my_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch settings or create if not present
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    user_settings = result.scalar_one_or_none()
    
    if not user_settings:
        user_settings = UserSettings(
            user_id=current_user.id,
            theme="light",
            email_marketing=True,
            email_price_alerts=True,
            email_product_updates=True
        )
        db.add(user_settings)
        await db.commit()
        await db.refresh(user_settings)
        
    return user_settings

@router.put("/me", response_model=SettingsResponse)
async def update_my_settings(
    body: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    user_settings = result.scalar_one_or_none()
    
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        db.add(user_settings)
        await db.flush()
        
    # Update fields provided in request body
    if body.theme is not None:
        if body.theme not in ["light", "dark"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Theme must be either 'light' or 'dark'",
            )
        user_settings.theme = body.theme
    if body.email_marketing is not None:
        user_settings.email_marketing = body.email_marketing
    if body.email_price_alerts is not None:
        user_settings.email_price_alerts = body.email_price_alerts
    if body.email_product_updates is not None:
        user_settings.email_product_updates = body.email_product_updates
        
    await db.commit()
    await db.refresh(user_settings)
    return user_settings
