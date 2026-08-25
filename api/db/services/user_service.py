#!/usr/bin/env python
# encoding: utf-8
"""
@author: Datawhale
@file: user_service.py
@time: 2025/7/22 17:00
@project: resonant-soul
@desc: 用户服务
"""
import hashlib
import hmac
import os
from datetime import datetime

from api.db.db_models import User


class UserService:
    PASSWORD_ITERATIONS = 600_000

    @classmethod
    def _hash_password(cls, password):
        salt = os.urandom(16)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt, cls.PASSWORD_ITERATIONS
        )
        return (
            f"pbkdf2_sha256${cls.PASSWORD_ITERATIONS}$"
            f"{salt.hex()}${password_hash.hex()}"
        )

    @staticmethod
    def get_by_username(username):
        try:
            return User.get(User.username == username)
        except User.DoesNotExist:
            return None

    @staticmethod
    def verify_password(user, password):
        stored = user.password
        if stored.startswith("pbkdf2_sha256$"):
            try:
                _, iterations, salt, expected = stored.split("$", 3)
                actual = hashlib.pbkdf2_hmac(
                    "sha256", password.encode(), bytes.fromhex(salt), int(iterations)
                ).hex()
                return hmac.compare_digest(actual, expected)
            except (TypeError, ValueError):
                return False

        # Support and transparently upgrade databases created by the upstream app.
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()
        if hmac.compare_digest(stored, legacy_hash):
            user.password = UserService._hash_password(password)
            user.updated_at = datetime.now()
            user.save()
            return True
        return False

    @staticmethod
    def check_user_status(user):
        """检查用户状态"""
        message = "正常"
        status_ok = True
        if not user.status:
            message = "账号已被禁用，请联系管理员"
            status_ok = False
        return status_ok, message

    @staticmethod
    def register(username, name_nick, password, is_admin=False):
        username = (username or "").strip()
        name_nick = (name_nick or "").strip()
        if len(username) < 3 or len(password or "") < 8 or not name_nick:
            return None
        if UserService.get_by_username(username):
            return None

        # 密码哈希处理
        password_hash = UserService._hash_password(password)
        current_time = datetime.now()

        # 保存用户数据
        user = User.create(
            username=username,
            password=password_hash,
            name_nick=name_nick,
            is_admin=is_admin,
            status=True,
            created_at=current_time,
            updated_at=current_time
        )
        return user

    @staticmethod
    def register_admin(username, name_nick, password):
        return UserService.register(username, name_nick, password, is_admin=True)

    @staticmethod
    def get_all_users():
        return User.select()

    @staticmethod
    def update_status(user_id, status):
        try:
            user = User.get_by_id(user_id)
            # 防止禁用管理员账号
            if user.is_admin and not status:
                return False
            user.status = status
            user.updated_at = datetime.now()
            user.save()
            return True
        except User.DoesNotExist:
            return False

    @staticmethod
    def delete_user(user_id):
        try:
            user = User.get_by_id(user_id)
            # 防止删除管理员账号
            if user.is_admin:
                return False
            user.delete_instance()
            return True
        except User.DoesNotExist:
            return False

    @classmethod
    def update_password(cls, user_id, new_password):
        if len(new_password or "") < 8:
            raise ValueError("密码长度至少为 8 位")
        user = User.get_by_id(user_id)
        password_hash = cls._hash_password(new_password)
        user.password = password_hash
        user.updated_at = datetime.now()
        user.save()
        return True

    @classmethod
    def get_by_id(cls, user_id):
        try:
            return User.get_by_id(user_id)
        except User.DoesNotExist:
            return None
