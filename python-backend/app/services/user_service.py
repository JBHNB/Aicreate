"""用户业务逻辑"""

from datetime import datetime
from typing import Any, Optional

from databases import Database
from sqlalchemy import and_, func, select

from app.constants.user import UserConstant
from app.exceptions import ErrorCode, throw_if, throw_if_not
from app.models.user import User
from app.schemas.user import (
    LoginUserVO,
    UserAddRequest,
    UserLoginRequest,
    UserQueryRequest,
    UserRegisterRequest,
    UserUpdateRequest,
    UserVO,
)
from app.utils.password import encrypt_password

T = User.__table__


def _dt_iso(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v)


class UserService:
    def __init__(self, db: Database):
        self.db = db

    async def register(self, request: UserRegisterRequest) -> int:
        throw_if(
            len(request.user_account) < 4,
            ErrorCode.PARAMS_ERROR,
            "账号长度不能小于 4 位",
        )
        throw_if(
            len(request.user_password) < 8,
            ErrorCode.PARAMS_ERROR,
            "密码长度不能小于 8 位",
        )
        throw_if(
            request.user_password != request.check_password,
            ErrorCode.PARAMS_ERROR,
            "两次输入的密码不一致",
        )

        count_q = select(func.count(T.c.id)).where(
            and_(T.c.userAccount == request.user_account, T.c.isDelete == 0)
        )
        count = await self.db.fetch_val(count_q)
        throw_if(count and count > 0, ErrorCode.USER_ALREADY_EXIST, "账号已存在")

        encrypted = encrypt_password(request.user_password)
        q = """
        INSERT INTO user (userAccount, userPassword, userName, userRole, quota)
        VALUES (:userAccount, :userPassword, :userName, :userRole, :quota)
        """
        await self.db.execute(
            q,
            {
                "userAccount": request.user_account,
                "userPassword": encrypted,
                "userName": f"用户{request.user_account}",
                "userRole": UserConstant.DEFAULT_ROLE,
                "quota": UserConstant.DEFAULT_QUOTA,
            },
        )
        last_id = await self.db.fetch_val("SELECT LAST_INSERT_ID() AS id")
        return int(last_id)

    async def login(self, request: UserLoginRequest) -> LoginUserVO:
        throw_if(
            len(request.user_account) < 4,
            ErrorCode.PARAMS_ERROR,
            "账号长度不能小于 4 位",
        )
        throw_if(
            len(request.user_password) < 8,
            ErrorCode.PARAMS_ERROR,
            "密码长度不能小于 8 位",
        )

        stmt = select(T).where(
            and_(T.c.userAccount == request.user_account, T.c.isDelete == 0)
        )
        row = await self.db.fetch_one(stmt)
        throw_if_not(row, ErrorCode.USER_NOT_EXIST, "用户不存在")

        u = dict(row)
        enc = encrypt_password(request.user_password)
        throw_if(
            u.get("userPassword") != enc,
            ErrorCode.PASSWORD_ERROR,
            "密码错误",
        )

        return LoginUserVO.model_validate(
            {
                "id": u["id"],
                "userAccount": u["userAccount"],
                "userName": u.get("userName"),
                "userAvatar": u.get("userAvatar"),
                "userProfile": u.get("userProfile"),
                "userRole": u["userRole"],
                "quota": u.get("quota"),
                "vipTime": _dt_iso(u.get("vipTime")) if u.get("vipTime") else None,
                "createTime": _dt_iso(u.get("createTime")),
                "updateTime": _dt_iso(u.get("updateTime")),
            }
        )

    async def get_by_id(self, user_id: int) -> UserVO:
        stmt = select(T).where(and_(T.c.id == user_id, T.c.isDelete == 0))
        row = await self.db.fetch_one(stmt)
        throw_if_not(row, ErrorCode.NOT_FOUND_ERROR, "用户不存在")
        u = dict(row)
        return UserVO.model_validate(
            {
                "id": u["id"],
                "userAccount": u["userAccount"],
                "userName": u.get("userName"),
                "userAvatar": u.get("userAvatar"),
                "userProfile": u.get("userProfile"),
                "userRole": u["userRole"],
                "quota": u.get("quota"),
                "vipTime": _dt_iso(u.get("vipTime")) if u.get("vipTime") else None,
                "createTime": _dt_iso(u.get("createTime")),
            }
        )

    async def list_by_page(
        self, request: UserQueryRequest
    ) -> tuple[list[dict], int]:
        conditions = [T.c.isDelete == 0]
        if request.id is not None:
            conditions.append(T.c.id == request.id)
        if request.user_account:
            conditions.append(T.c.userAccount.like(f"%{request.user_account}%"))
        if request.user_name:
            conditions.append(T.c.userName.like(f"%{request.user_name}%"))
        if request.user_profile:
            conditions.append(T.c.userProfile.like(f"%{request.user_profile}%"))
        if request.user_role:
            conditions.append(T.c.userRole == request.user_role)

        where_clause = and_(*conditions)

        total = await self.db.fetch_val(select(func.count()).select_from(T).where(where_clause))
        total = int(total or 0)

        order_col = T.c.updateTime
        if request.sort_field:
            col_map = {
                "userAccount": T.c.userAccount,
                "userName": T.c.userName,
                "userRole": T.c.userRole,
                "createTime": T.c.createTime,
                "updateTime": T.c.updateTime,
            }
            order_col = col_map.get(request.sort_field, T.c.updateTime)
        desc = request.sort_order != "ascend"

        offset = (request.current - 1) * request.page_size
        stmt = (
            select(T)
            .where(where_clause)
            .order_by(order_col.desc() if desc else order_col.asc())
            .offset(offset)
            .limit(request.page_size)
        )
        rows = await self.db.fetch_all(stmt)
        records: list[dict] = []
        for row in rows:
            u = dict(row)
            records.append(
                UserVO.model_validate(
                    {
                        "id": u["id"],
                        "userAccount": u["userAccount"],
                        "userName": u.get("userName"),
                        "userAvatar": u.get("userAvatar"),
                        "userProfile": u.get("userProfile"),
                        "userRole": u["userRole"],
                        "quota": u.get("quota"),
                        "vipTime": _dt_iso(u.get("vipTime")) if u.get("vipTime") else None,
                        "createTime": _dt_iso(u.get("createTime")),
                    }
                ).model_dump(by_alias=True)
            )
        return records, total

    async def add_user(self, request: UserAddRequest) -> int:
        count_q = select(func.count(T.c.id)).where(
            and_(T.c.userAccount == request.user_account, T.c.isDelete == 0)
        )
        count = await self.db.fetch_val(count_q)
        throw_if(count and count > 0, ErrorCode.USER_ALREADY_EXIST, "账号已存在")

        enc = encrypt_password(request.user_password)
        q = """
        INSERT INTO user (userAccount, userPassword, userName, userAvatar, userProfile, userRole, quota)
        VALUES (:userAccount, :userPassword, :userName, :userAvatar, :userProfile, :userRole, :quota)
        """
        await self.db.execute(
            q,
            {
                "userAccount": request.user_account,
                "userPassword": enc,
                "userName": request.user_name or f"用户{request.user_account}",
                "userAvatar": request.user_avatar,
                "userProfile": request.user_profile,
                "userRole": request.user_role or UserConstant.DEFAULT_ROLE,
                "quota": UserConstant.DEFAULT_QUOTA,
            },
        )
        last_id = await self.db.fetch_val("SELECT LAST_INSERT_ID() AS id")
        return int(last_id)

    async def update_user(self, request: UserUpdateRequest) -> bool:
        stmt = select(T.c.id).where(and_(T.c.id == request.id, T.c.isDelete == 0))
        row = await self.db.fetch_one(stmt)
        throw_if_not(row, ErrorCode.NOT_FOUND_ERROR, "用户不存在")

        fields: dict[str, Any] = {"editTime": datetime.now()}
        if request.user_name is not None:
            fields["userName"] = request.user_name
        if request.user_avatar is not None:
            fields["userAvatar"] = request.user_avatar
        if request.user_profile is not None:
            fields["userProfile"] = request.user_profile
        if request.user_role is not None:
            fields["userRole"] = request.user_role

        if len(fields) == 1 and "editTime" in fields:
            return True

        set_parts = [f"`{k}` = :{k}" for k in fields]
        params = {k: v for k, v in fields.items()}
        params["id"] = request.id
        sql = f"UPDATE user SET {', '.join(set_parts)} WHERE id = :id AND isDelete = 0"
        await self.db.execute(sql, params)
        return True

    async def delete_user(self, user_id: int) -> bool:
        stmt = select(T.c.id).where(and_(T.c.id == user_id, T.c.isDelete == 0))
        row = await self.db.fetch_one(stmt)
        throw_if_not(row, ErrorCode.NOT_FOUND_ERROR, "用户不存在")
        await self.db.execute(
            "UPDATE user SET isDelete = 1 WHERE id = :id",
            {"id": user_id},
        )
        return True
