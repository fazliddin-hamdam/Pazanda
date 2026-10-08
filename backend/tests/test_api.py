import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from app.auth import validate_init_data


def sign(data: dict, token: str) -> str:
    check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    return urlencode({**data, "hash": hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()})


def test_init_data_validation():
    data = {"auth_date": str(int(time.time())), "user": json.dumps({"id": 42, "first_name": "Dilnoza"})}
    init_data = sign(data, "123456:TEST")
    user = validate_init_data(init_data, "123456:TEST", 3600)
    assert user.id == 42 and user.first_name == "Dilnoza"
    with pytest.raises(ValueError):
        validate_init_data(init_data, "other-token")
    with pytest.raises(ValueError):
        validate_init_data(init_data.replace("Dilnoza", "Hacker"), "123456:TEST")


def test_telegram_header_creates_user(client):
    data = {"auth_date": str(int(time.time())), "user": json.dumps({"id": 777, "first_name": "Aziz"})}
    r = client.get("/api/me", headers={"Authorization": "tma " + sign(data, "123456:TEST")})
    assert r.status_code == 200 and r.json()["id"] == 777
    r = client.get("/api/me", headers={"Authorization": "tma hash=bad"})
    assert r.status_code == 401


def test_full_flow(client):
    # 1. Ombor bo'sh — tavsiya yo'q
    r = client.post("/api/suggest", json={"servings": 3})
    assert r.json()["suggestions"] == []

    # 2. Bozordan qaytdik
    r = client.post("/api/stock/parse", json={"text": "2 kg guruch, 10 ta piyoz, 1 kg sabzi, 1 kg go'sht, 1 l yog'"})
    body = r.json()
    assert {a["name"] for a in body["added"]} == {"guruch", "piyoz", "sabzi", "go'sht", "o'simlik yog'i"}
    assert "Omborga qo'shdim" in body["message"]
    titles = {c["title"] for c in body["stock"]["categories"]}
    assert {"Go'sht", "Sabzavotlar", "Don mahsulotlari"} <= titles

    # 3. A ssenariy: osh to'liq chiqadi
    r = client.post("/api/suggest", json={"servings": 3}).json()
    top = r["suggestions"][0]
    assert top["slug"] == "osh" and top["ready"]

    # 4. B ssenariy: qozon kabob uchun kartoshka yetishmaydi
    recipe = client.post("/api/recipes/resolve", json={"query": "Qozon Kabob"}).json()
    assert recipe["slug"] == "qozon-kabob"
    plan = client.post("/api/plan", json={"slug": "qozon-kabob", "servings": 3}).json()
    missing = {m["name"]: m["missing_g"] for m in plan["check"]["missing"]}
    assert missing == {"kartoshka": 750}
    assert "Xarid ro'yxatiga qo'shaymi?" in plan["message"]

    # 5. Xarid ro'yxati -> sotib oldim -> omborga o'tdi
    items = client.post("/api/shopping", json={"items": [{"name": "kartoshka", "grams": 750}]}).json()["items"]
    r = client.post(f"/api/shopping/{items[0]['id']}/bought").json()
    assert r["items"] == []
    plan = client.post("/api/plan", json={"slug": "qozon-kabob", "servings": 3}).json()
    assert plan["check"]["ready"]

    # 6. Taom tayyor — ombordan ayiriladi
    r = client.post("/api/cook/finish", json={"slug": "qozon-kabob", "servings": 3}).json()
    used = {u["name"]: u["grams"] for u in r["used"]}
    assert used["go'sht"] == 600 and used["kartoshka"] == 750 and used["piyoz"] == 150
    stock = {i["name"]: i["grams"] for c in r["stock"]["categories"] for i in c["items"]}
    assert stock["go'sht"] == 400
    assert "kartoshka" not in stock
    assert stock["piyoz"] == 1350


def test_substitute_meat_and_typo(client):
    client.post("/api/stock/parse", json={"text": "500 g mol go'shti, 300 g qo'y go'shti"})
    recipe = client.post("/api/recipes/resolve", json={"query": "lagmon"}).json()
    assert recipe["slug"] == "lagmon"
    plan = client.post("/api/plan", json={"slug": "lagmon", "servings": 2}).json()
    meat = next(i for i in plan["check"]["ingredients"] if i["name"] == "go'sht")
    assert meat["have_g"] == 800 and meat["missing_g"] == 0
    # ayirish avval mol go'shtidan, keyin qo'y go'shtidan
    client.post("/api/stock/parse", json={"text": "3 kg un, 2 kg pomidor, 5 ta bulg'or qalampiri, 2 kg piyoz, 1 kg sarimsoq, 1 l yog'"})
    r = client.post("/api/cook/finish", json={"slug": "lagmon", "servings": 6}).json()
    stock = {i["name"]: i["grams"] for c in r["stock"]["categories"] for i in c["items"]}
    assert "mol go'shti" not in stock and stock["qo'y go'shti"] == 200


def test_unknown_dish_without_llm(client):
    r = client.post("/api/recipes/resolve", json={"query": "norin"})
    assert r.status_code == 503


def test_admin_upsert(client):
    data = {
        "name": "Norin", "aliases": ["naryn"], "description": "Toshkentcha norin", "time_minutes": 180,
        "ingredients": [{"name": "un", "grams_per_person": 100}, {"name": "ot go'shti", "grams_per_person": 150}],
        "steps": ["Xamir qoriladi", "Go'sht qaynatiladi", "Ingichka to'g'raladi"],
    }
    assert client.post("/api/admin/recipes", json=data, headers={"X-Admin-Token": "wrong"}).status_code == 403
    r = client.post("/api/admin/recipes", json=data, headers={"X-Admin-Token": "secret"})
    assert r.status_code == 200 and r.json()["slug"] == "norin"
    assert client.post("/api/recipes/resolve", json={"query": "naryn"}).json()["slug"] == "norin"


def test_llm_only_gets_unparsed_chunks(client, monkeypatch):
    from app import llm

    sent = []

    def fake_parse(text):
        sent.append(text)
        return [{"name": "xurmo", "grams": 500, "category": "boshqa"}], []

    monkeypatch.setattr(llm, "enabled", lambda: True)
    monkeypatch.setattr(llm, "parse_stock", fake_parse)

    # Hammasi tushunarli — Gemini chaqirilmaydi
    client.post("/api/stock/parse", json={"text": "2 kg guruch, 5 ta piyoz"})
    assert sent == []

    # Faqat tushunilmagan bo'lak yuboriladi
    r = client.post("/api/stock/parse", json={"text": "1 kg sabzi, bir quti xurmo"}).json()
    assert sent == ["bir quti xurmo"]
    assert {a["name"] for a in r["added"]} == {"sabzi", "xurmo"}
    assert r["unknown"] == []
