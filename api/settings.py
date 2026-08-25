#!/usr/bin/env python
# encoding: utf-8
"""
@author: Datawhale
@file: settings.py
@time: 2025/7/21 14:58
@project: resonant-soul
@desc: 
"""

import logging
import os

from dotenv import load_dotenv

from api.db.db_models import DBManager
from api.utils import get_base_config

EMOTION_RECORDS = []
databaseConn = None
CHAT_MDL = None
ADMIN_USER = None


def init_settings():
    global EMOTION_RECORDS, databaseConn, CHAT_MDL, ADMIN_USER
    # 存储情绪记录和日记
    # 加载环境变量
    load_dotenv(dotenv_path='.env')

    databaseConn = DBManager(os.getenv("DB_PATH", "mindmate.db"))

    LLM = get_base_config("llm")
    api_key = os.getenv("LLM_API_KEY", "").strip()

    if api_key:
        # Delay the heavyweight CAMEL imports so the app can run in demo mode.
        from camel.models import ModelFactory
        from camel.types import ModelPlatformType

        CHAT_MDL = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type=os.getenv("LLM_MODEL_TYPE", LLM['model_type']),
            url=os.getenv("LLM_MODEL_URL", LLM['model_url']),
            api_key=api_key
        )
        logging.info("LLM client initialized")
    else:
        CHAT_MDL = None
        logging.warning("LLM_API_KEY is not configured; offline demo mode is enabled")

    admin_config = get_base_config("admin").copy()
    admin_config.update({
        "username": os.getenv("ADMIN_USERNAME", admin_config.get("username", "admin")),
        "password": os.getenv("ADMIN_PASSWORD", ""),
        "name_nick": os.getenv("ADMIN_NAME", admin_config.get("name_nick", "系统管理员")),
    })
    ADMIN_USER = admin_config
