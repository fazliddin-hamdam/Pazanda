"""Oshpaz-yordamchining samimiy o'zbekcha matnlari."""

import random

from .ingredients import format_grams
from .kitchen import RecipeCheck

PERSONA_SYSTEM = """Sen "Pazanda" — o'zbek oshxonasini yaxshi biladigan, tajribali va samimiy oshpaz-yordamchisan.
Foydalanuvchi bilan faqat o'zbek tilida (lotin yozuvida) gaplash. Rasmiy robotdek emas, oshxonada yonida turgan
mehribon opa yoki aka kabi iliq va qisqa gapir. Qozon, zirvak, kapgir, damlash, dasturxon kabi
milliy atamalarni tabiiy ishlat. Faqat o'zbek taomlari va oshxona mavzusida yordam ber; boshqa mavzularda
muloyimlik bilan oshxonaga qaytar. Javoblaring 1-4 gapdan oshmasin, ro'yxat kerak bo'lsa qisqa qil."""


def greeting(first_name: str) -> str:
    name = first_name or "aziz pazanda"
    return random.choice([
        f"Assalomu alaykum, {name}! Qozon tayyormi? Bugun nima pishiramiz?",
        f"Xush kelibsiz, {name}! Omborga bir ko'z tashlab, mazali narsa o'ylab topamiz.",
        f"Salom, {name}! Bozordan nima olib keldingiz? Yozib qo'ying, qolganini o'zim hisoblayman.",
    ])


def stock_added(added: list[tuple[str, float]], unknown: list[str]) -> str:
    if not added and unknown:
        return "Kechirasiz, tushunmadim 🙈 Masalan, shunday yozing: \"2 kg guruch, 5 ta piyoz, 1 kg go'sht\"."
    parts = ", ".join(f"{format_grams(g, n)} {n}" for n, g in added)
    text = f"Barakalla! Omborga qo'shdim: {parts}."
    if unknown:
        text += " Lekin bularni tushunmadim: " + "; ".join(f"\"{u}\"" for u in unknown) + "."
    return text


def _missing_list(check: RecipeCheck) -> str:
    return ", ".join(f"{format_grams(i.missing_g, i.name)} {i.name}" for i in check.missing)


def suggestions(checks: list[RecipeCheck], servings: int) -> str:
    if not checks:
        return ("Omborimiz hozircha bo'sh ko'rinadi. Bozordan nima olib kelganingizni yozing — "
                "keyin birgalikda qozonga nima tushishini hal qilamiz!")
    lines = [f"Keling, ko'raylik... Omboringizga qarab, {servings} kishiga mana bular chiqadi:"]
    for c in checks:
        if c.ready:
            lines.append(f"• {c.name} — hamma masalliq joyida, bemalol qilsa bo'ladi!")
        else:
            lines.append(f"• {c.name} — {_missing_list(c)} yetishmaydi.")
    return "\n".join(lines)


def plan(check: RecipeCheck) -> str:
    if check.ready:
        return (f"{check.name} uchun hamma narsa yetarli, {check.servings} kishiga bemalol yetadi! "
                "Boshlaymizmi?")
    enough = [i.name for i in check.ingredients if not i.optional and not i.staple and i.missing_g <= 5]
    head = f"{check.name} uchun {', '.join(enough)} yetarli, lekin" if enough else f"{check.name} uchun"
    return f"{head} {check.servings} kishiga yana {_missing_list(check)} kerak. Xarid ro'yxatiga qo'shaymi?"


def start_cooking(name: str, servings: int) -> str:
    return random.choice([
        f"Bismillah, boshladik! {servings} kishilik {name} tayyorlaymiz. Men yoningizdaman, qadamma-qadam boramiz.",
        f"Qani, yenglarni shimaraylik! {servings} kishilik {name} — hozir hammasini tushuntirib beraman.",
    ])


def finished(name: str) -> str:
    return random.choice([
        f"Osh bo'lsin! 🍽 {name} tayyor. Ishlatilgan masalliqlarni ombordan ayirib qo'ydim.",
        f"Barakalla, qo'lingiz dard ko'rmasin! {name} dasturxonga yarashadi. Omborni yangilab qo'ydim.",
    ])


NOT_FOUND = ("Afsuski, bu taomni topa olmadim. Nomini boshqacharoq yozib ko'ring "
             "(masalan: \"qozon kabob\", \"lag'mon\", \"dimlama\").")
NOT_UZBEK = ("Men faqat o'zbek oshxonasi bo'yicha pazandaman 😊 Bu taom bizning dasturxondan emas ekan. "
             "Osh, lag'mon yoki manti qilib ko'rmaysizmi?")
AI_OFFLINE = ("Bu taom hali retseptlar daftarimda yo'q, yangi retsept izlash esa hozir ishlamayapti. "
              "Ro'yxatdagi taomlardan birini tanlab ko'ring.")
