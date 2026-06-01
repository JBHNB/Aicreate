"""用户路由"""

from typing import Optional

from databases import Database
from fastapi import APIRouter, Depends, Response

from app.config import settings
from app.database import get_db
from app.deps import (
    generate_session_id,
    get_current_user,
    get_session_id,
    require_admin,
    require_login,
)
from app.schemas.common import BaseResponse, DeleteRequest
from app.schemas.user import (
    LoginUserVO,
    UserAddRequest,
    UserLoginRequest,
    UserQueryRequest,
    UserRegisterRequest,
    UserUpdateRequest,
    UserVO,
)
from app.services.user_service import UserService
from app.utils.session import remove_session, set_session

router = APIRouter(prefix="/user", tags=["用户管理"])


@router.post(
    "/register",
    response_model=BaseResponse[int],
    response_model_by_alias=True,
)
async def register(request: UserRegisterRequest, db: Database = Depends(get_db)):
    service = UserService(db)
    user_id = await service.register(request)
    return BaseResponse.success(data=user_id, message="注册成功")


@router.post(
    "/login",
    response_model=BaseResponse[LoginUserVO],
    response_model_by_alias=True,
)
async def login(
    request: UserLoginRequest,
    response: Response,
    db: Database = Depends(get_db),
):
    service = UserService(db)
    user = await service.login(request)
    session_id = generate_session_id()
    await set_session(session_id, {"user": user.model_dump(by_alias=True)})
    response.set_cookie(
        key="SESSION",
        value=session_id,
        max_age=settings.session_max_age,
        httponly=True,
        samesite="lax",
    )
    return BaseResponse.success(data=user, message="登录成功")


@router.post(
    "/logout",
    response_model=BaseResponse[bool],
    response_model_by_alias=True,
)
async def logout(
    response: Response,
    session_id: Optional[str] = Depends(get_session_id),
):
    if session_id:
        await remove_session(session_id)
    response.delete_cookie(key="SESSION", path="/", samesite="lax")
    return BaseResponse.success(data=True, message="登出成功")


@router.get(
    "/get/login",
    response_model=BaseResponse[LoginUserVO],
    response_model_by_alias=True,
)
async def get_login_user(current_user: LoginUserVO = Depends(require_login)):
    return BaseResponse.success(data=current_user)


@router.get(
    "/get",
    response_model=BaseResponse[UserVO],
    response_model_by_alias=True,
)
async def get_user_by_id(id: int, db: Database = Depends(get_db)):
    service = UserService(db)
    user = await service.get_by_id(id)
    return BaseResponse.success(data=user)


@router.post(
    "/list/page",
    response_model=BaseResponse[dict],
    response_model_by_alias=True,
)
async def list_users_by_page(
    request: UserQueryRequest,
    db: Database = Depends(get_db),
    _: LoginUserVO = Depends(require_admin),
):
    service = UserService(db)
    users, total = await service.list_by_page(request)
    return BaseResponse.success(
        data={
            "records": users,
            "total": total,
            "current": request.current,
            "size": request.page_size,
        }
    )


@router.post(
    "/add",
    response_model=BaseResponse[int],
    response_model_by_alias=True,
)
async def add_user(
    request: UserAddRequest,
    db: Database = Depends(get_db),
    _: LoginUserVO = Depends(require_admin),
):
    service = UserService(db)
    user_id = await service.add_user(request)
    return BaseResponse.success(data=user_id, message="添加成功")


@router.post(
    "/update",
    response_model=BaseResponse[bool],
    response_model_by_alias=True,
)
async def update_user(
    request: UserUpdateRequest,
    db: Database = Depends(get_db),
    _: LoginUserVO = Depends(require_admin),
):
    service = UserService(db)
    result = await service.update_user(request)
    return BaseResponse.success(data=result, message="更新成功")


@router.post(
    "/delete",
    response_model=BaseResponse[bool],
    response_model_by_alias=True,
)
async def delete_user(
    request: DeleteRequest,
    db: Database = Depends(get_db),
    _: LoginUserVO = Depends(require_admin),
):
    service = UserService(db)
    result = await service.delete_user(request.id)
    return BaseResponse.success(data=result, message="删除成功")
