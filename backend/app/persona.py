"""Oshpaz-yordamchining samimiy matnlari — o'zbek, ingliz va turk tillarida."""

import random

from .ingredients import DEFAULT_LANG, display_name, format_grams
from .kitchen import RecipeCheck

LANGUAGE_NAMES = {"uz": "Uzbek (Latin script)", "en": "English", "tr": "Turkish"}


def lang_from_code(code: str | None) -> str:
    """Telegram language_code -> ilova tili. Turk va ingliz tillaridan boshqasi uchun o'zbekcha."""
    code = (code or "").lower()
    if code.startswith("tr"):
        return "tr"
    if code.startswith("en"):
        return "en"
    return "uz"


def persona_system(lang: str) -> str:
    return f"""You are "Pazanda", a warm, experienced home cook who knows Uzbek cuisine inside out and helps the
user in their kitchen. Always reply in {LANGUAGE_NAMES.get(lang, LANGUAGE_NAMES[DEFAULT_LANG])}, whatever language
the user writes in. Sound like a kind friend standing next to them at the stove, not a formal robot. Use Uzbek
culinary words naturally (qozon, zirvak, kapgir, dasturxon...) and, when not replying in Uzbek, briefly explain
them the first time. Only help with Uzbek dishes and cooking; gently steer other topics back to the kitchen.
Keep answers to 1-4 sentences; if a list is needed, keep it short."""


# Har bir matn: til -> shablon yoki shablonlar ro'yxati (tasodifiy tanlanadi)
TEXTS: dict[str, dict[str, str | list[str]]] = {
    "greeting": {
        "uz": [
            "Assalomu alaykum, {name}! Qozon tayyormi? Bugun nima pishiramiz?",
            "Xush kelibsiz, {name}! Omborga bir ko'z tashlab, mazali narsa o'ylab topamiz.",
            "Salom, {name}! Bozordan nima olib keldingiz? Yozib qo'ying, qolganini o'zim hisoblayman.",
        ],
        "en": [
            "Assalomu alaykum, {name}! Is the qozon ready? What shall we cook today?",
            "Welcome, {name}! Let's peek into the pantry and come up with something delicious.",
            "Hi {name}! What did you bring from the market? Write it down and I'll do the maths.",
        ],
        "tr": [
            "Assalomu alaykum, {name}! Kazan hazır mı? Bugün ne pişiriyoruz?",
            "Hoş geldin, {name}! Kilere bir göz atalım, lezzetli bir şey bulalım.",
            "Selam {name}! Pazardan ne aldın? Yaz bakalım, gerisini ben hesaplarım.",
        ],
    },
    "friend": {"uz": "aziz pazanda", "en": "dear cook", "tr": "sevgili aşçı"},
    "not_understood": {
        "uz": "Kechirasiz, tushunmadim 🙈 Masalan, shunday yozing: \"2 kg guruch, 5 ta piyoz, 1 kg go'sht\".",
        "en": "Sorry, I didn't get that 🙈 Try something like: \"2 kg rice, 5 onions, 1 kg beef\".",
        "tr": "Kusura bakma, anlayamadım 🙈 Şöyle yazabilirsin: \"2 kg pirinç, 5 adet soğan, 1 kg et\".",
    },
    "stock_added": {
        "uz": "Barakalla! Omborga qo'shdim: {items}.",
        "en": "Lovely! Added to your pantry: {items}.",
        "tr": "Harika! Kilere ekledim: {items}.",
    },
    "stock_unknown": {
        "uz": " Lekin bularni tushunmadim: {items}.",
        "en": " But I couldn't understand: {items}.",
        "tr": " Ama şunları anlayamadım: {items}.",
    },
    "suggest_empty": {
        "uz": "Omborimiz hozircha bo'sh ko'rinadi. Bozordan nima olib kelganingizni yozing — keyin birgalikda qozonga nima tushishini hal qilamiz!",
        "en": "Your pantry looks empty for now. Tell me what you brought from the market — then we'll decide together what goes into the qozon!",
        "tr": "Kiler şimdilik boş görünüyor. Pazardan ne aldığını yaz — sonra kazana ne gireceğine birlikte karar veririz!",
    },
    "suggest_head": {
        "uz": "Keling, ko'raylik... Omboringizga qarab, {n} kishiga mana bular chiqadi:",
        "en": "Let's see... Based on your pantry, here's what we can make for {n}:",
        "tr": "Bir bakalım... Kilerdekilere göre {n} kişilik şunlar çıkar:",
    },
    "suggest_ready": {
        "uz": "• {dish} — hamma masalliq joyida, bemalol qilsa bo'ladi!",
        "en": "• {dish} — you have everything, go for it!",
        "tr": "• {dish} — her şey tamam, rahatça yapabilirsin!",
    },
    "suggest_missing": {
        "uz": "• {dish} — {missing} yetishmaydi.",
        "en": "• {dish} — missing {missing}.",
        "tr": "• {dish} — eksik: {missing}.",
    },
    "plan_ready": {
        "uz": "{dish} uchun hamma narsa yetarli, {n} kishiga bemalol yetadi! Boshlaymizmi?",
        "en": "You have everything for {dish} — plenty for {n}! Shall we start?",
        "tr": "{dish} için her şey yeterli, {n} kişiye rahatça yeter! Başlayalım mı?",
    },
    "plan_missing": {
        "uz": "{dish} uchun {enough} yetarli, lekin {n} kishiga yana {missing} kerak. Xarid ro'yxatiga qo'shaymi?",
        "en": "For {dish} you have enough {enough}, but for {n} people you still need {missing}. Shall I add it to the shopping list?",
        "tr": "{dish} için {enough} yeterli, ama {n} kişi için {missing} daha lazım. Alışveriş listesine ekleyeyim mi?",
    },
    "plan_missing_all": {
        "uz": "{dish} uchun {n} kishiga yana {missing} kerak. Xarid ro'yxatiga qo'shaymi?",
        "en": "For {dish} for {n} people you still need {missing}. Shall I add it to the shopping list?",
        "tr": "{n} kişilik {dish} için {missing} daha lazım. Alışveriş listesine ekleyeyim mi?",
    },
    "start": {
        "uz": [
            "Bismillah, boshladik! {n} kishilik {dish} tayyorlaymiz. Men yoningizdaman, qadamma-qadam boramiz.",
            "Qani, yenglarni shimaraylik! {n} kishilik {dish} — hozir hammasini tushuntirib beraman.",
        ],
        "en": [
            "Bismillah, let's begin! We're making {dish} for {n}. I'm right here with you, step by step.",
            "Sleeves up! {dish} for {n} — I'll walk you through everything.",
        ],
        "tr": [
            "Bismillah, başlıyoruz! {n} kişilik {dish} yapıyoruz. Ben yanındayım, adım adım gideceğiz.",
            "Haydi kolları sıvayalım! {n} kişilik {dish} — şimdi her şeyi anlatıyorum.",
        ],
    },
    "finished": {
        "uz": [
            "Osh bo'lsin! 🍽 {dish} tayyor. Ishlatilgan masalliqlarni ombordan ayirib qo'ydim.",
            "Barakalla, qo'lingiz dard ko'rmasin! {dish} dasturxonga yarashadi. Omborni yangilab qo'ydim.",
        ],
        "en": [
            "Osh bo'lsin — enjoy your meal! 🍽 {dish} is ready. I've taken the used ingredients out of your pantry.",
            "Well done, what skilled hands! {dish} will grace the dasturxon. Your pantry is updated.",
        ],
        "tr": [
            "Afiyet olsun! 🍽 {dish} hazır. Kullanılan malzemeleri kilerden düştüm.",
            "Ellerine sağlık! {dish} sofraya çok yakışacak. Kileri güncelledim.",
        ],
    },
    "shopping_added": {
        "uz": "Xarid ro'yxatiga qo'shdim. Bozorga borganingizda esdan chiqmaydi!",
        "en": "Added to your shopping list — you won't forget it at the market!",
        "tr": "Alışveriş listesine ekledim. Pazara gidince unutmazsın!",
    },
    "not_found": {
        "uz": "Afsuski, bu taomni topa olmadim. Nomini boshqacharoq yozib ko'ring (masalan: \"qozon kabob\", \"lag'mon\", \"dimlama\").",
        "en": "Sorry, I couldn't find that dish. Try spelling it differently (e.g. \"qozon kabob\", \"lagman\", \"dimlama\").",
        "tr": "Maalesef bu yemeği bulamadım. Adını farklı yazmayı dene (örneğin: \"kazan kebabı\", \"lağman\", \"dımlama\").",
    },
    "not_uzbek": {
        "uz": "Men faqat o'zbek oshxonasi bo'yicha pazandaman 😊 Bu taom bizning dasturxondan emas ekan. Osh, lag'mon yoki manti qilib ko'rmaysizmi?",
        "en": "I only cook Uzbek cuisine 😊 That dish isn't from our dasturxon. How about plov, lagman or manti?",
        "tr": "Ben sadece Özbek mutfağında ustayım 😊 Bu yemek bizim sofradan değil. Pilav, lağman ya da mantı denemeye ne dersin?",
    },
    "ai_offline": {
        "uz": "Bu taom hali retseptlar daftarimda yo'q, yangi retsept izlash esa hozir ishlamayapti. Ro'yxatdagi taomlardan birini tanlab ko'ring.",
        "en": "That dish isn't in my recipe book yet, and searching for new recipes isn't available right now. Please pick one from the list.",
        "tr": "Bu yemek henüz tarif defterimde yok, yeni tarif arama da şu an çalışmıyor. Listeden bir yemek seçmeyi dene.",
    },
    "chat_offline": {
        "uz": "Hozircha savollarga javob bera olmayman, lekin retsept qadamlari doim shu yerda!",
        "en": "I can't answer questions right now, but the recipe steps are always here!",
        "tr": "Şu an sorulara cevap veremiyorum ama tarif adımları hep burada!",
    },
    "chat_failed": {
        "uz": "Kechirasiz, hozir javob bera olmadim. Birozdan keyin qayta so'rang.",
        "en": "Sorry, I couldn't answer just now. Please ask again in a moment.",
        "tr": "Kusura bakma, şu an cevap veremedim. Birazdan tekrar sor.",
    },
    "item_not_found": {"uz": "Topilmadi", "en": "Not found", "tr": "Bulunamadı"},
    "chat_context": {
        "uz": "Foydalanuvchi hozir {n} kishilik {dish} tayyorlamoqda.\nRetsept:\n{steps}",
        "en": "The user is currently cooking {dish} for {n}.\nRecipe:\n{steps}",
        "tr": "Kullanıcı şu anda {n} kişilik {dish} pişiriyor.\nTarif:\n{steps}",
    },
}


def t(key: str, lang: str, **kwargs) -> str:
    variants = TEXTS[key]
    template = variants.get(lang) or variants[DEFAULT_LANG]
    if isinstance(template, list):
        template = random.choice(template)
    return template.format(**kwargs)


def greeting(first_name: str, lang: str) -> str:
    return t("greeting", lang, name=first_name or t("friend", lang))


def _amount(grams: float, name: str, lang: str) -> str:
    return f"{format_grams(grams, name, lang)} {display_name(name, lang)}"


def stock_added(added: list[tuple[str, float]], unknown: list[str], lang: str) -> str:
    if not added and unknown:
        return t("not_understood", lang)
    text = t("stock_added", lang, items=", ".join(_amount(g, n, lang) for n, g in added))
    if unknown:
        text += t("stock_unknown", lang, items="; ".join(f"\"{u}\"" for u in unknown))
    return text


def _missing_list(check: RecipeCheck, lang: str) -> str:
    return ", ".join(_amount(i.missing_g, i.name, lang) for i in check.missing)


def suggestions(checks: list[RecipeCheck], servings: int, lang: str) -> str:
    if not checks:
        return t("suggest_empty", lang)
    lines = [t("suggest_head", lang, n=servings)]
    for c in checks:
        if c.ready:
            lines.append(t("suggest_ready", lang, dish=c.name))
        else:
            lines.append(t("suggest_missing", lang, dish=c.name, missing=_missing_list(c, lang)))
    return "\n".join(lines)


def plan(check: RecipeCheck, lang: str) -> str:
    if check.ready:
        return t("plan_ready", lang, dish=check.name, n=check.servings)
    enough = [display_name(i.name, lang) for i in check.ingredients if not i.optional and not i.staple and i.missing_g <= 5]
    if not enough:
        return t("plan_missing_all", lang, dish=check.name, n=check.servings, missing=_missing_list(check, lang))
    return t("plan_missing", lang, dish=check.name, n=check.servings, enough=", ".join(enough), missing=_missing_list(check, lang))


def start_cooking(name: str, servings: int, lang: str) -> str:
    return t("start", lang, dish=name, n=servings)


def finished(name: str, lang: str) -> str:
    return t("finished", lang, dish=name)
