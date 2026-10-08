"""Erkin matndan masalliqlarni ajratib olish (LLMsiz zaxira varianti). O'zbek, ingliz va turk tillarida.

Misol: "2 kg guruch, 10 ta piyoz" / "2 kg pirinç, 10 adet soğan" / "2 kg rice, 10 onions" ->
    [ParsedItem("guruch", 2000), ParsedItem("piyoz", 1500)]
"""

import re
from dataclasses import dataclass

from .ingredients import UNIT_ALIASES, canonical, lookup, normalize, to_grams

WORD_NUMBERS = {
    # o'zbekcha
    "yarim": 0.5, "bir": 1, "ikki": 2, "uch": 3, "to'rt": 4, "tort": 4, "besh": 5,
    "olti": 6, "yetti": 7, "sakkiz": 8, "to'qqiz": 9, "toqqiz": 9, "o'n": 10, "on": 10,
    "bir yarim": 1.5, "ikki yarim": 2.5,
    # turkcha ("bir" va "on" yuqorida bor)
    "yarım": 0.5, "iki": 2, "üç": 3, "dört": 4, "beş": 5, "altı": 6, "yedi": 7, "sekiz": 8, "dokuz": 9,
    "bir buçuk": 1.5, "iki buçuk": 2.5,
    # inglizcha
    "half a": 0.5, "half": 0.5, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "one and a half": 1.5, "a couple of": 2,
    "a dozen": "1 dozen", "a": 1, "an": 1,
}

# Gap oxiridagi fe'llar va ortiqcha so'zlar
STOPWORDS = {
    "olib", "keldim", "oldim", "sotib", "bor", "qo'sh", "qo'shing", "qoshing", "uyda", "uyga",
    "bozordan", "marketdan", "do'kondan", "dokondan", "yana", "ham", "va", "edim", "keltirdim",
    "qo'ydim", "qoydim", "xarid", "qildim",
    # turkcha
    "aldım", "aldim", "aldık", "getirdim", "pazardan", "marketten", "manavdan", "bakkaldan", "kasaptan",
    "evde", "eve", "ve", "de", "da", "biraz", "taze", "var", "ayrıca",
    # inglizcha
    "i", "we", "bought", "got", "picked", "up", "from", "the", "market", "store", "shop", "some", "of",
    "fresh", "and", "also", "have", "today",
}

# Vergul ajratuvchi, lekin "1,5 kg" dagi o'nlik vergul emas
_SPLIT = re.compile(r"(?:(?<!\d),|,(?!\d)|[;\n])+|\s+(?:va|hamda|ve|and|&)\s+")
_NUM = r"(\d+(?:[.,]\d+)?)"
_UNIT_WORDS = sorted(UNIT_ALIASES, key=len, reverse=True)
_UNIT = r"(" + "|".join(re.escape(u) for u in _UNIT_WORDS) + r")\.?"

# "2 kg guruch", "2kg guruch", "10 ta piyoz", "guruch 2 kg", "guruch - 2kg"
_QTY_FIRST = re.compile(rf"^{_NUM}\s*(?:{_UNIT}(?=\s|$))?\s*(.+)$")
_NAME_FIRST = re.compile(rf"^(.+?)\s*[-:–]?\s*{_NUM}\s*(?:{_UNIT})?$")


@dataclass
class ParsedItem:
    name: str
    category: str
    grams: float
    raw: str


def _words_to_digits(text: str) -> str:
    for word, value in sorted(WORD_NUMBERS.items(), key=lambda kv: len(kv[0]), reverse=True):
        text = re.sub(rf"(?<![\w']){re.escape(word)}(?![\w'])", str(value), text)
    return text


def _clean_name(name: str) -> str:
    words = [w for w in name.split() if w.strip(".!?") not in STOPWORDS]
    return " ".join(words).strip(" .!?-:")


def parse_stock_text(text: str) -> tuple[list[ParsedItem], list[str]]:
    """Qaytaradi: (tanilgan masalliqlar, tushunilmagan bo'laklar)."""
    items: list[ParsedItem] = []
    unknown: list[str] = []
    for chunk in _SPLIT.split(normalize(text)):
        chunk = chunk.strip(" .!?")
        if not chunk:
            continue
        prepared = _words_to_digits(chunk)
        # "i bought 2 kg rice" -> "2 kg rice": boshidagi ortiqcha so'zlar sonni to'smasin
        words = prepared.split()
        while words and words[0] in STOPWORDS:
            words.pop(0)
        prepared = " ".join(words)
        qty, unit, name = None, None, None
        if m := _QTY_FIRST.match(prepared):
            qty, unit, name = m.group(1), m.group(2), m.group(3)
        elif m := _NAME_FIRST.match(prepared):
            name, qty, unit = m.group(1), m.group(2), m.group(3)
        if not name:
            unknown.append(chunk)
            continue
        name = _clean_name(name)
        if not name:
            unknown.append(chunk)
            continue
        canon, category = canonical(name)
        in_catalog = lookup(name) is not None
        weight_unit = UNIT_ALIASES.get(normalize(unit)) in ("kg", "g", "l", "ml") if unit else False
        if not in_catalog and (not weight_unit or len(name.split()) > 3):
            # Katalogda yo'q va aniq og'irlik berilmagan ("bir chelak olma") — taxmin qilmaymiz
            unknown.append(chunk)
            continue
        quantity = float(qty.replace(",", "."))
        grams = to_grams(quantity, unit, canon)
        if grams <= 0:
            unknown.append(chunk)
            continue
        items.append(ParsedItem(canon, category, grams, chunk))
    return items, unknown
