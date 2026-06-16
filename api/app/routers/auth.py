from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash password and create user
    hashed_password = hash_password(request.password)
    new_user = User(
        email=request.email,
        hashed_password=hashed_password,
        full_name=request.full_name,
        organisation=request.organisation,
        role=request.role,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Create access token
    access_token = create_access_token(data={"sub": new_user.id})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=new_user.id,
        email=new_user.email,
        role=new_user.role,
    )

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Find user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    # Verify credentials
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.id})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
    )

@router.get("/me", response_model=UserResponse)
async def get_me(
    credentials: HTTPAuthCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(token=credentials.credentials, db=db)
    return UserResponse.model_validate(user)

@router.put("/me", response_model=UserResponse)
async def update_me(
    full_name: str,
    organisation: str,
    credentials: HTTPAuthCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(token=credentials.credentials, db=db)
    user.full_name = full_name
    user.organisation = organisation
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)
