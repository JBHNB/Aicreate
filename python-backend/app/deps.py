"""依赖注入"""

import uuid
from typing import Optional

from databases import Database
from fastapi import Cookie, Depends

from app.database import get_db
from app.exceptions import BusinessException, ErrorCode
from app.schemas.user import LoginUserVO
from app.services.user_service import UserService
from app.utils.session import get_session, set_session


async def get_session_id(
    session_id: Optional[str] = Cookie(None, alias="SESSION"),
) -> Optional[str]:
    return session_id


async def get_current_user(
    session_id: Optional[str] = Depends(get_session_id),
    db: Database = Depends(get_db),
) -> Optional[LoginUserVO]:
    if not session_id:
        return None
    session_data = await get_session(session_id)
    if not session_data or "user" not in session_data:
        return None

    user_id = session_data["user"].get("id")
    if not user_id:
        return LoginUserVO.model_validate(session_data["user"])

    try:
        service = UserService(db)
        fresh_user = await service.get_login_user_by_id(int(user_id))
        await set_session(session_id, {"user": fresh_user.model_dump(by_alias=True)})
        return fresh_user
    except BusinessException:
        return None


async def require_login(
    current_user: Optional[LoginUserVO] = Depends(get_current_user),
) -> LoginUserVO:
    if not current_user:
        raise BusinessException(ErrorCode.NOT_LOGIN_ERROR)
    return current_user


async def require_admin(
    current_user: LoginUserVO = Depends(require_login),
) -> LoginUserVO:
    if current_user.user_role != "admin":
        raise BusinessException(ErrorCode.NO_AUTH_ERROR)
    return current_user


def generate_session_id() -> str:
    return str(uuid.uuid4())
