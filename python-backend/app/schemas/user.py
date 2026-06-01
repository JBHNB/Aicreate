"""用户相关请求/响应模型"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PageRequest


class UserRegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_account: str = Field(
        ..., min_length=4, max_length=256, alias="userAccount", description="账号"
    )
    user_password: str = Field(
        ..., min_length=8, max_length=512, alias="userPassword", description="密码"
    )
    check_password: str = Field(
        ..., min_length=8, max_length=512, alias="checkPassword", description="确认密码"
    )


class UserLoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_account: str = Field(
        ..., min_length=4, max_length=256, alias="userAccount", description="账号"
    )
    user_password: str = Field(
        ..., min_length=8, max_length=512, alias="userPassword", description="密码"
    )


class UserAddRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_account: str = Field(..., alias="userAccount", description="账号")
    user_password: str = Field(..., alias="userPassword", description="密码")
    user_name: Optional[str] = Field(None, alias="userName", description="用户昵称")
    user_avatar: Optional[str] = Field(None, alias="userAvatar", description="用户头像")
    user_profile: Optional[str] = Field(
        None, alias="userProfile", description="用户简介"
    )
    user_role: str = Field(default="user", alias="userRole", description="用户角色")


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(..., description="用户 ID")
    user_name: Optional[str] = Field(None, alias="userName", description="用户昵称")
    user_avatar: Optional[str] = Field(None, alias="userAvatar", description="用户头像")
    user_profile: Optional[str] = Field(
        None, alias="userProfile", description="用户简介"
    )
    user_role: Optional[str] = Field(None, alias="userRole", description="用户角色")


class UserQueryRequest(PageRequest):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[int] = Field(None, description="用户 ID")
    user_account: Optional[str] = Field(None, alias="userAccount", description="账号")
    user_name: Optional[str] = Field(None, alias="userName", description="用户昵称")
    user_profile: Optional[str] = Field(
        None, alias="userProfile", description="用户简介"
    )
    user_role: Optional[str] = Field(None, alias="userRole", description="用户角色")


class UserVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    user_account: str = Field(..., alias="userAccount")
    user_name: Optional[str] = Field(None, alias="userName")
    user_avatar: Optional[str] = Field(None, alias="userAvatar")
    user_profile: Optional[str] = Field(None, alias="userProfile")
    user_role: str = Field(..., alias="userRole")
    quota: Optional[int] = Field(default=None, description="剩余配额")
    vip_time: Optional[str] = Field(
        default=None, alias="vipTime", description="成为会员时间"
    )
    create_time: str = Field(..., alias="createTime")


class LoginUserVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    user_account: str = Field(..., alias="userAccount")
    user_name: Optional[str] = Field(None, alias="userName")
    user_avatar: Optional[str] = Field(None, alias="userAvatar")
    user_profile: Optional[str] = Field(None, alias="userProfile")
    user_role: str = Field(..., alias="userRole")
    quota: Optional[int] = Field(default=None, description="剩余配额")
    vip_time: Optional[str] = Field(
        default=None, alias="vipTime", description="成为会员时间"
    )
    create_time: str = Field(..., alias="createTime")
    update_time: str = Field(..., alias="updateTime")
