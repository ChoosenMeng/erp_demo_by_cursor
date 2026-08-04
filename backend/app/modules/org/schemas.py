"""Pydantic schemas for org / auth APIs."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login body."""

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class CompanyBrief(BaseModel):
    """Company summary attached to the current user."""

    id: int
    code: str
    name: str
    is_default: bool


class UserMe(BaseModel):
    """Current user profile returned by login / me."""

    id: int
    username: str
    display_name: str
    roles: list[str]
    permissions: list[str]
    companies: list[CompanyBrief]
    company_id: int | None = None  # default / active company context


class TokenResponse(BaseModel):
    """Login token payload."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserMe
