from pydantic import BaseModel, EmailStr
from uuid import UUID


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerificationRequest(BaseModel):
    email: EmailStr
    code: str


class MessageResponse(BaseModel):
    message: str


class AuthenticatedUserResponse(BaseModel):
    id: UUID
    email: EmailStr


class AuthenticatedResponse(BaseModel):
    user: AuthenticatedUserResponse
    csrf_token: str
