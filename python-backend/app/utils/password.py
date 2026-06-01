"""密码加密工具"""

import hashlib

from app.config import settings


def encrypt_password(password: str) -> str:
    """MD5(password + salt)，与 Java 版一致"""
    salted_password = password + settings.password_salt
    return hashlib.md5(salted_password.encode()).hexdigest()


def verify_password(plain_password: str, encrypted_password: str) -> bool:
    return encrypt_password(plain_password) == encrypted_password
