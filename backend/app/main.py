import hmac
import logging
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import kitchen, llm, persona, recipes
from .auth import current_user
from .config import BACKEND_DIR, settings
from .db import SessionLocal, get_db, migrate
from .ingredients import CATEGORIES, DEFAULT_LANG, canonical, category_title, display_name, format_grams, is_staple
from .models import CookLog, Recipe, ShoppingItem, StockItem, User
from .parser import parse_stock_text
from .persona import t

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ovqatbot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    migrate()
    with SessionLocal() as db:
        recipes.seed(db)
    log.info("LLM: %s", "yoqilgan (%s)" % settings.gemini_model if llm.enabled() else "o'chirilgan — qoidaga asoslangan rejim")
    yield


# Swagger faqat ishlab chiqishda — ilova tunnel orqali internetga ochiq
docs = {} if settings.dev_mode else {"docs_url": None, "redoc_url": None, "openapi_url": None}
app = FastAPI(title="O'zbek Pazanda Bot", lifespan=lifespan, **docs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------- sxemalar

Servings = Field(ge=1, le=50)


class LanguageIn(BaseModel):
    language: Literal["uz", "en", "tr"]


class StockText(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class StockUpdate(BaseModel):
    grams: float = Field(ge=0, le=1_000_000)


class SuggestIn(BaseModel):
    servings: int = Servings


class ResolveIn(BaseModel):
    query: str = Field(min_length=1, max_length=100)


class PlanIn(BaseModel):
    slug: str
    servings: int = Servings


class ShoppingIn(BaseModel):
    items: list[dict] = Field(max_length=50)  # [{name, grams}]


class ChatIn(BaseModel):
    messages: list[dict] = Field(max_length=40)
    slug: str | None = None
    servings: int | None = None


# ---------------------------------------------------------------- yordamchilar


def lang_of(user: User) -> str:
    return user.language or DEFAULT_LANG


def _item_out(id_: int, name: str, grams: float, lang: str) -> dict:
    return {"id": id_, "name": name, "display": display_name(name, lang), "grams": round(grams), "label": format_grams(grams, name, lang)}


def _stock_out(db: Session, user: User) -> dict:
    lang = lang_of(user)
    rows = db.scalars(select(StockItem).where(StockItem.user_id == user.id)).all()
    groups: dict[str, list] = {key: [] for key in CATEGORIES}
    for r in rows:
        groups.setdefault(r.category, []).append(_item_out(r.id, r.name, r.grams, lang))
    return {
        "categories": [
            {"key": key, "title": category_title(key, lang), "items": sorted(items, key=lambda i: i["display"])}
            for key, items in groups.items()
            if items
        ],
        "count": len(rows),
    }


def _recipe_out(r: Recipe, lang: str) -> dict:
    return {
        "slug": r.slug,
        **recipes.localized(r, lang),
        "time_minutes": r.time_minutes,
        "ingredients": r.ingredients,
        "source": r.source,
    }


def _check_out(check: kitchen.RecipeCheck, lang: str) -> dict:
    data = check.to_dict()
    for item in data["ingredients"] + data["missing"]:
        item["display"] = display_name(item["name"], lang)
        item["need_label"] = format_grams(item["need_g"], item["name"], lang)
        item["missing_label"] = format_grams(item["missing_g"], item["name"], lang) if item["missing_g"] > 0 else ""
    return data


def _add_stock(db: Session, user: User, name: str, category: str, grams: float) -> None:
    row = db.scalar(select(StockItem).where(StockItem.user_id == user.id, StockItem.name == name))
    if row:
        row.grams += grams
    else:
        db.add(StockItem(user_id=user.id, name=name, category=category, grams=grams))


def _recipe_or_404(db: Session, slug: str, lang: str) -> Recipe:
    recipe = recipes.get(db, slug)
    if not recipe:
        raise HTTPException(404, t("not_found", lang))
    return recipe


def _own_or_404(row, user: User):
    if not row or row.user_id != user.id:
        raise HTTPException(404, t("item_not_found", lang_of(user)))
    return row


# ---------------------------------------------------------------- endpointlar


@app.get("/api/health")
def health():
    return {"ok": True, "llm": llm.enabled()}


def _me_out(user: User) -> dict:
    return {
        "id": user.id,
        "first_name": user.first_name,
        "language": user.language,  # None — ilova til tanlash oynasini ko'rsatadi
        "greeting": persona.greeting(user.first_name, lang_of(user)),
        "llm": llm.enabled(),
    }


@app.get("/api/me")
def me(user: User = Depends(current_user)):
    return _me_out(user)


@app.put("/api/me/language")
def set_language(body: LanguageIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    user = db.merge(user)
    user.language = body.language
    db.commit()
    return _me_out(user)


@app.get("/api/stock")
def get_stock(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return _stock_out(db, user)


@app.post("/api/stock/parse")
def parse_stock(body: StockText, user: User = Depends(current_user), db: Session = Depends(get_db)):
    lang = lang_of(user)
    # Avval bepul qoidaga asoslangan parser; Gemini faqat u tushunmagan bo'laklar uchun chaqiriladi
    parsed, unknown = parse_stock_text(body.text)
    items: list[tuple[str, str, float]] = [(p.name, p.category, p.grams) for p in parsed]
    if unknown and llm.enabled():
        try:
            llm_items, unknown = llm.parse_stock("\n".join(unknown))
            for p in llm_items:
                name, category = canonical(p["name"])
                items.append((name, category if category != "boshqa" else p["category"], float(p["grams"])))
        except llm.LLMUnavailable as e:
            log.warning("Gemini parse ishlamadi (%s), tushunilmagan bo'laklar qoldi", e)

    for name, category, grams in items:
        _add_stock(db, user, name, category, grams)
    db.commit()
    return {
        "message": persona.stock_added([(n, g) for n, _, g in items], unknown, lang),
        "added": [{"name": n, "display": display_name(n, lang), "grams": round(g)} for n, _, g in items],
        "unknown": unknown,
        "stock": _stock_out(db, user),
    }


@app.patch("/api/stock/{item_id}")
def update_stock(item_id: int, body: StockUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = _own_or_404(db.get(StockItem, item_id), user)
    if body.grams <= 0:
        db.delete(row)
    else:
        row.grams = body.grams
    db.commit()
    return _stock_out(db, user)


@app.delete("/api/stock/{item_id}")
def delete_stock(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_own_or_404(db.get(StockItem, item_id), user))
    db.commit()
    return _stock_out(db, user)


@app.get("/api/recipes")
def list_recipes(user: User = Depends(current_user), db: Session = Depends(get_db)):
    lang = lang_of(user)
    items = [
        {"slug": r.slug, "name": recipes.localized(r, lang)["name"], "time_minutes": r.time_minutes}
        for r in recipes.all_recipes(db)
    ]
    return sorted(items, key=lambda i: i["name"])


@app.post("/api/suggest")
def suggest(body: SuggestIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """A ssenariy: "Bugun nima ovqat qilsam ekan?" """
    lang = lang_of(user)
    stock = kitchen.stock_map(db, user.id)
    checks = kitchen.suggest(recipes.all_recipes(db), body.servings, stock, lang)
    return {"message": persona.suggestions(checks, body.servings, lang), "suggestions": [_check_out(c, lang) for c in checks]}


@app.post("/api/recipes/resolve")
def resolve_recipe(body: ResolveIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """B ssenariy: foydalanuvchi yozgan taomni topish (bazada bo'lmasa — web qidiruv orqali)."""
    lang = lang_of(user)
    try:
        recipe = recipes.resolve(db, body.query)
    except recipes.NotUzbekDish:
        raise HTTPException(422, t("not_uzbek", lang))
    except recipes.RecipeNotFound:
        raise HTTPException(404, t("not_found", lang))
    except llm.LLMUnavailable as e:
        raise HTTPException(503, t("ai_offline", lang) if str(e) == "disabled" else t("not_found", lang))
    return _recipe_out(recipe, lang)


@app.post("/api/plan")
def plan(body: PlanIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Tanlangan taom uchun omborni hisoblaydi va yetishmovchilikni aytadi."""
    lang = lang_of(user)
    recipe = _recipe_or_404(db, body.slug, lang)
    check = kitchen.check_recipe(recipe, body.servings, kitchen.stock_map(db, user.id), lang)
    return {"message": persona.plan(check, lang), "check": _check_out(check, lang), "recipe": _recipe_out(recipe, lang)}


@app.post("/api/cook/start")
def cook_start(body: PlanIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    lang = lang_of(user)
    recipe = _recipe_or_404(db, body.slug, lang)
    out = _recipe_out(recipe, lang)
    return {"message": persona.start_cooking(out["name"], body.servings, lang), "recipe": out}


@app.post("/api/cook/finish")
def cook_finish(body: PlanIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """"Taom tayyor" — ishlatilgan masalliqlar ombordan ayiriladi."""
    lang = lang_of(user)
    recipe = _recipe_or_404(db, body.slug, lang)
    used = kitchen.consume(db, user.id, recipe, body.servings)
    db.add(CookLog(user_id=user.id, recipe_slug=recipe.slug, servings=body.servings, used=used))
    db.commit()
    return {
        "message": persona.finished(recipes.localized(recipe, lang)["name"], lang),
        "used": [
            {**u, "display": display_name(u["name"], lang), "label": format_grams(u["grams"], u["name"], lang)} for u in used
        ],
        "stock": _stock_out(db, user),
    }


# ---------------------------------------------------------------- xarid ro'yxati


def _shopping_out(db: Session, user: User) -> list[dict]:
    lang = lang_of(user)
    rows = db.scalars(select(ShoppingItem).where(ShoppingItem.user_id == user.id).order_by(ShoppingItem.id)).all()
    return [_item_out(r.id, r.name, r.grams, lang) for r in rows]


@app.get("/api/shopping")
def get_shopping(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return _shopping_out(db, user)


@app.post("/api/shopping")
def add_shopping(body: ShoppingIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    for item in body.items:
        name = canonical(str(item.get("name", "")))[0]
        grams = float(item.get("grams", 0))
        if not name or grams <= 0 or is_staple(name):
            continue
        row = db.scalar(select(ShoppingItem).where(ShoppingItem.user_id == user.id, ShoppingItem.name == name))
        if row:
            row.grams = max(row.grams, grams)
        else:
            db.add(ShoppingItem(user_id=user.id, name=name, grams=grams))
    db.commit()
    return {"message": t("shopping_added", lang_of(user)), "items": _shopping_out(db, user)}


@app.post("/api/shopping/{item_id}/bought")
def shopping_bought(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Sotib olindi — omborga o'tkaziladi."""
    row = _own_or_404(db.get(ShoppingItem, item_id), user)
    name, category = canonical(row.name)
    _add_stock(db, user, name, category, row.grams)
    db.delete(row)
    db.commit()
    return {"items": _shopping_out(db, user), "stock": _stock_out(db, user)}


@app.delete("/api/shopping/{item_id}")
def shopping_delete(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_own_or_404(db.get(ShoppingItem, item_id), user))
    db.commit()
    return _shopping_out(db, user)


# ---------------------------------------------------------------- suhbat


@app.post("/api/chat")
def chat(body: ChatIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    lang = lang_of(user)
    if not llm.enabled():
        raise HTTPException(503, t("chat_offline", lang))
    context = None
    if body.slug and (recipe := recipes.get(db, body.slug)):
        local = recipes.localized(recipe, lang)
        steps = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(local["steps"]))
        context = t("chat_context", lang, n=body.servings or 1, dish=local["name"], steps=steps)
    try:
        reply = llm.chat(body.messages, context, lang)
    except llm.LLMUnavailable:
        raise HTTPException(503, t("chat_failed", lang))
    return {"reply": reply}


# ---------------------------------------------------------------- n8n / avtomatlashtirish


@app.post("/api/admin/recipes")
def admin_upsert_recipe(data: dict, x_admin_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    """n8n workflow topgan retseptni JSON ko'rinishida bazaga yozadi (ixtiyoriy "translations": {"en": ..., "tr": ...})."""
    if not settings.admin_token or not hmac.compare_digest(x_admin_token or "", settings.admin_token):
        raise HTTPException(403, "Forbidden")
    try:
        recipe = recipes.upsert(db, data, source="n8n")
    except ValueError as e:
        raise HTTPException(422, str(e))
    return _recipe_out(recipe, DEFAULT_LANG)


# ---------------------------------------------------------------- Mini App (frontend/dist)

FRONTEND_DIST = BACKEND_DIR.parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    # API marshrutlaridan keyin ulanadi, shuning uchun /api/* ni to'smaydi
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="webapp")
