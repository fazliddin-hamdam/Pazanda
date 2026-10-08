"""Masalliqlar katalogi, nomlarni normallashtirish va birliklarni grammga o'girish.

Bazada masalliqlar har doim kanonik o'zbekcha nom bilan saqlanadi; foydalanuvchiga esa
tanlangan tilda (uz / en / tr) ko'rsatiladi. Kiritishda uch tildagi nomlar ham tushuniladi.
"""

import re
from dataclasses import dataclass

LANGS = ("uz", "en", "tr")
DEFAULT_LANG = "uz"

CATEGORIES = {
    "gosht": {"uz": "Go'sht", "en": "Meat", "tr": "Et"},
    "sabzavot": {"uz": "Sabzavotlar", "en": "Vegetables", "tr": "Sebzeler"},
    "don": {"uz": "Don mahsulotlari", "en": "Grains & legumes", "tr": "Tahıl ve bakliyat"},
    "sut": {"uz": "Sut mahsulotlari", "en": "Dairy & eggs", "tr": "Süt ürünleri ve yumurta"},
    "yog": {"uz": "Yog'lar", "en": "Oils & fats", "tr": "Yağlar"},
    "ziravor": {"uz": "Ziravorlar", "en": "Spices", "tr": "Baharatlar"},
    "boshqa": {"uz": "Boshqalar", "en": "Other", "tr": "Diğer"},
}


def category_title(key: str, lang: str) -> str:
    titles = CATEGORIES.get(key) or CATEGORIES["boshqa"]
    return titles.get(lang, titles[DEFAULT_LANG])


@dataclass(frozen=True)
class Ingredient:
    name: str  # kanonik nom (o'zbek lotin, kichik harf)
    category: str
    en: str
    tr: str
    aliases: tuple[str, ...] = ()  # istalgan tildagi boshqa yozilishlar
    piece_g: float | None = None  # 1 ta / 1 dona / 1 bosh og'irligi
    bunch_g: float | None = None  # 1 bog' og'irligi
    density: float = 1.0  # litr -> kg
    staple: bool = False  # tuz, ziravor, suv: tekshirilmaydi va ayirilmaydi


I = Ingredient

CATALOG: list[Ingredient] = [
    # Go'sht
    I("go'sht", "gosht", "meat", "et", ("gosht", "myaso", "мясо", "гўшт", "red meat", "kırmızı et")),
    I("mol go'shti", "gosht", "beef", "dana eti", ("mol goshti", "mol gosht", "govyadina", "sığır eti", "dana")),
    I("qo'y go'shti", "gosht", "lamb", "kuzu eti", ("qoy goshti", "qoy gosht", "baranina", "mutton", "koyun eti", "kuzu")),
    I("qiyma", "gosht", "minced meat", "kıyma", ("qiyma gosht", "farsh", "ground beef", "ground meat", "mince")),
    I("tovuq go'shti", "gosht", "chicken", "tavuk", ("tovuq", "tovuq goshti", "kurica", "tavuk eti"), piece_g=1500),
    I("dumba yog'i", "gosht", "lamb tail fat", "kuyruk yağı", ("dumba", "dumba yogi", "tail fat")),
    # Sabzavotlar
    I("piyoz", "sabzavot", "onion", "soğan", ("piez", "luk", "kuru soğan"), piece_g=150),
    I("sabzi", "sabzavot", "carrot", "havuç", ("sariq sabzi", "qizil sabzi", "morkov", "sarı havuç"), piece_g=120),
    I("kartoshka", "sabzavot", "potato", "patates", ("kartofel",), piece_g=150),
    I("pomidor", "sabzavot", "tomato", "domates", ("pamidor", "tomat"), piece_g=120),
    I("bodring", "sabzavot", "cucumber", "salatalık", ("ogurec", "hıyar"), piece_g=120),
    I("sarimsoq", "sabzavot", "garlic", "sarımsak", ("sarimsoq piyoz", "chesnok", "sarmısak"), piece_g=40),
    I("bulg'or qalampiri", "sabzavot", "bell pepper", "dolmalık biber",
      ("bulgor qalampiri", "bulgor qalampir", "bolgar qalampiri", "shirin qalampir", "sweet pepper", "pepper",
       "biber", "kapya biber", "çarliston biber", "yeşil biber"), piece_g=150),
    I("achchiq qalampir", "sabzavot", "chili pepper", "acı biber", ("achchiq qalampiri", "chili", "hot pepper", "sivri biber"), piece_g=15),
    I("karam", "sabzavot", "cabbage", "lahana", ("kapusta",), piece_g=1500),
    I("baqlajon", "sabzavot", "eggplant", "patlıcan", ("baklajan", "aubergine"), piece_g=250),
    I("qovoq", "sabzavot", "pumpkin", "balkabağı", ("tikva", "bal kabağı"), piece_g=2000),
    I("turp", "sabzavot", "radish", "turp", ("rediska", "daikon"), piece_g=300),
    I("sholg'om", "sabzavot", "turnip", "şalgam", ("sholgom",), piece_g=250),
    I("ko'k piyoz", "sabzavot", "green onion", "yeşil soğan", ("kok piyoz", "spring onion", "scallion", "taze soğan"), bunch_g=100),
    I("shivit", "sabzavot", "dill", "dereotu", ("ukrop", "ukrob", "dere otu"), bunch_g=50),
    I("kashnich", "sabzavot", "coriander", "kişniş", ("kinza", "kashnich ko'ki", "cilantro"), bunch_g=50),
    I("rayhon", "sabzavot", "basil", "fesleğen", ("bazilik", "reyhan"), bunch_g=30),
    # Don mahsulotlari
    I("guruch", "don", "rice", "pirinç", ("ris", "devzira", "lazer guruch", "baldo", "osmancık")),
    I("un", "don", "flour", "un", ("muka",)),
    I("no'xat", "don", "chickpeas", "nohut", ("noxat", "chickpea")),
    I("mosh", "don", "mung beans", "maş fasulyesi", ("mash", "mung bean", "maş")),
    I("loviya", "don", "beans", "kuru fasulye", ("fasol", "kidney beans", "fasulye")),
    I("makaron", "don", "pasta", "makarna", ("vermishel", "noodles")),
    # Sut mahsulotlari
    I("tuxum", "sut", "eggs", "yumurta", ("yaytso", "egg"), piece_g=55),
    I("sut", "sut", "milk", "süt", ("moloko",), density=1.03),
    I("qatiq", "sut", "yogurt", "yoğurt", ("katik", "yoghurt"), density=1.03),
    I("qaymoq", "sut", "sour cream", "kaymak", ("smetana", "cream", "krema")),
    I("sariyog'", "sut", "butter", "tereyağı", ("sariyog", "saryog", "tereyağ"), piece_g=200),
    # Yog'lar
    I("o'simlik yog'i", "yog", "vegetable oil", "sıvı yağ",
      ("osimlik yogi", "paxta yogi", "kungaboqar yogi", "yog'", "yog", "maslo", "oil", "cooking oil",
       "sunflower oil", "ayçiçek yağı", "yağ"), density=0.92),
    # Ziravorlar va doimiy mahsulotlar
    I("tuz", "ziravor", "salt", "tuz", (), staple=True),
    I("zira", "ziravor", "cumin", "kimyon", ("cumin seeds",), staple=True),
    I("qora murch", "ziravor", "black pepper", "karabiber", ("murch", "qora qalampir", "kara biber"), staple=True),
    I("qizil qalampir", "ziravor", "red pepper flakes", "pul biber",
      ("maydalangan qalampir", "paprika", "kırmızı toz biber", "kırmızı biber"), staple=True),
    I("kashnich urug'i", "ziravor", "coriander seeds", "kişniş tohumu", ("kashnich urugi",), staple=True),
    I("zirk", "ziravor", "barberries", "amberbaris", ("barberry", "kadın tuzluğu"), staple=True),
    I("suv", "ziravor", "water", "su", (), staple=True),
    # Boshqalar
    I("tomat pastasi", "boshqa", "tomato paste", "domates salçası", ("tomat pasta", "salça")),
    I("non", "boshqa", "bread", "ekmek", ("lepyoshka",), piece_g=300),
    I("mayiz", "boshqa", "raisins", "kuru üzüm", ("kishmish", "raisin")),
    I("limon", "boshqa", "lemon", "limon", (), piece_g=100),
    I("olma", "boshqa", "apple", "elma", ("yabloko",), piece_g=180),
]

# Retseptda "go'sht" so'ralsa, shulardan istalgani yaraydi (ayirish ham shu tartibda).
SUBSTITUTES: dict[str, list[str]] = {
    "go'sht": ["go'sht", "mol go'shti", "qo'y go'shti", "qiyma"],
}

_APOSTROPHES = re.compile(r"[ʻʼ’‘`´]")
_TURKISH_FOLD = str.maketrans({"ı": "i", "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ç": "c", "â": "a", "î": "i", "û": "u"})


def normalize(text: str) -> str:
    """Kichik harf, barcha apostrof turlarini ' ga keltirish, ortiqcha bo'shliqlarni olib tashlash."""
    text = _APOSTROPHES.sub("'", text.replace("İ", "i").lower())
    return re.sub(r"\s+", " ", text).strip()


def fold(text: str) -> str:
    """Solishtirish kaliti: apostrofsiz va turkcha harflarsiz ("go'sht" == "gosht", "soğan" == "sogan")."""
    return normalize(text).translate(_TURKISH_FOLD).replace("'", "")


_key = fold

BY_NAME: dict[str, Ingredient] = {i.name: i for i in CATALOG}

# (kalit, ingredient) juftliklari, eng uzunidan boshlab: "mol go'shti" "go'sht"dan oldin tekshiriladi
_ALIAS_INDEX: list[tuple[str, Ingredient]] = sorted(
    ((_key(alias), ing) for ing in CATALOG for alias in (ing.name, ing.en, ing.tr, *ing.aliases)),
    key=lambda pair: len(pair[0]),
    reverse=True,
)


def lookup(name: str) -> Ingredient | None:
    """Matn ichidan katalogdagi masalliqni topadi ("piyozni" / "soğanı" / "onions" -> piyoz)."""
    key = _key(name)
    if not key:
        return None
    words = key.split()
    for alias, ing in _ALIAS_INDEX:
        alias_words = alias.split()
        n = len(alias_words)
        for i in range(len(words) - n + 1):
            window = words[i : i + n]
            # oxirgi so'z qo'shimcha olishi mumkin: "piyozni", "soğanı", "potatoes"
            if window[:-1] == alias_words[:-1] and window[-1].startswith(alias_words[-1]):
                if len(window[-1]) - len(alias_words[-1]) <= 4:
                    return ing
    return None


def canonical(name: str) -> tuple[str, str]:
    """(kanonik nom, kategoriya). Katalogda bo'lmasa, normallashtirilgan nom va "boshqa"."""
    ing = lookup(name)
    if ing:
        return ing.name, ing.category
    return normalize(name), "boshqa"


def display_name(name: str, lang: str) -> str:
    """Kanonik nomni tanlangan tilda ko'rsatish. Katalogda yo'q nomlar o'zgarishsiz qoladi."""
    ing = BY_NAME.get(name)
    if not ing or lang == "uz":
        return name
    return getattr(ing, lang, name)


def is_staple(name: str) -> bool:
    ing = BY_NAME.get(name) or lookup(name)
    return bool(ing and ing.staple)


UNIT_ALIASES = {
    "kg": "kg", "kgs": "kg", "kilo": "kg", "kilos": "kg", "kilogramm": "kg", "kilogram": "kg", "kilograms": "kg", "кг": "kg",
    "g": "g", "gr": "g", "gramm": "g", "gram": "g", "grams": "g", "г": "g",
    "l": "l", "lt": "l", "litr": "l", "liter": "l", "litre": "l", "liters": "l", "litres": "l", "л": "l",
    "ml": "ml", "мл": "ml",
    "ta": "ta", "dona": "ta", "bosh": "ta", "шт": "ta", "та": "ta",
    "adet": "ta", "tane": "ta", "pcs": "ta", "pc": "ta", "piece": "ta", "pieces": "ta",
    "bog'": "bog", "bog": "bog", "bog'lam": "bog", "demet": "bog", "bunch": "bog", "bunches": "bog",
    "stakan": "stakan", "bardak": "stakan", "cup": "stakan", "cups": "stakan",
    "piyola": "piyola",
    "dozen": "dozen", "düzine": "dozen",
}

DEFAULT_PIECE_G = 100
DEFAULT_BUNCH_G = 50


def to_grams(quantity: float, unit: str | None, name: str) -> float:
    """Miqdor + birlikni grammga o'giradi. Birlik yo'q bo'lsa, masalliqqa qarab taxmin qiladi."""
    ing = BY_NAME.get(name) or lookup(name)
    unit = UNIT_ALIASES.get(normalize(unit), normalize(unit)) if unit else None
    density = ing.density if ing else 1.0
    piece = (ing and (ing.piece_g or ing.bunch_g)) or DEFAULT_PIECE_G

    if unit == "kg":
        return quantity * 1000
    if unit == "g":
        return quantity
    if unit == "l":
        return quantity * 1000 * density
    if unit == "ml":
        return quantity * density
    if unit == "stakan":
        return quantity * 200 * density
    if unit == "piyola":
        return quantity * 250 * density
    if unit == "bog":
        return quantity * ((ing and ing.bunch_g) or DEFAULT_BUNCH_G)
    if unit == "ta":
        return quantity * piece
    if unit == "dozen":
        return quantity * 12 * piece

    # Birliksiz: "5 piyoz" -> dona; "guruch 2" -> kg; "guruch 300" -> gramm
    if ing and ing.piece_g:
        return quantity * ing.piece_g
    if quantity <= 20:
        return quantity * 1000
    return quantity


UNIT_LABELS = {
    "uz": {"kg": "kg", "g": "gramm", "l": "litr", "ml": "ml", "pcs": "ta"},
    "en": {"kg": "kg", "g": "g", "l": "L", "ml": "ml", "pcs": "pcs"},
    "tr": {"kg": "kg", "g": "gr", "l": "litre", "ml": "ml", "pcs": "adet"},
}


def format_grams(grams: float, name: str | None = None, lang: str = DEFAULT_LANG) -> str:
    """Foydalanuvchiga ko'rsatish: "1.5 kg", "300 gramm", donali masalliqlar uchun "(≈2 ta)"."""
    units = UNIT_LABELS.get(lang, UNIT_LABELS[DEFAULT_LANG])
    ing = (BY_NAME.get(name) or lookup(name)) if name else None
    if ing and ing.density != 1.0 and ing.category in ("yog", "sut") and ing.name not in ("qaymoq", "sariyog'", "tuxum"):
        ml = grams / ing.density
        text = f"{_num(ml / 1000, lang)} {units['l']}" if ml >= 1000 else f"{_round(ml)} {units['ml']}"
    elif grams >= 1000:
        text = f"{_num(grams / 1000, lang)} {units['kg']}"
    else:
        text = f"{_round(grams)} {units['g']}"
    if ing and ing.piece_g and ing.piece_g <= 500:
        pieces = grams / ing.piece_g
        if pieces >= 0.5:
            text += f" (≈{_num(round(pieces * 2) / 2, lang)} {units['pcs']})"
    return text


def _round(value: float) -> int:
    if value >= 100:
        return int(round(value / 10) * 10)
    return max(1, int(round(value)))


def _num(value: float, lang: str = DEFAULT_LANG) -> str:
    value = round(value, 1)
    text = str(int(value)) if value == int(value) else str(value)
    return text.replace(".", ",") if lang == "tr" else text
