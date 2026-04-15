"""
F.A.R.O. Auth API - Authentication endpoints
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.api.v1.deps import get_db
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
    verify_token_type,
)
from app.db.base import Agency, Device, Unit, User, UserRole
from app.schemas.user import (
    UserLogin,
    UserCreate,
    UserResponse,
    Token,
    TokenRefresh,
    PasswordChange,
)

router = APIRouter()
security = HTTPBearer(auto_error=False)


# =============================================================================
# TODO[FUTURO - OUTRO DEV]: AUTENTICAÇÃO EM BASES OFICIAIS EXTERNAS
# =============================================================================
# Esta seção prepara a integração com sistemas de autenticação externos.
# POR ENQUANTO: Autenticação local via CPF/email + senha no banco FARO.
# 
# ROADMAP DE INTEGRAÇÃO:
# -----------------------------------------------------------------------------
# 
# 1. GOV.BR (SSO Federal) - PRIORIDADE ALTA
#    - Implementar OAuth2/OIDC com gov.br
#    - Validar CPF via token gov.br
#    - Criar adapter: app/integrations/govbr_auth_adapter.py
#    - Endpoint: https://sso.acesso.gov.br/
#    - Necessário: Cadastro do FARO como aplicação no gov.br
# 
# 2. SISTEMA INTERNO PMMS (RH/Pessoal) - PRIORIDADE ALTA  
#    - Integrar com sistema de pessoal da PMMS
#    - Validar matrícula, CPF, unidade lotação, status ativo
#    - Criar adapter: app/integrations/pmms_hr_adapter.py
#    - Dados necessários: Endpoint interno, credenciais, certificado
#    - Verificar: Se policial está ativo, afastado, férias, etc.
# 
# 3. SIGMIL (Sistema de Identidade Militar) - PRIORIDADE MÉDIA
#    - Integrar com SIGMIL se disponível
#    - Validar credencial militar
#    - Criar adapter: app/integrations/sigmil_adapter.py
# 
# 4. CONSULTA BÁSICA RECEITA FEDERAL - PRIORIDADE BAIXA
#    - Validar existência do CPF na Receita
#    - Usar CPF para confirmar dados básicos
#    - Criar adapter: app/integrations/receita_adapter.py
# 
# IMPLEMENTAÇÃO:
# -----------------------------------------------------------------------------
# Para ativar, descomentar a função abaixo e implementar os adapters.
# A lógica de login em /auth/login já está preparada para chamar esta função
# quando um CPF é detectado (linha ~186: user_info = await verify_with_intelligence_db(...))
#
# FLUXO FUTURO:
#   1. Usuário digita CPF na tela de login
#   2. Sistema detecta CPF (11 dígitos)
#   3. Chama verify_with_intelligence_db(cpf, badge_number)
#   4. Se sucesso: autentica no FARO com dados da base oficial
#   5. Se falha: recusa acesso ou redireciona para registro manual
# =============================================================================

# async def verify_with_intelligence_db(cpf: str, badge_number: str) -> Optional[dict]:
#     """
#     Verify user credentials against external intelligence database.
#     
#     IMPLEMENTATION CHECKLIST FOR NEXT DEVELOPER:
#     
#     [ ] Criar arquivo app/integrations/govbr_auth_adapter.py
#     [ ] Criar arquivo app/integrations/pmms_hr_adapter.py  
#     [ ] Configurar variáveis de ambiente no .env:
#         - GOVBR_CLIENT_ID, GOVBR_CLIENT_SECRET
#         - PMMS_HR_ENDPOINT, PMMS_HR_API_KEY
#     [ ] Implementar retry logic e circuit breaker
#     [ ] Adicionar testes de integração (mock)
#     [ ] Documentar no onboarding.md
#     
#     Args:
#         cpf: Brazilian CPF (11 digits, cleaned)
#         badge_number: Police badge number (optional)
#
#     Returns:
#         Dict with user info if valid:
#         {
#             "cpf": str,
#             "full_name": str,
#             "badge_number": str,
#             "unit_code": str,
#             "unit_name": str,
#             "is_active": bool,
#             "role": str,  # "field_agent", "intelligence", "supervisor"
#             "source": str,  # "govbr", "pmms_hr", "sigmil"
#         }
#         None if invalid or not found
#     """
#     # IMPLEMENTATION EXAMPLE:
#     # 
#     # # Try PMMS HR system first (internal)
#     # from app.integrations.pmms_hr_adapter import verify_with_pmms_hr
#     # result = await verify_with_pmms_hr(cpf=cpf, badge_number=badge_number)
#     # if result:
#     #     return result
#     #
#     # # Fallback to gov.br
#     # from app.integrations.govbr_auth_adapter import verify_with_govbr
#     # result = await verify_with_govbr(cpf=cpf)
#     # if result:
#     #     return result
#     #
#     # return None
#     pass


async def build_user_response(db: AsyncSession, user: User) -> UserResponse:
    unit_name: Optional[str] = None
    agency_name: Optional[str] = None

    # NOTE: explicit queries avoid lazy-loading surprises on async sessions.
    if user.unit_id:
        unit = (
            await db.execute(select(Unit).where(Unit.id == user.unit_id))
        ).scalar_one_or_none()
        unit_name = unit.name if unit is not None else None
    if user.agency_id:
        agency = (
            await db.execute(select(Agency).where(Agency.id == user.agency_id))
        ).scalar_one_or_none()
        agency_name = agency.name if agency is not None else None

    return UserResponse.model_validate(user).model_copy(
        update={
            "unit_name": unit_name,
            "agency_name": agency_name,
        }
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


def require_role(*roles: UserRole):
    """Dependency factory for role-based access control."""

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user using email or CPF, with optional intelligence DB verification."""

    # Determine if identifier is CPF (11 digits) or email
    identifier = login_data.identifier.replace(".", "").replace("-", "")
    is_cpf = len(identifier) == 11 and identifier.isdigit()

    # Build query based on identifier type
    if is_cpf:
        # Authenticate by CPF
        # TODO: Uncomment the following line when ready to use intelligence DB verification
        # user_info = await verify_with_intelligence_db(identifier, login_data.badge_number)
        result = await db.execute(select(User).where(User.cpf == identifier))
    else:
        # Authenticate by email
        result = await db.execute(
            select(User).where(User.email == login_data.identifier)
        )

    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    # Update last login
    user.last_login = datetime.utcnow()

    # Register/update device if provided
    if login_data.device_id:
        device_result = await db.execute(
            select(Device).where(
                Device.user_id == user.id,
                Device.device_id == login_data.device_id,
            )
        )
        device = device_result.scalar_one_or_none()

        if device:
            if device.agency_id != user.agency_id:
                device.agency_id = user.agency_id
            device.last_seen = datetime.utcnow()
            device.app_version = login_data.app_version or device.app_version
        else:
            device = Device(
                user_id=user.id,
                agency_id=user.agency_id,
                device_id=login_data.device_id,
                device_model=login_data.device_model or "Unknown",
                os_version=login_data.os_version or "Unknown",
                app_version=login_data.app_version or "Unknown",
                last_seen=datetime.utcnow(),
            )
            db.add(device)

    await db.commit()

    # Create tokens
    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        agency_id=str(user.agency_id),
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=await build_user_response(db, user),
    )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    # Update last login
    user.last_login = datetime.utcnow()

    # Register/update device if provided
    if login_data.device_id:
        device_result = await db.execute(
            select(Device).where(
                Device.user_id == user.id,
                Device.device_id == login_data.device_id,
            )
        )
        device = device_result.scalar_one_or_none()

        if device:
            if device.agency_id != user.agency_id:
                device.agency_id = user.agency_id
            device.last_seen = datetime.utcnow()
            device.app_version = login_data.app_version or device.app_version
        else:
            device = Device(
                user_id=user.id,
                agency_id=user.agency_id,
                device_id=login_data.device_id,
                device_model=login_data.device_model or "Unknown",
                os_version=login_data.os_version or "Unknown",
                app_version=login_data.app_version or "Unknown",
                last_seen=datetime.utcnow(),
            )
            db.add(device)

    await db.commit()

    # Create tokens
    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        agency_id=str(user.agency_id),
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=await build_user_response(db, user),
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    payload = decode_token(refresh_data.refresh_token)

    if not payload or not verify_token_type(payload, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new tokens
    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        agency_id=str(user.agency_id),
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=await build_user_response(db, user),
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
):
    """Logout user (client-side token removal)."""
    # In a more complex setup, we could blacklist tokens here
    return {"message": "Successfully logged out"}


@router.post("/password/change")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change user password."""
    if not verify_password(
        password_data.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.password_changed_at = datetime.utcnow()
    await db.commit()

    return {"message": "Password changed successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user information."""
    return await build_user_response(db, current_user)
