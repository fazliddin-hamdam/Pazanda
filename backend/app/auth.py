"""Telegram Mini App initData imzosini tekshirish.

https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
Frontend har so'rovda `Authorization: tma <initData>` sarlavhasini yuboradi.
"""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

from fastapi import Depends, Header, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import User

DEV_USER_ID = 1


@dataclass
class TelegramUser:
    id: int
    first_name: str = ""
    username: str | None = None


def validate_init_data(init_data: str, bot_token: str, max_age: int | None = None) -> TelegramUser:
    pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=False))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise ValueError("hash yo'q")
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise ValueError("imzo noto'g'ri")
    if max_age:
        auth_date = int(pairs.get("auth_date", "0"))
        if time.time() - auth_date > max_age:
            raise ValueError("initData eskirgan")
    user = json.loads(pairs.get("user", "{}"))
    if "id" not in user:
        raise ValueError("user yo'q")
    return TelegramUser(id=int(user["id"]), first_name=user.get("first_name", ""), username=user.get("username"))


def current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if authorization and authorization.lower().startswith("tma ") and settings.telegram_bot_token:
        try:
            tg = validate_init_data(authorization[4:], settings.telegram_bot_token, settings.init_data_max_age)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=f"Telegram ma'lumotlari yaroqsiz: {e}") from e
    elif settings.dev_mode:
        tg = TelegramUser(id=DEV_USER_ID, first_name="Mehmon")
    else:
        raise HTTPException(status_code=401, detail="Ilovani Telegram orqali oching")

    user = db.get(User, tg.id)
    if user is None:
        # Ilova ochilganda bir nechta so'rov parallel keladi — ikkinchisi foydalanuvchini allaqachon yaratgan bo'lishi mumkin
        try:
            user = User(id=tg.id, first_name=tg.first_name, username=tg.username)
            db.add(user)
            db.commit()
        except IntegrityError:
            db.rollback()
            user = db.get(User, tg.id)
    elif user.first_name != tg.first_name and tg.first_name:
        user.first_name = tg.first_name
        db.commit()
    return user
