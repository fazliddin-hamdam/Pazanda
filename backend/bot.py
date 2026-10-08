"""Telegram bot: /start buyrug'iga Mini App tugmasi bilan javob beradi va menyu tugmasini o'rnatadi.

Xabarlar foydalanuvchi ilovada tanlagan tilda; hali tanlamagan bo'lsa — Telegram tiliga qarab (uz / en / tr).

Ishga tushirish:  python bot.py   (TELEGRAM_BOT_TOKEN va WEBAPP_URL .env da bo'lishi kerak)
"""

import logging
import time

import httpx

from app.config import settings
from app.db import SessionLocal
from app.models import User
from app.persona import lang_from_code

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
# httpx har bir so'rov URL'ini yozadi, URL esa bot tokenini o'z ichiga oladi — logga tushmasin
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("bot")

API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"

WELCOME = {
    "uz": (
        "Assalomu alaykum! Men — Pazanda, oshxonadagi yordamchingiz 🍲\n\n"
        "Bozordan nima olib kelganingizni yozasiz, men omborni yuritaman. "
        "\"Bugun nima pishirsam?\" desangiz — bor masalliqqa qarab o'zbekcha taom tavsiya qilaman, "
        "yetishmaganini aytaman va qadamma-qadam retseptini beraman.\n\n"
        "Boshlash uchun pastdagi tugmani bosing 👇 (Tilni ilova ichida o'zgartirish mumkin.)"
    ),
    "en": (
        "Assalomu alaykum! I'm Pazanda, your kitchen helper 🍲\n\n"
        "Tell me what you brought from the market and I'll keep track of your pantry. "
        "Ask \"What should I cook today?\" and I'll suggest Uzbek dishes you can make, tell you what's missing "
        "and walk you through the recipe step by step.\n\n"
        "Tap the button below to start 👇 (You can change the language inside the app.)"
    ),
    "tr": (
        "Assalomu alaykum! Ben Pazanda, mutfaktaki yardımcın 🍲\n\n"
        "Pazardan ne aldığını yaz, kilerini ben takip edeyim. "
        "\"Bugün ne pişirsem?\" dersen elindeki malzemelere göre Özbek yemekleri öneririm, eksikleri söylerim "
        "ve tarifi adım adım anlatırım.\n\n"
        "Başlamak için aşağıdaki butona bas 👇 (Dili uygulamanın içinden değiştirebilirsin.)"
    ),
}
OPEN_BUTTON = {"uz": "🍲 Oshxonani ochish", "en": "🍲 Open the kitchen", "tr": "🍲 Mutfağı aç"}
MENU_BUTTON = {"uz": "Oshxona", "en": "Kitchen", "tr": "Mutfak"}
COMMAND = {"uz": "Pazandani ochish", "en": "Open Pazanda", "tr": "Pazanda'yı aç"}


def user_language(tg_user: dict) -> str:
    """Ilovada tanlangan til; bo'lmasa Telegram interfeysi tili."""
    try:
        with SessionLocal() as db:
            user = db.get(User, tg_user.get("id"))
            if user and user.language:
                return user.language
    except Exception as e:  # baza hali tayyor bo'lmasa ham bot javob bersin
        log.warning("Foydalanuvchi tilini o'qib bo'lmadi: %s", type(e).__name__)
    return lang_from_code(tg_user.get("language_code"))


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
            "type": "web_app", "text": "🍲 Pazanda", "web_app": {"url": settings.webapp_url},
        })
        call(client, "setMyCommands", commands=[{"command": "start", "description": COMMAND["uz"]}])
        for code in ("uz", "en", "tr"):
            call(client, "setMyCommands", commands=[{"command": "start", "description": COMMAND[code]}], language_code=code)
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
                    lang = user_language(msg.get("from") or {})
                    chat_id = msg["chat"]["id"]
                    call(client, "sendMessage", chat_id=chat_id, text=WELCOME[lang], reply_markup={
                        "inline_keyboard": [[{"text": OPEN_BUTTON[lang], "web_app": {"url": settings.webapp_url}}]],
                    })
                    # Shu chat uchun menyu tugmasi ham tanlangan tilda
                    call(client, "setChatMenuButton", chat_id=chat_id, menu_button={
                        "type": "web_app", "text": MENU_BUTTON[lang], "web_app": {"url": settings.webapp_url},
                    })


if __name__ == "__main__":
    main()
