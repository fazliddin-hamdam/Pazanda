import pytest

from app.ingredients import format_grams, lookup, to_grams
from app.parser import parse_stock_text


def as_dict(text):
    items, unknown = parse_stock_text(text)
    return {i.name: round(i.grams) for i in items}, unknown


def test_spec_example():
    items, unknown = as_dict("2 kg guruch, 10 ta piyoz, 1 kg sabzi")
    assert items == {"guruch": 2000, "piyoz": 1500, "sabzi": 1000}
    assert unknown == []


def test_sentence_with_verb():
    items, _ = as_dict("1 kg go'sht olib keldim")
    assert items == {"go'sht": 1000}


@pytest.mark.parametrize("text,name,grams", [
    ("yarim kg mol go'shti", "mol go'shti", 500),
    ("bir yarim kg kartoshka", "kartoshka", 1500),
    ("uch ta pomidor", "pomidor", 360),
    ("guruch 3kg", "guruch", 3000),
    ("1 l o'simlik yog'i", "o'simlik yog'i", 920),
    ("500 gr qiyma", "qiyma", 500),
    ("2 bog' shivit", "shivit", 100),
    ("5 piyoz", "piyoz", 750),
    ("1,5 kg goʻsht", "go'sht", 1500),
    ("10 dona tuxum", "tuxum", 550),
])
def test_variants(text, name, grams):
    items, _ = as_dict(text)
    assert items == {name: grams}


def test_and_separator_and_unknown():
    items, unknown = as_dict("2 kg un va 6 ta tuxum, salom qalaysiz")
    assert items == {"un": 2000, "tuxum": 330}
    assert unknown == ["salom qalaysiz"]


def test_lookup_suffix_and_longest_match():
    assert lookup("piyozni").name == "piyoz"
    assert lookup("qo'y go'shti").name == "qo'y go'shti"
    assert lookup("bulg'or qalampiri").name == "bulg'or qalampiri"
    assert lookup("kosmos") is None


def test_units():
    assert to_grams(1, "ta", "piyoz") == 150
    assert to_grams(2, "kg", "un") == 2000
    assert format_grams(1500, "guruch") == "1.5 kg"
    assert format_grams(450, "piyoz") == "450 gramm (≈3 ta)"
    assert format_grams(920, "o'simlik yog'i") == "1 litr"
