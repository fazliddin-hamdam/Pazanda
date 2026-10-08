"""Telegram bot: /start buyrug'iga Mini App tugmasi bilan javob beradi va menyu tugmasini o'rnatadi.

Ishga tushirish:  python bot.py   (TELEGRAM_BOT_TOKEN va WEBAPP_URL .env da bo'lishi kerak)
"""

import logging
import time

import httpx

from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
# httpx har bir so'rov URL'ini yozadi, URL esa bot tokenini o'z ichiga oladi — logga tushmasin
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("bot")

API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"

WELCOME = (
    "Assalomu alaykum! Men — Pazanda, oshxonadagi yordamchingiz 🍲\n\n"
    "Bozordan nima olib kelganingizni yozasiz, men omborni yuritaman. "
    "\"Bugun nima pishirsam?\" desangiz — bor masalliqqa qarab o'zbekcha taom tavsiya qilaman, "
    "yetishmaganini aytaman va qadamma-qadam retseptini beraman.\n\n"
    "Boshlash uchun pastdagi tugmani bosing 👇"
)


def call(client: httpx.Client, method: str, **params):
    r = client.post(f"{API}/{method}", json=params, timeout=40)
    data = r.json()
    if not data.get("ok"):
        log.error("%s xato: %s", method, data)
    return data.get("result")


def main():
    if not settings.telegram_bot_token or not settings.webapp_url:
        raise SystemExit("TELEGRAM_BOT_TOKEN va WEBAPP_URL (https://...) .env faylida ko'rsatilishi kerak")
    with httpx.Client() as client:
        call(client, "setChatMenuButton", menu_button={
            "type": "web_app", "text": "Oshxona", "web_app": {"url": settings.webapp_url},
        })
        call(client, "setMyCommands", commands=[{"command": "start", "description": "Pazandani ochish"}])
        log.info("Bot ishga tushdi, WebApp: %s", settings.webapp_url)
        offset = 0
        while True:
            try:
                updates = call(client, "getUpdates", offset=offset, timeout=30, allowed_updates=["message"]) or []
            except httpx.HTTPError as e:
                log.warning("getUpdates: %s", type(e).__name__)  # xabarda URL (token) bo'lishi mumkin
                time.sleep(3)
                continue
            for upd in updates:
                offset = upd["update_id"] + 1
                msg = upd.get("message") or {}
                if msg.get("text", "").startswith("/start"):
                    call(client, "sendMessage", chat_id=msg["chat"]["id"], text=WELCOME, reply_markup={
                        "inline_keyboard": [[{"text": "🍲 Oshxonani ochish", "web_app": {"url": settings.webapp_url}}]],
                    })


if __name__ == "__main__":
    main()
