"""Pydantic schemas for org / auth APIs."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login body."""

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    """Refresh token body."""

    refresh_token: str = Field(min_length=1)


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
    company_id: int | None = None  # active company context


class TokenResponse(BaseModel):
    """Login / refresh token payload."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserMe


class PageMeta(BaseModel):
    """Pagination meta."""

    page: int
    page_size: int
    total: int


class CompanyCreate(BaseModel):
    """Create company payload."""

    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    base_currency_code: str = Field(default="CNY", min_length=3, max_length=3)
    status: str = Field(default="active", max_length=16)


class CompanyUpdate(BaseModel):
    """Patch company payload."""

    name: str | None = Field(default=None, max_length=128)
    base_currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    status: str | None = Field(default=None, max_length=16)


class CompanyOut(BaseModel):
    """Company response row."""

    id: int
    code: str
    name: str
    base_currency_code: str
    status: str


class UserCreate(BaseModel):
    """Create user payload."""

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=64)
    email: str | None = Field(default=None, max_length=128)
    status: str = Field(default="active", max_length=16)
    role_ids: list[int] = Field(default_factory=list)
    company_ids: list[int] = Field(default_factory=list)
    default_company_id: int | None = None


class UserUpdate(BaseModel):
    """Patch user payload."""

    display_name: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=128)
    status: str | None = Field(default=None, max_length=16)
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserOut(BaseModel):
    """User list/detail row."""

    id: int
    username: str
    display_name: str
    email: str | None
    status: str
    roles: list[str]


class UserRolesUpdate(BaseModel):
    """Replace user role bindings."""

    role_ids: list[int]


class RoleCreate(BaseModel):
    """Create role payload."""

    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=255)


class RoleOut(BaseModel):
    """Role response row."""

    id: int
    code: str
    name: str
    description: str | None
    permission_codes: list[str] = Field(default_factory=list)


class RolePermissionsUpdate(BaseModel):
    """Replace role permission bindings."""

    permission_ids: list[int]


class PermissionOut(BaseModel):
    """Permission response row."""

    id: int
    code: str
    name: str
    module: str
