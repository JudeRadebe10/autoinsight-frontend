from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import Base, engine, AsyncSessionLocal
from app.models.models import User, Role, UserRole, UserSettings
from app.core.security import hash_password
from app.routers import auth, settings as settings_router, admin

app = FastAPI(
    title=settings.APP_NAME,
    description="AutoInsight ZA Production-Ready Backend API (Login, Persistent Settings & RBAC)",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(settings_router.router)
app.include_router(admin.router)

async def seed_data():
    async with AsyncSessionLocal() as session:
        # Create default roles
        roles_to_seed = ["super_admin", "admin", "client"]
        seeded_roles = {}
        for r_name in roles_to_seed:
            res = await session.execute(select(Role).where(Role.name == r_name))
            role = res.scalar_one_or_none()
            if not role:
                role = Role(name=r_name, description=f"{r_name.capitalize()} Role")
                session.add(role)
                await session.flush()
            seeded_roles[r_name] = role

        # Seed default Super Admin
        res_super = await session.execute(select(User).where(User.email == settings.SEED_SUPER_ADMIN_EMAIL))
        if not res_super.scalar_one_or_none():
            super_user = User(
                email=settings.SEED_SUPER_ADMIN_EMAIL,
                hashed_password=hash_password(settings.SEED_SUPER_ADMIN_PASSWORD),
                full_name="System Super Admin",
                is_active=True
            )
            session.add(super_user)
            await session.flush()
            
            # Link role
            session.add(UserRole(user_id=super_user.id, role_id=seeded_roles["super_admin"].id))
            # Link settings
            session.add(UserSettings(user_id=super_user.id, theme="dark"))
            await session.flush()

        # Seed default Admin
        res_admin = await session.execute(select(User).where(User.email == settings.SEED_ADMIN_EMAIL))
        if not res_admin.scalar_one_or_none():
            admin_user = User(
                email=settings.SEED_ADMIN_EMAIL,
                hashed_password=hash_password(settings.SEED_ADMIN_PASSWORD),
                full_name="System Admin",
                is_active=True
            )
            session.add(admin_user)
            await session.flush()
            
            # Link role
            session.add(UserRole(user_id=admin_user.id, role_id=seeded_roles["admin"].id))
            # Link settings
            session.add(UserSettings(user_id=admin_user.id, theme="light"))
            await session.flush()

        # Seed default Client
        res_client = await session.execute(select(User).where(User.email == settings.SEED_CLIENT_EMAIL))
        if not res_client.scalar_one_or_none():
            client_user = User(
                email=settings.SEED_CLIENT_EMAIL,
                hashed_password=hash_password(settings.SEED_CLIENT_PASSWORD),
                full_name="Sample Client User",
                is_active=True
            )
            session.add(client_user)
            await session.flush()
            
            # Link role
            session.add(UserRole(user_id=client_user.id, role_id=seeded_roles["client"].id))
            # Link settings
            session.add(UserSettings(user_id=client_user.id, theme="light"))
            await session.flush()

        await session.commit()

@app.on_event("startup")
async def startup_event():
    # Create tables if not exists
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed tables with roles and default users
    await seed_data()

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "message": "Welcome to AutoInsight ZA Backend. Persisted settings & RBAC enabled."
    }
