"""Masalliqlar katalogi, nomlarni normallashtirish va birliklarni grammga o'girish."""

import re
from dataclasses import dataclass, field

CATEGORIES = {
    "gosht": "Go'sht",
    "sabzavot": "Sabzavotlar",
    "don": "Don mahsulotlari",
    "sut": "Sut mahsulotlari",
    "yog": "Yog'lar",
    "ziravor": "Ziravorlar",
    "boshqa": "Boshqalar",
}


@dataclass(frozen=True)
class Ingredient:
    name: str  # kanonik nom (lotin, kichik harf)
    category: str
    aliases: tuple[str, ...] = ()
    piece_g: float | None = None  # 1 ta / 1 dona / 1 bosh og'irligi
    bunch_g: float | None = None  # 1 bog' og'irligi
    density: float = 1.0  # litr -> kg
    staple: bool = False  # tuz, ziravor, suv: tekshirilmaydi va ayirilmaydi
    extra: dict = field(default_factory=dict, compare=False, hash=False)


CATALOG: list[Ingredient] = [
    # Go'sht
    Ingredient("go'sht", "gosht", ("gosht", "myaso", "мясо", "гўшт")),
    Ingredient("mol go'shti", "gosht", ("mol goshti", "mol gosht", "govyadina")),
    Ingredient("qo'y go'shti", "gosht", ("qoy goshti", "qoy gosht", "baranina")),
    Ingredient("qiyma", "gosht", ("qiyma gosht", "farsh")),
    Ingredient("tovuq go'shti", "gosht", ("tovuq", "tovuq goshti", "kurica"), piece_g=1500),
    Ingredient("dumba yog'i", "gosht", ("dumba", "dumba yogi")),
    # Sabzavotlar
    Ingredient("piyoz", "sabzavot", ("piez", "lyuk", "luk"), piece_g=150),
    Ingredient("sabzi", "sabzavot", ("sariq sabzi", "qizil sabzi", "morkov"), piece_g=120),
    Ingredient("kartoshka", "sabzavot", ("kartofel",), piece_g=150),
    Ingredient("pomidor", "sabzavot", ("pamidor", "tomat"), piece_g=120),
    Ingredient("bodring", "sabzavot", ("ogurec",), piece_g=120),
    Ingredient("sarimsoq", "sabzavot", ("sarimsoq piyoz", "chesnok"), piece_g=40),
    Ingredient("bulg'or qalampiri", "sabzavot", ("bulgor qalampiri", "bulgor qalampir", "bolgar qalampiri", "shirin qalampir"), piece_g=150),
    Ingredient("achchiq qalampir", "sabzavot", ("achchiq qalampiri",), piece_g=15),
    Ingredient("karam", "sabzavot", ("kapusta",), piece_g=1500),
    Ingredient("baqlajon", "sabzavot", ("baklajan",), piece_g=250),
    Ingredient("qovoq", "sabzavot", ("tikva",), piece_g=2000),
    Ingredient("turp", "sabzavot", ("rediska",), piece_g=300),
    Ingredient("sholg'om", "sabzavot", ("sholgom",), piece_g=250),
    Ingredient("ko'k piyoz", "sabzavot", ("kok piyoz",), bunch_g=100),
    Ingredient("shivit", "sabzavot", ("ukrop", "ukrob"), bunch_g=50),
    Ingredient("kashnich", "sabzavot", ("kinza", "kashnich ko'ki"), bunch_g=50),
    Ingredient("rayhon", "sabzavot", ("bazilik",), bunch_g=30),
    # Don mahsulotlari
    Ingredient("guruch", "don", ("ris", "devzira", "lazer guruch")),
    Ingredient("un", "don", ("muka",)),
    Ingredient("no'xat", "don", ("noxat", "nut")),
    Ingredient("mosh", "don", ("mash",)),
    Ingredient("loviya", "don", ("fasol",)),
    Ingredient("makaron", "don", ("vermishel",)),
    # Sut mahsulotlari
    Ingredient("tuxum", "sut", ("yaytso",), piece_g=55),
    Ingredient("sut", "sut", ("moloko",), density=1.03),
    Ingredient("qatiq", "sut", ("katik",), density=1.03),
    Ingredient("qaymoq", "sut", ("smetana",)),
    Ingredient("sariyog'", "sut", ("sariyog", "saryog"), piece_g=200),
    # Yog'lar
    Ingredient("o'simlik yog'i", "yog", ("osimlik yogi", "paxta yogi", "kungaboqar yogi", "yog'", "yog", "maslo"), density=0.92),
    # Ziravorlar va doimiy mahsulotlar
    Ingredient("tuz", "ziravor", (), staple=True),
    Ingredient("zira", "ziravor", (), staple=True),
    Ingredient("qora murch", "ziravor", ("murch", "qora qalampir"), staple=True),
    Ingredient("qizil qalampir", "ziravor", ("maydalangan qalampir",), staple=True),
    Ingredient("kashnich urug'i", "ziravor", ("kashnich urugi",), staple=True),
    Ingredient("zirk", "ziravor", (), staple=True),
    Ingredient("suv", "ziravor", (), staple=True),
    # Boshqalar
    Ingredient("tomat pastasi", "boshqa", ("tomat pasta",)),
    Ingredient("non", "boshqa", (), piece_g=300),
    Ingredient("mayiz", "boshqa", ("kishmish",)),
    Ingredient("limon", "boshqa", (), piece_g=100),
    Ingredient("olma", "boshqa", ("yabloko",), piece_g=180),
]

# Retseptda "go'sht" so'ralsa, shulardan istalgani yaraydi (ayirish ham shu tartibda).
SUBSTITUTES: dict[str, list[str]] = {
    "go'sht": ["go'sht", "mol go'shti", "qo'y go'shti", "qiyma"],
}

_APOSTROPHES = re.compile(r"[ʻʼ’‘`´]")


def normalize(text: str) -> str:
    """Kichik harf, barcha apostrof turlarini ' ga keltirish, ortiqcha bo'shliqlarni olib tashlash."""
    text = _APOSTROPHES.sub("'", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _key(text: str) -> str:
    """Apostrofsiz solishtirish kaliti: "go'sht" == "gosht"."""
    return normalize(text).replace("'", "")


BY_NAME: dict[str, Ingredient] = {i.name: i for i in CATALOG}

# (kalit, ingredient) juftliklari, eng uzunidan boshlab: "mol go'shti" "go'sht"dan oldin tekshiriladi
_ALIAS_INDEX: list[tuple[str, Ingredient]] = sorted(
    ((_key(alias), ing) for ing in CATALOG for alias in (ing.name, *ing.aliases)),
    key=lambda pair: len(pair[0]),
    reverse=True,
)


def lookup(name: str) -> Ingredient | None:
    """Matn ichidan katalogdagi masalliqni topadi ("piyozni" -> piyoz, "mol go'shti" -> mol go'shti)."""
    key = _key(name)
    if not key:
        return None
    words = key.split()
    for alias, ing in _ALIAS_INDEX:
        alias_words = alias.split()
        n = len(alias_words)
        for i in range(len(words) - n + 1):
            window = words[i : i + n]
            # oxirgi so'z qo'shimcha olishi mumkin: "piyozni", "go'shtdan"
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


def is_staple(name: str) -> bool:
    ing = BY_NAME.get(name) or lookup(name)
    return bool(ing and ing.staple)


UNIT_ALIASES = {
    "kg": "kg", "kilo": "kg", "kilogramm": "kg", "kilogram": "kg", "кг": "kg",
    "g": "g", "gr": "g", "gramm": "g", "gram": "g", "г": "g",
    "l": "l", "litr": "l", "liter": "l", "л": "l",
    "ml": "ml", "мл": "ml",
    "ta": "ta", "dona": "ta", "bosh": "ta", "шт": "ta", "та": "ta",
    "bog'": "bog", "bog": "bog", "bog'lam": "bog",
    "stakan": "stakan", "piyola": "piyola",
}

DEFAULT_PIECE_G = 100
DEFAULT_BUNCH_G = 50


def to_grams(quantity: float, unit: str | None, name: str) -> float:
    """Miqdor + birlikni grammga o'giradi. Birlik yo'q bo'lsa, masalliqqa qarab taxmin qiladi."""
    ing = BY_NAME.get(name) or lookup(name)
    unit = UNIT_ALIASES.get(normalize(unit), normalize(unit)) if unit else None
    density = ing.density if ing else 1.0

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
        return quantity * ((ing and (ing.piece_g or ing.bunch_g)) or DEFAULT_PIECE_G)

    # Birliksiz: "5 piyoz" -> dona; "guruch 2" -> kg; "guruch 300" -> gramm
    if ing and ing.piece_g:
        return quantity * ing.piece_g
    if quantity <= 20:
        return quantity * 1000
    return quantity


def format_grams(grams: float, name: str | None = None) -> str:
    """Foydalanuvchiga ko'rsatish: "1.5 kg", "300 gramm", donali masalliqlar uchun "(≈2 ta)"."""
    ing = (BY_NAME.get(name) or lookup(name)) if name else None
    if ing and ing.density != 1.0 and ing.category in ("yog", "sut") and ing.name not in ("qaymoq", "sariyog'", "tuxum"):
        ml = grams / ing.density
        text = f"{_num(ml / 1000)} litr" if ml >= 1000 else f"{_round(ml)} ml"
    elif grams >= 1000:
        text = f"{_num(grams / 1000)} kg"
    else:
        text = f"{_round(grams)} gramm"
    if ing and ing.piece_g and ing.piece_g <= 500:
        pieces = grams / ing.piece_g
        if pieces >= 0.5:
            text += f" (≈{_num(round(pieces * 2) / 2)} ta)"
    return text


def _round(value: float) -> int:
    if value >= 100:
        return int(round(value / 10) * 10)
    return max(1, int(round(value)))


def _num(value: float) -> str:
    value = round(value, 1)
    return str(int(value)) if value == int(value) else str(value)
