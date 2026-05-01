from pydantic import BaseModel, EmailStr, field_validator


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str


class UserResponse(BaseModel):
    email: str
    full_name: str
    created_at: str


class MessageResponse(BaseModel):
    message: str


class SaveItineraryRequest(BaseModel):
    itinerary_id: str
    data: dict


class ItinerarySummary(BaseModel):
    itinerary_id: str
    destination: str
    start_date: str
    end_date: str
    num_days: int
    saved_at: str
