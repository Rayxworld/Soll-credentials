from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.api.v1.dependencies import (
    AuthContext,
    get_current_auth,
    require_csrf,
)
from app.core.config import settings
from app.db.dependencies import get_db
from app.schemas.auth import (
    AuthenticatedResponse,
    AuthenticatedUserResponse,
    MessageResponse,
    OTPRequest,
    OTPVerificationRequest,
)
from app.services.auth_session import (
    create_auth_session,
    revoke_auth_session,
)
from app.services.email_delivery import send_otp_email
from app.services.email_otp import (
    request_email_otp,
    verify_email_otp,
)
from app.services.ip_rate_limit import enforce_ip_rate_limit


router = APIRouter(prefix="/auth", tags=["Authentication"])


def set_auth_cookies(
    response: Response,
    session_token: str,
    csrf_token: str,
) -> None:
    max_age = settings.session_ttl_days * 24 * 60 * 60

    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )

    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )

    response.delete_cookie(
        key=settings.csrf_cookie_name,
        path="/",
        secure=settings.cookie_secure,
        httponly=False,
        samesite=settings.cookie_samesite,
    )


@router.post(
    "/request-code",
    response_model=MessageResponse,
)
def request_code(
    request: Request,
    payload: OTPRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    enforce_ip_rate_limit(request, db, "otp_request")

    try:
        dispatch = request_email_otp(db, str(payload.email))
        send_otp_email(dispatch.email, dispatch.code)
        db.commit()

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email delivery is temporarily unavailable.",
        ) from exc

    except Exception:
        db.rollback()
        raise

    return MessageResponse(
        message=(
            "If the address can receive email, "
            "a sign-in code has been sent."
        )
    )


@router.post(
    "/verify-code",
    response_model=AuthenticatedResponse,
)
def verify_code(
    request: Request,
    payload: OTPVerificationRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthenticatedResponse:
    enforce_ip_rate_limit(request, db, "otp_verify")

    try:
        result = verify_email_otp(
            db,
            str(payload.email),
            payload.code,
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid verification request.",
        ) from exc

    if not result.success or result.user is None:
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification code.",
        )

    created = create_auth_session(db, result.user)
    db.commit()

    set_auth_cookies(
        response,
        created.session_token,
        created.csrf_token,
    )

    return AuthenticatedResponse(
        user=AuthenticatedUserResponse(
            id=result.user.id,
            email=result.user.email,
        ),
        csrf_token=created.csrf_token,
    )


@router.get(
    "/me",
    response_model=AuthenticatedUserResponse,
)
def current_user(
    auth: AuthContext = Depends(get_current_auth),
) -> AuthenticatedUserResponse:
    return AuthenticatedUserResponse(
        id=auth.user.id,
        email=auth.user.email,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
)
def logout(
    response: Response,
    auth: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> MessageResponse:
    revoke_auth_session(db, auth.session)
    db.commit()
    clear_auth_cookies(response)

    return MessageResponse(message="Signed out successfully.")
