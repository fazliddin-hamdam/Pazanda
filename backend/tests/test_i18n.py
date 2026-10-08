import pytest

from app.ingredients import CATALOG, display_name, format_grams, lookup
from app.parser import parse_stock_text
from app.persona import TEXTS
from app.seed_recipes import SEED_RECIPES
from app.seed_translations import TRANSLATIONS


def test_every_seed_recipe_is_translated_with_same_steps():
    for recipe in SEED_RECIPES:
        for lang in ("en", "tr"):
            t = TRANSLATIONS[recipe["slug"]][lang]
            assert t["name"] and t["description"]
            assert len(t["steps"]) == len(recipe["steps"]), (recipe["slug"], lang)


def test_every_persona_text_has_all_languages():
    for key, variants in TEXTS.items():
        assert set(variants) == {"uz", "en", "tr"}, key


def test_catalog_names_resolve_in_every_language():
    for ing in CATALOG:
        for name in (ing.name, ing.en, ing.tr):
            found = lookup(name)
            assert found is not None and found.name == ing.name, (name, found and found.name)


@pytest.mark.parametrize("text,expected", [
    ("2 kg pirinç, 10 adet soğan ve 1 kg havuç aldım", {"guruch": 2000, "piyoz": 1500, "sabzi": 1000}),
    ("yarım kilo kıyma, üç domates", {"qiyma": 500, "pomidor": 360}),
    ("2 kg of rice, 10 onions and 1 kg carrots", {"guruch": 2000, "piyoz": 1500, "sabzi": 1000}),
    ("I bought half a kilo of beef", {"mol go'shti": 500}),
    ("a dozen eggs, two bunches of dill", {"tuxum": 660, "shivit": 100}),
])
def test_parse_turkish_and_english(text, expected):
    items, unknown = parse_stock_text(text)
    assert {i.name: round(i.grams) for i in items} == expected
    assert unknown == []


def test_display_and_units():
    assert display_name("piyoz", "tr") == "soğan"
    assert display_name("piyoz", "en") == "onion"
    assert display_name("xurmo", "tr") == "xurmo"
    assert format_grams(1500, "guruch", "tr") == "1,5 kg"
    assert format_grams(450, "piyoz", "en") == "450 g (≈3 pcs)"
    assert format_grams(450, "piyoz", "tr") == "450 gr (≈3 adet)"


def test_language_flow_turkish(client):
    me = client.get("/api/me").json()
    assert me["language"] is None  # ilova til tanlash oynasini ko'rsatadi

    me = client.put("/api/me/language", json={"language": "tr"}).json()
    assert me["language"] == "tr"
    assert client.put("/api/me/language", json={"language": "de"}).status_code == 422

    r = client.post("/api/stock/parse", json={"text": "2 kg pirinç, 10 adet soğan, 1 kg et, 1 litre yağ, 1 kg havuç"}).json()
    assert r["message"].startswith("Harika! Kilere ekledim")
    titles = {c["title"] for c in r["stock"]["categories"]}
    assert {"Et", "Sebzeler", "Tahıl ve bakliyat"} <= titles
    displays = {i["display"] for c in r["stock"]["categories"] for i in c["items"]}
    assert {"pirinç", "soğan", "havuç"} <= displays

    names = {r["name"] for r in client.get("/api/recipes").json()}
    assert "Kazan Kebabı" in names and "Özbek Pilavı (Osh)" in names

    recipe = client.post("/api/recipes/resolve", json={"query": "kazan kebabı"}).json()
    assert recipe["slug"] == "qozon-kabob" and recipe["name"] == "Kazan Kebabı"

    plan = client.post("/api/plan", json={"slug": "qozon-kabob", "servings": 3}).json()
    assert "Alışveriş listesine ekleyeyim mi?" in plan["message"]
    assert "750 gr (≈5 adet) patates" in plan["message"]
    assert plan["recipe"]["steps"][0].startswith("Eti")
    assert {m["display"] for m in plan["check"]["missing"]} == {"patates"}

    sugg = client.post("/api/suggest", json={"servings": 3}).json()
    assert sugg["suggestions"][0]["name"] == "Özbek Pilavı (Osh)"

    done = client.post("/api/cook/finish", json={"slug": "osh", "servings": 2}).json()
    assert done["message"].startswith(("Afiyet olsun", "Ellerine sağlık"))
    assert {u["display"] for u in done["used"]} >= {"pirinç", "havuç"}


def test_language_flow_english(client):
    client.put("/api/me/language", json={"language": "en"})
    r = client.post("/api/stock/parse", json={"text": "1 kg beef, 2 kg potatoes, 3 onions and 1 litre of oil"}).json()
    assert r["message"].startswith("Lovely!")
    recipe = client.post("/api/recipes/resolve", json={"query": "cauldron kebab"}).json()
    assert recipe["name"] == "Qozon Kabob (Cauldron Kebab)"
    plan = client.post("/api/plan", json={"slug": "qozon-kabob", "servings": 2}).json()
    assert plan["check"]["ready"] and plan["message"].startswith("You have everything")
    start = client.post("/api/cook/start", json={"slug": "qozon-kabob", "servings": 2}).json()
    assert "Qozon Kabob" in start["message"]
    assert client.post("/api/recipes/resolve", json={"query": "pizza"}).status_code == 503


def test_switching_language_keeps_stock(client):
    client.put("/api/me/language", json={"language": "uz"})
    client.post("/api/stock/parse", json={"text": "2 kg guruch"})
    client.put("/api/me/language", json={"language": "en"})
    stock = client.get("/api/stock").json()
    item = stock["categories"][0]["items"][0]
    assert item["name"] == "guruch" and item["display"] == "rice" and item["label"] == "2 kg"
